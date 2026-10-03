"""
AI Resume Analysis & ATS evaluation service.
Integrates with OllamaProvider to evaluate actual user resume text,
applies a transparent weighted rubric for ATS scores, and validates all AI outputs via Pydantic.
"""

import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.ai.ollama import OllamaProvider
from app.models.resume import Resume, ResumeVersion
from app.models.resume_analysis import ResumeAnalysis, ResumeSkill
from app.models.user import User
from app.schemas.resume_analysis import AIResumeAnalysisPayload
from app.services.profile_service import get_or_create_profile
from app.services.resume_service import get_current_version, get_user_resume_by_id

logger = logging.getLogger(__name__)


def compute_ats_score(payload: AIResumeAnalysisPayload) -> tuple[float, dict]:
    """Compute transparent weighted ATS score based on rubric component scores.

    Rubric Weights:
    - Structure & Section Completeness: 20%
    - Skills & Keywords Density: 30%
    - Work Experience & Impact: 25%
    - Education & Certifications: 15%
    - Formatting & Readability: 10%
    """
    weights = {
        "structure": 0.20,
        "skills": 0.30,
        "experience": 0.25,
        "education": 0.15,
        "formatting": 0.10,
    }

    raw_score = (
        payload.structure_score * weights["structure"]
        + payload.skills_score * weights["skills"]
        + payload.experience_score * weights["experience"]
        + payload.education_score * weights["education"]
        + payload.formatting_score * weights["formatting"]
    )

    overall_ats = round(min(max(raw_score, 0.0), 100.0), 1)

    breakdown = {
        "overall_ats_score": overall_ats,
        "structure_score": payload.structure_score,
        "skills_score": payload.skills_score,
        "experience_score": payload.experience_score,
        "education_score": payload.education_score,
        "formatting_score": payload.formatting_score,
        "weights": weights,
        "rubric_description": (
            "Transparent ATS Score formula: Structure (20%) + Skills & Keywords (30%) + "
            "Work Experience (25%) + Education (15%) + Formatting (10%)."
        ),
    }

    return overall_ats, breakdown


ANALYSIS_PROMPT_TEMPLATE = """You are an expert AI Resume Analyst and Applicant Tracking System (ATS) evaluator.
Analyze the following resume text and provide comprehensive, actionable feedback in valid JSON format.

DO NOT invent random scores — evaluate each section honestly from 0 to 100 based on standard industry criteria:
- structure_score: standard headings, contact info, completeness (0-100)
- skills_score: relevant technical/soft skill density and keywords (0-100)
- experience_score: work achievements, action verbs, and quantifiable impact (0-100)
- education_score: degree details, school, certifications (0-100)
- formatting_score: readability, grammar, clear layout (0-100)

IMPORTANT: Provide clear, detailed explanations for strengths, weaknesses, formatting, grammar, and improvement recommendations! Do NOT leave lists empty. Limit the extracted skills list to the top 15-20 key skills.

OUTPUT FORMAT MUST BE VALID JSON matching this exact structure:
{{
  "structure_score": 85.0,
  "skills_score": 80.0,
  "experience_score": 75.0,
  "education_score": 90.0,
  "formatting_score": 85.0,
  "experience_summary": "Summary of career trajectory and work history...",
  "education_summary": "Summary of academic qualifications...",
  "project_summary": "Summary of key projects mentioned...",
  "certifications": ["AWS Certified Solutions Architect"],
  "strengths": [
    "Demonstrates clear hands-on experience with modern technologies",
    "Strong educational background and structured academic credentials",
    "Clear separation of technical skills and project descriptions"
  ],
  "weaknesses": [
    "Lacks quantifiable business metrics (e.g., % latency reduction or user growth) in work bullet points",
    "Project bullet points could describe measurable problem-solving impact more clearly"
  ],
  "missing_keywords": ["Docker", "CI/CD", "Kubernetes", "Microservices", "Unit Testing"],
  "grammar_suggestions": [
    "Begin each bullet point with strong action verbs (e.g., 'Architected', 'Spearheaded', 'Optimized')",
    "Ensure consistent past-tense phrasing across previous employment roles"
  ],
  "formatting_suggestions": [
    "Ensure uniform date formatting (e.g., 'Jan 2024 - Present') throughout all sections",
    "Maintain consistent indentation and bullet spacing across technical skills and project blocks"
  ],
  "improvement_recommendations": [
    "Incorporate quantifiable metrics into each project (e.g., 'Reduced query latency by 35% through indexing')",
    "Highlight automated testing, containerization, or cloud deployment practices in project bullets",
    "Add direct links to live GitHub repositories or deployed demonstrations"
  ],
  "skills": [
    {{"name": "Python", "category": "technical", "proficiency": "advanced"}},
    {{"name": "FastAPI", "category": "framework", "proficiency": "intermediate"}}
  ]
}}

RESUME TEXT:
---
{resume_text}
---
"""


