"""
Pydantic schemas for Personal Trainer requests and responses.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


# --- Request Schemas ---

class TrainingPlanCreateRequest(BaseModel):
    """Payload to investigate goal and create a personalized day-by-day training plan."""

    goal_dimensions: list[str] = Field(
        default_factory=lambda: ["role"],
        description="Selected dimensions: ['skill'], ['role'], ['company'], or combinations",
    )
    target_skill: str | None = Field(None, description="Target skill, e.g. 'Python', 'FastAPI'")
    target_role: str | None = Field(None, description="Target role, e.g. 'AI Engineer'")
    target_company: str | None = Field(None, description="Target company, e.g. 'Google'")
    current_skills: list[str] = Field(
        default_factory=list,
        description="List of verified existing skills or extracted from resume",
    )
    experience_level: str = Field(
        default="Intermediate",
        description="Beginner, Intermediate, Advanced, or 'AI Estimate'",
    )
    daily_hours: float = Field(
        default=2.0,
        ge=0.5,
        le=12.0,
        description="Available study hours per day (e.g. 0.5, 1, 2, 3, 4, 5)",
    )
    target_deadline: str | None = Field(
        None,
        description="Optional target deadline in YYYY-MM-DD format",
    )
    learning_preference: str = Field(
        default="Balanced",
        description="Theory + Practice, Mostly Practical, Interview Focused, Project Based, Balanced",
    )


class TaskStatusUpdateRequest(BaseModel):
    """Payload to update an individual task's status or notes."""

    status: str = Field(
        ...,
        description="Status: 'not_started', 'in_progress', 'completed', 'skipped', 'rescheduled'",
    )
    notes: str | None = Field(None, description="Optional personal note")
    time_spent_minutes: int | None = Field(None, ge=0, description="Actual time spent in minutes")


class RescheduleDayRequest(BaseModel):
    """Payload when user adjusts today's study availability."""

    available_hours: float = Field(
        ...,
        ge=0.25,
        le=12.0,
        description="Adjusted study hours for today (e.g., 1.0)",
    )


class DayReviewRequest(BaseModel):
    """Payload to rate confidence for a day or topic."""

    confidence_rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Confidence score from 1 (lowest) to 5 (highest)",
    )
    feedback: str | None = Field(None, description="Optional reflection or feedback")


class PersonalTrainerSettingsUpdateRequest(BaseModel):
    """Payload to update n8n and daily notification settings."""

    notifications_enabled: bool = Field(default=False)
    preferred_time: str = Field(default="09:00", description="Preferred notification time, e.g., '09:00'")
    notification_channel: str = Field(
        default="email",
        description="Channel: 'email', 'sms', or 'telegram'",
    )


# --- Response Schemas ---

class TrainingTaskResponse(BaseModel):
    """Granular task details."""

    id: int
    day_id: int
    title: str
    description: str | None = None
    task_type: str
    estimated_minutes: int
    status: str
    order_index: int
    is_carried_over: bool = False
    original_day_number: int | None = None
    notes: str | None = None
    time_spent_minutes: int | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TrainingDayResponse(BaseModel):
    """Day details with tasks."""

    id: int
    plan_id: int
    day_number: int
    phase_name: str
    objective: str
    topics: list[str] = Field(default_factory=list)
    expected_outcome: str | None = None
    total_planned_minutes: int
    is_completed: bool
    completed_at: datetime | None = None
    confidence_rating: int | None = None
    ai_review_recommendation: str | None = None
    tasks: list[TrainingTaskResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TrainingPlanResponse(BaseModel):
    """Comprehensive training plan with nested days."""

    id: int
    user_id: int
    title: str
    goal_dimensions: list[str] = Field(default_factory=list)
    target_skill: str | None = None
    target_role: str | None = None
    target_company: str | None = None
    current_skills: list[str] = Field(default_factory=list)
    experience_level: str
    daily_hours: float
    learning_preference: str
    target_deadline: datetime | None = None
    estimated_duration_days: int
    total_learning_hours: float
    overall_progress: float
    is_active: bool
    phases_summary: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    days: list[TrainingDayResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DailyTrainingViewResponse(BaseModel):
    """Dedicated daily training view data."""

    plan_id: int
    goal_title: str
    day_number: int
    total_days: int
    current_day: TrainingDayResponse
    yesterday_summary: dict[str, Any] = Field(default_factory=dict)
    tomorrow_preview: dict[str, Any] | None = None
    daily_ai_summary: str
    available_hours: float
    workload_minutes: int
    available_minutes: int
    buffer_minutes: int
    overall_progress: float

    model_config = ConfigDict(from_attributes=True)


class ResumeSkillsResponse(BaseModel):
    """Extracted skills from existing resume records without duplicate parsing."""

    skills: list[str] = Field(default_factory=list)
    source: str = "resume_analysis"


class PersonalTrainerSettingsResponse(BaseModel):
    """User notification settings and n8n webhook status."""

    notifications_enabled: bool
    preferred_time: str
    notification_channel: str
    webhook_configured: bool


class N8nWebhookTriggerResponse(BaseModel):
    """Response returned when triggering or testing the n8n webhook."""

    success: bool
    message: str
    webhook_configured: bool
    payload: dict[str, Any] | None = None
    webhook_status_code: int | None = None
