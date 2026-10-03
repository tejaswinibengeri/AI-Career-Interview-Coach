"""
Email notification service for Personal Trainer.

Sends SMTP emails for:
1. Task completion notifications (real-time instant)
2. Morning daily briefing (configurable morning cron, default 7:00 / 8:00 AM)
3. Evening progress wrap-up (configurable evening cron, default 20:00 / 8:00 PM)

Uses aiosmtplib for async, non-blocking email delivery.
Gracefully degrades when SMTP is not configured.
"""

import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Core SMTP Sender
# =============================================================================

async def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an HTML email via SMTP. Returns True on success, False on failure."""
    if not settings.SMTP_ENABLED:
        logger.debug("SMTP disabled — skipping email to %s", to)
        return False

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured — skipping email.")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        use_tls = settings.SMTP_PORT == 465
        start_tls = settings.SMTP_PORT == 587 or (not use_tls and settings.SMTP_PORT != 25)
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=use_tls,
            start_tls=start_tls,
        )
        logger.info("Email sent to %s — Subject: %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False


def _fire_and_forget_email(to: str, subject: str, html_body: str) -> None:
    """Schedule email sending as a non-blocking background coroutine."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(send_email(to, subject, html_body))
    except RuntimeError:
        logger.warning("No running event loop — email to %s skipped.", to)


# =============================================================================
# Shared CSS Styles
# =============================================================================

_BASE_STYLE = """
<style>
    body { margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f1117; color: #e2e8f0; }
    .container { max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1a1d2e 0%, #0f1117 100%); border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); }
    .header { padding: 32px 28px; text-align: center; }
    .header-morning { background: linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%); }
    .header-evening { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #c026d3 100%); }
    .header-complete { background: linear-gradient(135deg, #059669 0%, #10b981 50%, #14b8a6 100%); }
    .header h1 { margin: 0; font-size: 22px; font-weight: 800; color: #fff; letter-spacing: -0.5px; }
    .header p { margin: 8px 0 0; font-size: 13px; color: rgba(255,255,255,0.85); }
    .body-content { padding: 28px; }
    .card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
    .card-title { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #a78bfa; margin: 0 0 12px; }
    .task-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .task-item:last-child { border-bottom: none; }
    .task-icon { font-size: 16px; flex-shrink: 0; margin-top: 2px; }
    .task-title { font-size: 14px; font-weight: 600; color: #e2e8f0; margin: 0; }
    .task-meta { font-size: 11px; color: #94a3b8; margin-top: 2px; }
    .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
    .badge-completed { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
    .badge-pending { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
    .badge-theory { background: rgba(96,165,250,0.15); color: #60a5fa; }
    .badge-practice { background: rgba(52,211,153,0.15); color: #34d399; }
    .badge-project { background: rgba(168,85,247,0.15); color: #a855f7; }
    .progress-bar-outer { width: 100%; height: 10px; background: rgba(255,255,255,0.06); border-radius: 8px; overflow: hidden; margin-top: 8px; }
    .progress-bar-inner { height: 100%; background: linear-gradient(90deg, #6366f1, #a855f7, #34d399); border-radius: 8px; }
    .stat-grid { display: flex; gap: 12px; margin-top: 12px; }
    .stat-box { flex: 1; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 14px; text-align: center; }
    .stat-value { font-size: 22px; font-weight: 800; color: #fff; }
    .stat-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; color: #64748b; margin-top: 4px; }
    .callout { background: rgba(99,102,241,0.08); border-left: 3px solid #6366f1; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; }
    .callout-title { font-size: 13px; font-weight: 700; color: #818cf8; margin: 0 0 4px; }
    .callout-text { font-size: 12px; color: #cbd5e1; margin: 0; }
    .footer { padding: 20px 28px; text-align: center; border-top: 1px solid rgba(255,255,255,0.05); }
    .footer p { margin: 0; font-size: 11px; color: #475569; }
    .emoji-big { font-size: 32px; margin-bottom: 8px; }
</style>
"""


# =============================================================================
# 1. Real-Time Task Completion Email
# =============================================================================

