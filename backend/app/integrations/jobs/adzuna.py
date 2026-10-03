"""
Adzuna External Job API Provider Implementation.
Queries real external job listings via Adzuna API using ADZUNA_APP_ID and ADZUNA_APP_KEY.
Does NOT generate fake jobs.
"""

import html
import logging
from datetime import datetime
from typing import Any
import httpx

from app.core.config import settings
from app.integrations.jobs.base import JobProvider, NormalizedJobData

logger = logging.getLogger(__name__)


class AdzunaJobProvider(JobProvider):
    """Adzuna Job API implementation."""

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        country: str | None = None,
        base_url: str | None = None,
        timeout: float = 10.0,
    ):
        self.app_id = app_id or settings.JOB_PROVIDER_API_ID or settings.ADZUNA_APP_ID
        self.app_key = app_key or settings.JOB_PROVIDER_API_KEY or settings.ADZUNA_APP_KEY
        self.country = (country or settings.ADZUNA_COUNTRY or "us").lower()
        self.timeout = timeout
        self.base_url = (
            base_url
            or settings.JOB_PROVIDER_URL
            or f"https://api.adzuna.com/v1/api/jobs/{self.country}/search"
        ).rstrip("/")

    def _normalize_item(self, item: dict[str, Any]) -> NormalizedJobData:
        """Normalize an Adzuna API JSON result item into NormalizedJobData schema."""
        ext_id = str(item.get("id", ""))
        title = html.unescape(item.get("title", "Job Listing"))
        company_data = item.get("company", {})
        company = company_data.get("display_name", "Confidential Company") if isinstance(company_data, dict) else "Company"

        loc_data = item.get("location", {})
        location = loc_data.get("display_name", "Remote / USA") if isinstance(loc_data, dict) else "USA"

        desc = item.get("description", "")
        clean_desc = html.unescape(desc)

        is_remote = "remote" in title.lower() or "remote" in clean_desc.lower() or "remote" in location.lower()

        created_str = item.get("created")
        posted_at: datetime | None = None
        if created_str:
            try:
                posted_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except Exception:
                posted_at = None

        return NormalizedJobData(
            external_id=ext_id,
            provider="adzuna",
            title=title,
            company=company,
            location=location,
            is_remote=is_remote,
            description=clean_desc,
            salary_min=item.get("salary_min"),
            salary_max=item.get("salary_max"),
            salary_currency="USD",
            redirect_url=item.get("redirect_url", "#"),
            posted_at=posted_at,
        )

    async def search_jobs(
        self,
        query: str = "",
        location: str = "",
        is_remote: bool = False,
        page: int = 1,
        limit: int = 20,
    ) -> list[NormalizedJobData]:
        """Query real Adzuna API endpoints.

        Raises:
            ConnectionError: If API credentials missing or connection fails.
        """
        if not self.app_id or not self.app_key:
            logger.warning("Adzuna API credentials (ADZUNA_APP_ID / ADZUNA_APP_KEY) not configured.")
            raise ConnectionError(
                "Job search provider (Adzuna) is not configured with API credentials."
            )

        endpoint = f"{self.base_url}/{page}"
        params: dict[str, Any] = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": limit,
            "content-type": "application/json",
        }

        search_query = query.strip() if query else ""
        if is_remote and "remote" not in search_query.lower():
            search_query = f"{search_query} remote".strip()

        if search_query:
            params["what"] = search_query
        if location and location.strip():
            params["where"] = location.strip()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint, params=params)
                if response.status_code == 401 or response.status_code == 403:
                    raise ConnectionError("Adzuna API credentials invalid or rate limit exceeded.")
                response.raise_for_status()

                data = response.json()
                results = data.get("results", [])
                return [self._normalize_item(item) for item in results]

        except httpx.ConnectError as exc:
            logger.error("Adzuna API connection error: %s", exc)
            raise ConnectionError("Cannot connect to job provider API.") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("Adzuna API HTTP status error: %s", exc)
            raise ConnectionError(f"Job provider API returned status {exc.response.status_code}") from exc
        except Exception as exc:
            if isinstance(exc, ConnectionError):
                raise
            logger.error("Unexpected error querying Adzuna API: %s", exc)
            raise ConnectionError(f"Job provider error: {exc}") from exc

    async def get_job_details(self, external_id: str) -> NormalizedJobData | None:
        """Fetch single job detail."""
        results = await self.search_jobs(query=external_id, limit=5)
        for job in results:
            if job.external_id == external_id:
                return job
        return results[0] if results else None
