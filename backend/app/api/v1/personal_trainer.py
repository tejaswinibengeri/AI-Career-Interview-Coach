"""
API endpoints for Personal Trainer module.
"""

from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.personal_trainer import (
    DailyTrainingViewResponse,
    DayReviewRequest,
    N8nWebhookTriggerResponse,
    PersonalTrainerSettingsResponse,
    PersonalTrainerSettingsUpdateRequest,
    RescheduleDayRequest,
    ResumeSkillsResponse,
    TaskStatusUpdateRequest,
    TrainingPlanCreateRequest,
    TrainingPlanResponse,
    TrainingTaskResponse,
)
from app.schemas.user import APIEnvelope
from app.services import personal_trainer_service

router = APIRouter(prefix="/personal-trainer", tags=["Personal Trainer"])


@router.get("/resume-skills", response_model=APIEnvelope[ResumeSkillsResponse])
async def get_user_resume_skills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve verified skills from the user's uploaded resume or analysis records without duplicate parsing."""
    skills = await personal_trainer_service.get_user_resume_skills(db, current_user)
    return APIEnvelope(
        status="success",
        message="Resume skills retrieved.",
        data=ResumeSkillsResponse(skills=skills, source="resume_analysis"),
    )


@router.post("/investigate", response_model=APIEnvelope[TrainingPlanResponse], status_code=status.HTTP_201_CREATED)
async def investigate_goal_and_create_plan(
    request: TrainingPlanCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Investigate candidate's goal, decompose prerequisites with Ollama, and generate a day-by-day plan."""
    plan = await personal_trainer_service.generate_training_plan(db, current_user, request)
    return APIEnvelope(
        status="success",
        message="Training plan created successfully.",
        data=TrainingPlanResponse.model_validate(plan),
    )


@router.get("/active", response_model=APIEnvelope[TrainingPlanResponse | None])
async def get_active_training_plan(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch active training plan with all days and tasks for the authenticated user."""
    plan = await personal_trainer_service.get_active_training_plan(db, current_user)
    if plan is None:
        return APIEnvelope(
            status="success",
            message="No active training plan found.",
            data=None,
        )
    return APIEnvelope(
        status="success",
        message="Active training plan retrieved.",
        data=TrainingPlanResponse.model_validate(plan),
    )


@router.get("/daily/{day_number}", response_model=APIEnvelope[DailyTrainingViewResponse])
async def get_daily_training(
    day_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get dedicated daily workspace view with yesterday context and dynamic AI summary."""
    view = await personal_trainer_service.get_daily_training_view(db, current_user, day_number)
    return APIEnvelope(
        status="success",
        message="Daily training view retrieved.",
        data=view,
    )


@router.get("/daily", response_model=APIEnvelope[DailyTrainingViewResponse])
async def get_today_training(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get today's training view (defaults to first incomplete day or day 1)."""
    view = await personal_trainer_service.get_daily_training_view(db, current_user, None)
    return APIEnvelope(
        status="success",
        message="Today's training view retrieved.",
        data=view,
    )


@router.patch("/tasks/{task_id}", response_model=APIEnvelope[TrainingTaskResponse])
async def update_training_task_status(
    task_id: int,
    request: TaskStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update task status (e.g. complete, skip, reschedule), notes, or recorded study time."""
    task = await personal_trainer_service.update_training_task_status(db, current_user, task_id, request)
    return APIEnvelope(
        status="success",
        message="Task updated successfully.",
        data=TrainingTaskResponse.model_validate(task),
    )


@router.post("/reschedule-today", response_model=APIEnvelope[DailyTrainingViewResponse])
async def reschedule_today_workload(
    request: RescheduleDayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Recalculate today's workload based on limited availability and defer excess tasks to next day."""
    view = await personal_trainer_service.reschedule_today_workload(db, current_user, request)
    return APIEnvelope(
        status="success",
        message="Today's schedule rescheduled.",
        data=view,
    )


@router.post("/days/{day_id}/review")
async def submit_day_confidence_review(
    day_id: int,
    request: DayReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Submit confidence rating (1-5) and receive tailored review recommendations."""
    result = await personal_trainer_service.submit_day_confidence_review(db, current_user, day_id, request)
    return APIEnvelope(
        status="success",
        message="Confidence review submitted.",
        data=result,
    )


@router.get("/settings", response_model=APIEnvelope[PersonalTrainerSettingsResponse])
async def get_trainer_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get notification preferences and external n8n status."""
    settings_obj = await personal_trainer_service.get_trainer_settings(db, current_user)
    webhook_set = bool(settings.N8N_WEBHOOK_URL and settings.N8N_WEBHOOK_URL.strip())
    return APIEnvelope(
        status="success",
        message="Trainer settings retrieved.",
        data=PersonalTrainerSettingsResponse(
            notifications_enabled=settings_obj.notifications_enabled,
            preferred_time=settings_obj.preferred_time,
            notification_channel=settings_obj.notification_channel,
            webhook_configured=webhook_set,
        ),
    )


@router.put("/settings", response_model=APIEnvelope[PersonalTrainerSettingsResponse])
async def update_trainer_settings(
    request: PersonalTrainerSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update notification preferences."""
    settings_obj = await personal_trainer_service.update_trainer_settings(db, current_user, request)
    webhook_set = bool(settings.N8N_WEBHOOK_URL and settings.N8N_WEBHOOK_URL.strip())
    return APIEnvelope(
        status="success",
        message="Trainer settings updated.",
        data=PersonalTrainerSettingsResponse(
            notifications_enabled=settings_obj.notifications_enabled,
            preferred_time=settings_obj.preferred_time,
            notification_channel=settings_obj.notification_channel,
            webhook_configured=webhook_set,
        ),
    )


@router.post("/notify-webhook", response_model=APIEnvelope[N8nWebhookTriggerResponse])
async def trigger_n8n_notification(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Trigger the external n8n webhook notification workflow with real day training data."""
    result = await personal_trainer_service.trigger_n8n_daily_notification(db, current_user)
    return APIEnvelope(
        status="success",
        message="Webhook triggered.",
        data=result,
    )
