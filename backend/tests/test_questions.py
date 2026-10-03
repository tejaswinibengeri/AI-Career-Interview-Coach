"""
Comprehensive unit and integration tests for Module 09: Interview Question Bank.
"""

import json
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.integrations.ai.ollama import OllamaProvider

SAMPLE_AI_QUESTIONS_OUTPUT = json.dumps({
    "questions": [
        {
            "question": "What is the Virtual DOM in React and how does reconciliation work?",
            "category": "Technical",
            "difficulty": "Medium",
            "role": "Frontend Engineer",
            "tags": ["React", "Virtual DOM", "Frontend"],
            "explanation": "The Virtual DOM is a lightweight in-memory representation of the real DOM. Reconciliation is the diffing algorithm React uses to efficiently update only modified DOM nodes."
        },
        {
            "question": "Explain the difference between useEffect and useLayoutEffect hooks in React.",
            "category": "Technical",
            "difficulty": "Hard",
            "role": "Frontend Engineer",
            "tags": ["React", "Hooks", "JavaScript"],
            "explanation": "useEffect runs asynchronously after paint. useLayoutEffect runs synchronously after DOM mutations but before paint."
        }
    ]
})


@pytest.mark.asyncio
async def test_list_and_seed_questions(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/questions seeds standard initial questions and returns list."""
    response = await client.get("/api/v1/questions", headers=auth_headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    data = payload["data"]
    assert len(data) >= 5
    assert data[0]["source_label"] == "Standard Interview Question"


@pytest.mark.asyncio
async def test_filter_questions_by_category_and_difficulty(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/questions filters by category and difficulty."""
    response = await client.get("/api/v1/questions?category=DSA&difficulty=Easy", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()["data"]
    assert len(data) >= 1
    assert data[0]["category"] == "DSA"
    assert data[0]["difficulty"] == "Easy"


@pytest.mark.asyncio
async def test_get_random_question(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/questions/random returns a random practice question."""
    response = await client.get("/api/v1/questions/random", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()["data"]
    assert "question" in data
    assert "category" in data


@pytest.mark.asyncio
async def test_generate_ai_questions(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/questions/generate synthesizes AI questions explicitly marked as 'AI-generated practice question'."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_AI_QUESTIONS_OUTPUT

        req_body = {
            "topic": "React Hooks",
            "category": "Technical",
            "difficulty": "Medium",
            "role": "Frontend Engineer",
            "count": 2,
        }
        response = await client.post("/api/v1/questions/generate", json=req_body, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()["data"]
        assert len(data) == 2
        assert data[0]["source_type"] == "ai_generated"
        assert data[0]["source_label"] == "AI-generated practice question"


@pytest.mark.asyncio
async def test_save_and_unsave_question(client: AsyncClient, auth_headers: dict[str, str]):
    """Users can bookmark/save interview questions and filter saved questions."""
    list_res = await client.get("/api/v1/questions", headers=auth_headers)
    question_id = list_res.json()["data"][0]["id"]

    # Save question
    save_res = await client.post(f"/api/v1/questions/{question_id}/save", headers=auth_headers)
    assert save_res.status_code == 200
    assert save_res.json()["data"]["is_saved"] is True

    # Retrieve saved only
    saved_list_res = await client.get("/api/v1/questions?saved_only=true", headers=auth_headers)
    assert saved_list_res.status_code == 200
    saved_data = saved_list_res.json()["data"]
    assert any(q["id"] == question_id for q in saved_data)

    # Unsave question
    unsave_res = await client.delete(f"/api/v1/questions/{question_id}/save", headers=auth_headers)
    assert unsave_res.status_code == 200
    assert unsave_res.json()["data"]["is_saved"] is False


@pytest.mark.asyncio
async def test_generate_ai_questions_offline_fallback(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/questions/generate succeeds even when Ollama raises ConnectionError."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = ConnectionError("Ollama unreachable")

        req_body = {
            "topic": "SQL Indexing",
            "category": "SQL",
            "difficulty": "Hard",
            "role": "Database Engineer",
            "count": 3,
        }
        response = await client.post("/api/v1/questions/generate", json=req_body, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()["data"]
        assert len(data) == 3
        assert data[0]["source_type"] == "ai_generated"
        assert data[0]["source_label"] == "AI-generated practice question"
        assert data[0]["category"] == "SQL"


@pytest.mark.asyncio
async def test_generate_ai_questions_malformed_json_fallback(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/questions/generate recovers gracefully when Ollama returns non-JSON text."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = "Here are questions: 1. Explain B-Tree. 2. What is WAL?"

        req_body = {
            "topic": "Storage Engines",
            "category": "Technical",
            "difficulty": "Medium",
            "role": "Systems Engineer",
            "count": 4,
        }
        response = await client.post("/api/v1/questions/generate", json=req_body, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()["data"]
        assert len(data) == 4
        assert data[0]["source_type"] == "ai_generated"

