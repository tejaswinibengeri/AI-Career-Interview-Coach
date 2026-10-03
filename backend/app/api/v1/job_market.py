"""
Job Market Analyzer API Endpoints.
Independent module for searching real-world job market data and deriving live market analytics.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.job_market import JobMarketSearchFilters, JobMarketSearchResponse
from app.schemas.user import APIEnvelope
from app.services import job_market_service

router = APIRouter(prefix="/job-market", tags=["Job Market Analyzer"])


@router.get(
    "/search",
    response_model=APIEnvelope[JobMarketSearchResponse],
    summary="Search real external job listings and compute live market analytics",
)
async def search_job_market_endpoint(
    query: str = Query("", description="Job title, keywords, or skills"),
    location: str = Query("", description="Location or city filter"),
    is_remote: bool = Query(False, description="Remote only filter"),
    workplace_type: str | None = Query(None, description="All, Remote, Hybrid, On-site"),
    experience_level: str | None = Query(None, description="All, Entry, Mid, Senior, Lead"),
    skills: str | None = Query(None, description="Comma-separated skill keywords"),
    company: str | None = Query(None, description="Company name filter"),
    job_type: str | None = Query(None, description="Full-time, Part-time, Contract, Any"),
    date_posted: str | None = Query("all", description="all, 24h, 7d, 30d"),
    use_profile: bool = Query(False, description="Optionally use user target career, skills, and location"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[JobMarketSearchResponse]:
    """Execute real job search against external provider with live computed analytics."""
    filters = JobMarketSearchFilters(
        query=query,
        location=location,
        is_remote=is_remote,
        workplace_type=workplace_type,
        experience_level=experience_level,
        skills=skills,
        company=company,
        job_type=job_type,
        date_posted=date_posted,
        use_profile=use_profile,
        page=page,
        limit=limit,
    )
    result = await job_market_service.search_job_market(db, user, filters)
    return APIEnvelope(data=result, message=result.status_message)
