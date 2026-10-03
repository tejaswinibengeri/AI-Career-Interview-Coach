"""
Career Selection & Skill Gap Analysis Service.
Integrates O*NET career data provider, calculates skill gaps, and generates AI roadmaps via Ollama.
"""

import logging
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.ai.ollama import OllamaProvider
from app.integrations.careers.onet import ONET_DATASET, ONetCareerProvider
from app.models.career import (
    CareerGoal,
    Occupation,
    OccupationSkill,
    Skill,
    SkillGapReport,
    UserSkill,
)
from app.models.resume_analysis import ResumeAnalysis, ResumeSkill
from app.models.user import User
from app.schemas.career import AISkillGapExplanationPayload
from app.services.profile_service import get_or_create_profile

logger = logging.getLogger(__name__)


async def seed_occupations_if_empty(db: AsyncSession) -> None:
    """Seed O*NET occupations dataset into database if table is currently empty."""
    query = select(func.count()).select_from(Occupation)
    res = await db.execute(query)
    count = res.scalar() or 0

    if count > 0:
        return

    logger.info("Seeding O*NET occupation taxonomy database...")
    provider = ONetCareerProvider()
    dataset = await provider.search_occupations("", limit=100)

    for occ_data in dataset:
        occ = Occupation(
            code=occ_data.code,
            title=occ_data.title,
            description=occ_data.description,
            industry=occ_data.industry,
        )
        db.add(occ)
        await db.flush()

        for skill_data in occ_data.skills:
            # Check or create Skill
            s_query = select(Skill).where(func.lower(Skill.name) == skill_data.name.lower())
            s_res = await db.execute(s_query)
            skill = s_res.scalar_one_or_none()

            if not skill:
                skill = Skill(name=skill_data.name, category=skill_data.category)
                db.add(skill)
                await db.flush()

            occ_skill = OccupationSkill(
                occupation_id=occ.id,
                skill_id=skill.id,
                importance=skill_data.importance,
                level=skill_data.level,
                is_required=skill_data.is_required,
            )
            db.add(occ_skill)

    await db.commit()
    logger.info("O*NET occupations successfully seeded.")


