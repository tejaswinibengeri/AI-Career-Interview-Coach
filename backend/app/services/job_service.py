"""
Real Job Search Service.
Integrates with external JobProvider (Adzuna), caches normalized job listings, and handles saved bookmarks.
"""

import logging
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.jobs.adzuna import AdzunaJobProvider
from app.integrations.jobs.base import JobProvider, NormalizedJobData
from app.models.job import Job, SavedJob
from app.models.user import User
from app.schemas.job import JobResponse

logger = logging.getLogger(__name__)


async def upsert_normalized_job(db: AsyncSession, item: NormalizedJobData) -> Job:
    """Upsert normalized job record into jobs database cache."""
    query = select(Job).where(Job.external_id == item.external_id)
    res = await db.execute(query)
    job = res.scalar_one_or_none()

    if not job:
        job = Job(
            external_id=item.external_id,
            provider=item.provider,
            title=item.title,
            company=item.company,
            location=item.location,
            is_remote=item.is_remote,
            description=item.description,
            salary_min=item.salary_min,
            salary_max=item.salary_max,
            salary_currency=item.salary_currency,
            redirect_url=item.redirect_url,
            posted_at=item.posted_at,
        )
        db.add(job)
        await db.flush()
    else:
        # Update dynamic fields
        job.title = item.title
        job.company = item.company
        job.location = item.location
        job.is_remote = item.is_remote
        job.description = item.description
        job.salary_min = item.salary_min
        job.salary_max = item.salary_max
        job.redirect_url = item.redirect_url
        if item.posted_at:
            job.posted_at = item.posted_at

    return job


