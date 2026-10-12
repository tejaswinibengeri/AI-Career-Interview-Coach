# Placement AI (AI Career & Interview Coach)
## Master Technical Specification, System Architecture & Algorithmic Documentation

---

## 1. Executive Summary & Problem Formulation

### 1.1 Product Identity
**Placement AI** (also identified as **AI Career & Interview Coach** or **CareerCoachAI**) is an enterprise-grade, offline-capable, full-stack career acceleration and interview preparation platform. It is engineered to bridge the gap between academic preparation and competitive technical hiring for software engineering, data science, DevOps, and cloud computing roles.

### 1.2 Core Problem Statement
Traditional placement preparation is fragmented:
1. **Opaque ATS Filtering:** Candidates do not understand why automated Applicant Tracking Systems reject their resumes.
2. **Generic Roadmaps:** Generic static roadmaps do not adapt to an individual candidate's specific missing skills or target roles.
3. **High-Stress, High-Cost Mock Interviews:** Commercial human mock interviews are expensive ($50–$200/hr), lack standardized evaluation rubrics, and fail to provide immediate, actionable quantitative feedback.
4. **Execution Paralysis:** Candidates struggle to translate high-level career objectives into realistic daily micro-habits and tasks.

### 1.3 Architectural Design Principles
1. **"Deterministic Mathematics + AI Narration":**
   Scores, percentages, and metrics are computed through explicit, auditable Python algorithms (weighted rubrics, set intersection, token frequency, and linear combinations). The local Large Language Model (LLM) is strictly utilized for prose generation, structured entity extraction, and pedagogical explanations—never as an uncontrolled source of quantitative truth.
2. **Zero-Cloud, Private Offline AI:**
   All generative operations interface with a locally hosted **Ollama** runtime (`llama3.2:3b`, `llama3`, or `mistral`). No candidate resumes, transcripts, or proprietary data are transmitted to third-party commercial APIs (e.g., OpenAI, Anthropic), ensuring zero API token costs and absolute data privacy.
3. **Resilient Graceful Degradation:**
   Every single AI-augmented module incorporates a deterministic fallback generator. If the local Ollama instance is offline, uninstalled, or times out, the platform seamlessly substitutes hand-curated pedagogical data structures so that the user interface never crashes.
4. **Strict Multi-Tenant Row-Level Isolation:**
   Every database query filters strictly by authenticated `user_id`. Cascading deletions guarantee that user data can be cleanly purged.

---

## 2. Exhaustive Technology Stack & Tools Inventory

### 2.1 Backend Engineering
| Layer / Tool | Exact Version / Spec | Technical Purpose & Architectural Role |
|---|---|---|
| **Python** | `3.11.9+` | Primary programming language; utilized for asynchronous concurrency, typing, and data processing. |
| **FastAPI** | `0.115.*` | High-performance asynchronous web framework providing ASGI routing, dependency injection (`Depends`), and automatic OpenAPI / Swagger generation. |
| **Uvicorn** | `0.32.* (uvicorn[standard])` | Production-grade ASGI server utilizing `uvloop` and `httptools` for async event handling. |
| **SQLAlchemy** | `2.0.* (sqlalchemy[asyncio])` | Modern 2.0-style asynchronous Object Relational Mapper utilizing `Mapped[...]` and `mapped_column` type annotations. |
| **aiosqlite** | `0.22.*` | Asynchronous SQLite driver used for zero-configuration local development and rapid test isolation. |
| **asyncpg / psycopg2** | `asyncpg 0.30.*`, `psycopg2-binary 2.9.*` | High-throughput asynchronous and synchronous PostgreSQL drivers for production container deployment. |
| **Alembic** | `1.14.*` | Database schema migration engine with automated schema revision generation. |
| **Pydantic** | `2.10.*` & `pydantic-settings 2.7.*` | High-speed Rust-based data validation and settings management reading `.env` configurations. |
| **PyMuPDF (`fitz`)** | `1.27.*` | Low-level C-accelerated PDF parsing library extracting raw text and metadata from uploaded resumes. |
| **python-docx** | `1.2.*` | Microsoft Word (`.docx`) XML unpacker and paragraph/table text extractor. |
| **python-jose** | `3.3.* [cryptography]` | Cryptographic library implementing JSON Web Signature (JWS) and JWT encoding/decoding. |
| **passlib** | `1.7.* [bcrypt]` | Password hashing framework utilizing salted blowfish password hashing. |
| **httpx** | `0.28.*` | Fully asynchronous HTTP client utilizing connection pooling to interact with Ollama and the Adzuna Job API. |
| **aiosmtplib** | `5.1.*` | Non-blocking asynchronous SMTP client supporting SSL/TLS and STARTTLS for automated email delivery. |
| **APScheduler** | `3.11.*` | Asynchronous In-Process Cron Scheduler (`AsyncIOScheduler`) driving daily morning and evening notifications. |
| **pytest & pytest-asyncio** | `pytest 8.3.*`, `pytest-asyncio 0.25.*` | Asynchronous unit and integration test suite executing against in-memory SQLite fixtures. |

