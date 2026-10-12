"""
Pydantic schemas for Admin Panel System (Module 20).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminSystemStatsResponse(BaseModel):
    """Real database aggregated system metrics for admin dashboard."""

    total_users: int = 0
    active_users: int = 0
    resumes: int = 0
    interviews: int = 0
    coding_submissions: int = 0
    job_searches: int = 0
    ai_evaluations: int = 0


class AdminUserResponse(BaseModel):
    """User overview for admin management with privacy protection."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    role: str = "user"
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime


class AdminUserRoleUpdate(BaseModel):
    """Payload to update user role or active status."""

    role: str | None = None
    is_active: bool | None = None


class AdminQuestionCreate(BaseModel):
    """Payload to add or edit interview question bank items."""

    category: str
    difficulty: str
    question_text: str
    role: str = "General Software Engineer"
    explanation: str | None = None



class AdminResourceCreate(BaseModel):
    """Payload to add or edit verified learning resource catalog items."""

    title: str
    description: str
    url: str
    skill_name: str
    source: str = "Official Documentation"
    difficulty: str = "Beginner"
    resource_type: str = "Course"


class AdminAuditLogItem(BaseModel):
    """An administrative audit or telemetry event item."""

    timestamp: datetime
    event_type: str
    description: str
    actor: str


class AdminSettingsResponse(BaseModel):
    """Platform operational settings for administrators."""

    app_name: str
    app_version: str
    environment: str
    ollama_model: str
    ollama_base_url: str
    jwt_expiration_minutes: int
    database_url_masked: str
    registration_enabled: bool = True
