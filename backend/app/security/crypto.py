"""
Encryption utilities for protecting prompts and sensitive data
Uses Fernet (symmetric encryption with AES-128)
"""

from cryptography.fernet import Fernet
import os
from pathlib import Path
from app.settings import settings


class CryptoManager:
    """Manages encryption/decryption of sensitive data"""
    
    def __init__(self):
        self._cipher = None
        self._load_or_create_key()
    
    def _load_or_create_key(self):
        """Load or create encryption key"""
        key_file = settings.config_dir / ".key"
        
        if key_file.exists():
            # Load existing key
            key = key_file.read_bytes()
        else:
            # Generate new key
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            # Make key file read-only
            os.chmod(key_file, 0o600)
        
        self._cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt string to bytes"""
        return self._cipher.encrypt(plaintext.encode('utf-8'))
    
    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt bytes to string"""
        return self._cipher.decrypt(ciphertext).decode('utf-8')
    
    def encrypt_file(self, input_path: Path, output_path: Path):
        """Encrypt file contents"""
        plaintext = input_path.read_bytes()
        ciphertext = self._cipher.encrypt(plaintext)
        output_path.write_bytes(ciphertext)
    
    def decrypt_file(self, input_path: Path) -> bytes:
        """Decrypt file contents"""
        ciphertext = input_path.read_bytes()
        return self._cipher.decrypt(ciphertext)


# Global crypto manager instance
crypto = CryptoManager()
