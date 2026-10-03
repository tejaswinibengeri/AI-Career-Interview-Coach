"""
User Dashboard API endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.schemas.user import APIEnvelope
from app.services.dashboard_service import get_user_dashboard_data

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "",
    response_model=APIEnvelope[DashboardResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user dashboard aggregation data",
)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[DashboardResponse]:
    """Retrieve aggregated real user data and module statuses for dashboard."""
    dashboard_data = await get_user_dashboard_data(db, current_user)

    return APIEnvelope(
        status="success",
        message="Dashboard data retrieved successfully.",
        data=dashboard_data,
    )
