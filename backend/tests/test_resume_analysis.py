"""
Comprehensive unit and integration tests for Module 04: AI Resume Analyzer and ATS.
"""

import json
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.integrations.ai.ollama import OllamaProvider
from app.models.resume import Resume, ResumeVersion
from app.models.user import User


SAMPLE_AI_JSON_OUTPUT = json.dumps({
    "structure_score": 85.0,
    "skills_score": 80.0,
    "experience_score": 75.0,
    "education_score": 90.0,
    "formatting_score": 85.0,
    "skills": [
        {"name": "Python", "category": "technical", "proficiency": "advanced"},
        {"name": "FastAPI", "category": "framework", "proficiency": "intermediate"},
        {"name": "Docker", "category": "tool", "proficiency": "intermediate"},
    ],
    "experience_summary": "Strong software engineering background with backend API development.",
    "education_summary": "Bachelor of Science in Computer Science.",
    "project_summary": "Built scalable cloud microservices.",
    "certifications": ["AWS Certified Developer"],
    "strengths": ["Clear technical focus", "Modern framework knowledge"],
    "weaknesses": ["Lacks quantitative metrics in accomplishment bullet points"],
    "missing_keywords": ["Kubernetes", "GraphQL", "CI/CD"],
    "grammar_suggestions": ["Use active verbs for past employment descriptions"],
    "formatting_suggestions": ["Ensure date formatting consistency across sections"],
    "improvement_recommendations": ["Quantify impact with metrics (e.g. 'Reduced latency by 40%')"],
})


@pytest.fixture
async def sample_resume(db_session: AsyncSession, sample_user: User) -> Resume:
    """Create a sample resume with extracted text for sample_user."""
    resume = Resume(user_id=sample_user.id, title="sample_resume.pdf")
    db_session.add(resume)
    await db_session.flush()

    version = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        filename="sample_resume.pdf",
        file_path="/tmp/sample_resume.pdf",
        file_size=1024,
        file_type="pdf",
        mime_type="application/pdf",
        extracted_text="Alex Mercer - Senior Software Engineer with 5 years experience in Python, FastAPI, and PostgreSQL.",
        is_current=True,
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(resume)
    return resume


@pytest.mark.asyncio
async def test_successful_resume_analysis(
    client: AsyncClient, sample_resume: Resume, auth_headers: dict[str, str]
):
    """POST /api/v1/resumes/{id}/analyze executes Ollama analysis, calculates ATS score, and saves output."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = SAMPLE_AI_JSON_OUTPUT

        response = await client.post(f"/api/v1/resumes/{sample_resume.id}/analyze", headers=auth_headers)
        assert response.status_code == 200

        payload = response.json()
        assert payload["status"] == "success"
        data = payload["data"]

        # Expected ATS score calculation based on rubric:
        # (85*0.20 + 80*0.30 + 75*0.25 + 90*0.15 + 85*0.10) = 17 + 24 + 18.75 + 13.5 + 8.5 = 81.8
        assert data["ats_score"] == 81.8
        assert data["scoring_breakdown"]["structure_score"] == 85.0
        assert data["scoring_breakdown"]["skills_score"] == 80.0
        assert len(data["skills"]) == 3
        assert "Kubernetes" in data["missing_keywords"]
        assert len(data["strengths"]) == 2

        # Verify GET /api/v1/resumes/{id}/analysis retrieves the saved record
        get_res = await client.get(f"/api/v1/resumes/{sample_resume.id}/analysis", headers=auth_headers)
        assert get_res.status_code == 200
        get_data = get_res.json()["data"]
        assert get_data["ats_score"] == 81.8


@pytest.mark.asyncio
async def test_ollama_unavailable_returns_503(
    client: AsyncClient, sample_resume: Resume, auth_headers: dict[str, str]
):
    """When Ollama is unreachable, endpoint should return 503 Service Unavailable with clear message."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = ConnectionError("Cannot connect to Ollama at http://localhost:11434")

        response = await client.post(f"/api/v1/resumes/{sample_resume.id}/analyze", headers=auth_headers)
        assert response.status_code == 503

        payload = response.json()
        assert payload["status"] == "error"
        assert "Ollama" in payload["message"]
        assert "unavailable" in payload["message"].lower()


@pytest.mark.asyncio
async def test_invalid_ai_response_returns_502(
    client: AsyncClient, sample_resume: Resume, auth_headers: dict[str, str]
):
    """When Ollama returns non-JSON or invalid schema, endpoint should return 502 Bad Gateway."""
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = "SORRY_I_CANNOT_FORMAT_JSON"

        response = await client.post(f"/api/v1/resumes/{sample_resume.id}/analyze", headers=auth_headers)
        assert response.status_code == 502
        assert "invalid response structure" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_empty_resume_text_analysis_returns_400(
    client: AsyncClient, db_session: AsyncSession, sample_user: User, auth_headers: dict[str, str]
):
    """Attempting analysis on a resume with empty extracted text should return 400 Bad Request."""
    empty_resume = Resume(user_id=sample_user.id, title="empty.pdf")
    db_session.add(empty_resume)
    await db_session.flush()

    empty_version = ResumeVersion(
        resume_id=empty_resume.id,
        version_number=1,
        filename="empty.pdf",
        file_path="/tmp/empty.pdf",
        file_size=0,
        file_type="pdf",
        mime_type="application/pdf",
        extracted_text="   ",
        is_current=True,
    )
    db_session.add(empty_version)
    await db_session.commit()

    response = await client.post(f"/api/v1/resumes/{empty_resume.id}/analyze", headers=auth_headers)
    assert response.status_code == 400
    assert "text is empty or missing" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_user_isolation_resume_analysis(
    client: AsyncClient, db_session: AsyncSession, sample_resume: Resume
):
    """User B cannot trigger or view User A's resume analysis (returns 404 Not Found)."""
    # Create User B
    user_b = User(
        email="user_b_analysis@example.com",
        name="User B",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({"sub": str(user_b.id), "email": user_b.email})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B attempts to analyze User A's resume -> 404
    post_res = await client.post(f"/api/v1/resumes/{sample_resume.id}/analyze", headers=headers_b)
    assert post_res.status_code == 404

    # User B attempts to get User A's analysis -> 404
    get_res = await client.get(f"/api/v1/resumes/{sample_resume.id}/analysis", headers=headers_b)
    assert get_res.status_code == 404
