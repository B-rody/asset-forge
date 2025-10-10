"""
User Preferences Configuration Store
Manages persistent user preferences in a JSON config file
"""

import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from app.logger import setup_logger

logger = setup_logger(__name__)

# Thread lock for file operations
_lock = threading.Lock()


def get_preferences_file(config_dir: Path) -> Path:
    """
    Get path to preferences.json file

    Args:
        config_dir: Configuration directory path
    """
    return config_dir / "preferences.json"


def load_preferences(config_dir: Path) -> Dict[str, Any]:
    """
    Load all preferences from config file

    Args:
        config_dir: Configuration directory path

    Returns:
        Dictionary of preferences, empty dict if file doesn't exist
    """
    prefs_file = get_preferences_file(config_dir)

    with _lock:
        try:
            if not prefs_file.exists():
                logger.debug(f"Preferences file not found at {prefs_file}")
                return {}

            with open(prefs_file, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
                logger.debug(f"Loaded preferences: {list(prefs.keys())}")
                return prefs

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse preferences file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load preferences: {e}")
            return {}


def save_preferences(config_dir: Path, preferences: Dict[str, Any]) -> bool:
    """
    Save all preferences to config file

    Args:
        config_dir: Configuration directory path
        preferences: Dictionary of preferences to save

    Returns:
        True if successful, False otherwise
    """
    prefs_file = get_preferences_file(config_dir)

    with _lock:
        try:
            # Ensure parent directory exists
            prefs_file.parent.mkdir(parents=True, exist_ok=True)

            # Write with pretty formatting
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved preferences to {prefs_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            return False


def get_preference(config_dir: Path, key: str, default: Any = None) -> Any:
    """
    Get a specific preference value

    Args:
        config_dir: Configuration directory path
        key: Preference key
        default: Default value if key doesn't exist

    Returns:
        Preference value or default
    """
    prefs = load_preferences(config_dir)
    value = prefs.get(key, default)
    logger.debug(f"Get preference '{key}': {value}")
    return value


def save_preference(config_dir: Path, key: str, value: Any) -> bool:
    """
    Save a specific preference value

    Args:
        config_dir: Configuration directory path
        key: Preference key
        value: Value to save

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Saving preference '{key}': {value}")
    prefs = load_preferences(config_dir)
    prefs[key] = value
    return save_preferences(config_dir, prefs)


def delete_preference(config_dir: Path, key: str) -> bool:
    """
    Delete a specific preference

    Args:
        config_dir: Configuration directory path
        key: Preference key to delete

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Deleting preference '{key}'")
    prefs = load_preferences(config_dir)

    if key in prefs:
        del prefs[key]
        return save_preferences(config_dir, prefs)

    return True  # Already doesn't exist, consider success