### 2.2 Frontend Engineering
| Layer / Tool | Exact Version / Spec | Technical Purpose & Architectural Role |
|---|---|---|
| **React** | `19.2.*` | Modern declarative user interface library utilizing concurrent rendering and React Hooks. |
| **TypeScript** | `~6.0 / 5.8` | Strictly-typed static analysis enforcing interfaces for all API contracts and component props. |
| **Vite** | `8.2.*` | Ultra-fast ESM-based frontend bundler and development server featuring Hot Module Replacement (HMR). |
| **React Router** | `react-router-dom 7.3.*` | Client-side declarative routing system managing navigation, protected route guards, and URL parameters. |
| **Tailwind CSS** | `3.4.*` | Utility-first CSS styling framework compiled with PostCSS and Autoprefixer; configured with dark mode surfaces and glassmorphic elevation tokens. |
| **Web Speech API** | Native Browser API | Client-side hardware integration: `SpeechRecognition` (voice-to-text) and `speechSynthesis` (text-to-speech) for realistic mock interviews. |
| **oxlint** | `0.15.*` | High-performance Rust-based JavaScript/TypeScript linter. |

### 2.3 Local AI & External Integrations
| Service / Integration | Protocol / Format | Technical Purpose |
|---|---|---|
| **Ollama** | Local REST HTTP (`127.0.0.1:11434`) | Runs open-weights models (`llama3.2:3b`, `llama3`, `mistral`) locally in GPU/CPU VRAM. |
| **Adzuna Job API** | External REST HTTPS | Real-time global and domestic live job search query provider. |
| **O\*NET Taxonomy** | Static In-Memory Dataset | Standard Occupational Classification (SOC) system mapping tech occupations to weighted skills. |
| **Mailtrap / SMTP** | SMTP Port 587 / 465 | Development and production transactional email transport. |

---

## 3. Mathematical Models & Core Algorithms

### 3.1 Algorithm 1: Transparent Weighted ATS Resume Scoring
The resume ATS evaluation applies a multi-criteria linear scoring model. Rather than allowing the LLM to emit an arbitrary single number, the LLM evaluates 5 distinct dimensions (from 0 to 100), and the backend computes the final score via a weighted linear combination:

$$\text{ATS Score} = \sum_{i=1}^{5} w_i \cdot s_i$$

Where:
- $w_{\text{structure}} = 0.20$ (Standard headings, contact details, chronological layout)
- $w_{\text{skills}} = 0.30$ (Technical keyword density, modern tool stack coverage)
- $w_{\text{experience}} = 0.25$ (Action verb usage, measurable business impact metrics)
- $w_{\text{education}} = 0.15$ (Degree relevance, academic standing, certifications)
- $w_{\text{formatting}} = 0.10$ (Parseability, spacing, typography, absence of parsing noise)

$$\text{ATS Score} = \text{round}\Big(\min\big(100.0, \max(0.0, 0.20 s_{\text{struct}} + 0.30 s_{\text{skills}} + 0.25 s_{\text{exp}} + 0.15 s_{\text{edu}} + 0.10 s_{\text{format}})\big), 1\Big)$$

**Heuristic Metric Enforcement:**
If the LLM returns an empty weakness list, the system executes a deterministic regex scan:
$$\text{Has Metrics} = \text{regex\_match}\big(\text{"\%|\b(increased|reduced|improved|boosted|saved)\b"}, \text{ResumeText}\big)$$
If false, the system automatically appends: *"Lacks quantifiable business metrics (e.g., % latency reduction or user growth) in work bullet points."*

---

### 3.2 Algorithm 2: O\*NET Skill Gap Analysis & Overlap Ratio
Given an occupation $O$ with required skills $K_O = \{k_1, k_2, \dots, k_m\}$ and user skill profile $U = \text{ProfileSkills} \cup \text{ResumeSkills} \cup \text{UserSkills}$:

1. For each skill $k_j \in K_O$ with O\*NET importance weight $I(k_j) \in [0, 100]$:
   - If $\exists u \in U$ such that $u \subseteq k_j$ or $k_j \subseteq u$:
     - If $I(k_j) \ge 85 \implies k_j \in \text{Strong Skills}$
     - Else $\implies k_j \in \text{Intermediate Skills}$
   - Else:
     - $k_j \in \text{Missing Skills}$
     - Priority assignment:
       $$\text{Priority}(k_j) = \begin{cases} \text{High}, & I(k_j) \ge 88 \\ \text{Medium}, & 80 \le I(k_j) < 88 \\ \text{Low}, & I(k_j) < 80 \end{cases}$$

2. **Deterministic Match Percentage:**
   $$\text{Match Percentage} = \frac{|\text{Strong}| \cdot 1.0 + |\text{Intermediate}| \cdot 0.6}{|K_O|} \times 100$$

---

### 3.3 Algorithm 3: Dynamic Placement Readiness Composite Index
The readiness index quantifies the candidate's hiring readiness using a **Multi-Attribute Utility Model** with dynamic weight renormalization for missing user data:

$$\text{Readiness Index} = \sum_{k \in \text{Available}} W_{\text{effective}, k} \cdot S_k$$

