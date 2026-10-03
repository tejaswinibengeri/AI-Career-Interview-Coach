"""
Pydantic schemas for Real Job Search and Saved Job Bookmarks.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class JobResponse(BaseModel):
    """Normalized job entity response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    provider: str = "adzuna"
    title: str
    company: str
    location: str
    is_remote: bool
    description: str
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = "USD"
    redirect_url: str
    posted_at: datetime | None = None
    is_saved: bool = False
    created_at: datetime


class SaveJobResponse(BaseModel):
    """Saved job response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    job_id: int
    saved_at: datetime
    job: JobResponse
