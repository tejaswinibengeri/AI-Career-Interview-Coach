"""
Pydantic schemas for Learning Resources System (Module 14).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ToggleProgressRequest(BaseModel):
    """Payload to toggle saved or completed state for a learning resource."""

    is_saved: bool | None = None
    is_completed: bool | None = None


class LearningResourceResponse(BaseModel):
    """Full learning resource response schema with user progress state."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    url: str
    source: str
    resource_type: str
    skill_name: str
    difficulty: str
    estimated_hours: int | None = None
    is_verified: bool = True
    is_saved: bool = False
    is_completed: bool = False
    is_recommended_for_gap: bool = False
    created_at: datetime
