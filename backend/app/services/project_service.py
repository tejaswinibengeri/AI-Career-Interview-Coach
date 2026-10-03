"""
AI Project Recommendations Service (Module 15).
Generates personalized portfolio project recommendations tailored to candidate's actual skills, target career, skill gaps, and roadmap.
"""

import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.ai.ollama import OllamaProvider
from app.models.career import SkillGapReport
from app.models.project_recommendation import ProjectRecommendation
from app.models.roadmap import Roadmap
from app.models.user import Profile, User
from app.schemas.project_recommendation import (
    ProjectRecommendationResponse,
    UpdateProjectStatusRequest,
)

logger = logging.getLogger(__name__)

PROJECT_RECOMMENDATION_PROMPT = """You are a Principal Software Architect and Portfolio Coach.
Recommend 4 to 6 distinct, highly impressive portfolio projects tailored strictly to the candidate's actual career profile across Beginner, Intermediate, and Advanced tiers:

CANDIDATE TARGET CAREER ROLE: {target_role}
CURRENT ROLE & EXPERIENCE: {current_role}
KNOWN SKILLS: {known_skills}
IDENTIFIED SKILL GAPS: {skill_gaps}
ROADMAP GOALS: {roadmap_summary}

RULES:
1. Ensure projects directly address and close candidate's IDENTIFIED SKILL GAPS and align with TARGET CAREER ROLE.
2. Provide at least 1 Beginner, 2 Intermediate, and 1 Advanced project across diverse domains (e.g., API Engineering, Full-Stack Application, AI/Agentic System, Distributed Systems/DevOps).
3. Return valid JSON containing an array of project objects matching this exact structure:

[
  {{
    "title": "Clear Actionable Project Name",
    "difficulty": "Beginner",
    "description": "Clear problem statement solving a practical skill gap requirement.",
    "technologies": ["Python", "FastAPI", "SQLite", "Pytest"],
    "features": ["RESTful API Endpoints", "Input Validation", "Automated Unit Tests"],
    "skills_learned": ["REST Architecture", "Pydantic Validation"],
    "expected_outcome": "Working REST service with documentation and automated test suite."
  }},
  {{
    "title": "Full-Stack Application Name",
    "difficulty": "Intermediate",
    "description": "Full-stack interactive application with database persistence and authentication.",
    "technologies": ["React", "TypeScript", "FastAPI", "PostgreSQL", "Tailwind CSS"],
    "features": ["User Authentication", "Real-time Dashboard Analytics", "Database Migrations"],
    "skills_learned": ["Full Stack Integration", "State Management", "Database Design"],
    "expected_outcome": "Responsive production-style web application deployed with persistent storage."
  }},
  {{
    "title": "AI Agent or Intelligent Workflow Name",
    "difficulty": "Intermediate",
    "description": "Intelligent workflow leveraging LLM tool calling, vector search, or background task orchestration.",
    "technologies": ["Python", "LangChain", "FastAPI", "ChromaDB", "Docker"],
    "features": ["RAG Vector Pipeline", "Streaming AI Responses", "Contextual Memory"],
    "skills_learned": ["RAG Architecture", "Vector Databases", "Prompt Engineering"],
    "expected_outcome": "Deployable AI service with vector retrieval benchmarks and evaluation suite."
  }},
  {{
    "title": "Enterprise Distributed System Name",
    "difficulty": "Advanced",
    "description": "Enterprise-grade high-throughput distributed system with async queuing and telemetry.",
    "technologies": ["Python", "Docker", "Redis", "Kafka", "Kubernetes", "Prometheus"],
    "features": ["Distributed Message Queue", "Redis Caching Layer", "CI/CD Pipeline", "Telemetry Metrics"],
    "skills_learned": ["High Scalability", "Containerization", "System Monitoring"],
    "expected_outcome": "Production-ready distributed architecture containerized with Docker Compose and load test reports."
  }}
]
"""


