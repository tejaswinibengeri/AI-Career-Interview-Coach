"""
AI Project Recommendations API Router (Module 15).
"""

from typing import List, Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.project_recommendation import (
    ProjectRecommendationResponse,
    UpdateProjectStatusRequest,
)
from app.schemas.user import APIEnvelope
from app.services.project_service import (
    generate_personalized_project_recommendations,
    list_user_project_recommendations,
    update_project_status,
)

router = APIRouter(prefix="/projects", tags=["AI Project Recommendations"])


@router.post(
    "/recommendations",
    response_model=APIEnvelope[List[ProjectRecommendationResponse]],
    status_code=status.HTTP_200_OK,
    summary="Generate personalized AI project recommendations",
)
async def create_project_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[ProjectRecommendationResponse]]:
    """Generate Beginner, Intermediate, and Advanced portfolio projects tailored to candidate skills, skill gaps, and target career."""
    recommendations = await generate_personalized_project_recommendations(db, user=current_user)
    return APIEnvelope(
        status="success",
        message="Personalized AI project recommendations generated successfully.",
        data=recommendations,
    )


@router.get(
    "",
    response_model=APIEnvelope[List[ProjectRecommendationResponse]],
    status_code=status.HTTP_200_OK,
    summary="List project recommendations",
)
async def get_project_recommendations(
    difficulty: Optional[str] = Query(None, description="Beginner, Intermediate, Advanced"),
    status_filter: Optional[str] = Query(None, alias="status", description="Not Started, In Progress, Completed"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[ProjectRecommendationResponse]]:
    """Retrieve candidate project recommendations filtered by difficulty or status."""
    projects = await list_user_project_recommendations(
        db, user=current_user, difficulty=difficulty, status_filter=status_filter
    )
    return APIEnvelope(
        status="success",
        message="Project recommendations retrieved successfully.",
        data=projects,
    )


@router.patch(
    "/{id}/status",
    response_model=APIEnvelope[ProjectRecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="Update project bookmark or status",
)
async def update_project_progress(
    id: int,
    body: UpdateProjectStatusRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ProjectRecommendationResponse]:
    """Save/bookmark or update status ('Not Started', 'In Progress', 'Completed') of a project recommendation."""
    updated = await update_project_status(db, user=current_user, project_id=id, request=body)
    return APIEnvelope(
        status="success",
        message="Project recommendation status updated.",
        data=updated,
    )
