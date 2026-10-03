"""
Comprehensive unit and integration tests for Module 05: Career Selection and Skill Gap Analysis.
"""

import json
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.integrations.ai.ollama import OllamaProvider
from app.models.user import User


SAMPLE_AI_SKILL_GAP_OUTPUT = json.dumps({
    "explanation": "You have a solid foundation in Python and SQL. However, to excel as a Data Scientist, mastering Machine Learning algorithms, Pandas, and PyTorch is essential.",
    "learning_order": [
        {"step": 1, "skill_name": "Pandas / NumPy", "priority": "High", "rationale": "Prerequisite for data manipulation and analysis."},
        {"step": 2, "skill_name": "Machine Learning", "priority": "High", "rationale": "Core requirement for model building."},
        {"step": 3, "skill_name": "PyTorch", "priority": "Medium", "rationale": "Advanced deep learning framework capability."}
    ]
})


@pytest.mark.asyncio
async def test_search_careers(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/careers searches O*NET occupation taxonomy."""
    response = await client.get("/api/v1/careers?q=Software", headers=auth_headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    data = payload["data"]
    assert len(data) > 0
    assert any("Software" in occ["title"] for occ in data)


@pytest.mark.asyncio
async def test_get_career_detail(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/careers/{id} returns details and required skills for an occupation."""
    # First search for career ID
    res = await client.get("/api/v1/careers?q=Software", headers=auth_headers)
    career_id = res.json()["data"][0]["id"]

    detail_res = await client.get(f"/api/v1/careers/{career_id}", headers=auth_headers)
    assert detail_res.status_code == 200

    data = detail_res.json()["data"]
    assert data["id"] == career_id
    assert len(data["skills"]) > 0
    assert "code" in data


@pytest.mark.asyncio
async def test_generate_skill_gap_report(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/career/skill-gap performs deterministic matching and generates Ollama AI roadmap."""
    # Get career ID
    res = await client.get("/api/v1/careers?q=Data%20Scientist", headers=auth_headers)
    careers = res.json()["data"]
    career_id = careers[0]["id"] if careers else 1

    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_AI_SKILL_GAP_OUTPUT

        response = await client.post(
            "/api/v1/career/skill-gap",
            json={"occupation_id": career_id},
            headers=auth_headers,
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["status"] == "success"
        data = payload["data"]

        assert "match_percentage" in data
        assert "ai_explanation" in data
        assert len(data["learning_order"]) == 3

        # Verify GET /api/v1/career/skill-gap/latest retrieves the report
        latest_res = await client.get("/api/v1/career/skill-gap/latest", headers=auth_headers)
        assert latest_res.status_code == 200
        assert latest_res.json()["data"]["id"] == data["id"]


@pytest.mark.asyncio
async def test_ollama_unavailable_returns_503(client: AsyncClient, auth_headers: dict[str, str]):
    """When Ollama is offline, skill gap endpoint returns 503 Service Unavailable."""
    res = await client.get("/api/v1/careers?limit=1", headers=auth_headers)
    career_id = res.json()["data"][0]["id"]

    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = ConnectionError("Cannot connect to Ollama")

        response = await client.post(
            "/api/v1/career/skill-gap",
            json={"occupation_id": career_id},
            headers=auth_headers,
        )
        assert response.status_code == 503
        assert "unavailable" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_set_career_goal(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/career/goal sets active career goal for authenticated user."""
    res = await client.get("/api/v1/careers?q=DevOps", headers=auth_headers)
    careers = res.json()["data"]
    career_id = careers[0]["id"] if careers else 1

    response = await client.post(
        "/api/v1/career/goal",
        json={"occupation_id": career_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "updated" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_user_isolation_skill_gap(client: AsyncClient, db_session: AsyncSession):
    """User B cannot access User A's skill gap report (returns 404)."""
    user_b = User(
        email="user_b_career@example.com",
        name="User B Career",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({"sub": str(user_b.id), "email": user_b.email})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    response = await client.get("/api/v1/career/skill-gap/latest", headers=headers_b)
    assert response.status_code == 404
