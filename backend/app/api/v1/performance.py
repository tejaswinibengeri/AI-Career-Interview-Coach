"""
Interview Performance Analytics API Router.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.performance import PerformanceResponse
from app.schemas.user import APIEnvelope
from app.services.performance_service import get_user_performance_data

router = APIRouter(prefix="/performance", tags=["Performance Analytics"])


@router.get(
    "",
    response_model=APIEnvelope[PerformanceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user interview performance analytics & score history",
)
async def get_performance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[PerformanceResponse]:
    """Retrieve interview performance analytics, rubric dimension averages, and chronological score history."""
    perf_data = await get_user_performance_data(db, user=current_user)
    return APIEnvelope(
        status="success",
        message="Performance analytics retrieved successfully.",
        data=perf_data,
    )
