# 🚀 Placement AI — Comprehensive AI Career, Resume & Interview Coach

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5.3-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4.1-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black.svg?style=flat&logo=ollama&logoColor=white)](https://ollama.ai)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Pytest](https://img.shields.io/badge/Pytest-121_Passed-brightgreen.svg?style=flat&logo=pytest&logoColor=white)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)](LICENSE)

An enterprise-grade, end-to-end **AI Career Coaching, Resume Analysis, Job Matching, Mock Interview, and Placement Readiness Platform**. Built with **FastAPI**, **React 18 (TypeScript)**, **SQLAlchemy 2.0 Async**, and local offline **Ollama LLM** inference.

---

## 📑 Table of Contents
1. [🌟 Executive Overview](#-executive-overview)
2. [🏗️ System Architecture](#️-system-architecture)
3. [✨ Key Features & Modules](#-key-features--modules)
4. [🛠️ Technology Stack](#️-technology-stack)
5. [📂 Project Directory Structure](#-project-directory-structure)
6. [📊 Database Schema & Entities](#-database-schema--entities)
7. [⚙️ Installation & Getting Started](#️-installation--getting-started)
8. [🔐 Environment Variables Reference](#-environment-variables-reference)
9. [🌐 API Endpoints Reference](#-api-endpoints-reference)
10. [🧪 Testing & Quality Assurance](#-testing--quality-assurance)
11. [📧 Email & SMTP Notifications](#-email--smtp-notifications)
12. [🔒 Security, Sandboxing & Isolation](#-security-sandboxing--isolation)
13. [❓ Troubleshooting & FAQ](#-troubleshooting--faq)
14. [📜 License](#-license)

---

## 🌟 Executive Overview

**Placement AI** bridges the gap between academic preparation and industry placement by providing candidates with personalized, transparent, and actionable AI-driven mentorship:
- **Zero Hallucination Scoring**: Transparent breakdowns for ATS scoring, interview rubrics, and placement readiness based on deterministic data models.
- **Privacy First (Local LLM)**: Operates with local **Ollama** LLMs (`llama3.2:3b`, `llama3`, `mistral`), ensuring that candidate resumes, speech recordings, and coding submissions remain private and fast without API token costs.
- **Actionable Execution**: Rather than giving generic advice, the system decomposes goals into daily hands-on tasks, generates tailored code architectures for portfolio projects, runs real-time in-browser code sandboxes, and matches resumes against live job openings.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND CLIENT (React 18 + TS)                     │
│  Vite SPA • Tailwind CSS • Lucide Icons • Web Speech API • Pyodide WASM │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP REST / JSON (Axios)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       BACKEND API (FastAPI + Python)                    │
│  FastAPI Router • JWT Auth Guard • CORS Middleware • Async Pydantic v2  │
├────────────────────────────────────┬────────────────────────────────────┤
│           SERVICE LAYER            │          INTEGRATIONS LAYER        │
│  • Resume Analysis Service         │  • Ollama Local LLM Client         │
│  • Career Intelligence Matcher     │  • Adzuna Live Job Provider API    │
│  • Personal Trainer & Rollover     │  • Twice-Daily Email Scheduler     │
│  • Mock Interview Evaluation Engine│  • aiosmtplib (STARTTLS & Direct)  │
│  • Project Recommendation Engine   │  • PDF/DOCX Parsing Engine         │
│  • In-Browser Coding Challenge     │                                    │
└──────────────────┬─────────────────┴──────────────────┬─────────────────┘
                   │                                    │
                   ▼                                    ▼
┌─────────────────────────────────────┐  ┌────────────────────────────────┐
│      DATABASE & REPOSITORY LAYER     │  │        LOCAL AI RUNTIME        │
│  PostgreSQL / SQLite (Async Engine) │  │  Ollama Engine (llama3.2:3b)   │
│  SQLAlchemy 2.0 • 42 Schema Tables  │  │  Prompt Optimization & Fallback│
└─────────────────────────────────────┘  └────────────────────────────────┘
```

---

## ✨ Key Features & Modules

### 1. 📄 Resume Studio & Transparent ATS Scoring
- **Multi-Format Parsing**: Secure upload and text extraction from `.pdf` and `.docx` documents.
- **5-Dimension ATS Breakdown**:
  - **Structure (20%)**: Section order, contact info, professional summary.
  - **Skills Match (30%)**: Extraction of technical, soft, and tool skills.
  - **Experience Impact (25%)**: Action verbs, quantifiable metrics, work history.
  - **Education (15%)**: Degrees, universities, graduation years.
  - **Formatting & Grammar (10%)**: Length, readability, clean typography.
- **Actionable Explanations**: Instant itemized lists of **Key Strengths**, **Areas for Improvement**, and **Formatting Suggestions** with smart semantic fallback recovery.
- **Version Comparison**: Side-by-side ATS score diffs across resume uploads over time.

### 2. 🧠 Career Intelligence & JD Matcher
- **Job Description Analyzer**: Paste external job postings from LinkedIn, Indeed, or company career sites to extract required skills, qualifications, and core responsibilities.
- **Resume → JD Matcher**: Calculates alignment score (0–100%) and highlights missing keywords/skills needed to pass recruiter filters.
- **Cover Letter Generator**: Creates compelling, customized cover letters tuned specifically for the target company and role.
- **Cold Email Generator**: Generates concise, high-converting outreach emails for hiring managers and recruiters.

### 3. 🎙️ AI Mock Interview System (Text & Speech)
- **Role & Difficulty Targeting**: Choose roles (Software Engineer, Backend, Frontend, Full Stack) and levels (Entry, Mid, Senior).
- **Audio Speech Input (Voice)**: Integrated browser Speech-to-Text (`webkitSpeechRecognition`) for hands-free speaking practice with automatic fallback to text typing.
- **Multi-Category Focus**: Technical, Behavioral (STAR method), and HR interview modes.
- **Instant Rubric Evaluation**: Every answer receives turn-by-turn transparent scoring across **Relevance**, **Technical Correctness**, and **Communication Clarity**, followed by an **Ideal Answer Model** and coaching tips.

### 4. 🧠 Personal Trainer (Module 15)
- **Customized Learning Schedules**: Generates structured, day-by-day learning curriculums tailored to user goal dimensions (Role, Company, or Skill) and available daily study hours.
- **Structured Daily Workloads**: Each day is broken down into structured **Theory**, **Practice**, and **Project** tasks with estimated durations.
- **Adaptive Workload Rescheduling**: If a candidate only has 45 minutes today, the engine reschedules workloads without losing streak momentum.
- **Automated Morning & Evening Briefings**: Morning agenda emails and evening progress check-ins sent automatically via SMTP.

### 5. 🚀 AI Portfolio Project Recommendations
- **Gap-Targeted Projects**: Generates **4 to 6 complete project architectures** customized to close candidate skill gaps.
- **Multi-Tier Difficulty**: Covers Beginner, Intermediate, and Advanced project tiers.
- **Complete Blueprints**: Tech stack breakdown, core architecture, key features to build, and resume bullet points.
- **Interactive Tracking**: Status buttons (**Saved**, **In Progress**, **Completed**).

### 6. 💻 In-Browser Coding Challenge Sandbox
- **Language Support**: Python 3.11 & SQLite challenges.
- **Safe Sandboxing**: Client-side execution in WebAssembly (Pyodide & SQLite WASM) with zero server security risk and memory/CPU limits.
- **Automated Test Runners**: Instant test verification with output logs, execution duration, and AI hints.

### 7. 💼 Live Jobs Hub & Match Engine
- **Live Search**: Integrated with **Adzuna Job API** for live job market search by keyword and location, with a **Remote Only** toggle.
- **One-Click Resume Alignment**: Compares the user's active resume against any live posting.
- **Direct Application**: Jump straight to employer application portals.

### 8. 🏢 Company-Specific Interview Preparation
- **Company Blueprints**: Tailored preparation for top tier companies (Google, Amazon, Microsoft, Meta, Adobe, etc.).
- **Strategy & Competency Breakdown**: System architecture priorities, behavioral leadership principles, and curated question sets.

### 9. 📈 Placement Readiness & Analytics
- **Readiness Formula**: Weighted metric combining Resume ATS Score, Skill Gap Coverage, Interview Performance, and Coding Challenge mastery.
- **Radar & Progress Visualizations**: Skill radar charts, historical performance curves, and milestone tracking.

### 10. 💬 Floating AI Platform Coach (Chatbot)
- **Instant Guidance**: Floating in the bottom-right corner with a live status beacon.
- **Comprehensive Knowledge Base**: Answers platform FAQs (ATS score checking, job applications, profile setup, interview tips).
- **One-Click Deep Links**: Direct shortcuts to platform features.

---

## 🛠️ Technology Stack

| Layer | Technology | Description |
|---|---|---|
| **Frontend Framework** | React 18.3.1 | Single-Page Application (SPA) with TypeScript |
| **Build Tool** | Vite 8.2 | Ultra-fast HMR and production asset bundling |
| **Styling** | Tailwind CSS v3 | Modern glassmorphism, responsive dark-slate design |
| **Icons & UI** | Lucide React | Lightweight vector icons |
| **Client Execution** | Pyodide & SQLite WASM | Sandboxed in-browser code execution |
| **Backend Framework** | FastAPI 0.110.0 | High-performance async REST API with Python 3.11+ |
| **Validation & Schema** | Pydantic v2.6.4 | Strict data validation and typing |
| **ORM & Database** | SQLAlchemy 2.0 (Async) | Async database driver with SQLite / PostgreSQL support |
| **Database Migrations** | Alembic 1.13.1 | Schema versioning and migration engine |
| **AI LLM Inference** | Ollama (`llama3.2:3b`) | Offline, local AI model execution |
| **Job Market API** | Adzuna Provider API | Live job feed integration |
| **Email Transport** | aiosmtplib | Async SMTP client supporting Mailtrap & Gmail (STARTTLS/SSL) |
| **Test Suite** | Pytest & pytest-asyncio | 121 unit & integration tests (100% passing) |

---

## 📂 Project Directory Structure

```
Major_Project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                    # Auth & DB session dependencies
│   │   │   └── v1/                        # API route controllers
│   │   │       ├── auth.py                # Registration, Login, JWT tokens
│   │   │       ├── resumes.py             # Resume upload, delete, download
│   │   │       ├── resume_analysis.py     # ATS scoring & AI evaluations
│   │   │       ├── career_intelligence.py # JD analyzer, Cover letter & Cold email
│   │   │       ├── personal_trainer.py    # Daily learning plan endpoints
│   │   │       ├── interviews.py          # AI mock interview session manager
│   │   │       ├── projects.py            # Project recommendations & tracking
│   │   │       ├── coding.py              # Coding sandbox submission runner
│   │   │       ├── jobs.py                # Live job search & saving
│   │   │       ├── company_prep.py        # Company-specific prep studio
│   │   │       ├── questions.py           # Question bank & bookmarks
│   │   │       ├── dashboard.py           # Placement readiness aggregation
│   │   │       ├── notifications.py       # Notifications & preferences
│   │   │       ├── performance.py         # Analytics & radar metrics
│   │   │       ├── roadmap.py             # Career roadmaps & milestones
│   │   │       └── admin.py               # Admin telemetry & user management
│   │   ├── core/
│   │   │   ├── config.py                  # Pydantic Settings & .env loading
│   │   │   ├── database.py                # Async engine & session factory
│   │   │   ├── scheduler.py               # Twice-daily email scheduler
│   │   │   └── security.py                # Password hashing & JWT creation
│   │   ├── integrations/
│   │   │   ├── ai/ollama.py               # Ollama local LLM integration
│   │   │   └── jobs/adzuna.py             # Adzuna Live Job Provider
│   │   ├── models/                        # SQLAlchemy database models (42 tables)
│   │   ├── schemas/                       # Pydantic request/response schemas
│   │   └── services/                      # Business logic & algorithms
│   │       ├── resume_analysis_service.py # ATS scoring & prompt engineering
│   │       ├── personal_trainer_service.py# Decompose goals into daily tasks
│   │       ├── project_service.py         # Multi-tiered project generation
│   │       ├── email_service.py           # Async HTML email dispatch
│   │       └── interview_service.py       # Turn-by-turn rubric evaluation
│   ├── scripts/
│   │   ├── seed_data.py                   # Initial database seeding
│   │   └── test_smtp.py                   # SMTP diagnostic verification script
│   ├── tests/                             # Pytest automated test suite (121 tests)
│   ├── requirements.txt                   # Python package dependencies
│   ├── pytest.ini                         # Pytest configuration
│   └── career_coach.db                    # SQLite primary database
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   └── PlatformHelpChatbot.tsx# Floating interactive AI coach
│   │   │   ├── layout/
│   │   │   │   ├── Navbar.tsx             # Slide-over sidebar drawer & top nav
│   │   │   │   ├── Footer.tsx             # Platform footer
│   │   │   │   └── Layout.tsx             # Root layout wrapper
│   │   │   └── ui/                        # Reusable UI component library
│   │   ├── pages/                         # Route page views
│   │   │   ├── Dashboard.tsx              # Placement readiness dashboard
│   │   │   ├── ResumeAnalysis.tsx         # ATS score breakdown & details
│   │   │   ├── Resumes.tsx                # Resume management & upload
│   │   │   ├── CareerIntelligence.tsx     # JD analyzer, Matcher, Cover Letter
│   │   │   ├── PersonalTrainer.tsx        # Daily learning plan & reschedule
│   │   │   ├── MockInterview.tsx          # Speech & text AI interview runner
│   │   │   ├── ProjectRecommendations.tsx # AI portfolio project ideas
│   │   │   ├── CodingPractice.tsx         # In-browser challenge sandbox
│   │   │   ├── Jobs.tsx                   # Live job search & match
│   │   │   ├── CompanyPrep.tsx            # Company-specific studio
│   │   │   ├── QuestionBank.tsx           # Categorized interview questions
│   │   │   ├── CareerRoadmap.tsx          # Phase milestone roadmap
│   │   │   ├── LearningHub.tsx            # Verified courses & docs
│   │   │   ├── PerformanceAnalytics.tsx   # Score progression & radar charts
│   │   │   ├── Profile.tsx                # Candidate profile management
│   │   │   ├── Achievements.tsx           # Badges & trophy showcase
│   │   │   ├── Notifications.tsx          # Inbox & alert preferences
│   │   │   └── AdminDashboard.tsx         # Governance & telemetry panel
│   │   ├── lib/
│   │   │   └── api.ts                     # Axios client & API endpoints
│   │   └── App.tsx                        # React Router configuration
│   ├── package.json                       # Node dependencies
│   ├── tailwind.config.js                 # Tailwind CSS theme configuration
│   └── vite.config.ts                     # Vite build configuration
├── .env                                   # Root environment variables template
└── README.md                              # Professional Documentation
```

---

## 📊 Database Schema & Entities

The system manages **42 relational tables** with foreign key constraints, indexes, and user isolation:

```
[Users] (id, email, password_hash, role, is_active)
   ├── [Profiles] (target_role, degree, graduation_year, bio)
   ├── [Resumes] (file_name, file_size, raw_text, version)
   │      └── [ResumeAnalysis] (overall_score, structure_score, skills_score, strengths, improvements)
   │             └── [ResumeSkills] (skill_name, category, proficiency)
   ├── [TrainingPlans] (title, target_role, daily_hours, overall_progress)
   │      └── [TrainingDays] (day_number, objective, workload_minutes)
   │             └── [TrainingTasks] (title, task_type, estimated_minutes, status, time_spent)
   ├── [InterviewSessions] (role, difficulty, overall_score, summary)
   │      └── [InterviewQuestions] (question_text, category, order_index)
   │             └── [InterviewAnswers] (user_answer, relevance_score, clarity_score, feedback)
   ├── [ProjectRecommendations] (title, difficulty, tech_stack, deliverables, status)
   ├── [CodingSubmissions] (challenge_id, code, language, is_passed, runtime_ms)
   ├── [SavedJobs] (job_id, title, company, match_score)
   ├── [UserAchievements] (achievement_id, unlocked_at)
   └── [Notifications] (title, message, is_read, link_url)
```

---

## ⚙️ Installation & Getting Started

### ⚡ Method 1: Instant 1-Click Launch (Recommended)

- **On Windows**: Double-click **`run.bat`** (or `start.bat`) in the root folder.
- **On macOS / Linux**: Run `./run.sh` in the terminal (`chmod +x run.sh` if needed).
- **Or with npm (Any OS)**: Run `npm start` in the root folder.

> **This automatically:**
> 1. Verifies Python 3 and Node.js.
> 2. Auto-installs missing dependencies (`npm install` & pip requirements).
> 3. Auto-initializes the SQLite database and seeds verified jobs, challenges, and demo user accounts.
> 4. Launches both Backend (`http://127.0.0.1:8000`) and Frontend (`http://localhost:5173`).
> 5. Automatically opens your browser to `http://localhost:5173`!

---

### 🔑 Instant Demo Accounts (Zero Registration Needed)

On the login page, you can use the **1-Click Quick Demo Logins** or use these credentials:

| Role | Email | Password |
|---|---|---|
| **Candidate Demo** | `demo@example.com` | `Password123!` |
| **System Admin** | `admin@example.com` | `AdminPassword123!` |

*(Or register a new account on `/register`)*

---

### 🛠️ Method 2: Manual Terminal Launch (Optional)

If you prefer starting backend and frontend in separate terminal windows:

#### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies (optionally in a virtual environment)
pip install -r requirements.txt

# Start FastAPI server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend is now running at **`http://127.0.0.1:8000`** (Swagger docs available at **`http://127.0.0.1:8000/docs`**).

#### 2. Frontend Setup
```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```
Frontend is now live at **`http://localhost:5173/`**.

---

## 🔐 Environment Variables Reference

Create a `.env` file in the root and in the `backend/` directory:

| Variable | Default Value | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./career_coach.db` | Async database connection URI |
| `DATABASE_URL_SYNC` | `sqlite:///./career_coach.db` | Sync database connection URI (migrations) |
| `JWT_SECRET` | `your-secret-key` | Secret key for signing JWT auth tokens |
| `JWT_ALGORITHM` | `HS256` | Token hashing algorithm |
| `JWT_EXPIRATION_MINUTES` | `30` | Access token lifespan |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama local server address |
| `OLLAMA_MODEL` | `llama3.2:3b` | Target LLM model name |
| `ADZUNA_APP_ID` | `3510f190` | Adzuna Live Job Provider App ID |
| `ADZUNA_APP_KEY` | `6c8f1f8090a309a90dff9d3e4cc69e97` | Adzuna Live Job Provider App Key |
| `ADZUNA_COUNTRY` | `in` | Default search country (`in`, `us`, `gb`) |
| `SMTP_ENABLED` | `true` | Enable/disable outgoing SMTP email |
| `SMTP_HOST` | `sandbox.smtp.mailtrap.io` | SMTP server host (`smtp.gmail.com` for Gmail) |
| `SMTP_PORT` | `587` | SMTP port (`587` for STARTTLS, `465` for SSL) |
| `SMTP_USER` | `977a6e0a7d13df` | SMTP username or Gmail address |
| `SMTP_PASSWORD` | `8aa0814d45b9fd` | SMTP password or 16-char Google App Password |
| `SMTP_FROM_NAME` | `CareerCoachAI` | Display name on outgoing emails |
| `REMINDER_MORNING_TIME` | `07:00` | Morning briefing trigger time (HH:MM) |
| `REMINDER_EVENING_TIME` | `20:00` | Evening check-in trigger time (HH:MM) |
| `REMINDER_TIMEZONE` | `Asia/Kolkata` | Scheduler timezone |

---

## 🌐 API Endpoints Reference

### Authentication & Profile
- `POST /api/v1/auth/register` — Create candidate account
- `POST /api/v1/auth/login` — Authenticate and receive JWT
- `GET /api/v1/auth/me` — Retrieve active authenticated session
- `GET /api/v1/profile` — Fetch profile details and target role
- `PUT /api/v1/profile` — Update education, skills, and goals

### Resume Studio & ATS
- `GET /api/v1/resumes` — List uploaded resume versions
- `POST /api/v1/resumes/upload` — Upload `.pdf` or `.docx` resume
- `POST /api/v1/resumes/{id}/analyze` — Run/refresh ATS scoring engine (`?force=true`)
- `GET /api/v1/resumes/{id}/analysis` — Retrieve ATS score breakdown
- `DELETE /api/v1/resumes/{id}` — Delete resume document

### Career Intelligence
- `POST /api/v1/career-intelligence/analyze-jd` — Extract required skills from external JD
- `POST /api/v1/career-intelligence/match-resume` — Calculate Resume → JD alignment score
- `POST /api/v1/career-intelligence/generate-cover-letter` — Generate tailored cover letter
- `POST /api/v1/career-intelligence/generate-cold-email` — Generate recruiter outreach email

### Personal Trainer (Module 15)
- `POST /api/v1/personal-trainer/investigate` — Create custom day-by-day learning plan
- `GET /api/v1/personal-trainer/active` — Get active training plan and progress
- `GET /api/v1/personal-trainer/daily/{day_number}` — Get day agenda and tasks
- `PATCH /api/v1/personal-trainer/tasks/{task_id}` — Update task completion status
- `POST /api/v1/personal-trainer/reschedule-today` — Reschedule workload to fit available time
- `POST /api/v1/personal-trainer/days/{day_id}/review` — Submit confidence score review

### Mock Interview Studio
- `POST /api/v1/interviews/start` — Start new interactive interview session
- `GET /api/v1/interviews/{id}` — Retrieve session progress and questions
- `POST /api/v1/interviews/{id}/answer` — Submit voice/text answer for AI rubric grading
- `GET /api/v1/interviews/{id}/results` — Get final interview evaluation summary

### Coding Practice & Sandboxing
- `GET /api/v1/coding/challenges` — List challenges (Python, SQL, DSA)
- `GET /api/v1/coding/challenges/{id}` — Challenge description, starter code, test cases
- `POST /api/v1/coding/challenges/{id}/submit` — Record challenge submission
- `POST /api/v1/coding/challenges/{id}/hint` — Request contextual AI coding hint

### Projects & Jobs
- `POST /api/v1/projects/recommendations` — Generate customized portfolio projects
- `GET /api/v1/projects/recommendations` — List project recommendations
- `PATCH /api/v1/projects/recommendations/{id}/status` — Update project execution status
- `GET /api/v1/jobs/search` — Search live job market with resume match score

---

## 🧪 Testing & Quality Assurance

### 1. Automated Backend Unit & Integration Tests (121/121 Passed)
```bash
cd backend
pytest -v
```
**Test Coverage Includes:**
- JWT Authentication & Role Governance (`tests/test_auth.py`, `tests/test_admin.py`)
- Resume Upload, Parsing & ATS Engine (`tests/test_resumes.py`, `tests/test_resume_analysis.py`)
- Career Intelligence & JD Extraction (`tests/test_career_intelligence.py`)
- Personal Trainer & Rollover Scheduling (`tests/test_personal_trainer.py`, `tests/test_email_scheduler.py`)
- AI Mock Interview Engine & Turn-by-Turn Rubrics (`tests/test_interviews.py`)
- Project Recommendation Engine (`tests/test_projects.py`)
- Coding Sandbox Execution (`tests/test_coding.py`)
- Offline AI Fallbacks & Ollama Integration (`tests/test_ollama.py`)

### 2. Frontend Production Build & TypeScript Verification
```bash
cd frontend
npm run build
```
Validates strict type-checking (`tsc -b`) and ensures 0 bundle errors.

### 3. SMTP Verification Diagnostic
```bash
cd backend
python scripts/test_smtp.py your_email@gmail.com
```
Validates SMTP credentials and tests instant email delivery.

---

## 📧 Email & SMTP Notifications

The platform includes an automated email dispatch engine for:
1. **Real-Time Task Completion Alerts**: Sent instantly when a learning task is marked complete.
2. **Morning Daily Briefings (7:00 AM)**: Daily goals, planned workload, and yesterday's recap.
3. **Evening Progress Wrap-Ups (8:00 PM)**: Summary of tasks accomplished and evening streaks.

### Delivery Modes:
- **Mailtrap Sandbox (Default)**: Catches all emails in the developer inbox at `https://mailtrap.io/inboxes`.
- **Real Gmail Inbox**: To receive emails directly in your personal Gmail, configure Google App Passwords in `.env`:
  ```env
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=your_email@gmail.com
  SMTP_PASSWORD=your_16_char_google_app_password
  ```

---

## 🔒 Security, Sandboxing & Isolation

1. **Candidate Data Isolation**: All database queries enforce strict user ID filtering, preventing cross-tenant access.
2. **Secure Passwords & Stateless Auth**: Passwords hashed using industry-standard `bcrypt`. Stateless JWT authentication with role-based authorization guards.
3. **Sandboxed Code Execution**: User code in the Coding Challenge module runs in client-side WebAssembly sandboxes (Pyodide & SQLite WASM), ensuring zero server-side remote code execution vulnerability.
4. **Input Sanitization & Prompt Defense**: All external job descriptions and resumes undergo strict text sanitization before processing by the LLM.

---

## ❓ Troubleshooting & FAQ

**Q: Why does Resume Analysis or Project Generation take a few seconds?**  
A: Generations use the local Ollama LLM (`llama3.2:3b`) on your machine. Ensure Ollama is running (`ollama serve`). If Ollama is temporarily offline, the system automatically uses built-in heuristic semantic generators so the UI never breaks.

**Q: How do I test email notifications without configuring Gmail?**  
A: The default `.env` is pre-configured with Mailtrap credentials. When you complete tasks, visit [https://mailtrap.io/inboxes](https://mailtrap.io/inboxes) to view the rendered HTML emails.

**Q: Can I use a different Ollama model?**  
A: Yes! You can set `OLLAMA_MODEL=llama3:8b` or `mistral:7b` in `backend/.env`.

---

## 📜 License
This project is licensed under the **MIT License** — open source and free for educational and commercial adaptation.

---
*Built with ❤️ for candidate empowerment and placement excellence.*
