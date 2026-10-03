"""
Tests for AI Project Recommendations System (Module 15).
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def mock_ollama_provider():
    """Autouse fixture to prevent real Ollama network timeouts during tests."""
    mock_json = """
    [
      {
        "title": "Beginner Task API",
        "difficulty": "Beginner",
        "description": "Simple REST API using FastAPI.",
        "technologies": ["Python", "FastAPI"],
        "features": ["CRUD Endpoints"],
        "skills_learned": ["REST APIs"],
        "expected_outcome": "Working repository."
      },
      {
        "title": "Intermediate Analytics Platform",
        "difficulty": "Intermediate",
        "description": "Full stack dashboard.",
        "technologies": ["React", "FastAPI", "PostgreSQL"],
        "features": ["Dashboard Analytics", "Auth"],
        "skills_learned": ["Full Stack Integration"],
        "expected_outcome": "Full stack app."
      },
      {
        "title": "Advanced Microservice Gateway",
        "difficulty": "Advanced",
        "description": "High scale architecture.",
        "technologies": ["Docker", "Redis", "Kafka"],
        "features": ["Caching", "Message Queue"],
        "skills_learned": ["System Architecture"],
        "expected_outcome": "Production system."
      }
    ]
    """
    with patch("app.integrations.ai.ollama.OllamaProvider.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_json
        yield mock_gen


@pytest.mark.asyncio
async def test_generate_project_recommendations(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/projects/recommendations generates 3 tiered personalized projects."""
    res = await client.post("/api/v1/projects/recommendations", headers=auth_headers)
    assert res.status_code == 200
    projects = res.json()["data"]

    assert len(projects) == 3
    difficulties = set(p["difficulty"] for p in projects)
    assert "Beginner" in difficulties
    assert "Intermediate" in difficulties
    assert "Advanced" in difficulties


@pytest.mark.asyncio
async def test_list_and_filter_project_recommendations(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/projects lists recommendations and filters by difficulty and status."""
    await client.post("/api/v1/projects/recommendations", headers=auth_headers)

    # 1. List all
    res = await client.get("/api/v1/projects", headers=auth_headers)
    assert res.status_code == 200
    all_projects = res.json()["data"]
    assert len(all_projects) >= 3

    # 2. Filter by difficulty
    res_beg = await client.get("/api/v1/projects?difficulty=Beginner", headers=auth_headers)
    assert res_beg.status_code == 200
    beg_projects = res_beg.json()["data"]
    assert all(p["difficulty"] == "Beginner" for p in beg_projects)


@pytest.mark.asyncio
async def test_update_project_status(client: AsyncClient, auth_headers: dict[str, str]):
    """PATCH /api/v1/projects/{id}/status saves project and updates execution status."""
    gen_res = await client.post("/api/v1/projects/recommendations", headers=auth_headers)
    p_id = gen_res.json()["data"][0]["id"]

    # 1. Save project
    save_res = await client.patch(
        f"/api/v1/projects/{p_id}/status",
        json={"is_saved": True},
        headers=auth_headers,
    )
    assert save_res.status_code == 200
    assert save_res.json()["data"]["is_saved"] is True

    # 2. Mark started (In Progress)
    start_res = await client.patch(
        f"/api/v1/projects/{p_id}/status",
        json={"status": "In Progress"},
        headers=auth_headers,
    )
    assert start_res.status_code == 200
    assert start_res.json()["data"]["status"] == "In Progress"

    # 3. Mark completed
    comp_res = await client.patch(
        f"/api/v1/projects/{p_id}/status",
        json={"status": "Completed"},
        headers=auth_headers,
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["data"]["status"] == "Completed"
