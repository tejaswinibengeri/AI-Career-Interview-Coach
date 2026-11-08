"""
Resume-to-Job Matching Service.
Calculates deterministic match scores across skills, experience, and education,
and invokes Ollama AI to provide narrative explanations and recommendations.
"""

import json
import logging
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.ai import get_ai_provider
from app.integrations.ai.base import AIProvider
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.models.user import User
from app.schemas.job_match import AIJobMatchExplanationPayload, JobMatchResponse
from app.services.career_service import aggregate_user_skills
from app.services.job_service import get_job_by_id
from app.services.profile_service import get_or_create_profile

logger = logging.getLogger(__name__)

COMMON_TECH_KEYWORDS = [
    "python", "java", "javascript", "typescript", "react", "fastapi", "django", "flask",
    "sql", "postgresql", "mysql", "mongodb", "docker", "kubernetes", "aws", "azure",
    "git", "ci/cd", "rest api", "graphql", "machine learning", "deep learning", "pytorch",
    "tensorflow", "pandas", "numpy", "html", "css", "tailwinds", "node", "express",
    "linux", "bash", "jira", "agile", "scrum", "qa", "selenium", "pytest", "junit"
]


def extract_keywords_from_job(job_title: str, job_desc: str) -> list[str]:
    """Extract required technical and domain keywords from real job title and description."""
    text = f"{job_title} {job_desc}".lower()
    found: list[str] = []
    for kw in COMMON_TECH_KEYWORDS:
        if kw in text:
            found.append(kw)

    # Fallback to title words if no common tech keywords found
    if not found:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", job_title.lower())
        found = list(set(words))

    return found


def calculate_experience_match(user_exp: str | None, job_desc: str) -> float:
    """Calculate deterministic experience compatibility (0-100)."""
    if not user_exp or user_exp == "0 years" or user_exp == "Student / Entry Level":
        return 70.0 if "entry" in job_desc.lower() or "junior" in job_desc.lower() else 60.0
    if "senior" in job_desc.lower() or "lead" in job_desc.lower():
        return 85.0 if ("5+" in user_exp or "senior" in user_exp.lower()) else 70.0
    return 85.0


def calculate_education_match(user_degree: str | None, job_desc: str) -> float:
    """Calculate deterministic education compatibility (0-100)."""
    if user_degree and ("bachelor" in user_degree.lower() or "master" in user_degree.lower() or "computer" in user_degree.lower()):
        return 90.0
    return 75.0


JOB_MATCH_PROMPT_TEMPLATE = """You are an expert AI Talent Matcher and Technical Recruiter.
Analyze a candidate's compatibility for the following real job listing:

JOB TITLE: {job_title}
COMPANY: {job_company}
JOB DESCRIPTION:
---
{job_desc_snippet}
---

DETERMINISTIC MATCH EVALUATION:
- Overall Compatibility Match: {match_score}%
- Skill Overlap Match: {matched_skills_str}
- Missing Required Skills: {missing_skills_str}
- Candidate Education / Background: {user_education}

OUTPUT MUST BE VALID JSON ONLY matching this exact structure:
{{
  "explanation": "Narrative analysis analyzing why the candidate scored {match_score}% for '{job_title}' at {job_company}, highlighting key skill overlaps and identifying critical gaps.",
  "recommendations": [
    "Highlight experience in ... on your resume",
    "Add projects demonstrating ..."
  ]
}}
"""


async def match_resume_to_job(
    db: AsyncSession,
    user: User,
    job_id: int,
    resume_id: int | None = None,
    ai_provider: AIProvider | None = None,
) -> JobMatchResponse:
    """Calculate deterministic match between user resume/profile and real job listing, then generate AI explanation."""
    job_resp = await get_job_by_id(db, job_id=job_id, user_id=user.id)
    profile = await get_or_create_profile(db, user.id)
    user_skills = await aggregate_user_skills(db, user.id)

    # Required job skills
    job_keywords = extract_keywords_from_job(job_resp.title, job_resp.description)

    matched_skills: list[str] = []
    missing_skills: list[str] = []

    for kw in job_keywords:
        if kw in user_skills or any(kw in u_s or u_s in kw for u_s in user_skills):
            matched_skills.append(kw.title())
        else:
            missing_skills.append(kw.title())

    # Deterministic scoring calculation
    if job_keywords:
        skill_score = (len(matched_skills) / len(job_keywords)) * 100.0
    else:
        skill_score = 80.0

    exp_score = calculate_experience_match(profile.experience, job_resp.description)
    edu_score = calculate_education_match(profile.degree or profile.education, job_resp.description)

    raw_overall = skill_score * 0.50 + exp_score * 0.25 + edu_score * 0.25
    overall_match = round(min(max(raw_overall, 20.0), 98.0), 1)

    matched_str = ", ".join(matched_skills) or "None"
    missing_str = ", ".join(missing_skills) or "None"
    edu_str = profile.degree or profile.education or "Undergraduate"

    provider = ai_provider or get_ai_provider()
    prompt = JOB_MATCH_PROMPT_TEMPLATE.format(
        job_title=job_resp.title,
        job_company=job_resp.company,
        job_desc_snippet=job_resp.description[:2000],
        match_score=overall_match,
        matched_skills_str=matched_str,
        missing_skills_str=missing_str,
        user_education=edu_str,
    )

    try:
        raw_response = await provider.generate(
            prompt,
            format="json",
            options={"num_predict": 800, "num_ctx": 4096, "temperature": 0.2},
        )
    except ConnectionError as exc:
        logger.warning("Ollama connection error during job matching: %s", exc)
        raise AppException(
            message="AI Service (Ollama) is currently unavailable. Please ensure Ollama is running.",
            status_code=503,
        ) from exc
    except Exception as exc:
        logger.error("Ollama generation error during job matching: %s", exc)
        raise AppException(
            message=f"AI generation error: {exc}",
            status_code=502,
        ) from exc

    # Parse and validate AI payload
    from app.integrations.ai.json_utils import extract_and_parse_json

    parsed = extract_and_parse_json(raw_response)
    if isinstance(parsed, dict):
        explanation = str(parsed.get("explanation", f"Matched {overall_match}% compatibility."))
        recommendations = list(parsed.get("recommendations", []))
    else:
        explanation = f"Matched {overall_match}% compatibility based on target skills."
        recommendations = []

    job_match = JobMatch(
        user_id=user.id,
        job_id=job_resp.id,
        resume_id=resume_id,
        match_score=overall_match,
        experience_match=exp_score,
        education_match=edu_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        explanation=explanation,
        recommendations=recommendations,
    )
    db.add(job_match)
    await db.commit()

    return await get_user_job_match(db, user_id=user.id, job_id=job_resp.id)


async def get_user_job_match(db: AsyncSession, user_id: int, job_id: int) -> JobMatchResponse:
    """Retrieve existing job match analysis by user ID and job ID."""
    query = (
        select(JobMatch)
        .where(JobMatch.user_id == user_id, JobMatch.job_id == job_id)
        .order_by(JobMatch.created_at.desc())
    )
    res = await db.execute(query)
    match_rec = res.scalars().first()

    if not match_rec:
        raise AppException(
            message="No resume-to-job match analysis found for this job listing. Please run matching first.",
            status_code=404,
        )

    return JobMatchResponse.model_validate(match_rec)
