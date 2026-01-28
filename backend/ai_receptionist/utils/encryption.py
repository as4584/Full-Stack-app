"""
Encryption utilities for secure token storage.

Uses Fernet symmetric encryption for encrypting OAuth tokens.
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


def _get_encryption_key() -> bytes:
    """
    Get or generate encryption key for token storage.
    
    Uses ENCRYPTION_KEY env var if set, otherwise generates from ADMIN_PRIVATE_KEY.
    For production, set a dedicated ENCRYPTION_KEY environment variable.
    
    Returns:
        32-byte encryption key suitable for Fernet
    """
    # Check for dedicated encryption key
    encryption_key = os.environ.get("ENCRYPTION_KEY")
    if encryption_key:
        # Decode if base64, otherwise derive from string
        try:
            key_bytes = base64.urlsafe_b64decode(encryption_key)
            if len(key_bytes) == 32:
                return encryption_key.encode()
        except Exception:
            pass
    
    # Fallback: derive from ADMIN_PRIVATE_KEY
    secret = os.environ.get("ADMIN_PRIVATE_KEY", "default-dev-secret-change-in-production")
    
    # Use PBKDF2 to derive a proper 32-byte key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ai-receptionist-oauth",  # Static salt for consistency
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


def encrypt_token(token: str) -> str:
    """
    Encrypt a token for secure storage.
    
    Args:
        token: Plain text token to encrypt
        
    Returns:
        Base64-encoded encrypted token
    """
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(token.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Token encryption failed: {e}")
        raise


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a stored token.
    
    Args:
        encrypted_token: Base64-encoded encrypted token
        
    Returns:
        Decrypted plain text token
    """
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Token decryption failed: {e}")
        raise


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.
    
    Use this to generate an ENCRYPTION_KEY for your .env file.
    
    Returns:
        Base64-encoded 32-byte key
    """
    return Fernet.generate_key().decode()
