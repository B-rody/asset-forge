"""
Base Agent Class
Provides common functionality for all pipeline agents
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING
import json
import jsonschema
import re
from openai import OpenAI

from app.logger import setup_logger

if TYPE_CHECKING:
    from app.database.db import DatabaseManager


class BaseAgent(ABC):
    """
    Base class for all pipeline agents with common functionality.

    All agents should inherit from this class and implement the execute() method.
    """

    def __init__(self, agent_name: str, db_manager: Optional["DatabaseManager"] = None):
        """
        Initialize base agent with common setup.

        Args:
            agent_name: Name of the agent (e.g., 'researcher', 'planner', 'maker', 'packager')
            db_manager: Optional database manager for persistence (enables _save_result)
        """
        self.agent_name = agent_name
        self._client: Optional[OpenAI] = None  # Private attribute for lazy loading
        self.db_manager = db_manager
        self.logger = setup_logger(f"agent.{agent_name}")

        # Load instructions automatically
        self.instructions = self._load_instructions()
        self.input = self._load_input()
        self.output_schema = self._load_output_schema()

    @property
    def client(self) -> OpenAI:
        """
        Lazy-loading OpenAI client property.

        Automatically initializes the client on first access using API key from system keyring.

        Returns:
            OpenAI: Configured client instance

        Raises:
            ValueError: If no API key is found in keyring
        """
        if self._client is None:
            from app.security.keyring_store import get_openai_client
            try:
                self._client = get_openai_client()
                self.logger.info("OpenAI client initialized successfully")
            except ValueError as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
                raise
        return self._client

    @property
    def step_name(self) -> str:
        """
        Returns the capitalized step name for frontend display.

        Returns:
            str: Capitalized agent name (e.g., 'researcher' -> 'Researcher')
        """
        return self.agent_name.capitalize()

    @property
    def research_queries(self):
        """Lazy-load research queries (requires db_manager)"""
        if not self.db_manager:
            raise ValueError(f"{self.agent_name}: db_manager required for research_queries")
        if not hasattr(self, '_research_queries'):
            from app.database.queries import ResearchQueries
            self._research_queries = ResearchQueries(self.db_manager)
        return self._research_queries

    @property
    def idea_queries(self):
        """Lazy-load idea queries (requires db_manager)"""
        if not self.db_manager:
            raise ValueError(f"{self.agent_name}: db_manager required for idea_queries")
        if not hasattr(self, '_idea_queries'):
            from app.database.queries import IdeaQueries
            self._idea_queries = IdeaQueries(self.db_manager)
        return self._idea_queries

    @property
    def bundle_queries(self):
        """Lazy-load bundle queries (requires db_manager)"""
        if not self.db_manager:
            raise ValueError(f"{self.agent_name}: db_manager required for bundle_queries")
        if not hasattr(self, '_bundle_queries'):
            from app.database.queries import BundleQueries
            self._bundle_queries = BundleQueries(self.db_manager)
        return self._bundle_queries

    @property
    def maker_queries(self):
        """Lazy-load maker queries (requires db_manager)"""
        if not self.db_manager:
            raise ValueError(f"{self.agent_name}: db_manager required for maker_queries")
        if not hasattr(self, '_maker_queries'):
            from app.database.queries import MakerQueries
            self._maker_queries = MakerQueries(self.db_manager)
        return self._maker_queries

    @property
    def used_idea_queries(self):
        """Lazy-load used idea queries (requires db_manager)"""
        if not self.db_manager:
            raise ValueError(f"{self.agent_name}: db_manager required for used_idea_queries")
        if not hasattr(self, '_used_idea_queries'):
            from app.database.queries import UsedIdeaQueries
            self._used_idea_queries = UsedIdeaQueries(self.db_manager)
        return self._used_idea_queries

    @property
    def created_bundle_queries(self):
        """Lazy-load created bundle queries (requires db_manager)"""
        if not self.db_manager:
            raise ValueError(f"{self.agent_name}: db_manager required for created_bundle_queries")
        if not hasattr(self, '_created_bundle_queries'):
            from app.database.queries import CreatedBundleQueries
            self._created_bundle_queries = CreatedBundleQueries(self.db_manager)
        return self._created_bundle_queries

    def _load_instructions(self) -> str:
        """
        Load agent instructions from prompts/instructions/{agent_name}.instructions.md

        Returns:
            str: Contents of the instructions file

        Raises:
            FileNotFoundError: If instructions file doesn't exist
        """
        filename = f"{self.agent_name}.instructions.md"
        path = Path(__file__).parent / "prompts" / "instructions" / filename

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.logger.debug(f"Loaded instructions from {filename}")
            return content
        except FileNotFoundError:
            self.logger.error(f"Instructions file not found: {path}")
            raise

    def _load_input(self) -> str:
        """
        Load input prompt from prompts/input/{input_name}

        Args:
            input_name: Name of the input file to load

        Returns:
            str: Contents of the input file

        Raises:
            FileNotFoundError: If input file doesn't exist
        """
        filename = f"{self.agent_name}.input.json"
        path = Path(__file__).parent / "prompts" / "input" / filename

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.logger.debug(f"Loaded input from {filename}")
            return content
        except FileNotFoundError:
            self.logger.error(f"Input file not found: {path}")
            raise

    def _load_output_schema(self) -> Optional[Dict[str, Any]]:
        """
        Load output schema from schemas/{agent_name}.output.schema.json

        If the schema file is missing or empty, returns None instead of raising.
        This allows agents to operate without output schemas when appropriate
        (e.g., maker agent generates files rather than structured JSON).

        Returns:
            Optional[Dict[str, Any]]: Parsed JSON schema, or None if not available

        Raises:
            json.JSONDecodeError: If schema file exists but contains invalid JSON
        """
        filename = f"{self.agent_name}.output.schema.json"
        schema_path = Path(__file__).parent / "schemas" / filename

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

                # Handle empty file gracefully
                if not content:
                    self.logger.warning(f"Output schema file is empty: {filename} - schema validation disabled")
                    return None

                schema = json.loads(content)
            self.logger.debug(f"Loaded output schema from {filename}")
            return schema
        except FileNotFoundError:
            self.logger.warning(f"Schema file not found: {filename} - schema validation disabled")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Malformed schema JSON in {schema_path}: {e}")
            raise

    def _validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate API response against agent's output schema.

        If no output schema is loaded (self.output_schema is None), validation
        is skipped and True is returned. This allows agents without schemas to
        bypass validation.

        Args:
            response: API response data to validate

        Returns:
            bool: True if validation passes (or no schema exists), False otherwise
        """
        # Skip validation if no schema is loaded
        if self.output_schema is None:
            self.logger.debug(f"No output schema loaded for {self.agent_name} - skipping validation")
            return True

        try:
            # Validate using the pre-loaded schema
            jsonschema.validate(response, self.output_schema)
            self.logger.info(f"Response validation passed for {self.agent_name}")
            return True

        except jsonschema.ValidationError as e:
            self.logger.error(f"Response validation failed: {e.message}")
            self.logger.debug(f"Validation error details: {e}")
            return False
        except jsonschema.SchemaError as e:
            self.logger.error(f"Invalid schema: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected validation error: {e}")
            return False

    def _strip_citations(self, data: Any) -> Any:
        """
        Recursively strip OpenAI citation markers from data structures.

        Citation markers follow the pattern: \ue200cite\ue202<refs>\ue201
        where <refs> can be multiple citation references separated by \ue202

        Args:
            data: Any data structure (dict, list, str, or primitive)

        Returns:
            Same data structure with citations stripped from all string values
        """
        if isinstance(data, dict):
            # Recursively process dictionary values
            return {key: self._strip_citations(value) for key, value in data.items()}

        elif isinstance(data, list):
            # Recursively process list items
            return [self._strip_citations(item) for item in data]

        elif isinstance(data, str):
            # Strip citation markers from string and clean trailing whitespace
            # Pattern: \ue200cite\ue202<citation-refs>\ue201
            cleaned = re.sub(r'\ue200cite\ue202[^\ue201]*\ue201', '', data)
            return cleaned.strip()

        else:
            # Return primitives (int, float, bool, None) unchanged
            return data

    def _handle_stream(
        self,
        stream,
        emit: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """
        Handle streaming response from OpenAI API.

        Uses a defensive approach that doesn't hard-code event types,
        making it resilient to API changes.

        Args:
            stream: Iterator from OpenAI responses.create(stream=True)
            emit: Callback function for progress updates

        Returns:
            Dict[str, Any]: Parsed JSON response from final output

        Raises:
            ValueError: If no output received, request failed, or incomplete
            json.JSONDecodeError: If output is not valid JSON
        """
        final_output = None
        failure_reason = None

        for event in stream:
            # Get event type safely without hard-coding
            event_type = getattr(event, 'type', 'unknown')

            # Only emit logs for key response lifecycle events
            if event_type in ['response.created', 'response.in_progress', 'response.completed', 'response.failed', 'response.incomplete']:
                emit({
                    "event": "log",
                    "step": self.step_name,
                    "message": f"Processing: {event_type}"
                })

            # Handle failure states explicitly
            if event_type == 'response.failed':
                error_msg = getattr(getattr(event, 'response', None), 'error', {})
                failure_reason = f"OpenAI request failed: {error_msg.get('message', 'Unknown error')}"
                emit({"event": "error", "step": self.step_name, "message": failure_reason})

            elif event_type == 'response.incomplete':
                failure_reason = "OpenAI request incomplete: The model did not finish processing the request"
                emit({"event": "error", "step": self.step_name, "message": failure_reason})

            # Extract output from response.completed event
            elif event_type == 'response.completed':
                # Extract output using correct path
                try:
                    if hasattr(event, 'response') and hasattr(event.response, 'output_text'):
                        final_output = event.response.output_text
                        self.logger.info(f"Successfully extracted output from stream")
                except Exception as e:
                    self.logger.error(f"Error extracting output: {e}")
                    emit({"event": "error", "step": self.step_name, "message": f"Extraction error: {e}"})

        # Check for failures
        if failure_reason:
            self.logger.error(failure_reason)
            raise ValueError(failure_reason)

        # Validate we got output
        if not final_output:
            error_msg = "No output received from OpenAI stream"
            self.logger.error(error_msg)
            emit({"event": "error", "step": self.step_name, "message": error_msg})
            raise ValueError(error_msg)

        # Parse JSON response
        try:
            result = json.loads(final_output)
            self.logger.info("Successfully parsed stream output")

            # Strip OpenAI citation markers from all string values
            result = self._strip_citations(result)
            self.logger.debug("Stripped citation markers from response")

            return result
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse stream output as JSON: {e}"
            self.logger.error(error_msg)
            emit({"event": "error", "step": self.step_name, "message": error_msg})
            raise

    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute agent logic - must be implemented by subclass.

        This method should contain the agent-specific logic for processing
        inputs and generating outputs.

        Returns:
            Dict[str, Any]: Structured output data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute() method"
        )

    def _save_result(self, result: Dict[str, Any]) -> bool:
        """
        Save agent result to database (optional, only if db_manager provided).

        Subclasses can override this to implement their own persistence logic.
        By default, this is a no-op if db_manager is not provided.

        Args:
            result: The result dictionary from execute()

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.db_manager:
            self.logger.debug(f"{self.agent_name}: No db_manager, skipping _save_result")
            return False

        self.logger.warning(
            f"{self.agent_name}: _save_result() not implemented, result not saved to DB"
        )
        return False
