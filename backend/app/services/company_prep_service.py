"""
Company-Specific Preparation Service (Module 13).
Maintains verified company knowledge registry and generates interview preparation plans with explicitly labeled AI-generated practice questions.
"""

import asyncio
import json
import logging
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.ai.ollama import OllamaProvider
from app.models.company_prep import CompanyPrepPlan
from app.models.user import User
from app.schemas.company_prep import CompanyPrepResponse, GenerateCompanyPrepRequest

logger = logging.getLogger(__name__)

# Verified public company knowledge registry
VERIFIED_COMPANIES_REGISTRY: dict[str, dict] = {
    "google": {
        "name": "Google",
        "overview": "Google is a global technology leader in search engines, cloud computing (GCP), artificial intelligence (DeepMind, Gemini), online advertising, and mobile operating systems (Android). Known for high scale distributed systems engineering, Go, C++, Python, and Kubernetes.",
        "culture": "Emphasizes Googleyness, intellectual humility, collaborative innovation, and data-driven problem solving.",
        "core_skills": ["Distributed Systems", "Algorithms", "System Design", "Go/C++/Python", "Machine Learning"],
        "behavioral_focus": "Googleyness, collaboration, ambiguity navigation, and bias for impact.",
    },
    "amazon": {
        "name": "Amazon",
        "overview": "Amazon is a multinational tech giant focusing on e-commerce, cloud infrastructure (AWS), digital streaming, and AI. Known for microservices, Java, Python, DynamoDB, serverless architectures, and high-velocity execution.",
        "culture": "Guided strictly by 16 Leadership Principles including Customer Obsession, Ownership, Invent and Simplify, and Have Backbone; Disagree and Commit.",
        "core_skills": ["AWS Cloud Architecture", "Object-Oriented Design", "Java/C#", "Data Structures", "Microservices"],
        "behavioral_focus": "STAR Method answers strictly aligned with Amazon Leadership Principles.",
    },
    "microsoft": {
        "name": "Microsoft",
        "overview": "Microsoft is a global leader in software, cloud computing (Azure), enterprise solutions, productivity software (Microsoft 365), gaming (Xbox), and AI integrations (OpenAI partnership). Known for C#, .NET, TypeScript, C++, and Azure enterprise scale.",
        "culture": "Emphasizes a Growth Mindset, customer empathy, diversity, inclusion, and one-team collaboration.",
        "core_skills": ["C# / .NET", "Azure Cloud Services", "System Architecture", "TypeScript / React", "Data Structures"],
        "behavioral_focus": "Growth mindset, handling setbacks, team collaboration, and customer empathy.",
    },
    "meta": {
        "name": "Meta",
        "overview": "Meta develops technologies that help people connect, find communities, and grow businesses (Facebook, Instagram, WhatsApp, Quest VR). Known for high-throughput social graph architectures, React, PyTorch, C++, and Hack/PHP.",
        "culture": "Focuses on 'Move Fast', focus on long-term impact, build awesome things, and live in the future.",
        "core_skills": ["Data Structures & Algorithms", "React / Front-End Performance", "C++ / Systems", "PyTorch AI", "Large-scale Systems"],
        "behavioral_focus": "Fast execution, conflict resolution, project ownership, and bold decision making.",
    },
    "apple": {
        "name": "Apple",
        "overview": "Apple designs, manufactures, and markets smartphones (iPhone), personal computers (Mac), tablets, wearables, and services. Known for iOS/Swift development, hardware-software integration, C++, Metal, and privacy-first engineering.",
        "culture": "Fosters extreme attention to detail, secrecy, product excellence, and cross-functional alignment.",
        "core_skills": ["Swift / Objective-C", "C / C++", "iOS / macOS Architecture", "Memory Management", "User Interface Precision"],
        "behavioral_focus": "Product passion, attention to detail, domain mastery, and cross-team execution.",
    },
    "netflix": {
        "name": "Netflix",
        "overview": "Netflix is a premier entertainment streaming service with hundreds of millions of subscribers worldwide. Renowned for pioneering chaos engineering, microservices on AWS, high-throughput caching with EVCache, Java, Python, and data-driven personalization.",
        "culture": "Freedom and Responsibility culture, stunning colleagues, high performance context over control.",
        "core_skills": ["Microservices Architecture", "Distributed Systems", "Java / Spring Cloud", "Python Data Pipelines", "Cloud Scale AWS"],
        "behavioral_focus": "Context not control, high candor, independent decision making, and ownership.",
    },
    "uber": {
        "name": "Uber",
        "overview": "Uber develops ride-hailing, food delivery (Uber Eats), and freight transportation platforms. Pioneers in real-time geospatial computing, Go microservices, Kafka streaming, and distributed dispatch engines.",
        "culture": "Focuses on 'Go get it', 'Trip over pennies for dollars', champion diversity, and customer obsession.",
        "core_skills": ["Go / Java / Python", "Geospatial Indexing & H3", "Kafka & Stream Processing", "Distributed Concurrency", "System Design"],
        "behavioral_focus": "Speed of execution, handling scale under pressure, customer impact, and analytical rigor.",
    },
    "tcs": {
        "name": "Tata Consultancy Services (TCS)",
        "overview": "TCS is a global leader in IT services, consulting, and business solutions. Known for enterprise application development, Java, Python, SQL, cloud migration, and IT consulting.",
        "culture": "Emphasizes integrity, continuous learning (Elevate platform), customer satisfaction, and structured engineering processes.",
        "core_skills": ["Java / J2EE", "SQL & Database Queries", "Python", "Cloud Fundamentals", "Aptitude & Logical Reasoning"],
        "behavioral_focus": "Team spirit, adaptability, client communication, and willingness to learn.",
    },
    "infosys": {
        "name": "Infosys",
        "overview": "Infosys is a global digital services and consulting firm providing cloud transformation, software development, AI solutions, and enterprise services.",
        "culture": "Focuses on lifelong learning, ethical leadership, digital transformation, and client value.",
        "core_skills": ["Java / Spring Boot", "Python / Data Science", "SQL", "Web Development (HTML/CSS/JS)", "Problem Solving"],
        "behavioral_focus": "Communication skills, flexibility, problem-solving mindset, and teamwork.",
    },
    "wipro": {
        "name": "Wipro",
        "overview": "Wipro is a leading technology services and consulting company focused on building innovative solutions addressing clients' most complex digital transformation needs.",
        "culture": "Spirit of Wipro — intensity to win, act with sensitivity, be unyielding in integrity.",
        "core_skills": ["Java Full Stack", "Python & Automation", "Cloud Migration (AWS/Azure)", "RDBMS & SQL", "Agile Methodologies"],
        "behavioral_focus": "Customer centricity, collaborative attitude, and proactive learning.",
    },
}