Where raw weights are:
- $W_{\text{raw, resume}} = 0.25$ (Latest Resume ATS Score)
- $W_{\text{raw, skills}} = 0.25$ (Skill Gap Match % or $\min(100, |\text{ProfileSkills}| \times 15)$)
- $W_{\text{raw, interview}} = 0.35$ (Historical Mock Interview Average)
- $W_{\text{raw, coding}} = 0.15$ (Coding/DSA Interview Question Average)

**Dynamic Renormalization Formula:**
$$W_{\text{effective}, k} = \frac{W_{\text{raw}, k}}{\sum_{j \in \text{Available}} W_{\text{raw}, j}}$$

**Readiness Classification Bands:**
$$\text{Readiness Band} = \begin{cases} \text{Job Ready}, & \text{Score} \ge 80.0 \\ \text{Nearly Ready}, & 65.0 \le \text{Score} < 80.0 \\ \text{Needs Preparation}, & \text{Score} < 65.0 \end{cases}$$

---

### 3.4 Algorithm 4: Resume-to-Job Lexical Matching
When matching a candidate resume against a live Job Description (JD):
1. Candidate text $T_R$ and Job text $T_{JD}$ are scanned against a technology lexicon of ~250 tokens.
2. Skill match:
   $$S_{\text{skill}} = \frac{|K_R \cap K_{JD}|}{|K_{JD}|} \times 100$$
3. Experience and education alignments ($S_{\text{exp}}, S_{\text{edu}}$) are computed through regex heuristic checks (years of experience match and degree type matching).
4. Composite score:
   $$\text{Overall Match} = \text{clamp}\big(0.50 S_{\text{skill}} + 0.25 S_{\text{exp}} + 0.25 S_{\text{edu}}, 20.0, 98.0\big)$$

---

### 3.5 Algorithm 5: Mock Interview 6-Metric Evaluation Rubric
When an interview answer is submitted, Ollama evaluates it against a 6-dimensional rubric (clamped $0–100$):
1. **Technical Correctness ($s_1$):** Accuracy of technical facts, algorithms, and design choices.
2. **Relevance ($s_2$):** How directly the answer addresses the prompt without tangent deviation.
3. **Completeness ($s_3$):** Coverage of edge cases, trade-offs, and underlying mechanisms.
4. **Communication ($s_4$):** Professional vocabulary and absence of filler hesitation.
5. **Structure ($s_5$):** STAR format (Situation, Task, Action, Result) or structured problem decomposition.
6. **Clarity ($s_6$):** Conciseness and conceptual lucidity.

$$\text{Overall Answer Score} = \frac{1}{6} \sum_{i=1}^{6} s_i$$
Session overall score is the arithmetic mean across all answers in the session.

---

### 3.6 Algorithm 6: Server-Side Isolated Code Execution Sandbox
To eliminate security vulnerabilities, user code is executed in an isolated process sandbox (`services/code_executor.py`):

```
Candidate Code (Python)
         │
         ▼
[ast.parse Pre-check] ────(Syntax Error)────► Fast Rejection (< 1ms)
         │
         ▼ (Syntax Valid)
[Inject into Isolated Test Harness Wrapper]
         │
         ▼
[Spawn Subprocess: python -I -S solution.py]
  - Flag -I: Isolated mode (ignores PYTHONPATH and user site-packages)
  - Flag -S: Do not import 'site' module on initialization
  - Timeout: 3.0s watchdog timer
         │
         ├────(TimeoutExpired)────► "Time Limit Exceeded"
         ├────(Exit Code != 0)────► "Runtime Error"
         └────(Exit Code == 0)────► Compare Actual vs Expected (JSON/Text Equality)
```

**SQL Execution Sandbox:**
Queries run against an ephemeral in-memory SQLite database:
1. `conn = sqlite3.connect(":memory:")`
2. Execute problem `sql_schema` (DDL `CREATE TABLE` and DML `INSERT INTO`).
3. Execute candidate SQL query.
4. Serialize row tuples to JSON format and compare with expected output test cases.
5. Close and garbage collect connection.

---

### 3.7 Algorithm 7: Adaptive Task Rollover & Rescheduling
The Personal Trainer schedules daily tasks based on candidate capacity:
1. **Daily Workload Constraint:**
   $$\sum_{t \in \text{Tasks}_d} \text{Duration}(t) \le \text{DailyHours} \times 60$$
   If total exceeds limit, tasks are scaled down proportionally:
   $$\text{NewDuration}(t) = \max\Big(15, \text{round}\big(\text{Duration}(t) \cdot \frac{\text{DailyHours} \times 60}{\text{TotalMinutes}}\big)\Big)$$
2. **Adaptive Rollover Engine:**
   On date transition, if any task in Day $d-1$ has status $\in \{\text{not\_started}, \text{in\_progress}\}$:
   - Original task status updated to `rescheduled`.
   - Cloned into Day $d$ with `is_carried_over = True` and title suffix `"(Carried Over)"`.
3. **Greedy Rescheduling Knapsack:**
   Given user-specified hours $H_{\text{avail}}$:
   - Accumulate tasks until $\sum \text{Minutes} \le H_{\text{avail}} \times 60$.
   - Any overflow tasks are shifted to Day $d+1$.

