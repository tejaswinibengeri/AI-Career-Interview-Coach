"""
Job Market Analyzer Service.
Queries REAL external job provider APIs (e.g. Adzuna), enforces zero-fake-data policies,
computes dynamic market analytics from retrieved data, and optionally integrates candidate profile.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone
import logging
import re
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.jobs.adzuna import AdzunaJobProvider
from app.integrations.jobs.base import JobProvider, NormalizedJobData
from app.models.user import User
from app.schemas.job_market import (
    JobMarketAnalytics,
    JobMarketListing,
    JobMarketMetricItem,
    JobMarketSearchFilters,
    JobMarketSearchResponse,
)
from app.services.job_service import upsert_normalized_job
from app.services.profile_service import get_or_create_profile

logger = logging.getLogger(__name__)

# Standard tech and skill lexicon for identifying requested competencies in real JD texts
KNOWN_TECH_LEXICON = {
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "Django",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes",
    "AWS", "Azure", "GCP", "Git", "GraphQL", "REST", "Java", "C++", "C#", ".NET",
    "Go", "Rust", "PHP", "Ruby", "HTML", "CSS", "TailwindCSS", "Kafka", "Linux",
    "PyTorch", "TensorFlow", "Pandas", "Spark", "Airflow", "Snowflake", "Terraform",
    "CI/CD", "Next.js", "Vue.js", "Angular", "Microservices", "NLP", "LLM",
}


def _detect_workplace_type(title: str, desc: str, loc: str, is_remote: bool) -> str:
    """Classify listing into Remote, Hybrid, or On-site based strictly on real text."""
    combined = f"{title} {desc} {loc}".lower()
    if "hybrid" in combined:
        return "Hybrid"
    if is_remote or "remote" in combined or "work from home" in combined or "telecommute" in combined:
        return "Remote"
    return "On-site"


def _detect_experience_level(title: str, desc: str) -> str:
    """Detect seniority level from real title/description keywords."""
    combined = f"{title} {desc}".lower()
    if re.search(r"\b(lead|principal|staff|director|architect|head of)\b", combined):
        return "Lead / Principal"
    if re.search(r"\b(senior|sr\.?|5\+\s*years|7\+\s*years)\b", combined):
        return "Senior"
    if re.search(r"\b(junior|jr\.?|entry[\s-]level|associate|intern|internship|graduate)\b", combined):
        return "Entry / Junior"
    return "Mid-Level"


def _extract_skills_from_text(text: str) -> list[str]:
    """Find known technical skills present in real job description."""
    found = []
    text_lower = f" {text.lower()} "
    for tech in KNOWN_TECH_LEXICON:
        pattern = rf"\b{re.escape(tech.lower())}\b"
        if re.search(pattern, text_lower):
            found.append(tech)
    return sorted(found)


def _compute_analytics_from_real_jobs(jobs: list[JobMarketListing]) -> JobMarketAnalytics:
    """Derive aggregate statistics strictly from the retrieved set of real job listings."""
    total_jobs = len(jobs)
    insufficient_data: list[str] = []

    if total_jobs == 0:
        return JobMarketAnalytics(
            total_matching_jobs=0,
            insufficient_data_metrics=[
                "Top Skills",
                "Technologies",
                "Top Job Titles",
                "Location Distribution",
                "Workplace Distribution",
                "Experience Levels",
                "Company Distribution",
                "Posting Trends",
            ],
        )

    # 1. Top Skills & Technologies
    skill_counter: Counter[str] = Counter()
    for j in jobs:
        for s in j.extracted_skills:
            skill_counter[s] += 1

    top_skills_items = [
        JobMarketMetricItem(name=k, count=v, percentage=round(v / total_jobs * 100, 1))
        for k, v in skill_counter.most_common(12)
    ]
    if not top_skills_items:
        insufficient_data.append("Top Skills")

    # 2. Top Job Titles (grouped / cleaned)
    title_counter: Counter[str] = Counter()
    for j in jobs:
        cleaned_title = re.sub(r"\(.*?\)", "", j.title).strip()
        title_counter[cleaned_title] += 1

    top_title_items = [
        JobMarketMetricItem(name=k, count=v, percentage=round(v / total_jobs * 100, 1))
        for k, v in title_counter.most_common(8)
    ]

    # 3. Location Distribution
    loc_counter: Counter[str] = Counter()
    for j in jobs:
        loc = j.location.split(",")[0].strip() or "Various"
        loc_counter[loc] += 1

    loc_items = [
        JobMarketMetricItem(name=k, count=v, percentage=round(v / total_jobs * 100, 1))
        for k, v in loc_counter.most_common(6)
    ]

    # 4. Workplace Distribution (Remote vs Hybrid vs On-site)
    workplace_counter: Counter[str] = Counter(j.workplace_type for j in jobs)
    workplace_items = [
        JobMarketMetricItem(name=k, count=v, percentage=round(v / total_jobs * 100, 1))
        for k, v in workplace_counter.most_common()
    ]

    # 5. Experience Distribution
    exp_counter: Counter[str] = Counter(j.experience_level or "Mid-Level" for j in jobs)
    exp_items = [
        JobMarketMetricItem(name=k, count=v, percentage=round(v / total_jobs * 100, 1))
        for k, v in exp_counter.most_common()
    ]

    # 6. Company Distribution
    comp_counter: Counter[str] = Counter(j.company for j in jobs if j.company and j.company != "Company")
    comp_items = [
        JobMarketMetricItem(name=k, count=v, percentage=round(v / total_jobs * 100, 1))
        for k, v in comp_counter.most_common(6)
    ]
    if not comp_items:
        insufficient_data.append("Company Distribution")

    # 7. Posting Trends (if posted_at available)
    posted_dates = [j.posted_at for j in jobs if j.posted_at]
    trend_items: list[JobMarketMetricItem] = []
    if len(posted_dates) >= 3:
        date_counter: Counter[str] = Counter()
        for dt in posted_dates:
            date_counter[dt.strftime("%b %d")] += 1
        trend_items = [
            JobMarketMetricItem(name=k, count=v)
            for k, v in sorted(date_counter.items(), key=lambda x: x[0])[-7:]
        ]
    else:
        insufficient_data.append("Posting Trends")

    # 8. Salary Summary
    salaries = [
        (j.salary_min + j.salary_max) / 2
        for j in jobs
        if j.salary_min and j.salary_max and j.salary_max > 0
    ]
    salary_summary = None
    if len(salaries) >= 2:
        salary_summary = {
            "avg_salary": round(sum(salaries) / len(salaries)),
            "min_salary": min(salaries),
            "max_salary": max(salaries),
            "currency": "USD",
            "samples_count": len(salaries),
        }
    else:
        insufficient_data.append("Salary Benchmark")

    return JobMarketAnalytics(
        total_matching_jobs=total_jobs,
        top_skills=top_skills_items,
        top_technologies=top_skills_items,  # Lexicon encapsulates tech & tools
        top_job_titles=top_title_items,
        location_distribution=loc_items,
        workplace_distribution=workplace_items,
        experience_distribution=exp_items,
        company_distribution=comp_items,
        posting_trends=trend_items,
        salary_summary=salary_summary,
        insufficient_data_metrics=insufficient_data,
    )


async def search_job_market(
    db: AsyncSession,
    user: User,
    filters: JobMarketSearchFilters,
    job_provider: JobProvider | None = None,
) -> JobMarketSearchResponse:
    """Execute real job search against external provider, apply filters, and compute live analytics."""
    provider = job_provider or AdzunaJobProvider()

    # 1. Handle profile enhancement if requested
    query_str = filters.query.strip()
    loc_str = filters.location.strip()

    if filters.use_profile:
        profile = await get_or_create_profile(db, user.id)
        if not query_str:
            if profile.target_role:
                query_str = profile.target_role
            elif profile.current_role:
                query_str = profile.current_role
            elif profile.skills:
                query_str = " ".join(profile.skills[:2])
        if not loc_str and profile.preferred_location:
            loc_str = profile.preferred_location

    # 2. Check if provider credentials exist
    if isinstance(provider, AdzunaJobProvider) and (not provider.app_id or not provider.app_key):
        return JobMarketSearchResponse(
            live_data_available=False,
            provider_configured=False,
            provider_name="Adzuna External Job API",
            status_message="Live job data is currently unavailable. Please configure external job provider credentials (JOB_PROVIDER_API_KEY / ADZUNA_APP_ID in .env).",
            total_results=0,
            page=filters.page,
            limit=filters.limit,
            jobs=[],
            analytics=_compute_analytics_from_real_jobs([]),
        )

    # 3. Query External Provider
    try:
        raw_items: list[NormalizedJobData] = await provider.search_jobs(
            query=query_str,
            location=loc_str,
            is_remote=filters.is_remote or (filters.workplace_type == "Remote"),
            page=filters.page,
            limit=filters.limit,
        )
    except ConnectionError as exc:
        logger.warning("External job provider connection failure: %s", exc)
        return JobMarketSearchResponse(
            live_data_available=False,
            provider_configured=True,
            provider_name="Adzuna External Job API",
            status_message=f"Live job data is currently unavailable: {exc}",
            total_results=0,
            page=filters.page,
            limit=filters.limit,
            jobs=[],
            analytics=_compute_analytics_from_real_jobs([]),
        )
    except Exception as exc:
        logger.error("Unexpected error contacting external job provider: %s", exc)
        return JobMarketSearchResponse(
            live_data_available=False,
            provider_configured=True,
            provider_name="Adzuna External Job API",
            status_message="Live job data provider encountered an unexpected error. Please try again later.",
            total_results=0,
            page=filters.page,
            limit=filters.limit,
            jobs=[],
            analytics=_compute_analytics_from_real_jobs([]),
        )

    # 4. Normalize and cache real jobs in DB
    listings: list[JobMarketListing] = []
    for item in raw_items:
        # Cache to jobs table
        try:
            orm_job = await upsert_normalized_job(db, item)
            job_id = orm_job.id
        except Exception:
            job_id = None

        workplace_type = _detect_workplace_type(item.title, item.description, item.location, item.is_remote)
        exp_level = _detect_experience_level(item.title, item.description)
        skills = _extract_skills_from_text(f"{item.title} {item.description}")

        listing = JobMarketListing(
            id=job_id,
            external_id=item.external_id,
            provider=item.provider,
            title=item.title,
            company=item.company,
            location=item.location,
            is_remote=item.is_remote,
            workplace_type=workplace_type,
            description=item.description,
            salary_min=item.salary_min,
            salary_max=item.salary_max,
            salary_currency=item.salary_currency or "USD",
            redirect_url=item.redirect_url,
            posted_at=item.posted_at,
            extracted_skills=skills,
            experience_level=exp_level,
        )
        listings.append(listing)

    try:
        await db.commit()
    except Exception:
        pass

    # 5. Apply in-memory secondary filters if provided by user
    filtered_listings = listings

    # Filter: Workplace type
    if filters.workplace_type and filters.workplace_type != "All":
        filtered_listings = [
            j for j in filtered_listings
            if j.workplace_type.lower() == filters.workplace_type.lower()
        ]

    # Filter: Experience level
    if filters.experience_level and filters.experience_level != "All":
        filtered_listings = [
            j for j in filtered_listings
            if j.experience_level and filters.experience_level.lower() in j.experience_level.lower()
        ]

    # Filter: Company
    if filters.company and filters.company.strip():
        comp_query = filters.company.strip().lower()
        filtered_listings = [
            j for j in filtered_listings
            if comp_query in j.company.lower()
        ]

    # Filter: Skills
    if filters.skills and filters.skills.strip():
        req_skills = [s.strip().lower() for s in filters.skills.split(",") if s.strip()]
        filtered_listings = [
            j for j in filtered_listings
            if any(rs in [s.lower() for s in j.extracted_skills] or rs in j.description.lower() for rs in req_skills)
        ]

    # Filter: Date posted
    if filters.date_posted and filters.date_posted != "all":
        now = datetime.now(timezone.utc)
        cutoff: datetime | None = None
        if filters.date_posted == "24h":
            cutoff = now - timedelta(days=1)
        elif filters.date_posted == "7d":
            cutoff = now - timedelta(days=7)
        elif filters.date_posted == "30d":
            cutoff = now - timedelta(days=30)

        if cutoff:
            filtered_listings = [
                j for j in filtered_listings
                if j.posted_at and j.posted_at >= cutoff
            ]

    # 6. Compute Real Analytics from Retrieved Listings
    analytics = _compute_analytics_from_real_jobs(filtered_listings)

    return JobMarketSearchResponse(
        live_data_available=True,
        provider_configured=True,
        provider_name="Adzuna Real-Time Job API",
        status_message=f"Retrieved {len(filtered_listings)} live market positions.",
        total_results=len(filtered_listings),
        page=filters.page,
        limit=filters.limit,
        jobs=filtered_listings,
        analytics=analytics,
    )
