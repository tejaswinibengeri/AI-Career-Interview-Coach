"""
Comprehensive unit and integration tests for Module 08: Resume-to-Job Matching.
"""

import json
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.integrations.ai.ollama import OllamaProvider
from app.integrations.jobs.adzuna import AdzunaJobProvider
from app.integrations.jobs.base import NormalizedJobData
from app.models.user import User

SAMPLE_NORMALIZED_JOBS = [
    NormalizedJobData(
        external_id="adzuna-201",
        provider="adzuna",
        title="Python Backend Software Engineer",
        company="PyTech Solutions",
        location="Austin, TX",
        is_remote=True,
        description="We are seeking a Python engineer proficient in FastAPI, SQL databases, Docker, and REST APIs.",
        salary_min=115000.0,
        salary_max=145000.0,
        salary_currency="USD",
        redirect_url="https://www.adzuna.com/land/ad/201",
    )
]

SAMPLE_AI_JOB_MATCH_OUTPUT = json.dumps({
    "explanation": "The candidate presents a strong 85% compatibility match for the Python Backend Software Engineer position at PyTech Solutions, demonstrating solid foundational knowledge in Python, SQL, and FastAPI.",
    "recommendations": [
        "Add explicit Docker deployment projects to your resume skills section.",
        "Highlight experience with REST API design patterns."
    ]
})


@pytest.mark.asyncio
async def test_match_resume_to_job_success(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/jobs/{id}/match calculates deterministic compatibility score and generates AI explanation."""
    with patch.object(AdzunaJobProvider, "search_jobs", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = SAMPLE_NORMALIZED_JOBS
        search_res = await client.get("/api/v1/jobs?q=Python", headers=auth_headers)
        job_id = search_res.json()["data"][0]["id"]

    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_AI_JOB_MATCH_OUTPUT

        response = await client.post(f"/api/v1/jobs/{job_id}/match", headers=auth_headers)
        assert response.status_code == 200

        payload = response.json()
        assert payload["status"] == "success"
        data = payload["data"]

        assert data["job_id"] == job_id
        assert data["match_score"] > 0
        assert "Python" in data["explanation"]
        assert len(data["recommendations"]) == 2

        # Verify GET /api/v1/jobs/{id}/match retrieves persisted report
        get_res = await client.get(f"/api/v1/jobs/{job_id}/match", headers=auth_headers)
        assert get_res.status_code == 200
        assert get_res.json()["data"]["id"] == data["id"]


@pytest.mark.asyncio
async def test_job_match_ollama_unavailable(client: AsyncClient, auth_headers: dict[str, str]):
    """When Ollama is offline, matching returns 503 Service Unavailable."""
    with patch.object(AdzunaJobProvider, "search_jobs", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = SAMPLE_NORMALIZED_JOBS
        search_res = await client.get("/api/v1/jobs?q=Python", headers=auth_headers)
        job_id = search_res.json()["data"][0]["id"]

    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = ConnectionError("Ollama unreachable")

        response = await client.post(f"/api/v1/jobs/{job_id}/match", headers=auth_headers)
        assert response.status_code == 503
        assert "unavailable" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_user_isolation_job_match(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict[str, str]
):
    """User B cannot view User A's private job match report."""
    with patch.object(AdzunaJobProvider, "search_jobs", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = SAMPLE_NORMALIZED_JOBS
        search_res = await client.get("/api/v1/jobs?q=Python", headers=auth_headers)
        job_id = search_res.json()["data"][0]["id"]

    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_AI_JOB_MATCH_OUTPUT
        await client.post(f"/api/v1/jobs/{job_id}/match", headers=auth_headers)

    # Create User B
    user_b = User(
        email="user_b_match@example.com",
        name="User B Match",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({"sub": str(user_b.id), "email": user_b.email})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B requests User A's job match -> 404
    get_res = await client.get(f"/api/v1/jobs/{job_id}/match", headers=headers_b)
    assert get_res.status_code == 404
