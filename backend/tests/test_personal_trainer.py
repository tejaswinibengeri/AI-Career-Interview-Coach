"""
Tests for Personal Trainer API endpoints, daily schedules, adaptive rollover,
progress persistence, and n8n webhook notifications.
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.integrations.ai.ollama import OllamaProvider
from app.models.user import User


@pytest.fixture(autouse=True)
def mock_ollama_for_unit_tests():
    """Ensure tests run deterministically and fast without external LLM network latency."""
    with patch.object(OllamaProvider, "health_check", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False
        yield mock_health


@pytest.mark.asyncio
async def test_get_resume_skills(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_user: User,
):
    """Test retrieving user skills from existing profile/resume without duplicate AI parsing."""
    response = await client.get("/api/v1/personal-trainer/resume-skills", headers=auth_headers)
    assert response.status_code == 200
    res_json = response.json()
    data = res_json.get("data", res_json)
    assert "skills" in data
    assert isinstance(data["skills"], list)
    # sample_user profile has Python, FastAPI, React, TypeScript
    assert "Python" in data["skills"]


@pytest.mark.asyncio
async def test_investigate_goal_and_create_plan(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Test deep plan generation with combinations of skill, role, company and daily hour constraints."""
    payload = {
        "goal_dimensions": ["role", "company"],
        "target_role": "AI Engineer",
        "target_company": "Google",
        "target_skill": "Machine Learning",
        "current_skills": ["Python", "SQL"],
        "experience_level": "Intermediate",
        "daily_hours": 3.0,
        "learning_preference": "Balanced",
    }
    response = await client.post(
        "/api/v1/personal-trainer/investigate",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    res_json = response.json()
    data = res_json.get("data", res_json)
    assert "AI Engineer" in data["title"]
    assert data["daily_hours"] == 3.0
    assert len(data["days"]) >= 5

    # Verify daily time limit is respected on Day 1
    day_1 = data["days"][0]
    assert day_1["day_number"] == 1
    assert len(day_1["tasks"]) >= 2
    for task in day_1["tasks"]:
        assert task["estimated_minutes"] > 0
        assert task["task_type"] in ("theory", "practice", "project", "assessment")

    # Sum of day 1 tasks must not exceed daily_hours * 60 (180 mins)
    total_day_mins = sum(t["estimated_minutes"] for t in day_1["tasks"])
    assert total_day_mins <= 180


@pytest.mark.asyncio
async def test_get_active_training_plan(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Test retrieving active plan and overall progress."""
    # Create plan first
    payload = {
        "goal_dimensions": ["skill"],
        "target_skill": "Python Concurrency",
        "current_skills": ["Python"],
        "experience_level": "Beginner",
        "daily_hours": 2.0,
        "learning_preference": "Mostly Practical",
    }
    await client.post("/api/v1/personal-trainer/investigate", json=payload, headers=auth_headers)

    response = await client.get("/api/v1/personal-trainer/active", headers=auth_headers)
    assert response.status_code == 200
    res_json = response.json()
    data = res_json.get("data", res_json)
    assert data is not None
    assert data["is_active"] is True
    assert data["overall_progress"] == 0.0


@pytest.mark.asyncio
async def test_daily_training_view_and_summary(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Test dedicated daily view with AI summary and workload calculation."""
    payload = {
        "goal_dimensions": ["role"],
        "target_role": "Backend Developer",
        "current_skills": ["Python", "FastAPI"],
        "daily_hours": 2.5,
    }
    await client.post("/api/v1/personal-trainer/investigate", json=payload, headers=auth_headers)

    response = await client.get("/api/v1/personal-trainer/daily/1", headers=auth_headers)
    assert response.status_code == 200
    res_json = response.json()
    data = res_json.get("data", res_json)
    assert data["day_number"] == 1
    assert "daily_ai_summary" in data
    assert data["available_minutes"] == 150
    assert data["workload_minutes"] <= 150
    assert data["buffer_minutes"] >= 0


@pytest.mark.asyncio
async def test_task_status_update_and_progress_persistence(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Test completing a task, verifying persistence and overall progress recalculation."""
    # Create plan
    payload = {
        "goal_dimensions": ["skill"],
        "target_skill": "FastAPI",
        "daily_hours": 2.0,
    }
    plan_resp = await client.post("/api/v1/personal-trainer/investigate", json=payload, headers=auth_headers)
    res_json = plan_resp.json()
    plan_data = res_json.get("data", res_json)
    first_task = plan_data["days"][0]["tasks"][0]
    task_id = first_task["id"]

    # Mark complete
    patch_resp = await client.patch(
        f"/api/v1/personal-trainer/tasks/{task_id}",
        json={"status": "completed", "notes": "Solid understanding of dependency injection", "time_spent_minutes": 35},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    p_json = patch_resp.json()
    updated_task = p_json.get("data", p_json)
    assert updated_task["status"] == "completed"
    assert updated_task["notes"] == "Solid understanding of dependency injection"
    assert updated_task["time_spent_minutes"] == 35

    # Check active plan progress has increased
    active_resp = await client.get("/api/v1/personal-trainer/active", headers=auth_headers)
    a_json = active_resp.json()
    active_data = a_json.get("data", a_json)
    assert active_data["overall_progress"] > 0.0


@pytest.mark.asyncio
async def test_reschedule_today_workload(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Test rescheduling today's workload when user only has limited time (e.g. 1 hour)."""
    payload = {
        "goal_dimensions": ["role"],
        "target_role": "Full Stack Engineer",
        "daily_hours": 3.0,
    }
    await client.post("/api/v1/personal-trainer/investigate", json=payload, headers=auth_headers)

    # User says: "I only have 0.75 hours (45 mins) today"
    resched_resp = await client.post(
        "/api/v1/personal-trainer/reschedule-today",
        json={"available_hours": 0.75},
        headers=auth_headers,
    )
    assert resched_resp.status_code == 200
    r_json = resched_resp.json()
    resched_data = r_json.get("data", r_json)
    assert resched_data["workload_minutes"] <= 45


@pytest.mark.asyncio
async def test_day_confidence_review(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Test confidence review submission and recommendation generation."""
    payload = {
        "goal_dimensions": ["role"],
        "target_role": "Data Scientist",
        "daily_hours": 2.0,
    }
    plan_resp = await client.post("/api/v1/personal-trainer/investigate", json=payload, headers=auth_headers)
    p_json = plan_resp.json()
    plan_data = p_json.get("data", p_json)
    day_id = plan_data["days"][0]["id"]

    # Low confidence review
    rev_resp = await client.post(
        f"/api/v1/personal-trainer/days/{day_id}/review",
        json={"confidence_rating": 2, "feedback": "Struggled with eigenvectors"},
        headers=auth_headers,
    )
    assert rev_resp.status_code == 200
    rv_json = rev_resp.json()
    data = rv_json.get("data", rv_json)
    assert data["confidence_rating"] == 2
    assert "extra 45–60 minutes" in data["ai_review_recommendation"]


@pytest.mark.asyncio
async def test_notification_settings_and_unconfigured_webhook(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Test notification settings toggle and verifying n8n webhook returns unconfigured error rather than fake success."""
    # 1. Update settings
    settings_payload = {
        "notifications_enabled": True,
        "preferred_time": "08:30",
        "notification_channel": "email",
    }
    put_resp = await client.put(
        "/api/v1/personal-trainer/settings",
        json=settings_payload,
        headers=auth_headers,
    )
    assert put_resp.status_code == 200
    pt_json = put_resp.json()
    settings_data = pt_json.get("data", pt_json)
    assert settings_data["notifications_enabled"] is True
    assert settings_data["preferred_time"] == "08:30"

    # 2. Trigger webhook when N8N_WEBHOOK_URL is not set
    # Should report not configured and not fake success
    wh_resp = await client.post("/api/v1/personal-trainer/notify-webhook", headers=auth_headers)
    assert wh_resp.status_code == 200
    wh_json = wh_resp.json()
    wh_data = wh_json.get("data", wh_json)
    assert wh_data["success"] is False
    assert "not configured yet" in wh_data["message"]
