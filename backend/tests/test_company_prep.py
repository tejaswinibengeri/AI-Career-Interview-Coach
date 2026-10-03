"""
Tests for Company-Specific Preparation System (Module 13).
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def mock_ollama_provider():
    """Autouse fixture to prevent real Ollama network timeouts during tests."""
    mock_json = """
    {
      "company_overview": "Verified company overview.",
      "role_summary": "Role expectations summary.",
      "required_skills": ["Python", "System Design", "Distributed Systems"],
      "technical_prep_topics": [
        {"topic": "System Design", "description": "Microservices", "importance": "High"}
      ],
      "coding_topics": ["Arrays", "Trees"],
      "hr_topics": ["Why this company?"],
      "behavioral_prep": [
        {"principle": "Leadership", "advice": "Focus on impact", "example_prompt": "Tell me about a project."}
      ],
      "practice_questions": [
        {
          "question_text": "How do you design a rate limiter?",
          "category": "System Design",
          "difficulty": "Hard",
          "label": "AI-generated practice question",
          "sample_answer_points": ["Token bucket algorithm", "Redis storage"]
        }
      ]
    }
    """
    with patch("app.integrations.ai.ollama.OllamaProvider.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_json
        yield mock_gen


@pytest.mark.asyncio
async def test_create_company_prep_verified_company(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/company-prep generates plan for a verified company (Google)."""
    res = await client.post(
        "/api/v1/company-prep",
        json={"company_name": "Google", "target_role": "Software Engineer"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["company_name"] == "Google"
    assert data["target_role"] == "Software Engineer"
    assert data["is_verified_company"] is True
    assert data["verification_notes"] is None
    assert len(data["practice_questions"]) >= 1

    # Verify practice question mandatory labeling requirement
    for q in data["practice_questions"]:
        assert q["label"] == "AI-generated practice question"


@pytest.mark.asyncio
async def test_create_company_prep_unverified_company(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/company-prep generates plan with disclaimer note for unverified company."""
    res = await client.post(
        "/api/v1/company-prep",
        json={"company_name": "Acme Futuristic Tech 999", "target_role": "Backend Engineer"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["company_name"] == "Acme Futuristic Tech 999"
    assert data["is_verified_company"] is False
    assert "could not be verified" in data["verification_notes"]
    assert len(data["practice_questions"]) >= 1

    # Verify practice question mandatory labeling requirement
    for q in data["practice_questions"]:
        assert q["label"] == "AI-generated practice question"


@pytest.mark.asyncio
async def test_get_saved_company_prep_plans(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/company-prep lists saved prep plans for the user."""
    # Create plan
    create_res = await client.post(
        "/api/v1/company-prep",
        json={"company_name": "Amazon", "target_role": "Cloud Architect"},
        headers=auth_headers,
    )
    plan_id = create_res.json()["data"]["id"]

    # List plans
    list_res = await client.get("/api/v1/company-prep", headers=auth_headers)
    assert list_res.status_code == 200
    plans = list_res.json()["data"]
    assert len(plans) >= 1
    assert any(p["id"] == plan_id for p in plans)

    # Get single detail
    detail_res = await client.get(f"/api/v1/company-prep/{plan_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()["data"]
    assert detail["company_name"] == "Amazon"
