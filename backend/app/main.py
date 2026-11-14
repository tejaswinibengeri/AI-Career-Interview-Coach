"""
FastAPI application factory.

Creates the app, configures middleware, registers routers,
and manages application lifespan (startup / shutdown).
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.db.session import engine

from app.core.middleware import (
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    setup_logging()
    logger.info(
        "Starting %s v%s",
        settings.APP_NAME,
        settings.APP_VERSION,
    )
    logger.info("Database: %s", settings.DATABASE_URL.split("@")[-1])  # log host only
    logger.info("Ollama: %s (model=%s)", settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL)

    # Ensure uploads directory structure exists
    try:
        from pathlib import Path
        upload_path = Path(settings.UPLOAD_DIR)
        (upload_path / "resumes").mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        logger.warning("Could not initialize upload directories: %s", exc)

    try:
        from app.db.base import Base
        from app.db.session import async_session_factory
        from app.services.auth_service import seed_demo_users_if_empty
        from app.services.job_service import seed_verified_jobs_if_empty
        from app.services.coding_service import seed_standard_challenges_if_empty

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified.")

        async with async_session_factory() as session:
            try:
                await seed_demo_users_if_empty(session)
                await seed_verified_jobs_if_empty(session)
                await seed_standard_challenges_if_empty(session)
                logger.info("Standard seed data verified.")
            except Exception as e:
                logger.warning("Could not seed data on startup: %s", e)
    except Exception as exc:
        logger.warning("Could not auto-initialize tables on startup: %s", exc)

    # Pre-warm Ollama LLM model in background to eliminate user cold-start latency
    try:
        import asyncio
        from app.integrations.ai.ollama import OllamaProvider, close_shared_client
        asyncio.create_task(OllamaProvider().warmup())
    except Exception as e:
        logger.debug("Could not initiate LLM warmup: %s", e)

    # Start daily email scheduler (7 AM IST cron for training summaries)
    try:
        from app.core.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.warning("Could not start email scheduler: %s", e)

    yield
    # --- Shutdown ---
    logger.info("Shutting down %s", settings.APP_NAME)
    try:
        from app.core.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass
    try:
        from app.integrations.ai.ollama import close_shared_client
        await close_shared_client()
    except Exception:
        pass
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory — builds and configures the FastAPI instance."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered career coaching and interview preparation platform",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- Security Middlewares ---
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(RequestSizeLimitMiddleware)
    application.add_middleware(RateLimitMiddleware)

    # --- CORS ---
    cors_origin_regex = (
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
        if settings.ENVIRONMENT.lower() != "production"
        else None
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=cors_origin_regex,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # --- Exception handlers ---
    register_exception_handlers(application)

    # --- Root welcome endpoint ---
    @application.get("/", tags=["Health"])
    async def root():
        return {
            "status": "online",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    # --- Routers ---
    application.include_router(api_router)

    return application


# Application instance used by uvicorn
app = create_app()
