"""
Profile management and password update business logic.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import get_password_hash, verify_password
from app.models.user import Profile, User
from app.schemas.user import ProfileUpdateRequest


async def get_or_create_profile(db: AsyncSession, user_id: int) -> Profile:
    """Retrieve profile for a user ID or create an empty one if missing."""
    query = select(Profile).where(Profile.user_id == user_id)
    result = await db.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        profile = Profile(user_id=user_id, skills=[])
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return profile


async def update_user_profile(
    db: AsyncSession, user: User, data: ProfileUpdateRequest
) -> Profile:
    """Update profile attributes and user name.

    Returns:
        The updated Profile instance.
    """
    profile = await get_or_create_profile(db, user.id)

    # Update user name if passed
    if data.name is not None:
        user.name = data.name.strip()

    # Update non-null profile fields
    if data.education is not None:
        profile.education = data.education
    if data.degree is not None:
        profile.degree = data.degree
    if data.graduation_year is not None:
        profile.graduation_year = data.graduation_year
    if data.experience is not None:
        profile.experience = data.experience
    if data.current_role is not None:
        profile.current_role = data.current_role
    if data.target_role is not None:
        profile.target_role = data.target_role
    if data.skills is not None:
        profile.skills = data.skills
    if data.preferred_location is not None:
        profile.preferred_location = data.preferred_location
    if data.work_preference is not None:
        profile.work_preference = data.work_preference
    if data.career_goal is not None:
        profile.career_goal = data.career_goal

    await db.commit()
    await db.refresh(profile)
    await db.refresh(user)
    return profile


async def change_user_password(
    db: AsyncSession, user: User, current_password: str, new_password: str
) -> None:
    """Change the user's password after verifying the existing password.

    Raises:
        AppException: If current password is incorrect.
    """
    if not verify_password(current_password, user.hashed_password):
        raise AppException(
            message="Current password is incorrect.",
            status_code=400,
        )

    if current_password == new_password:
        raise AppException(
            message="New password must be different from current password.",
            status_code=400,
        )

    user.hashed_password = get_password_hash(new_password)
    await db.commit()
    await db.refresh(user)
