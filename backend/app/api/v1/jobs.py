"""
Real Job Search API Router.
"""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.job import JobResponse
from app.schemas.user import APIEnvelope
from app.services.job_service import (
    get_job_by_id,
    get_user_saved_jobs,
    save_job_for_user,
    search_and_cache_jobs,
    unsave_job_for_user,
)

router = APIRouter(prefix="/jobs", tags=["Real Job Search"])


@router.get(
    "",
    response_model=APIEnvelope[List[JobResponse]],
    status_code=status.HTTP_200_OK,
    summary="Search real external job listings",
)
async def list_jobs(
    q: str = Query("", description="Keyword search query (role, skills)"),
    location: str = Query("", description="Location filter (city, state)"),
    is_remote: bool = Query(False, description="Filter for remote jobs"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[JobResponse]]:
    """Search real external job listings from Adzuna job provider API."""
    jobs = await search_and_cache_jobs(
        db,
        user=current_user,
        query=q,
        location=location,
        is_remote=is_remote,
        page=page,
        limit=limit,
    )
    return APIEnvelope(
        status="success",
        message="Jobs retrieved successfully.",
        data=jobs,
    )


@router.get(
    "/saved",
    response_model=APIEnvelope[List[JobResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get user's bookmarked saved jobs",
)
async def get_saved_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[JobResponse]]:
    """Retrieve all jobs bookmarked by the authenticated user."""
    jobs = await get_user_saved_jobs(db, user_id=current_user.id)
    return APIEnvelope(
        status="success",
        message="Saved jobs retrieved successfully.",
        data=jobs,
    )


@router.get(
    "/{id}",
    response_model=APIEnvelope[JobResponse],
    status_code=status.HTTP_200_OK,
    summary="Get detailed job listing by ID",
)
async def get_job(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[JobResponse]:
    """Retrieve full details for a specific cached job listing."""
    job = await get_job_by_id(db, job_id=id, user_id=current_user.id)
    return APIEnvelope(
        status="success",
        message="Job detail retrieved successfully.",
        data=job,
    )


@router.post(
    "/{id}/save",
    response_model=APIEnvelope[JobResponse],
    status_code=status.HTTP_200_OK,
    summary="Bookmark/Save a job listing",
)
async def save_job(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[JobResponse]:
    """Save a job listing to user's saved jobs list."""
    job = await save_job_for_user(db, user=current_user, job_id=id)
    return APIEnvelope(
        status="success",
        message="Job saved successfully.",
        data=job,
    )


@router.delete(
    "/{id}/save",
    response_model=APIEnvelope[JobResponse],
    status_code=status.HTTP_200_OK,
    summary="Remove a saved job bookmark",
)
async def unsave_job(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[JobResponse]:
    """Remove a job from user's saved jobs list."""
    job = await unsave_job_for_user(db, user=current_user, job_id=id)
    return APIEnvelope(
        status="success",
        message="Job removed from saved list.",
        data=job,
    )
