"""
Authentication API endpoints.
"""

import asyncio
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, security_scheme
from app.core.config import settings
from app.core.security import create_access_token, revoke_token
from app.models.user import User
from app.schemas.user import (
    APIEnvelope,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_password_reset_token,
    register_user,
    reset_password_with_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=APIEnvelope[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[TokenResponse]:
    """Create a new user account, initialize profile, and return an access token."""
    user = await register_user(db, data)
    token = create_access_token({"sub": str(user.id), "email": user.email})

    return APIEnvelope(
        status="success",
        message="Account registered successfully.",
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        ),
    )


@router.post(
    "/login",
    response_model=APIEnvelope[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate user credentials",
)
async def login(
    data: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[TokenResponse]:
    """Validate user credentials and return a signed JWT access token."""
    user = await authenticate_user(db, data)
    token = create_access_token({"sub": str(user.id), "email": user.email})

    return APIEnvelope(
        status="success",
        message="Login successful.",
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        ),
    )


@router.post(
    "/logout",
    response_model=APIEnvelope[None],
    status_code=status.HTTP_200_OK,
    summary="Log out of current session",
)
async def logout(
    auth_header: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> APIEnvelope[None]:
    """Revoke current JWT access token on server and acknowledge user logout."""
    if auth_header and auth_header.credentials:
        revoke_token(auth_header.credentials)

    return APIEnvelope(
        status="success",
        message="Logged out successfully.",
        data=None,
    )


@router.get(
    "/me",
    response_model=APIEnvelope[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> APIEnvelope[UserResponse]:
    """Return user data and profile for the authenticated bearer token."""
    return APIEnvelope(
        status="success",
        message="Current user profile retrieved.",
        data=UserResponse.model_validate(current_user),
    )


@router.post(
    "/forgot-password",
    response_model=APIEnvelope[ForgotPasswordResponse],
    status_code=status.HTTP_200_OK,
    summary="Request a password reset token",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ForgotPasswordResponse]:
    """Generate a password reset token for the given account email.
    
    Protects against user enumeration and does not leak reset tokens in production.
    """
    user, token = await create_password_reset_token(db, data.email)

    if user and token and settings.SMTP_ENABLED:
        from app.services.email_service import send_email
        reset_link = f"http://localhost:5173/reset-password?token={token}"
        email_html = (
            f"<div style='font-family: sans-serif;'>"
            f"<h2>Password Reset Request</h2>"
            f"<p>Hello {user.name},</p>"
            f"<p>We received a request to reset your password for your account.</p>"
            f"<p><a href='{reset_link}' style='padding: 10px 18px; background: #6366f1; color: white; border-radius: 8px; text-decoration: none;'>Reset My Password</a></p>"
            f"<p>Or copy this link: {reset_link}</p>"
            f"<p>This token will expire in 1 hour.</p>"
            f"</div>"
        )
        asyncio.create_task(send_email(user.email, "Password Reset Instructions", email_html))

    # Security: In production, NEVER expose the reset token in the HTTP API response.
    # In development / test environments, allow local verification and test suite flow.
    is_production = settings.ENVIRONMENT.lower() == "production"
    safe_token = None if is_production else token

    return APIEnvelope(
        status="success",
        message="If an account with this email address exists, password reset instructions have been dispatched.",
        data=ForgotPasswordResponse(
            email=data.email,
            reset_token=safe_token,
        ),
    )


@router.post(
    "/reset-password",
    response_model=APIEnvelope[None],
    status_code=status.HTTP_200_OK,
    summary="Reset password using a valid token",
)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[None]:
    """Reset user password using token received via reset flow."""
    await reset_password_with_token(db, data.token, data.new_password)

    return APIEnvelope(
        status="success",
        message="Password has been successfully reset. You may now log in.",
        data=None,
    )
