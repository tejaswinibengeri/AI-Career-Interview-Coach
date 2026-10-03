"""
Tests for Admin Panel System & Backend Authorization Enforcement (Module 20).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_non_admin_user_forbidden_from_admin_panel(client: AsyncClient, auth_headers: dict[str, str]):
    """Backend strictly enforces 403 Forbidden on non-admin users attempting to access admin endpoints."""
    # 1. Statistics endpoint
    res_stats = await client.get("/api/v1/admin/statistics", headers=auth_headers)
    assert res_stats.status_code == 403
    assert "Admin authorization required" in res_stats.json()["message"]

    # 2. Users endpoint
    res_users = await client.get("/api/v1/admin/users", headers=auth_headers)
    assert res_users.status_code == 403

    # 3. Questions endpoint
    res_q = await client.get("/api/v1/admin/questions", headers=auth_headers)
    assert res_q.status_code == 403

    # 4. Resources endpoint
    res_r = await client.get("/api/v1/admin/resources", headers=auth_headers)
    assert res_r.status_code == 403


@pytest.mark.asyncio
async def test_admin_user_statistics_and_management(
    client: AsyncClient, auth_headers: dict[str, str], sample_user: User, db_session: AsyncSession
):
    """Admin user can successfully access real aggregated statistics and management resources."""
    # Promote sample user to admin
    sample_user.is_superuser = True
    sample_user.role = "admin"
    await db_session.commit()

    # 1. GET /api/v1/admin/statistics
    res_stats = await client.get("/api/v1/admin/statistics", headers=auth_headers)
    assert res_stats.status_code == 200
    data = res_stats.json()["data"]

    assert "total_users" in data
    assert data["total_users"] >= 1
    assert "active_users" in data
    assert "resumes" in data
    assert "interviews" in data
    assert "coding_submissions" in data

    # 2. GET /api/v1/admin/users
    res_users = await client.get("/api/v1/admin/users", headers=auth_headers)
    assert res_users.status_code == 200
    user_list = res_users.json()["data"]
    assert len(user_list) >= 1

    # 3. Question Bank CRUD
    res_create_q = await client.post(
        "/api/v1/admin/questions",
        json={
            "category": "Technical",
            "role": "Software Engineer",
            "difficulty": "Medium",
            "question_text": "Explain Python GIL and Asyncio event loop concurrency.",
        },
        headers=auth_headers,
    )

    assert res_create_q.status_code == 201
    q_data = res_create_q.json()["data"]
    q_id = q_data["id"]

    res_del_q = await client.delete(f"/api/v1/admin/questions/{q_id}", headers=auth_headers)
    assert res_del_q.status_code == 200

    # 4. Learning Resources CRUD
    res_create_r = await client.post(
        "/api/v1/admin/resources",
        json={
            "title": "FastAPI Official Admin Guide",
            "description": "Comprehensive FastAPI framework documentation",
            "url": "https://fastapi.tiangolo.com/",
            "skill_name": "FastAPI",
            "source": "Official Documentation",
            "difficulty": "Intermediate",
            "resource_type": "Documentation",
        },
        headers=auth_headers,
    )

    assert res_create_r.status_code == 201
    r_data = res_create_r.json()["data"]
    r_id = r_data["id"]

    res_del_r = await client.delete(f"/api/v1/admin/resources/{r_id}", headers=auth_headers)
    assert res_del_r.status_code == 200
