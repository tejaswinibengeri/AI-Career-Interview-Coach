"""
Tests for Dashboard API endpoints (Module 02).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import Profile, User


@pytest.mark.asyncio
async def test_get_dashboard_unauthorized(client: AsyncClient):
    """GET /api/v1/dashboard without authentication header should return 401."""
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 401
    json_data = response.json()
    assert json_data["status"] == "error"


@pytest.mark.asyncio
async def test_get_dashboard_success(client: AsyncClient, sample_user: User, auth_headers: dict[str, str]):
    """GET /api/v1/dashboard with valid token returns aggregated real user data and empty states."""
    response = await client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    data = payload["data"]

    # Welcome message
    assert data["welcome_message"] == "Welcome back, Alex Mercer!"

    # Profile summary
    profile = data["profile"]
    assert profile["name"] == "Alex Mercer"
    assert profile["email"] == "testuser@example.com"
    assert profile["current_role"] == "Junior Software Engineer"
    assert profile["target_role"] == "Senior Full Stack Engineer"
    assert profile["completion_percentage"] == 100

    # Career goal
    assert data["career_goal"] == "Lead high-impact full stack architecture projects"

    # Skills summary
    skills = data["skills"]
    assert skills["total_skills"] == 4
    assert "Python" in skills["skills"]
    assert "FastAPI" in skills["skills"]

    # Module empty states (no fake metrics!)
    assert data["resume"]["has_resume"] is False
    assert data["resume"]["status"] == "no_resume"
    assert data["resume"]["latest_ats_score"] is None

    assert data["interviews"]["total_mock_interviews"] == 0
    assert data["interviews"]["average_score"] is None

    assert data["coding"]["total_problems_solved"] == 0
    assert data["coding"]["streak_days"] == 0

    assert data["placement_readiness"]["readiness_score"] == 60.0
    assert data["placement_readiness"]["level"] == "Needs Preparation"


    # Recent activity
    assert len(data["recent_activity"]) >= 1
    assert data["recent_activity"][0]["title"] in ["Account Created", "Profile Updated"]


@pytest.mark.asyncio
async def test_dashboard_user_data_isolation(
    client: AsyncClient, db_session: AsyncSession, sample_user: User, auth_headers: dict[str, str]
):
    """Ensure User A cannot see User B's dashboard information."""
    # Create User B
    user_b = User(
        email="user_b@example.com",
        name="User B",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
    )
    db_session.add(user_b)
    await db_session.flush()

    profile_b = Profile(
        user_id=user_b.id,
        current_role="Student",
        target_role="Data Scientist",
        skills=["Python", "SQL"],
        career_goal="Become a Principal Data Scientist",
    )
    db_session.add(profile_b)
    await db_session.commit()

    token_b = create_access_token({"sub": str(user_b.id), "email": user_b.email})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Fetch User B dashboard
    res_b = await client.get("/api/v1/dashboard", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.json()["data"]

    # Verify User B sees only their data
    assert data_b["welcome_message"] == "Welcome back, User B!"
    assert data_b["profile"]["name"] == "User B"
    assert data_b["profile"]["current_role"] == "Student"
    assert data_b["career_goal"] == "Become a Principal Data Scientist"
    assert data_b["skills"]["skills"] == ["Python", "SQL"]

    # Verify User A dashboard remains unchanged
    res_a = await client.get("/api/v1/dashboard", headers=auth_headers)
    assert res_a.status_code == 200
    data_a = res_a.json()["data"]
    assert data_a["welcome_message"] == "Welcome back, Alex Mercer!"
    assert data_a["profile"]["name"] == "Alex Mercer"


@pytest.mark.asyncio
async def test_dashboard_reflects_profile_updates(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Updating user profile immediately updates dashboard output."""
    # Update profile
    update_payload = {
        "name": "Alex Mercer Updated",
        "target_role": "AI Architect",
        "skills": ["Python", "PyTorch", "FastAPI", "React", "Docker"],
        "career_goal": "Build world-class AI agent systems",
    }
    update_res = await client.put("/api/v1/profile", json=update_payload, headers=auth_headers)
    assert update_res.status_code == 200

    # Fetch updated dashboard
    dash_res = await client.get("/api/v1/dashboard", headers=auth_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]

    assert dash_data["welcome_message"] == "Welcome back, Alex Mercer Updated!"
    assert dash_data["profile"]["name"] == "Alex Mercer Updated"
    assert dash_data["profile"]["target_role"] == "AI Architect"
    assert dash_data["career_goal"] == "Build world-class AI agent systems"
    assert dash_data["skills"]["total_skills"] == 5
    assert "PyTorch" in dash_data["skills"]["skills"]
