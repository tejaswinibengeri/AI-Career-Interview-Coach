"""
Placement Readiness Evaluation API Router.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.performance import ReadinessResponse
from app.schemas.user import APIEnvelope
from app.services.performance_service import get_user_readiness_data

router = APIRouter(prefix="/readiness", tags=["Placement Readiness"])


@router.get(
    "",
    response_model=APIEnvelope[ReadinessResponse],
    status_code=status.HTTP_200_OK,
    summary="Get candidate job placement readiness score & component breakdown",
)
async def get_readiness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ReadinessResponse]:
    """Retrieve transparent placement readiness calculation, weighted component breakdown, and actionable recommendations."""
    readiness_data = await get_user_readiness_data(db, user=current_user)
    return APIEnvelope(
        status="success",
        message="Placement readiness report retrieved successfully.",
        data=readiness_data,
    )