---

### 3.8 Algorithm 8: Resilient LLM JSON Extraction & State-Machine Repair
Because LLMs frequently return markdown fences, trailing commas, or incomplete brackets, `json_utils.py` uses a multi-tier parsing state machine:

1. **Step 1:** Strip opening and closing markdown code fences (```` ```json ````).
2. **Step 2:** Direct parse attempt via `json.loads`.
3. **Step 3 (Substring Extraction):** Search for outermost balanced `{...}` or `[...]`.
4. **Step 4 (Syntax Normalization):**
   - Strip trailing commas before closing braces/brackets: `re.sub(r",\s*([\}\]])", r"\1", text)`.
   - Substitute Python literals with JSON counterparts: `True` $\to$ `true`, `False` $\to$ `false`, `None` $\to$ `null`.
5. **Step 5 (Stack-Based Truncation Repair):**
   ```python
   # State machine tracking string escape states and nesting stack:
   for char in text:
       if escape: escape = False; continue
       if char == "\\": escape = True; continue
       if char == '"': in_string = not in_string; continue
       if not in_string:
           if char in "{[": stack.append(char)
           elif char == "}" and stack[-1] == "{": stack.pop()
           elif char == "]" and stack[-1] == "[": stack.pop()
   # Close open string quote
   if in_string: text += '"'
   # Close remaining open brackets in reverse order
   while stack:
       opener = stack.pop()
       text += "}" if opener == "{" else "]"
   ```

---

### 3.9 Algorithm 9: In-Memory LRU + TTL Cache for LLM Generations
To prevent redundant GPU inference, `LLMResponseCache` implements an LRU cache with time-to-live:
1. Cache key derivation:
   $$\text{Key} = \text{SHA-256}\big(\text{model} \,||\, \text{prompt} \,||\, \text{sorted(kwargs)}\big)$$
2. Expiration: Default TTL = 1800 seconds (30 minutes). Max capacity = 500 entries.
3. Cold-Start Pre-Warming:
   On application startup, a background coroutine sends `{"prompt": "ping", "num_predict": 1, "keep_alive": "60m"}` to Ollama, pinning model weights in VRAM for instant subsequent inferences.

---

### 3.10 Algorithm 10: Cryptographic Security & Auth Verification
- **Password Hashing:** Passlib with Blowfish `bcrypt` algorithm. Auto-generates random 128-bit salt and applies 12 work factor rounds.
- **Access Tokens:** Stateless HMAC-SHA256 (`HS256`) JSON Web Tokens containing `{"sub": str(user_id), "email": email, "exp": now + 30m}`.
- **Reset Token Generation:** Cryptographically Secure Pseudorandom Number Generator (CSPRNG): `secrets.token_urlsafe(32)`.

---

## 4. System Architecture & Data Flow

### 4.1 High-Level Architecture Diagram
```
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT BROWSER (Vite + React 19)                │
│  - Tailwind CSS v3 UI Components       - Web Speech API (TTS & STT)   │
│  - React Router v7 SPA Navigation      - Typed Fetch Client (api.ts)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST / JSON
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND (Uvicorn ASGI)                  │
│                                                                        │
│  ┌───────────────────────┐  ┌───────────────────────────────────────┐  │
│  │   API Router / v1     │  │        Security & Middleware          │  │
│  │ (22 Modular Routers)  │  │  - CORS Middleware  - JWT Bearer Auth │  │
│  └───────────┬───────────┘  └───────────────────────────────────────┘  │
│              │                                                         │
│              ▼                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     Service Business Logic Layer                  │  │
│  │  - ATS Engine      - Interview Evaluator    - Code Sandbox        │  │
│  │  - Skill Gap Math  - Personal Trainer       - Job Matcher         │  │
│  └───────────┬─────────────────────────┬─────────────────────────────┘  │
│              │                         │                                │
│              ▼                         ▼                                │
│  ┌───────────────────────┐ ┌─────────────────────────────────────────┐  │
│  │   SQLAlchemy 2.0 ORM  │ │   Local AI Layer (OllamaProvider)       │  │
│  │ (Async Engine & Pool) │ │ - SHA-256 LRU Cache  - JSON Auto-Repair │  │
│  └───────────┬───────────┘ └───────────────────┬─────────────────────┘  │
└──────────────┼─────────────────────────────────┼────────────────────────┘
               │                                 │ Local HTTP
               ▼                                 ▼
┌──────────────────────────────┐  ┌──────────────────────────────────────┐
│  DATABASE STORAGE            │  │  LOCAL OLLAMA ENGINE (:11434)        │
│  - SQLite (career_coach.db)  │  │  - Model: llama3.2:3b / llama3       │
│  - or PostgreSQL 16 (Docker) │  │  - Zero Cloud Costs & Zero Leakage   │
└──────────────────────────────┘  └──────────────────────────────────────┘
```

### 4.2 Background Scheduling & Notification Pipeline
```
[APScheduler AsyncIOScheduler]
        │
        ├─► 07:00 AM (Asia/Kolkata): Morning Briefing Cron Job
        │     └─► Queries Incomplete Day Tasks ──► Compiles HTML ──► aiosmtplib Send
        │
        └─► 08:00 PM (Asia/Kolkata): Evening Wrap-Up Cron Job
              └─► Evaluates Daily Task Velocity ─► Compiles HTML ──► aiosmtplib Send
```

---

## 5. Comprehensive Database Schema (39 Models)

### 5.1 Identity & User Profiles
1. **`users`**:
   - `id`: Integer, Primary Key, Autoincrement.
   - `email`: String(255), Unique, Indexed.
   - `name`: String(255).
   - `hashed_password`: String(255).
   - `is_active`: Boolean (Default: True).
   - `role`: String(50) (Default: "user").
   - `is_superuser`: Boolean (Default: False).
   - `reset_token`: String(255), Nullable.
   - `reset_token_expires_at`: DateTime(timezone=True), Nullable.
   - `created_at`, `updated_at`: DateTime(timezone=True).
2. **`profiles`**:
   - `id`: Integer, Primary Key.
   - `user_id`: Integer, ForeignKey(`users.id`, ondelete="CASCADE"), Unique.
   - `education`, `degree`, `graduation_year`: String / Integer.
   - `experience`, `current_role`, `target_role`: String.
   - `skills`: JSON (SQLite) / JSONB (Postgres) array of skill strings.
   - `preferred_location`, `work_preference`, `career_goal`: String / Text.

### 5.2 Resume Studio
3. **`resumes`**:
   - `id`: Integer, Primary Key.
   - `user_id`: Integer, ForeignKey(`users.id`, ondelete="CASCADE").
   - `title`: String(255).
4. **`resume_versions`**:
   - `id`: Integer, Primary Key.
   - `resume_id`: Integer, ForeignKey(`resumes.id`, ondelete="CASCADE").
   - `version_number`: Integer.
   - `filename`, `file_path`, `mime_type`: String.
   - `file_size`: Integer.
   - `extracted_text`: Text (Raw UTF-8 extracted from PDF/DOCX).
   - `is_current`: Boolean.
5. **`resume_analysis`**:
   - `id`: Integer, Primary Key.
   - `resume_id`: ForeignKey(`resumes.id`), `resume_version_id`: ForeignKey(`resume_versions.id`).
   - `ats_score`: Float.
   - `scoring_breakdown`: JSON (Dictionary containing the 5 sub-scores & weights).
   - `strengths`, `weaknesses`, `missing_keywords`: JSON list.
   - `grammar_suggestions`, `formatting_suggestions`, `improvement_recommendations`: JSON list.
6. **`resume_skills`**:
   - `id`: Integer, Primary Key.
   - `resume_analysis_id`: ForeignKey(`resume_analysis.id`, ondelete="CASCADE").
   - `skill_name`, `category`, `proficiency_level`: String.

### 5.3 Careers & O\*NET Skill Taxonomy
7. **`occupations`**: `id`, `code` (SOC Code, Unique), `title`, `description`, `industry`.
8. **`skills`**: `id`, `name` (Unique), `category`.
9. **`occupation_skills`**: `id`, `occupation_id` (FK), `skill_id` (FK), `importance` (0-100), `level` (0-100), `is_required`.
10. **`user_skills`**: `id`, `user_id` (FK), `skill_name`, `source` ("profile" / "resume"), `proficiency`.
11. **`career_goals`**: `id`, `user_id` (FK), `occupation_id` (FK), `target_role_title`, `is_active`.
12. **`skill_gap_reports`**: `id`, `user_id` (FK), `occupation_id` (FK), `match_percentage`, `strong_skills` (JSON), `intermediate_skills` (JSON), `missing_skills` (JSON), `learning_order` (JSON), `ai_explanation` (Text).

### 5.4 Career Roadmap
13. **`roadmaps`**: `id`, `user_id` (FK), `occupation_id` (FK, Nullable), `title`, `target_role`, `overall_progress`, `is_active`.
14. **`roadmap_items`**: `id`, `roadmap_id` (FK), `phase`, `skill`, `topics` (JSON), `projects` (JSON), `resources` (JSON), `priority`, `estimated_effort`, `is_completed`.
15. **`roadmap_progress`**: `id`, `roadmap_item_id` (FK), `user_id` (FK), `status`, `notes`.

### 5.5 Personal Trainer
16. **`training_plans`**: `id`, `user_id` (FK), `title`, `goal_dimensions` (JSON), `target_skill`, `target_role`, `target_company`, `current_skills` (JSON), `daily_hours`, `estimated_duration_days`, `total_learning_hours`, `overall_progress`, `is_active`, `phases_summary` (JSON).
17. **`training_days`**: `id`, `plan_id` (FK), `day_number`, `phase_name`, `objective`, `topics` (JSON), `expected_outcome`, `total_planned_minutes`, `is_completed`, `confidence_rating` (1-5), `ai_review_recommendation`.
18. **`training_tasks`**: `id`, `day_id` (FK), `title`, `description`, `task_type` (theory/practice/project/assessment), `estimated_minutes`, `status` (not_started/in_progress/completed/skipped/rescheduled), `is_carried_over`, `original_day_number`, `time_spent_minutes`.
19. **`personal_trainer_settings`**: `id`, `user_id` (FK, Unique), `notifications_enabled`, `preferred_time`, `notification_channel`.

### 5.6 Mock Interviews
20. **`interview_sessions`**: `id`, `user_id` (FK), `role`, `difficulty`, `status`, `total_questions`, `current_question_index`, `overall_score`, `summary_feedback`.
21. **`interview_questions`**: `id`, `session_id` (FK), `question_bank_id` (FK, Nullable), `question_text`, `category`, `difficulty`, `question_order`, `explanation`.
22. **`interview_answers`**: `id`, `session_id` (FK), `question_id` (FK), `user_answer`, `submitted_at`.
23. **`interview_evaluations`**: `id`, `answer_id` (FK, Unique), `technical_correctness`, `relevance`, `completeness`, `communication`, `structure`, `clarity`, `overall_score`, `feedback`, `strengths` (JSON), `improvements` (JSON), `ideal_answer`.

### 5.7 Question Bank & Coding Challenges
24. **`question_bank`**: `id`, `question`, `category`, `difficulty`, `role`, `tags` (JSON), `source_type` ("standard" / "ai_generated"), `explanation`.
25. **`saved_questions`**: `id`, `user_id` (FK), `question_id` (FK), UniqueConstraint(`user_id`, `question_id`).
26. **`coding_challenges`**: `id`, `title`, `slug` (Unique), `category` (Python/SQL/DSA), `difficulty`, `description`, `starter_code`, `language`, `examples` (JSON), `test_cases` (JSON), `sql_schema` (Text).
27. **`coding_submissions`**: `id`, `user_id` (FK), `challenge_id` (FK), `language`, `code`, `status` (Passed/Failed/Time Limit Exceeded/Runtime Error/Syntax Error), `passed_test_cases`, `total_test_cases`, `execution_time_ms`.
28. **`coding_results`**: `id`, `submission_id` (FK), `test_case_index`, `passed`, `input_data`, `expected_output`, `actual_output`, `error_output`, `execution_time_ms`.

### 5.8 Company Prep & Jobs
29. **`company_prep_plans`**: `id`, `user_id` (FK), `company_name`, `target_role`, `is_verified_company`, `company_overview`, `role_summary`, `required_skills` (JSON), `technical_prep_topics` (JSON), `coding_topics` (JSON), `hr_topics` (JSON), `behavioral_prep` (JSON), `practice_questions` (JSON).
30. **`jobs`**: `id`, `external_id` (Unique), `provider` ("adzuna" / "seed"), `title`, `company`, `location`, `is_remote`, `description`, `salary_min`, `salary_max`, `redirect_url`, `posted_at`.
31. **`saved_jobs`**: `id`, `user_id` (FK), `job_id` (FK), UniqueConstraint(`user_id`, `job_id`).
32. **`job_matches`**: `id`, `user_id` (FK), `job_id` (FK), `resume_id` (FK, Nullable), `match_score`, `experience_match`, `education_match`, `matched_skills` (JSON), `missing_skills` (JSON), `explanation`, `recommendations` (JSON).

### 5.9 Career Intelligence
33. **`resume_jd_matches`**: `id`, `user_id` (FK), `resume_id` (FK, Nullable), `resume_title`, `job_title`, `company_name`, `job_description`, `overall_score`, `skills_score`, `keyword_score`, `experience_score`, `responsibility_score`, `matched_skills` (JSON), `missing_skills` (JSON), `potential_gaps` (JSON), `improvement_suggestions` (JSON).
34. **`cover_letters`**: `id`, `user_id` (FK), `resume_id` (FK, Nullable), `job_title`, `company_name`, `tone`, `length`, `content`.
35. **`cold_emails`**: `id`, `user_id` (FK), `job_title`, `company_name`, `recruiter_name`, `recruiter_email`, `email_type`, `tone`, `length`, `subject`, `body`.

### 5.10 Learning, Projects, Achievements, Notifications
36. **`learning_resources`**: `id`, `title`, `description`, `url`, `source`, `resource_type`, `skill_name`, `difficulty`, `estimated_hours`, `is_verified`.
37. **`user_learning_progress`**: `id`, `user_id` (FK), `resource_id` (FK), `is_saved`, `is_completed`, `completed_at`.
38. **`project_recommendations`**: `id`, `user_id` (FK), `title`, `description`, `difficulty`, `target_role`, `technologies` (JSON), `features` (JSON), `skills_learned` (JSON), `status` ("Not Started" / "In Progress" / "Completed").
39. **`achievements` & `user_achievements`**: System badges with numeric thresholds (`threshold`), progress tracking, and unlocked timestamps.
40. **`notifications` & `notification_preferences`**: In-app activity alert events and category opt-in boolean preferences.

---

## 6. Functional Module Deep Dive (All 20 Modules)

| # | Module Name | Route | Service Layer | Key Mechanism & Algorithm |
|---|---|---|---|---|
| **1** | **User Authentication & Profile** | `/login`, `/register`, `/profile` | `auth_service.py`, `profile_service.py` | Bcrypt password hashing; HS256 JWT tokens; Profile completion ratio. |
| **2** | **Executive Dashboard** | `/dashboard` | `dashboard_service.py` | Aggregated real-time metrics, chronological activity stream, readiness index preview. |
| **3** | **Resume Studio** | `/resumes` | `resume_service.py`, `resume_parser.py` | PyMuPDF & python-docx parser; version history; set-diff comparison. |
| **4** | **Transparent ATS Analyzer** | `/resume-analysis/:id` | `resume_analysis_service.py` | 5-part weighted linear rubric; heuristic quantifiable impact validator. |
| **5** | **Career Intelligence: JD Analyzer** | `/career-intelligence?tab=analyzer` | `career_intelligence_service.py` | Zero-shot JSON extraction of required technologies, soft skills, and credentials. |
| **6** | **Career Intelligence: Resume→JD Match** | `/career-intelligence?tab=match` | `career_intelligence_service.py` | 5-dimensional match scoring (Skills, Keywords, Experience, Responsibilities, Overall). |
| **7** | **Career Intelligence: Cover Letter** | `/career-intelligence?tab=cover-letter` | `career_intelligence_service.py` | Anti-hallucination prompt generator strictly bound to verified resume facts. |
| **8** | **Career Intelligence: Cold Email** | `/career-intelligence?tab=cold-email` | `career_intelligence_service.py` | Recruiter outreach generator with subject line regeneration & retry loop. |
| **9** | **Careers Taxonomy & Skill Gap** | `/careers`, `/skill-gap` | `career_service.py` | O\*NET SOC taxonomy; substring skill overlap; deterministic match percentage. |
| **10**| **Career Roadmap** | `/roadmap` | `roadmap_service.py` | 5-phase structured milestones with curated fallback curricula. |
| **11**| **Personal Trainer** | `/personal-trainer` | `personal_trainer_service.py` | Day-by-day micro-tasks; capacity constraint scaling; adaptive carry-over rollover. |
| **12**| **AI Mock Interview Simulator** | `/interview`, `/interview/:id` | `interview_service.py` | State-persisted session runner; 6-metric rubric evaluation; browser voice engine. |
| **13**| **Technical Question Bank** | `/question-bank` | `question_service.py` | Seeded + AI-generated categorized technical questions with answer reveal. |
| **14**| **Coding & SQL Sandbox** | `/coding`, `/coding/:slug` | `coding_service.py`, `code_executor.py` | AST pre-validation; isolated subprocess execution (`-I -S`); in-memory SQLite sandbox. |
| **15**| **Company-Specific Prep** | `/company-preparation` | `company_prep_service.py` | Verified enterprise dossiers (FAANG/MNC) + 25-question interview bank. |
| **16**| **Live Jobs Hub** | `/jobs` | `job_service.py`, `job_match_service.py` | Adzuna live REST ingestion + seed cache fallback; resume keyword overlap matcher. |
| **17**| **Job Market Trends Analyzer** | `/job-market` | `job_market_service.py` | Aggregate real-time salary, workplace type, and skill demand distributions. |
| **18**| **Curated Learning Hub** | `/learning-resources` | `learning_resource_service.py` | Real external verified documentation/course catalog filtered by skill gaps. |
| **19**| **Portfolio Project Blueprints**| `/projects` | `project_service.py` | Personalized multi-tier project architectures designed to fill missing resume skills. |
| **20**| **Performance Analytics & Badges**| `/performance`, `/achievements` | `performance_service.py`, `achievement_service.py` | Longitudinal interview improvement analytics; 9 system achievement triggers. |

---

## 7. Master API Endpoints Reference

### 7.1 Authentication & Profile
- `POST /api/v1/auth/register` — Register a new candidate (`{name, email, password}`)
- `POST /api/v1/auth/login` — Authenticate and receive JWT Bearer token
- `GET /api/v1/auth/me` — Retrieve active user session profile
- `POST /api/v1/auth/forgot-password` — Generate password reset token
- `POST /api/v1/auth/reset-password` — Apply new password via valid reset token
- `GET /api/v1/profile` — Fetch user career profile
- `PUT /api/v1/profile` — Update target role, education, skills, and work preference
- `POST /api/v1/profile/change-password` — Update password with current password verification

### 7.2 Resume Studio & ATS Analysis
- `GET /api/v1/resumes` — List all user resumes with active version metadata
- `POST /api/v1/resumes` — Multipart file upload (`.pdf`, `.docx`)
- `GET /api/v1/resumes/{id}/download` — Stream resume file bytes with original filename
- `GET /api/v1/resumes/{id}/history` — Retrieve version progression and ATS score trajectory
- `GET /api/v1/resumes/{id}/compare?v1={v1}&v2={v2}` — Set-diff comparison between versions
- `DELETE /api/v1/resumes/{id}` — Delete resume and associated disk files
- `POST /api/v1/resumes/{id}/analyze` — Trigger transparent 5-part ATS analysis
- `GET /api/v1/resumes/{id}/analysis` — Retrieve latest ATS scoring breakdown and recommendations

### 7.3 Career Intelligence & O\*NET
- `POST /api/v1/career-intelligence/analyze-jd` — Extract structured entities from raw job description
- `POST /api/v1/career-intelligence/match` — Compute 5-score match between resume and job description
- `POST /api/v1/career-intelligence/cover-letter` — Generate hallucination-free cover letter
- `POST /api/v1/career-intelligence/cold-email/generate` — Generate recruiter outreach email
- `POST /api/v1/career-intelligence/cold-email/regenerate-subject` — Regenerate compelling subject lines
- `GET /api/v1/careers` — Search O\*NET occupation taxonomy
- `POST /api/v1/career/skill-gap` — Generate skill gap report comparing profile to target role
- `POST /api/v1/career/goal` — Set primary occupational target goal

### 7.4 Personal Trainer & Roadmap
- `POST /api/v1/personal-trainer/investigate` — Generate customized multi-week training plan
- `GET /api/v1/personal-trainer/active` — Fetch current active training plan
- `GET /api/v1/personal-trainer/daily/{day_number}` — Fetch daily training view with carried-over tasks
- `PATCH /api/v1/personal-trainer/tasks/{task_id}` — Update task status (`completed`, `in_progress`, etc.)
- `POST /api/v1/personal-trainer/reschedule-today` — Dynamically reallocate workload for today
- `POST /api/v1/personal-trainer/days/{day_id}/review` — Submit 1-5 confidence rating
- `POST /api/v1/roadmap/generate` — Generate 5-phase career milestone roadmap
- `PUT /api/v1/roadmap/items/{id}/toggle` — Mark roadmap item complete/incomplete

### 7.5 Mock Interviews & Question Bank
- `POST /api/v1/interviews` — Initialize interview session (`role`, `difficulty`, `total_questions`)
- `GET /api/v1/interviews/{id}` — Fetch session state and current question
- `POST /api/v1/interviews/{id}/answer` — Submit answer text/voice transcript for 6-metric evaluation
- `GET /api/v1/interviews/{id}/results` — Fetch final report with metric radar averages
- `GET /api/v1/questions` — Filter question bank by category, role, and difficulty
- `POST /api/v1/questions/generate` — Trigger AI generation of new practice questions

### 7.6 Coding Sandbox & Code Execution
- `GET /api/v1/coding/challenges` — List coding and SQL challenges
- `GET /api/v1/coding/challenges/{id_or_slug}` — Fetch challenge description, starter code, and test cases
- `POST /api/v1/coding/challenges/{id}/submit` — Execute code against sandbox test cases
- `POST /api/v1/coding/challenges/{id}/hint` — Request AI pedagogical hint without revealing full solution
- `POST /api/v1/coding/challenges/generate` — Synthesize new coding challenge on specified topic

### 7.7 Jobs & Analytics
- `GET /api/v1/jobs` — Search live Adzuna listings with local fallback cache
- `POST /api/v1/jobs/{id}/save` — Bookmark job listing
- `POST /api/v1/jobs/{job_id}/match` — Match current resume against specific job listing
- `GET /api/v1/job-market/search` — Retrieve aggregated market analytics (salaries, locations, skills)
- `GET /api/v1/performance` — Fetch longitudinal interview metrics and topic mastery
- `GET /api/v1/readiness` — Compute composite hiring readiness score

### 7.8 System & Administration
- `GET /api/v1/health` — Probes database and Ollama AI runtime status
- `GET /api/v1/admin/statistics` — Real database counts across all user activities
- `GET /api/v1/admin/users` — User management directory (role modification and deactivation)

---

## 8. Security Architecture & Operational Hardening

1. **Row-Level Tenant Isolation:**
   All read and write queries enforce `.where(Model.user_id == user.id)` preventing cross-user data leakage.
2. **Execution Sandboxing Safeguards:**
   Python code submitted by users is executed with `python -I -S` in an isolated temporary directory, enforcing a 3.0-second timeout and 10 KB maximum stdout capture. Subprocess calls are isolated from the FastAPI application thread.
3. **In-Memory SQL Isolation:**
   Candidate SQL queries execute in dedicated `:memory:` SQLite instances that are destroyed immediately after execution.
4. **Input Sanitization & Injection Prevention:**
   All database operations utilize SQLAlchemy parameterized statements, preventing SQL injection. File uploads are validated by MIME type and size (< 10 MB).
5. **CORS Defense-in-Depth:**
   The backend restricts origins to explicit developer origins and matches local network interfaces via regex (`r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"`).

---

## 9. Verification & Setup Instructions

### 9.1 Environment Prerequisites
- **Node.js:** v18+ (Tested on v24.11.1)
- **Python:** v3.10+ (Tested on v3.11.9)
- **Ollama (Optional but recommended):** Download from [ollama.com](https://ollama.com) and pull `llama3.2:3b`.

### 9.2 Launching the Application
- **Windows (1-Click):** Double-click `run.bat` or run `node scripts/run.js`.
- **macOS / Linux:** Execute `chmod +x run.sh && ./run.sh`.
- **Manual Launch:**
  - Backend: `cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
  - Frontend: `cd frontend && npm run dev`

### 9.3 Default Test Accounts
- **Candidate Demo:** `demo@example.com` / `Password123!`
- **Administrator Demo:** `admin@example.com` / `AdminPassword123!`