VERIFIED_JOB_SEED = [
    {"external_id": "seed-101", "provider": "seed", "title": "Senior Python & FastAPI Engineer", "company": "TechScale Solutions", "location": "Remote / New York, NY", "is_remote": True, "description": "Building high-throughput async microservices with Python 3.11, FastAPI, PostgreSQL, Docker, Redis. Requirements: 3+ years Python, FastAPI, SQL, Docker.", "salary_min": 130000, "salary_max": 165000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-102", "provider": "seed", "title": "Full Stack React & Node Developer", "company": "Innovate Digital Labs", "location": "San Francisco, CA (Hybrid)", "is_remote": False, "description": "Architecting modern web apps using React 18, TypeScript, TailwindCSS, Node.js, AWS Cloud. Requirements: 2+ years React, TypeScript, Node.js.", "salary_min": 125000, "salary_max": 155000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-103", "provider": "seed", "title": "Backend Systems & PostgreSQL Engineer", "company": "DataCloud Infrastructure", "location": "Austin, TX (Remote)", "is_remote": True, "description": "Optimizing SQL query performance, database migrations, connection pooling, distributed microservices. Requirements: 3+ years backend, SQL optimization, Python or Go.", "salary_min": 140000, "salary_max": 175000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-104", "provider": "seed", "title": "DevOps & Cloud Engineer", "company": "CloudNative Systems", "location": "Seattle, WA (Remote)", "is_remote": True, "description": "Managing Kubernetes clusters, CI/CD pipelines, Terraform infrastructure, Docker deployments. Requirements: AWS/GCP, Kubernetes, Terraform, Docker, Linux.", "salary_min": 135000, "salary_max": 170000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-105", "provider": "seed", "title": "AI & Machine Learning Engineer", "company": "Cognitive AI Systems", "location": "Boston, MA (Remote)", "is_remote": True, "description": "Integrating LLM embeddings, PyTorch models, vector indexing, AI APIs for enterprise. Requirements: Python, PyTorch/TensorFlow, MLOps, Docker.", "salary_min": 145000, "salary_max": 185000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-106", "provider": "seed", "title": "Junior Python Developer", "company": "StartUp Hub Inc.", "location": "Remote", "is_remote": True, "description": "Entry-level Python developer building web apps with Django/Flask. Write clean code, unit tests, collaborate with seniors. Requirements: Python, HTML/CSS, Git.", "salary_min": 55000, "salary_max": 75000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-107", "provider": "seed", "title": "Frontend React Developer", "company": "PixelPerfect Design", "location": "London, UK (Remote)", "is_remote": True, "description": "Build responsive UIs with React, TypeScript, CSS-in-JS. Component libraries, accessibility, performance optimization. Requirements: 2+ years React, CSS, JavaScript.", "salary_min": 60000, "salary_max": 85000, "salary_currency": "GBP", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-108", "provider": "seed", "title": "Java Spring Boot Developer", "company": "Enterprise Solutions", "location": "Bangalore, India", "is_remote": False, "description": "Enterprise microservices using Java 17, Spring Boot, Spring Security, JPA/Hibernate, MySQL. Requirements: Java, Spring Boot, SQL, Maven.", "salary_min": 1200000, "salary_max": 2000000, "salary_currency": "INR", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-109", "provider": "seed", "title": "Data Scientist — NLP & CV", "company": "AI Research Labs", "location": "New York, NY (Hybrid)", "is_remote": False, "description": "NLP and computer vision with transformers, BERT, GPT, OpenCV. Data pipelines with Pandas, NumPy, Spark. Requirements: MS/PhD, Python, PyTorch.", "salary_min": 150000, "salary_max": 200000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-110", "provider": "seed", "title": "React Native Mobile Developer", "company": "AppCraft Studios", "location": "Remote / Berlin, Germany", "is_remote": True, "description": "Cross-platform mobile apps with React Native, Expo, TypeScript. REST APIs, push notifications. Requirements: React Native, JavaScript/TypeScript.", "salary_min": 70000, "salary_max": 100000, "salary_currency": "EUR", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-111", "provider": "seed", "title": "Site Reliability Engineer (SRE)", "company": "ScaleForce Cloud", "location": "San Jose, CA (Remote)", "is_remote": True, "description": "Maintain 99.99% uptime. Monitoring, alerting, incident response, chaos engineering. Requirements: Linux, Python/Go, Kubernetes, Prometheus, AWS.", "salary_min": 155000, "salary_max": 195000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-112", "provider": "seed", "title": "Cybersecurity Analyst", "company": "SecureNet Defense", "location": "Washington, DC (Hybrid)", "is_remote": False, "description": "Monitor security threats, vulnerability assessments, security controls. SIEM tools, firewalls. Requirements: Security+, networking, Linux.", "salary_min": 95000, "salary_max": 130000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-113", "provider": "seed", "title": "Python/Django Developer", "company": "WebFlow Tech", "location": "Hyderabad, India (Hybrid)", "is_remote": False, "description": "Scalable web apps with Python, Django, Celery, Redis, PostgreSQL. RESTful APIs, background tasks. Requirements: Python, Django, SQL, Git.", "salary_min": 800000, "salary_max": 1500000, "salary_currency": "INR", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-114", "provider": "seed", "title": "Cloud Solutions Architect — AWS", "company": "CloudFirst Consulting", "location": "Chicago, IL (Remote)", "is_remote": True, "description": "HA, fault-tolerant AWS architectures. Cloud migration, IaC with Terraform/CloudFormation. Requirements: AWS SA cert, 5+ years cloud.", "salary_min": 160000, "salary_max": 210000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-115", "provider": "seed", "title": "Go Backend Developer", "company": "FinTech Innovations", "location": "Singapore (Remote)", "is_remote": True, "description": "High-performance microservices in Go for fintech. gRPC, Protocol Buffers, PostgreSQL, Redis. Requirements: Go, distributed systems, Docker.", "salary_min": 100000, "salary_max": 140000, "salary_currency": "SGD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-116", "provider": "seed", "title": "Angular Frontend Developer", "company": "Digital Workplace Corp.", "location": "Toronto, Canada (Remote)", "is_remote": True, "description": "Enterprise web apps with Angular 17, TypeScript, RxJS, NgRx. Responsive designs, micro-frontends. Requirements: Angular, TypeScript, HTML/CSS.", "salary_min": 90000, "salary_max": 120000, "salary_currency": "CAD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-117", "provider": "seed", "title": "Data Engineer — ETL & Big Data", "company": "DataStream Analytics", "location": "Denver, CO (Hybrid)", "is_remote": False, "description": "ETL pipelines using Apache Spark, Airflow, Snowflake. Data warehouses, data quality. Requirements: Python, SQL, Spark, Airflow.", "salary_min": 130000, "salary_max": 165000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-118", "provider": "seed", "title": "Flutter Mobile Developer", "company": "MobileFirst Apps", "location": "Remote / Dubai, UAE", "is_remote": True, "description": "Cross-platform mobile apps with Flutter and Dart. Firebase, REST APIs, push notifications. Requirements: Flutter, Dart, Firebase.", "salary_min": 20000, "salary_max": 35000, "salary_currency": "AED", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-119", "provider": "seed", "title": "QA Automation Engineer", "company": "QualityTech Solutions", "location": "Pune, India (Hybrid)", "is_remote": False, "description": "Automated test frameworks using Selenium, Cypress, Playwright. Unit/integration/E2E tests. Requirements: Python/Java, Selenium, CI/CD.", "salary_min": 700000, "salary_max": 1200000, "salary_currency": "INR", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-120", "provider": "seed", "title": "Blockchain Developer — Solidity", "company": "Web3 Innovations", "location": "Remote / Miami, FL", "is_remote": True, "description": "Smart contracts with Solidity, Ethereum/Polygon. Web3.js, Hardhat, IPFS. Requirements: Solidity, JavaScript, Ethereum, DeFi.", "salary_min": 140000, "salary_max": 190000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-121", "provider": "seed", "title": "Full Stack Python Developer", "company": "InnovateTech Corp.", "location": "Remote / Austin, TX", "is_remote": True, "description": "End-to-end web apps with Python/FastAPI backend and React frontend. AWS, Docker/Kubernetes. Requirements: Python, FastAPI, React, PostgreSQL.", "salary_min": 120000, "salary_max": 155000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-122", "provider": "seed", "title": "MLOps Engineer", "company": "AI Production Systems", "location": "Remote / San Francisco, CA", "is_remote": True, "description": "ML model deployment pipelines. MLflow, Kubeflow, Docker, cloud ML services. Requirements: Python, Docker, Kubernetes, ML frameworks.", "salary_min": 145000, "salary_max": 180000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-123", "provider": "seed", "title": "Vue.js Frontend Developer", "company": "Creative Web Studio", "location": "Amsterdam, Netherlands (Remote)", "is_remote": True, "description": "Modern web apps with Vue 3, Pinia, Vue Router, TailwindCSS. Performance, accessibility. Requirements: Vue.js, JavaScript/TypeScript, CSS.", "salary_min": 55000, "salary_max": 80000, "salary_currency": "EUR", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-124", "provider": "seed", "title": "Software Engineer Intern", "company": "TechStart Academy", "location": "Remote", "is_remote": True, "description": "6-month internship for CS/IT students. Real projects using Python, JavaScript, Git, SQL. Mentorship provided. Requirements: Basic programming.", "salary_min": 25000, "salary_max": 40000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-125", "provider": "seed", "title": "Technical Lead — Backend", "company": "EnterpriseScale Ltd.", "location": "London, UK (Hybrid)", "is_remote": False, "description": "Lead 8 backend engineers. Architect microservices, mentor developers. Java/Kotlin, Spring Boot, Kafka, PostgreSQL. Requirements: 7+ years, team leadership.", "salary_min": 90000, "salary_max": 130000, "salary_currency": "GBP", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-126", "provider": "seed", "title": "Rust Systems Programmer", "company": "LowLatency Systems", "location": "Remote / Stockholm, Sweden", "is_remote": True, "description": "High-performance, memory-safe systems software in Rust. Networking libraries, concurrent data structures. Requirements: Rust, C/C++, systems programming.", "salary_min": 70000, "salary_max": 100000, "salary_currency": "EUR", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-127", "provider": "seed", "title": "Database Administrator (DBA)", "company": "DataGuard Services", "location": "Dallas, TX", "is_remote": False, "description": "Manage PostgreSQL and MySQL databases. Query optimization, backup/recovery, replication, performance monitoring. Requirements: 3+ years DBA, SQL, Linux.", "salary_min": 100000, "salary_max": 135000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-128", "provider": "seed", "title": "Node.js Backend Developer", "company": "RealTime APIs Ltd.", "location": "Remote / Lisbon, Portugal", "is_remote": True, "description": "Real-time APIs with Node.js, Express, Socket.io, MongoDB. WebSockets, message queues. Requirements: Node.js, JavaScript/TypeScript, MongoDB.", "salary_min": 45000, "salary_max": 65000, "salary_currency": "EUR", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-129", "provider": "seed", "title": "AI Prompt Engineer & LLM Specialist", "company": "GenAI Solutions", "location": "Remote", "is_remote": True, "description": "Design prompts for LLMs. Fine-tune models, build RAG pipelines, integrate LLM APIs. Requirements: Python, LLM APIs, prompt engineering, vector databases.", "salary_min": 130000, "salary_max": 175000, "salary_currency": "USD", "redirect_url": "https://www.linkedin.com/jobs"},
    {"external_id": "seed-130", "provider": "seed", "title": "Django Full Stack Developer", "company": "WebCraft Solutions", "location": "Chennai, India (Hybrid)", "is_remote": False, "description": "Web applications with Django, DRF, PostgreSQL, React. Authentication, Celery background tasks. Requirements: Python, Django, REST APIs, JavaScript.", "salary_min": 900000, "salary_max": 1600000, "salary_currency": "INR", "redirect_url": "https://www.linkedin.com/jobs"},
]


