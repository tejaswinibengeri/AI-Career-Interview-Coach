"""
Pydantic schemas for authentication and user profile operations.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class APIEnvelope(BaseModel, Generic[T]):
    """Standard API response envelope."""

    status: str = "success"
    message: str = "Operation completed successfully"
    data: T | None = None


# --- Auth Request Schemas ---


class UserRegisterRequest(BaseModel):
    """Payload for user registration."""

    name: str = Field(..., min_length=1, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 characters)")


class UserLoginRequest(BaseModel):
    """Payload for user login."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=1, description="Account password")


class ForgotPasswordRequest(BaseModel):
    """Payload for initiating password reset."""

    email: EmailStr = Field(..., description="Account email address")


class ResetPasswordRequest(BaseModel):
    """Payload for resetting password with a token."""

    token: str = Field(..., min_length=1, description="Password reset token")
    new_password: str = Field(..., min_length=6, max_length=128, description="New password (min 6 characters)")


class ChangePasswordRequest(BaseModel):
    """Payload for updating password from profile settings."""

    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=6, max_length=128, description="New password (min 6 characters)")


# --- Profile Schemas ---


class ProfileUpdateRequest(BaseModel):
    """Payload for editing profile information."""

    name: str | None = Field(None, min_length=1, max_length=255, description="User full name")
    education: str | None = Field(None, max_length=255, description="University / Institution")
    degree: str | None = Field(None, max_length=255, description="Degree / Major")
    graduation_year: int | None = Field(None, ge=1950, le=2100, description="Graduation year")
    experience: str | None = Field(None, max_length=255, description="Years / level of experience")
    current_role: str | None = Field(None, max_length=255, description="Current title or status")
    target_role: str | None = Field(None, max_length=255, description="Aspirations / target title")
    skills: list[str] | None = Field(None, description="List of technical/soft skills")
    preferred_location: str | None = Field(None, max_length=255, description="Preferred work city or country")
    work_preference: str | None = Field(None, max_length=50, description="Remote / Hybrid / On-site")
    career_goal: str | None = Field(None, description="Detailed career goals and aspirations")


class ProfileResponse(BaseModel):
    """User profile data returned to client."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    education: str | None = None
    degree: str | None = None
    graduation_year: int | None = None
    experience: str | None = None
    current_role: str | None = None
    target_role: str | None = None
    skills: list[str] = Field(default_factory=list)
    preferred_location: str | None = None
    work_preference: str | None = None
    career_goal: str | None = None
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    """User account details."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: str = "user"
    is_superuser: bool = False
    is_active: bool
    created_at: datetime
    profile: ProfileResponse | None = None


class TokenResponse(BaseModel):
    """JWT authorization token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ForgotPasswordResponse(BaseModel):
    """Response payload for forgot password request."""

    email: str
    reset_token: str | None = None  # Returned for testability/architecture demonstration
