"""
Notification Service (Module 19).
Generates in-app notifications strictly corresponding to real candidate application state.
"""

from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.career import SkillGapReport
from app.models.coding import CodingChallenge, CodingSubmission
from app.models.interview import InterviewSession
from app.models.notification import Notification, NotificationPreference
from app.models.resume_analysis import ResumeAnalysis
from app.models.roadmap import Roadmap, RoadmapItem
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferenceRequest,
    NotificationPreferenceResponse,
    NotificationResponse,
)


async def get_or_create_user_preferences(
    db: AsyncSession, user_id: int
) -> NotificationPreference:
    """Retrieve or initialize default notification preferences for user."""
    query = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    res = await db.execute(query)
    pref = res.scalar_one_or_none()

    if not pref:
        pref = NotificationPreference(
            user_id=user_id,
            enable_roadmap_reminders=True,
            enable_interview_reminders=True,
            enable_coding_reminders=True,
            enable_resume_suggestions=True,
            enable_learning_milestones=True,
        )
        db.add(pref)
        await db.commit()
        await db.refresh(pref)

    return pref


async def generate_real_state_notifications(db: AsyncSession, user: User) -> None:
    """Inspect candidate REAL database activity and generate meaningful, non-duplicate notifications."""
    pref = await get_or_create_user_preferences(db, user.id)

    # Helper to check if a notification of this type already exists for candidate
    async def has_existing_notification(notif_type: str) -> bool:
        check = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user.id,
                Notification.type == notif_type,
            )
        )
        return (check.scalar() or 0) > 0

    # 1. Continue Roadmap Reminder
    if pref.enable_roadmap_reminders:
        if not await has_existing_notification("roadmap_reminder"):
            rm_res = await db.execute(
                select(Roadmap)
                .where(Roadmap.user_id == user.id, Roadmap.is_active == True)
                .order_by(Roadmap.created_at.desc())
            )
            active_roadmap = rm_res.scalars().first()

            if active_roadmap:
                uncompleted_item = next((item for item in active_roadmap.items if not item.is_completed), None)
                if uncompleted_item:
                    notif = Notification(
                        user_id=user.id,
                        title="Continue Your Career Roadmap",
                        message=f"You have pending learning milestones for your target role '{active_roadmap.target_role}'. Next topic: {uncompleted_item.skill}.",
                        type="roadmap_reminder",
                        link_url="/roadmap",
                        is_read=False,
                    )
                    db.add(notif)

    # 2. Practice Mock Interview Reminder
    if pref.enable_interview_reminders:
        if not await has_existing_notification("interview_reminder"):
            int_res = await db.execute(
                select(func.count(InterviewSession.id)).where(
                    InterviewSession.user_id == user.id, InterviewSession.status == "completed"
                )
            )
            completed_interviews = int_res.scalar() or 0

            if completed_interviews == 0:
                notif = Notification(
                    user_id=user.id,
                    title="Practice AI Mock Interview",
                    message="Test your readiness with Ollama AI! Practice a 5-question mock interview for your target role.",
                    type="interview_reminder",
                    link_url="/interview",
                    is_read=False,
                )
                db.add(notif)

    # 3. Coding Challenge Reminder
    if pref.enable_coding_reminders:
        if not await has_existing_notification("coding_reminder"):
            total_challenges = (await db.execute(select(func.count(CodingChallenge.id)))).scalar() or 0
            passed_challenges = (
                await db.execute(
                    select(func.count(CodingSubmission.id)).where(
                        CodingSubmission.user_id == user.id, CodingSubmission.status == "Passed"
                    )
                )
            ).scalar() or 0

            if total_challenges > passed_challenges:
                notif = Notification(
                    user_id=user.id,
                    title="Daily Coding Challenge Practice",
                    message="Solve interactive Python, SQL, and DSA coding challenges to build portfolio proof.",
                    type="coding_reminder",
                    link_url="/coding",
                    is_read=False,
                )
                db.add(notif)

    # 4. Resume ATS Improvement Suggestion
    if pref.enable_resume_suggestions:
        if not await has_existing_notification("resume_suggestion"):
            an_res = await db.execute(
                select(ResumeAnalysis)
                .where(ResumeAnalysis.user_id == user.id)
                .order_by(ResumeAnalysis.created_at.desc())
            )
            latest_analysis = an_res.scalars().first()

            if latest_analysis and (latest_analysis.ats_score < 75.0 or latest_analysis.missing_keywords):
                notif = Notification(
                    user_id=user.id,
                    title="Resume ATS Score Improvement",
                    message=f"Your latest resume scored {int(latest_analysis.ats_score)}/100. Add missing keywords to reach 75+ target ATS score.",
                    type="resume_suggestion",
                    link_url="/resumes",
                    is_read=False,
                )
                db.add(notif)

    # 5. Skill Gap Learning Milestone
    if pref.enable_learning_milestones:
        if not await has_existing_notification("learning_milestone"):

            sg_res = await db.execute(
                select(SkillGapReport)
                .where(SkillGapReport.user_id == user.id)
                .order_by(SkillGapReport.created_at.desc())
            )
            sg_report = sg_res.scalars().first()

            if sg_report and sg_report.missing_skills:
                notif = Notification(
                    user_id=user.id,
                    title="Skill Gap Learning Resources Available",
                    message="Access verified documentation and accredited courses directly targeting your missing career skills.",
                    type="learning_milestone",
                    link_url="/learning-resources",
                    is_read=False,
                )
                db.add(notif)

    await db.commit()


