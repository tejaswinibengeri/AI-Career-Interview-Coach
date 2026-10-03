"""
Pydantic schemas for AI Project Recommendations System (Module 15).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UpdateProjectStatusRequest(BaseModel):
    """Payload to update saved state or status of a project recommendation."""

    is_saved: bool | None = None
    status: str | None = Field(None, description="Not Started, In Progress, Completed")


class ProjectRecommendationResponse(BaseModel):
    """Response schema for personalized project recommendation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: str
    difficulty: str
    target_role: str | None = None
    technologies: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    skills_learned: list[str] = Field(default_factory=list)
    expected_outcome: str
    is_saved: bool = False
    status: str = "Not Started"
    created_at: datetime
