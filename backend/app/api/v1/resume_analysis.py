"""
Resume Analysis API Router — AI evaluation and ATS scoring endpoints.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.resume_analysis import ResumeAnalysisResponse
from app.schemas.user import APIEnvelope
from app.services.resume_analysis_service import (
    analyze_user_resume,
    get_user_resume_analysis,
)

router = APIRouter(prefix="/resumes", tags=["Resume Analysis"])


@router.post(
    "/{id}/analyze",
    response_model=APIEnvelope[ResumeAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Trigger AI ATS Analysis on a resume",
)
async def trigger_resume_analysis(
    id: int,
    version_id: int | None = Query(None, description="Optional specific resume version ID"),
    force: bool = Query(False, description="Force re-analysis and bypass cached result"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ResumeAnalysisResponse]:
    """Perform Ollama AI analysis and transparent ATS scoring on target resume."""
    analysis = await analyze_user_resume(
        db, user=current_user, resume_id=id, version_id=version_id, force=force
    )

    return APIEnvelope(
        status="success",
        message="Resume analyzed successfully.",
        data=ResumeAnalysisResponse.model_validate(analysis),
    )


@router.get(
    "/{id}/analysis",
    response_model=APIEnvelope[ResumeAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Get latest AI ATS analysis for a resume",
)
async def get_resume_analysis(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ResumeAnalysisResponse]:
    """Retrieve existing AI analysis and ATS evaluation for the specified resume."""
    analysis = await get_user_resume_analysis(db, user_id=current_user.id, resume_id=id)

    return APIEnvelope(
        status="success",
        message="Analysis retrieved successfully.",
        data=ResumeAnalysisResponse.model_validate(analysis),
    )
