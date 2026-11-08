"""
Personal Trainer Service.
Handles AI goal investigation, deep day-by-day learning plan generation,
task completion tracking, adaptive carry-overs, workload rescheduling,
review confidence evaluation, and n8n webhook notifications.
"""

from datetime import datetime, timezone
import json
import logging
import re
from typing import Any
import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AppException
from app.integrations.ai.json_utils import extract_and_parse_json
from app.integrations.ai import get_ai_provider
from app.integrations.ai.base import AIProvider
from app.models.personal_trainer import (
    PersonalTrainerSettings,
    TrainingDay,
    TrainingPlan,
    TrainingTask,
)
from app.models.resume import Resume, ResumeVersion
from app.models.resume_analysis import ResumeAnalysis, ResumeSkill
from app.models.user import User
from app.schemas.personal_trainer import (
    DayReviewRequest,
    PersonalTrainerSettingsUpdateRequest,
    RescheduleDayRequest,
    TaskStatusUpdateRequest,
    TrainingPlanCreateRequest,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 1. Resume Skills Extraction (Zero Duplicate AI Parsing)
# =============================================================================

async def get_user_resume_skills(db: AsyncSession, user: User) -> list[str]:
    """Retrieve verified skills from user's existing resume analysis or profile.
    Reuses existing parsed data without making duplicate LLM calls.
    """
    extracted_skills: list[str] = []

    # 1. Try ResumeSkill records linked to user's resume analyses
    stmt = (
        select(ResumeSkill.skill_name)
        .join(ResumeAnalysis, ResumeSkill.resume_analysis_id == ResumeAnalysis.id)
        .where(ResumeAnalysis.user_id == user.id)
        .order_by(ResumeSkill.id.asc())
    )
    result = await db.execute(stmt)
    skills = [s for s in result.scalars().all() if s and s.strip()]
    if skills:
        # Deduplicate preserving order
        seen = set()
        for s in skills:
            clean = s.strip()
            if clean.lower() not in seen:
                seen.add(clean.lower())
                extracted_skills.append(clean)
        return extracted_skills

    # 2. Fallback to User Profile skills if set
    if user.profile and user.profile.skills:
        for s in user.profile.skills:
            if s and s.strip() and s.strip().lower() not in [x.lower() for x in extracted_skills]:
                extracted_skills.append(s.strip())
        if extracted_skills:
            return extracted_skills

    # 3. Fallback: Parse common tech tokens from user's latest ResumeVersion text
    v_stmt = (
        select(ResumeVersion.extracted_text)
        .join(Resume, ResumeVersion.resume_id == Resume.id)
        .where(Resume.user_id == user.id, ResumeVersion.extracted_text != None)
        .order_by(ResumeVersion.version_number.desc())
    )
    v_res = await db.execute(v_stmt)
    raw_text = v_res.scalar_one_or_none()
    if raw_text:
        common_tech_keywords = [
            "Python", "FastAPI", "Django", "Flask", "JavaScript", "TypeScript",
            "React", "Node.js", "SQL", "PostgreSQL", "MySQL", "MongoDB",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "Linux",
            "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow",
            "DSA", "REST API", "GraphQL", "System Design", "Ollama", "Pandas", "NumPy"
        ]
        text_lower = raw_text.lower()
        for kw in common_tech_keywords:
            if re.search(rf"\b{re.escape(kw.lower())}\b", text_lower):
                extracted_skills.append(kw)

    return extracted_skills


# =============================================================================
# 2. Dynamic Training Plan Generation (Ollama + Anti-Hallucination)
# =============================================================================

PLAN_SYSTEM_PROMPT = """You are an elite AI Personal Learning Manager and Technical Career Coach.
Your task is to decompose the user's career/skill goal into a deep, prerequisite-aware, day-by-day training plan.

CRITICAL RULES:
1. Divide the plan into individual DAYS (Day 1, Day 2, Day 3...).
2. Every day must strictly respect the daily study limit: {daily_hours} hours ({max_daily_minutes} minutes maximum total task time per day).
3. Every task must be GRANULAR (e.g. 20m, 30m, 45m, 60m). NEVER generate vague multi-hour tasks.
4. Tasks must have types: "theory", "practice", "project", or "assessment".
5. Prerequisite progression must be deep and logical (Foundations -> Intermediate -> Advanced -> Capstone/Projects -> Interview Preparation).
6. ANTI-HALLUCINATION: Do NOT fabricate fake personal candidate achievements or imaginary company policies. Focus on concrete technical skills, architectures, and practice tasks.
7. Return strictly a JSON object with this structure:
{{
  "title": "...",
  "estimated_duration_days": 30,
  "total_learning_hours": 60.0,
  "phases_summary": [
    {{"phase": 1, "title": "Phase 1: Foundations", "description": "Core concepts and setup"}},
    {{"phase": 2, "title": "Phase 2: Deep Dive", "description": "Implementation and patterns"}},
    {{"phase": 3, "title": "Phase 3: Applied Projects", "description": "Hands-on projects"}},
    {{"phase": 4, "title": "Phase 4: Interview & Mastery", "description": "System design and mock tests"}}
  ],
  "days": [
    {{
      "day_number": 1,
      "phase_name": "Phase 1: Foundations",
      "objective": "Concise daily focus",
      "topics": ["Topic A", "Topic B"],
      "expected_outcome": "Specific skill mastered today",
      "tasks": [
        {{
          "title": "Specific granular task",
          "description": "Short guideline",
          "task_type": "theory",
          "estimated_minutes": 30
        }},
        {{
          "title": "Hands-on practice task",
          "description": "Short guideline",
          "task_type": "practice",
          "estimated_minutes": 45
        }}
      ]
    }}
  ]
}}
"""

def _build_deterministic_deep_plan(
    title: str,
    target_skill: str | None,
    target_role: str | None,
    target_company: str | None,
    current_skills: list[str],
    experience_level: str,
    daily_hours: float,
    learning_preference: str,
) -> dict[str, Any]:
    """Deterministic fallback generator for comprehensive day-by-day plan."""
    daily_mins = int(daily_hours * 60)
    target_name = target_role or target_skill or "Software Engineer"
    company_name = target_company or "Target Company"

    # Curate realistic topics according to target domain
    if "data" in target_name.lower() or "ai" in target_name.lower() or "machine" in target_name.lower():
        topics_sequence = [
            ("Core Mathematics & Vector Calculus", ["Linear Algebra", "Matrix Operations", "Gradients"]),
            ("NumPy & Numerical Processing", ["Array slicing", "Broadcasting", "Vectorized functions"]),
            ("Pandas Data Wrangling", ["DataFrames", "GroupBy", "Missing data imputation"]),
            ("Statistical Modeling & Hypothesis", ["Normal distribution", "p-values", "A/B test principles"]),
            ("Supervised Learning Foundations", ["Linear & Logistic Regression", "Loss functions", "Regularization"]),
            ("Decision Trees & Ensemble Methods", ["Random Forest", "XGBoost", "Hyperparameter tuning"]),
            ("Model Validation & Metrics", ["Precision/Recall", "ROC-AUC", "Cross validation strategies"]),
            ("Deep Learning & PyTorch Basics", ["Tensors", "Autograd", "Building a Neural Net"]),
            ("Convolutional & Sequential Nets", ["CNNs", "RNNs", "LSTM architecture"]),
            ("Transformer Architectures & Attention", ["Self-attention", "Multi-head attention", "Positional encoding"]),
            ("LLM Fine-Tuning & Embeddings", ["HuggingFace", "Embeddings generation", "Cosine similarity"]),
            ("Vector Databases & Retrieval", ["ChromaDB", "FAISS", "Semantic indexing"]),
            ("Retrieval-Augmented Generation (RAG)", ["Chunking strategies", "Context retrieval", "Prompt engineering"]),
            ("AI Agent Systems & Tool Use", ["Tool routing", "ReAct loop", "Memory patterns"]),
            ("Production AI Deployment", ["FastAPI serving", "Model quantization (GGUF)", "Docker containerization"]),
            (f"{target_name} System Design & Case Study", ["Latency optimization", "Cache tiers", "Batching"]),
            (f"{company_name} Technical Interview Prep", ["Coding practice", "ML theory questions", "Behavioral STAR"]),
        ]
    else:
        topics_sequence = [
            ("Programming Fundamentals & Typing", ["Type system", "Memory model", "Control flows"]),
            ("Object-Oriented & Functional Patterns", ["Classes", "Decorators", "Generators"]),
            ("Data Structures & Algorithms I", ["Arrays", "Hash Tables", "Two-pointer technique"]),
            ("Data Structures & Algorithms II", ["Trees", "Binary Search", "Graph Traversal (BFS/DFS)"]),
            ("REST API Architecture & Validation", ["HTTP methods", "Schema validation", "Status codes"]),
            ("Database Modeling & SQL Mastery", ["Schema design", "Indexes", "Complex Joins", "ACID"]),
            ("Asynchronous Programming", ["Async/Await", "Event loop", "Concurrency patterns"]),
            ("Authentication & Security", ["JWT Tokens", "OAuth2 flows", "Rate limiting"]),
            ("Testing & Test-Driven Development", ["Unit tests", "Integration tests", "Mocking"]),
            ("Caching & Performance Optimization", ["Redis caching", "Query optimization", "Connection pooling"]),
            ("Containerization with Docker", ["Dockerfiles", "Multi-stage builds", "Docker Compose"]),
            ("CI/CD & Cloud Deployment", ["GitHub Actions", "Environment configs", "Cloud hosting"]),
            ("Microservices & Message Queues", ["Event-driven systems", "RabbitMQ/Kafka basics"]),
            ("System Design & High Availability", ["Load balancing", "Horizontal scaling", "Database replication"]),
            ("Capstone Project Development", ["End-to-end implementation", "Architecture review"]),
            (f"{company_name} Coding & Technical Assessment", ["DSA problem solving", "Code quality"]),
            (f"{company_name} Behavioral & Architecture Round", ["System design case study", "STAR framework"]),
        ]

    days_list: list[dict[str, Any]] = []
    day_counter = 1

    for idx, (topic_title, subtopics) in enumerate(topics_sequence):
        phase_num = min(4, (idx // 4) + 1)
        phase_name = f"Phase {phase_num}: " + (
            "Foundations" if phase_num == 1 else
            "Deep Dive" if phase_num == 2 else
            "Applied Projects" if phase_num == 3 else
            "Interview & Mastery"
        )

        # Build granular tasks that sum to approximately daily_mins (with buffer)
        task1_mins = min(45, daily_mins // 3)
        task2_mins = min(45, daily_mins // 3)
        task3_mins = max(30, daily_mins - task1_mins - task2_mins - 15)  # leave ~15 min buffer

        tasks = [
            {
                "title": f"Deep Dive: {subtopics[0]}",
                "description": f"Master conceptual theory and mental models for {subtopics[0]}.",
                "task_type": "theory",
                "estimated_minutes": task1_mins,
            },
            {
                "title": f"Hands-on Implementation: {subtopics[1] if len(subtopics) > 1 else 'Code Sandbox'}",
                "description": f"Write working code examples and verify corner cases for {subtopics[1] if len(subtopics) > 1 else 'concepts'}.",
                "task_type": "practice",
                "estimated_minutes": task2_mins,
            },
            {
                "title": f"Practice Challenge: {subtopics[2] if len(subtopics) > 2 else 'Synthesis Exercise'}",
                "description": "Solve practical exercises and integrate into your portfolio workspace.",
                "task_type": "project" if "project" in learning_preference.lower() else "practice",
                "estimated_minutes": task3_mins,
            },
        ]

        days_list.append({
            "day_number": day_counter,
            "phase_name": phase_name,
            "objective": topic_title,
            "topics": subtopics,
            "expected_outcome": f"Confidently apply {topic_title} to build real-world components.",
            "tasks": tasks,
        })
        day_counter += 1

    total_hours = round(len(days_list) * (daily_mins / 60.0), 1)

    return {
        "title": title,
        "estimated_duration_days": len(days_list) * 2,  # total estimated journey
        "total_learning_hours": total_hours * 2,
        "phases_summary": [
            {"phase": 1, "title": "Phase 1: Foundations", "description": "Essential syntax, prerequisites, and foundational theory."},
            {"phase": 2, "title": "Phase 2: Deep Dive", "description": "Core algorithms, data systems, and architectural patterns."},
            {"phase": 3, "title": "Phase 3: Applied Projects", "description": "Hands-on projects, containerization, and production deployment."},
            {"phase": 4, "title": "Phase 4: Interview & Mastery", "description": "System design, question bank drill-down, and mock interviews."},
        ],
        "days": days_list,
    }


async def generate_training_plan(
    db: AsyncSession,
    user: User,
    request: TrainingPlanCreateRequest,
) -> TrainingPlan:
    """Generate and persist a deep, dependency-aware day-by-day training plan."""

    # 1. Determine title from dimensions
    parts = []
    if request.target_role:
        parts.append(request.target_role)
    if request.target_skill:
        parts.append(f"({request.target_skill})")
    if request.target_company:
        parts.append(f"at {request.target_company}")
    title = " ".join(parts) if parts else "Personalized Career Training Plan"

    # 2. Deactivate previous active plans for this user
    existing_plans_stmt = select(TrainingPlan).where(
        TrainingPlan.user_id == user.id,
        TrainingPlan.is_active == True,
    )
    res = await db.execute(existing_plans_stmt)
    for p in res.scalars().all():
        p.is_active = False

    # 3. Call Ollama for deep reasoning and task generation
    max_daily_minutes = int(request.daily_hours * 60)
    user_skills_str = ", ".join(request.current_skills) if request.current_skills else "None specified"

    user_prompt = f"""Target Goal:
- Dimensions: {', '.join(request.goal_dimensions)}
- Target Role: {request.target_role or 'Not specified'}
- Target Skill: {request.target_skill or 'Not specified'}
- Target Company: {request.target_company or 'Not specified'}
- Candidate Existing Skills: {user_skills_str}
- Experience Level: {request.experience_level}
- Daily Study Availability: {request.daily_hours} hours ({max_daily_minutes} minutes/day)
- Learning Preference: {request.learning_preference}
- Target Deadline: {request.target_deadline or 'Flexible'}

Build a complete, deep, multi-phase training plan divided into individual days (at least 14 days initially).
Ensure EVERY day has granular tasks with estimated_minutes that sum to <= {max_daily_minutes} minutes.
"""

    parsed_plan = None
    try:
        provider = get_ai_provider()
        is_healthy = await provider.health_check()
        if is_healthy:
            full_prompt = (
                PLAN_SYSTEM_PROMPT.format(
                    daily_hours=request.daily_hours,
                    max_daily_minutes=max_daily_minutes,
                )
                + "\n\n"
                + user_prompt
            )
            raw_response = await provider.generate(
                full_prompt,
                format="json",
                options={"temperature": 0.2, "num_predict": 3000},
                timeout=45.0,
            )
            parsed = extract_and_parse_json(raw_response)
            if parsed and isinstance(parsed, dict) and "days" in parsed and len(parsed["days"]) > 0:
                parsed_plan = parsed
    except Exception as exc:
        logger.warning("Ollama plan generation fell back to deterministic generator: %s", exc)

    if not parsed_plan:
        parsed_plan = _build_deterministic_deep_plan(
            title=title,
            target_skill=request.target_skill,
            target_role=request.target_role,
            target_company=request.target_company,
            current_skills=request.current_skills,
            experience_level=request.experience_level,
            daily_hours=request.daily_hours,
            learning_preference=request.learning_preference,
        )

    # 4. Create database entities
    target_deadline_dt = None
    if request.target_deadline:
        try:
            target_deadline_dt = datetime.fromisoformat(request.target_deadline).replace(tzinfo=timezone.utc)
        except Exception:
            pass

    plan = TrainingPlan(
        user_id=user.id,
        title=title,
        goal_dimensions=request.goal_dimensions,
        target_skill=request.target_skill,
        target_role=request.target_role,
        target_company=request.target_company,
        current_skills=request.current_skills,
        experience_level=request.experience_level,
        daily_hours=request.daily_hours,
        learning_preference=request.learning_preference,
        target_deadline=target_deadline_dt,
        estimated_duration_days=parsed_plan.get("estimated_duration_days", len(parsed_plan.get("days", []))),
        total_learning_hours=float(parsed_plan.get("total_learning_hours", 60.0)),
        overall_progress=0.0,
        is_active=True,
        phases_summary=parsed_plan.get("phases_summary", []),
    )
    db.add(plan)
    await db.flush()

    for d_idx, day_data in enumerate(parsed_plan.get("days", [])):
        tasks_data = day_data.get("tasks", [])
        total_mins = sum(t.get("estimated_minutes", 30) for t in tasks_data)

        # Strictly enforce daily hours limit if AI exceeded it
        if total_mins > max_daily_minutes:
            factor = (max_daily_minutes - 10) / total_mins
            for t in tasks_data:
                t["estimated_minutes"] = max(15, int(t.get("estimated_minutes", 30) * factor))
            total_mins = sum(t["estimated_minutes"] for t in tasks_data)

        training_day = TrainingDay(
            plan_id=plan.id,
            day_number=day_data.get("day_number", d_idx + 1),
            phase_name=day_data.get("phase_name", "Core Curriculum"),
            objective=day_data.get("objective", f"Day {d_idx + 1} Objectives"),
            topics=day_data.get("topics", []),
            expected_outcome=day_data.get("expected_outcome", "Master foundational concepts and exercises."),
            total_planned_minutes=total_mins,
            is_completed=False,
        )
        db.add(training_day)
        await db.flush()

        for t_idx, task_dict in enumerate(tasks_data):
            task = TrainingTask(
                day_id=training_day.id,
                title=task_dict.get("title", f"Task {t_idx + 1}"),
                description=task_dict.get("description", ""),
                task_type=task_dict.get("task_type", "practice"),
                estimated_minutes=task_dict.get("estimated_minutes", 30),
                status="not_started",
                order_index=t_idx,
            )
            db.add(task)

    await db.commit()
    reload_stmt = (
        select(TrainingPlan)
        .options(selectinload(TrainingPlan.days).selectinload(TrainingDay.tasks))
        .where(TrainingPlan.id == plan.id)
    )
    reload_res = await db.execute(reload_stmt)
    return reload_res.scalar_one()


# =============================================================================
# 3. Active Plan & Adaptive Schedule Rollover
# =============================================================================

async def get_active_training_plan(db: AsyncSession, user: User) -> TrainingPlan | None:
    """Fetch user's current active training plan and adaptively roll over incomplete tasks."""
    stmt = (
        select(TrainingPlan)
        .options(selectinload(TrainingPlan.days).selectinload(TrainingDay.tasks))
        .where(TrainingPlan.user_id == user.id, TrainingPlan.is_active == True)
        .order_by(TrainingPlan.id.desc())
    )
    res = await db.execute(stmt)
    plan = res.scalar_one_or_none()
    if not plan:
        return None

    # Calculate overall progress from all tasks
    all_tasks_stmt = (
        select(TrainingTask)
        .join(TrainingDay, TrainingTask.day_id == TrainingDay.id)
        .where(TrainingDay.plan_id == plan.id)
    )
    all_tasks_res = await db.execute(all_tasks_stmt)
    all_tasks = all_tasks_res.scalars().all()
    if all_tasks:
        completed_count = sum(1 for t in all_tasks if t.status == "completed")
        new_progress = round((completed_count / len(all_tasks)) * 100.0, 1)
        if plan.overall_progress != new_progress:
            plan.overall_progress = new_progress
            plan.updated_at = datetime.now(timezone.utc)
            await db.commit()
            reload_stmt = (
                select(TrainingPlan)
                .options(selectinload(TrainingPlan.days).selectinload(TrainingDay.tasks))
                .where(TrainingPlan.id == plan.id)
            )
            reload_res = await db.execute(reload_stmt)
            plan = reload_res.scalar_one()

    return plan


async def get_daily_training_view(
    db: AsyncSession,
    user: User,
    day_number: int | None = None,
) -> dict[str, Any]:
    """Get rich view for a specific day including yesterday summary and tomorrow preview."""
    plan = await get_active_training_plan(db, user)
    if not plan:
        raise AppException("No active training plan found. Please create one first.", status_code=404)

    # If day_number not given, find first day with incomplete tasks, or day 1
    if day_number is None:
        target_day = None
        for d in plan.days:
            if not d.is_completed:
                target_day = d
                break
        if not target_day:
            target_day = plan.days[0] if plan.days else None
    else:
        target_day = next((d for d in plan.days if d.day_number == day_number), None)

    if not target_day:
        raise AppException(f"Day {day_number} not found in current plan.", status_code=404)

    # 1. Adaptive Check: Incomplete tasks from yesterday automatically carried over
    if target_day.day_number > 1:
        prev_day = next((d for d in plan.days if d.day_number == target_day.day_number - 1), None)
        if prev_day:
            for pt in prev_day.tasks:
                if pt.status in ("not_started", "in_progress"):
                    # Check if already carried over to target_day
                    already_in_today = any(
                        t.title == pt.title and t.is_carried_over for t in target_day.tasks
                    )
                    if not already_in_today:
                        carried_task = TrainingTask(
                            day_id=target_day.id,
                            title=f"{pt.title} (Carried Over)",
                            description=f"Incomplete from Day {prev_day.day_number}. {pt.description or ''}",
                            task_type=pt.task_type,
                            estimated_minutes=pt.estimated_minutes,
                            status="not_started",
                            order_index=0,
                            is_carried_over=True,
                            original_day_number=prev_day.day_number,
                        )
                        db.add(carried_task)
                        pt.status = "rescheduled"
                        await db.commit()
                        await db.refresh(target_day)

    # 2. Yesterday Summary
    yesterday_summary = {
        "has_yesterday": target_day.day_number > 1,
        "completed": [],
        "incomplete": [],
    }
    if target_day.day_number > 1:
        y_day = next((d for d in plan.days if d.day_number == target_day.day_number - 1), None)
        if y_day:
            yesterday_summary["completed"] = [t.title for t in y_day.tasks if t.status == "completed"]
            yesterday_summary["incomplete"] = [t.title for t in y_day.tasks if t.status != "completed"]

    # 3. Tomorrow Preview
    tomorrow_preview = None
    next_day = next((d for d in plan.days if d.day_number == target_day.day_number + 1), None)
    if next_day:
        tomorrow_preview = {
            "day_number": next_day.day_number,
            "objective": next_day.objective,
            "total_minutes": next_day.total_planned_minutes,
            "task_count": len(next_day.tasks),
        }

    # 4. Workload calculation
    workload_minutes = sum(t.estimated_minutes for t in target_day.tasks if t.status != "skipped")
    available_minutes = int(plan.daily_hours * 60)
    buffer_minutes = max(0, available_minutes - workload_minutes)

    # 5. Dynamic AI Summary
    carried_count = sum(1 for t in target_day.tasks if t.is_carried_over)
    completed_yesterday_count = len(yesterday_summary["completed"])
    total_yesterday_count = completed_yesterday_count + len(yesterday_summary["incomplete"])

    ai_summary_parts = []
    if total_yesterday_count > 0:
        ai_summary_parts.append(
            f"Yesterday you completed {completed_yesterday_count} of {total_yesterday_count} tasks."
        )
    if carried_count > 0:
        ai_summary_parts.append(
            f"{carried_count} incomplete task{'s have' if carried_count > 1 else ' has'} been moved forward to today."
        )
    ai_summary_parts.append(f"Today's focus is {target_day.objective}.")
    ai_summary_parts.append(
        f"Planned workload: {workload_minutes // 60}h {workload_minutes % 60}m (Available: {plan.daily_hours}h)."
    )

    return {
        "plan_id": plan.id,
        "goal_title": plan.title,
        "day_number": target_day.day_number,
        "total_days": len(plan.days),
        "current_day": target_day,
        "yesterday_summary": yesterday_summary,
        "tomorrow_preview": tomorrow_preview,
        "daily_ai_summary": " ".join(ai_summary_parts),
        "available_hours": plan.daily_hours,
        "workload_minutes": workload_minutes,
        "available_minutes": available_minutes,
        "buffer_minutes": buffer_minutes,
        "overall_progress": plan.overall_progress,
    }


# =============================================================================
# 4. Task Status & Adaptive Rescheduling
# =============================================================================

async def update_training_task_status(
    db: AsyncSession,
    user: User,
    task_id: int,
    request: TaskStatusUpdateRequest,
) -> TrainingTask:
    """Update task completion status, record time, and recalculate plan progress."""
    stmt = (
        select(TrainingTask)
        .join(TrainingDay, TrainingTask.day_id == TrainingDay.id)
        .join(TrainingPlan, TrainingDay.plan_id == TrainingPlan.id)
        .where(TrainingTask.id == task_id, TrainingPlan.user_id == user.id)
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise AppException("Task not found or access unauthorized.", status_code=404)

    task.status = request.status
    if request.notes is not None:
        task.notes = request.notes
    if request.time_spent_minutes is not None:
        task.time_spent_minutes = request.time_spent_minutes

    if request.status == "completed":
        task.completed_at = datetime.now(timezone.utc)
    elif request.status in ("not_started", "in_progress"):
        task.completed_at = None

    # Check if all tasks for this day are completed
    day_stmt = (
        select(TrainingDay)
        .options(selectinload(TrainingDay.tasks))
        .where(TrainingDay.id == task.day_id)
    )
    day_res = await db.execute(day_stmt)
    day = day_res.scalar_one()

    all_done = all(t.status in ("completed", "skipped") for t in day.tasks)
    day.is_completed = all_done
    if all_done:
        day.completed_at = datetime.now(timezone.utc)
    else:
        day.completed_at = None

    await db.commit()
    await db.refresh(task)

    # --- Send task completion email notification (non-blocking) ---
    if request.status == "completed":
        try:
            from app.services.email_service import send_task_completed_notification

            # Load plan for progress and title
            plan_stmt = (
                select(TrainingPlan)
                .where(TrainingPlan.id == day.plan_id)
            )
            plan_res = await db.execute(plan_stmt)
            plan = plan_res.scalar_one_or_none()

            if plan:
                # Recalculate progress
                all_tasks_stmt = (
                    select(TrainingTask)
                    .join(TrainingDay, TrainingTask.day_id == TrainingDay.id)
                    .where(TrainingDay.plan_id == plan.id)
                )
                all_tasks_res = await db.execute(all_tasks_stmt)
                all_tasks = all_tasks_res.scalars().all()
                completed_count = sum(1 for t in all_tasks if t.status == "completed")
                progress = round((completed_count / len(all_tasks)) * 100.0, 1) if all_tasks else 0.0

                send_task_completed_notification(
                    user_email=user.email,
                    user_name=user.name,
                    task_title=task.title,
                    task_type=task.task_type,
                    estimated_minutes=task.estimated_minutes,
                    day_number=day.day_number,
                    day_objective=day.objective,
                    plan_title=plan.title,
                    overall_progress=progress,
                )
        except Exception as exc:
            logger.warning("Could not send task completion email: %s", exc)

    return task


async def reschedule_today_workload(
    db: AsyncSession,
    user: User,
    request: RescheduleDayRequest,
) -> dict[str, Any]:
    """Adjust today's schedule when user has limited availability, deferring excess to next day."""
    plan = await get_active_training_plan(db, user)
    if not plan:
        raise AppException("No active training plan found.", status_code=404)

    # Find today
    today = None
    for d in plan.days:
        if not d.is_completed:
            today = d
            break
    if not today:
        today = plan.days[0] if plan.days else None

    if not today:
        raise AppException("No training day available to reschedule.", status_code=400)

    available_mins = int(request.available_hours * 60)
    accumulated_mins = 0
    deferred_tasks: list[TrainingTask] = []

    # Sort tasks: prioritize in_progress or uncompleted tasks
    for t in sorted(today.tasks, key=lambda x: (x.status == "completed", x.order_index)):
        if t.status == "completed":
            accumulated_mins += t.estimated_minutes
            continue

        if accumulated_mins + t.estimated_minutes <= available_mins:
            accumulated_mins += t.estimated_minutes
        else:
            # Must defer this task to next day
            deferred_tasks.append(t)

    if deferred_tasks:
        next_day = next((d for d in plan.days if d.day_number == today.day_number + 1), None)
        if not next_day:
            # Create next day dynamically if at the end of plan
            next_day = TrainingDay(
                plan_id=plan.id,
                day_number=today.day_number + 1,
                phase_name=today.phase_name,
                objective=f"Continued Practice: {today.objective}",
                topics=today.topics,
                expected_outcome=today.expected_outcome,
                total_planned_minutes=0,
                is_completed=False,
            )
            db.add(next_day)
            await db.flush()

        for dt in deferred_tasks:
            dt.day_id = next_day.id
            dt.is_carried_over = True
            dt.original_day_number = today.day_number
            if dt in today.tasks:
                today.tasks.remove(dt)
            next_day.tasks.append(dt)

        today.total_planned_minutes = accumulated_mins
        await db.commit()

    return await get_daily_training_view(db, user, today.day_number)


async def submit_day_confidence_review(
    db: AsyncSession,
    user: User,
    day_id: int,
    request: DayReviewRequest,
) -> dict[str, Any]:
    """Submit confidence rating for a day and generate tailored AI review recommendations."""
    stmt = (
        select(TrainingDay)
        .join(TrainingPlan, TrainingDay.plan_id == TrainingPlan.id)
        .where(TrainingDay.id == day_id, TrainingPlan.user_id == user.id)
    )
    res = await db.execute(stmt)
    day = res.scalar_one_or_none()
    if not day:
        raise AppException("Training day not found.", status_code=404)

    day.confidence_rating = request.confidence_rating

    # Recommendation heuristic
    if request.confidence_rating <= 2:
        rec = (
            f"Confidence is low ({request.confidence_rating}/5). We strongly recommend scheduling an "
            f"extra 45–60 minutes reviewing core documentation, syntax, and exercises for {day.objective} "
            f"before advancing to the next milestone."
        )
    elif request.confidence_rating == 3:
        rec = (
            f"Moderate confidence ({request.confidence_rating}/5). Review any tricky areas in {day.objective} "
            f"and try writing 1–2 practical unit tests or exercises to solidify your understanding."
        )
    else:
        rec = (
            f"Outstanding mastery ({request.confidence_rating}/5)! You have demonstrated solid command over "
            f"{day.objective}. You are fully primed for the upcoming challenges."
        )

    day.ai_review_recommendation = rec
    await db.commit()
    await db.refresh(day)
    return {
        "day_id": day.id,
        "confidence_rating": day.confidence_rating,
        "ai_review_recommendation": rec,
    }


# =============================================================================
# 5. Personal Trainer Settings & n8n Webhook Integration
# =============================================================================

async def get_trainer_settings(db: AsyncSession, user: User) -> PersonalTrainerSettings:
    """Retrieve or create user-specific trainer and webhook notification settings."""
    stmt = select(PersonalTrainerSettings).where(PersonalTrainerSettings.user_id == user.id)
    res = await db.execute(stmt)
    settings_obj = res.scalar_one_or_none()
    if not settings_obj:
        settings_obj = PersonalTrainerSettings(
            user_id=user.id,
            notifications_enabled=False,
            preferred_time="09:00",
            notification_channel="email",
        )
        db.add(settings_obj)
        await db.commit()
        await db.refresh(settings_obj)
    return settings_obj


async def update_trainer_settings(
    db: AsyncSession,
    user: User,
    request: PersonalTrainerSettingsUpdateRequest,
) -> PersonalTrainerSettings:
    """Update user-specific trainer settings."""
    settings_obj = await get_trainer_settings(db, user)
    settings_obj.notifications_enabled = request.notifications_enabled
    settings_obj.preferred_time = request.preferred_time
    settings_obj.notification_channel = request.notification_channel
    await db.commit()
    await db.refresh(settings_obj)
    return settings_obj


async def trigger_n8n_daily_notification(
    db: AsyncSession,
    user: User,
) -> dict[str, Any]:
    """Trigger the external n8n notification workflow with real user training progress."""
    webhook_url = settings.N8N_WEBHOOK_URL.strip() if settings.N8N_WEBHOOK_URL else ""

    if not webhook_url:
        return {
            "success": False,
            "message": "Daily notifications are not configured yet. Please configure N8N_WEBHOOK_URL in .env.",
            "webhook_configured": False,
            "payload": None,
            "webhook_status_code": None,
        }

    # Fetch active plan and day view
    plan = await get_active_training_plan(db, user)
    if not plan:
        raise AppException("No active training plan to dispatch via n8n.", status_code=400)

    daily_data = await get_daily_training_view(db, user)
    curr_day: TrainingDay = daily_data["current_day"]

    payload = {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "goal": plan.title,
        "role": plan.target_role or "Candidate",
        "company": plan.target_company or "Target Company",
        "day_number": curr_day.day_number,
        "yesterday": daily_data["yesterday_summary"],
        "today": {
            "objective": curr_day.objective,
            "tasks": [
                {
                    "title": t.title,
                    "estimated_minutes": t.estimated_minutes,
                    "type": t.task_type,
                    "status": t.status,
                }
                for t in curr_day.tasks
            ],
        },
        "total_minutes": daily_data["workload_minutes"],
        "progress": plan.overall_progress,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code in (200, 201, 202, 204):
                return {
                    "success": True,
                    "message": f"Daily training notification dispatched to n8n successfully (status {response.status_code}).",
                    "webhook_configured": True,
                    "payload": payload,
                    "webhook_status_code": response.status_code,
                }
            else:
                return {
                    "success": False,
                    "message": f"n8n webhook returned status code {response.status_code}.",
                    "webhook_configured": True,
                    "payload": payload,
                    "webhook_status_code": response.status_code,
                }
    except Exception as exc:
        logger.error("Error triggering n8n webhook: %s", exc)
        return {
            "success": False,
            "message": f"Could not reach n8n webhook: {exc}",
            "webhook_configured": True,
            "payload": payload,
            "webhook_status_code": None,
        }