async def search_occupations(db: AsyncSession, query: str = "", limit: int = 20) -> list[Occupation]:
    """Search occupations by title, code, industry, or description."""
    await seed_occupations_if_empty(db)

    stmt = select(Occupation)

    if query and query.strip():
        q = f"%{query.strip()}%"
        stmt = stmt.where(
            Occupation.title.ilike(q)
            | Occupation.code.ilike(q)
            | Occupation.industry.ilike(q)
            | Occupation.description.ilike(q)
        )

    stmt = stmt.order_by(Occupation.title.asc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_occupation_by_id(db: AsyncSession, occupation_id: int) -> Occupation:
    """Fetch an Occupation record by ID.

    Raises:
        AppException: 404 if not found.
    """
    await seed_occupations_if_empty(db)

    query = select(Occupation).where(Occupation.id == occupation_id)
    result = await db.execute(query)
    occ = result.scalar_one_or_none()

    if not occ:
        raise AppException(
            message="Target occupation not found.",
            status_code=404,
        )
    return occ


async def aggregate_user_skills(db: AsyncSession, user_id: int) -> set[str]:
    """Aggregate all user skills from Profile, Resume Analysis, and UserSkills.

    Returns normalized (lowercase) set of skill strings.
    """
    skills_set: set[str] = set()

    # 1. Profile skills
    profile = await get_or_create_profile(db, user_id)
    if profile.skills:
        for s in profile.skills:
            if s and s.strip():
                skills_set.add(s.strip().lower())

    # 2. Resume extracted skills
    ra_query = select(ResumeSkill.skill_name).join(ResumeAnalysis).where(ResumeAnalysis.user_id == user_id)
    ra_res = await db.execute(ra_query)
    for s_name in ra_res.scalars().all():
        if s_name and s_name.strip():
            skills_set.add(s_name.strip().lower())

    # 3. UserSkills entries
    us_query = select(UserSkill.skill_name).where(UserSkill.user_id == user_id)
    us_res = await db.execute(us_query)
    for s_name in us_res.scalars().all():
        if s_name and s_name.strip():
            skills_set.add(s_name.strip().lower())

    return skills_set


SKILL_GAP_PROMPT_TEMPLATE = """You are an AI Career Coach analyzing a skill gap report for a user aiming for the target role: '{occupation_title}'.

Target Occupation Description: {occupation_description}

SKILL GAP EVALUATION:
- Match Percentage: {match_percentage}%
- Matched / Strong Skills: {strong_skills_list}
- Missing Skills: {missing_skills_list}

PROVIDE OUTPUT AS VALID JSON matching this exact structure:
{{
  "explanation": "Narrative explanation analyzing the user's current readiness, highlighting their strong areas and explaining why key missing skills are crucial for '{occupation_title}'.",
  "learning_order": [
    {{
      "step": 1,
      "skill_name": "Skill Name",
      "priority": "High",
      "rationale": "Reason why this skill should be learned first (e.g. foundational prerequisite)."
    }}
  ]
}}
"""


async def generate_skill_gap_report(
    db: AsyncSession,
    user: User,
    occupation_id: int,
    ai_provider: OllamaProvider | None = None,
) -> SkillGapReport:
    """Compare user's real skills against O*NET occupation requirements and generate AI report."""
    occupation = await get_occupation_by_id(db, occupation_id)
    user_skills = await aggregate_user_skills(db, user.id)

    strong_skills: list[dict] = []
    intermediate_skills: list[dict] = []
    missing_skills: list[dict] = []

    req_skills = occupation.skills or []

    for occ_skill in req_skills:
        skill_name = occ_skill.skill.name
        norm_name = skill_name.strip().lower()

        skill_info = {
            "name": skill_name,
            "category": occ_skill.skill.category,
            "importance": occ_skill.importance,
            "level": occ_skill.level,
        }

        # Check match against user skills
        if norm_name in user_skills or any(norm_name in u_s or u_s in norm_name for u_s in user_skills):
            if occ_skill.importance >= 85.0:
                strong_skills.append(skill_info)
            else:
                intermediate_skills.append(skill_info)
        else:
            # Priority assignment based on O*NET importance
            if occ_skill.importance >= 88.0:
                priority = "High"
            elif occ_skill.importance >= 80.0:
                priority = "Medium"
            else:
                priority = "Low"

            missing_skills.append({**skill_info, "priority": priority})

    total_req = len(req_skills)
    if total_req > 0:
        match_score = (len(strong_skills) * 1.0 + len(intermediate_skills) * 0.6) / total_req * 100
        match_percentage = round(min(max(match_score, 0.0), 100.0), 1)
    else:
        match_percentage = 100.0

    # Format lists for LLM prompt
    strong_list_str = ", ".join([s["name"] for s in strong_skills + intermediate_skills]) or "None yet"
    missing_list_str = ", ".join([s["name"] for s in missing_skills]) or "None"

    provider = ai_provider or OllamaProvider()
    prompt = SKILL_GAP_PROMPT_TEMPLATE.format(
        occupation_title=occupation.title,
        occupation_description=occupation.description,
        match_percentage=match_percentage,
        strong_skills_list=strong_list_str,
        missing_skills_list=missing_list_str,
    )

    try:
        raw_response = await provider.generate(
            prompt,
            format="json",
            options={"num_predict": 800, "num_ctx": 4096, "temperature": 0.2},
        )
    except ConnectionError as exc:
        logger.warning("Ollama connection failed during skill gap analysis: %s", exc)
        raise AppException(
            message="AI Service (Ollama) is currently unavailable. Please ensure Ollama is running.",
            status_code=503,
        ) from exc
    except Exception as exc:
        logger.error("Ollama generation failed during skill gap analysis: %s", exc)
        raise AppException(
            message=f"AI generation error: {exc}",
            status_code=502,
        ) from exc

    # Parse and validate AI explanation & learning order
    from app.integrations.ai.json_utils import extract_and_parse_json

    parsed = extract_and_parse_json(raw_response)
    if isinstance(parsed, dict):
        ai_explanation = str(parsed.get("explanation", "Skill gap analysis completed."))
        learning_order = list(parsed.get("learning_order", []))
    else:
        ai_explanation = "Skill gap analysis completed based on occupational requirements."
        learning_order = []

    report = SkillGapReport(
        user_id=user.id,
        occupation_id=occupation.id,
        match_percentage=match_percentage,
        strong_skills=strong_skills,
        intermediate_skills=intermediate_skills,
        missing_skills=missing_skills,
        learning_order=learning_order,
        ai_explanation=ai_explanation,
    )
    db.add(report)
    await db.commit()

    return await get_latest_user_skill_gap_report(db, user_id=user.id, report_id=report.id)


async def get_latest_user_skill_gap_report(
    db: AsyncSession,
    user_id: int,
    report_id: int | None = None,
) -> SkillGapReport:
    """Retrieve the user's latest skill gap report or specific report ID."""
    query = select(SkillGapReport).where(SkillGapReport.user_id == user_id)

    if report_id is not None:
        query = query.where(SkillGapReport.id == report_id)
    else:
        query = query.order_by(SkillGapReport.created_at.desc())

    result = await db.execute(query)
    report = result.scalars().first()

    if not report:
        raise AppException(
            message="No skill gap report found. Please run a skill gap analysis first.",
            status_code=404,
        )
    return report


async def set_user_career_goal(db: AsyncSession, user: User, occupation_id: int) -> CareerGoal:
    """Set active target career goal for user and update profile target_role."""
    occupation = await get_occupation_by_id(db, occupation_id)

    # Deactivate existing active goals
    await db.execute(
        update(CareerGoal)
        .where(CareerGoal.user_id == user.id, CareerGoal.is_active == True)
        .values(is_active=False)
    )

    goal = CareerGoal(
        user_id=user.id,
        occupation_id=occupation.id,
        target_role_title=occupation.title,
        is_active=True,
    )
    db.add(goal)

    # Update profile target_role & career_goal
    profile = await get_or_create_profile(db, user.id)
    profile.target_role = occupation.title
    if not profile.career_goal or profile.career_goal.startswith("No career goal"):
        profile.career_goal = f"Targeting {occupation.title} — {occupation.description[:150]}..."

    await db.commit()

    query = select(CareerGoal).where(CareerGoal.id == goal.id)
    res = await db.execute(query)
    return res.scalar_one()
