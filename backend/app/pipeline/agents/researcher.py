"""
Researcher Agent
Finds and prioritizes profitable digital-product niches using OpenAI
"""

import json
from typing import Dict, Any, Callable
from app.pipeline.agents.base_agent import BaseAgent


class ResearcherAgent(BaseAgent):
    """Researches profitable digital product niches using OpenAI API"""

    def __init__(self):
        """Initialize ResearcherAgent with base functionality"""
        super().__init__("researcher")

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
        emit({"event": "log", "step": self.agent_name, "message": "Starting research..."})

        try:
            # Build user prompt based on mode
            user_prompt = self._build_user_prompt(focus, niches)

            emit({"event": "log", "step": self.agent_name, "message": "Calling OpenAI API..."})

            # Call OpenAI API
            response = self.client.responses.create(
                model="gpt-5",
                instructions = self.instructions,
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
            emit({"event": "log", "step": self.agent_name, "message": "Processing stream..."})
            result = self._handle_stream(response, emit)

            # Validate against schema
            emit({"event": "log", "step": self.agent_name, "message": "Validating response..."})
            if not self._validate_response(result):
                raise ValueError("Response validation failed against schema")

            emit({"event": "log", "step": self.agent_name, "message": "Research complete"})
            return result

        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            emit({"event": "error", "step": self.agent_name, "message": str(e)})
            raise

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
