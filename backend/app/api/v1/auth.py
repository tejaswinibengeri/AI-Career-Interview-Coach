"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token
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
async def logout() -> APIEnvelope[None]:
    """Acknowledge user logout (JWT is statelessly invalidated on client)."""
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
    """Generate a password reset token for the given account email."""
    user, token = await create_password_reset_token(db, data.email)

    return APIEnvelope(
        status="success",
        message="Password reset instructions generated successfully.",
        data=ForgotPasswordResponse(
            email=user.email,
            reset_token=token,
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
