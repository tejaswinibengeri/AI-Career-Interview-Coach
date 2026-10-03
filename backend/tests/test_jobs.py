"""
Comprehensive unit and integration tests for Module 07: Real Job Search.
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.integrations.jobs.adzuna import AdzunaJobProvider
from app.integrations.jobs.base import NormalizedJobData
from app.models.user import User

SAMPLE_NORMALIZED_JOBS = [
    NormalizedJobData(
        external_id="adzuna-101",
        provider="adzuna",
        title="Senior Python / FastAPI Developer",
        company="TechCorp Innovations",
        location="San Francisco, CA",
        is_remote=True,
        description="Design and implement high performance RESTful microservices using Python and FastAPI.",
        salary_min=120000.0,
        salary_max=150000.0,
        salary_currency="USD",
        redirect_url="https://www.adzuna.com/land/ad/101",
    ),
    NormalizedJobData(
        external_id="adzuna-102",
        provider="adzuna",
        title="Data Engineer",
        company="DataFlow Inc",
        location="New York, NY",
        is_remote=False,
        description="Build scalable data pipelines and SQL databases.",
        salary_min=110000.0,
        salary_max=140000.0,
        salary_currency="USD",
        redirect_url="https://www.adzuna.com/land/ad/102",
    ),
]


@pytest.mark.asyncio
async def test_search_jobs_with_mocked_provider(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/jobs searches external provider and caches normalized listings."""
    with patch.object(AdzunaJobProvider, "search_jobs", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = SAMPLE_NORMALIZED_JOBS

        response = await client.get("/api/v1/jobs?q=Python", headers=auth_headers)
        assert response.status_code == 200

        payload = response.json()
        assert payload["status"] == "success"
        data = payload["data"]
        assert len(data) == 2
        assert data[0]["title"] == "Senior Python / FastAPI Developer"
        assert data[0]["company"] == "TechCorp Innovations"
        assert data[0]["is_remote"] is True
        assert data[0]["provider"] == "adzuna"


@pytest.mark.asyncio
async def test_save_and_unsave_job(client: AsyncClient, auth_headers: dict[str, str]):
    """Users can bookmark/save jobs and retrieve their saved jobs list."""
    with patch.object(AdzunaJobProvider, "search_jobs", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = SAMPLE_NORMALIZED_JOBS
        search_res = await client.get("/api/v1/jobs?q=Python", headers=auth_headers)
        job_id = search_res.json()["data"][0]["id"]

    # Bookmark job
    save_res = await client.post(f"/api/v1/jobs/{job_id}/save", headers=auth_headers)
    assert save_res.status_code == 200
    assert save_res.json()["data"]["is_saved"] is True

    # Retrieve saved jobs list
    saved_list_res = await client.get("/api/v1/jobs/saved", headers=auth_headers)
    assert saved_list_res.status_code == 200
    saved_data = saved_list_res.json()["data"]
    assert len(saved_data) == 1
    assert saved_data[0]["id"] == job_id

    # Unbookmark job
    unsave_res = await client.delete(f"/api/v1/jobs/{job_id}/save", headers=auth_headers)
    assert unsave_res.status_code == 200
    assert unsave_res.json()["data"]["is_saved"] is False


@pytest.mark.asyncio
async def test_job_provider_failure_returns_503(client: AsyncClient, auth_headers: dict[str, str]):
    """When external provider is unconfigured or fails, returns 503 with standard exact error message."""
    with patch.object(AdzunaJobProvider, "search_jobs", new_callable=AsyncMock) as mock_search:
        mock_search.side_effect = ConnectionError("Job provider unreachable")

        response = await client.get("/api/v1/jobs?q=Developer", headers=auth_headers)
        assert response.status_code == 503

        payload = response.json()
        assert payload["status"] == "error"
        assert payload["message"] == "Job search is temporarily unavailable. Please try again later."


@pytest.mark.asyncio
async def test_user_isolation_saved_jobs(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict[str, str]
):
    """User B cannot see User A's saved job bookmarks."""
    # User A saves a job
    with patch.object(AdzunaJobProvider, "search_jobs", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = SAMPLE_NORMALIZED_JOBS
        search_res = await client.get("/api/v1/jobs?q=Python", headers=auth_headers)
        job_id = search_res.json()["data"][0]["id"]
        await client.post(f"/api/v1/jobs/{job_id}/save", headers=auth_headers)

    # Create User B
    user_b = User(
        email="user_b_jobs@example.com",
        name="User B Jobs",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({"sub": str(user_b.id), "email": user_b.email})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B checks saved jobs -> empty
    response = await client.get("/api/v1/jobs/saved", headers=headers_b)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 0
