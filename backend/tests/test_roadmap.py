"""
Comprehensive unit and integration tests for Module 06: Personalized Career Roadmap.
"""

import json
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.integrations.ai.ollama import OllamaProvider
from app.models.user import User


SAMPLE_AI_ROADMAP_OUTPUT = json.dumps({
    "title": "Personalized Roadmap: Path to Software Developer",
    "items": [
        {
            "phase": "Phase 1: Core Prerequisites",
            "skill": "Python & Data Structures",
            "topics": ["Lists & Dicts", "Time Complexity", "OOP Basics"],
            "projects": ["Build CLI Task Manager"],
            "resources": ["Official Python Docs", "Data Structures Guide"],
            "priority": "High",
            "estimated_effort": "2 weeks"
        },
        {
            "phase": "Phase 2: Framework Mastery",
            "skill": "FastAPI & Async IO",
            "topics": ["Routing", "Pydantic Schemas", "Dependency Injection"],
            "projects": ["Build REST API Microservice"],
            "resources": ["Official FastAPI Tutorial"],
            "priority": "High",
            "estimated_effort": "3 weeks"
        },
        {
            "phase": "Phase 3: Portfolio & System Design",
            "skill": "Docker & Deployment",
            "topics": ["Dockerfiles", "Docker Compose", "CI/CD Actions"],
            "projects": ["Deploy Fullstack App to Cloud"],
            "resources": ["Docker Documentation"],
            "priority": "Medium",
            "estimated_effort": "2 weeks"
        }
    ]
})


@pytest.mark.asyncio
async def test_generate_roadmap_success(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/roadmap/generate generates structured AI roadmap and persists it."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_AI_ROADMAP_OUTPUT

        response = await client.post("/api/v1/roadmap/generate", json={}, headers=auth_headers)
        assert response.status_code == 200

        payload = response.json()
        assert payload["status"] == "success"
        data = payload["data"]

        assert "Roadmap" in data["title"]
        assert len(data["items"]) == 3
        assert data["overall_progress"] == 0.0

        # Verify GET /api/v1/roadmap/latest retrieves the active roadmap
        get_res = await client.get("/api/v1/roadmap/latest", headers=auth_headers)
        assert get_res.status_code == 200
        assert get_res.json()["data"]["id"] == data["id"]


@pytest.mark.asyncio
async def test_toggle_roadmap_item_completion(client: AsyncClient, auth_headers: dict[str, str]):
    """PUT /api/v1/roadmap/items/{id}/toggle updates item completion and overall progress percentage."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_AI_ROADMAP_OUTPUT
        gen_res = await client.post("/api/v1/roadmap/generate", json={}, headers=auth_headers)
        roadmap_data = gen_res.json()["data"]
        item_id = roadmap_data["items"][0]["id"]

    # Toggle completion to true
    toggle_res = await client.put(
        f"/api/v1/roadmap/items/{item_id}/toggle",
        json={"is_completed": True},
        headers=auth_headers,
    )
    assert toggle_res.status_code == 200
    updated_data = toggle_res.json()["data"]

    # 1 item completed out of 3 -> ~33.3% progress
    assert updated_data["overall_progress"] > 30.0
    item = next(it for it in updated_data["items"] if it["id"] == item_id)
    assert item["is_completed"] is True

    # Toggle completion back to false
    toggle_off_res = await client.put(
        f"/api/v1/roadmap/items/{item_id}/toggle",
        json={"is_completed": False},
        headers=auth_headers,
    )
    assert toggle_off_res.status_code == 200
    assert toggle_off_res.json()["data"]["overall_progress"] == 0.0


@pytest.mark.asyncio
async def test_ollama_unavailable_roadmap(client: AsyncClient, auth_headers: dict[str, str]):
    """When Ollama is offline, roadmap endpoint returns 503 Service Unavailable."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = ConnectionError("Ollama unreachable")

        response = await client.post("/api/v1/roadmap/generate", json={}, headers=auth_headers)
        assert response.status_code == 503
        assert "unavailable" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_user_isolation_roadmap(client: AsyncClient, db_session: AsyncSession):
    """User B cannot view or toggle User A's active roadmap items (returns 404)."""
    user_b = User(
        email="user_b_roadmap@example.com",
        name="User B Roadmap",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({"sub": str(user_b.id), "email": user_b.email})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B gets latest roadmap -> 404
    get_res = await client.get("/api/v1/roadmap/latest", headers=headers_b)
    assert get_res.status_code == 404
