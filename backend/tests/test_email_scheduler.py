"""
Tests for Personal Trainer scheduled email notification system.
Tests templates, time parsing, and scheduler configuration.
"""

import pytest
from app.core.config import settings
from app.core.scheduler import _parse_time
from app.services.email_service import (
    build_evening_reminder_email,
    build_morning_reminder_email,
    build_task_completed_email,
)


def test_time_parser():
    """Verify time parsing utility converts strings properly and handles fallbacks."""
    assert _parse_time("07:30", 8, 0) == (7, 30)
    assert _parse_time("08:00", 8, 0) == (8, 0)
    assert _parse_time("20:15", 20, 0) == (20, 15)
    assert _parse_time("00:00", 8, 0) == (0, 0)
    assert _parse_time("23:59", 8, 0) == (23, 59)

    # Invalid cases fallback to defaults
    assert _parse_time("invalid", 8, 0) == (8, 0)
    assert _parse_time("25:00", 8, 0) == (8, 0)
    assert _parse_time("12:65", 8, 0) == (8, 0)
    assert _parse_time("", 8, 0) == (8, 0)


def test_build_task_completed_email():
    """Verify task completion real-time email template structure."""
    subject, html = build_task_completed_email(
        user_name="John Doe",
        task_title="Build FastAPI Auth Module",
        task_type="project",
        estimated_minutes=45,
        day_number=3,
        day_objective="Build core API backend",
        plan_title="Full Stack Engineer Plan",
        overall_progress=35.5,
    )

    assert "✅ Task Completed — Build FastAPI Auth Module" in subject
    assert "John Doe" in html
    assert "Build FastAPI Auth Module" in html
    assert "45 min" in html
    assert "Day 3" in html
    assert "35.5%" in html


def test_build_morning_reminder_email_with_yesterday_leftovers():
    """Verify morning briefing email formats yesterday's incomplete tasks and today's agenda."""
    today_tasks = [
        {"title": "Study System Design Patterns", "task_type": "theory", "estimated_minutes": 30, "status": "not_started"},
        {"title": "Write LeetCode Hard Solution", "task_type": "practice", "estimated_minutes": 45, "status": "not_started"},
    ]
    yesterday_completed = ["Setup Docker Container"]
    yesterday_incomplete = ["Write Pytest Unit Tests"]

    subject, html = build_morning_reminder_email(
        user_name="Alice",
        plan_title="Backend Master",
        overall_progress=40.0,
        day_number=4,
        day_objective="Advanced Microservices",
        today_tasks=today_tasks,
        yesterday_completed=yesterday_completed,
        yesterday_incomplete=yesterday_incomplete,
        total_days=14,
    )

    assert "🌅 Morning Briefing — Day 4: Backend Master" in subject
    assert "Alice" in html
    assert "Day 4" in html
    assert "Study System Design Patterns" in html
    assert "Write LeetCode Hard Solution" in html
    # Yesterday callback verification
    assert "Yesterday's Leftover Note" in html
    assert "Write Pytest Unit Tests" in html
    assert "Setup Docker Container" in html


def test_build_evening_reminder_email_with_pending_tasks():
    """Verify evening wrap-up email highlights completed vs pending tasks and adds nudge."""
    completed_today = [
        {"title": "Morning Warmup Task", "estimated_minutes": 20, "status": "completed"}
    ]
    pending_today = [
        {"title": "Evening Code Review", "estimated_minutes": 30, "status": "in_progress"}
    ]

    subject, html = build_evening_reminder_email(
        user_name="Bob",
        plan_title="DevOps Specialist",
        overall_progress=60.0,
        day_number=5,
        day_objective="Kubernetes Deployments",
        completed_today_tasks=completed_today,
        pending_today_tasks=pending_today,
        total_days=10,
    )

    assert "🌙 Evening Check-In — Day 5 Progress Wrap-Up" in subject
    assert "Bob" in html
    assert "Completed Today (1)" in html
    assert "Still Pending (1)" in html
    assert "Morning Warmup Task" in html
    assert "Evening Code Review" in html
    assert "Evening Nudge" in html