COMPANY_PREP_PROMPT = """You are an expert Technical Interviewer for {company_name}.
Generate a concise, high-impact interview preparation plan for the target role '{target_role}' at {company_name}.

COMPANY NAME: {company_name}
TARGET ROLE: {target_role}
VERIFIED OVERVIEW SUMMARY: {verified_overview}

CRITICAL: Keep descriptions crisp, precise, and highly technical. Avoid filler.
Return valid JSON matching this exact structure:
{{
  "company_overview": "Concise 2-3 sentence overview of {company_name}'s core engineering stack and standards.",
  "role_summary": "Crisp summary of expectations and daily engineering responsibilities for a {target_role}.",
  "required_skills": ["Skill1", "Skill2", "Skill3", "Skill4", "Skill5", "Skill6"],
  "technical_prep_topics": [
    {{"topic": "Core Architecture", "description": "Key patterns, concurrency, and performance considerations", "importance": "High"}},
    {{"topic": "Data & Persistence", "description": "Database queries, indexing, and caching patterns", "importance": "High"}},
    {{"topic": "API & Services", "description": "Microservices, protocol design, and fault tolerance", "importance": "High"}}
  ],
  "coding_topics": ["Data Structures", "Algorithms", "System Design", "SQL Optimization"],
  "hr_topics": ["Why {company_name}?", "Describe a complex engineering challenge you solved", "Collaboration and conflicts"],
  "behavioral_prep": [
    {{"principle": "STAR Method", "advice": "Structure answers with quantifiable metrics.", "example_prompt": "Describe how you resolved an unexpected production incident."}},
    {{"principle": "Ownership & Impact", "advice": "Highlight calculated decision-making and cross-team alignment.", "example_prompt": "Tell me about an architectural improvement you championed."}}
  ],
  "practice_questions": [
    {{
      "question_text": "Targeted interview question for {target_role} at {company_name}?",
      "category": "Technical",
      "difficulty": "Medium",
      "label": "AI-generated practice question",
      "sample_answer_points": [
        "Core technical concept and standard implementation pattern.",
        "Key trade-offs, edge cases, and architectural best practices."
      ]
    }},
    {{
      "question_text": "System scalability or domain-specific challenge question?",
      "category": "System Design",
      "difficulty": "Hard",
      "label": "AI-generated practice question",
      "sample_answer_points": [
        "Bottleneck identification and distributed architecture strategy.",
        "Reliability, caching, and failover mechanisms."
      ]
    }}
  ]
}}
"""


