"""
Unit and integration tests for Career Intelligence module:
- Job Description Analyzer
- Resume -> JD Match
- AI Cover Letter Generator
"""

import json
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.ai.ollama import OllamaProvider
from app.models.resume import Resume, ResumeVersion
from app.models.user import User


SAMPLE_JD_TEXT = """
We are looking for a Senior Backend Engineer to join our cloud platform team.
Required Skills: Python, FastAPI, PostgreSQL, Docker, AsyncIO.
Preferred Skills: Redis, Kubernetes, GraphQL.
Technologies: AWS, Git, Linux.
Experience: 4+ years of professional backend software development.
Responsibilities: Design distributed APIs, optimize SQL queries, lead architecture discussions.
Education: Bachelor's degree in Computer Science or equivalent practical experience.
Certifications: AWS Solutions Architect preferred.
Soft Skills: Strong communication, technical leadership, agile collaboration.
Keywords: Microservices, Scalability, High Availability, REST APIs.
"""

SAMPLE_JD_ANALYSIS_AI_OUTPUT = json.dumps({
    "job_title": "Senior Backend Engineer",
    "company": "Cloud Platform Corp",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AsyncIO"],
    "preferred_skills": ["Redis", "Kubernetes", "GraphQL"],
    "technologies": ["AWS", "Git", "Linux"],
    "experience": ["4+ years of professional backend software development"],
    "responsibilities": ["Design distributed APIs", "Optimize SQL queries", "Lead architecture discussions"],
    "education": ["Bachelor's degree in Computer Science"],
    "certifications": ["AWS Solutions Architect preferred"],
    "soft_skills": ["Strong communication", "Technical leadership"],
    "keywords": ["Microservices", "Scalability", "High Availability", "REST APIs"]
})

SAMPLE_MATCH_AI_OUTPUT = json.dumps({
    "overall_score": 88.0,
    "skills_score": 85.0,
    "keyword_score": 90.0,
    "experience_score": 85.0,
    "responsibility_score": 92.0,
    "matched_skills": ["Python", "FastAPI", "PostgreSQL", "AsyncIO"],
    "missing_skills": ["Docker", "Kubernetes"],
    "partial_matches": ["AWS Cloud (Candidate has generic cloud experience)"],
    "relevant_experience": ["Built high-throughput async APIs using FastAPI"],
    "potential_gaps": ["No explicit container orchestration mentioned"],
    "improvement_suggestions": ["Highlight Docker and Kubernetes container workflows"]
})

SAMPLE_COVER_LETTER_OUTPUT = """Dear Hiring Manager,

I am writing to express my enthusiasm for the Senior Backend Engineer position at Cloud Platform Corp. With my background in Python, FastAPI, and PostgreSQL microservices, I am confident in my ability to contribute to your team.

Throughout my career, I have focused on designing scalable APIs and optimizing asynchronous database workloads. I look forward to discussing how my experience aligns with your team's objectives.

Sincerely,
Candidate
"""


