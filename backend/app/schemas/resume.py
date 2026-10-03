"""
Pydantic schemas for Resume management and Version History (Module 16).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ResumeVersionResponse(BaseModel):
    """Details of a single uploaded version of a resume."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    version_number: int
    filename: str
    file_size: int
    file_type: str
    mime_type: str
    extracted_text: str | None = None
    is_current: bool
    created_at: datetime


class ResumeResponse(BaseModel):
    """Details of a resume entity with current version and version history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    current_version: ResumeVersionResponse | None = None
    versions: list[ResumeVersionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ResumeVersionHistoryItem(BaseModel):
    """Detailed history record for a single resume version."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    version_number: int
    filename: str
    file_size: int
    file_type: str
    mime_type: str
    is_current: bool
    ats_score: float | None = None
    skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    created_at: datetime


class ResumeVersionHistoryResponse(BaseModel):
    """Detailed resume version history with real score trajectory."""

    resume_id: int
    title: str
    total_versions: int
    score_improvement: float | None = None
    versions: list[ResumeVersionHistoryItem] = Field(default_factory=list)


class ResumeVersionComparisonResponse(BaseModel):
    """Comparison result between two resume versions."""

    resume_id: int
    v1_version_id: int
    v1_version_number: int
    v1_filename: str
    v1_ats_score: float | None = None
    v1_skills: list[str] = Field(default_factory=list)

    v2_version_id: int
    v2_version_number: int
    v2_filename: str
    v2_ats_score: float | None = None
    v2_skills: list[str] = Field(default_factory=list)

    ats_score_delta: float | None = None
    added_skills: list[str] = Field(default_factory=list)
    removed_skills: list[str] = Field(default_factory=list)
    resolved_missing_keywords: list[str] = Field(default_factory=list)
