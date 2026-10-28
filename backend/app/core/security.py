"""
JWT and password hashing security utilities.
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Thread-safe in-memory token revocation blacklist with automatic TTL cleanup
_revoked_tokens: dict[str, float] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash of the password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def generate_reset_token() -> str:
    """Generate a secure random string for password reset tokens."""
    return secrets.token_urlsafe(32)


def revoke_token(token: str) -> None:
    """Revoke a JWT token by hashing it and recording its expiration timestamp."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        exp = float(payload.get("exp", time.time() + 1800))
    except Exception:
        exp = time.time() + 1800

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    _revoked_tokens[token_hash] = exp
    _cleanup_revoked_tokens()


def is_token_revoked(token: str) -> bool:
    """Check if token hash exists in the revoked blacklist."""
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    exp = _revoked_tokens.get(token_hash)
    if exp is None:
        return False
    if time.time() > exp:
        _revoked_tokens.pop(token_hash, None)
        return False
    return True


def _cleanup_revoked_tokens() -> None:
    """Prune expired tokens from the revocation store."""
    now = time.time()
    expired = [k for k, exp in _revoked_tokens.items() if now > exp]
    for k in expired:
        _revoked_tokens.pop(k, None)
