"""
Abstract Base Interface for External Job Search Providers.
Enforces normalized job schema and zero-fake-job policies.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field


class NormalizedJobData(BaseModel):
    """Normalized job entity from external legitimate provider APIs."""

    external_id: str
    provider: str = "adzuna"
    title: str
    company: str
    location: str
    is_remote: bool = False
    description: str
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = "USD"
    redirect_url: str
    posted_at: datetime | None = None


class JobProvider(ABC):
    """Abstract contract for searching external job provider APIs."""

    @abstractmethod
    async def search_jobs(
        self,
        query: str = "",
        location: str = "",
        is_remote: bool = False,
        page: int = 1,
        limit: int = 20,
    ) -> list[NormalizedJobData]:
        """Search external job provider for real job listings."""
        pass

    @abstractmethod
    async def get_job_details(self, external_id: str) -> NormalizedJobData | None:
        """Fetch single job detail from external provider."""
        pass
