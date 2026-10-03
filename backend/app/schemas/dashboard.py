"""
Pydantic schemas for the User Dashboard aggregation endpoint.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ProfileSummary(BaseModel):
    """Real profile data summary and calculated completion rate."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    email: str
    current_role: str | None = None
    target_role: str | None = None
    education: str | None = None
    degree: str | None = None
    graduation_year: int | None = None
    experience: str | None = None
    preferred_location: str | None = None
    work_preference: str | None = None
    completion_percentage: int = Field(
        ..., ge=0, le=100, description="Dynamically calculated profile completion percentage"
    )


class ResumeSummary(BaseModel):
    """Resume analysis summary (supports real values and empty state)."""

    model_config = ConfigDict(from_attributes=True)

    has_resume: bool = False
    filename: str | None = None
    uploaded_at: datetime | None = None
    latest_ats_score: float | None = None
    status: str = "no_resume"  # "no_resume", "uploaded", "analyzed"


class SkillProgressSummary(BaseModel):
    """Real skills list extracted from profile."""

    model_config = ConfigDict(from_attributes=True)

    total_skills: int = 0
    skills: list[str] = Field(default_factory=list)


class InterviewStatsSummary(BaseModel):
    """Mock interview session statistics (supports real values and empty state)."""

    model_config = ConfigDict(from_attributes=True)

    total_mock_interviews: int = 0
    average_score: float | None = None
    last_interview_date: datetime | None = None


class CodingStatsSummary(BaseModel):
    """Coding practice statistics (supports real values and empty state)."""

    model_config = ConfigDict(from_attributes=True)

    total_problems_solved: int = 0
    streak_days: int = 0
    last_practiced_date: datetime | None = None


class PlacementReadinessSummary(BaseModel):
    """Overall job placement readiness evaluation."""

    model_config = ConfigDict(from_attributes=True)

    readiness_score: float | None = None
    level: str | None = None
    status_message: str = "No assessments completed yet"


class ActivityItem(BaseModel):
    """Individual real timestamped activity event."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    activity_type: str
    title: str
    description: str
    timestamp: datetime


class DashboardResponse(BaseModel):
    """Aggregated dashboard payload with actual user data and explicit empty states."""

    model_config = ConfigDict(from_attributes=True)

    welcome_message: str
    profile: ProfileSummary
    career_goal: str | None = None
    resume: ResumeSummary
    skills: SkillProgressSummary
    interviews: InterviewStatsSummary
    coding: CodingStatsSummary
    placement_readiness: PlacementReadinessSummary
    recent_activity: list[ActivityItem] = Field(default_factory=list)