async def generate_personalized_project_recommendations(
    db: AsyncSession,
    user: User,
    ai_provider: OllamaProvider | None = None,
) -> list[ProjectRecommendationResponse]:
    """Gather candidate actual DB context (skills, target role, skill gaps, roadmap) and generate Ollama project recommendations."""
    # 1. Fetch Profile
    prof_res = await db.execute(select(Profile).where(Profile.user_id == user.id))
    prof = prof_res.scalar_one_or_none()

    target_role = prof.target_role if prof and prof.target_role else "Software Engineer"
    current_role = prof.current_role if prof and prof.current_role else "Junior Developer"
    known_skills = ", ".join(prof.skills) if prof and prof.skills else "Python, SQL, HTML/CSS"

    # 2. Fetch Skill Gap Report
    sg_res = await db.execute(
        select(SkillGapReport)
        .where(SkillGapReport.user_id == user.id)
        .order_by(SkillGapReport.created_at.desc())
    )
    sg_report = sg_res.scalars().first()

    skill_gaps_list = []
    if sg_report and sg_report.missing_skills:
        for ms in sg_report.missing_skills:
            if isinstance(ms, str):
                skill_gaps_list.append(ms)
            elif isinstance(ms, dict) and "name" in ms:
                skill_gaps_list.append(str(ms["name"]))

    skill_gaps = ", ".join(skill_gaps_list) if skill_gaps_list else "Docker, AWS, System Design, React"

    # 3. Fetch Roadmap
    rm_res = await db.execute(
        select(Roadmap).where(Roadmap.user_id == user.id).order_by(Roadmap.created_at.desc())
    )
    roadmap = rm_res.scalars().first()
    roadmap_summary = f"Roadmap for {roadmap.target_role}" if roadmap else f"Target roadmap for {target_role}"

    provider = ai_provider or OllamaProvider()
    prompt = PROJECT_RECOMMENDATION_PROMPT.format(
        target_role=target_role,
        current_role=current_role,
        known_skills=known_skills,
        skill_gaps=skill_gaps,
        roadmap_summary=roadmap_summary,
    )

    from app.integrations.ai.json_utils import extract_and_parse_json

    # Clean up old unsaved and not-started projects on fresh generation so user gets new projects
    from sqlalchemy import delete
    await db.execute(
        delete(ProjectRecommendation).where(
            ProjectRecommendation.user_id == user.id,
            ProjectRecommendation.is_saved == False,
            ProjectRecommendation.status == "Not Started",
        )
    )

    try:
        raw_json = await provider.generate(
            prompt,
            format="json",
            options={"num_predict": 3000, "num_ctx": 4096, "temperature": 0.7},
        )
        parsed = extract_and_parse_json(raw_json)

        # Handle array or object wrapping
        if isinstance(parsed, dict) and "projects" in parsed:
            raw_projects = parsed["projects"]
        elif isinstance(parsed, list):
            raw_projects = parsed
        elif isinstance(parsed, dict) and any(k in parsed for k in ["title", "description"]):
            raw_projects = [parsed]
        else:
            raw_projects = []

        valid_projects = [
            p for p in raw_projects
            if isinstance(p, dict) and p.get("title") and p.get("title") != "Portfolio Project"
        ]

        if not valid_projects:
            raise ValueError("No valid project structures parsed from LLM response.")

        created_recommendations: list[ProjectRecommendationResponse] = []
        for p in valid_projects:
            diff = str(p.get("difficulty", "Intermediate")).capitalize()
            if diff not in ["Beginner", "Intermediate", "Advanced"]:
                diff = "Intermediate"

            pr = ProjectRecommendation(
                user_id=user.id,
                title=str(p.get("title", f"{target_role} Project")),
                description=str(p.get("description", f"Practical portfolio project for {target_role}.")),
                difficulty=diff,
                target_role=target_role,
                technologies=p.get("technologies", [target_role, "Python"]),
                features=p.get("features", ["Modular Architecture", "Clean Code"]),
                skills_learned=p.get("skills_learned", ["Problem Solving", "System Design"]),
                expected_outcome=str(p.get("expected_outcome", "Working project repository with documentation.")),
                is_saved=False,
                status="Not Started",
            )
            db.add(pr)
            await db.flush()
            created_recommendations.append(ProjectRecommendationResponse.model_validate(pr))

        await db.commit()
        return created_recommendations

    except ConnectionError as exc:
        raise AppException(
            message="AI Service (Ollama) is currently unavailable. Ensure Ollama is running.",
            status_code=503,
        ) from exc
    except Exception as exc:
        logger.warning("Error generating AI project recommendations, using dynamic fallbacks: %s", exc)
        # Dynamic fallback personalized recommendations
        fallback_projects = [
            {
                "title": f"{target_role} Skill-Gap Benchmark API",
                "difficulty": "Beginner",
                "description": f"Build a modular REST API demonstrating core competencies in {known_skills}.",
                "technologies": ["Python", "FastAPI", "SQLite", "Pytest"],
                "features": ["CRUD Operations", "Pydantic Models", "Automated Unit Tests"],
                "skills_learned": ["API Engineering", "Clean Architecture", "Unit Testing"],
                "expected_outcome": "Documented REST API with Automated Test Suite.",
            },
            {
                "title": f"Interactive Career Dashboard for {target_role}",
                "difficulty": "Intermediate",
                "description": f"Build a full-stack responsive web application addressing missing skills ({skill_gaps}).",
                "technologies": ["React", "TypeScript", "FastAPI", "PostgreSQL", "Tailwind CSS"],
                "features": ["JWT Authentication", "Interactive Visualizations", "Database Migrations"],
                "skills_learned": ["Full Stack Integration", "State Management", "Database Design"],
                "expected_outcome": "Fully responsive web application with database persistent storage.",
            },
            {
                "title": f"AI-Powered Knowledge & RAG Assistant for {target_role}",
                "difficulty": "Intermediate",
                "description": "Develop an intelligent search and retrieval-augmented generation (RAG) assistant with vector embeddings.",
                "technologies": ["Python", "LangChain", "FastAPI", "ChromaDB", "Docker"],
                "features": ["Document Ingestion & Chunking", "Semantic Search", "Streaming Responses"],
                "skills_learned": ["RAG Architecture", "Vector Embeddings", "AI Agent Pipelines"],
                "expected_outcome": "Containerized AI retrieval microservice with evaluation benchmarks.",
            },
            {
                "title": f"High-Throughput Distributed Platform for {target_role}",
                "difficulty": "Advanced",
                "description": "Architect a production-ready cloud system centerpiece with redis caching, background workers, and telemetry.",
                "technologies": ["Python", "Docker", "Redis", "Kafka", "PostgreSQL", "Prometheus"],
                "features": ["Caching Layer", "Asynchronous Task Queuing", "Rate Limiting", "Telemetry Monitoring"],
                "skills_learned": ["Distributed Systems", "Performance Tuning", "Container Orchestration"],
                "expected_outcome": "Production-grade portfolio repository with load test benchmarks and Docker Compose setup.",
            },
            {
                "title": f"Cloud-Native CI/CD & Microservice Deployment for {target_role}",
                "difficulty": "Advanced",
                "description": "Design an automated cloud pipeline with infrastructure as code, automated testing gates, and blue-green deployments.",
                "technologies": ["Docker", "Kubernetes", "GitHub Actions", "AWS", "Terraform"],
                "features": ["Automated CI/CD Pipeline", "Health Checking & Rollbacks", "Infrastructure as Code"],
                "skills_learned": ["Cloud Infrastructure", "DevOps Automation", "Production Reliability"],
                "expected_outcome": "Fully automated deployment repository with GitHub Actions workflows.",
            }
        ]

        created_recommendations = []
        for p in fallback_projects:
            pr = ProjectRecommendation(
                user_id=user.id,
                title=p["title"],
                description=p["description"],
                difficulty=p["difficulty"],
                target_role=target_role,
                technologies=p["technologies"],
                features=p["features"],
                skills_learned=p["skills_learned"],
                expected_outcome=p["expected_outcome"],
                is_saved=False,
                status="Not Started",
            )
            db.add(pr)
            await db.flush()
            created_recommendations.append(ProjectRecommendationResponse.model_validate(pr))

        await db.commit()
        return created_recommendations


