"""
Career Intelligence Service.
Handles Job Description Analysis, Resume -> Job Description Match, and AI Cover Letter Generation.
Integrates directly with Ollama and stores match/cover letter history.
"""

import json
import logging
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.ai.ollama import OllamaProvider
from app.models.career_intelligence import ColdEmail, CoverLetter, ResumeJdMatch
from app.models.resume import Resume, ResumeVersion
from app.models.user import User
from app.schemas.career_intelligence import (
    ColdEmailGenerateRequest,
    ColdEmailHistoryItem,
    ColdEmailRegenerateSubjectRequest,
    ColdEmailRegenerateSubjectResponse,
    ColdEmailResponse,
    ColdEmailUpdateRequest,
    CoverLetterGenerateRequest,
    CoverLetterHistoryItem,
    CoverLetterResponse,
    JobDescriptionAnalysisResponse,
    JobDescriptionAnalyzeRequest,
    ResumeJdMatchHistoryItem,
    ResumeJdMatchRequest,
    ResumeJdMatchResponse,
)

logger = logging.getLogger(__name__)


# --- Helper: Safely parse JSON from LLM output ---
def _extract_json_from_llm(raw_text: str) -> dict:
    """Extract and parse JSON object from LLM response string."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try finding outermost braces
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except Exception:
                pass
    return {}


# =============================================================================
# 1. Job Description Analyzer
# =============================================================================

JD_ANALYZE_PROMPT = """You are an expert AI Job Description Analyst.
Analyze the following Job Description and extract structured information.

CRITICAL INSTRUCTION:
Base your extraction ONLY on the supplied Job Description text.
Do NOT invent requirements, qualifications, or responsibilities that are not mentioned.

JOB DESCRIPTION:
{job_description}

Respond ONLY with valid JSON matching this exact structure:
{{
  "job_title": "Extracted role title or null",
  "company": "Extracted company name or null",
  "required_skills": ["List of explicitly mandatory skills"],
  "preferred_skills": ["List of nice-to-have/preferred skills"],
  "technologies": ["List of specific tools, libraries, languages, databases, or frameworks"],
  "experience": ["Years of experience or specific seniority requirements mentioned"],
  "responsibilities": ["Primary role duties and expectations"],
  "education": ["Degree or education requirements mentioned"],
  "certifications": ["Certifications mentioned (e.g. AWS, PMP, CISSP) or empty"],
  "soft_skills": ["Communication, leadership, teamwork mentioned"],
  "keywords": ["Top domain and industry keywords from this description"]
}}
"""


async def analyze_job_description(
    payload: JobDescriptionAnalyzeRequest,
    ai_provider: OllamaProvider | None = None,
) -> JobDescriptionAnalysisResponse:
    """Extract structured skills, requirements, and keywords from a raw job description using Ollama."""
    jd_text = payload.job_description.strip()
    if len(jd_text) < 20:
        raise AppException("Job description is too short to analyze.", status_code=400)

    provider = ai_provider or OllamaProvider()
    prompt = JD_ANALYZE_PROMPT.format(job_description=jd_text[:12000])

    try:
        raw_response = await provider.generate(
            prompt,
            format="json",
            options={"temperature": 0.1, "num_predict": 1200, "num_ctx": 4096},
        )
    except Exception as exc:
        logger.error("Ollama error during JD analysis: %s", exc)
        raise AppException(
            "AI Service (Ollama) is currently unavailable for Job Description analysis. Please check your Ollama connection.",
            status_code=503,
        ) from exc

    parsed = _extract_json_from_llm(raw_response)
    if not parsed:
        logger.warning("Failed to parse JSON from Ollama JD analysis output: %s", raw_response[:300])
        # Fallback to simple extraction if LLM formatting failed
        return JobDescriptionAnalysisResponse(
            job_title=None,
            company=None,
            required_skills=[],
            preferred_skills=[],
            technologies=[],
            experience=[],
            responsibilities=[],
            education=[],
            certifications=[],
            soft_skills=[],
            keywords=[],
        )

    def _clean_list(items: object) -> list[str]:
        if not isinstance(items, list):
            return []
        res = []
        for i in items:
            if isinstance(i, str) and i.strip():
                res.append(i.strip())
        return res

    return JobDescriptionAnalysisResponse(
        job_title=parsed.get("job_title"),
        company=parsed.get("company"),
        required_skills=_clean_list(parsed.get("required_skills")),
        preferred_skills=_clean_list(parsed.get("preferred_skills")),
        technologies=_clean_list(parsed.get("technologies")),
        experience=_clean_list(parsed.get("experience")),
        responsibilities=_clean_list(parsed.get("responsibilities")),
        education=_clean_list(parsed.get("education")),
        certifications=_clean_list(parsed.get("certifications")),
        soft_skills=_clean_list(parsed.get("soft_skills")),
        keywords=_clean_list(parsed.get("keywords")),
    )


# =============================================================================
# 2. Resume -> Job Description Match
# =============================================================================

RESUME_JD_MATCH_PROMPT = """You are an expert AI Career Match & ATS Evaluator.
Compare the Candidate's Resume against the Target Job Description with high precision.

