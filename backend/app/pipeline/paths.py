"""
Utility for managing file paths in the pipeline
"""

from pathlib import Path
from app.settings import settings


def get_prompts_dir() -> Path:
    """Get the prompts directory"""
    return Path(__file__).parent.parent / "prompts" / "blobs"


def get_schemas_dir() -> Path:
    """Get the schemas directory"""
    return Path(__file__).parent.parent / "schemas"


def get_bundle_dir(bundle_id: str) -> Path:
    """Get directory for a specific bundle"""
    return settings.get_bundle_dir(bundle_id)