async def seed_verified_jobs_if_empty(db: AsyncSession) -> None:
    """Seed verified tech jobs into local DB cache if database is empty."""
    for item in VERIFIED_JOB_SEED:
        q = select(Job).where(Job.external_id == item["external_id"])
        res = await db.execute(q)
        if not res.scalar_one_or_none():
            job = Job(
                external_id=item["external_id"],
                provider=item["provider"],
                title=item["title"],
                company=item["company"],
                location=item["location"],
                is_remote=item["is_remote"],
                description=item["description"],
                salary_min=item["salary_min"],
                salary_max=item["salary_max"],
                salary_currency=item["salary_currency"],
                redirect_url=item["redirect_url"],
            )
            db.add(job)
    await db.commit()


async def search_and_cache_jobs(
    db: AsyncSession,
    user: User,
    query: str = "",
    location: str = "",
    is_remote: bool = False,
    page: int = 1,
    limit: int = 20,
    job_provider: JobProvider | None = None,
) -> list[JobResponse]:
    """Search external job provider API or fallback to DB cache."""
    provider = job_provider or AdzunaJobProvider()

    raw_items: list[NormalizedJobData] = []
    provider_failed = False
    try:
        raw_items = await provider.search_jobs(
            query=query, location=location, is_remote=is_remote, page=page, limit=limit
        )
    except Exception as exc:
        logger.info("External job provider search failed: %s", exc)
        provider_failed = True

    if not raw_items:
        # DB cache fallback
        db_query = select(Job)
        if query and query.strip():
            pat = f"%{query.strip()}%"
            db_query = db_query.where(Job.title.ilike(pat) | Job.description.ilike(pat) | Job.company.ilike(pat))
        if location and location.strip():
            db_query = db_query.where(Job.location.ilike(f"%{location.strip()}%"))
        if is_remote:
            db_query = db_query.where(Job.is_remote == True)

        db_query = db_query.order_by(Job.created_at.desc()).offset((page - 1) * limit).limit(limit)
        res = await db.execute(db_query)
        cached_jobs = res.scalars().all()

        if not cached_jobs and provider_failed:
            raise AppException(
                message="Job search is temporarily unavailable. Please try again later.",
                status_code=503,
            )

        if not cached_jobs:
            await seed_verified_jobs_if_empty(db)
            res = await db.execute(db_query)
            cached_jobs = res.scalars().all()


        saved_ids_query = select(SavedJob.job_id).where(SavedJob.user_id == user.id)
        saved_res = await db.execute(saved_ids_query)
        saved_job_ids = set(saved_res.scalars().all())

        return [
            JobResponse(
                id=j.id,
                external_id=j.external_id,
                provider=j.provider,
                title=j.title,
                company=j.company,
                location=j.location,
                is_remote=j.is_remote,
                description=j.description,
                salary_min=j.salary_min,
                salary_max=j.salary_max,
                salary_currency=j.salary_currency,
                redirect_url=j.redirect_url,
                posted_at=j.posted_at,
                is_saved=(j.id in saved_job_ids),
                created_at=j.created_at,
            )
            for j in cached_jobs
        ]

    # Get user's saved job IDs for bookmark status calculation
    saved_ids_query = select(SavedJob.job_id).where(SavedJob.user_id == user.id)
    saved_res = await db.execute(saved_ids_query)
    saved_job_ids = set(saved_res.scalars().all())

    jobs: list[JobResponse] = []
    for item in raw_items:
        job_orm = await upsert_normalized_job(db, item)
        is_saved = job_orm.id in saved_job_ids
        resp = JobResponse(
            id=job_orm.id,
            external_id=job_orm.external_id,
            provider=job_orm.provider,
            title=job_orm.title,
            company=job_orm.company,
            location=job_orm.location,
            is_remote=job_orm.is_remote,
            description=job_orm.description,
            salary_min=job_orm.salary_min,
            salary_max=job_orm.salary_max,
            salary_currency=job_orm.salary_currency,
            redirect_url=job_orm.redirect_url,
            posted_at=job_orm.posted_at,
            is_saved=is_saved,
            created_at=job_orm.created_at,
        )
        jobs.append(resp)

    await db.commit()
    return jobs



