"""
Admin Panel Service (Module 20).
Calculates real aggregated statistics and provides administrative management operations.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.coding import CodingSubmission
from app.models.interview import InterviewEvaluation, InterviewSession
from app.models.job import SavedJob
from app.models.job_match import JobMatch
from app.models.learning_resource import LearningResource
from app.models.question import Question
from app.models.resume import ResumeVersion
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User
from app.schemas.admin import (
    AdminAuditLogItem,
    AdminQuestionCreate,
    AdminResourceCreate,
    AdminSettingsResponse,
    AdminSystemStatsResponse,
    AdminUserResponse,
    AdminUserRoleUpdate,
)


async def get_admin_system_statistics(db: AsyncSession) -> AdminSystemStatsResponse:
    """Calculate REAL database aggregated metrics for admin dashboard."""
    # Total Users
    u_res = await db.execute(select(func.count(User.id)))
    total_users = u_res.scalar() or 0

    # Active Users
    au_res = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_users = au_res.scalar() or 0

    # Resumes
    r_res = await db.execute(select(func.count(ResumeVersion.id)))
    total_resumes = r_res.scalar() or 0

    # Interviews
    i_res = await db.execute(
        select(func.count(InterviewSession.id)).where(InterviewSession.status == "completed")
    )
    total_interviews = i_res.scalar() or 0

    # Coding Submissions
    c_res = await db.execute(select(func.count(CodingSubmission.id)))
    coding_submissions = c_res.scalar() or 0

    # Job Searches (Saved Jobs + Job Matches)
    sj_res = await db.execute(select(func.count(SavedJob.id)))
    jm_res = await db.execute(select(func.count(JobMatch.id)))
    total_job_searches = (sj_res.scalar() or 0) + (jm_res.scalar() or 0)

    # AI Usage (Interview Evaluations + Resume Analyses)
    ie_res = await db.execute(select(func.count(InterviewEvaluation.id)))
    ra_res = await db.execute(select(func.count(ResumeAnalysis.id)))
    ai_evaluations = (ie_res.scalar() or 0) + (ra_res.scalar() or 0)

    return AdminSystemStatsResponse(
        total_users=total_users,
        active_users=active_users,
        resumes=total_resumes,
        interviews=total_interviews,
        coding_submissions=coding_submissions,
        job_searches=total_job_searches,
        ai_evaluations=ai_evaluations,
    )


async def get_admin_users(db: AsyncSession) -> list[AdminUserResponse]:
    """Retrieve user list for admin management with privacy protection."""
    res = await db.execute(select(User).order_by(User.created_at.desc()))
    users = res.scalars().all()
    return [AdminUserResponse.model_validate(u) for u in users]


async def update_admin_user(
    db: AsyncSession, target_user_id: int, payload: AdminUserRoleUpdate
) -> AdminUserResponse:
    """Update user role or active status."""
    res = await db.execute(select(User).where(User.id == target_user_id))
    user = res.scalar_one_or_none()

    if not user:
        raise AppException(message="User not found.", status_code=404)

    if payload.role is not None:
        user.role = payload.role
        if payload.role == "admin":
            user.is_superuser = True
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()
    await db.refresh(user)
    return AdminUserResponse.model_validate(user)


async def delete_admin_user(db: AsyncSession, target_user_id: int) -> None:
    """Delete a user from system."""
    res = await db.execute(select(User).where(User.id == target_user_id))
    user = res.scalar_one_or_none()

    if not user:
        raise AppException(message="User not found.", status_code=404)

    await db.delete(user)
    await db.commit()


async def get_admin_questions(db: AsyncSession) -> list[Question]:
    """List all question bank items."""
    res = await db.execute(select(Question).order_by(Question.id.desc()))
    return list(res.scalars().all())


async def create_admin_question(db: AsyncSession, payload: AdminQuestionCreate) -> Question:
    """Create a new question bank item."""
    q = Question(
        category=payload.category,
        difficulty=payload.difficulty,
        role=payload.role,
        question=payload.question_text,
        explanation=payload.explanation,
    )
    db.add(q)
    await db.commit()
    await db.refresh(q)
    return q



async def delete_admin_question(db: AsyncSession, question_id: int) -> None:
    """Delete a question bank item."""
    res = await db.execute(select(Question).where(Question.id == question_id))
    q = res.scalar_one_or_none()
    if not q:
        raise AppException(message="Question not found.", status_code=404)
    await db.delete(q)
    await db.commit()


async def get_admin_resources(db: AsyncSession) -> list[LearningResource]:
    """List all verified learning resources."""
    res = await db.execute(select(LearningResource).order_by(LearningResource.id.desc()))
    return list(res.scalars().all())


async def create_admin_resource(db: AsyncSession, payload: AdminResourceCreate) -> LearningResource:
    """Create a new verified learning resource."""
    lr = LearningResource(
        title=payload.title,
        description=payload.description,
        url=payload.url,
        skill_name=payload.skill_name,
        source=payload.source,
        difficulty=payload.difficulty,
        resource_type=payload.resource_type,
        is_verified=True,
    )
    db.add(lr)
    await db.commit()
    await db.refresh(lr)
    return lr



async def delete_admin_resource(db: AsyncSession, resource_id: int) -> None:
    """Delete a learning resource."""
    res = await db.execute(select(LearningResource).where(LearningResource.id == resource_id))
    lr = res.scalar_one_or_none()
    if not lr:
        raise AppException(message="Resource not found.", status_code=404)
    await db.delete(lr)
    await db.commit()


async def get_admin_audit_logs(db: AsyncSession, limit: int = 50) -> list[AdminAuditLogItem]:
    """Compile real event logs from platform activities for audit trails."""
    logs: list[AdminAuditLogItem] = []

    # 1. Recent Users
    u_res = await db.execute(select(User).order_by(User.created_at.desc()).limit(20))
    for u in u_res.scalars().all():
        logs.append(
            AdminAuditLogItem(
                timestamp=u.created_at,
                event_type="USER_REGISTERED",
                description=f"New user registered: {u.name} (Role: {u.role})",
                actor=u.email,
            )
        )

    # 2. Recent Interviews
    i_res = await db.execute(
        select(InterviewSession).order_by(InterviewSession.created_at.desc()).limit(20)
    )
    for s in i_res.scalars().all():
        logs.append(
            AdminAuditLogItem(
                timestamp=s.created_at,
                event_type="INTERVIEW_SESSION",
                description=f"Mock interview started for role '{s.role}' [Status: {s.status}]",
                actor=f"User ID #{s.user_id}",
            )
        )

    # 3. Recent Coding Submissions
    c_res = await db.execute(
        select(CodingSubmission).order_by(CodingSubmission.created_at.desc()).limit(20)
    )
    for cs in c_res.scalars().all():
        logs.append(
            AdminAuditLogItem(
                timestamp=cs.created_at,
                event_type="CODING_SUBMISSION",
                description=f"Code challenge evaluated in {cs.language} [Verdict: {cs.status}]",
                actor=f"User ID #{cs.user_id}",
            )
        )

    # Sort all events chronologically descending
    logs.sort(key=lambda x: x.timestamp, reverse=True)
    return logs[:limit]


def get_admin_settings() -> AdminSettingsResponse:
    """Return platform configuration settings safely."""
    # Mask database URL
    db_raw = settings.DATABASE_URL
    masked_db = db_raw
    if "@" in db_raw:
        prefix, rest = db_raw.split("@", 1)
        scheme = prefix.split("://")[0]
        masked_db = f"{scheme}://***:***@{rest}"

    return AdminSettingsResponse(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        environment=getattr(settings, "ENVIRONMENT", "development"),
        ollama_model=settings.OLLAMA_MODEL,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        jwt_expiration_minutes=settings.JWT_EXPIRATION_MINUTES,
        database_url_masked=masked_db,
        registration_enabled=True,
    )
