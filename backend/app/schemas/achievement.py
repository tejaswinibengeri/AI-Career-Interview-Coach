"""
Pydantic schemas for Achievements and Badges System (Module 18).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AchievementResponse(BaseModel):
    """Schema for individual user achievement with progress and earned status."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    icon: str
    category: str
    threshold: int
    current_progress: int = 0
    is_earned: bool = False
    earned_at: datetime | None = None


class AchievementSummaryResponse(BaseModel):
    """Aggregate achievements progress for authenticated user."""

    total_achievements: int
    earned_count: int
    completion_percentage: float
    achievements: list[AchievementResponse] = Field(default_factory=list)