async def generate_company_prep_plan(
    db: AsyncSession,
    user: User,
    request: GenerateCompanyPrepRequest,
    ai_provider: OllamaProvider | None = None,
) -> CompanyPrepResponse:
    """Generate or retrieve company-specific interview preparation plan."""
    c_key = request.company_name.strip().lower()
    is_verified = c_key in VERIFIED_COMPANIES_REGISTRY
    verified_data = VERIFIED_COMPANIES_REGISTRY.get(c_key)

    verification_notes = None
    if is_verified and verified_data:
        verified_overview = f"{verified_data['overview']} Culture: {verified_data['culture']}"
    else:
        verified_overview = f"Target Company: {request.company_name}. General industry benchmarks."
        verification_notes = f"Company facts for '{request.company_name}' could not be verified against official public company databases. Prep plan below uses verified role benchmarks with AI-generated practice questions."

    from app.integrations.ai.json_utils import extract_and_parse_json
    from app.services.company_questions_bank import get_curated_company_questions

    provider = ai_provider or OllamaProvider()
    prompt = COMPANY_PREP_PROMPT.format(
        company_name=request.company_name,
        target_role=request.target_role,
        is_verified=is_verified,
        verified_overview=verified_overview,
    )

    try:
        raw_json = await asyncio.wait_for(
            provider.generate(
                prompt,
                format="json",
                options={"num_predict": 1200, "num_ctx": 4096, "temperature": 0.2},
            ),
            timeout=90.0,
        )
        parsed = extract_and_parse_json(raw_json) or {}

        company_overview = parsed.get("company_overview", verified_overview)
        role_summary = parsed.get(
            "role_summary",
            f"Expectations for {request.target_role} include strong technical fundamentals and clear communication.",
        )
        required_skills = parsed.get(
            "required_skills",
            verified_data.get("core_skills", ["Problem Solving", "System Architecture", "Communication"])
            if verified_data
            else ["Problem Solving", "Data Structures", "System Design"],
        )
        technical_topics = parsed.get("technical_prep_topics", [])
        coding_topics = parsed.get("coding_topics", ["Data Structures", "Algorithms", "System Design"])
        hr_topics = parsed.get("hr_topics", ["Why this company?", "Career ambitions"])
        behavioral_prep = parsed.get("behavioral_prep", [])

        raw_questions = parsed.get("practice_questions", [])
        formatted_questions = []
        seen_questions = set()

        if isinstance(raw_questions, list):
            for q in raw_questions:
                if isinstance(q, dict) and q.get("question_text"):
                    q_text = str(q.get("question_text")).strip()
                    if q_text not in seen_questions:
                        seen_questions.add(q_text)
                        formatted_questions.append(
                            {
                                "question_text": q_text,
                                "category": str(q.get("category", "Technical")),
                                "difficulty": str(q.get("difficulty", "Medium")),
                                "label": "AI-generated practice question",  # ENFORCE MANDATORY LABEL
                                "sample_answer_points": q.get("sample_answer_points", []),
                            }
                        )

        # Supplement with curated questions bank if fewer than 25 questions
        if len(formatted_questions) < 25:
            bank_questions = get_curated_company_questions(
                request.company_name, request.target_role, count=25
            )
            for bq in bank_questions:
                b_text = bq["question_text"].strip()
                if b_text not in seen_questions:
                    seen_questions.add(b_text)
                    formatted_questions.append(bq)
                if len(formatted_questions) >= 25:
                    break

        # Save to database
        prep_plan = CompanyPrepPlan(
            user_id=user.id,
            company_name=request.company_name.strip(),
            target_role=request.target_role.strip(),
            is_verified_company=is_verified,
            verification_notes=verification_notes,
            company_overview=company_overview,
            role_summary=role_summary,
            required_skills=required_skills,
            technical_prep_topics=technical_topics,
            coding_topics=coding_topics,
            hr_topics=hr_topics,
            behavioral_prep=behavioral_prep,
            practice_questions=formatted_questions,
        )

        db.add(prep_plan)
        await db.commit()
        await db.refresh(prep_plan)

        return CompanyPrepResponse.model_validate(prep_plan)

    except ConnectionError as exc:
        raise AppException(
            message="AI Service (Ollama) is currently unavailable. Ensure Ollama is running.",
            status_code=503,
        ) from exc
    except Exception as exc:
        logger.error("Error generating company prep plan: %s", exc)
        from app.services.company_questions_bank import get_curated_company_questions

        fallback_questions = get_curated_company_questions(
            request.company_name, request.target_role, count=25
        )

        prep_plan = CompanyPrepPlan(
            user_id=user.id,
            company_name=request.company_name.strip(),
            target_role=request.target_role.strip(),
            is_verified_company=is_verified,
            verification_notes=verification_notes,
            company_overview=verified_overview,
            role_summary=f"Comprehensive preparation guide for {request.target_role} at {request.company_name}.",
            required_skills=verified_data.get("core_skills", ["System Design", "Problem Solving", "Clean Code"]) if verified_data else ["System Design", "Problem Solving", "Clean Code"],
            technical_prep_topics=[
                {"topic": "Core Data Structures & Algorithms", "description": "High-throughput problem solving, trees, graphs, and dynamic programming.", "importance": "High"},
                {"topic": "System Architecture & Scalability", "description": "Microservices, caching, rate limiting, and database indexing.", "importance": "High"},
                {"topic": "Language Mastery & Concurrency", "description": "Memory management, async event loops, and thread synchronization.", "importance": "High"},
            ],
            coding_topics=["Arrays & Two Pointers", "Trees & BST", "System Design", "SQL Query Optimization"],
            hr_topics=["Tell me about yourself", "Why this company?", "Conflict Resolution"],
            behavioral_prep=[
                {"principle": "STAR Method", "advice": "Structure answers as Situation, Task, Action, Result with quantifiable impact.", "example_prompt": "Describe a time when an unexpected incident occurred and how you resolved it."}
            ],
            practice_questions=fallback_questions,
        )

        db.add(prep_plan)
        await db.commit()
        await db.refresh(prep_plan)

        return CompanyPrepResponse.model_validate(prep_plan)


async def list_user_company_plans(db: AsyncSession, user: User) -> list[CompanyPrepResponse]:
    """Retrieve saved company prep plans for candidate."""
    query = (
        select(CompanyPrepPlan)
        .where(CompanyPrepPlan.user_id == user.id)
        .order_by(CompanyPrepPlan.created_at.desc())
    )
    res = await db.execute(query)
    plans = res.scalars().all()
    return [CompanyPrepResponse.model_validate(p) for p in plans]


async def get_company_prep_plan_by_id(
    db: AsyncSession, user: User, plan_id: int
) -> CompanyPrepResponse:
    """Get single company prep plan detail by ID."""
    query = select(CompanyPrepPlan).where(
        CompanyPrepPlan.id == plan_id, CompanyPrepPlan.user_id == user.id
    )
    res = await db.execute(query)
    plan = res.scalar_one_or_none()

    if not plan:
        raise AppException(message="Company preparation plan not found.", status_code=404)

    return CompanyPrepResponse.model_validate(plan)
