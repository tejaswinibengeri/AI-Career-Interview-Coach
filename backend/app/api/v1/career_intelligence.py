"""
Career Intelligence API Endpoints.
Covers Job Description Analyzer, Resume -> JD Match, and AI Cover Letter Generator.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.career_intelligence import (
    ColdEmailGenerateRequest,
    ColdEmailHistoryItem,
    ColdEmailRegenerateSubjectRequest,
    ColdEmailRegenerateSubjectResponse,
    ColdEmailResponse,
    ColdEmailUpdateRequest,
    CoverLetterGenerateRequest,
    CoverLetterHistoryItem,
    CoverLetterResponse,
    JobDescriptionAnalysisResponse,
    JobDescriptionAnalyzeRequest,
    ResumeJdMatchHistoryItem,
    ResumeJdMatchRequest,
    ResumeJdMatchResponse,
)
from app.schemas.user import APIEnvelope
from app.services import career_intelligence_service

router = APIRouter(prefix="/career-intelligence", tags=["Career Intelligence"])


# --- 1. Job Description Analyzer ---

@router.post(
    "/analyze-jd",
    response_model=APIEnvelope[JobDescriptionAnalysisResponse],
    summary="Analyze a raw job description using Ollama",
)
async def analyze_job_description_endpoint(
    payload: JobDescriptionAnalyzeRequest,
    _user: User = Depends(get_current_user),
) -> APIEnvelope[JobDescriptionAnalysisResponse]:
    """Parse and extract structured skills, requirements, and keywords from a supplied JD."""
    result = await career_intelligence_service.analyze_job_description(payload)
    return APIEnvelope(data=result, message="Job description analyzed successfully.")


# --- 2. Resume -> JD Match ---

@router.post(
    "/match",
    response_model=APIEnvelope[ResumeJdMatchResponse],
    summary="Match an uploaded resume against a job description",
)
async def match_resume_endpoint(
    payload: ResumeJdMatchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ResumeJdMatchResponse]:
    """Evaluate candidate resume against a job description and store results."""
    result = await career_intelligence_service.match_resume_to_jd(db, user, payload)
    return APIEnvelope(data=result, message="Resume matched against job description successfully.")


@router.get(
    "/matches",
    response_model=APIEnvelope[list[ResumeJdMatchHistoryItem]],
    summary="List previous resume match evaluations",
)
async def get_match_history_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[list[ResumeJdMatchHistoryItem]]:
    """Retrieve history of previous resume-to-JD match comparisons."""
    records = await career_intelligence_service.get_match_history(db, user)
    return APIEnvelope(data=records, message="Match history retrieved successfully.")


@router.get(
    "/matches/{match_id}",
    response_model=APIEnvelope[ResumeJdMatchResponse],
    summary="Get full details for a previous resume match",
)
async def get_match_detail_endpoint(
    match_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ResumeJdMatchResponse]:
    """Retrieve specific previous match evaluation."""
    record = await career_intelligence_service.get_match_detail(db, user, match_id)
    return APIEnvelope(data=record, message="Match details retrieved successfully.")


# --- 3. AI Cover Letter Generator ---

@router.post(
    "/cover-letter",
    response_model=APIEnvelope[CoverLetterResponse],
    summary="Generate tailored AI cover letter from resume & job description",
)
async def generate_cover_letter_endpoint(
    payload: CoverLetterGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[CoverLetterResponse]:
    """Generate professional cover letter grounded in candidate resume."""
    result = await career_intelligence_service.generate_cover_letter(db, user, payload)
    return APIEnvelope(data=result, message="Cover letter generated successfully.")


@router.get(
    "/cover-letters",
    response_model=APIEnvelope[list[CoverLetterHistoryItem]],
    summary="List previously generated cover letters",
)
async def get_cover_letters_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[list[CoverLetterHistoryItem]]:
    """Retrieve list of previously saved cover letters."""
    records = await career_intelligence_service.get_cover_letters(db, user)
    return APIEnvelope(data=records, message="Cover letters retrieved successfully.")


# --- 4. Cold Email Generator ---

@router.post(
    "/cold-email/generate",
    response_model=APIEnvelope[ColdEmailResponse],
    summary="Generate personalized cold outreach email using Ollama",
)
async def generate_cold_email_endpoint(
    payload: ColdEmailGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ColdEmailResponse]:
    """Generate high-impact cold outreach email grounded in candidate credentials and job criteria."""
    result = await career_intelligence_service.generate_cold_email(db, user, payload)
    return APIEnvelope(data=result, message="Cold email generated successfully.")


@router.post(
    "/cold-email/regenerate-subject",
    response_model=APIEnvelope[ColdEmailRegenerateSubjectResponse],
    summary="Regenerate subject line for a cold outreach email",
)
async def regenerate_cold_email_subject_endpoint(
    payload: ColdEmailRegenerateSubjectRequest,
    _user: User = Depends(get_current_user),
) -> APIEnvelope[ColdEmailRegenerateSubjectResponse]:
    """Generate a crisp, compelling subject line without altering the email body."""
    result = await career_intelligence_service.regenerate_cold_email_subject(payload)
    return APIEnvelope(data=result, message="Subject line regenerated successfully.")


@router.get(
    "/cold-email/history",
    response_model=APIEnvelope[list[ColdEmailHistoryItem]],
    summary="List previously generated cold outreach emails",
)
async def get_cold_email_history_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[list[ColdEmailHistoryItem]]:
    """Retrieve history of cold emails generated by the authenticated user."""
    records = await career_intelligence_service.get_cold_email_history(db, user)
    return APIEnvelope(data=records, message="Cold email history retrieved successfully.")


@router.get(
    "/cold-email/{email_id}",
    response_model=APIEnvelope[ColdEmailResponse],
    summary="Get full details of a saved cold outreach email",
)
async def get_cold_email_detail_endpoint(
    email_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ColdEmailResponse]:
    """Retrieve a specific cold email record."""
    record = await career_intelligence_service.get_cold_email_detail(db, user, email_id)
    return APIEnvelope(data=record, message="Cold email details retrieved successfully.")


@router.put(
    "/cold-email/{email_id}",
    response_model=APIEnvelope[ColdEmailResponse],
    summary="Save edits to a cold outreach email",
)
async def update_cold_email_endpoint(
    email_id: int,
    payload: ColdEmailUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ColdEmailResponse]:
    """Update subject or body of a saved cold email."""
    record = await career_intelligence_service.update_cold_email(db, user, email_id, payload)
    return APIEnvelope(data=record, message="Cold email updated successfully.")


@router.delete(
    "/cold-email/{email_id}",
    response_model=APIEnvelope[bool],
    summary="Delete a saved cold outreach email",
)
async def delete_cold_email_endpoint(
    email_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[bool]:
    """Delete a saved cold email from user history."""
    await career_intelligence_service.delete_cold_email(db, user, email_id)
    return APIEnvelope(data=True, message="Cold email deleted successfully.")

