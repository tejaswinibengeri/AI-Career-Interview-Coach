"""
Pydantic schemas for Career Intelligence module:
Job Description Analyzer, Resume -> JD Match, and AI Cover Letter.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# --- 1. Job Description Analyzer Schemas ---

class JobDescriptionAnalyzeRequest(BaseModel):
    """Request payload for analyzing a raw job description."""

    job_description: str = Field(..., min_length=20, max_length=50000, description="Raw job description text")


class JobDescriptionAnalysisResponse(BaseModel):
    """Structured extraction results from the supplied job description."""

    job_title: str | None = None
    company: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


# --- 2. Resume -> JD Match Schemas ---

class ResumeJdMatchRequest(BaseModel):
    """Request payload for matching an uploaded resume against a job description."""

    resume_id: int = Field(..., description="ID of the user's uploaded resume")
    job_description: str = Field(..., min_length=20, max_length=50000, description="Job description text")
    job_title: str | None = None
    company_name: str | None = None
    target_occupation_id: int | None = None


class ResumeJdMatchResponse(BaseModel):
    """Evaluation results comparing a candidate's resume to a specific job description."""

    id: int
    resume_id: int | None = None
    resume_title: str
    job_title: str | None = None
    company_name: str | None = None
    job_description_snippet: str | None = None

    # Granular Scores (0 - 100)
    overall_score: float
    skills_score: float
    keyword_score: float
    experience_score: float
    responsibility_score: float

    # Categorized matches
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    partial_matches: list[str] = Field(default_factory=list)
    relevant_experience: list[str] = Field(default_factory=list)
    potential_gaps: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)

    target_occupation_title: str | None = None
    created_at: datetime


class ResumeJdMatchHistoryItem(BaseModel):
    """Compact history representation of a previous match."""

    id: int
    resume_id: int | None = None
    resume_title: str
    job_title: str | None = None
    company_name: str | None = None
    overall_score: float
    skills_score: float
    created_at: datetime


# --- 3. Cover Letter Generator Schemas ---

class CoverLetterGenerateRequest(BaseModel):
    """Request payload for generating an AI cover letter."""

    resume_id: int = Field(..., description="ID of the user's uploaded resume")
    job_description: str = Field(..., min_length=20, max_length=50000, description="Target job description")
    job_title: str = Field(..., min_length=2, max_length=255, description="Target role title")
    company_name: str = Field(..., min_length=1, max_length=255, description="Target company name")
    tone: str = Field(default="Professional", description="Tone: Professional, Confident, Concise")
    length: str = Field(default="Standard", description="Length: Short, Standard, Detailed")


class CoverLetterResponse(BaseModel):
    """AI-generated cover letter response."""

    id: int | None = None
    job_title: str
    company_name: str
    tone: str
    length: str
    content: str
    label: str = "AI-generated cover letter"
    created_at: datetime


class CoverLetterHistoryItem(BaseModel):
    """Compact summary of previously saved cover letters."""

    id: int
    job_title: str
    company_name: str
    tone: str
    length: str
    created_at: datetime


# --- 4. Cold Email Generator Schemas ---

class ColdEmailGenerateRequest(BaseModel):
    """Request payload for generating an AI cold outreach email."""

    job_title: str = Field(..., min_length=1, max_length=255, description="Target role title")
    company_name: str = Field(..., min_length=1, max_length=255, description="Target company name")
    resume_id: int | None = Field(default=None, description="Optional ID of user's uploaded resume")
    match_id: int | None = Field(default=None, description="Optional ID of existing Resume -> JD match to reuse")
    job_description: str | None = Field(default=None, max_length=50000, description="Optional target job description")
    recruiter_name: str | None = Field(default=None, max_length=255, description="Optional recruiter/contact name")
    recruiter_email: str | None = Field(default=None, max_length=255, description="Optional recruiter email")
    company_info: str | None = Field(default=None, max_length=5000, description="Optional company info or news")
    portfolio_url: str | None = Field(default=None, max_length=500, description="Optional portfolio link")
    github_url: str | None = Field(default=None, max_length=500, description="Optional GitHub profile link")
    linkedin_url: str | None = Field(default=None, max_length=500, description="Optional LinkedIn profile link")
    additional_context: str | None = Field(default=None, max_length=5000, description="Optional additional notes/context")
    email_type: str = Field(default="Recruiter Outreach", description="Outreach purpose/type")
    tone: str = Field(default="Professional", description="Tone: Professional, Friendly, Confident, Concise")
    length: str = Field(default="Short", description="Length: Short, Standard")


class ColdEmailUpdateRequest(BaseModel):
    """Request payload for updating an edited cold email."""

    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    recruiter_name: str | None = None
    recruiter_email: str | None = None


class ColdEmailResponse(BaseModel):
    """AI-generated cold outreach email response."""

    id: int | None = None
    job_title: str
    company_name: str
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    email_type: str
    tone: str
    length: str
    subject: str
    body: str
    created_at: datetime


class ColdEmailHistoryItem(BaseModel):
    """Compact summary of previously saved cold emails."""

    id: int
    job_title: str
    company_name: str
    email_type: str
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    subject: str
    created_at: datetime


class ColdEmailRegenerateSubjectRequest(BaseModel):
    """Request payload to generate fresh subject lines."""

    job_title: str = Field(..., min_length=1, max_length=255)
    company_name: str = Field(..., min_length=1, max_length=255)
    candidate_name: str | None = None
    key_skills: list[str] = Field(default_factory=list)
    email_type: str = Field(default="Recruiter Outreach")


class ColdEmailRegenerateSubjectResponse(BaseModel):
    """Refreshed subject line response."""

    subject: str

