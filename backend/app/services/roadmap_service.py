"""
Personalized Career Roadmap Service.
Uses Ollama AI to generate step-by-step learning roadmaps based on user profile,
resume analysis, and skill gaps, and tracks milestone progress.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.ai import get_ai_provider
from app.integrations.ai.base import AIProvider
from app.models.career import CareerGoal, Occupation, SkillGapReport
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapProgress
from app.models.user import User
from app.schemas.roadmap import (
    AIRoadmapItemPayload,
    AIRoadmapPromptPayload,
    RoadmapItemResponse,
    RoadmapResponse,
)

from app.services.career_service import (
    aggregate_user_skills,
    get_latest_user_skill_gap_report,
    get_occupation_by_id,
    search_occupations,
)
from app.services.profile_service import get_or_create_profile

logger = logging.getLogger(__name__)


ROADMAP_PROMPT_TEMPLATE = """You are an expert AI Technical Career Coach and Senior Engineering Mentor.
Generate a highly detailed, structured, and comprehensive career roadmap for a candidate pursuing the target role: '{target_role}'.

CANDIDATE CURRENT PROFILE & STATE:
- Current Target Role: {target_role}
- Existing Strong Skills: {current_skills_list}
- Identified Skill Gaps to Bridge: {missing_skills_list}

ROADMAP REQUIREMENTS — MUST BE VERY DETAILED AND ACTIONABLE:
1. Divide the learning journey into 5 distinct phases:
   - Phase 1: Core Prerequisites & Language Fundamentals (weeks 1-3)
   - Phase 2: Framework Mastery & Development Tools (weeks 4-7)
   - Phase 3: Database, APIs & Backend Architecture (weeks 8-11)
   - Phase 4: Advanced Concepts, Testing & DevOps (weeks 12-15)
   - Phase 5: Real-World Portfolio Projects & Interview Preparation (weeks 16-20)
2. Generate 1 high-impact comprehensive item for each phase (5 total milestone items).
3. Each item MUST include:
   - phase: Phase title (e.g. 'Phase 1: Core Prerequisites & Language Fundamentals')
   - skill: Specific skill/technology to master
   - topics: Array of 5-6 specific concepts to study with clear detail
   - projects: Array of 2 practical portfolio project ideas that demonstrate the skill
   - resources: Array of 3 trusted learning resource names
   - priority: 'High', 'Medium', or 'Low'
   - estimated_effort: Detailed estimated duration (e.g. '2-3 weeks (25-35 hours)')
4. Topics MUST be specific and actionable, NOT vague. Instead of 'Learn basics', write 'Variables, Data Types, Control Flow (if/elif/else), Loops (for/while), Functions & Lambda Expressions'.
5. Projects MUST be specific portfolio-worthy ideas, NOT generic. Instead of 'Build a project', write 'Build a REST API task manager with user authentication, CRUD endpoints, and PostgreSQL database'.