CANDIDATE RESUME CONTENT:
{resume_text}

TARGET JOB DESCRIPTION:
{job_description}

TARGET OCCUPATION CONTEXT: {occupation_context}

EVALUATION CRITERIA:
1. Overall Match Score (0 - 100)
2. Skills Match (0 - 100): Alignment with technical/domain skills.
3. Keyword Match (0 - 100): Alignment with key role terminology.
4. Experience Match (0 - 100): Seniority, scope, and domain relevance.
5. Responsibility Match (0 - 100): Demonstrated track record on target tasks.

CRITICAL RULES:
- "matched_skills": Skills explicitly present in BOTH the resume and the job description.
- "missing_skills": Skills required or preferred by the JD that were NOT found in the provided resume.
  NOTE: "Missing" strictly means "The skill was not found in the provided resume." Do not assert the candidate does not have it in real life.
- "partial_matches": Skills where the resume shows adjacent/related experience.
- "relevant_experience": 2-4 bullet points highlighting specific resume experiences that match the JD.
- "potential_gaps": 2-3 specific requirements where the resume lacks clear evidence.
- "improvement_suggestions": 3-4 actionable steps for the candidate to improve alignment with this specific role.

Respond ONLY with valid JSON:
{{
  "overall_score": 82.0,
  "skills_score": 80.0,
  "keyword_score": 85.0,
  "experience_score": 78.0,
  "responsibility_score": 84.0,
  "matched_skills": ["Python", "FastAPI", "SQL"],
  "missing_skills": ["Docker", "Kubernetes"],
  "partial_matches": ["AWS Cloud (Candidate has generic cloud experience)"],
  "relevant_experience": ["Built microservices handling 10k requests/sec", "Designed PostgreSQL schemas"],
  "potential_gaps": ["No explicit container orchestration experience listed", "CI/CD automation not mentioned"],
  "improvement_suggestions": ["Highlight Docker and container experience on the resume if possessed", "Add metrics demonstrating scale and team leadership"]
}}
"""


async def match_resume_to_jd(
    db: AsyncSession,
    user: User,
    payload: ResumeJdMatchRequest,
    ai_provider: OllamaProvider | None = None,
) -> ResumeJdMatchResponse:
    """Compare a candidate's uploaded resume with a target Job Description and save to database."""
    # 1. Fetch Resume & Current Version
    r_query = select(Resume).where(Resume.id == payload.resume_id, Resume.user_id == user.id)
    r_res = await db.execute(r_query)
    resume = r_res.scalar_one_or_none()
    if not resume:
        raise AppException("Resume not found or unauthorized.", status_code=404)

    v_query = (
        select(ResumeVersion)
        .where(ResumeVersion.resume_id == resume.id, ResumeVersion.is_current == True)
        .order_by(ResumeVersion.version_number.desc())
    )
    v_res = await db.execute(v_query)
    version = v_res.scalar_one_or_none()

    if not version or not version.extracted_text or not version.extracted_text.strip():
        # Fallback to any version with text
        v_fallback_query = (
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume.id, ResumeVersion.extracted_text != None)
            .order_by(ResumeVersion.version_number.desc())
        )
        v_res2 = await db.execute(v_fallback_query)
        version = v_res2.scalar_one_or_none()

    if not version or not version.extracted_text or not version.extracted_text.strip():
        raise AppException(
            "Selected resume has no parsed text content. Please re-upload your resume file.",
            status_code=400,
        )

    # 2. Target Occupation Benchmark Context (if provided or user has active goal)
    occupation_context = "General Tech Industry Standard"
    target_occupation_title = None
    if payload.target_occupation_id:
        occ_query = select(Occupation).where(Occupation.id == payload.target_occupation_id)
        occ_res = await db.execute(occ_query)
        occ = occ_res.scalar_one_or_none()
        if occ:
            occupation_context = f"{occ.title} ({occ.industry}): {occ.description[:200]}"
            target_occupation_title = occ.title

    # 3. Query Ollama for AI Match
    provider = ai_provider or OllamaProvider()
    prompt = RESUME_JD_MATCH_PROMPT.format(
        resume_text=version.extracted_text[:10000],
        job_description=payload.job_description.strip()[:10000],
        occupation_context=occupation_context,
    )

    try:
        raw_response = await provider.generate(
            prompt,
            format="json",
            options={"temperature": 0.2, "num_predict": 1400, "num_ctx": 4096},
        )
    except Exception as exc:
        logger.error("Ollama error during Resume-JD match: %s", exc)
        raise AppException(
            "AI Service (Ollama) is currently unavailable for resume matching. Please ensure Ollama is running.",
            status_code=503,
        ) from exc

    parsed = _extract_json_from_llm(raw_response)
    if not parsed:
        raise AppException("Could not generate structured match score from AI output.", status_code=500)

    def _clean_str_list(lst: object) -> list[str]:
        if not isinstance(lst, list):
            return []
        return [str(x).strip() for x in lst if str(x).strip()]

    def _clean_score(val: object, default: float = 70.0) -> float:
        try:
            num = float(val)
            return round(min(max(num, 0.0), 100.0), 1)
        except (ValueError, TypeError):
            return default

    overall_score = _clean_score(parsed.get("overall_score"), 70.0)
    skills_score = _clean_score(parsed.get("skills_score"), overall_score)
    keyword_score = _clean_score(parsed.get("keyword_score"), overall_score)
    experience_score = _clean_score(parsed.get("experience_score"), overall_score)
    responsibility_score = _clean_score(parsed.get("responsibility_score"), overall_score)

    matched_skills = _clean_str_list(parsed.get("matched_skills"))
    missing_skills = _clean_str_list(parsed.get("missing_skills"))
    partial_matches = _clean_str_list(parsed.get("partial_matches"))
    relevant_experience = _clean_str_list(parsed.get("relevant_experience"))
    potential_gaps = _clean_str_list(parsed.get("potential_gaps"))
    improvement_suggestions = _clean_str_list(parsed.get("improvement_suggestions"))

    # 4. Save Record to Database
    record = ResumeJdMatch(
        user_id=user.id,
        resume_id=resume.id,
        resume_title=resume.title,
        job_title=payload.job_title or parsed.get("job_title") or "Target Role",
        company_name=payload.company_name or parsed.get("company") or "Target Company",
        job_description=payload.job_description.strip(),
        overall_score=overall_score,
        skills_score=skills_score,
        keyword_score=keyword_score,
        experience_score=experience_score,
        responsibility_score=responsibility_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        partial_matches=partial_matches,
        relevant_experience=relevant_experience,
        potential_gaps=potential_gaps,
        improvement_suggestions=improvement_suggestions,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return ResumeJdMatchResponse(
        id=record.id,
        resume_id=record.resume_id,
        resume_title=record.resume_title,
        job_title=record.job_title,
        company_name=record.company_name,
        job_description_snippet=record.job_description[:300] + ("..." if len(record.job_description) > 300 else ""),
        overall_score=record.overall_score,
        skills_score=record.skills_score,
        keyword_score=record.keyword_score,
        experience_score=record.experience_score,
        responsibility_score=record.responsibility_score,
        matched_skills=record.matched_skills,
        missing_skills=record.missing_skills,
        partial_matches=record.partial_matches,
        relevant_experience=record.relevant_experience,
        potential_gaps=record.potential_gaps,
        improvement_suggestions=record.improvement_suggestions,
        target_occupation_title=target_occupation_title,
        created_at=record.created_at,
    )


async def get_match_history(
    db: AsyncSession,
    user: User,
    limit: int = 20,
) -> list[ResumeJdMatchHistoryItem]:
    """Retrieve historical match records for the user."""
    query = (
        select(ResumeJdMatch)
        .where(ResumeJdMatch.user_id == user.id)
        .order_by(ResumeJdMatch.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(query)
    records = res.scalars().all()

    return [
        ResumeJdMatchHistoryItem(
            id=r.id,
            resume_id=r.resume_id,
            resume_title=r.resume_title,
            job_title=r.job_title,
            company_name=r.company_name,
            overall_score=r.overall_score,
            skills_score=r.skills_score,
            created_at=r.created_at,
        )
        for r in records
    ]


async def get_match_detail(
    db: AsyncSession,
    user: User,
    match_id: int,
) -> ResumeJdMatchResponse:
    """Retrieve full details for a previous match evaluation."""
    query = select(ResumeJdMatch).where(ResumeJdMatch.id == match_id, ResumeJdMatch.user_id == user.id)
    res = await db.execute(query)
    record = res.scalar_one_or_none()
    if not record:
        raise AppException("Match record not found.", status_code=404)

    return ResumeJdMatchResponse(
        id=record.id,
        resume_id=record.resume_id,
        resume_title=record.resume_title,
        job_title=record.job_title,
        company_name=record.company_name,
        job_description_snippet=record.job_description[:300] + ("..." if len(record.job_description) > 300 else ""),
        overall_score=record.overall_score,
        skills_score=record.skills_score,
        keyword_score=record.keyword_score,
        experience_score=record.experience_score,
        responsibility_score=record.responsibility_score,
        matched_skills=record.matched_skills,
        missing_skills=record.missing_skills,
        partial_matches=record.partial_matches,
        relevant_experience=record.relevant_experience,
        potential_gaps=record.potential_gaps,
        improvement_suggestions=record.improvement_suggestions,
        created_at=record.created_at,
    )


# =============================================================================
# 3. AI Cover Letter Generator
# =============================================================================

COVER_LETTER_PROMPT = """You are an elite career strategist and executive resume writer.
Generate a tailored, highly compelling cover letter for the candidate.

CANDIDATE ACTUAL RESUME CONTENT:
{resume_text}

TARGET ROLE TITLE: {job_title}
TARGET COMPANY NAME: {company_name}
JOB DESCRIPTION:
{job_description}

DESIRED TONE: {tone} (Options: Professional, Confident, Concise)
DESIRED LENGTH: {length} (Options: Short, Standard, Detailed)

MANDATORY FACTUAL INTEGRITY RULES:
1. Base the letter STRICTLY on the candidate's actual resume provided above.
2. NEVER invent experiences, achievements, certifications, projects, tools, employment history, or numerical metrics.
3. Align the real achievements from the resume directly to the needs stated in the Job Description.
4. Output ONLY the raw letter text with appropriate professional formatting, salutation, paragraphs, and sign-off.
5. Do NOT include markdown code fences like ``` or introductory/closing conversational filler.
"""


async def generate_cover_letter(
    db: AsyncSession,
    user: User,
    payload: CoverLetterGenerateRequest,
    ai_provider: OllamaProvider | None = None,
) -> CoverLetterResponse:
    """Generate a cover letter strictly grounded in the candidate's real resume and the supplied JD."""
    # 1. Fetch Resume & Extracted Text
    r_query = select(Resume).where(Resume.id == payload.resume_id, Resume.user_id == user.id)
    r_res = await db.execute(r_query)
    resume = r_res.scalar_one_or_none()
    if not resume:
        raise AppException("Resume not found or unauthorized.", status_code=404)

    v_query = (
        select(ResumeVersion)
        .where(ResumeVersion.resume_id == resume.id, ResumeVersion.is_current == True)
        .order_by(ResumeVersion.version_number.desc())
    )
    v_res = await db.execute(v_query)
    version = v_res.scalar_one_or_none()

    if not version or not version.extracted_text or not version.extracted_text.strip():
        v_fallback_query = (
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume.id, ResumeVersion.extracted_text != None)
            .order_by(ResumeVersion.version_number.desc())
        )
        v_res2 = await db.execute(v_fallback_query)
        version = v_res2.scalar_one_or_none()

    if not version or not version.extracted_text or not version.extracted_text.strip():
        raise AppException(
            "Selected resume has no parsed text content to generate a cover letter from.",
            status_code=400,
        )

    # 2. Call Ollama
    provider = ai_provider or OllamaProvider()
    prompt = COVER_LETTER_PROMPT.format(
        resume_text=version.extracted_text[:10000],
        job_title=payload.job_title.strip(),
        company_name=payload.company_name.strip(),
        job_description=payload.job_description.strip()[:10000],
        tone=payload.tone,
        length=payload.length,
    )

    try:
        raw_response = await provider.generate(
            prompt,
            options={"temperature": 0.4, "num_predict": 1200, "num_ctx": 4096},
        )
    except Exception as exc:
        logger.error("Ollama error during cover letter generation: %s", exc)
        raise AppException(
            "AI Service (Ollama) is currently unavailable for Cover Letter generation. Please verify Ollama is running.",
            status_code=503,
        ) from exc

    cleaned_letter = raw_response.strip()
    if cleaned_letter.startswith("```"):
        cleaned_letter = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned_letter)
        cleaned_letter = re.sub(r"\n?```$", "", cleaned_letter).strip()

    # 3. Store in Database
    cover_letter = CoverLetter(
        user_id=user.id,
        resume_id=resume.id,
        job_title=payload.job_title.strip(),
        company_name=payload.company_name.strip(),
        tone=payload.tone,
        length=payload.length,
        content=cleaned_letter,
    )
    db.add(cover_letter)
    await db.commit()
    await db.refresh(cover_letter)

    return CoverLetterResponse(
        id=cover_letter.id,
        job_title=cover_letter.job_title,
        company_name=cover_letter.company_name,
        tone=cover_letter.tone,
        length=cover_letter.length,
        content=cover_letter.content,
        label="AI-generated cover letter",
        created_at=cover_letter.created_at,
    )


async def get_cover_letters(
    db: AsyncSession,
    user: User,
    limit: int = 20,
) -> list[CoverLetterHistoryItem]:
    """Retrieve previously generated cover letters."""
    query = (
        select(CoverLetter)
        .where(CoverLetter.user_id == user.id)
        .order_by(CoverLetter.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(query)
    records = res.scalars().all()

    return [
        CoverLetterHistoryItem(
            id=r.id,
            job_title=r.job_title,
            company_name=r.company_name,
            tone=r.tone,
            length=r.length,
            created_at=r.created_at,
        )
        for r in records
    ]


# =============================================================================
# 4. AI Cold Email Generator
# =============================================================================

COLD_EMAIL_PROMPT = """You are an elite career coach and executive recruiter specializing in high-converting, professional cold outreach emails.
Generate a tailored, high-impact, professional outreach email for the candidate.

OUTREACH TYPE: {email_type}
(Types: Recruiter Outreach, Hiring Manager Outreach, General HR Inquiry, Networking / Referral Request, Job Application Follow-up)

TARGET ROLE: {job_title}
TARGET COMPANY: {company_name}
RECIPIENT NAME: {recruiter_name}
RECIPIENT EMAIL: {recruiter_email}
JOB DESCRIPTION / REQUIREMENTS:
{job_description}

COMPANY INFORMATION / RECENT NEWS:
{company_info}

CANDIDATE ACTUAL BACKGROUND & CREDENTIALS:
{candidate_background}

PREVIOUS RESUME -> JOB DESCRIPTION MATCH INTELLIGENCE (IF REUSED):
{match_intelligence}

PORTFOLIO / SOCIAL LINKS:
{links}

ADDITIONAL CONTEXT / NOTES:
{additional_context}

DESIRED TONE: {tone} (Options: Professional, Friendly, Confident, Concise)
DESIRED LENGTH: {length} (Options: Short, Standard)

MANDATORY FACTUAL INTEGRITY & ANTI-HALLUCINATION RULES:
1. Base the email STRICTLY on the supplied candidate credentials and job information.
2. NEVER invent experience, achievements, certifications, companies, projects, metrics, or credentials.
3. NEVER invent recruiter names, recruiter emails, phone numbers, or company details.
4. If Recruiter Name is provided, address them politely (e.g. "Dear {recruiter_name}," or "Hi {recruiter_name},"). If not provided, use an appropriate salutation such as "Dear {company_name} Recruiting Team," or "Dear Hiring Team at {company_name},". NEVER fabricate a person's name.
5. If URLs (Portfolio, GitHub, LinkedIn) are supplied, integrate them naturally. If not provided, do NOT fabricate URLs or social links.
6. NEVER claim the candidate worked at {company_name} or make unsupported claims.
7. If any information is unavailable, omit it cleanly rather than inventing it.
8. Avoid generic clichés such as "Dear Sir/Madam, I am writing to apply for...". Instead, deliver a concise, relevant value proposition highlighting the candidate's real proficiencies.
9. Email length should generally be concise and easy to read on mobile in 30-45 seconds.

Respond ONLY with valid JSON matching this exact structure:
{{
  "subject": "Compelling subject line (e.g., Application — {job_title} | Key Skills or Candidate Name)",
  "body": "Full body of the email including salutation, value pitch, call-to-action, and professional sign-off."
}}
"""

REGENERATE_SUBJECT_PROMPT = """You are an expert career strategist. Generate a single crisp, compelling email subject line for cold outreach.

ROLE: {job_title}
COMPANY: {company_name}
CANDIDATE NAME: {candidate_name}
KEY RELEVANT SKILLS: {key_skills}
EMAIL TYPE: {email_type}

RULES:
- Must be concise (under 60 characters).
- Grounded strictly in the provided role, company, and real skills.
- Do NOT invent credentials or information.
- Return ONLY valid JSON:
{{"subject": "Your generated subject line"}}
"""


async def generate_cold_email(
    db: AsyncSession,
    user: User,
    payload: ColdEmailGenerateRequest,
    ai_provider: OllamaProvider | None = None,
) -> ColdEmailResponse:
    """Generate a personalized cold outreach email strictly grounded in candidate data and job context."""
    # 1. Candidate Background (Resume or Profile)
    candidate_background = "No resume selected."
    resume: Resume | None = None
    if payload.resume_id:
        r_query = select(Resume).where(Resume.id == payload.resume_id, Resume.user_id == user.id)
        r_res = await db.execute(r_query)
        resume = r_res.scalar_one_or_none()
        if resume:
            v_query = (
                select(ResumeVersion)
                .where(ResumeVersion.resume_id == resume.id, ResumeVersion.is_current == True)
                .order_by(ResumeVersion.version_number.desc())
            )
            v_res = await db.execute(v_query)
            version = v_res.scalar_one_or_none()
            if version and version.extracted_text:
                candidate_background = version.extracted_text[:4000]
            else:
                candidate_background = f"Resume: {resume.title}"

    if candidate_background == "No resume selected.":
        # Fallback to User Profile if available
        prof = user.profile
        profile_parts: list[str] = [f"Candidate Name: {user.name}"]
        if prof:
            if prof.current_role:
                profile_parts.append(f"Current Role: {prof.current_role}")
            if prof.experience:
                profile_parts.append(f"Experience Level: {prof.experience}")
            if prof.skills:
                profile_parts.append(f"Verified Skills: {', '.join(prof.skills)}")
            if prof.degree or prof.education:
                profile_parts.append(f"Education: {prof.degree or ''} {prof.education or ''}".strip())
        candidate_background = "\n".join(profile_parts)

    # 2. Match Intelligence (Reuse previous Resume -> JD Match if available)
    match_intelligence = "No prior match analysis found. Direct analysis applied."
    reused_match_id: int | None = None

    if payload.match_id:
        m_query = select(ResumeJdMatch).where(ResumeJdMatch.id == payload.match_id, ResumeJdMatch.user_id == user.id)
        m_res = await db.execute(m_query)
        match_record = m_res.scalar_one_or_none()
        if match_record:
            reused_match_id = match_record.id
            match_intelligence = (
                f"Overall Compatibility Score: {match_record.overall_score}%\n"
                f"Verified Matched Skills: {', '.join(match_record.matched_skills)}\n"
                f"Relevant Resume Experience: {'; '.join(match_record.relevant_experience)}\n"
                f"Partial Competencies: {', '.join(match_record.partial_matches[:3])}"
            )
    elif payload.resume_id and payload.job_description:
        # Check if there is a recent match record for this user and resume
        m_recent_query = (
            select(ResumeJdMatch)
            .where(ResumeJdMatch.user_id == user.id, ResumeJdMatch.resume_id == payload.resume_id)
            .order_by(ResumeJdMatch.created_at.desc())
            .limit(1)
        )
        m_recent_res = await db.execute(m_recent_query)
        recent_match = m_recent_res.scalar_one_or_none()
        if recent_match:
            reused_match_id = recent_match.id
            match_intelligence = (
                f"Overall Compatibility Score: {recent_match.overall_score}%\n"
                f"Verified Matched Skills: {', '.join(recent_match.matched_skills)}\n"
                f"Relevant Resume Experience: {'; '.join(recent_match.relevant_experience)}\n"
                f"Partial Competencies: {', '.join(recent_match.partial_matches[:3])}"
            )

    # 3. Format Links
    links_list: list[str] = []
    if payload.portfolio_url and payload.portfolio_url.strip():
        links_list.append(f"Portfolio: {payload.portfolio_url.strip()}")
    if payload.github_url and payload.github_url.strip():
        links_list.append(f"GitHub: {payload.github_url.strip()}")
    if payload.linkedin_url and payload.linkedin_url.strip():
        links_list.append(f"LinkedIn: {payload.linkedin_url.strip()}")
    links_str = "\n".join(links_list) if links_list else "None provided."

    # 4. Construct Prompt
    prompt = COLD_EMAIL_PROMPT.format(
        email_type=payload.email_type,
        job_title=payload.job_title.strip(),
        company_name=payload.company_name.strip(),
        recruiter_name=payload.recruiter_name.strip() if payload.recruiter_name else "Not provided (Use general professional salutation)",
        recruiter_email=payload.recruiter_email.strip() if payload.recruiter_email else "Not provided",
        job_description=payload.job_description.strip() if payload.job_description else "Not provided.",
        company_info=payload.company_info.strip() if payload.company_info else "None provided.",
        candidate_background=candidate_background,
        match_intelligence=match_intelligence,
        links=links_str,
        additional_context=payload.additional_context.strip() if payload.additional_context else "None provided.",
        tone=payload.tone,
        length=payload.length,
    )

    # 5. Query Ollama with JSON output expectation and retry fallback
    provider = ai_provider or OllamaProvider()
    parsed: dict = {}
    try:
        raw = await provider.generate(
            prompt=prompt,
            format="json",
            options={"temperature": 0.2, "num_predict": 1200, "num_ctx": 4096},
        )
        parsed = _extract_json_from_llm(raw)

        # Retry once if parsed output missing body
        if not parsed or not parsed.get("body"):
            logger.warning("Ollama cold email response incomplete, retrying once...")
            raw_retry = await provider.generate(
                prompt=prompt + "\n\nCRITICAL: You MUST respond with JSON containing both 'subject' and 'body' keys.",
                format="json",
                options={"temperature": 0.2, "num_predict": 1200, "num_ctx": 4096},
            )
            parsed = _extract_json_from_llm(raw_retry)
    except Exception as exc:
        logger.error("Ollama error during cold email generation: %s", exc)
        raise AppException(
            "AI Service (Ollama) is currently unavailable for Cold Email Generation. Please check your Ollama connection.",
            status_code=503,
        ) from exc

    # Default fallback content if JSON keys are absent
    subject = parsed.get("subject") if parsed and parsed.get("subject") else f"Application — {payload.job_title.strip()} | {user.name}"
    body = parsed.get("body") if parsed and parsed.get("body") else ""
    if not body.strip():
        # Fallback clean structure
        greeting = f"Dear {payload.recruiter_name.strip()}," if payload.recruiter_name else f"Dear {payload.company_name.strip()} Team,"
        body = (
            f"{greeting}\n\n"
            f"I am writing to express my strong interest in the {payload.job_title.strip()} opportunity at {payload.company_name.strip()}.\n\n"
            f"With verified experience aligned to your technical needs, I would welcome the opportunity to discuss how my background can contribute to your team's upcoming milestones.\n\n"
            f"Thank you for your time and consideration.\n\n"
            f"Best regards,\n{user.name}"
        )

    # Clean markdown artifacts from subject & body
    subject = subject.replace("\n", " ").strip()
    if body.startswith("```"):
        body = re.sub(r"^```[a-zA-Z]*\n?", "", body)
        body = re.sub(r"\n?```$", "", body).strip()

    # 6. Save to Database
    cold_email = ColdEmail(
        user_id=user.id,
        resume_id=resume.id if resume else None,
        match_id=reused_match_id,
        job_title=payload.job_title.strip(),
        company_name=payload.company_name.strip(),
        recruiter_name=payload.recruiter_name.strip() if payload.recruiter_name else None,
        recruiter_email=payload.recruiter_email.strip() if payload.recruiter_email else None,
        job_description=payload.job_description.strip() if payload.job_description else None,
        company_info=payload.company_info.strip() if payload.company_info else None,
        portfolio_url=payload.portfolio_url.strip() if payload.portfolio_url else None,
        github_url=payload.github_url.strip() if payload.github_url else None,
        linkedin_url=payload.linkedin_url.strip() if payload.linkedin_url else None,
        additional_context=payload.additional_context.strip() if payload.additional_context else None,
        email_type=payload.email_type,
        tone=payload.tone,
        length=payload.length,
        subject=subject,
        body=body,
    )
    db.add(cold_email)
    await db.commit()
    await db.refresh(cold_email)

    return ColdEmailResponse(
        id=cold_email.id,
        job_title=cold_email.job_title,
        company_name=cold_email.company_name,
        recruiter_name=cold_email.recruiter_name,
        recruiter_email=cold_email.recruiter_email,
        email_type=cold_email.email_type,
        tone=cold_email.tone,
        length=cold_email.length,
        subject=cold_email.subject,
        body=cold_email.body,
        created_at=cold_email.created_at,
    )


async def regenerate_cold_email_subject(
    payload: ColdEmailRegenerateSubjectRequest,
    ai_provider: OllamaProvider | None = None,
) -> ColdEmailRegenerateSubjectResponse:
    """Generate a crisp, refreshed subject line using Ollama without altering the email body."""
    prompt = REGENERATE_SUBJECT_PROMPT.format(
        job_title=payload.job_title.strip(),
        company_name=payload.company_name.strip(),
        candidate_name=payload.candidate_name or "Candidate",
        key_skills=", ".join(payload.key_skills) if payload.key_skills else "Engineering & Domain Experience",
        email_type=payload.email_type,
    )

    provider = ai_provider or OllamaProvider()
    try:
        raw = await provider.generate(
            prompt=prompt,
            format="json",
            options={"temperature": 0.3, "num_predict": 150, "num_ctx": 2048},
        )
        parsed = _extract_json_from_llm(raw)
        subject = parsed.get("subject") if parsed and parsed.get("subject") else None
    except Exception as exc:
        logger.warning("Ollama subject regeneration failed, applying deterministic fallback: %s", exc)
        subject = None

    if not subject:
        candidate_tag = f" — {payload.candidate_name}" if payload.candidate_name else ""
        skills_tag = f" | {payload.key_skills[0]}" if payload.key_skills else ""
        subject = f"Application: {payload.job_title.strip()} at {payload.company_name.strip()}{skills_tag}{candidate_tag}"

    subject = subject.replace("\n", " ").strip()
    return ColdEmailRegenerateSubjectResponse(subject=subject)


async def get_cold_email_history(
    db: AsyncSession,
    user: User,
    limit: int = 20,
) -> list[ColdEmailHistoryItem]:
    """Retrieve history of previously generated cold outreach emails for the user."""
    query = (
        select(ColdEmail)
        .where(ColdEmail.user_id == user.id)
        .order_by(ColdEmail.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(query)
    records = res.scalars().all()

    return [
        ColdEmailHistoryItem(
            id=r.id,
            job_title=r.job_title,
            company_name=r.company_name,
            email_type=r.email_type,
            recruiter_name=r.recruiter_name,
            recruiter_email=r.recruiter_email,
            subject=r.subject,
            created_at=r.created_at,
        )
        for r in records
    ]


async def get_cold_email_detail(
    db: AsyncSession,
    user: User,
    email_id: int,
) -> ColdEmailResponse:
    """Retrieve full details of a previously generated cold outreach email."""
    query = select(ColdEmail).where(ColdEmail.id == email_id, ColdEmail.user_id == user.id)
    res = await db.execute(query)
    record = res.scalar_one_or_none()
    if not record:
        raise AppException("Cold email record not found.", status_code=404)

    return ColdEmailResponse(
        id=record.id,
        job_title=record.job_title,
        company_name=record.company_name,
        recruiter_name=record.recruiter_name,
        recruiter_email=record.recruiter_email,
        email_type=record.email_type,
        tone=record.tone,
        length=record.length,
        subject=record.subject,
        body=record.body,
        created_at=record.created_at,
    )


async def update_cold_email(
    db: AsyncSession,
    user: User,
    email_id: int,
    payload: ColdEmailUpdateRequest,
) -> ColdEmailResponse:
    """Save user edits to a previously generated cold outreach email."""
    query = select(ColdEmail).where(ColdEmail.id == email_id, ColdEmail.user_id == user.id)
    res = await db.execute(query)
    record = res.scalar_one_or_none()
    if not record:
        raise AppException("Cold email record not found.", status_code=404)

    record.subject = payload.subject.strip()
    record.body = payload.body.strip()
    if payload.recruiter_name is not None:
        record.recruiter_name = payload.recruiter_name.strip() or None
    if payload.recruiter_email is not None:
        record.recruiter_email = payload.recruiter_email.strip() or None

    await db.commit()
    await db.refresh(record)

    return ColdEmailResponse(
        id=record.id,
        job_title=record.job_title,
        company_name=record.company_name,
        recruiter_name=record.recruiter_name,
        recruiter_email=record.recruiter_email,
        email_type=record.email_type,
        tone=record.tone,
        length=record.length,
        subject=record.subject,
        body=record.body,
        created_at=record.created_at,
    )


async def delete_cold_email(
    db: AsyncSession,
    user: User,
    email_id: int,
) -> bool:
    """Delete a saved cold email from the user's history."""
    query = select(ColdEmail).where(ColdEmail.id == email_id, ColdEmail.user_id == user.id)
    res = await db.execute(query)
    record = res.scalar_one_or_none()
    if not record:
        raise AppException("Cold email record not found.", status_code=404)

    await db.delete(record)
    await db.commit()
    return True

