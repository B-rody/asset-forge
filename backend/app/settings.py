"""
Application Settings and Configuration
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from platformdirs import user_data_dir, user_config_dir

APP_NAME = "AssetForge"
APP_AUTHOR = "AssetForge"


class Settings(BaseModel):
    """Application settings"""

    # Paths
    data_dir: Path = Field(default_factory=lambda: Path(user_data_dir(APP_NAME, APP_AUTHOR)))
    config_dir: Path = Field(default_factory=lambda: Path(user_config_dir(APP_NAME, APP_AUTHOR)))
    output_dir: Optional[Path] = None
    db_path: Optional[Path] = None

    # AI Model settings
    default_model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4000

    # Security
    encrypt_prompts: bool = True

    def __init__(self, **data):
        super().__init__(**data)

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        if self.output_dir is None:
            self.output_dir = self.data_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set database path
        if self.db_path is None:
            self.db_path = self.data_dir / "history.db"

    def get_bundle_dir(self, bundle_id: str) -> Path:
        """Get directory for a specific bundle"""
        bundle_dir = self.data_dir / "bundles" / bundle_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        return bundle_dir


# Global settings instance
settings = Settings()
