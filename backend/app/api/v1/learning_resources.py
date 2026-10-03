"""
Learning Resources System API Router (Module 14).
"""

from typing import List, Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.learning_resource import LearningResourceResponse, ToggleProgressRequest
from app.schemas.user import APIEnvelope
from app.services.learning_resource_service import (
    list_learning_resources,
    toggle_resource_progress,
)

router = APIRouter(prefix="/learning-resources", tags=["Learning Resources Hub"])


@router.get(
    "",
    response_model=APIEnvelope[List[LearningResourceResponse]],
    status_code=status.HTTP_200_OK,
    summary="List learning resources catalog",
)
async def get_learning_resources(
    skill_name: Optional[str] = Query(None, description="Filter by skill name (Python, React, etc.)"),
    difficulty: Optional[str] = Query(None, description="Beginner, Intermediate, Advanced"),
    resource_type: Optional[str] = Query(None, description="Documentation, Course, Video, Book, Certification"),
    search: Optional[str] = Query(None, description="Search keyword"),
    skill_gap_only: bool = Query(False, description="Filter only candidate skill gap recommendations"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[LearningResourceResponse]]:
    """Retrieve verified learning documentation and courses connected to candidate skill gaps."""
    resources = await list_learning_resources(
        db,
        user=current_user,
        skill_name=skill_name,
        difficulty=difficulty,
        resource_type=resource_type,
        search=search,
        skill_gap_only=skill_gap_only,
    )
    return APIEnvelope(
        status="success",
        message="Learning resources retrieved successfully.",
        data=resources,
    )


@router.get(
    "/recommended",
    response_model=APIEnvelope[List[LearningResourceResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get recommended learning resources for candidate skill gap",
)
async def get_recommended_resources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[LearningResourceResponse]]:
    """Retrieve personalized learning resources addressing candidate's identified career skill gaps."""
    resources = await list_learning_resources(
        db, user=current_user, skill_gap_only=True
    )
    return APIEnvelope(
        status="success",
        message="Recommended skill gap learning resources retrieved.",
        data=resources,
    )


@router.post(
    "/{id}/progress",
    response_model=APIEnvelope[LearningResourceResponse],
    status_code=status.HTTP_200_OK,
    summary="Toggle save or completion status for a resource",
)
async def update_resource_progress(
    id: int,
    body: ToggleProgressRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[LearningResourceResponse]:
    """Save/bookmark or mark a learning resource as completed."""
    updated = await toggle_resource_progress(
        db, user=current_user, resource_id=id, request=body
    )
    return APIEnvelope(
        status="success",
        message="Resource progress updated.",
        data=updated,
    )
