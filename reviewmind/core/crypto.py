"""
Symmetric encryption for secrets we store on a user's behalf (e.g. their
GitHub OAuth token in Supabase's profiles table). Encrypted at the app
layer so the ciphertext, not the raw token, is what ever reaches the
database — a leaked service-role key or DB dump doesn't hand over usable
GitHub credentials.
"""

from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from reviewmind.core.config import settings
from reviewmind.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    if not settings.token_encryption_key:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY is not set. Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(settings.token_encryption_key.encode())


def encrypt_token(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(value: str) -> str:
    """Decrypt a stored token.

    Tokens saved before encryption was introduced are still plaintext in
    the database — fall back to returning them as-is rather than locking
    those users out, so they keep working until they re-save a token
    (which then gets encrypted going forward).
    """
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        logger.warning("token_decrypt_fallback_to_plaintext")
        return value
