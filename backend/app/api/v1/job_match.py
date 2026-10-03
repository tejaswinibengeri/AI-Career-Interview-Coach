"""
Resume-to-Job Matching API Router.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.job_match import JobMatchResponse
from app.schemas.user import APIEnvelope
from app.services.job_match_service import get_user_job_match, match_resume_to_job

router = APIRouter(prefix="/jobs", tags=["Resume-to-Job Matching"])


@router.post(
    "/{id}/match",
    response_model=APIEnvelope[JobMatchResponse],
    status_code=status.HTTP_200_OK,
    summary="Match user resume & profile against a real job listing",
)
async def analyze_job_match(
    id: int,
    resume_id: int | None = Query(None, description="Optional specific resume ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[JobMatchResponse]:
    """Calculate deterministic compatibility score and generate AI narrative explanation for target job."""
    match_result = await match_resume_to_job(
        db, user=current_user, job_id=id, resume_id=resume_id
    )
    return APIEnvelope(
        status="success",
        message="Resume-to-job match analysis generated successfully.",
        data=match_result,
    )


@router.get(
    "/{id}/match",
    response_model=APIEnvelope[JobMatchResponse],
    status_code=status.HTTP_200_OK,
    summary="Get existing job match analysis",
)
async def get_job_match(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[JobMatchResponse]:
    """Retrieve existing resume-to-job match analysis for the specified job."""
    match_result = await get_user_job_match(db, user_id=current_user.id, job_id=id)
    return APIEnvelope(
        status="success",
        message="Job match analysis retrieved successfully.",
        data=match_result,
    )
