"""
Tests for User Profile endpoints (/api/v1/profile/*) and user isolation.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import Profile, User


@pytest.fixture
async def second_user(db_session: AsyncSession) -> User:
    """Create a second isolated user."""
    user = User(
        email="seconduser@example.com",
        name="Bob Builder",
        hashed_password=get_password_hash("BobPassword123!"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    profile = Profile(
        user_id=user.id,
        education="Stanford",
        degree="B.S. Mechanical Engineering",
        graduation_year=2023,
        experience="3 years",
        current_role="Hardware Engineer",
        target_role="Robotics Software Engineer",
        skills=["C++", "ROS", "Python"],
        preferred_location="Seattle, WA",
        work_preference="Hybrid",
        career_goal="Build autonomous mobile robotics platforms",
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_profile(
    client: AsyncClient, sample_user: User, auth_headers: dict[str, str]
):
    """GET /api/v1/profile returns current user's profile details."""
    response = await client.get("/api/v1/profile", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["user_id"] == sample_user.id
    assert data["data"]["education"] == "MIT"
    assert "Python" in data["data"]["skills"]


@pytest.mark.asyncio
async def test_update_profile(
    client: AsyncClient, sample_user: User, auth_headers: dict[str, str]
):
    """PUT /api/v1/profile updates fields properly."""
    payload = {
        "name": "Alex Mercer Updated",
        "education": "MIT Graduate School",
        "target_role": "Principal AI Engineer",
        "skills": ["Python", "PyTorch", "FastAPI", "React", "Docker"],
        "work_preference": "Remote",
        "career_goal": "Lead world-class generative AI systems development",
    }
    response = await client.put("/api/v1/profile", headers=auth_headers, json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["education"] == "MIT Graduate School"
    assert data["data"]["target_role"] == "Principal AI Engineer"
    assert "Docker" in data["data"]["skills"]

    # Verify updated name on /api/v1/auth/me
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_resp.json()["data"]["name"] == "Alex Mercer Updated"


@pytest.mark.asyncio
async def test_change_password_success(
    client: AsyncClient, sample_user: User, auth_headers: dict[str, str]
):
    """PUT /api/v1/profile/password with correct current password succeeds."""
    payload = {
        "current_password": "Password123!",
        "new_password": "NewSecretPassword2026!",
    }
    response = await client.put(
        "/api/v1/profile/password", headers=auth_headers, json=payload
    )
    assert response.status_code == 200

    # Verify login with new password
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": sample_user.email, "password": "NewSecretPassword2026!"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(
    client: AsyncClient, sample_user: User, auth_headers: dict[str, str]
):
    """PUT /api/v1/profile/password with incorrect current password returns 400."""
    payload = {
        "current_password": "IncorrectPassword999!",
        "new_password": "NewSecretPassword2026!",
    }
    response = await client.put(
        "/api/v1/profile/password", headers=auth_headers, json=payload
    )
    assert response.status_code == 400
    assert "current password is incorrect" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_user_isolation(
    client: AsyncClient,
    sample_user: User,
    second_user: User,
    auth_headers: dict[str, str],
):
    """User A's token strictly accesses and alters only User A's data."""
    # User A gets profile
    resp_a = await client.get("/api/v1/profile", headers=auth_headers)
    assert resp_a.json()["data"]["user_id"] == sample_user.id
    assert resp_a.json()["data"]["education"] == "MIT"

    # User B gets profile with User B's token
    token_b = create_access_token(
        {"sub": str(second_user.id), "email": second_user.email}
    )
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp_b = await client.get("/api/v1/profile", headers=headers_b)
    assert resp_b.json()["data"]["user_id"] == second_user.id
    assert resp_b.json()["data"]["education"] == "Stanford"

    # User A modifies their profile
    await client.put(
        "/api/v1/profile",
        headers=auth_headers,
        json={"education": "MIT Updated"},
    )

    # Verify User B's profile remained completely untouched
    resp_b_check = await client.get("/api/v1/profile", headers=headers_b)
    assert resp_b_check.json()["data"]["education"] == "Stanford"
