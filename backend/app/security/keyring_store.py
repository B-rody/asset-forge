"""
Secure API key storage using encrypted file storage
Uses Fernet (AES-128) encryption via CryptoManager
"""

from typing import Optional
from pathlib import Path
from app.logger import setup_logger
from app.security.crypto import crypto
from app.settings import settings

logger = setup_logger(__name__)

# Encrypted API key file location
API_KEY_FILE = settings.config_dir / ".api_key.enc"


class KeyringStore:
    """Manages secure storage of API keys using encrypted file storage"""

    @staticmethod
    def save_api_key(api_key: str) -> bool:
        """Save API key to encrypted file"""
        try:
            # Ensure config directory exists
            settings.config_dir.mkdir(parents=True, exist_ok=True)

            # Encrypt and save
            encrypted = crypto.encrypt(api_key)
            API_KEY_FILE.write_bytes(encrypted)

            logger.info("API key saved to encrypted storage")
            return True
        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
            return False

    @staticmethod
    def get_api_key() -> Optional[str]:
        """Retrieve API key from encrypted file"""
        try:
            if not API_KEY_FILE.exists():
                return None

            # Read and decrypt
            encrypted = API_KEY_FILE.read_bytes()
            api_key = crypto.decrypt(encrypted)

            logger.info("API key retrieved from encrypted storage")
            return api_key
        except Exception as e:
            logger.error(f"Failed to retrieve API key: {e}")
            return None

    @staticmethod
    def delete_api_key() -> bool:
        """Delete API key from encrypted file"""
        try:
            if API_KEY_FILE.exists():
                API_KEY_FILE.unlink()
                logger.info("API key deleted from encrypted storage")
            return True
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False

    @staticmethod
    def has_api_key() -> bool:
        """Check if API key exists in encrypted storage"""
        return API_KEY_FILE.exists()


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
        import httpx
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

    # Configure extended timeout for long-running operations
    # Researcher agent with web_search can take 10+ minutes
    # Using httpx.Timeout for granular control:
    # - connect: 10s (time to establish connection)
    # - read: 15 minutes (time to receive response - important for streaming)
    # - write: 30s (time to send request)
    # - pool: 10s (time to acquire connection from pool)
    timeout = httpx.Timeout(
        connect=10.0,
        read=900.0,  # 15 minutes for long-running researcher operations
        write=30.0,
        pool=10.0
    )

    # max_retries=3 ensures transient network errors are retried
    return OpenAI(
        api_key=api_key,
        timeout=timeout,
        max_retries=3  # Retry transient connection errors
    )
