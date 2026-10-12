# 🚀 Placement AI — AI Career, Resume & Interview Coaching Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-8.2-646CFF.svg?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0_Async-D71F00.svg?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)
[![Ollama](https://img.shields.io/badge/Ollama-Offline_AI-black.svg?style=flat&logo=ollama&logoColor=white)](https://ollama.ai)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Pytest](https://img.shields.io/badge/Pytest-121_Passed-brightgreen.svg?style=flat&logo=pytest&logoColor=white)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)](LICENSE)

An enterprise-grade, offline-first **AI Career Acceleration, Resume Studio, Job Market Intelligence, Mock Interview, and Placement Readiness Platform**. Engineered with **FastAPI**, **React 19**, **TypeScript**, **SQLAlchemy 2.0 Async**, and local **Ollama LLM** inference for zero cloud costs, absolute privacy, and mathematically grounded evaluation.

---

## 📑 Table of Contents

1. [🌟 Executive Overview](#-executive-overview)
2. [📐 Architectural Principles](#-architectural-principles)
3. [🏗️ System Architecture & Data Flow](#️-system-architecture--data-flow)
4. [🧮 Mathematical Models & Core Algorithms](#-mathematical-models--core-algorithms)
5. [✨ Complete Feature Modules](#-complete-feature-modules)
6. [🛠️ Technology Stack & Dependencies](#️-technology-stack--dependencies)
7. [📊 Relational Data Topology](#-relational-data-topology)
8. [⚡ Quick Start & Execution Guide](#-quick-start--execution-guide)
9. [🔐 Environment Variables Specification](#-environment-variables-specification)
10. [🌐 Comprehensive API Directory](#-comprehensive-api-directory)
11. [🧪 Quality Assurance & Test Verification](#-quality-assurance--test-verification)
12. [🔒 Security, Sandboxing & Row-Level Isolation](#-security-sandboxing--row-level-isolation)
13. [📧 Automated Scheduler & SMTP Dispatch](#-automated-scheduler--smtp-dispatch)
14. [📜 License & Citation](#-license--citation)

---

## 🌟 Executive Overview

In modern technical recruiting, candidates confront severe structural hurdles:
- **Opaque Applicant Tracking Systems (ATS):** Black-box automated parsers reject qualified resumes without actionable diagnostics.
- **Abstract Career Roadmaps:** Generic curricula fail to target candidate-specific skill deficits.
- **Prohibitive Mock Interview Costs:** Human interview coaching is expensive, subjective, and lacks reproducible quantitative scoring.
- **Execution Friction:** Candidates struggle to decompose career goals into structured, daily micro-workloads.

**Placement AI** resolves these challenges by uniting **deterministic mathematical scoring** with **private, offline AI narration**:
- **Zero-Hallucination Metrics:** All evaluation scores (ATS, readiness, skill match, interview rubrics) are calculated using auditable mathematical formulas. The LLM is strictly utilized for pedagogical feedback, entity extraction, and prose narration.
- **100% Offline & Privacy-Preserving:** Powered by locally hosted **Ollama** runtimes (`llama3.2:3b`, `llama3`, `mistral`). Sensitive candidate resumes, interview transcripts, and code submissions never leave the local environment.
- **Resilient Fallback Heuristics:** Built-in semantic fallbacks ensure that all modules continue functioning seamlessly even when the local LLM is temporarily unavailable or uninstalled.

---

## 📐 Architectural Principles

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           CORE SYSTEM TENETS                           │
  ├────────────────────────────────────────────────────────────────────────┤
  │ 1. Deterministic Math + AI Narration                                   │
  │    Scores are computed via transparent linear combinations; LLMs only  │
  │    narrate insights and extract structured entities.                   │
  │                                                                        │
  │ 2. Air-Gapped Local Intelligence                                       │
  │    Zero external API token charges; zero external data leakage.        │
  │                                                                        │
  │ 3. Universal Graceful Degradation                                      │
  │    Every generative service features deterministic fallback pipelines. │
  │                                                                        │
  │ 4. Strict Row-Level Multi-Tenancy                                      │
  │    Every query enforces `user_id` scoping with cascading lifecycle     │
  │    management.                                                         │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ System Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT BROWSER (Vite + React 19)                          │
│   • Tailwind CSS v3 UI Architecture          • Web Speech API (TTS & STT Engine)    │
│   • React Router v7 SPA Routing              • Type-Safe Fetch Client (api.ts)      │
│   • Interactive Voice Mock Interview         • In-App Notification Tray & Drawer    │
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           │ HTTP REST / JSON (Bearer JWT)
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI ASYNCHRONOUS BACKEND (Uvicorn)                    │
│   • 22 Modular Version 1 Routers             • HTTPBearer JWT Authentication Guard  │
│   • Global AppException Handlers             • CORS RegEx Middleware                │
├──────────────────────────────────────────┬──────────────────────────────────────────┤
│             BUSINESS SERVICES            │           INFRASTRUCTURE & WORKERS       │
│   • ATS Resume Scoring Engine            │   • Ollama Local LLM Client (HTTPX Pool) │
│   • O*NET Skill Gap Analyzer             │   • Response LRU + TTL In-Memory Cache   │
│   • Dynamic Placement Readiness Index    │   • Robust JSON Auto-Repair State Engine │
│   • Subprocess Sandbox Code Executor     │   • APScheduler Asynchronous Cron Engine │
│   • Adaptive Personal Trainer Scheduler  │   • Adzuna Live Job Provider Gateway     │
│   • 6-Vector Mock Interview Evaluator    │   • aiosmtplib Non-Blocking Dispatcher   │
└────────────────────┬─────────────────────┴────────────────────┬─────────────────────┘
                     │ Async SQLAlchemy 2.0                     │ Local HTTP (:11434)
                     ▼                                          ▼
┌──────────────────────────────────────────┐ ┌────────────────────────────────────────┐
│            DATABASE LAYER                │ │         LOCAL OLLAMA RUNTIME           │
│   • SQLite (career_coach.db)             │ │   • Model: llama3.2:3b / llama3        │
│   • PostgreSQL 16 (Production Docker)    │ │   • Background VRAM Keep-Alive (60m)   │
│   • 39 Relational Tables (JSONB / JSON)  │ │   • Zero Cloud Egress & Zero Latency   │
└──────────────────────────────────────────┘ └────────────────────────────────────────┘
```

---

## 🧮 Mathematical Models & Core Algorithms

### 1. ATS Resume Linear Scoring Algorithm
To prevent arbitrary LLM scoring, the Applicant Tracking System (ATS) evaluation decomposes resume quality into 5 weighted rubric dimensions:

$$\text{ATS Score} = \sum_{i=1}^{5} w_i \cdot s_i$$

$$\text{ATS Score} = \text{round}\Big(\min\big(100.0, \max(0.0, 0.20 s_{\text{struct}} + 0.30 s_{\text{skills}} + 0.25 s_{\text{exp}} + 0.15 s_{\text{edu}} + 0.10 s_{\text{format}})\big), 1\Big)$$

- **Structure ($20\%$):** Standard headings, contact information, completeness.
- **Skills Match ($30\%$):** Density and diversity of technical tools and keywords.
- **Experience Impact ($25\%$):** Action verbs and measurable business results.
- **Education ($15\%$):** Degree relevance, institutions, and certifications.
- **Formatting ($10\%$):** Readability, layout parseability, typographic clarity.
- **Quantification Heuristic:** The engine performs a deterministic regular expression scan for metric indicators (`%`, `increased`, `reduced`, `saved`). If absent, specific corrective recommendations are injected.

---

### 2. O*NET Skill Gap & Overlap Ratio Algorithm
Given target occupation $O$ with required skills $K_O$ and candidate skill union $U = \text{ProfileSkills} \cup \text{ResumeSkills} \cup \text{UserSkills}$:
1. For each required skill $k \in K_O$ with O*NET importance metric $I(k) \in [0, 100]$:
   - If matched in candidate pool $U$:
     - $I(k) \ge 85 \implies k \in \text{Strong Skills}$
     - $I(k) < 85 \implies k \in \text{Intermediate Skills}$
   - If not matched:
     - $k \in \text{Missing Skills}$ with priority classification:
       $$\text{Priority}(k) = \begin{cases} \text{High}, & I(k) \ge 88 \\ \text{Medium}, & 80 \le I(k) < 88 \\ \text{Low}, & I(k) < 80 \end{cases}$$
2. **Deterministic Match Percentage:**
   $$\text{Match Percentage} = \frac{|\text{Strong}| \cdot 1.0 + |\text{Intermediate}| \cdot 0.6}{|K_O|} \times 100$$

---

### 3. Dynamic Multi-Attribute Placement Readiness Metric
Quantifies overall employability using a Multi-Attribute Utility function with dynamic weight renormalization for missing user data:

$$\text{Readiness Index} = \sum_{k \in \text{Available}} W_{\text{effective}, k} \cdot S_k \qquad \text{where} \qquad W_{\text{effective}, k} = \frac{W_{\text{raw}, k}}{\sum_{j \in \text{Available}} W_{\text{raw}, j}}$$

- **Component Weights:** Resume ATS ($25\%$), Skill Gap Match ($25\%$), Mock Interview Score ($35\%$), Coding Practice ($15\%$).
- **Classification Thresholds:**
  $$\text{Status Band} = \begin{cases} \text{Job Ready}, & \text{Index} \ge 80.0 \\ \text{Nearly Ready}, & 65.0 \le \text{Index} < 80.0 \\ \text{Needs Preparation}, & \text{Index} < 65.0 \end{cases}$$

---

### 4. Mock Interview 6-Dimensional Rubric Evaluation
Interview answers are scored across 6 objective evaluation vectors (clamped $0–100$):
1. **Technical Correctness ($s_1$):** Accuracy of architectural concepts and algorithmic complexity.
2. **Relevance ($s_2$):** Direct alignment with the interviewer prompt.
3. **Completeness ($s_3$):** Consideration of edge cases, trade-offs, and boundary constraints.
4. **Communication ($s_4$):** Professional technical vocabulary and absence of filler hesitation.
5. **Structure ($s_5$):** Problem decomposition or adherence to the STAR methodology.
6. **Clarity ($s_6$):** Conciseness and conceptual delivery.

$$\text{Turn Score} = \frac{1}{6} \sum_{i=1}^{6} s_i \qquad \text{Session Score} = \frac{1}{N} \sum_{j=1}^{N} \text{TurnScore}_j$$

---

### 5. Server-Side Isolated Code Execution Sandbox
Candidate code execution operates in a multi-tier server-side sandbox (`services/code_executor.py`):
1. **Syntax Pre-Validation:** Static `ast.parse` validates Python syntax in $< 1\text{ms}$.
2. **Subprocess Isolation:** Executed via `sys.executable -I -S` (`-I` isolates environment paths; `-S` suppresses default site initialization).
3. **Watchdog Timer:** Hardware watchdog enforces a strict **3.0-second** execution deadline.
4. **Output Verification:** Normalized comparison against test cases supporting deep JSON equivalence and whitespace-agnostic string matching.
5. **SQL Isolation:** SQL queries execute against transient in-memory `:memory:` SQLite instances that are initialized and destroyed per test case.

---

### 6. Adaptive Workload Scheduling & Rollover Algorithm
1. **Capacity Scaling:** Daily planned minutes are strictly capped to candidate capacity:
   $$\text{Minutes}_t = \max\Big(15, \text{round}\big(\text{OriginalMinutes}_t \cdot \frac{\text{DailyHours} \times 60}{\text{TotalPlannedMinutes}}\big)\Big)$$
2. **Streak-Preserving Rollover:** Any unfinished tasks from yesterday are automatically transitioned to `rescheduled`, cloned into today's view as `(Carried Over)`, and flagged with `is_carried_over = True`.
3. **Greedy Rescheduling Knapsack:** Given dynamic available hours $H_{\text{avail}}$, tasks are allocated greedily until capacity is reached, while excess tasks are deferred to the following day.

---

### 7. State-Machine LLM JSON Extraction & Syntax Repair
To handle malformed LLM outputs, `json_utils.py` uses a state-machine parser:
- Strips markdown code block fences (```` ```json ````).
- Scans characters with a bracket stack while tracking quotation and backslash escape states.
- Auto-closes open string quotations and missing closing brackets (`}`, `]`) on truncated outputs.
- Regex removes illegal trailing commas before brackets (`re.sub(r",\s*([\}\]])", r"\1", text)`).
- Normalizes Python literals (`True` $\to$ `true`, `False` $\to$ `false`, `None` $\to$ `null`).

---

## ✨ Complete Feature Modules

| # | Module | Route | Technical Implementation & Capability |
|---|---|---|---|
| **1** | **User Authentication & Profiles** | `/login`, `/register`, `/profile` | Passlib salted bcrypt hashing; HS256 stateless JWT tokens; 10-point profile completion index. |
| **2** | **Executive Dashboard** | `/dashboard` | Aggregated user readiness overview; chronological activity stream; quick-action navigation cards. |
| **3** | **Resume Studio** | `/resumes` | Binary file parsing (PyMuPDF for PDF, python-docx for DOCX); version tree; set-diff comparisons. |
| **4** | **Transparent ATS Analyzer** | `/resume-analysis/:id` | 5-part weighted linear rubric; heuristic metric validator; actionable keyword gap insights. |
| **5** | **JD Entity Analyzer** | `/career-intelligence?tab=analyzer` | Zero-shot structured JSON extraction of required vs. preferred technologies and credentials. |
| **6** | **Resume → JD Alignment Matcher** | `/career-intelligence?tab=match` | 5-dimensional match scoring across Skills, Keywords, Experience, and Responsibilities. |
| **7** | **Cover Letter Generator** | `/career-intelligence?tab=cover-letter` | Anti-hallucination prompt generator strictly bound to verified candidate resume bullets. |
| **8** | **Cold Email Outreach Engine** | `/career-intelligence?tab=cold-email` | Context-aware outreach generator for hiring managers with subject line regeneration. |
| **9** | **Careers Taxonomy & Skill Gap** | `/careers`, `/skill-gap` | O*NET SOC standard taxonomy; substring token matching; deterministic match percentage. |
| **10**| **Career Roadmap Generator** | `/roadmap` | 5-phase structured milestones with curated fallback curricula across major engineering tracks. |
| **11**| **Personal Trainer** | `/personal-trainer` | Day-by-day micro-tasks; capacity constraint scaling; adaptive carry-over rollover engine. |
| **12**| **AI Mock Interview Simulator** | `/interview`, `/interview/:id` | Full speech-to-text and text-to-speech integration; 6-metric objective evaluation rubric. |
| **13**| **Technical Question Bank** | `/question-bank` | Categorized questions (DSA, System Design, HR, SQL) with revealable model answers. |
| **14**| **Coding & SQL Sandbox** | `/coding`, `/coding/:slug` | Real-time Python/SQL sandbox executing test cases in isolated subprocesses (`-I -S`). |
| **15**| **Company-Specific Prep** | `/company-preparation` | Verified enterprise dossiers (Google, Amazon, Microsoft, TCS, Infosys) + 25 practice questions. |
| **16**| **Live Jobs Hub** | `/jobs` | Adzuna live REST ingestion with local seed fallback; resume keyword overlap matcher. |
| **17**| **Job Market Trends Analyzer** | `/job-market` | Aggregate real-time salary, workplace type, and skill demand distributions. |
| **18**| **Curated Learning Hub** | `/learning-resources` | Verified technical courses, documentation, and book links mapped to user skill gaps. |
| **19**| **AI Portfolio Project Blueprints**| `/projects` | Personalized multi-tier project architectures designed to fill missing resume skills. |
| **20**| **Performance Analytics & Badges**| `/performance`, `/achievements` | Longitudinal interview scoring charts and 9 automatic achievement milestones. |

---

## 🛠️ Technology Stack & Dependencies

### Backend Dependencies (`backend/requirements.txt`)
```toml
fastapi == "0.115.*"              # High-performance asynchronous ASGI web framework
uvicorn[standard] == "0.32.*"      # ASGI server with uvloop and httptools
sqlalchemy[asyncio] == "2.0.*"     # Modern 2.0-style async ORM
asyncpg == "0.30.*"                # High-speed PostgreSQL async driver
psycopg2-binary == "2.9.*"         # Sync PostgreSQL driver for migrations
aiosqlite == "0.22.*"              # Async SQLite driver for zero-config local dev
alembic == "1.14.*"                # Database migrations engine
pydantic == "2.10.*"               # High-speed data validation & serialization
pydantic-settings == "2.7.*"       # Environment settings management
httpx == "0.28.*"                  # Async HTTP client with connection pooling
python-jose[cryptography] == "3.3.*" # JWT signing and cryptographic tokens
passlib[bcrypt] == "1.7.*"         # Password hashing using bcrypt
python-multipart == "0.0.*"        # Multipart form data parser for resume uploads
pytest == "8.3.*"                  # Unit and integration test runner
pytest-asyncio == "0.25.*"         # Async test harness fixtures
aiosmtplib == "5.1.*"              # Async non-blocking SMTP email transport
apscheduler == "3.11.*"            # Asynchronous in-process cron scheduler
PyMuPDF == "1.27.*"                # C-accelerated PDF text & layout extraction
python-docx == "1.2.*"             # Microsoft Word (.docx) document extraction
```

### Frontend Dependencies (`frontend/package.json`)
```json
{
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-router-dom": "^7.3.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4.0.0",
    "@types/node": "^24.11.1",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^5.0.0",
    "autoprefixer": "^10.4.20",
    "oxlint": "^0.15.0",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.8.0",
    "vite": "^8.2.0"
  }
}
```

---

## 📊 Relational Data Topology

The platform manages **39 relational database models** categorized into 13 core functional domains:

```
[Users]
  │── (1:1) ──► [Profiles]
  │── (1:N) ──► [Resumes] ── (1:N) ──► [ResumeVersions]
  │                 │
  │                 └── (1:N) ──► [ResumeAnalysis] ── (1:N) ──► [ResumeSkills]
  │
  │── (1:N) ──► [TrainingPlans] ── (1:N) ──► [TrainingDays] ── (1:N) ──► [TrainingTasks]
  │                 │
  │                 └── (1:1) ──► [PersonalTrainerSettings]
  │
  │── (1:N) ──► [InterviewSessions] ── (1:N) ──► [InterviewQuestions]
  │                                                     │
  │                                                     └── (1:1) ──► [InterviewAnswers] ── (1:1) ──► [InterviewEvaluations]
  │
  │── (1:N) ──► [Roadmaps] ── (1:N) ──► [RoadmapItems] ── (1:N) ──► [RoadmapProgress]
  │── (1:N) ──► [CareerGoals]
  │── (1:N) ──► [SkillGapReports]
  │── (1:N) ──► [CodingSubmissions] ── (1:N) ──► [CodingResults]
  │── (1:N) ──► [CompanyPrepPlans]
  │── (1:N) ──► [ResumeJdMatches]
  │── (1:N) ──► [CoverLetters]
  │── (1:N) ──► [ColdEmails]
  │── (1:N) ──► [JobMatches]
  │── (1:N) ──► [SavedJobs]
  │── (1:N) ──► [SavedQuestions]
  │── (1:N) ──► [UserLearningProgress]
  │── (1:N) ──► [ProjectRecommendations]
  │── (1:N) ──► [UserAchievements]
  │── (1:N) ──► [Notifications]
  └── (1:1) ──► [NotificationPreferences]

[Global Catalogs]
  ├── [Occupations] ── (1:N) ──► [OccupationSkills] ◄── (1:N) ── [Skills]
  ├── [CodingChallenges]
  ├── [QuestionBank]
  ├── [Jobs]
  ├── [LearningResources]
  └── [Achievements]
```

---

## ⚡ Quick Start & Execution Guide

### Method 1: Instant 1-Click Launch (Recommended)

- **On Windows:** Double-click **`run.bat`** (or `start.bat`) in the root directory.
- **On macOS / Linux:**
  ```bash
  chmod +x run.sh && ./run.sh
  ```
- **Or via Node.js (Cross-Platform):**
  ```bash
  npm start
  ```

> **Automated Startup Sequence:**
> 1. Verifies Python 3.10+ and Node.js 18+ environments.
> 2. Auto-installs missing backend requirements and frontend `node_modules`.
> 3. Creates the database schema and seeds standard verified jobs, coding challenges, and demo accounts.
> 4. Launches the FastAPI Backend on `http://127.0.0.1:8000` and Vite Frontend on `http://localhost:5173`.
> 5. Opens your default web browser automatically to `http://localhost:5173`.

---

### 🔑 Pre-Seeded Demonstration Accounts

You can log in instantly using the pre-seeded demo accounts (or use the 1-click login buttons on `/login`):

| Account Role | Email Address | Password | Permissions |
|---|---|---|---|
| **Candidate Demo** | `demo@example.com` | `Password123!` | Full candidate access to all 20 modules |
| **System Administrator** | `admin@example.com` | `AdminPassword123!` | Full candidate access + Admin Dashboard & Telemetry |

---

### Method 2: Manual Terminal Execution

#### Terminal 1: Backend Service
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 2: Frontend Service
```bash
cd frontend
npm install
npm run dev
```

#### Method 3: Docker Compose (PostgreSQL Deployment)
```bash
docker compose up --build
```

---

## 🔐 Environment Variables Specification

Configure in `backend/.env` or root `.env`:

| Key | Default Value | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./career_coach.db` | Primary asynchronous database connection URI |
| `DATABASE_URL_SYNC` | `sqlite:///./career_coach.db` | Synchronous URI utilized by Alembic migrations |
| `JWT_SECRET` | `change-me-to-a-random-secret-in-production` | Cryptographic secret for signing JWT tokens |
| `JWT_ALGORITHM` | `HS256` | HMAC-SHA256 signature algorithm |
| `JWT_EXPIRATION_MINUTES`| `30` | Access token lifespan before re-authentication |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama inference server address |
| `OLLAMA_MODEL` | `llama3.2:3b` | Target LLM model name (`llama3.2:3b`, `llama3`, `mistral`) |
| `ADZUNA_APP_ID` | `3510f190` | Adzuna Live Job Provider App ID |
| `ADZUNA_APP_KEY` | `6c8f1f8090a309a90dff9d3e4cc69e97` | Adzuna Live Job Provider Secret Key |
| `ADZUNA_COUNTRY` | `in` | Default job search country code (`in`, `us`, `gb`) |
| `SMTP_ENABLED` | `true` | Master toggle for email delivery and cron scheduling |
| `SMTP_HOST` | `sandbox.smtp.mailtrap.io` | SMTP transport host (`smtp.gmail.com` for Gmail) |
| `SMTP_PORT` | `587` | Port (`587` for STARTTLS, `465` for SSL) |
| `SMTP_USER` | `977a6e0a7d13df` | SMTP user / Gmail address |
| `SMTP_PASSWORD` | `8aa0814d45b9fd` | SMTP password / 16-character Google App Password |
| `SMTP_FROM_NAME` | `CareerCoachAI` | Sender display name |
| `REMINDER_MORNING_TIME`| `07:00` | Morning briefing cron trigger time (`HH:MM`) |
| `REMINDER_EVENING_TIME`| `20:00` | Evening wrap-up cron trigger time (`HH:MM`) |
| `REMINDER_TIMEZONE` | `Asia/Kolkata` | Cron scheduler timezone |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Allowed CORS origins list or JSON array |
| `MAX_FILE_SIZE_BYTES` | `10485760` (10 MB) | Maximum permitted file upload size for resumes |

---

## 🌐 Comprehensive API Directory

All API routes are served under `/api/v1` and wrapped in a standard response envelope:
```json
{
  "status": "success",
  "message": "Human-readable status summary",
  "data": { ... }
}
```

### Core API Endpoints Table

| Method | Endpoint Path | Authentication | Description |
|---|---|---|---|
| `GET` | `/api/v1/health` | Public | System health check (probes Database and Ollama status) |
| `POST` | `/api/v1/auth/register` | Public | Register new candidate account |
| `POST` | `/api/v1/auth/login` | Public | Authenticate user credentials and issue Bearer JWT |
| `GET` | `/api/v1/auth/me` | Bearer Token | Retrieve currently authenticated user and profile |
| `GET` | `/api/v1/dashboard` | Bearer Token | Aggregated placement metrics, readiness gauge, and activity feed |
| `GET` | `/api/v1/resumes` | Bearer Token | List all user resumes with version metadata |
| `POST` | `/api/v1/resumes` | Bearer Token | Multipart resume upload (`.pdf`, `.docx`) |
| `GET` | `/api/v1/resumes/{id}/download` | Bearer Token | Stream original resume document binary |
| `POST` | `/api/v1/resumes/{id}/analyze` | Bearer Token | Trigger 5-part ATS scoring analysis (`?force=true`) |
| `GET` | `/api/v1/resumes/{id}/analysis` | Bearer Token | Retrieve ATS scores, rubric breakdown, and missing keywords |
| `POST` | `/api/v1/career-intelligence/analyze-jd` | Bearer Token | Extract structured skills, tech stack, and credentials from JD |
| `POST` | `/api/v1/career-intelligence/match` | Bearer Token | 5-part alignment evaluation between resume and job description |
| `POST` | `/api/v1/career-intelligence/cover-letter` | Bearer Token | Generate tailored cover letter grounded in candidate resume |
| `POST` | `/api/v1/career-intelligence/cold-email/generate` | Bearer Token | Generate high-converting recruiter cold email |
| `GET` | `/api/v1/careers` | Bearer Token | Query O*NET standard occupation taxonomy |
| `POST` | `/api/v1/career/skill-gap` | Bearer Token | Compute skill gap report against target occupation |
| `POST` | `/api/v1/roadmap/generate` | Bearer Token | Generate 5-phase career milestone roadmap |
| `PUT` | `/api/v1/roadmap/items/{id}/toggle` | Bearer Token | Toggle roadmap milestone completion state |
| `POST` | `/api/v1/personal-trainer/investigate` | Bearer Token | Generate customized day-by-day learning plan |
| `GET` | `/api/v1/personal-trainer/daily/{day}` | Bearer Token | Get daily study agenda with carried-over tasks |
| `PATCH`| `/api/v1/personal-trainer/tasks/{id}` | Bearer Token | Update task status (`completed`, `in_progress`, etc.) |
| `POST` | `/api/v1/personal-trainer/reschedule-today` | Bearer Token | Dynamically fit tasks into today's available hours |
| `POST` | `/api/v1/interviews` | Bearer Token | Create new mock interview session |
| `POST` | `/api/v1/interviews/{id}/answer` | Bearer Token | Submit answer for 6-metric objective evaluation |
| `GET` | `/api/v1/interviews/{id}/results` | Bearer Token | Final session performance report with radar averages |
| `GET` | `/api/v1/coding/challenges` | Bearer Token | List coding and SQL technical challenges |
| `POST` | `/api/v1/coding/challenges/{id}/submit` | Bearer Token | Execute code against isolated sandbox test cases |
| `POST` | `/api/v1/coding/challenges/{id}/hint` | Bearer Token | Generate pedagogical AI hint without revealing solution |
| `POST` | `/api/v1/company-prep` | Bearer Token | Generate targeted interview prep dossier for top companies |
| `GET` | `/api/v1/jobs` | Bearer Token | Search live job openings via Adzuna with local cache |
| `POST` | `/api/v1/jobs/{id}/match` | Bearer Token | Calculate match score between active resume and specific job |
| `GET` | `/api/v1/job-market/search` | Bearer Token | Real-time market analytics (salary curves, skills, workplace) |
| `GET` | `/api/v1/performance` | Bearer Token | Longitudinal interview analytics and topic mastery |
| `GET` | `/api/v1/readiness` | Bearer Token | Multi-attribute placement readiness index calculation |
| `GET` | `/api/v1/admin/statistics` | Admin Role | System-wide usage counts and operational telemetry |

---

## 🧪 Quality Assurance & Test Verification

### Backend Automated Test Suite (121/121 Passing)
```bash
cd backend
pytest -v
```

The automated test suite executes against isolated in-memory SQLite instances:
- **Authentication & Governance:** `tests/test_auth.py`, `tests/test_admin.py`
- **Resume Processing & ATS Engine:** `tests/test_resumes.py`, `tests/test_resume_analysis.py`
- **Career Intelligence Pipeline:** `tests/test_career_intelligence.py`
- **Personal Trainer & Rollover:** `tests/test_personal_trainer.py`, `tests/test_email_scheduler.py`
- **Mock Interview Rubrics:** `tests/test_interviews.py`
- **Coding Sandbox Execution:** `tests/test_coding.py`
- **Ollama Provider & Offline Fallbacks:** `tests/test_ollama.py`

### Frontend Production Build Verification
```bash
cd frontend
npm run build
```
Validates strict TypeScript types (`tsc -b`) and ensures 0 bundle errors.

### SMTP Diagnostic Utility
```bash
cd backend
python scripts/test_smtp.py your_email@gmail.com
```

---

## 🔒 Security, Sandboxing & Row-Level Isolation

1. **Row-Level Tenant Isolation:** Every database operation strictly filters by authenticated `user_id`. Cascading deletions guarantee complete data removal upon account deletion.
2. **Execution Sandbox Isolation:** User Python code runs in temporary directories via `python -I -S` under a **3.0-second** timeout and a 10 KB stdout limit. Subprocesses run completely isolated from the FastAPI application loop.
3. **In-Memory SQL Protection:** Candidate SQL queries execute in dedicated `:memory:` SQLite databases that are immediately torn down.
4. **Input Sanitization & Parameterized Queries:** All database queries utilize SQLAlchemy parameterized statements, preventing SQL injection. File uploads are validated by MIME type, format (`.pdf`, `.docx`), and size ($< 10\text{ MB}$).
5. **CORS Defense-in-Depth:** Origin headers are matched against explicit origins and loopback interfaces via regex (`r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"`).

---

## 📧 Automated Scheduler & SMTP Dispatch

When `SMTP_ENABLED=true`, **APScheduler** manages two daily cron jobs:
- **Morning Briefing (07:00 AM IST):** Summarizes today's agenda, planned study minutes, and yesterday's progress.
- **Evening Wrap-Up (08:00 PM IST):** Reviews completed tasks, logs study velocity, and encourages streak preservation.
- **Task Milestone Alerts:** Dispatches an immediate confirmation email whenever an individual training task is marked `completed`.

---

## 📜 License & Citation

Distributed under the **MIT License**. Free for educational, academic, and commercial research adaptation.

```bibtex
@software{placement_ai_2026,
  author = {Tejaswini Bengeri & Team},
  title = {Placement AI: Comprehensive AI Career, Resume & Interview Coaching Platform},
  year = {2026},
  url = {https://github.com/tejaswinibengeri/AI-Career-Interview-Coach}
}
```