async def list_user_project_recommendations(
    db: AsyncSession,
    user: User,
    difficulty: str | None = None,
    status_filter: str | None = None,
) -> list[ProjectRecommendationResponse]:
    """Retrieve saved and recommended portfolio projects for candidate."""
    query = (
        select(ProjectRecommendation)
        .where(ProjectRecommendation.user_id == user.id)
        .order_by(ProjectRecommendation.created_at.desc())
    )

    if difficulty and difficulty.strip():
        query = query.where(ProjectRecommendation.difficulty.ilike(f"%{difficulty.strip()}%"))

    if status_filter and status_filter.strip():
        query = query.where(ProjectRecommendation.status.ilike(f"%{status_filter.strip()}%"))

    res = await db.execute(query)
    projects = res.scalars().all()
    return [ProjectRecommendationResponse.model_validate(pr) for pr in projects]


async def update_project_status(
    db: AsyncSession,
    user: User,
    project_id: int,
    request: UpdateProjectStatusRequest,
) -> ProjectRecommendationResponse:
    """Update saved bookmark state or execution status (Not Started, In Progress, Completed)."""
    query = select(ProjectRecommendation).where(
        ProjectRecommendation.id == project_id,
        ProjectRecommendation.user_id == user.id,
    )
    res = await db.execute(query)
    pr = res.scalar_one_or_none()

    if not pr:
        raise AppException(message="Project recommendation not found.", status_code=404)

    if request.is_saved is not None:
        pr.is_saved = request.is_saved

    if request.status is not None:
        if request.status not in ["Not Started", "In Progress", "Completed"]:
            raise AppException(message="Invalid status value.", status_code=422)
        pr.status = request.status

    await db.commit()
    await db.refresh(pr)

    return ProjectRecommendationResponse.model_validate(pr)