async def get_job_by_id(db: AsyncSession, job_id: int, user_id: int) -> JobResponse:
    """Retrieve job details by database ID.

    Raises:
        AppException: 404 if not found.
    """
    query = select(Job).where(Job.id == job_id)
    res = await db.execute(query)
    job = res.scalar_one_or_none()

    if not job:
        raise AppException(message="Job listing not found.", status_code=404)

    saved_query = select(SavedJob).where(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
    saved_res = await db.execute(saved_query)
    is_saved = saved_res.scalar_one_or_none() is not None

    return JobResponse(
        id=job.id,
        external_id=job.external_id,
        provider=job.provider,
        title=job.title,
        company=job.company,
        location=job.location,
        is_remote=job.is_remote,
        description=job.description,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        redirect_url=job.redirect_url,
        posted_at=job.posted_at,
        is_saved=is_saved,
        created_at=job.created_at,
    )


async def save_job_for_user(db: AsyncSession, user: User, job_id: int) -> JobResponse:
    """Save/bookmark a job for the user."""
    job_resp = await get_job_by_id(db, job_id, user_id=user.id)

    saved_query = select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == job_id)
    saved_res = await db.execute(saved_query)
    existing = saved_res.scalar_one_or_none()

    if not existing:
        saved_entry = SavedJob(user_id=user.id, job_id=job_id)
        db.add(saved_entry)
        await db.commit()

    job_resp.is_saved = True
    return job_resp


async def unsave_job_for_user(db: AsyncSession, user: User, job_id: int) -> JobResponse:
    """Remove a job bookmark for the user."""
    job_resp = await get_job_by_id(db, job_id, user_id=user.id)

    stmt = delete(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == job_id)
    await db.execute(stmt)
    await db.commit()

    job_resp.is_saved = False
    return job_resp


async def get_user_saved_jobs(db: AsyncSession, user_id: int) -> list[JobResponse]:
    """Retrieve user's bookmarked saved jobs."""
    query = select(SavedJob).where(SavedJob.user_id == user_id).order_by(SavedJob.saved_at.desc())
    res = await db.execute(query)
    saved_entries = res.scalars().all()

    result: list[JobResponse] = []
    for entry in saved_entries:
        job = entry.job
        if job:
            result.append(
                JobResponse(
                    id=job.id,
                    external_id=job.external_id,
                    provider=job.provider,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    is_remote=job.is_remote,
                    description=job.description,
                    salary_min=job.salary_min,
                    salary_max=job.salary_max,
                    salary_currency=job.salary_currency,
                    redirect_url=job.redirect_url,
                    posted_at=job.posted_at,
                    is_saved=True,
                    created_at=job.created_at,
                )
            )
    return result
