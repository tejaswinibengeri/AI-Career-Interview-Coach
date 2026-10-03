"""
Personalized Career Roadmap API Router.
"""

from fastapi import APIRouter, Depends, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.roadmap import GenerateRoadmapRequest, RoadmapResponse
from app.schemas.user import APIEnvelope
from app.services.roadmap_service import (
    generate_user_roadmap,
    get_user_latest_roadmap,
    toggle_roadmap_item_completion,
)

router = APIRouter(prefix="/roadmap", tags=["Career Roadmap"])


@router.post(
    "/generate",
    response_model=APIEnvelope[RoadmapResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate a personalized career roadmap with AI",
)
async def generate_roadmap(
    body: GenerateRoadmapRequest = Body(default_factory=GenerateRoadmapRequest),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[RoadmapResponse]:
    """Generate structured step-by-step career development roadmap based on actual user state."""
    roadmap = await generate_user_roadmap(
        db, user=current_user, occupation_id=body.occupation_id, custom_query=body.custom_query
    )

    return APIEnvelope(
        status="success",
        message="Personalized career roadmap generated successfully.",
        data=roadmap,
    )


@router.get(
    "/latest",
    response_model=APIEnvelope[RoadmapResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user's active career roadmap",
)
async def get_latest_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[RoadmapResponse]:
    """Retrieve the current active career roadmap and completion status."""
    roadmap = await get_user_latest_roadmap(db, user_id=current_user.id)
    return APIEnvelope(
        status="success",
        message="Active career roadmap retrieved successfully.",
        data=roadmap,
    )


@router.put(
    "/items/{item_id}/toggle",
    response_model=APIEnvelope[RoadmapResponse],
    status_code=status.HTTP_200_OK,
    summary="Toggle completion status for a roadmap item",
)
async def toggle_item_completion(
    item_id: int,
    is_completed: bool = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[RoadmapResponse]:
    """Mark a roadmap item as completed or incomplete and update overall progress."""
    roadmap = await toggle_roadmap_item_completion(
        db, user=current_user, item_id=item_id, is_completed=is_completed
    )
    return APIEnvelope(
        status="success",
        message="Roadmap item completion updated.",
        data=roadmap,
    )
