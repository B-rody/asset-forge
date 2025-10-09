"""
Secure API key storage using OS keyring
Windows: Credential Manager
macOS: Keychain
Linux: Secret Service API
"""

import keyring
from typing import Optional
from app.logger import setup_logger

logger = setup_logger(__name__)

SERVICE_NAME = "AssetForge"
KEY_NAME = "openai_api_key"


class KeyringStore:
    """Manages secure storage of API keys"""
    
    @staticmethod
    def save_api_key(api_key: str) -> bool:
        """Save API key to system keyring"""
        try:
            keyring.set_password(SERVICE_NAME, KEY_NAME, api_key)
            logger.info("API key saved to system keyring")
            return True
        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
            return False
    
    @staticmethod
    def get_api_key() -> Optional[str]:
        """Retrieve API key from system keyring"""
        try:
            api_key = keyring.get_password(SERVICE_NAME, KEY_NAME)
            if api_key:
                logger.info("API key retrieved from system keyring")
            return api_key
        except Exception as e:
            logger.error(f"Failed to retrieve API key: {e}")
            return None
    
    @staticmethod
    def delete_api_key() -> bool:
        """Delete API key from system keyring"""
        try:
            keyring.delete_password(SERVICE_NAME, KEY_NAME)
            logger.info("API key deleted from system keyring")
            return True
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False
    
    @staticmethod
    def has_api_key() -> bool:
        """Check if API key exists in keyring"""
        return KeyringStore.get_api_key() is not None


# Convenience functions
def save_api_key(api_key: str) -> bool:
    """Save API key to keyring"""
    return KeyringStore.save_api_key(api_key)


def get_api_key() -> Optional[str]:
    """Get API key from keyring"""
    return KeyringStore.get_api_key()


def delete_api_key() -> bool:
    """Delete API key from keyring"""
    return KeyringStore.delete_api_key()


def has_api_key() -> bool:
    """Check if API key exists"""
    return KeyringStore.has_api_key()


def get_openai_client():
    """
    Get configured OpenAI client with API key from keyring.

    Returns:
        OpenAI: Configured client instance

    Raises:
        ValueError: If no API key is found in keyring
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI package not installed. Run: pip install openai"
        )

    api_key = get_api_key()
    if not api_key:
        raise ValueError(
            "No API key found in system keyring. "
            "Please configure your OpenAI API key in Settings."
        )

    logger.info("Creating OpenAI client with key from keyring")
    return OpenAI(api_key=api_key)
