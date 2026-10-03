"""
Background scheduler for Personal Trainer twice-daily email notifications.

Uses APScheduler to run two cron jobs daily in the configured timezone:
1. Morning Daily Briefing (default: 08:00 AM / REMINDER_MORNING_TIME)
   - Outlines today's agenda with minute estimates
   - Calls back to leftover / completed items from yesterday
2. Evening Progress Wrap-Up (default: 20:00 / 8:00 PM / REMINDER_EVENING_TIME)
   - Summarizes what was completed today
   - Highlights tasks still pending with a motivational nudge

Gracefully loops across all active users with active plans, skipping users
without emails, and isolating errors so one failed email delivery never
interrupts the entire job.
"""

import asyncio
import logging
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level scheduler instance
_scheduler: AsyncIOScheduler | None = None


def _parse_time(time_str: str, default_hour: int, default_minute: int) -> tuple[int, int]:
    """Parse 'HH:MM' string into (hour, minute). Falls back to defaults on error."""
    try:
        parts = time_str.strip().split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
    except Exception as exc:
        logger.warning(
            "Invalid time format '%s', falling back to %02d:%02d: %s",
            time_str,
            default_hour,
            default_minute,
            exc,
        )
    return default_hour, default_minute


# =============================================================================
# 1. Morning Reminder Job (Daily Briefing)
# =============================================================================

async def _morning_reminder_job() -> None:
    """Cron handler: send morning briefing email to all users with active plans."""
    if not settings.SMTP_ENABLED:
        logger.debug("SMTP disabled — skipping morning reminder job.")
        return

    logger.info("Running morning training reminder email job...")

    try:
        from app.db.session import async_session_factory
        from app.models.personal_trainer import TrainingDay, TrainingPlan, TrainingTask
        from app.models.user import User
        from app.services.email_service import send_morning_reminder_for_user

        async with async_session_factory() as db:
            # Query all active training plans with days and tasks
            stmt = (
                select(TrainingPlan)
                .options(
                    selectinload(TrainingPlan.days).selectinload(TrainingDay.tasks),
                )
                .where(TrainingPlan.is_active == True)
            )
            result = await db.execute(stmt)
            plans = result.scalars().all()

            if not plans:
                logger.info("No active training plans found — no morning emails to send.")
                return

            sent_count = 0
            for plan in plans:
                try:
                    # Load user
                    user_stmt = select(User).where(User.id == plan.user_id)
                    user_res = await db.execute(user_stmt)
                    user = user_res.scalar_one_or_none()
                    if not user or not user.email or not user.is_active:
                        continue

                    # Sort days by day_number
                    sorted_days = sorted(plan.days, key=lambda d: d.day_number)
                    if not sorted_days:
                        continue

                    # Find today's day (first incomplete day, or last day if all completed)
                    today: TrainingDay | None = None
                    for d in sorted_days:
                        if not d.is_completed:
                            today = d
                            break
                    if not today:
                        today = sorted_days[-1]

                    # Yesterday data
                    yesterday_completed: list[str] = []
                    yesterday_incomplete: list[str] = []
                    if today.day_number > 1:
                        yesterday = next(
                            (d for d in sorted_days if d.day_number == today.day_number - 1),
                            None,
                        )
                        if yesterday:
                            for t in yesterday.tasks:
                                if t.status == "completed":
                                    yesterday_completed.append(t.title)
                                else:
                                    yesterday_incomplete.append(t.title)

                    # Today's tasks
                    today_tasks = [
                        {
                            "title": t.title,
                            "task_type": t.task_type,
                            "estimated_minutes": t.estimated_minutes,
                            "status": t.status,
                        }
                        for t in sorted(today.tasks, key=lambda x: x.order_index)
                    ]

                    # Overall progress calculation
                    all_tasks = [t for d in sorted_days for t in d.tasks]
                    completed_count = sum(1 for t in all_tasks if t.status == "completed")
                    progress = (
                        round((completed_count / len(all_tasks)) * 100.0, 1)
                        if all_tasks
                        else 0.0
                    )

                    success = await send_morning_reminder_for_user(
                        user_email=user.email,
                        user_name=user.name,
                        plan_title=plan.title,
                        overall_progress=progress,
                        day_number=today.day_number,
                        day_objective=today.objective,
                        today_tasks=today_tasks,
                        yesterday_completed=yesterday_completed,
                        yesterday_incomplete=yesterday_incomplete,
                        total_days=len(sorted_days),
                    )
                    if success:
                        sent_count += 1
                        # Brief pause to avoid SMTP rate limits on free-tier providers
                        await asyncio.sleep(2)

                except Exception as user_exc:
                    logger.error(
                        "Failed to send morning reminder to user_id=%s: %s",
                        plan.user_id,
                        user_exc,
                    )

            logger.info("Morning reminder email job completed — %d emails sent.", sent_count)

    except Exception as exc:
        logger.error("Morning reminder cron job failed: %s", exc)


# =============================================================================
# 2. Evening Reminder Job (Progress Wrap-Up)
# =============================================================================

