"""
Base Agent Class
Provides common functionality for all pipeline agents
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import json
import jsonschema
from openai import OpenAI

from app.logger import setup_logger


class BaseAgent(ABC):
    """
    Base class for all pipeline agents with common functionality.

    All agents should inherit from this class and implement the execute() method.
    """

    def __init__(self, agent_name: str):
        """
        Initialize base agent with common setup.

        Args:
            agent_name: Name of the agent (e.g., 'researcher', 'planner', 'maker', 'packager')
        """
        self.agent_name = agent_name
        self._client: Optional[OpenAI] = None  # Private attribute for lazy loading
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

    def _load_output_schema(self) -> Dict[str, Any]:
        """
        Load output schema from schemas/{output_schema_name}

        Returns:
            Dict[str, Any]: Parsed JSON schema

        Raises:
            FileNotFoundError: If schema file doesn't exist
            json.JSONDecodeError: If schema file is not valid JSON
        """
        filename = f"{self.agent_name}.output.schema.json"
        schema_path = Path(__file__).parent / "schemas" / filename

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            self.logger.debug(f"Loaded output schema from {filename}")
            return schema
        except FileNotFoundError:
            self.logger.error(f"Schema file not found: {schema_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Malformed schema JSON in {schema_path}: {e}")
            raise

    def _validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate API response against agent's output schema.

        Args:
            response: API response data to validate

        Returns:
            bool: True if validation passes, False otherwise
        """
        schema_path = Path(__file__).parent / "schemas" / self.output_schema_name

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)

            # Validate using Draft 7 schema
            jsonschema.validate(response, schema)
            self.logger.info(f"Response validation passed for {self.agent_name}")
            return True

        except jsonschema.ValidationError as e:
            self.logger.error(f"Response validation failed: {e.message}")
            self.logger.debug(f"Validation error details: {e}")
            return False
        except jsonschema.SchemaError as e:
            self.logger.error(f"Invalid schema file: {e}")
            return False
        except FileNotFoundError:
            self.logger.error(f"Schema file not found: {schema_path}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"Malformed schema JSON: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected validation error: {e}")
            return False

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
            ValueError: If no output received from stream
            json.JSONDecodeError: If output is not valid JSON
        """
        final_output = None

        for event in stream:
            # Get event type safely without hard-coding
            event_type = getattr(event, 'type', 'unknown')

            # Emit log event for UI display
            emit({
                "event": "log",
                "step": self.agent_name,
                "message": f"Processing: {event_type}"
            })

            # Extract output from response.completed event
            if event_type == 'response.completed':
                self.logger.info(f"FINAL EVENT DETECTED: {event_type}")

                # DEBUG: Show the event type/class
                event_class = type(event).__name__
                event_module = type(event).__module__
                emit({"event": "log", "step": self.agent_name, "message": f"DEBUG: Event type = {event_module}.{event_class}"})

                # DEBUG: Show the actual event object
                emit({"event": "log", "step": self.agent_name, "message": f"DEBUG: Event attributes = {dir(event)}"})

                # Try to convert event to dict/string
                try:
                    event_str = str(event)
                    emit({"event": "log", "step": self.agent_name, "message": f"DEBUG: Event str() = {event_str}"})
                except Exception as e:
                    emit({"event": "log", "step": self.agent_name, "message": f"DEBUG: str() failed = {e}"})

                try:
                    event_repr = repr(event)
                    emit({"event": "log", "step": self.agent_name, "message": f"DEBUG: Event repr() = {event_repr}"})
                except Exception as e:
                    emit({"event": "log", "step": self.agent_name, "message": f"DEBUG: repr() failed = {e}"})

                # Try model_dump() if it's a Pydantic model
                if hasattr(event, 'model_dump'):
                    try:
                        event_dict = event.model_dump()
                        emit({"event": "log", "step": self.agent_name, "message": f"DEBUG: Event dict = {event_dict}"})
                    except Exception as e:
                        emit({"event": "log", "step": self.agent_name, "message": f"DEBUG: model_dump() failed = {e}"})

                # Extract output using correct path: event.response.output[0].content[0].text
                try:
                    if hasattr(event, 'response') and hasattr(event.response, 'output'):
                        output_list = event.response.output
                        if output_list and len(output_list) > 0:
                            message = output_list[0]
                            if hasattr(message, 'content') and message.content and len(message.content) > 0:
                                content = message.content[0]
                                if hasattr(content, 'text'):
                                    final_output = content.text
                                    self.logger.info(f"Successfully extracted output via event.response.output[0].content[0].text")
                                    emit({"event": "log", "step": self.agent_name, "message": f"DEBUG: Extracted output (length={len(final_output)} chars)"})
                except Exception as e:
                    self.logger.error(f"Error extracting output: {e}")
                    emit({"event": "log", "step": self.agent_name, "message": f"DEBUG: Extraction error = {e}"})

        # Validate we got output
        if not final_output:
            self.logger.error("No output received from stream")
            raise ValueError("No output received from stream")

        # Parse JSON response
        try:
            result = json.loads(final_output)
            self.logger.info("Successfully parsed stream output")
            return result
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse stream output as JSON: {e}")
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