def _ensure_detailed_explanations(payload: AIResumeAnalysisPayload, extracted_text: str) -> AIResumeAnalysisPayload:
    """Ensure that strengths, weaknesses, and recommendations have rich, actionable explanations even if the LLM output was partial."""
    text_lower = extracted_text.lower()

    if not payload.strengths:
        payload.strengths = [
            "Demonstrates solid technical foundation and familiarity with core domain technologies.",
            "Well-organized resume format with dedicated technical competency and project sections.",
            "Relevant educational and background qualifications clearly specified."
        ]

    if not payload.weaknesses:
        weaknesses = []
        if "%" not in extracted_text and "increased" not in text_lower and "reduced" not in text_lower:
            weaknesses.append("Lacks quantifiable impact metrics (e.g., % improvement, revenue, or latency reduction).")
        if "test" not in text_lower and "pytest" not in text_lower and "ci/cd" not in text_lower:
            weaknesses.append("Limited emphasis on automated testing, CI/CD pipelines, or deployment workflows.")
        if not weaknesses:
            weaknesses.append("Could further highlight ownership and end-to-end delivery of complex features.")
        payload.weaknesses = weaknesses

    if not payload.improvement_recommendations:
        payload.improvement_recommendations = [
            "Add quantifiable business metrics to project bullet points using the Google X-Y-Z formula (Accomplished X, measured by Y, by doing Z).",
            "Incorporate industry-standard keywords related to cloud deployment (e.g., Docker, AWS/GCP, CI/CD) into project tech stacks.",
            "Include direct hyperlinks to live demo deployments, GitHub repositories, or technical writeups for key projects."
        ]

    if not payload.formatting_suggestions:
        payload.formatting_suggestions = [
            "Verify uniform date formats (Month Year - Month Year) and consistent bullet indentation across all sections.",
            "Ensure standard margin spacing and avoid multi-column layouts to optimize ATS parser accuracy."
        ]

    if not payload.grammar_suggestions:
        payload.grammar_suggestions = [
            "Start all experience bullet points with strong active action verbs (e.g., 'Engineered', 'Optimized', 'Deployed').",
            "Maintain consistent tense usage (past tense for previous roles, present tense for current position)."
        ]

    if not payload.missing_keywords:
        common_keywords = ["Docker", "CI/CD", "REST APIs", "Git", "System Design", "Unit Testing", "Cloud (AWS/GCP)"]
        payload.missing_keywords = [kw for kw in common_keywords if kw.lower() not in text_lower][:5]

    return payload