def build_task_completed_email(
    user_name: str,
    task_title: str,
    task_type: str,
    estimated_minutes: int,
    day_number: int,
    day_objective: str,
    plan_title: str,
    overall_progress: float,
) -> tuple[str, str]:
    """Build subject + HTML body for a real-time task completion notification."""
    subject = f"✅ Task Completed — {task_title}"
    type_badge = f'<span class="badge badge-{task_type}">{task_type.title()}</span>'

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">{_BASE_STYLE}</head>
<body>
<div class="container">
    <div class="header header-complete">
        <div class="emoji-big">🎉</div>
        <h1>Task Completed!</h1>
        <p>Great work, {user_name}! You just crushed another task.</p>
    </div>
    <div class="body-content">
        <div class="card">
            <div class="card-title">Completed Task</div>
            <div class="task-item" style="border-bottom:none;">
                <div>
                    <p class="task-title">{task_title}</p>
                    <p class="task-meta">
                        {type_badge} &nbsp;·&nbsp; {estimated_minutes} min &nbsp;·&nbsp; Day {day_number}
                    </p>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Day Focus</div>
            <p style="margin:0;font-size:14px;color:#cbd5e1;">
                📅 <strong>Day {day_number}</strong> — {day_objective}
            </p>
        </div>

        <div class="card">
            <div class="card-title">Plan: {plan_title}</div>
            <p style="margin:0 0 8px;font-size:13px;color:#94a3b8;">Overall Progress</p>
            <div class="progress-bar-outer">
                <div class="progress-bar-inner" style="width:{min(100, max(0, overall_progress))}%;"></div>
            </div>
            <p style="margin:8px 0 0;font-size:20px;font-weight:800;color:#fff;">{overall_progress:.1f}%</p>
        </div>
    </div>
    <div class="footer">
        <p>🧠 CareerCoachAI — Personal Trainer</p>
    </div>
</div>
</body>
</html>"""

    return subject, html


# =============================================================================
# 2. Morning Daily Briefing Email
# =============================================================================

def build_morning_reminder_email(
    user_name: str,
    plan_title: str,
    overall_progress: float,
    day_number: int,
    day_objective: str,
    today_tasks: list[dict[str, Any]],
    yesterday_completed: list[str],
    yesterday_incomplete: list[str],
    total_days: int,
) -> tuple[str, str]:
    """Build subject + HTML body for the morning daily briefing."""
    subject = f"🌅 Morning Briefing — Day {day_number}: {plan_title}"

    # Yesterday callback section
    yesterday_html = ""
    if yesterday_completed or yesterday_incomplete:
        completed_items = "".join(
            f'<div class="task-item"><span class="task-icon">✅</span><div><p class="task-title">{t}</p></div></div>'
            for t in yesterday_completed
        ) if yesterday_completed else '<p style="color:#64748b;font-size:13px;margin:4px 0;">No tasks were marked completed yesterday.</p>'

        incomplete_items = "".join(
            f'<div class="task-item"><span class="task-icon">⚠️</span><div><p class="task-title">{t}</p><p class="task-meta" style="color:#fbbf24;">Left incomplete from yesterday</p></div></div>'
            for t in yesterday_incomplete
        ) if yesterday_incomplete else ""

        yesterday_callback_msg = ""
        if yesterday_incomplete:
            yesterday_callback_msg = f"""
            <div class="callout">
                <p class="callout-title">📌 Yesterday's Leftover Note</p>
                <p class="callout-text">You left off with <strong>{len(yesterday_incomplete)} task{'s' if len(yesterday_incomplete) > 1 else ''}</strong> pending from yesterday. Consider wrapping those up early today!</p>
            </div>"""

        yesterday_html = f"""
        {yesterday_callback_msg}
        <div class="card">
            <div class="card-title">📋 Yesterday's Recap</div>
            <p style="font-size:12px;color:#94a3b8;margin:0 0 8px;">
                <span class="badge badge-completed">{len(yesterday_completed)} Completed</span>
                {'<span class="badge badge-pending" style="margin-left:6px;">' + str(len(yesterday_incomplete)) + ' Pending</span>' if yesterday_incomplete else ''}
            </p>
            {completed_items}
            {incomplete_items}
        </div>"""

    # Today's tasks section
    today_items_html = ""
    total_minutes = 0
    for t in today_tasks:
        status = t.get("status", "not_started")
        title = t.get("title", "Task")
        est = t.get("estimated_minutes", 30)
        ttype = t.get("task_type", "practice")
        total_minutes += est
        icon = "✅" if status == "completed" else "🔵" if status == "in_progress" else "⬜"
        type_badge = f'<span class="badge badge-{ttype}" style="font-size:10px;">{ttype.title()}</span>'
        today_items_html += f"""
        <div class="task-item">
            <span class="task-icon">{icon}</span>
            <div>
                <p class="task-title">{title}</p>
                <p class="task-meta">{type_badge} &nbsp;·&nbsp; {est} min</p>
            </div>
        </div>"""

    hours = total_minutes // 60
    mins = total_minutes % 60
    workload_str = f"{hours}h {mins}m" if hours else f"{mins}m"

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">{_BASE_STYLE}</head>
<body>
<div class="container">
    <div class="header header-morning">
        <div class="emoji-big">🌅</div>
        <h1>Good Morning, {user_name}!</h1>
        <p>Here is what's on your agenda for Day {day_number}.</p>
    </div>
    <div class="body-content">
        <!-- Plan Overview -->
        <div class="card">
            <div class="card-title">🎯 {plan_title}</div>
            <div class="stat-grid">
                <div class="stat-box">
                    <div class="stat-value">{day_number}</div>
                    <div class="stat-label">Current Day</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{total_days}</div>
                    <div class="stat-label">Total Days</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{overall_progress:.0f}%</div>
                    <div class="stat-label">Progress</div>
                </div>
            </div>
            <div class="progress-bar-outer" style="margin-top:14px;">
                <div class="progress-bar-inner" style="width:{min(100, max(0, overall_progress))}%;"></div>
            </div>
        </div>

        {yesterday_html}

        <!-- Today's Tasks -->
        <div class="card">
            <div class="card-title">📅 Today's Focus — Day {day_number}</div>
            <p style="margin:0 0 4px;font-size:14px;color:#cbd5e1;font-weight:600;">
                {day_objective}
            </p>
            <p style="margin:0 0 12px;font-size:12px;color:#64748b;">
                {len(today_tasks)} tasks &nbsp;·&nbsp; ~{workload_str} planned
            </p>
            {today_items_html}
        </div>
    </div>
    <div class="footer">
        <p>🧠 CareerCoachAI — Your AI Personal Trainer</p>
        <p style="margin-top:6px;">Start strong and conquer today's goals! 🚀</p>
    </div>
</div>
</body>
</html>"""

    return subject, html


