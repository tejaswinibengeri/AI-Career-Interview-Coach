"""
FastAPI dependency injection functions.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import decode_access_token, is_token_revoked
from app.db.session import get_async_session
from app.models.user import User
from app.services.auth_service import get_user_by_id

security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session via dependency injection."""
    async for session in get_async_session():
        yield session


async def get_current_user(
    auth_header: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate JWT bearer token and return authenticated User model.

    Raises:
        AppException: 401 if missing, invalid, or expired token; 403 if deactivated.
    """
    if not auth_header or not auth_header.credentials:
        raise AppException(
            message="Authentication credentials were not provided.",
            status_code=401,
        )

    token = auth_header.credentials
    if is_token_revoked(token):
        raise AppException(
            message="Token has been revoked or session logged out.",
            status_code=401,
        )
    try:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise AppException(
                message="Invalid authentication credentials.",
                status_code=401,
            )
        user_id = int(user_id_raw)
    except (JWTError, ValueError):
        raise AppException(
            message="Invalid or expired token.",
            status_code=401,
        )

    user = await get_user_by_id(db, user_id)
    if not user:
        raise AppException(
            message="User associated with this token was not found.",
            status_code=401,
        )

    if not user.is_active:
        raise AppException(
            message="User account is deactivated.",
            status_code=403,
        )

    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce admin authorization requirement.

    Raises:
        AppException: 403 Forbidden if current user is not an admin.
    """
    if not (current_user.is_superuser or getattr(current_user, "role", "user") == "admin"):
        raise AppException(
            message="Forbidden: Admin authorization required.",
            status_code=403,
        )
    return current_user

