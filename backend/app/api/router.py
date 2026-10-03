"""
Top-level API router — aggregates all versioned sub-routers.
"""

from fastapi import APIRouter

from app.api.v1.achievements import router as achievements_router
from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.careers import router as careers_router
from app.api.v1.coding import router as coding_router
from app.api.v1.company_prep import router as company_prep_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.health import router as health_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.job_match import router as job_match_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.career_intelligence import router as career_intelligence_router
from app.api.v1.job_market import router as job_market_router
from app.api.v1.learning_resources import router as learning_resources_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.performance import router as performance_router
from app.api.v1.profile import router as profile_router
from app.api.v1.personal_trainer import router as personal_trainer_router
from app.api.v1.projects import router as projects_router
from app.api.v1.questions import router as questions_router
from app.api.v1.readiness import router as readiness_router
from app.api.v1.resume_analysis import router as resume_analysis_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.roadmap import router as roadmap_router

api_router = APIRouter(prefix="/api/v1")

# Mount version 1 routers
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(dashboard_router)
api_router.include_router(resumes_router)
api_router.include_router(resume_analysis_router)
api_router.include_router(careers_router)
api_router.include_router(roadmap_router)
api_router.include_router(jobs_router)
api_router.include_router(job_match_router)
api_router.include_router(personal_trainer_router)
api_router.include_router(career_intelligence_router)
api_router.include_router(job_market_router)
api_router.include_router(questions_router)
api_router.include_router(interviews_router)
api_router.include_router(performance_router)
api_router.include_router(readiness_router)
api_router.include_router(coding_router)
api_router.include_router(company_prep_router)
api_router.include_router(learning_resources_router)
api_router.include_router(projects_router)
api_router.include_router(achievements_router)
api_router.include_router(notifications_router)
api_router.include_router(admin_router)













