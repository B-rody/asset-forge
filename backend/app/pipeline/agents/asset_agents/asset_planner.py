"""
Planner Agent
Designs digital product bundle structure, personas, and pricing
"""

import json
from typing import Dict, Any, Callable, Optional, Union, TYPE_CHECKING
from datetime import datetime
from app.pipeline.agents.base_agent import BaseAgent

if TYPE_CHECKING:
    from app.database.db import DatabaseManager


class PlannerAgent(BaseAgent):
    """Designs digital product bundles based on research data"""

    def __init__(self, db_manager: Optional["DatabaseManager"] = None):
        """Initialize PlannerAgent with base functionality"""
        super().__init__("asset_planner", db_manager=db_manager)

    def execute(
        self,
        idea: Union[str, Dict[str, Any]],
        emit: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """
        Execute planning step with OpenAI

        Args:
            idea: Either an idea_id (string) to load from DB, or full idea data (dict)
            emit: Callback function for progress updates

        Returns:
            Structured bundle plan data

        Raises:
            ValueError: If API returns None, invalid response, or idea not found
            json.JSONDecodeError: If response is not valid JSON
        """
        emit({"event": "log", "step": self.step_name, "message": "Starting bundle planning..."})

        try:
            # Load idea data if idea_id provided
            idea_data = self._load_idea_data(idea, emit)

            # Build user prompt with idea data
            user_prompt = self._build_user_prompt(idea_data)

            emit({"event": "log", "step": self.step_name, "message": "Calling OpenAI API..."})

            # Call OpenAI API
            response = self.client.responses.create(
                model="gpt-5",
                instructions=self.instructions,
                input=user_prompt,
                tools=[{"type": "web_search"}],
                reasoning={"effort": "medium"},
                tool_choice="auto",
                stream=True,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "planner_response",
                        "schema": self.output_schema,
                        "strict": True
                    }
                }
            )

            # Handle streaming response
            emit({"event": "log", "step": self.step_name, "message": "Processing stream..."})
            result = self._handle_stream(response, emit)

            # Validate against schema
            emit({"event": "log", "step": self.step_name, "message": "Validating response..."})
            if not self._validate_response(result):
                raise ValueError("Response validation failed against schema")

            emit({"event": "log", "step": self.step_name, "message": "Planning complete"})

            # Save to database if db_manager is available
            if self.db_manager:
                emit({"event": "log", "step": self.step_name, "message": "Saving to database..."})
                save_success = self._save_result(result, idea_data)

                if save_success:
                    emit({"event": "log", "step": self.step_name, "message": "Database save complete"})
                else:
                    error_msg = "Failed to save bundle plan to database"
                    self.logger.error(error_msg)
                    emit({"event": "error", "step": self.step_name, "message": error_msg})
                    raise ValueError(error_msg)

            return result

        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            raise

    def _load_idea_data(
        self,
        idea: Union[str, Dict[str, Any]],
        emit: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """
        Load idea data from database or validate provided dict

        Args:
            idea: Either idea_id (string) or full idea dict
            emit: Callback for progress updates

        Returns:
            Complete idea data dictionary

        Raises:
            ValueError: If idea_id not found or invalid data provided
        """
        # If already a dict, validate it has required fields
        if isinstance(idea, dict):
            required_fields = ["idea_id", "title", "niche", "sub_niche", "value_prop",
                             "differentiation_angle", "demand_signals"]
            missing = [f for f in required_fields if f not in idea]
            if missing:
                raise ValueError(f"Idea data missing required fields: {missing}")
            return idea

        # Otherwise, load from database
        if not self.db_manager:
            raise ValueError("Cannot load idea by ID: no db_manager provided")

        emit({"event": "log", "step": self.step_name, "message": f"Loading idea: {idea}"})

        idea_record = self.idea_queries.get_by_id(idea)
        if not idea_record:
            raise ValueError(f"Idea not found: {idea}")

        # Parse the full idea JSON
        try:
            idea_data = json.loads(idea_record.idea_json)
            # IMPORTANT: Add idea_id to parsed data (it's stored in DB row, not in JSON blob)
            # This is needed for _save_result() to properly link the bundle to the idea
            idea_data["idea_id"] = idea_record.idea_id
            self.logger.info(f"Loaded idea data for: {idea_data.get('title', 'Unknown')}")
            return idea_data
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse idea_json for {idea}: {e}")
            raise ValueError(f"Invalid idea_json data for {idea}")

    def _build_user_prompt(self, idea_data: Dict[str, Any]) -> str:
        """
        Build user prompt combining input config and idea data

        Args:
            idea_data: Complete idea data from researcher

        Returns:
            JSON string with combined input parameters and idea data
        """
        # Load the base input JSON
        input_data = json.loads(self.input)

        # Inject the idea data into the prompt
        input_data["selected_idea"] = idea_data

        # Update selected_idea_id if present
        if "idea_id" in idea_data:
            input_data["selected_idea_id"] = idea_data["idea_id"]

        return json.dumps(input_data, indent=2)

    def _save_result(self, result: Dict[str, Any], idea_data: Dict[str, Any]) -> bool:
        """
        Save planner result to database.

        Creates a Bundle record with the planner output, and moves the source idea
        from ideas table to used_ideas archive.

        Args:
            result: The validated result from execute()
            idea_data: The source idea data used for planning

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.db_manager:
            self.logger.warning("No db_manager available, skipping database save")
            return False

        try:
            from app.database.models import Bundle, UsedIdea, Idea
            import re

            # IMPORTANT: Always use idea_id from input (idea_data), never trust AI's response
            # The AI may generate a different format or incorrect ID
            idea_id = idea_data.get("idea_id")
            if not idea_id:
                self.logger.error("Missing idea_id in idea_data")
                return False

            # Generate bundle_id in backend using timestamp pattern (don't trust AI)
            # Format: bundle-YYYY-MM-DD-{slug} (e.g., bundle-2025-10-18-low-fodmap-reintro)
            timestamp = datetime.now()
            date_str = timestamp.strftime("%Y-%m-%d")

            # Create slug from bundle title (from AI response)
            bundle_title = result.get("title", "untitled-bundle")
            # Sanitize title to create URL-safe slug
            slug = re.sub(r'[^a-z0-9]+', '-', bundle_title.lower())
            slug = slug.strip('-')[:50]  # Limit length

            bundle_id = f"bundle-{date_str}-{slug}"

            self.logger.info(f"Starting database save: bundle {bundle_id} from idea {idea_id}")

            # Inject backend-generated IDs into result dict (overwrite any AI-generated IDs)
            result["bundle_id"] = bundle_id
            result["idea_id"] = idea_id

            # 1. Create Bundle record
            self.logger.debug(f"Creating bundle: {bundle_id}")

            bundle = Bundle(
                bundle_id=bundle_id,
                idea_id=idea_id,
                created_at=result.get("generated_at", datetime.now().isoformat()),
                updated_at=datetime.now().isoformat(),
                current_step="maker",
                status="pending",
                error_message=None,
                planner_output=json.dumps(result)  # Store full planner output as JSON
            )

            if not self.bundle_queries.create(bundle):
                self.logger.error(f"Failed to create bundle: {bundle_id}")
                return False

            self.logger.info(f"✓ Bundle created: {bundle_id}")

            # 2. Move idea from ideas to used_ideas
            self.logger.debug(f"Archiving idea: {idea_id}")

            # Load the original idea record from database
            idea_record = self.idea_queries.get_by_id(idea_id)
            if not idea_record:
                self.logger.warning(f"Idea {idea_id} not found in ideas table (may already be archived)")
            else:
                # Create UsedIdea record
                used_idea = UsedIdea(
                    idea_id=idea_record.idea_id,
                    research_session_id=idea_record.research_session_id,
                    created_at=idea_record.created_at,
                    used_at=datetime.now().isoformat(),
                    bundle_id=bundle_id,
                    title=idea_record.title,
                    niche=idea_record.niche,
                    sub_niche=idea_record.sub_niche,
                    priority=idea_record.priority,
                    roi_estimate=idea_record.roi_estimate,
                    idea_json=idea_record.idea_json
                )

                if self.used_idea_queries.create(used_idea):
                    # Delete from ideas table
                    if self.idea_queries.delete(idea_id):
                        self.logger.info(f"✓ Idea archived: {idea_id} → used_ideas")
                    else:
                        self.logger.warning(f"Idea archived but failed to delete from ideas table: {idea_id}")
                else:
                    self.logger.warning(f"Failed to archive idea: {idea_id}")

            self.logger.info(f"✓ Successfully saved bundle plan to database: {bundle_id}")
            return True

        except Exception as e:
            self.logger.error(f"✗ Critical error in _save_result: {e}", exc_info=True)
            return False
