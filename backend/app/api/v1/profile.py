"""
User Profile API endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import (
    APIEnvelope,
    ChangePasswordRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.services.profile_service import (
    change_user_password,
    get_or_create_profile,
    update_user_profile,
)

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get(
    "",
    response_model=APIEnvelope[ProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user's profile",
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ProfileResponse]:
    """Retrieve career profile details for the authenticated user."""
    profile = await get_or_create_profile(db, current_user.id)

    return APIEnvelope(
        status="success",
        message="Profile retrieved successfully.",
        data=ProfileResponse.model_validate(profile),
    )


@router.put(
    "",
    response_model=APIEnvelope[ProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Update current user's profile and basic info",
)
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ProfileResponse]:
    """Update profile attributes and/or name for the authenticated user."""
    profile = await update_user_profile(db, current_user, data)

    return APIEnvelope(
        status="success",
        message="Profile updated successfully.",
        data=ProfileResponse.model_validate(profile),
    )


@router.put(
    "/password",
    response_model=APIEnvelope[None],
    status_code=status.HTTP_200_OK,
    summary="Change password for current user",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[None]:
    """Verify current password and update to new password."""
    await change_user_password(
        db,
        user=current_user,
        current_password=data.current_password,
        new_password=data.new_password,
    )

    return APIEnvelope(
        status="success",
        message="Password updated successfully.",
        data=None,
    )