# Backward-compatible alias
build_daily_summary_email = build_morning_reminder_email


# =============================================================================
# 3. Evening Progress Wrap-Up Email
# =============================================================================

def build_evening_reminder_email(
    user_name: str,
    plan_title: str,
    overall_progress: float,
    day_number: int,
    day_objective: str,
    completed_today_tasks: list[dict[str, Any]],
    pending_today_tasks: list[dict[str, Any]],
    total_days: int,
) -> tuple[str, str]:
    """Build subject + HTML body for the evening progress wrap-up."""
    subject = f"🌙 Evening Check-In — Day {day_number} Progress Wrap-Up"

    # Completed tasks section
    completed_html = ""
    if completed_today_tasks:
        items = "".join(
            f'<div class="task-item"><span class="task-icon">✅</span><div><p class="task-title">{t.get("title", "Task")}</p><p class="task-meta">{t.get("estimated_minutes", 30)} min</p></div></div>'
            for t in completed_today_tasks
        )
        completed_html = f"""
        <div class="card">
            <div class="card-title" style="color:#34d399;">🏆 Completed Today ({len(completed_today_tasks)})</div>
            {items}
        </div>"""
    else:
        completed_html = """
        <div class="card">
            <div class="card-title">🏆 Completed Today</div>
            <p style="color:#64748b;font-size:13px;margin:0;">No tasks marked completed today yet.</p>
        </div>"""

    # Pending tasks section & nudge
    pending_html = ""
    nudge_html = ""
    if pending_today_tasks:
        items = "".join(
            f'<div class="task-item"><span class="task-icon">⏳</span><div><p class="task-title">{t.get("title", "Task")}</p><p class="task-meta">{t.get("estimated_minutes", 30)} min &nbsp;·&nbsp; {t.get("status", "not_started").replace("_", " ").title()}</p></div></div>'
            for t in pending_today_tasks
        )
        nudge_html = f"""
        <div class="callout">
            <p class="callout-title">⚡ Evening Nudge</p>
            <p class="callout-text">You have <strong>{len(pending_today_tasks)} task{'s' if len(pending_today_tasks) > 1 else ''}</strong> still pending for Day {day_number}. A quick 20-minute push tonight will keep your streak intact!</p>
        </div>"""

        pending_html = f"""
        <div class="card">
            <div class="card-title" style="color:#fbbf24;">⏳ Still Pending ({len(pending_today_tasks)})</div>
            {items}
        </div>"""
    else:
        nudge_html = f"""
        <div class="callout" style="border-left-color:#10b981;background:rgba(16,185,129,0.08);">
            <p class="callout-title" style="color:#34d399;">🎉 Day Complete!</p>
            <p class="callout-text">You've completed all tasks for Day {day_number}! Excellent discipline. Rest up for tomorrow!</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">{_BASE_STYLE}</head>
<body>
<div class="container">
    <div class="header header-evening">
        <div class="emoji-big">🌙</div>
        <h1>Evening Check-In, {user_name}!</h1>
        <p>Here is your Day {day_number} progress summary.</p>
    </div>
    <div class="body-content">
        <!-- Progress Overview -->
        <div class="card">
            <div class="card-title">🎯 {plan_title}</div>
            <div class="stat-grid">
                <div class="stat-box">
                    <div class="stat-value">{len(completed_today_tasks)}</div>
                    <div class="stat-label">Done Today</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{len(pending_today_tasks)}</div>
                    <div class="stat-label">Pending</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{overall_progress:.0f}%</div>
                    <div class="stat-label">Total Progress</div>
                </div>
            </div>
            <div class="progress-bar-outer" style="margin-top:14px;">
                <div class="progress-bar-inner" style="width:{min(100, max(0, overall_progress))}%;"></div>
            </div>
        </div>

        {nudge_html}
        {completed_html}
        {pending_html}
    </div>
    <div class="footer">
        <p>🧠 CareerCoachAI — Your AI Personal Trainer</p>
        <p style="margin-top:6px;">Consistency turns ambition into achievement. ✨</p>
    </div>
</div>
</body>
</html>"""

    return subject, html