OUTPUT MUST BE VALID JSON ONLY matching this exact structure:
{{
  "title": "Comprehensive Roadmap: Path to {target_role}",
  "items": [
    {{
      "phase": "Phase 1: Core Prerequisites & Language Fundamentals",
      "skill": "Python Programming",
      "topics": ["Variables, Data Types & Type Casting", "Control Flow: if/elif/else, for/while loops", "Functions, Lambda Expressions & Closures", "List Comprehensions & Generator Expressions", "Object-Oriented Programming: Classes, Inheritance, Polymorphism", "Exception Handling with try/except/finally", "File I/O & Context Managers", "Virtual Environments & pip Package Management"],
      "projects": ["Build a CLI Task Manager with file-based storage", "Create a web scraper using BeautifulSoup/requests", "Develop a unit-tested calculator with pytest"],
      "resources": ["Official Python 3 Documentation & Tutorial", "freeCodeCamp Python Full Course (YouTube)", "Automate the Boring Stuff with Python (Free Book)", "Python Exercises on HackerRank"],
      "priority": "High",
      "estimated_effort": "2-3 weeks (25-35 hours)"
    }}
  ]
}}"""


def create_curated_roadmap_for_role(target_role: str, current_skills: str, missing_skills: str) -> AIRoadmapPromptPayload:
    """Construct a comprehensive 5-phase career roadmap with 12-15 detailed items tailored to the role."""
    r_lower = target_role.lower()

    if any(k in r_lower for k in ["data", "ai", "machine learning", "ml", "deep learning", "nlp"]):
        phase1_skill = "Python & Mathematical Foundations"
        phase1_topics = ["Python 3 Data Structures & Type Annotations", "NumPy Vectorized Arrays & Matrix Algebra", "Pandas DataFrames, Filtering & GroupBy Aggregations", "Linear Algebra & Calculus for Machine Learning", "Probability, Statistics & Hypothesis Testing"]
        phase1_projects = ["Exploratory Data Analysis (EDA) on Real-World Dataset", "Automated Financial Statement Analyzer"]
        phase1_resources = ["Python for Data Analysis (O'Reilly)", "Kaggle Micro-Courses", "3Blue1Brown Essence of Linear Algebra"]

        phase2_skill = "Machine Learning & Scikit-Learn"
        phase2_topics = ["Supervised Learning (Regression, Classification, Decision Trees)", "Unsupervised Learning (K-Means, PCA Dimensionality Reduction)", "Feature Engineering, Scaling & Encoding", "Cross-Validation & Hyperparameter Tuning (GridSearchCV)", "Model Evaluation Metrics (ROC-AUC, F1-Score, Confusion Matrix)"]
        phase2_projects = ["Customer Churn Prediction Model with Scikit-Learn", "Housing Price Regression with Feature Pipeline"]
        phase2_resources = ["Scikit-Learn Official User Guide", "Hands-On Machine Learning (Aurélien Géron)", "StatQuest with Josh Starmer"]

        phase3_skill = "Deep Learning & Neural Architectures"
        phase3_topics = ["PyTorch Tensors, Autograd & Custom Modules", "Convolutional Neural Networks (CNNs) for Computer Vision", "Recurrent Networks (RNN, LSTM, GRU) for Sequence Data", "Transformers Architecture & Self-Attention Mechanisms", "Transfer Learning with Hugging Face Pretrained Models"]
        phase3_projects = ["Image Classification System with Transfer Learning in PyTorch", "Sentiment Analysis & Text Classifier with Hugging Face Transformers"]
        phase3_resources = ["PyTorch Official Deep Learning Tutorials", "Hugging Face NLP Course", "DeepLearning.AI Specialization"]

        phase4_skill = "Data Engineering, SQL & Vector DBs"
        phase4_topics = ["Advanced SQL (Window Functions, CTEs, Indexing)", "Vector Databases (Pinecone, ChromaDB, Qdrant)", "Retrieval-Augmented Generation (RAG) Architectures", "Apache Spark & Distributed Data Processing Basics", "FastAPI Serving for ML Model APIs"]
        phase4_projects = ["Production RAG Knowledge Assistant with Vector Search", "Scalable Batch Inference Pipeline with SQL Database"]
        phase4_resources = ["Pinecone RAG Architectural Guide", "PostgreSQL Tutorial for Data Engineers", "Full Stack LLM BootCamp"]

        phase5_skill = "MLOps, Deployment & AI Portfolio"
        phase5_topics = ["Docker Containerization for ML Services", "Model Tracking & Versioning with MLflow/Weights & Biases", "CI/CD for Machine Learning (CML / GitHub Actions)", "Latency & Throughput Optimization (ONNX, Quantization)", "End-to-End Portfolio Demonstration & Technical Presentation"]
        phase5_projects = ["End-to-End Production ML Application Deployed on Cloud with CI/CD", "Interactive Streamlit / Gradio Showcase for Portfolio"]
        phase5_resources = ["Made With ML MLOps Course", "Docker for Data Science Guide", "NeetCode DSA & ML Interview Practice"]

    elif any(k in r_lower for k in ["frontend", "react", "vue", "angular", "ui", "web"]):
        phase1_skill = "Modern JavaScript & TypeScript Mastery"
        phase1_topics = ["ES6+ Features (Destructuring, Spread, Optional Chaining, Modules)", "Async/Await, Promises & Event Loop Mechanics", "TypeScript Core (Generics, Unions, Utility Types, Type Narrowing)", "DOM Manipulation & Browser Storage APIs (LocalStorage, IndexedDB)", "CSS Flexbox, Grid, Responsive Design & Tailwind CSS"]
        phase1_projects = ["Interactive Dashboard Component with Vanilla TypeScript", "Accessible Component Library with Tailwind CSS"]
        phase1_resources = ["javascript.info Interactive Guide", "TypeScript Official Handbook", "Frontend Masters JavaScript Deep Dive"]

        phase2_skill = "React 18/19 & State Architecture"
        phase2_topics = ["React Component Lifecycle & Custom Hooks", "State Management (Zustand, Redux Toolkit, React Query/TanStack)", "React Router DOM v6 Navigation & Protected Routes", "Forms Validation with React Hook Form & Zod", "Performance Optimization (useMemo, useCallback, Code Splitting)"]
        phase2_projects = ["E-Commerce Web Application with Cart, Filtering, and Checkout", "Kanban Task Management App with Drag & Drop"]
        phase2_resources = ["React.dev Official Documentation", "Epic React by Kent C. Dodds", "freeCodeCamp React Course"]

        phase3_skill = "API Integration & Real-time Web"
        phase3_topics = ["RESTful API Integration with Axios & Fetch", "WebSocket / Server-Sent Events (SSE) Real-Time Data", "Authentication Flow (JWT, Refresh Tokens, OAuth2)", "Optimistic UI Updates & Cache Invalidation", "Error Boundaries & Offline Capability"]
        phase3_projects = ["Real-Time Collaborative Chat App with WebSockets", "Live Crypto & Stock Market Tracker with Interactive Charts"]
        phase3_resources = ["TanStack Query Documentation", "MDN Web Docs WebSocket API", "Web.dev Performance Guides"]

        phase4_skill = "Testing, Next.js & Build Tooling"
        phase4_topics = ["Next.js App Router (Server Components vs Client Components)", "Server-Side Rendering (SSR) & Static Site Generation (SSG)", "Vite / Webpack Build Configuration & Bundle Analysis", "Unit Testing with Vitest & React Testing Library", "End-to-End Testing with Playwright / Cypress"]
        phase4_projects = ["Full-Featured Next.js 14 SaaS Product Landing & Dashboard", "Automated Playwright Test Suite for E-Commerce App"]
        phase4_resources = ["Next.js Official Learn Course", "Testing Library Guides", "Playwright Documentation"]

        phase5_skill = "Performance Optimization & Frontend Interview Prep"
        phase5_topics = ["Core Web Vitals Optimization (LCP, FID/INP, CLS)", "Web Accessibility (WCAG 2.1 AA Compliance, ARIA Roles)", "Micro-Frontend Architectures & Design Systems", "Frontend System Design (Virtualization, Infinite Scroll, Caching)", "Mock Technical Coding & Behavioral Interview Mastery"]
        phase5_projects = ["High-Performance Portfolio Site with 100/100 Lighthouse Score", "Production Ready Component Design System with Storybook"]
        phase5_resources = ["GreatFrontEnd System Design", "Frontend Interview Handbook", "WebPageTest Performance Audits"]

    elif any(k in r_lower for k in ["devops", "cloud", "sre", "infrastructure", "kubernetes", "security"]):
        phase1_skill = "Linux, Networking & Shell Scripting"
        phase1_topics = ["Linux System Administration & User/Permission Management", "Bash / Shell Scripting & Automated Cron Jobs", "Networking Fundamentals (TCP/IP, DNS, SSL/TLS, HTTP/HTTPS, SSH)", "Process Management, Systemd & Log Analysis (journalctl)", "Git Version Control & Branching Workflows"]
        phase1_projects = ["Automated Server Health Monitoring & Alerting Bash Script", "Secure Multi-User Linux Bastion Server Configuration"]
        phase1_resources = ["Linux Journey Interactive Guide", "OverTheWire Bandit Challenges", "ExplainShell Command Guide"]

        phase2_skill = "Docker & Containerization"
        phase2_topics = ["Dockerfiles, Multi-Stage Builds & Image Optimization", "Docker Compose Multi-Container Orchestration", "Container Networking, Volume Persistence & Healthchecks", "Container Security & Vulnerability Scanning (Trivy)", "Rootless Containers & Best Practices"]
        phase2_projects = ["Containerized 3-Tier Application with Microservices & Database", "Production Multi-Stage Dockerfile for Python/Node Apps"]
        phase2_resources = ["Docker Official Guides & Reference", "Bret Fisher Docker Mastery", "Dive Image Exploration Tool"]

        phase3_skill = "Kubernetes Orchestration"
        phase3_topics = ["Kubernetes Architecture (Control Plane, Worker Nodes, Kubelet)", "Pods, Deployments, ReplicaSets & StatefulSets", "Services (ClusterIP, NodePort, LoadBalancer) & Ingress Controllers", "ConfigMaps, Secrets Management & RBAC Permissions", "Helm Charts Packaging & Deployment Automation"]
        phase3_projects = ["Self-Healing Kubernetes Cluster Deployment with Helm", "Ingress Controller with Automatic SSL via Let's Encrypt"]
        phase3_resources = ["Kubernetes.io Interactive Tutorials", "KodeKloud CKA Training", "Mumshad Mannambeth Kubernetes Labs"]

        phase4_skill = "Infrastructure as Code (Terraform) & Cloud (AWS/Azure)"
        phase4_topics = ["Terraform State Management, Modules & Providers", "AWS Core Services (VPC, EC2, S3, RDS, IAM, CloudWatch)", "CI/CD Pipelines (GitHub Actions / GitLab CI)", "Secrets Management with HashiCorp Vault or AWS Secrets Manager", "GitOps Workflow with ArgoCD"]
        phase4_projects = ["Multi-Environment AWS Infrastructure Provisioned via Terraform", "Automated Zero-Downtime CI/CD Pipeline to Kubernetes"]
        phase4_resources = ["Terraform Associate Official Guide", "AWS Skill Builder Free Labs", "ArgoCD Getting Started"]

        phase5_skill = "Observability, SRE Practices & Interview Prep"
        phase5_topics = ["Prometheus Metrics Scraping & AlertManager", "Grafana Visualization Dashboards for System Metrics", "Distributed Tracing with OpenTelemetry & Jaeger", "SRE Fundamentals (SLIs, SLOs, Error Budgets, Incident Response)", "DevOps Scenario System Design Interviews"]
        phase5_projects = ["Enterprise Observability Suite (Prometheus + Grafana + Loki)", "Disaster Recovery & Automated Chaos Engineering Drill"]
        phase5_resources = ["Google SRE Books (Free Online)", "Brendan Gregg Systems Performance", "DevOps Interview Prep Roadmap"]

    else:
        # Software Engineer / Backend Engineer / Full Stack
        phase1_skill = "Core Programming & Data Structures"
        phase1_topics = ["Language Fundamentals (Python / Java / TypeScript)", "Object-Oriented Programming (OOP), SOLID Principles & Clean Code", "Core Data Structures (Arrays, HashMaps, Linked Lists, Trees, Stacks, Queues)", "Algorithm Complexity (Big-O Time & Space Analysis)", "Unit Testing Frameworks & Git Collaboration"]
        phase1_projects = ["In-Memory Key-Value Store with TTL & Serialization", "CLI Task Automation Tool with Pytest / Jest Suite"]
        phase1_resources = ["Official Language Documentation & Specifications", "NeetCode 150 Problem Patterns", "Clean Code (Robert C. Martin)"]

        phase2_skill = "Web Frameworks & API Architecture"
        phase2_topics = ["RESTful API Design & HTTP Status Codes", "FastAPI / Node.js Express Architecture & Routing", "Pydantic / Zod Data Validation & Serialization", "Authentication & Authorization (JWT, Session Cookies, OAuth2)", "Asynchronous Programming (AsyncIO, Event Loop, Coroutines)"]
        phase2_projects = ["Full RESTful CRUD API with Auth, Rate Limiting & OpenAPI Docs", "Multi-Tenant Task Management Backend Service"]
        phase2_resources = ["FastAPI Official Tutorial & User Guide", "MDN HTTP & REST Reference", "Real Python Backend Guides"]

        phase3_skill = "Databases & Data Modeling"
        phase3_topics = ["Relational Databases (PostgreSQL / MySQL Schema Design)", "SQL Query Optimization (EXPLAIN ANALYZE, B-Tree Indexes)", "SQLAlchemy 2.0 / Prisma ORM & Database Migrations (Alembic)", "ACID Transactions, Isolation Levels & Connection Pooling", "Caching Strategies with Redis (Read-Through, Cache-Aside)"]
        phase3_projects = ["E-Commerce Schema with Inventory Transactions & Optimistic Locking", "High-Throughput Analytics Service with Redis Caching"]
        phase3_resources = ["PostgreSQL Official Documentation", "Use The Index, Luke (Database Performance Guide)", "Redis University Free Courses"]

        phase4_skill = "System Design & Cloud Architecture"
        phase4_topics = ["Microservices vs Monolithic Architectural Trade-offs", "Message Queues & Asynchronous Workers (Celery, Kafka, RabbitMQ)", "Containerization with Docker & Multi-Container Docker Compose", "Cloud Infrastructure (AWS S3, EC2, RDS, IAM)", "CI/CD Automated Deployment Pipelines with GitHub Actions"]
        phase4_projects = ["Distributed Event-Driven Order Processing System with RabbitMQ", "Containerized Full-Stack Application Deployed on Cloud with CI/CD"]
        phase4_resources = ["System Design Primer (Donne Martin on GitHub)", "Designing Data-Intensive Applications (Martin Kleppmann)", "ByteByteGo System Design Newsletter"]

        phase5_skill = "Production Readiness & Technical Interview Prep"
        phase5_topics = ["API Security (CORS, CSRF, SQL Injection, Rate Limiting)", "Application Telemetry, Logging & Healthcheck Monitoring", "LeetCode Medium / Hard Coding Patterns (Two Pointers, DP, Graphs)", "Behavioral Interview Mastery using STAR Framework", "System Design Interview Simulation & Whiteboarding"]
        phase5_projects = ["Production-Grade Enterprise SaaS Application with Complete Test Coverage", "Interactive Resume & Portfolio Technical Showcase"]
        phase5_resources = ["Tech Interview Handbook (Yangshun Tay)", "Grokking the System Design Interview", "Cracking the Coding Interview"]

    items = [
        AIRoadmapItemPayload(
            phase="Phase 1: Core Prerequisites & Language Fundamentals (Weeks 1-3)",
            skill=phase1_skill,
            topics=phase1_topics,
            projects=phase1_projects,
            resources=phase1_resources,
            priority="High",
            estimated_effort="3 weeks (25-35 hours)",
        ),
        AIRoadmapItemPayload(
            phase="Phase 2: Framework Mastery & Development Tools (Weeks 4-7)",
            skill=phase2_skill,
            topics=phase2_topics,
            projects=phase2_projects,
            resources=phase2_resources,
            priority="High",
            estimated_effort="4 weeks (30-40 hours)",
        ),
        AIRoadmapItemPayload(
            phase="Phase 3: Database, APIs & Backend Architecture (Weeks 8-11)",
            skill=phase3_skill,
            topics=phase3_topics,
            projects=phase3_projects,
            resources=phase3_resources,
            priority="High",
            estimated_effort="4 weeks (30-40 hours)",
        ),
        AIRoadmapItemPayload(
            phase="Phase 4: Advanced Concepts, Testing & DevOps (Weeks 12-15)",
            skill=phase4_skill,
            topics=phase4_topics,
            projects=phase4_projects,
            resources=phase4_resources,
            priority="Medium",
            estimated_effort="4 weeks (25-35 hours)",
        ),
        AIRoadmapItemPayload(
            phase="Phase 5: Real-World Portfolio Projects & Interview Preparation (Weeks 16-20)",
            skill=phase5_skill,
            topics=phase5_topics,
            projects=phase5_projects,
            resources=phase5_resources,
            priority="High",
            estimated_effort="5 weeks (35-45 hours)",
        ),
    ]

    return AIRoadmapPromptPayload(
        title=f"Detailed Roadmap: Path to {target_role}",
        items=items,
    )


async def resolve_target_occupation(
    db: AsyncSession, user: User, occupation_id: int | None = None
) -> Occupation | None:
    """Resolve target occupation for roadmap generation."""
    if occupation_id is not None:
        try:
            return await get_occupation_by_id(db, occupation_id)
        except Exception:
            pass

    # Check active career goal
    try:
        goal_query = select(CareerGoal).where(CareerGoal.user_id == user.id, CareerGoal.is_active == True)
        goal_res = await db.execute(goal_query)
        goal = goal_res.scalar_one_or_none()
        if goal and goal.occupation:
            return goal.occupation
    except Exception:
        pass

    # Check profile target_role
    try:
        profile = await get_or_create_profile(db, user.id)
        if profile.target_role:
            occs = await search_occupations(db, query=profile.target_role, limit=1)
            if occs:
                return occs[0]
    except Exception:
        pass

    # Default to first occupation (Software Developers)
    try:
        occs = await search_occupations(db, query="", limit=1)
        if occs:
            return occs[0]
    except Exception:
        pass

    return None


async def generate_user_roadmap(
    db: AsyncSession,
    user: User,
    occupation_id: int | None = None,
    custom_query: str | None = None,
    ai_provider: AIProvider | None = None,
) -> RoadmapResponse:
    """Generate personalized career roadmap using Ollama AI and user state or custom search prompt."""
    if custom_query and custom_query.strip():
        target_role_title = custom_query.strip()
        occupation = None
        if occupation_id is not None:
            try:
                occupation = await get_occupation_by_id(db, occupation_id)
            except Exception:
                pass
    else:
        occupation = await resolve_target_occupation(db, user, occupation_id)
        if occupation:
            target_role_title = occupation.title
        else:
            profile = await get_or_create_profile(db, user.id)
            target_role_title = profile.target_role if profile and profile.target_role else "Software Engineer"

    user_skills = await aggregate_user_skills(db, user.id)

    # Get latest skill gap report if available
    missing_skills_names: list[str] = []
    if occupation:
        try:
            report = await get_latest_user_skill_gap_report(db, user_id=user.id)
            if report and report.occupation_id == occupation.id:
                missing_skills_names = [m["name"] for m in report.missing_skills]
        except Exception:
            pass

        if not missing_skills_names and occupation.skills:
            missing_skills_names = [
                os.skill.name for os in occupation.skills if os.skill.name.lower() not in user_skills
            ]

    current_skills_str = ", ".join(list(user_skills)[:10]) or "General Programming"
    missing_skills_str = ", ".join(missing_skills_names[:10]) or f"Core competencies for {target_role_title}"

    provider = ai_provider or get_ai_provider()
    prompt = ROADMAP_PROMPT_TEMPLATE.format(
        target_role=target_role_title,
        current_skills_list=current_skills_str,
        missing_skills_list=missing_skills_str,
    )

    payload = None
    try:
        raw_response = await asyncio.wait_for(
            provider.generate(
                prompt,
                format="json",
                options={"num_predict": 1200, "num_ctx": 4096, "temperature": 0.2},
            ),
            timeout=90.0,
        )
        from app.integrations.ai.json_utils import extract_and_parse_json
        parsed = extract_and_parse_json(raw_response)
        if isinstance(parsed, dict) and "items" in parsed and isinstance(parsed["items"], list) and len(parsed["items"]) > 0:
            valid_items = []
            for it in parsed["items"]:
                if isinstance(it, dict) and it.get("phase") and it.get("skill"):
                    valid_items.append(AIRoadmapItemPayload.model_validate(it))
            if valid_items:
                payload = AIRoadmapPromptPayload(
                    title=parsed.get("title", f"Detailed Roadmap: Path to {target_role_title}"),
                    items=valid_items,
                )
    except ConnectionError as exc:
        logger.warning("Ollama connection failed during roadmap generation: %s", exc)
        raise AppException(
            message="AI Service (Ollama) is currently unavailable. Please ensure Ollama is running.",
            status_code=503,
        ) from exc
    except asyncio.TimeoutError as exc:
        logger.warning("Ollama roadmap call timed out, delivering curated high-speed roadmap: %s", exc)
    except Exception as exc:
        logger.warning("Ollama roadmap generation had an issue, creating curated structured roadmap: %s", exc)

    if not payload or not payload.items:
        # Generate rich structured multi-phase curriculum based on target role
        payload = create_curated_roadmap_for_role(target_role_title, current_skills_str, missing_skills_str)

    # Deactivate prior active roadmaps
    await db.execute(
        update(Roadmap)
        .where(Roadmap.user_id == user.id, Roadmap.is_active == True)
        .values(is_active=False)
    )

    roadmap = Roadmap(
        user_id=user.id,
        occupation_id=occupation.id if occupation else None,
        title=payload.title or f"Roadmap: Path to {target_role_title}",
        target_role=target_role_title,
        overall_progress=0.0,
        is_active=True,
    )
    db.add(roadmap)
    await db.flush()

    for item_data in payload.items:
        item = RoadmapItem(
            roadmap_id=roadmap.id,
            phase=item_data.phase,
            skill=item_data.skill,
            topics=item_data.topics,
            projects=item_data.projects,
            resources=item_data.resources,
            priority=item_data.priority,
            estimated_effort=item_data.estimated_effort,
            is_completed=False,
        )
        db.add(item)

    await db.commit()

    return await get_user_latest_roadmap(db, user_id=user.id)


async def get_user_latest_roadmap(db: AsyncSession, user_id: int) -> RoadmapResponse:
    """Retrieve active career roadmap for user with recalculated progress and skills summary."""
    query = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True).order_by(Roadmap.created_at.desc())
    res = await db.execute(query)
    roadmap = res.scalars().first()

    if not roadmap:
        raise AppException(
            message="No active career roadmap found. Please generate a roadmap first.",
            status_code=404,
        )

    # Recalculate progress
    total_items = len(roadmap.items) if roadmap.items else 0
    completed_items = sum(1 for item in (roadmap.items or []) if item.is_completed)
    progress_pct = round((completed_items / total_items * 100), 1) if total_items > 0 else 0.0

    if roadmap.overall_progress != progress_pct:
        roadmap.overall_progress = progress_pct
        await db.commit()
        await db.refresh(roadmap)

    user_skills = await aggregate_user_skills(db, user_id)

    missing_skills_names: list[str] = []
    if roadmap.occupation_id:
        try:
            report = await get_latest_user_skill_gap_report(db, user_id=user_id)
            if report and report.occupation_id == roadmap.occupation_id:
                missing_skills_names = [m["name"] for m in report.missing_skills]
        except Exception:
            pass

    item_responses = [RoadmapItemResponse.model_validate(it) for it in (roadmap.items or [])]

    return RoadmapResponse(
        id=roadmap.id,
        user_id=roadmap.user_id,
        occupation_id=roadmap.occupation_id,
        title=roadmap.title,
        target_role=roadmap.target_role,
        overall_progress=roadmap.overall_progress,
        is_active=roadmap.is_active,
        items=item_responses,
        current_skills=list(user_skills)[:10],
        missing_skills=missing_skills_names[:10],
        created_at=roadmap.created_at,
        updated_at=roadmap.updated_at,
    )


async def toggle_roadmap_item_completion(
    db: AsyncSession, user: User, item_id: int, is_completed: bool
) -> RoadmapResponse:
    """Toggle item completion status and update roadmap overall progress percentage."""
    item_query = select(RoadmapItem).where(RoadmapItem.id == item_id)
    res = await db.execute(item_query)
    item = res.scalar_one_or_none()

    if not item or item.roadmap.user_id != user.id:
        raise AppException(message="Roadmap item not found or unauthorized.", status_code=404)

    item.is_completed = is_completed
    item.completed_at = datetime.now(timezone.utc) if is_completed else None

    # Save progress log entry
    progress_log = RoadmapProgress(
        roadmap_item_id=item.id,
        user_id=user.id,
        status="completed" if is_completed else "not_started",
    )
    db.add(progress_log)
    await db.commit()

    return await get_user_latest_roadmap(db, user_id=user.id)
