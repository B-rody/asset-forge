"""
Researcher Agent
Finds and prioritizes profitable digital-product niches using OpenAI
"""

import json
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from app.pipeline.agents.base_agent import BaseAgent

if False:  # TYPE_CHECKING
    from app.database.db import DatabaseManager


class ResearcherAgent(BaseAgent):
    """Researches profitable digital product niches using OpenAI API"""

    def __init__(self, db_manager: Optional["DatabaseManager"] = None):
        """Initialize ResearcherAgent with base functionality"""
        super().__init__("researcher", db_manager=db_manager)

    def execute(
        self,
        emit: Callable[[Dict[str, Any]], None],
        focus: bool = False,
        niches: str = "",
    ) -> Dict[str, Any]:
        """
        Execute research step with OpenAI

        Args:
            mode: Research mode (e.g., 'niche_discovery', 'trend_analysis')
            params: Input parameters for the research
            emit: Callback function for progress updates

        Returns:
            Structured research data

        Raises:
            ValueError: If API returns None or invalid response
            json.JSONDecodeError: If response is not valid JSON
        """
        emit({"event": "log", "step": self.step_name, "message": "Starting research..."})

        # Track execution time for error reporting
        start_time = datetime.now()

        try:
            # Build enhanced instructions with off-limits ideas
            enhanced_instructions = self._build_enhanced_instructions(emit)

            # Build user prompt based on mode
            user_prompt = self._build_user_prompt(focus, niches)

            emit({"event": "log", "step": self.step_name, "message": "Calling OpenAI API..."})

            # Call OpenAI API
            response = self.client.responses.create(
                model="gpt-5",
                instructions=enhanced_instructions,
                input=user_prompt,
                tools=[{"type": "web_search"}],
                reasoning={"effort" : "medium"},
                tool_choice="required",
                stream=True,
                text={
                    "format": {
                        "type": "json_schema",
                        "name" : "researcher_response",
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

            emit({"event": "log", "step": self.step_name, "message": "Research complete"})

            # Save to database if db_manager is available
            if self.db_manager:
                emit({"event": "log", "step": self.step_name, "message": "Saving to database..."})
                save_success = self._save_result(result)

                if save_success:
                    emit({"event": "log", "step": self.step_name, "message": "Database save complete"})
                else:
                    error_msg = "Failed to save research results to database"
                    self.logger.error(error_msg)
                    emit({"event": "error", "step": self.step_name, "message": error_msg})
                    raise ValueError(error_msg)

            return result

        except Exception as e:
            error_message = str(e)

            # Provide more helpful error messages for common failures
            if "peer closed connection" in error_message.lower() or "incomplete chunked read" in error_message.lower():
                elapsed = int((datetime.now() - start_time).total_seconds())
                error_message = (
                    "OpenAI API connection was interrupted during streaming. "
                    "This can happen with long-running web searches. "
                    f"The request ran for {elapsed}s before failing. "
                    "Please try again - the system will automatically retry on transient errors."
                )
            elif "timeout" in error_message.lower():
                error_message = (
                    f"OpenAI API request timed out. The researcher agent with web_search can take 10+ minutes. "
                    f"Current timeout is set to 15 minutes. Original error: {error_message}"
                )

            self.logger.error(f"Execution failed: {error_message}")
            emit({"event": "error", "step": self.step_name, "message": error_message})
            raise ValueError(error_message) from e

    def _build_enhanced_instructions(self, emit: Callable[[Dict[str, Any]], None]) -> str:
        """
        Build enhanced instructions with off-limits ideas from the database.

        Fetches product ideas from the past 8 weeks (both active and used ideas)
        and adds them to the system instructions to prevent duplicates.

        Args:
            emit: Callback function for progress updates

        Returns:
            Enhanced instructions string with off-limits ideas appended
        """
        # Start with base instructions
        instructions = self.instructions

        # Only fetch off-limits ideas if db_manager is available
        if not self.db_manager:
            self.logger.info("No db_manager available, skipping off-limits ideas check")
            return instructions

        try:
            emit({"event": "log", "step": self.step_name, "message": "Checking for off-limits ideas..."})

            # Fetch recent idea titles (past 8 weeks) from both ideas and used_ideas tables
            off_limits_titles = self.idea_queries.get_historical_titles(weeks_back=8)

            # Only append off-limits section if we have ideas to exclude
            if off_limits_titles and len(off_limits_titles) > 0:
                self.logger.info(f"Found {len(off_limits_titles)} off-limits ideas from past 8 weeks")

                # Append off-limits section to instructions
                off_limits_section = "\n\n## OFF-LIMITS IDEAS\n\n"
                off_limits_section += "The following product ideas have been researched or used in the past 8 weeks. "
                off_limits_section += "DO NOT generate ideas with these exact titles or extremely similar concepts:\n\n"

                for title in off_limits_titles:
                    off_limits_section += f"- {title}\n"

                off_limits_section += "\nEnsure your new ideas are distinctly different from these existing ideas."

                instructions += off_limits_section
                emit({"event": "log", "step": self.step_name, "message": f"Added {len(off_limits_titles)} off-limits ideas to instructions"})
            else:
                # No off-limits ideas - use base instructions without modification
                self.logger.info("No off-limits ideas found - using base instructions")
                emit({"event": "log", "step": self.step_name, "message": "No off-limits ideas to exclude"})

        except Exception as e:
            # Log error but don't fail the entire request
            self.logger.warning(f"Failed to fetch off-limits ideas: {e}")
            emit({"event": "log", "step": self.step_name, "message": "Warning: Could not fetch off-limits ideas"})

        return instructions

    def _build_user_prompt(self, focus: bool, niches: str) -> str:
        """
        Build user prompt based on focus mode and niches

        Args:
            focus: Whether to focus research on specific niches
            niches: Comma-separated niches to focus on

        Returns:
            JSON string with configured input parameters
        """
        # Load the base input JSON
        input_data = json.loads(self.input)

        # If focus mode, replace niches in constraints
        if focus:
            input_data["constraints"]["niches"] = niches

        return json.dumps(input_data)

    def _save_result(self, result: Dict[str, Any]) -> bool:
        """
        Save researcher results to database.

        Creates a research session and saves all generated ideas.

        Args:
            result: The validated result from execute()

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.db_manager:
            self.logger.warning("No db_manager available, skipping database save")
            return False

        try:
            from app.database.models import Idea, ResearchSession

            # Generate session ID and timestamp for unique idea IDs
            timestamp = datetime.now()
            session_id = f"session-{timestamp.strftime('%Y-%m-%d-%H%M%S')}"
            # Use compact format for idea IDs: idea-YYYYMMDD-HHMMSS-XXX
            idea_id_prefix = f"idea-{timestamp.strftime('%Y%m%d-%H%M%S')}"

            ideas = result.get("ideas", [])

            self.logger.info(f"Starting database save: {len(ideas)} ideas to session {session_id}")

            # Create research session
            self.logger.debug(f"Creating research session: {session_id}")
            session_created = self.research_queries.create_session(session_id, len(ideas))

            if not session_created:
                self.logger.error(f"Failed to create research session: {session_id}")
                return False

            self.logger.info(f"✓ Research session created: {session_id}")

            # Save each idea with detailed logging
            saved_count = 0
            failed_ideas = []

            for idx, idea_data in enumerate(ideas, 1):
                try:
                    # Generate unique ID in backend instead of trusting AI
                    # Format: idea-YYYYMMDD-HHMMSS-XXX (e.g., idea-20251017-143052-001)
                    idea_id = f"{idea_id_prefix}-{idx:03d}"
                    idea_title = idea_data.get("title", "Untitled")

                    self.logger.debug(f"Saving idea {idx}/{len(ideas)}: {idea_id} - {idea_title[:50]}")

                    # Map schema fields to Idea model
                    idea = Idea(
                        idea_id=idea_id,
                        research_session_id=session_id,
                        created_at=result.get("generated_at", datetime.now().isoformat()),
                        title=idea_title,
                        niche=idea_data["niche"],
                        sub_niche=idea_data["sub_niche"],
                        priority=idea_data["priority"],
                        roi_estimate=idea_data["roi_estimate"],
                        idea_json=json.dumps(idea_data)  # Store full idea as JSON
                    )

                    if self.idea_queries.create(idea):
                        saved_count += 1
                        self.logger.debug(f"  ✓ Saved idea {idx}/{len(ideas)}")
                    else:
                        failed_ideas.append(f"{idea_id} ({idea_title[:30]})")
                        self.logger.warning(f"  ✗ Failed to save idea {idx}/{len(ideas)}: {idea_id}")

                except KeyError as e:
                    failed_ideas.append(f"idea-{idx} (missing field: {e})")
                    self.logger.error(f"  ✗ Missing required field in idea {idx}: {e}")
                except Exception as e:
                    failed_ideas.append(f"idea-{idx} (error: {str(e)[:30]})")
                    self.logger.error(f"  ✗ Error saving idea {idx}: {e}", exc_info=True)

            # Log detailed summary
            if saved_count == len(ideas):
                self.logger.info(f"✓ Successfully saved all {saved_count}/{len(ideas)} ideas to database")
                return True
            elif saved_count > 0:
                self.logger.warning(f"⚠ Partially saved: {saved_count}/{len(ideas)} ideas succeeded")
                self.logger.warning(f"Failed ideas: {', '.join(failed_ideas)}")
                return False
            else:
                self.logger.error(f"✗ Failed to save any ideas (0/{len(ideas)})")
                self.logger.error(f"All failed: {', '.join(failed_ideas)}")
                return False

        except Exception as e:
            self.logger.error(f"✗ Critical error in _save_result: {e}", exc_info=True)
            return False