async def _evening_reminder_job() -> None:
    """Cron handler: send evening progress wrap-up email to all users with active plans."""
    if not settings.SMTP_ENABLED:
        logger.debug("SMTP disabled — skipping evening reminder job.")
        return

    logger.info("Running evening training reminder email job...")

    try:
        from app.db.session import async_session_factory
        from app.models.personal_trainer import TrainingDay, TrainingPlan, TrainingTask
        from app.models.user import User
        from app.services.email_service import send_evening_reminder_for_user

        async with async_session_factory() as db:
            # Query all active training plans with days and tasks
            stmt = (
                select(TrainingPlan)
                .options(
                    selectinload(TrainingPlan.days).selectinload(TrainingDay.tasks),
                )
                .where(TrainingPlan.is_active == True)
            )
            result = await db.execute(stmt)
            plans = result.scalars().all()

            if not plans:
                logger.info("No active training plans found — no evening emails to send.")
                return

            sent_count = 0
            for plan in plans:
                try:
                    # Load user
                    user_stmt = select(User).where(User.id == plan.user_id)
                    user_res = await db.execute(user_stmt)
                    user = user_res.scalar_one_or_none()
                    if not user or not user.email or not user.is_active:
                        continue

                    # Sort days by day_number
                    sorted_days = sorted(plan.days, key=lambda d: d.day_number)
                    if not sorted_days:
                        continue

                    # Find today's day (first incomplete day, or last day if all completed)
                    today: TrainingDay | None = None
                    for d in sorted_days:
                        if not d.is_completed:
                            today = d
                            break
                    if not today:
                        today = sorted_days[-1]

                    # Separate today's completed and pending tasks
                    completed_today_tasks: list[dict[str, Any]] = []
                    pending_today_tasks: list[dict[str, Any]] = []

                    for t in sorted(today.tasks, key=lambda x: x.order_index):
                        task_dict = {
                            "title": t.title,
                            "task_type": t.task_type,
                            "estimated_minutes": t.estimated_minutes,
                            "status": t.status,
                        }
                        if t.status == "completed":
                            completed_today_tasks.append(task_dict)
                        else:
                            pending_today_tasks.append(task_dict)

                    # Overall progress calculation
                    all_tasks = [t for d in sorted_days for t in d.tasks]
                    completed_count = sum(1 for t in all_tasks if t.status == "completed")
                    progress = (
                        round((completed_count / len(all_tasks)) * 100.0, 1)
                        if all_tasks
                        else 0.0
                    )

                    success = await send_evening_reminder_for_user(
                        user_email=user.email,
                        user_name=user.name,
                        plan_title=plan.title,
                        overall_progress=progress,
                        day_number=today.day_number,
                        day_objective=today.objective,
                        completed_today_tasks=completed_today_tasks,
                        pending_today_tasks=pending_today_tasks,
                        total_days=len(sorted_days),
                    )
                    if success:
                        sent_count += 1
                        # Brief pause to avoid SMTP rate limits on free-tier providers
                        await asyncio.sleep(2)

                except Exception as user_exc:
                    logger.error(
                        "Failed to send evening reminder to user_id=%s: %s",
                        plan.user_id,
                        user_exc,
                    )

            logger.info("Evening reminder email job completed — %d emails sent.", sent_count)

    except Exception as exc:
        logger.error("Evening reminder cron job failed: %s", exc)


# =============================================================================
# Lifecycle Management
# =============================================================================

def start_scheduler() -> None:
    """Start the APScheduler with morning and evening reminder cron triggers."""
    global _scheduler

    if not settings.SMTP_ENABLED:
        logger.info("SMTP disabled — daily email scheduler will NOT start.")
        return

    _scheduler = AsyncIOScheduler()

    tz = settings.REMINDER_TIMEZONE or "UTC"

    # Morning job
    morning_h, morning_m = _parse_time(settings.REMINDER_MORNING_TIME, default_hour=8, default_minute=0)
    _scheduler.add_job(
        _morning_reminder_job,
        trigger=CronTrigger(hour=morning_h, minute=morning_m, timezone=tz),
        id="personal_trainer_morning_reminder",
        name=f"Morning Training Briefing ({morning_h:02d}:{morning_m:02d} {tz})",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Evening job
    evening_h, evening_m = _parse_time(settings.REMINDER_EVENING_TIME, default_hour=20, default_minute=0)
    _scheduler.add_job(
        _evening_reminder_job,
        trigger=CronTrigger(hour=evening_h, minute=evening_m, timezone=tz),
        id="personal_trainer_evening_reminder",
        name=f"Evening Training Wrap-Up ({evening_h:02d}:{evening_m:02d} {tz})",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    _scheduler.start()
    logger.info(
        "[Email Scheduler] Twice-daily email scheduler started:\n"
        "   - Morning Briefing: %02d:%02d (%s)\n"
        "   - Evening Wrap-Up:  %02d:%02d (%s)",
        morning_h,
        morning_m,
        tz,
        evening_h,
        evening_m,
        tz,
    )


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Daily email scheduler stopped.")
        _scheduler = None