# =============================================================================
# High-Level Email Trigger Wrappers
# =============================================================================

def send_task_completed_notification(
    user_email: str,
    user_name: str,
    task_title: str,
    task_type: str,
    estimated_minutes: int,
    day_number: int,
    day_objective: str,
    plan_title: str,
    overall_progress: float,
) -> None:
    """Fire-and-forget: send task completion email in the background."""
    subject, html = build_task_completed_email(
        user_name=user_name,
        task_title=task_title,
        task_type=task_type,
        estimated_minutes=estimated_minutes,
        day_number=day_number,
        day_objective=day_objective,
        plan_title=plan_title,
        overall_progress=overall_progress,
    )
    _fire_and_forget_email(user_email, subject, html)


async def send_morning_reminder_for_user(
    user_email: str,
    user_name: str,
    plan_title: str,
    overall_progress: float,
    day_number: int,
    day_objective: str,
    today_tasks: list[dict[str, Any]],
    yesterday_completed: list[str],
    yesterday_incomplete: list[str],
    total_days: int,
) -> bool:
    """Send the morning briefing email. Used by the morning scheduler cron job."""
    subject, html = build_morning_reminder_email(
        user_name=user_name,
        plan_title=plan_title,
        overall_progress=overall_progress,
        day_number=day_number,
        day_objective=day_objective,
        today_tasks=today_tasks,
        yesterday_completed=yesterday_completed,
        yesterday_incomplete=yesterday_incomplete,
        total_days=total_days,
    )
    return await send_email(user_email, subject, html)


# Backward-compatible alias
send_daily_summary_for_user = send_morning_reminder_for_user


async def send_evening_reminder_for_user(
    user_email: str,
    user_name: str,
    plan_title: str,
    overall_progress: float,
    day_number: int,
    day_objective: str,
    completed_today_tasks: list[dict[str, Any]],
    pending_today_tasks: list[dict[str, Any]],
    total_days: int,
) -> bool:
    """Send the evening wrap-up email. Used by the evening scheduler cron job."""
    subject, html = build_evening_reminder_email(
        user_name=user_name,
        plan_title=plan_title,
        overall_progress=overall_progress,
        day_number=day_number,
        day_objective=day_objective,
        completed_today_tasks=completed_today_tasks,
        pending_today_tasks=pending_today_tasks,
        total_days=total_days,
    )
    return await send_email(user_email, subject, html)
