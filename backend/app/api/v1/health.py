"""
Health check endpoint — verifies database and Ollama connectivity.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.integrations.ai.ollama import OllamaProvider
from app.schemas.common import APIResponse, HealthData

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/health",
    response_model=APIResponse[HealthData],
    summary="Service health check",
    description="Returns the health status of the API, database, and Ollama AI service.",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> APIResponse[HealthData]:
    """Check connectivity to all dependent services."""

    # --- Database check ---
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        db_status = "unavailable"

    # --- Ollama check ---
    ollama_status = "unavailable"
    try:
        provider = OllamaProvider()
        if await provider.health_check():
            ollama_status = "connected"
    except Exception as exc:
        logger.warning("Ollama health check failed: %s", exc)

    # --- Overall status ---
    overall = "healthy" if db_status == "connected" else "degraded"

    health_data = HealthData(
        status=overall,
        version=settings.APP_VERSION,
        database=db_status,
        ollama=ollama_status,
    )

    return APIResponse[HealthData](
        status="success",
        data=health_data,
        message="Service is healthy" if overall == "healthy" else "Service is degraded",
    )
