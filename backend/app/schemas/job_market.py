"""
Pydantic schemas for Job Market Analyzer module.
Enforces real-data guarantees, structured analytics, and provider transparency.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class JobMarketSearchFilters(BaseModel):
    """Filter parameters for querying live market opportunities."""

    query: str = Field(default="", description="Target job title or skill keywords")
    location: str = Field(default="", description="Location or city filter")
    is_remote: bool = Field(default=False, description="Filter remote positions only")
    workplace_type: str | None = Field(default=None, description="All, Remote, Hybrid, On-site")
    experience_level: str | None = Field(default=None, description="All, Entry, Mid, Senior, Lead")
    skills: str | None = Field(default=None, description="Comma-separated skill keywords")
    company: str | None = Field(default=None, description="Company name filter")
    job_type: str | None = Field(default=None, description="Full-time, Part-time, Contract, Any")
    date_posted: str | None = Field(default="all", description="all, 24h, 7d, 30d")
    use_profile: bool = Field(default=False, description="Optionally bias or filter using user candidate profile")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class JobMarketMetricItem(BaseModel):
    """Generic category/count metric pair."""

    name: str
    count: int
    percentage: float | None = None


class JobMarketAnalytics(BaseModel):
    """Aggregated market intelligence derived strictly from real retrieved jobs."""

    total_matching_jobs: int
    top_skills: list[JobMarketMetricItem] = Field(default_factory=list)
    top_technologies: list[JobMarketMetricItem] = Field(default_factory=list)
    top_job_titles: list[JobMarketMetricItem] = Field(default_factory=list)
    location_distribution: list[JobMarketMetricItem] = Field(default_factory=list)
    workplace_distribution: list[JobMarketMetricItem] = Field(default_factory=list)
    experience_distribution: list[JobMarketMetricItem] = Field(default_factory=list)
    company_distribution: list[JobMarketMetricItem] = Field(default_factory=list)
    posting_trends: list[JobMarketMetricItem] = Field(default_factory=list)
    salary_summary: dict[str, Any] | None = None
    insufficient_data_metrics: list[str] = Field(default_factory=list)


class JobMarketListing(BaseModel):
    """Normalized real job opportunity from external API."""

    id: int | None = None
    external_id: str
    provider: str
    title: str
    company: str
    location: str
    is_remote: bool
    workplace_type: str
    description: str
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = "USD"
    redirect_url: str
    posted_at: datetime | None = None
    extracted_skills: list[str] = Field(default_factory=list)
    experience_level: str | None = None


class JobMarketSearchResponse(BaseModel):
    """Complete response payload for Job Market Analyzer."""

    live_data_available: bool
    provider_configured: bool
    provider_name: str
    status_message: str
    total_results: int
    page: int
    limit: int
    jobs: list[JobMarketListing] = Field(default_factory=list)
    analytics: JobMarketAnalytics | None = None
