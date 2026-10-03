"""
Career Selection & Skill Gap API Router endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.career import (
    CareerGoalRequest,
    CareerSkillResponse,
    OccupationResponse,
    SkillGapRequest,
    SkillGapReportResponse,
)
from app.schemas.user import APIEnvelope
from app.services.career_service import (
    generate_skill_gap_report,
    get_latest_user_skill_gap_report,
    get_occupation_by_id,
    search_occupations,
    set_user_career_goal,
)

router = APIRouter(prefix="", tags=["Career & Skill Gap"])


def format_occupation_response(occ) -> OccupationResponse:
    """Format ORM Occupation object into OccupationResponse schema."""
    skills = [
        CareerSkillResponse(
            name=os.skill.name,
            category=os.skill.category,
            importance=os.importance,
            level=os.level,
        )
        for os in (occ.skills or [])
    ]

    return OccupationResponse(
        id=occ.id,
        code=occ.code,
        title=occ.title,
        description=occ.description,
        industry=occ.industry,
        skills=skills,
    )


def format_report_response(report) -> SkillGapReportResponse:
    """Format ORM SkillGapReport into SkillGapReportResponse schema."""
    return SkillGapReportResponse(
        id=report.id,
        user_id=report.user_id,
        occupation_id=report.occupation_id,
        occupation_title=report.occupation.title if report.occupation else "Target Occupation",
        match_percentage=report.match_percentage,
        strong_skills=report.strong_skills,
        intermediate_skills=report.intermediate_skills,
        missing_skills=report.missing_skills,
        learning_order=report.learning_order,
        ai_explanation=report.ai_explanation,
        created_at=report.created_at,
    )


@router.get(
    "/careers",
    response_model=APIEnvelope[List[OccupationResponse]],
    status_code=status.HTTP_200_OK,
    summary="Search O*NET occupations and careers",
)
async def list_careers(
    q: str = Query("", description="Keyword search query"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[OccupationResponse]]:
    """Search O*NET occupation taxonomy by title, code, or industry keyword."""
    occupations = await search_occupations(db, query=q, limit=limit)
    data = [format_occupation_response(occ) for occ in occupations]

    return APIEnvelope(
        status="success",
        message="Careers retrieved successfully.",
        data=data,
    )


@router.get(
    "/careers/{id}",
    response_model=APIEnvelope[OccupationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get detailed occupation requirements",
)
async def get_career(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[OccupationResponse]:
    """Retrieve full details and skill requirements for an occupation."""
    occ = await get_occupation_by_id(db, occupation_id=id)
    return APIEnvelope(
        status="success",
        message="Career details retrieved successfully.",
        data=format_occupation_response(occ),
    )


@router.post(
    "/career/skill-gap",
    response_model=APIEnvelope[SkillGapReportResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate a personalized skill gap analysis report",
)
async def analyze_skill_gap(
    body: SkillGapRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[SkillGapReportResponse]:
    """Compare user's profile and resume skills against target O*NET occupation skills."""
    report = await generate_skill_gap_report(db, user=current_user, occupation_id=body.occupation_id)
    return APIEnvelope(
        status="success",
        message="Skill gap analysis report generated successfully.",
        data=format_report_response(report),
    )


@router.get(
    "/career/skill-gap/latest",
    response_model=APIEnvelope[SkillGapReportResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user's latest skill gap report",
)
async def get_latest_skill_gap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[SkillGapReportResponse]:
    """Retrieve the most recent skill gap report for the authenticated user."""
    report = await get_latest_user_skill_gap_report(db, user_id=current_user.id)
    return APIEnvelope(
        status="success",
        message="Latest skill gap report retrieved successfully.",
        data=format_report_response(report),
    )


@router.post(
    "/career/goal",
    response_model=APIEnvelope[OccupationResponse],
    status_code=status.HTTP_200_OK,
    summary="Set active target career goal",
)
async def set_career_goal(
    body: CareerGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[OccupationResponse]:
    """Set specified occupation as the user's target career goal."""
    goal = await set_user_career_goal(db, user=current_user, occupation_id=body.occupation_id)
    return APIEnvelope(
        status="success",
        message=f"Career goal updated to '{goal.target_role_title}'.",
        data=format_occupation_response(goal.occupation),
    )