@pytest.mark.asyncio
async def test_analyze_job_description(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/career-intelligence/analyze-jd extracts structured requirements via Ollama."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_JD_ANALYSIS_AI_OUTPUT

        response = await client.post(
            "/api/v1/career-intelligence/analyze-jd",
            json={"job_description": SAMPLE_JD_TEXT},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["job_title"] == "Senior Backend Engineer"
        assert "Python" in data["required_skills"]
        assert "Docker" in data["required_skills"]
        assert "AWS" in data["technologies"]


@pytest.mark.asyncio
async def test_match_resume_to_jd_flow(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    sample_user: User,
):
    """POST /api/v1/career-intelligence/match performs AI comparison, evaluates gaps, and saves history."""
    # Seed a resume with extracted text
    resume = Resume(user_id=sample_user.id, title="Senior Python Resume")
    db_session.add(resume)
    await db_session.flush()

    version = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        filename="resume.pdf",
        file_path="/fake/resume.pdf",
        file_size=1024,
        file_type="pdf",
        mime_type="application/pdf",
        extracted_text="Senior Software Engineer with 5 years experience in Python, FastAPI, PostgreSQL, and AsyncIO.",
        is_current=True,
    )
    db_session.add(version)
    await db_session.commit()

    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_MATCH_AI_OUTPUT

        payload = {
            "resume_id": resume.id,
            "job_description": SAMPLE_JD_TEXT,
            "job_title": "Senior Backend Engineer",
            "company_name": "Cloud Platform Corp",
        }
        res = await client.post(
            "/api/v1/career-intelligence/match",
            json=payload,
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["overall_score"] == 88.0
        assert "Python" in data["matched_skills"]
        assert "Docker" in data["missing_skills"]

        # Check history endpoint
        hist_res = await client.get("/api/v1/career-intelligence/matches", headers=auth_headers)
        assert hist_res.status_code == 200
        history_items = hist_res.json()["data"]
        assert len(history_items) >= 1
        assert history_items[0]["id"] == data["id"]


@pytest.mark.asyncio
async def test_generate_cover_letter_flow(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    sample_user: User,
):
    """POST /api/v1/career-intelligence/cover-letter generates and stores personalized letter."""
    resume = Resume(user_id=sample_user.id, title="Backend Developer Resume")
    db_session.add(resume)
    await db_session.flush()

    version = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        filename="resume.pdf",
        file_path="/fake/resume.pdf",
        file_size=1024,
        file_type="pdf",
        mime_type="application/pdf",
        extracted_text="Python engineer with 4 years building scalable services with FastAPI and PostgreSQL.",
        is_current=True,
    )
    db_session.add(version)
    await db_session.commit()

    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_COVER_LETTER_OUTPUT

        payload = {
            "resume_id": resume.id,
            "job_description": SAMPLE_JD_TEXT,
            "job_title": "Senior Backend Engineer",
            "company_name": "Cloud Platform Corp",
            "tone": "Professional",
            "length": "Standard",
        }
        res = await client.post(
            "/api/v1/career-intelligence/cover-letter",
            json=payload,
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "Dear Hiring Manager" in data["content"]
        assert data["label"] == "AI-generated cover letter"

        # Check history endpoint
        list_res = await client.get("/api/v1/career-intelligence/cover-letters", headers=auth_headers)
        assert list_res.status_code == 200
        letters = list_res.json()["data"]
        assert len(letters) >= 1


SAMPLE_COLD_EMAIL_OUTPUT = json.dumps({
    "subject": "Application — Senior Backend Engineer | Python & FastAPI",
    "body": "Dear Sarah Connors,\n\nI noticed Cloud Platform Corp is expanding its cloud infrastructure team and seeking a Senior Backend Engineer. With verified experience designing FastAPI microservices handling high concurrency, I would love to connect regarding this role.\n\nBest regards,\nCandidate",
})

SAMPLE_REGEN_SUBJECT_OUTPUT = json.dumps({
    "subject": "Senior Backend Engineer — Python & Cloud Architecture",
})


@pytest.mark.asyncio
async def test_generate_cold_email_flow(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    sample_user: User,
):
    """POST /api/v1/career-intelligence/cold-email/generate generates, stores, and allows editing of cold outreach email."""
    resume = Resume(user_id=sample_user.id, title="Lead Engineer Resume")
    db_session.add(resume)
    await db_session.flush()

    version = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        filename="resume.pdf",
        file_path="/fake/resume.pdf",
        file_size=1024,
        file_type="pdf",
        mime_type="application/pdf",
        extracted_text="Lead backend developer with extensive Python, FastAPI, and Postgres database tuning experience.",
        is_current=True,
    )
    db_session.add(version)
    await db_session.commit()

    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_COLD_EMAIL_OUTPUT

        payload = {
            "resume_id": resume.id,
            "job_title": "Senior Backend Engineer",
            "company_name": "Cloud Platform Corp",
            "recruiter_name": "Sarah Connors",
            "recruiter_email": "sarah@cloudplatform.com",
            "job_description": SAMPLE_JD_TEXT,
            "portfolio_url": "https://example.com/portfolio",
            "email_type": "Recruiter Outreach",
            "tone": "Professional",
            "length": "Short",
        }
        res = await client.post(
            "/api/v1/career-intelligence/cold-email/generate",
            json=payload,
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        email_id = data["id"]
        assert "Application — Senior Backend Engineer" in data["subject"]
        assert "Sarah Connors" in data["body"]
        assert data["recruiter_email"] == "sarah@cloudplatform.com"

        # Check history endpoint
        hist_res = await client.get("/api/v1/career-intelligence/cold-email/history", headers=auth_headers)
        assert hist_res.status_code == 200
        history_list = hist_res.json()["data"]
        assert len(history_list) >= 1
        assert any(h["id"] == email_id for h in history_list)

        # Check get detail endpoint
        detail_res = await client.get(f"/api/v1/career-intelligence/cold-email/{email_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        assert detail_res.json()["data"]["company_name"] == "Cloud Platform Corp"

        # Check edit/update endpoint
        update_payload = {
            "subject": "Updated Subject: Senior Backend Opportunity",
            "body": "Updated body text with customized personal signoff.",
            "recruiter_name": "Sarah C.",
            "recruiter_email": "sarah.c@cloudplatform.com",
        }
        put_res = await client.put(
            f"/api/v1/career-intelligence/cold-email/{email_id}",
            json=update_payload,
            headers=auth_headers,
        )
        assert put_res.status_code == 200
        updated_data = put_res.json()["data"]
        assert updated_data["subject"] == "Updated Subject: Senior Backend Opportunity"
        assert updated_data["recruiter_name"] == "Sarah C."


@pytest.mark.asyncio
async def test_regenerate_cold_email_subject(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/career-intelligence/cold-email/regenerate-subject generates a fresh subject line."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_REGEN_SUBJECT_OUTPUT

        payload = {
            "job_title": "Senior Backend Engineer",
            "company_name": "Cloud Platform Corp",
            "candidate_name": "Alex",
            "key_skills": ["Python", "FastAPI"],
            "email_type": "Recruiter Outreach",
        }
        res = await client.post(
            "/api/v1/career-intelligence/cold-email/regenerate-subject",
            json=payload,
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "Senior Backend Engineer" in data["subject"]

