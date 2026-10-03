"""
Tests for Learning Resources System & Skill Gap Integration (Module 14).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_learning_resources(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/learning-resources returns seeded verified resources catalog."""
    res = await client.get("/api/v1/learning-resources", headers=auth_headers)
    assert res.status_code == 200
    resources = res.json()["data"]
    assert len(resources) >= 5

    # Filter by skill
    res_python = await client.get("/api/v1/learning-resources?skill_name=Python", headers=auth_headers)
    assert res_python.status_code == 200
    py_resources = res_python.json()["data"]
    assert all("python" in r["skill_name"].lower() for r in py_resources)


@pytest.mark.asyncio
async def test_get_recommended_learning_resources(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/learning-resources/recommended returns resources matching candidate skill gaps."""
    res = await client.get("/api/v1/learning-resources/recommended", headers=auth_headers)
    assert res.status_code == 200
    resources = res.json()["data"]

    assert len(resources) >= 1
    assert all(r["is_recommended_for_gap"] is True for r in resources)


@pytest.mark.asyncio
async def test_toggle_learning_resource_progress(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/learning-resources/{id}/progress saves and completes resources."""
    list_res = await client.get("/api/v1/learning-resources", headers=auth_headers)
    r_id = list_res.json()["data"][0]["id"]

    # 1. Save resource
    save_res = await client.post(
        f"/api/v1/learning-resources/{r_id}/progress",
        json={"is_saved": True},
        headers=auth_headers,
    )
    assert save_res.status_code == 200
    assert save_res.json()["data"]["is_saved"] is True

    # 2. Complete resource
    comp_res = await client.post(
        f"/api/v1/learning-resources/{r_id}/progress",
        json={"is_completed": True},
        headers=auth_headers,
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["data"]["is_completed"] is True