async def analyze_user_resume(
    db: AsyncSession,
    user: User,
    resume_id: int,
    version_id: int | None = None,
    force: bool = False,
    ai_provider: OllamaProvider | None = None,
) -> ResumeAnalysis:
    """Perform AI analysis on user's resume text using Ollama.

    Validates output via Pydantic and computes a transparent ATS score.

    Raises:
        AppException: 400 if resume text is empty, 503 if Ollama is down, 502 if AI output is invalid.
    """
    resume = await get_user_resume_by_id(db, user_id=user.id, resume_id=resume_id)

    target_version: ResumeVersion | None = None
    if version_id is not None:
        for ver in resume.versions:
            if ver.id == version_id:
                target_version = ver
                break
        if not target_version:
            raise AppException(message="Specified resume version not found.", status_code=404)
    else:
        target_version = get_current_version(resume)

    if not target_version or not target_version.extracted_text or not target_version.extracted_text.strip():
        raise AppException(
            message="Resume file text is empty or missing. Unable to perform AI analysis.",
            status_code=400,
        )

    # Check for existing analysis record for this exact version if not forcing re-analysis
    if not force:
        existing_query = (
            select(ResumeAnalysis)
            .where(
                ResumeAnalysis.resume_id == resume_id,
                ResumeAnalysis.resume_version_id == target_version.id,
            )
            .order_by(ResumeAnalysis.created_at.desc())
        )
        existing_res = await db.execute(existing_query)
        existing_analysis = existing_res.scalars().first()
        # Only return if it has valid populated strengths and weaknesses
        if existing_analysis and existing_analysis.strengths and len(existing_analysis.strengths) > 0 and existing_analysis.weaknesses and len(existing_analysis.weaknesses) > 0:
            return existing_analysis

    provider = ai_provider or OllamaProvider()

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(resume_text=target_version.extracted_text[:4000])

    try:
        raw_response = await provider.generate(
            prompt,
            format="json",
            options={"num_predict": 3500, "num_ctx": 4096, "temperature": 0.2},
        )
    except ConnectionError as exc:
        logger.warning("Ollama connection failed during resume analysis: %s", exc)
        raise AppException(
            message="AI Analysis Service (Ollama) is currently unavailable. Please ensure Ollama is running.",
            status_code=503,
        ) from exc
    except Exception as exc:
        logger.error("Ollama generation failed during resume analysis: %s", exc)
        raise AppException(
            message=f"AI provider analysis error: {exc}",
            status_code=502,
        ) from exc

    # Validate JSON payload with Pydantic using robust extraction
    from app.integrations.ai.json_utils import extract_and_parse_json

    parsed = extract_and_parse_json(raw_response)
    if not isinstance(parsed, dict):
        logger.error("Failed to parse LLM JSON response. Raw Output: %s", raw_response)
        raise AppException(
            message="AI provider returned invalid response structure. Please try re-analyzing.",
            status_code=502,
        )

    try:
        payload = AIResumeAnalysisPayload.model_validate(parsed)
    except Exception as exc:
        logger.error("Failed to validate AIResumeAnalysisPayload: %s\nParsed: %s", exc, parsed)
        raise AppException(
            message="AI provider returned incomplete analysis structure. Please try re-analyzing.",
            status_code=502,
        ) from exc

    # Ensure rich explanations are always populated
    payload = _ensure_detailed_explanations(payload, target_version.extracted_text)

    # Compute transparent ATS score & breakdown
    ats_score, scoring_breakdown = compute_ats_score(payload)

    analysis = ResumeAnalysis(
        resume_id=resume.id,
        resume_version_id=target_version.id,
        user_id=user.id,
        ats_score=ats_score,
        scoring_breakdown=scoring_breakdown,
        experience_summary=payload.experience_summary,
        education_summary=payload.education_summary,
        project_summary=payload.project_summary,
        certifications=payload.certifications,
        strengths=payload.strengths,
        weaknesses=payload.weaknesses,
        missing_keywords=payload.missing_keywords,
        grammar_suggestions=payload.grammar_suggestions,
        formatting_suggestions=payload.formatting_suggestions,
        improvement_recommendations=payload.improvement_recommendations,
        raw_ai_response=raw_response,
    )
    db.add(analysis)
    await db.flush()

    # Save extracted skills
    extracted_skill_names: list[str] = []
    for skill_item in payload.skills:
        skill_name = skill_item.name.strip()
        if skill_name:
            skill_entry = ResumeSkill(
                resume_analysis_id=analysis.id,
                skill_name=skill_name,
                category=skill_item.category or "technical",
                proficiency_level=skill_item.proficiency,
            )
            db.add(skill_entry)
            extracted_skill_names.append(skill_name)

    # Sync extracted skills to user's Career Profile if relevant
    if extracted_skill_names:
        profile = await get_or_create_profile(db, user.id)
        current_skills = set(profile.skills or [])
        new_skills = [s for s in extracted_skill_names if s not in current_skills]
        if new_skills:
            profile.skills = list(profile.skills or []) + new_skills

    await db.commit()

    # Return complete re-fetched analysis with skills relationship loaded
    return await get_user_resume_analysis(db, user_id=user.id, resume_id=resume.id, analysis_id=analysis.id)


async def get_user_resume_analysis(
    db: AsyncSession,
    user_id: int,
    resume_id: int,
    analysis_id: int | None = None,
) -> ResumeAnalysis:
    """Retrieve resume analysis record for a user.

    If analysis_id is None, returns the latest analysis record.
    """
    # Verify resume ownership
    await get_user_resume_by_id(db, user_id=user_id, resume_id=resume_id)

    query = select(ResumeAnalysis).where(
        ResumeAnalysis.resume_id == resume_id,
        ResumeAnalysis.user_id == user_id,
    )

    if analysis_id is not None:
        query = query.where(ResumeAnalysis.id == analysis_id)
    else:
        query = query.order_by(ResumeAnalysis.created_at.desc())

    result = await db.execute(query)
    analysis = result.scalars().first()

    if not analysis:
        raise AppException(
            message="No analysis record found for this resume. Please trigger analysis first.",
            status_code=404,
        )

    return analysis
