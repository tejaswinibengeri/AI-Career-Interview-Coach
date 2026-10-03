"""
Unit and integration tests for Job Market Analyzer module.
Tests real-data guarantees, analytics computation, and honest fallback states.
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.integrations.jobs.adzuna import AdzunaJobProvider
from app.integrations.jobs.base import NormalizedJobData

SAMPLE_LIVE_JOBS = [
    NormalizedJobData(
        external_id="adz-101",
        provider="adzuna",
        title="Senior Python & FastAPI Engineer",
        company="TechScale Inc",
        location="New York, NY",
        is_remote=True,
        description="Looking for a Python developer with FastAPI, PostgreSQL, and Docker experience.",
        salary_min=130000.0,
        salary_max=160000.0,
        salary_currency="USD",
        redirect_url="https://api.adzuna.com/job/101",
    ),
    NormalizedJobData(
        external_id="adz-102",
        provider="adzuna",
        title="Full Stack React Developer",
        company="DesignWorks",
        location="San Francisco, CA",
        is_remote=False,
        description="React, TypeScript, Node.js, and AWS cloud engineer for hybrid position.",
        salary_min=120000.0,
        salary_max=150000.0,
        salary_currency="USD",
        redirect_url="https://api.adzuna.com/job/102",
    ),
]


@pytest.mark.asyncio
async def test_job_market_search_live_data(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/job-market/search computes analytics and returns normalized real jobs."""
    with patch.object(AdzunaJobProvider, "search_jobs", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = SAMPLE_LIVE_JOBS

        # Temporarily mock provider credentials check
        with patch("app.core.config.settings.JOB_PROVIDER_API_ID", "test_app_id"), \
             patch("app.core.config.settings.JOB_PROVIDER_API_KEY", "test_app_key"), \
             patch("app.core.config.settings.ADZUNA_APP_ID", "test_app_id"), \
             patch("app.core.config.settings.ADZUNA_APP_KEY", "test_app_key"):

            res = await client.get("/api/v1/job-market/search?query=Python", headers=auth_headers)
            assert res.status_code == 200
            data = res.json()["data"]
            assert data["live_data_available"] is True
            assert len(data["jobs"]) == 2

            analytics = data["analytics"]
            assert analytics["total_matching_jobs"] == 2
            # Verify skills extracted
            skill_names = [s["name"] for s in analytics["top_skills"]]
            assert "Python" in skill_names or "React" in skill_names


@pytest.mark.asyncio
async def test_job_market_search_unconfigured_fallback(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/job-market/search returns honest unconfigured state without fake jobs."""
    with patch("app.core.config.settings.JOB_PROVIDER_API_ID", ""), \
         patch("app.core.config.settings.JOB_PROVIDER_API_KEY", ""), \
         patch("app.core.config.settings.ADZUNA_APP_ID", ""), \
         patch("app.core.config.settings.ADZUNA_APP_KEY", ""):

        res = await client.get("/api/v1/job-market/search", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["live_data_available"] is False
        assert data["provider_configured"] is False
        assert "Live job data is currently unavailable" in data["status_message"]
        assert len(data["jobs"]) == 0
