"""
Achievements and Badges System API Router (Module 18).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.achievement import AchievementSummaryResponse
from app.schemas.user import APIEnvelope
from app.services.achievement_service import evaluate_and_get_user_achievements

router = APIRouter(prefix="/achievements", tags=["Achievements & Badges"])


@router.get(
    "",
    response_model=APIEnvelope[AchievementSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user achievements and earned badges",
)
async def get_user_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[AchievementSummaryResponse]:
    """Evaluates candidate database activity in real-time and returns earned, locked, and in-progress achievements."""
    summary = await evaluate_and_get_user_achievements(db, user=current_user)
    return APIEnvelope(
        status="success",
        message="User achievements retrieved successfully.",
        data=summary,
    )


@router.post(
    "/evaluate",
    response_model=APIEnvelope[AchievementSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Trigger achievement re-evaluation",
)
async def evaluate_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[AchievementSummaryResponse]:
    """Re-evaluates candidate actions against achievement thresholds."""
    summary = await evaluate_and_get_user_achievements(db, user=current_user)
    return APIEnvelope(
        status="success",
        message="Achievements evaluated successfully.",
        data=summary,
    )
