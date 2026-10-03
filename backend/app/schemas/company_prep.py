"""
Pydantic schemas for Company-Specific Preparation System (Module 13).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class GenerateCompanyPrepRequest(BaseModel):
    """Request payload to generate company interview prep plan."""

    company_name: str = Field(..., min_length=2, max_length=100, description="Target company name")
    target_role: str = Field(..., min_length=2, max_length=100, description="Target job role")


class PracticeQuestionItem(BaseModel):
    """Practice question with mandatory AI-generated label."""

    question_text: str
    category: str = "Technical"  # Technical, System Design, Behavioral, Coding, HR
    difficulty: str = "Medium"
    label: str = Field("AI-generated practice question", description="Mandatory question source label")
    sample_answer_points: list[str] = Field(default_factory=list)


class TechnicalTopicItem(BaseModel):
    """Technical preparation topic."""

    topic: str
    description: str
    importance: str = "High"


class BehavioralPrepItem(BaseModel):
    """Behavioral framework guidance."""

    principle: str
    advice: str
    example_prompt: str


class CompanyPrepResponse(BaseModel):
    """Full company preparation plan response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    company_name: str
    target_role: str
    is_verified_company: bool
    verification_notes: str | None = None

    company_overview: str
    role_summary: str

    required_skills: list[str] = Field(default_factory=list)
    technical_prep_topics: list[dict] = Field(default_factory=list)
    coding_topics: list[str] = Field(default_factory=list)
    hr_topics: list[str] = Field(default_factory=list)
    behavioral_prep: list[dict] = Field(default_factory=list)
    practice_questions: list[dict] = Field(default_factory=list)

    created_at: datetime
