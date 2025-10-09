"""
Base Agent Class
Provides common functionality for all pipeline agents
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import json
import jsonschema
from jsonschema.validators import Draft202012Validator
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

        # Set schema filename based on agent name
        self.output_schema_name = f"{agent_name}.output.schema.json"

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

    def _load_input(self, input_name: str) -> str:
        """
        Load input prompt from prompts/input/{input_name}

        Args:
            input_name: Name of the input file to load

        Returns:
            str: Contents of the input file

        Raises:
            FileNotFoundError: If input file doesn't exist
        """
        path = Path(__file__).parent / "prompts" / "input" / input_name

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.logger.debug(f"Loaded input from {input_name}")
            return content
        except FileNotFoundError:
            self.logger.error(f"Input file not found: {path}")
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

            # Use Draft 2020-12 validator for schemas using that draft
            validator = Draft202012Validator(schema)
            validator.validate(response)
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

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
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