async def get_user_notifications(db: AsyncSession, user: User) -> NotificationListResponse:
    """Retrieve in-app notifications for authenticated candidate."""
    await generate_real_state_notifications(db, user)

    query = select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())
    res = await db.execute(query)
    notifications = res.scalars().all()

    unread_count = sum(1 for n in notifications if not n.is_read)
    items = [NotificationResponse.model_validate(n) for n in notifications]

    return NotificationListResponse(unread_count=unread_count, notifications=items)


async def mark_notification_as_read(
    db: AsyncSession, user: User, notification_id: int
) -> NotificationResponse:
    """Mark single notification as read."""
    query = select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id)
    res = await db.execute(query)
    notif = res.scalar_one_or_none()

    if not notif:
        raise AppException(message="Notification not found.", status_code=404)

    notif.is_read = True
    await db.commit()
    await db.refresh(notif)
    return NotificationResponse.model_validate(notif)


async def mark_all_notifications_as_read(db: AsyncSession, user: User) -> None:
    """Mark all notifications as read for current user."""
    query = select(Notification).where(Notification.user_id == user.id, Notification.is_read == False)
    res = await db.execute(query)
    unread_items = res.scalars().all()

    for item in unread_items:
        item.is_read = True

    await db.commit()


async def delete_notification(db: AsyncSession, user: User, notification_id: int) -> None:
    """Delete a notification."""
    query = select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id)
    res = await db.execute(query)
    notif = res.scalar_one_or_none()

    if not notif:
        raise AppException(message="Notification not found.", status_code=404)

    await db.delete(notif)
    await db.commit()


async def get_user_notification_preferences(
    db: AsyncSession, user: User
) -> NotificationPreferenceResponse:
    """Retrieve user notification preferences."""
    pref = await get_or_create_user_preferences(db, user.id)
    return NotificationPreferenceResponse.model_validate(pref)


async def update_user_notification_preferences(
    db: AsyncSession, user: User, request: NotificationPreferenceRequest
) -> NotificationPreferenceResponse:
    """Update user notification preferences."""
    pref = await get_or_create_user_preferences(db, user.id)

    if request.enable_roadmap_reminders is not None:
        pref.enable_roadmap_reminders = request.enable_roadmap_reminders
    if request.enable_interview_reminders is not None:
        pref.enable_interview_reminders = request.enable_interview_reminders
    if request.enable_coding_reminders is not None:
        pref.enable_coding_reminders = request.enable_coding_reminders
    if request.enable_resume_suggestions is not None:
        pref.enable_resume_suggestions = request.enable_resume_suggestions
    if request.enable_learning_milestones is not None:
        pref.enable_learning_milestones = request.enable_learning_milestones

    await db.commit()
    await db.refresh(pref)
    return NotificationPreferenceResponse.model_validate(pref)
