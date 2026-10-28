"""
Authentication business logic and database interactions.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.core.security import (
    generate_reset_token,
    get_password_hash,
    verify_password,
)
from app.models.user import Profile, User
from app.schemas.user import UserLoginRequest, UserRegisterRequest


async def register_user(db: AsyncSession, data: UserRegisterRequest) -> User:
    """Register a new user account and initialize an empty profile.

    Raises:
        AppException: If email already exists.
    """
    normalized_email = data.email.strip().lower()

    # Check for existing email
    query = select(User).where(User.email == normalized_email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise AppException(
            message="An account with this email address already exists.",
            status_code=400,
        )

    # Hash password & construct user entity
    hashed_password = get_password_hash(data.password)
    user = User(
        email=normalized_email,
        name=data.name.strip(),
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create associated profile
    profile = Profile(
        user_id=user.id,
        skills=[],
    )
    db.add(profile)
    await db.commit()

    # Reload user with profile relationship eagerly loaded
    refreshed_user = await get_user_by_id(db, user.id)
    return refreshed_user or user


async def authenticate_user(db: AsyncSession, data: UserLoginRequest) -> User:
    """Validate user credentials and return the User instance.

    Raises:
        AppException: If invalid credentials or user is inactive.
    """
    normalized_email = data.email.strip().lower()

    query = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.email == normalized_email)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise AppException(
            message="Invalid email or password.",
            status_code=401,
        )

    if not user.is_active:
        raise AppException(
            message="Your account has been deactivated.",
            status_code=403,
        )

    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Retrieve user with profile by primary key ID."""
    query = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == user_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_password_reset_token(db: AsyncSession, email: str) -> tuple[User | None, str | None]:
    """Generate and persist a password reset token for a user if they exist.

    Returns:
        tuple[User | None, str | None]: The user and generated token if found, else (None, None).
    """
    normalized_email = email.strip().lower()
    query = select(User).where(User.email == normalized_email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        return None, None

    token = generate_reset_token()
    user.reset_token = token
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    await db.commit()
    await db.refresh(user)
    return user, token


async def reset_password_with_token(
    db: AsyncSession, token: str, new_password: str
) -> User:
    """Validate reset token and update user's password.

    Raises:
        AppException: If token is invalid or expired.
    """
    query = select(User).where(User.reset_token == token.strip())
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.reset_token_expires_at:
        raise AppException(
            message="Invalid or expired reset token.",
            status_code=400,
        )

    # Check token expiration
    now = datetime.now(timezone.utc)
    # Ensure timezone awareness comparison
    token_expiry = user.reset_token_expires_at
    if token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=timezone.utc)

    if token_expiry < now:
        raise AppException(
            message="Password reset token has expired. Please request a new one.",
            status_code=400,
        )

    # Update password and clear reset token
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires_at = None

    await db.commit()
    await db.refresh(user)
    return user


async def seed_demo_users_if_empty(db: AsyncSession) -> None:
    """Ensure standard demo candidates exist for effortless testing/evaluation."""
    demo_email = "demo@example.com"
    query = select(User).where(User.email == demo_email)
    result = await db.execute(query)
    demo_user = result.scalar_one_or_none()

    if not demo_user:
        hashed = get_password_hash("Password123!")
        demo = User(
            email=demo_email,
            name="Demo Candidate",
            hashed_password=hashed,
            is_active=True,
            role="user",
            is_superuser=False,
        )
        db.add(demo)
        await db.flush()

        profile = Profile(
            user_id=demo.id,
            target_role="Full Stack Engineer",
            current_role="Junior Developer",
            education="Bachelor of Technology in Computer Science",
            degree="B.Tech",
            graduation_year=2024,
            experience="1 year",
            preferred_location="Remote",
            work_preference="Full-time",
            career_goal="Become a Senior Full Stack Engineer specializing in React and Python.",
            skills=["Python", "FastAPI", "React", "TypeScript", "SQL", "Git", "Docker"],
        )
        db.add(profile)
        await db.commit()

    admin_email = "admin@example.com"
    query_admin = select(User).where(User.email == admin_email)
    result_admin = await db.execute(query_admin)
    admin_user = result_admin.scalar_one_or_none()

    if not admin_user:
        hashed_admin = get_password_hash("AdminPassword123!")
        admin = User(
            email=admin_email,
            name="System Administrator",
            hashed_password=hashed_admin,
            is_active=True,
            role="admin",
            is_superuser=True,
        )
        db.add(admin)
        await db.flush()

        admin_profile = Profile(
            user_id=admin.id,
            target_role="Engineering Manager",
            skills=["System Architecture", "Leadership", "Python", "Cloud Infrastructure"],
        )
        db.add(admin_profile)
        await db.commit()

