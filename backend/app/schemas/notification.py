"""
Pydantic schemas for Notifications and Notification Preferences (Module 19).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    """Schema for individual in-app notification."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    type: str
    link_url: str | None = None
    is_read: bool = False
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Response containing notification list and unread counter."""

    unread_count: int
    notifications: list[NotificationResponse] = Field(default_factory=list)


class NotificationPreferenceRequest(BaseModel):
    """Payload to update notification preferences."""

    enable_roadmap_reminders: bool | None = None
    enable_interview_reminders: bool | None = None
    enable_coding_reminders: bool | None = None
    enable_resume_suggestions: bool | None = None
    enable_learning_milestones: bool | None = None


class NotificationPreferenceResponse(BaseModel):
    """Schema for user notification preferences."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    enable_roadmap_reminders: bool = True
    enable_interview_reminders: bool = True
    enable_coding_reminders: bool = True
    enable_resume_suggestions: bool = True
    enable_learning_milestones: bool = True
    created_at: datetime
    updated_at: datetime
