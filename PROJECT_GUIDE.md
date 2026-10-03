# Placement AI — Complete Project Guide (Learn the Whole System Without Opening the Code)

This is a single reference that teaches the entire project: what it is, how it is built,
how every piece fits together, and how each feature works end‑to‑end (data → API → service →
AI → database → UI). Read this top to bottom and you will understand the project as well as
someone who wrote it.

> Scope note: this guide is written from the **actual source code**, not just the README.
> Where the README claims something the code does not do, this guide says so in
> **"Reality check"** callouts.

---

## Table of Contents

1. [What the product is](#1-what-the-product-is)
2. [Technology stack (as actually used)](#2-technology-stack-as-actually-used)
3. [Repository structure — every folder explained](#3-repository-structure--every-folder-explained)
4. [How to run it](#4-how-to-run-it)
5. [Cross‑cutting architecture (the patterns every feature reuses)](#5-cross-cutting-architecture)
6. [The AI layer in depth (Ollama, caching, fallback, JSON repair)](#6-the-ai-layer-in-depth)
7. [Authentication & authorization end‑to‑end](#7-authentication--authorization-end-to-end)
8. [The database model (all tables, grouped by domain)](#8-the-database-model)
9. [Feature deep‑dives](#9-feature-deep-dives) — one section per module
10. [Frontend architecture](#10-frontend-architecture)
11. [Background scheduler & email system](#11-background-scheduler--email-system)
12. [Testing](#12-testing)
13. [README vs. code — known inconsistencies](#13-readme-vs-code--known-inconsistencies)
14. [Recipe: how to add a new feature module](#14-recipe-how-to-add-a-new-feature-module)
15. [Quick glossary](#15-quick-glossary)

---

## 1. What the product is

**Placement AI** (internal names also seen: "AI Career & Interview Coach", "CareerCoachAI",
"Career Coach") is a full‑stack web application that helps a job candidate (typically a
student preparing for campus/industry placement) get "job ready". It bundles ~20 feature
modules around one candidate profile:

| Theme | Modules |
|---|---|
| **Resume** | Resume Studio (upload, versioning, download), Transparent ATS Analysis, Version comparison |
| **Targeting a role** | Careers directory (O*NET), Skill Gap report, Career Roadmap (5 phases) |
| **Applying** | Career Intelligence (JD analyzer, Resume→JD match, Cover Letter, Cold Email), Live Jobs Hub, Job→Resume match, Job Market Analyzer |
| **Interview prep** | AI Mock Interview (text + voice, 6‑metric rubric), Question Bank, Company‑specific Prep |
| **Skill building** | Personal Trainer (day‑by‑day plan + adaptive rollover + emails), Coding Challenges sandbox, Learning Resources catalog, AI Project Recommendations |
| **Feedback loop** | Dashboard, Performance Analytics, Placement Readiness score, Achievements/Badges, In‑app Notifications, Floating Help Chatbot |
| **Ops** | Admin panel (stats, users, question bank, learning resources) |

**Design philosophy (important — it explains 80% of the code):**

- **"Deterministic math + AI narration."** Scores are computed by explicit Python formulas
  (weighted rubrics, keyword overlap ratios). The local LLM is only asked to *explain*,
  *extract*, or *generate prose* — never to be the source of truth for a number. This makes
  scoring reproducible and "hallucination‑free".
- **Local, offline AI.** All generative AI goes to a local **Ollama** server
  (`llama3` / `llama3.2:3b` / `mistral`). No cloud API keys, no per‑token cost, candidate
  data never leaves the machine.
- **Always degrade gracefully.** Every AI call is wrapped so that if Ollama is down or
  returns junk, a **deterministic fallback generator** produces a sensible result and the UI
  never breaks.
- **Strict per‑user isolation.** Every query filters by `user_id`. Users can only ever see
  their own rows.

---

## 2. Technology stack (as actually used)

### Backend (`/backend`)

| Concern | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | |
| Web framework | **FastAPI** (`0.115.*` in `requirements.txt`; README says 0.110) | app factory in `app/main.py` |
| ASGI server | Uvicorn (`uvicorn[standard] 0.32.*`) | |
| ORM | **SQLAlchemy 2.0 async** (`sqlalchemy[asyncio] 2.0.*`) | `Mapped[...]` / `mapped_column` style |
| DB drivers | `aiosqlite` (dev), `asyncpg` + `psycopg2-binary` (Postgres) | |
| Migrations | **Alembic** (`1.14.*`) — one migration file exists (`001_...`), but in practice tables are auto‑created on startup via `Base.metadata.create_all` |
| Validation | **Pydantic v2** (`2.10.*`) + `pydantic-settings` | request/response schemas in `app/schemas` |
| HTTP client | **httpx** (`0.28.*`) — talks to Ollama and Adzuna |
| Auth | `python-jose[cryptography]` (JWT, HS256) + `passlib[bcrypt]` (password hashing) |
| File uploads | `python-multipart`; **PyMuPDF (`fitz`)** for PDF text, **`python-docx`** for DOCX |
| Email | **`aiosmtplib`** (async SMTP, STARTTLS/SSL) |
| Scheduling | **APScheduler** (`3.11.*`) — `AsyncIOScheduler` with two cron jobs |
| Tests | `pytest` + `pytest-asyncio`, in‑memory SQLite |
| Local LLM | **Ollama** over HTTP (`/api/generate`, `/api/tags`) |
| External job data | **Adzuna** public job API |
| Career taxonomy | **O*NET**‑style dataset, hard‑coded in `app/integrations/careers/onet.py` |

> Note: `fitz` (PyMuPDF) and `python-docx` are imported by `resume_parser.py` but are **not**
> listed in `requirements.txt`. They must be installed separately (`pip install pymupdf python-docx`).

### Frontend (`/frontend`)

| Concern | Choice | Notes |
|---|---|---|
| Framework | **React 19** (`package.json` says `react ^19.2`; README badge says 18.3) | |
| Language | **TypeScript ~6.0** | strict build via `tsc -b` |
| Build tool | **Vite 8** | dev server on `:5173`, host `0.0.0.0` |
| Routing | **react-router-dom v7** | all routes in `src/App.tsx` |
| Styling | **Tailwind CSS v3** (+ PostCSS + autoprefixer) | dark "surface/brand" palette, glassmorphism |
| State | React Context (`AuthContext`) + local component state + `localStorage` for token | no Redux/Zustand/React Query |
| HTTP | hand‑rolled `fetch` wrapper in `src/lib/api.ts` | |
| Icons | inline SVG + emoji (no icon library bundled) | README mentions Lucide; not in `package.json` |
| Lint | `oxlint` | |
| Code editor for challenges | plain `<textarea>` (no Monaco/CodeMirror) | |
| Voice | Browser **Web Speech API** (`SpeechRecognition` + `speechSynthesis`) via `useVoiceInterview` hook |

### Infra

- `docker-compose.yml`: 3 services — `db` (Postgres 16), `backend` (FastAPI, runs
  `alembic upgrade head` then uvicorn), `frontend` (Vite dev server). Backend talks to a
  host Ollama via `host.docker.internal:11434`.
- Local dev without Docker uses **SQLite** file `backend/career_coach.db`.

---

## 3. Repository structure — every folder explained

```
Major_Project/
├── .env / .env.example          # Root env (docker-compose reads .env). Postgres + Ollama + SMTP + Adzuna
├── docker-compose.yml           # db + backend + frontend
├── README.md                    # Marketing-flavored doc (see §13 for inaccuracies)
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── alembic.ini, alembic/    # Migration config + env.py + versions/001_create_users_and_profiles.py
│   ├── career_coach.db          # committed SQLite dev database
│   ├── scripts/test_smtp.py     # standalone SMTP credential checker
│   ├── uploads/resumes/user_<id>/…   # uploaded resume files on disk (many committed sample PDFs/DOCX)
│   │
│   └── app/
│       ├── main.py              # FastAPI app factory + lifespan (startup/shutdown)
│       │
│       ├── core/
│       │   ├── config.py        # Pydantic Settings singleton `settings` (reads .env)
│       │   ├── security.py      # bcrypt hash/verify, JWT encode/decode, reset-token gen
│       │   ├── exceptions.py    # AppException + global exception handlers → {status,message,details}
│       │   ├── logging.py       # logging setup
│       │   └── scheduler.py     # APScheduler: morning + evening reminder cron jobs
│       │
│       ├── db/
│       │   ├── base.py          # DeclarativeBase `Base`
│       │   └── session.py       # async engine, async_session_factory, get_async_session()
│       │
│       ├── api/
│       │   ├── deps.py          # get_db, get_current_user, get_current_admin_user
│       │   ├── router.py        # mounts every v1 sub-router under /api/v1
│       │   └── v1/*.py          # one thin controller file per feature (auth, resumes, coding, …)
│       │
│       ├── models/*.py          # SQLAlchemy ORM tables (one file per domain), aggregated in __init__.py
│       ├── schemas/*.py         # Pydantic request/response models (one file per domain)
│       │
│       ├── services/*.py        # ALL business logic + algorithms + AI prompts live here
│       │
│       └── integrations/
│           ├── ai/
│           │   ├── base.py      # AIProvider abstract class
│           │   ├── ollama.py    # OllamaProvider: HTTP client, LRU+TTL cache, warmup, model fallback
│           │   └── json_utils.py# robust "extract JSON out of messy LLM text" + repair truncated JSON
│           ├── jobs/
│           │   ├── base.py      # JobProvider abstract + NormalizedJobData schema
│           │   └── adzuna.py    # AdzunaJobProvider (real HTTP calls to Adzuna)
│           └── careers/
│               ├── base.py      # CareerDataProvider abstract + OccupationData / CareerSkillData
│               └── onet.py      # ONET_DATASET (8 hard-coded occupations w/ weighted skills)
│
└── frontend/
    ├── index.html, vite.config.ts, tailwind.config.js, postcss.config.js, tsconfig*.json
    ├── package.json
    ├── public/ (favicon.svg, icons.svg)
    ├── dist/  (a committed production build)
    └── src/
        ├── main.tsx             # ReactDOM root
        ├── App.tsx              # <AuthProvider><BrowserRouter> + all <Route>s
        ├── index.css            # Tailwind directives + custom classes
        ├── lib/api.ts           # typed fetch client + ALL endpoint helper methods + TS interfaces
        ├── context/
        │   ├── auth-context-def.ts   # AuthContext + AuthContextType
        │   └── AuthContext.tsx       # AuthProvider (token in localStorage, /auth/me on load)
        ├── hooks/
        │   ├── useAuth.ts            # useContext(AuthContext)
        │   ├── useHealthCheck.ts     # polls /api/v1/health
        │   └── useVoiceInterview.ts  # Web Speech API wrapper (TTS + STT)
        ├── components/
        │   ├── auth/ProtectedRoute.tsx
        │   ├── layout/{Layout,Navbar,Footer}.tsx
        │   ├── dashboard/{StatCard,WelcomeBanner,RecentActivityList}.tsx
        │   ├── ui/{LoadingSpinner,AILoadingState,ErrorBoundary}.tsx
        │   └── chat/PlatformHelpChatbot.tsx   # floating help widget
        └── pages/*.tsx          # one page component per route (+ pages/admin/*)
```

### The "5‑file pattern" per feature

Almost every feature is implemented as the same 5 layers. Once you know one, you know them all:

```
frontend/src/pages/<Feature>.tsx      →  UI + calls api.<method>()
frontend/src/lib/api.ts               →  api.<method>()  = fetch(`/api/v1/<feature>/…`)
backend/app/api/v1/<feature>.py       →  @router path, auth dependency, calls service
backend/app/services/<feature>_service.py →  the real logic: DB queries, scoring math, LLM prompt, fallback
backend/app/models/<feature>.py       →  the tables it reads/writes
backend/app/schemas/<feature>.py      →  request/response shapes (Pydantic)
```

---

## 4. How to run it

### Prerequisites
- Python 3.11+, Node 20+, and **Ollama** running locally (`ollama serve`) with a model
  pulled: `ollama pull llama3.2:3b` (or `llama3`, `mistral`).
- The backend also needs `pip install pymupdf python-docx` (see stack note above).

### Backend (SQLite, no Docker)
```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
pip install pymupdf python-docx  # not in requirements.txt but imported by resume_parser
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API root: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs` (only when `DEBUG=true`)
- On startup the app: creates all tables, seeds ~30 verified jobs + ~14 coding challenges,
  pre‑warms the Ollama model in the background, and starts the email scheduler (only if
  `SMTP_ENABLED=true`).

### Frontend
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```
`VITE_API_BASE_URL` (frontend `.env`) points at the backend; defaults to `http://localhost:8000`.

### Docker (Postgres)
```bash
docker compose up --build
```
Brings up Postgres + backend (`alembic upgrade head` then uvicorn) + frontend.

### Key environment variables (`backend/.env` or root `.env`)

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://…` (code default) / `sqlite+aiosqlite:///./career_coach.db` (README) | async DB URL used by the app |
| `DATABASE_URL_SYNC` | matching sync URL | used by Alembic |
| `JWT_SECRET` / `JWT_ALGORITHM` / `JWT_EXPIRATION_MINUTES` | `change-me…` / `HS256` / `30` | access‑token signing |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `http://localhost:11434` / `llama3` | local LLM |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` / `ADZUNA_COUNTRY` | sample creds / `in` or `us` | live job search |
| `JOB_PROVIDER_API_ID/KEY/URL` | — | generic alias for Adzuna creds (checked first) |
| `SMTP_ENABLED` | `false` | master switch for ALL email + the scheduler |
| `SMTP_HOST/PORT/USER/PASSWORD/FROM_NAME` | Gmail defaults | SMTP transport |
| `REMINDER_MORNING_TIME` / `REMINDER_EVENING_TIME` / `REMINDER_TIMEZONE` | `07:00`/`08:00`, `20:00`, `Asia/Kolkata` | cron times for the two daily emails |
| `N8N_WEBHOOK_URL` | — | optional external webhook the Personal Trainer can POST progress to |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | allowed browser origins |
| `MAX_FILE_SIZE_BYTES` | 10 MB | resume upload cap |
| `UPLOAD_DIR` | `uploads` | where resume files are written |

---

## 5. Cross‑cutting architecture

### 5.1 Application startup (`app/main.py` → `lifespan`)

```
create_app():
  FastAPI(title, version, docs_url=/docs if DEBUG)
  add CORSMiddleware(allow_origins=settings.CORS_ORIGINS, credentials, all methods/headers)
  register_exception_handlers(app)          # see 5.4
  include_router(api_router)                 # prefix /api/v1

lifespan (on startup):
  setup_logging()
  Base.metadata.create_all                   # auto-create every table (no migration needed for dev)
  seed_verified_jobs_if_empty()              # ~30 curated tech jobs into `jobs`
  seed_standard_challenges_if_empty()        # ~14 coding challenges into `coding_challenges`
  asyncio.create_task(OllamaProvider().warmup())   # load model into VRAM, keep_alive 60m
  start_scheduler()                          # APScheduler morning+evening jobs (only if SMTP_ENABLED)

lifespan (on shutdown):
  stop_scheduler(); close shared httpx client; engine.dispose()
```

Other seed functions run lazily on first use inside services:
`seed_occupations_if_empty` (careers), `seed_standard_questions_if_empty` (question bank),
`ensure_system_achievements_seeded` (achievements), the learning‑resource catalog, etc.

### 5.2 Request lifecycle for a typical authenticated call

```
Browser
  └─ api.<method>()  →  fetch(`${VITE_API_BASE_URL}/api/v1/…`, {Authorization: Bearer <token>})
       └─ FastAPI route in app/api/v1/<feature>.py
            ├─ Depends(get_current_user)  → decode JWT → load User (must be active) → 401/403 otherwise
            ├─ Depends(get_db)            → yields an AsyncSession (rollback on error, close in finally)
            └─ calls app/services/<feature>_service.<fn>(db, user, request)
                 ├─ SQLAlchemy queries (always `.where(<Model>.user_id == user.id)`)
                 ├─ deterministic computation (scores, ratios, filters)
                 ├─ optional OllamaProvider().generate(prompt, format="json", options=…)
                 │     └─ on failure → deterministic fallback branch
                 ├─ writes ORM rows, `await db.commit()`
                 └─ returns a Pydantic response schema
       └─ route wraps it: APIEnvelope(status="success", message="…", data=<schema>)
Browser
  └─ response.json() → { status, data, message } → page renders `data`
```

### 5.3 The standard API envelope

Every successful response is:
```json
{ "status": "success", "message": "human sentence", "data": <the actual payload> }
```
Implemented by `APIEnvelope[T]` / `APIResponse[T]` generic Pydantic models
(`app/schemas/user.py`, `app/schemas/common.py`). The frontend `api.request<T>()` returns
`APIResponse<T>` and pages read `res.data`.

### 5.4 Error handling (`app/core/exceptions.py`)

- `AppException(message, status_code, details=None)` — the app's own exception. Services
  raise it for expected failures (`404 not found`, `400 bad input`, `503 Ollama down`,
  `502 bad AI output`).
- Global handlers convert **everything** to the same error envelope:
  `{ "status": "error", "message": "...", "details": ... }` with the right HTTP status.
  Handlers exist for `AppException`, `HTTPException`, `RequestValidationError` (→ 422), and a
  catch‑all `Exception` (→ 500 "Internal server error", full traceback logged).

### 5.5 Database access pattern

- `app/db/session.py` builds one async engine (`echo=DEBUG`; connection pool only when not
  SQLite) and an `async_sessionmaker` with `expire_on_commit=False`.
- `get_async_session()` yields a session, `rollback()` on exception, `close()` in `finally`.
- Models use SQLAlchemy 2.0 typed style. `JSON().with_variant(JSONB, "postgresql")` is used
  everywhere a list/dict column is needed (so the same models work on SQLite and Postgres).
- Relationships mostly use `lazy="selectin"` and `cascade="all, delete-orphan"` so deleting a
  parent (e.g. a `User`) cleans up children.

### 5.6 Configuration (`app/core/config.py`)

A single `Settings(BaseSettings)` instance named `settings` is imported everywhere. It reads
`.env`, `case_sensitive=False`, `extra="ignore"`. `CORS_ORIGINS` has a validator that accepts
a JSON array string **or** a comma‑separated string.

---

## 6. The AI layer in depth

Everything AI goes through **`app/integrations/ai/ollama.py`**. Understand this file and every
"AI feature" becomes obvious.

### 6.1 `OllamaProvider`

- `__init__(base_url, model, timeout=90s)` — defaults from `settings.OLLAMA_BASE_URL` /
  `OLLAMA_MODEL`.
- `health_check()` → GET `/api/tags`, returns bool. Used by `/api/v1/health` and by some
  services before they even try to generate.
- `warmup()` → POST `/api/generate` with `prompt:"ping"`, `num_predict:1`,
  `keep_alive:"60m"`. Called once at startup so the first real user request isn't slow.
- `get_available_models()` → parses `/api/tags`.
- `generate(prompt, **kwargs)` — the workhorse:
  1. **In‑memory cache check** (`LLMResponseCache`, LRU + TTL). Key = SHA‑256 of
     `model : prompt : sorted(kwargs)` (excluding `bypass_cache`/`timeout`). Default TTL
     **1800s**, max **500** entries. Cache hit → returns instantly. `bypass_cache=True`
     skips it.
  2. Builds payload for POST `/api/generate` with `stream:false`, `keep_alive:"60m"` and
     default options `num_predict:1000, num_ctx:4096, temperature:0.2, top_p:0.9`
     (callers override via `options={...}`). `format="json"` is passed through to Ollama
     when a caller wants strict JSON.
  3. Uses one **shared pooled `httpx.AsyncClient`** (20 keep‑alive, 50 max connections).
  4. **Model fallback:** if Ollama replies `404` (model name not installed), it queries
     `/api/tags` and retries with the first of `llama3.2:3b` / `llama3:latest` / `llama3`
     that is actually present.
  5. Translates transport errors into typed exceptions:
     `ConnectionError` (can't connect / timeout) and `RuntimeError` (HTTP error / other).
     Services catch these and either fall back or raise `AppException(503/502)`.

### 6.2 `json_utils.extract_and_parse_json(text, default=None)`

LLMs return JSON wrapped in prose, ```` ```json ```` fences, with trailing commas, single
quotes, Python literals (`True/False/None`), or truncated mid‑object. This function tries, in
order:
1. strip markdown fences, `json.loads` directly
2. regex‑extract the first `{...}` or `[...]` block, strip trailing commas, parse
3. replace `True/False/None` → `true/false/null`, parse
4. `repair_truncated_json` (walks the string tracking string/escape state and the
   brace/bracket stack, closes an open string, drops a dangling comma/colon, then closes all
   open `{`/`[`), parse
5. repair + literal replacement, parse
6. return `default`

Some services (`career_intelligence_service`, `company_prep_service`) have their own smaller
`_extract_json_from_llm` doing steps 1–2 only.

### 6.3 The universal "AI with deterministic fallback" shape

Nearly every generative service looks like this:

```python
provider = ai_provider or OllamaProvider()
try:
    raw = await provider.generate(prompt, format="json", options={...})
    parsed = extract_and_parse_json(raw)
    if not valid(parsed):
        raise ValueError
    result = build_from(parsed)
except ConnectionError:
    raise AppException("AI Service (Ollama) is currently unavailable…", 503)   # some features
except Exception:
    result = deterministic_fallback(...)   # other features never fail the request
save(result); return result
```

Which branch is used differs per feature:
- **Hard‑fail (503) if Ollama down:** Resume Analysis, Skill Gap, Job→Resume Match,
  Career Intelligence (JD analyze / match / cover letter / cold email), Interview evaluation.
- **Silent deterministic fallback:** Personal Trainer plan, Career Roadmap, Project
  Recommendations, Company Prep, Coding‑challenge generation, AI hints, cold‑email subject.

The **deterministic fallback generators** are large hand‑written data structures — e.g.
`_build_deterministic_deep_plan` (Personal Trainer), `create_curated_roadmap_for_role`
(Roadmap, with role‑specific branches for Data/AI, Frontend, DevOps, and generic SWE),
`get_curated_company_questions` (Company Prep). They make the app fully usable with no LLM at all.

---

## 7. Authentication & authorization end‑to‑end

### Tables
- `users(id, email UNIQUE, name, hashed_password, is_active, role='user', is_superuser=False,
  reset_token, reset_token_expires_at, created_at, updated_at)`
- `profiles(id, user_id UNIQUE FK, education, degree, graduation_year, experience,
  current_role, target_role, skills JSON[], preferred_location, work_preference, career_goal, …)`
  — 1:1 with user, created empty at registration.

### Flow

1. **Register** — `POST /api/v1/auth/register` `{name,email,password}` (`password` min 6).
   `auth_service.register_user`: lowercase/trim email, reject if exists, `bcrypt` hash the
   password, insert `User` + empty `Profile`, commit. Route mints a JWT and returns
   `{access_token, token_type:"bearer", user}` inside the envelope. Status 201.
2. **Login** — `POST /api/v1/auth/login`. `authenticate_user`: find by email,
   `verify_password`, check `is_active`. Same token payload.
3. **Token** — `create_access_token({"sub": str(user.id), "email": …})`, signed HS256 with
   `JWT_SECRET`, `exp = now + JWT_EXPIRATION_MINUTES` (30). No refresh token; expiry = logout.
4. **Every protected request** — `Authorization: Bearer <token>`. `deps.get_current_user`:
   `HTTPBearer(auto_error=False)` → decode → `sub` → `int` → `auth_service.get_user_by_id`
   (loads profile) → 401 if missing/invalid/expired/unknown, 403 if `is_active=False`.
5. **Admin** — `deps.get_current_admin_user` additionally requires
   `is_superuser or role == "admin"`, else 403. Used by every `/api/v1/admin/*` route.
6. **Forgot / reset password** — `POST /auth/forgot-password` generates
   `secrets.token_urlsafe(32)`, stores it + 1‑hour expiry on the user, and (for
   demo/testability) **returns the token in the response body**. `POST /auth/reset-password`
   `{token, new_password}` validates + expiry‑checks the token, re‑hashes, clears the token.
7. **Change password (from Profile)** — `profile_service.change_user_password` verifies the
   current password and that the new one differs.
8. **Logout** — `POST /auth/logout` is a no‑op acknowledgement (JWT is stateless); the client
   just deletes the token.

### Frontend side
- `src/lib/api.ts`: token kept in `localStorage` under `cc_auth_token`; `request()` attaches
  `Authorization` automatically; non‑2xx → throws `APIError(message, status, details)`.
- `context/AuthContext.tsx`: on mount, if a token exists, calls `/auth/me`; on failure clears
  token. Exposes `user, token, isAuthenticated, login(authData), logout(), refreshUser(), updateUser()`.
- `components/auth/ProtectedRoute.tsx`: shows a spinner while `isLoading`, else redirects to
  `/login` if `!isAuthenticated`, else renders children.
- Admin links in the sidebar only render for `role==="admin" || is_superuser`.
  (The `/admin` route itself is wrapped in `AdminLayout`, not `ProtectedRoute`.)

---

## 8. The database model

All models inherit `Base` (`app/db/base.py`) and are aggregated in `app/models/__init__.py`.
Timestamps (`created_at`, sometimes `updated_at`) are on nearly every table. List/dict columns
are `JSON` (SQLite) / `JSONB` (Postgres). Every child table has a `user_id` or a chain that
leads to one, and FKs use `ondelete="CASCADE"` (or `SET NULL` for optional links).

### 8.1 Identity
| Table | Key columns | Relationships |
|---|---|---|
| `users` | email, name, hashed_password, is_active, role, is_superuser, reset_token | 1:1 `profiles`, 1:N `resumes` |
| `profiles` | target_role, current_role, degree, education, graduation_year, experience, skills[], preferred_location, work_preference, career_goal | belongs to user |

### 8.2 Resume
| Table | Key columns |
|---|---|
| `resumes` | user_id, title | → many `resume_versions`, many `resume_analysis` |
| `resume_versions` | resume_id, version_number, filename, file_path, file_size, file_type, mime_type, **extracted_text**, is_current |
| `resume_analysis` | resume_id, resume_version_id, user_id, **ats_score**, **scoring_breakdown (JSON)**, experience/education/project summaries, certifications[], strengths[], weaknesses[], missing_keywords[], grammar_suggestions[], formatting_suggestions[], improvement_recommendations[], raw_ai_response |
| `resume_skills` | resume_analysis_id, skill_name, category, proficiency_level |

### 8.3 Careers / skill gap
| Table | Key columns |
|---|---|
| `occupations` | code (SOC), title, description, industry |
| `skills` | name UNIQUE, category |
| `occupation_skills` | occupation_id, skill_id, **importance (0‑100)**, **level (0‑100)**, is_required |
| `user_skills` | user_id, skill_name, source ("profile"/"resume"/…), proficiency |
| `career_goals` | user_id, occupation_id, target_role_title, is_active |
| `skill_gap_reports` | user_id, occupation_id, **match_percentage**, strong_skills[], intermediate_skills[], missing_skills[], learning_order[], ai_explanation |

### 8.4 Roadmap
| Table | Key columns |
|---|---|
| `roadmaps` | user_id, occupation_id?, title, target_role, overall_progress, is_active |
| `roadmap_items` | roadmap_id, phase, skill, topics[], projects[], resources[], priority, estimated_effort, is_completed, completed_at |
| `roadmap_progress` | roadmap_item_id, user_id, status, notes (audit log) |

### 8.5 Personal Trainer
| Table | Key columns |
|---|---|
| `training_plans` | user_id, title, goal_dimensions[] (skill/role/company), target_skill/role/company, current_skills[], experience_level, **daily_hours**, learning_preference, target_deadline, estimated_duration_days, total_learning_hours, **overall_progress**, is_active, phases_summary[] |
| `training_days` | plan_id, day_number, phase_name, objective, topics[], expected_outcome, total_planned_minutes, is_completed, completed_at, **confidence_rating (1‑5)**, ai_review_recommendation |
| `training_tasks` | day_id, title, description, **task_type** (theory/practice/project/assessment), **estimated_minutes**, **status** (not_started/in_progress/completed/skipped/rescheduled), order_index, **is_carried_over**, original_day_number, time_spent_minutes, completed_at |
| `personal_trainer_settings` | user_id UNIQUE, notifications_enabled, preferred_time, notification_channel |

### 8.6 Mock Interview
| Table | Key columns |
|---|---|
| `interview_sessions` | user_id, role, difficulty, status (in_progress/completed/abandoned), total_questions, **current_question_index**, overall_score, summary_feedback, completed_at |
| `interview_questions` | session_id, question_bank_id?, question_text, category, difficulty, question_order, explanation |
| `interview_answers` | session_id, question_id, user_answer, submitted_at |
| `interview_evaluations` | answer_id UNIQUE, **technical_correctness, relevance, completeness, communication, structure, clarity, overall_score**, feedback, strengths[], improvements[], ideal_answer |

### 8.7 Question bank
| Table | Key columns |
|---|---|
| `question_bank` | question, category (Technical/HR/Behavioral/Coding/DSA/SQL/Aptitude/Role‑specific), difficulty, role, tags[], **source_type** (standard/ai_generated), explanation |
| `saved_questions` | user_id + question_id UNIQUE |

### 8.8 Coding
| Table | Key columns |
|---|---|
| `coding_challenges` | title, slug UNIQUE, category (Python/SQL/DSA), difficulty, description, **starter_code**, language, examples[], **test_cases[]**, explanation, **sql_schema** |
| `coding_submissions` | user_id, challenge_id, language, code, **status** (Passed/Failed/Time Limit Exceeded/Runtime Error/Syntax Error), passed_test_cases, total_test_cases, execution_time_ms, error_message |
| `coding_results` | submission_id, test_case_index, passed, input_data, expected_output, actual_output, error_output, execution_time_ms |

### 8.9 Company prep
| Table | Key columns |
|---|---|
| `company_prep_plans` | user_id, company_name, target_role, is_verified_company, verification_notes, company_overview, role_summary, required_skills[], technical_prep_topics[], coding_topics[], hr_topics[], behavioral_prep[], **practice_questions[]** |

### 8.10 Jobs
| Table | Key columns |
|---|---|
| `jobs` | external_id UNIQUE, provider (adzuna/seed), title, company, location, is_remote, description, salary_min/max/currency, redirect_url, posted_at |
| `saved_jobs` | user_id + job_id UNIQUE |
| `job_matches` | user_id, job_id, resume_id?, **match_score**, experience_match, education_match, matched_skills[], missing_skills[], explanation, recommendations[] |

### 8.11 Career Intelligence
| Table | Key columns |
|---|---|
| `resume_jd_matches` | user_id, resume_id?, resume_title, job_title, company_name, job_description, **overall/skills/keyword/experience/responsibility scores**, matched_skills[], missing_skills[], partial_matches[], relevant_experience[], potential_gaps[], improvement_suggestions[] |
| `cover_letters` | user_id, resume_id?, job_title, company_name, tone, length, content |
| `cold_emails` | user_id, resume_id?, match_id?, job_title, company_name, recruiter_name/email, job_description, company_info, portfolio/github/linkedin_url, additional_context, email_type, tone, length, subject, body |

### 8.12 Learning resources
| Table | Key columns |
|---|---|
| `learning_resources` | title, description, url, source, resource_type (Documentation/Course/Video/Book/Certification), skill_name, difficulty, estimated_hours, is_verified |
| `user_learning_progress` | user_id, resource_id, is_saved, is_completed, completed_at |

### 8.13 Projects, Achievements, Notifications
| Table | Key columns |
|---|---|
| `project_recommendations` | user_id, title, description, difficulty, target_role, technologies[], features[], skills_learned[], expected_outcome, is_saved, **status** (Not Started/In Progress/Completed) |
| `achievements` | slug UNIQUE, title, description, icon (emoji), category, **threshold** |
| `user_achievements` | user_id + achievement_id UNIQUE, current_progress, is_earned, earned_at |
| `notifications` | user_id, title, message, **type**, link_url, is_read |
| `notification_preferences` | user_id UNIQUE, 5 boolean toggles (roadmap/interview/coding/resume/learning) |

> The README claims "42 tables"; the actual count from `models/__init__.py` is ~**39** ORM classes.

---

## 9. Feature deep‑dives

Each subsection: **purpose → data → endpoints → backend flow → AI usage → fallback → frontend**.

---

### 9.1 Dashboard

- **Purpose:** one aggregated snapshot of the candidate's state.
- **Endpoint:** `GET /api/v1/dashboard` → `DashboardResponse`.
- **Backend (`dashboard_service.get_user_dashboard_data`):**
  - `calculate_profile_completion` = (# of 10 tracked profile fields that are non‑empty) / 10 × 100.
  - Builds a `recent_activity` list of real timestamped `ActivityItem`s: account created,
    profile updated (only if `updated_at` > `created_at` + 1s), resume uploaded, resume
    analyzed (with ATS score), skill‑gap analyzed. Sorted newest‑first.
  - Resume summary = latest resume's current version + latest analysis ATS score
    (status `no_resume` / `uploaded` / `analyzed`).
  - Calls `performance_service.get_user_performance_data` and `get_user_readiness_data`
    (see §9.16) to fill interview stats, "coding" stats (a rough proxy), and placement readiness.
- **No AI.** Pure aggregation.
- **Frontend:** `pages/Dashboard.tsx` with `WelcomeBanner`, `StatCard`s, `RecentActivityList`.

---

### 9.2 Resume Studio (upload / versioning / download / delete)

- **Data:** `resumes` → `resume_versions` (the file bytes on disk + `extracted_text`).
- **Endpoints (`api/v1/resumes.py`):**
  - `GET /resumes` — list
  - `POST /resumes` (multipart `file`, optional `resume_id`) — upload
  - `GET /resumes/{id}/download?version_id=` — stream file back
  - `GET /resumes/{id}/history` — version list + ATS score trajectory
  - `GET /resumes/{id}/compare?v1=&v2=` — diff two versions
  - `DELETE /resumes/{id}` and `DELETE /resumes/{id}/versions/{version_id}`
- **Upload flow (`resume_service.upload_user_resume`):**
  1. Read bytes → `resume_parser.process_and_extract_resume`:
     - `validate_file_metadata`: not empty, ≤ `MAX_FILE_SIZE_BYTES`, extension in
       `{.pdf,.docx}`, MIME in the allowed set.
     - PDF → PyMuPDF `fitz`: reject encrypted, join all page text, reject if empty.
     - DOCX → `python-docx`: paragraphs + table cells joined.
  2. If `resume_id` given → new version of that resume: mark old versions
     `is_current=False`, `version_number = max+1`. Else create a new `Resume`.
  3. Write bytes to `uploads/resumes/user_<id>/res_<rid>_v<n>_<8hex>.<ext>`.
  4. Insert `ResumeVersion` with `extracted_text`, commit.
- **History (`get_resume_version_history`):** joins each version with its analysis;
  `score_improvement` = latest evaluated ATS − earliest evaluated ATS.
- **Compare (`compare_resume_versions`):** ATS delta, `added_skills` / `removed_skills`
  (set diff of extracted skills), `resolved_missing_keywords` (missing in v1 but not v2).
- **Delete version:** if only 1 version left, deletes the whole resume; otherwise removes the
  file + row and promotes the highest remaining `version_number` to `is_current`.
- **Frontend:** `pages/Resumes.tsx` (upload, list, history timeline, compare UI, download via
  `downloadResumeBlob` which reads `Content-Disposition` for the filename).

---

### 9.3 Resume ATS Analysis (transparent scoring)

- **Purpose:** score a resume 0–100 with a visible rubric + actionable feedback.
- **Endpoints:** `POST /api/v1/resumes/{id}/analyze?version_id=&force=true`,
  `GET /api/v1/resumes/{id}/analysis`.
- **Backend (`resume_analysis_service.analyze_user_resume`):**
  1. Resolve target version (explicit `version_id` or current). Require non‑empty
     `extracted_text` else `400`.
  2. If not `force` and a prior analysis for that exact version exists **with populated
     strengths + weaknesses**, return it (cache).
  3. Prompt Ollama (`ANALYSIS_PROMPT_TEMPLATE`, first 4000 chars of resume text,
     `format="json"`, `num_predict:3500`) asking for 5 sub‑scores + summaries +
     strengths/weaknesses/missing_keywords/grammar/formatting/improvements + top 15–20 skills.
  4. `extract_and_parse_json` → validate against `AIResumeAnalysisPayload` (Pydantic). If
     Ollama is down → `AppException(503)`; if output unparseable → `502`.
  5. **`_ensure_detailed_explanations`** — if the LLM left any list empty, fill it with
     heuristic content (e.g. adds a "lacks quantifiable metrics" weakness only if the resume
     text has no `%`, "increased", "reduced"; suggests missing keywords from a common list).
  6. **`compute_ats_score`** — the deterministic part. Weighted sum:
     `structure 20% + skills 30% + experience 25% + education 15% + formatting 10%`,
     clamped 0–100, rounded to 1 dp. Returns `(overall, breakdown)` where `breakdown`
     includes the raw sub‑scores, the weight map, and a human `rubric_description`.
  7. Persist `ResumeAnalysis` + `ResumeSkill` rows. **Side effect:** any newly extracted
     skills are appended to the user's `profile.skills`.
- **Frontend:** `pages/ResumeAnalysis.tsx` — ring/bar chart of the 5 components, lists of
  strengths / weaknesses / missing keywords / grammar / formatting / recommendations, and the
  extracted skills.

---

### 9.4 Career Intelligence Hub (4 tools in one page)

Page: `pages/CareerIntelligence.tsx` (largest page, ~2100 lines), tabs driven by
`?tab=analyzer|match|cover-letter|cold-email`. Router redirects legacy `/career` and
`/career/skill-gap` here. Service: `career_intelligence_service.py`. Models:
`resume_jd_matches`, `cover_letters`, `cold_emails`.

**a) JD Analyzer** — `POST /career-intelligence/analyze-jd` `{job_description}`.
Prompt `JD_ANALYZE_PROMPT` (JD truncated to 12k chars, `temperature 0.1`) → structured JSON:
job_title, company, required/preferred skills, technologies, experience, responsibilities,
education, certifications, soft_skills, keywords. All list fields cleaned to non‑empty
strings. Ollama down → `503`; parse fail → returns an all‑empty structure (soft fail). **Not persisted.**

**b) Resume → JD Match** — `POST /career-intelligence/match`
`{resume_id, job_description, job_title?, company_name?, target_occupation_id?}`.
Loads the resume's current (or any text‑bearing) version. Optional occupation context.
Prompt `RESUME_JD_MATCH_PROMPT` asks for 5 scores (overall/skills/keyword/experience/
responsibility, each clamped 0–100) + matched/missing/partial skills + relevant_experience +
potential_gaps + improvement_suggestions. "Missing" is explicitly defined as *"not found in
the provided resume"* (not a claim about the person). Persists `ResumeJdMatch`. History:
`GET /matches`, detail `GET /matches/{id}`.

**c) Cover Letter** — `POST /career-intelligence/cover-letter`
`{resume_id, job_description, job_title, company_name, tone?, length?}`. Prompt
`COVER_LETTER_PROMPT` with strong anti‑hallucination rules (base strictly on the real resume,
never invent experience/metrics, output raw letter text, no markdown fences). Strips code
fences from the output, persists `CoverLetter`. History `GET /cover-letters`.

**d) Cold Email** — `POST /career-intelligence/cold-email/generate` (payload
`ColdEmailGeneratePayload`). Rich context builder:
- candidate background = resume text (4k chars) **or** a profile summary,
- **match intelligence** = reuse a prior `ResumeJdMatch` (explicit `match_id`, else the most
  recent one for this resume) — scores, matched skills, relevant experience get folded into
  the prompt,
- links block from portfolio/github/linkedin,
- `COLD_EMAIL_PROMPT` demands JSON `{subject, body}` with 9 anti‑hallucination rules (never
  fabricate a recruiter name/email/URL, never claim the candidate worked there, keep it
  mobile‑readable). **Retries once** with a stricter instruction if `body` is missing, then
  falls back to a templated greeting/body. Persists `ColdEmail`.
- Extras: `POST /cold-email/regenerate-subject` (LLM or deterministic subject),
  `GET /cold-email/history`, `GET /cold-email/{id}`, `PUT /cold-email/{id}` (save user edits),
  `DELETE /cold-email/{id}`.

---

### 9.5 Careers directory & Skill Gap (`careers.py`, `career_service.py`)

- **Data source:** `ONET_DATASET` in `integrations/careers/onet.py` — 8 IT‑ish occupations
  (Software Developer, QA, Systems Analyst, Data Scientist, AI/ML Engineer, DevOps/SysAdmin,
  InfoSec Analyst, Technical PM), each with ~7–10 skills carrying `importance` and `level`
  weights (0–100). `seed_occupations_if_empty` copies this into `occupations` /
  `skills` / `occupation_skills` on first use.
- **Endpoints:**
  - `GET /api/v1/careers?q=&limit=` — search occupations (ILIKE on title/code/industry/description)
  - `GET /api/v1/careers/{id}` — occupation detail with skills
  - `POST /api/v1/career/skill-gap` `{occupation_id}` — generate a `SkillGapReport`
  - `GET /api/v1/career/skill-gap/latest`
  - `POST /api/v1/career/goal` `{occupation_id}` — set active `CareerGoal` + update
    `profile.target_role` / `career_goal`
- **Skill Gap algorithm (`generate_skill_gap_report`):**
  1. `aggregate_user_skills(user_id)` — union (lowercased) of `profile.skills` +
     `resume_skills` (via analyses) + `user_skills`.
  2. For each required occupation skill: substring‑match against the user's set. If matched
     and `importance ≥ 85` → **strong**, else → **intermediate**; if not matched → **missing**
     with priority `High` (imp ≥ 88) / `Medium` (≥ 80) / `Low`.
  3. **`match_percentage` = (strong×1.0 + intermediate×0.6) / total_required × 100** (deterministic).
  4. LLM (`SKILL_GAP_PROMPT_TEMPLATE`) writes the narrative `explanation` + a `learning_order`
     array (step, skill_name, priority, rationale). Ollama down → `503`.
  5. Persist `SkillGapReport`.
- **Frontend:** `pages/Careers.tsx` (browse/select), `pages/SkillGap.tsx` (radar‑ish
  strong/intermediate/missing view + learning order). Note: the sidebar routes people to
  Career Intelligence; `SkillGap`/`Careers` pages still exist and are reachable directly.

---

### 9.6 Career Roadmap (`roadmap.py`, `roadmap_service.py`)

- **Purpose:** a 5‑phase (weeks 1‑3, 4‑7, 8‑11, 12‑15, 16‑20) learning path with, per phase:
  a skill, 5‑8 specific topics, 2 portfolio projects, 3 resources, priority, effort estimate.
- **Endpoints:** `POST /api/v1/roadmap/generate` `{occupation_id?, custom_query?}`,
  `GET /api/v1/roadmap/latest`, `PUT /api/v1/roadmap/items/{id}/toggle` `{is_completed}`.
- **Flow (`generate_user_roadmap`):**
  1. Resolve target role: explicit `custom_query`, else `resolve_target_occupation`
     (explicit id → active CareerGoal → profile.target_role search → first occupation).
  2. Gather `aggregate_user_skills` + missing skills from the latest matching `SkillGapReport`
     (or occupation skills not in user's set).
  3. Prompt `ROADMAP_PROMPT_TEMPLATE` (`asyncio.wait_for` 90s). Validate each item has
     `phase` + `skill`, build `AIRoadmapPromptPayload`.
  4. **Fallback:** `create_curated_roadmap_for_role` — a big hand‑authored 5‑phase curriculum
     with dedicated branches for Data/AI, Frontend, DevOps/Cloud/Security, and generic
     SWE/Backend/Full‑stack. Used on timeout, connection error, or empty output. (Connection
     error can also `503` depending on path.)
  5. Deactivate previous roadmaps, insert `Roadmap` + `RoadmapItem`s.
- **Progress:** `overall_progress` = completed items / total items × 100, recomputed on read
  and on toggle. Toggling also writes a `RoadmapProgress` audit row.
- **Frontend:** `pages/Roadmap.tsx` — phase accordions, per‑item checkboxes, progress bar.

---

### 9.7 Personal Trainer (the flagship module)

Files: `api/v1/personal_trainer.py`, `services/personal_trainer_service.py` (~900 lines),
`services/email_service.py`, `core/scheduler.py`. Page: `pages/PersonalTrainer.tsx` (~1475 lines).

- **Purpose:** turn a goal ("become a Backend Engineer at Amazon", "learn PyTorch") into a
  concrete **day‑by‑day** plan of minute‑sized tasks that adapts to how much time you actually
  have, with streak‑preserving rollover and twice‑daily email nudges.
- **Endpoints:**
  - `GET /personal-trainer/resume-skills` — reuse already‑parsed skills (no new LLM call):
    `resume_skills` → `profile.skills` → regex‑scan latest resume text for common tech tokens.
  - `POST /personal-trainer/investigate` — create a plan (payload: goal_dimensions[],
    target_skill/role/company, current_skills[], experience_level, `daily_hours`,
    target_deadline?, learning_preference).
  - `GET /personal-trainer/active` — active plan (also recomputes `overall_progress`).
  - `GET /personal-trainer/daily/{day_number?}` — the rich day view.
  - `PATCH /personal-trainer/tasks/{task_id}` `{status, notes?, time_spent_minutes?}`.
  - `POST /personal-trainer/reschedule-today` `{available_hours}`.
  - `POST /personal-trainer/days/{day_id}/review` `{confidence_rating 1‑5, feedback?}`.
  - `GET/PUT /personal-trainer/settings`, `POST /personal-trainer/notify-webhook`.
- **Plan generation (`generate_training_plan`):**
  1. Build a title from the dimensions; deactivate old active plans.
  2. If Ollama healthy → `PLAN_SYSTEM_PROMPT` + a user prompt (goal, skills, `daily_hours`,
     max minutes/day, ≥14 days). Wants JSON `{title, estimated_duration_days,
     total_learning_hours, phases_summary[4], days[{day_number, phase_name, objective,
     topics[], expected_outcome, tasks[{title, description, task_type, estimated_minutes}]}]}`.
  3. **Fallback `_build_deterministic_deep_plan`:** a curated 17‑topic sequence (a Data/AI
     branch and a generic SWE branch), 4 phases, 3 granular tasks/day sized to `daily_hours`.
  4. Persist `TrainingPlan` → `TrainingDay`s → `TrainingTask`s. **Hard enforcement:** if a
     day's task minutes exceed `daily_hours×60`, every task is scaled down proportionally
     (min 15 min).
- **Daily view (`get_daily_training_view`):** picks the first incomplete day (or the given
  one). Then:
  - **Adaptive rollover:** any `not_started`/`in_progress` task from *yesterday* is cloned
    into today as a new task titled "… (Carried Over)" with `is_carried_over=True`, and the
    original is marked `rescheduled`.
  - Builds yesterday recap (completed/incomplete), tomorrow preview, workload minutes vs
    available minutes vs buffer, and a plain‑English `daily_ai_summary` string
    (assembled deterministically from counts — **not** an LLM call).
- **Task status (`update_training_task_status`):** sets status/notes/time; a day flips
  `is_completed` when all its tasks are `completed`/`skipped`; recomputes plan progress; if
  the new status is `completed`, **fires a task‑completion email** (fire‑and‑forget).
- **Reschedule (`reschedule_today_workload`):** given `available_hours`, greedily keeps tasks
  that fit and **defers the rest to the next day** (creating a day if needed), marking them
  carried‑over.
- **Confidence review:** stores 1‑5 rating and a heuristic `ai_review_recommendation`
  (≤2 → "add 45‑60 min review", 3 → "write unit tests", ≥4 → "you're primed").
- **n8n webhook:** if `N8N_WEBHOOK_URL` set, POSTs the day's payload (goal, yesterday, today's
  tasks, progress) to that URL.
- **Emails:** see §11.

---

### 9.8 AI Mock Interview (text + voice, 6‑metric rubric)

Files: `api/v1/interviews.py`, `services/interview_service.py`. Pages: `InterviewSetup.tsx` →
`InterviewSession.tsx` → `InterviewResults.tsx`. Voice via `hooks/useVoiceInterview.ts`.

- **Endpoints:**
  - `POST /api/v1/interviews` `{role, difficulty, total_questions?}` → creates a session.
  - `GET /api/v1/interviews` — history; `GET /api/v1/interviews/{id}` — session state
    (survives browser refresh — server holds `current_question_index`).
  - `POST /api/v1/interviews/{id}/answer` `{question_id, user_answer}` — evaluate + advance.
  - `GET /api/v1/interviews/{id}/results` — aggregate report.
- **Session creation (`create_interview_session`):**
  1. `seed_standard_questions_if_empty`.
  2. Pull `total_questions` from `question_bank` matching role **and** difficulty (ILIKE);
     if short, top up by difficulty only; if still short, **generate** via
     `question_service.generate_ai_questions`; if the bank is totally empty, take any.
  3. Snapshot each chosen question into `interview_questions` (with `question_order`).
- **Answer evaluation (`submit_and_evaluate_answer`):**
  1. Guard: session must be `in_progress`, question must belong to it.
  2. Prompt `EVALUATE_ANSWER_PROMPT_TEMPLATE` (role, difficulty, question, reference answer,
     the candidate's text) → JSON with 6 metrics (0–100): **technical_correctness, relevance,
     completeness, communication, structure, clarity** + `overall_score` + `feedback` +
     `strengths[]` + `improvements[]` + `ideal_answer`. Ollama down → `503`, junk → `502`.
     Missing metrics default to sensible values.
  3. Insert `InterviewAnswer` + `InterviewEvaluation`. `current_question_index += 1`.
  4. When index ≥ `total_questions`: mark `completed`, set `completed_at`, and
     `overall_score` = mean of all evaluations' `overall_score`.
- **Results (`get_interview_results`):** per‑metric averages across all answers,
  deduped top‑5 strengths/improvements, full question transcript.
- **Voice (`useVoiceInterview`):** `speechSynthesis` reads the question aloud (TTS);
  `webkitSpeechRecognition`/`SpeechRecognition` (continuous, interim results, `en-US`)
  transcribes the spoken answer into the answer box; graceful messaging for
  `not-allowed` / `no-speech` / `network`; always falls back to typing.

---

### 9.9 Question Bank (`questions.py`, `question_service.py`)

- **Data:** `question_bank` (`source_type` = `standard` seeded list, or `ai_generated`) +
  `saved_questions` bookmarks.
- **Endpoints:** `GET /api/v1/questions` (filters: category, difficulty, role, `q`,
  `source_type`, `saved_only`, pagination), `GET /questions/random`,
  `POST /questions/generate` `{topic?, category?, difficulty?, role?, count?}`,
  `POST/DELETE /questions/{id}/save`.
- **AI generation (`generate_ai_questions`):** prompts Ollama for N questions with
  explanations; every generated row is stored with `source_type="ai_generated"` and surfaced
  with a "AI‑generated practice question" label; a deterministic fallback set is used if the
  LLM fails. Also reused by the Mock Interview module.
- **Frontend:** `pages/QuestionBank.tsx` — filter bar, cards with reveal‑explanation, bookmark
  toggle, "generate more".

---

### 9.10 Coding Challenges sandbox

Files: `api/v1/coding.py`, `services/coding_service.py`, `services/code_executor.py`.
Pages: `CodingDirectory.tsx` (list) → `CodingEnvironment.tsx` (solve).

- **Data:** `coding_challenges` (14 seeded: Two Sum, Valid Palindrome, Binary Search, Kadane,
  Valid Parentheses, Contains Duplicate, Best Time to Buy/Sell Stock, Group Anagrams,
  Climbing Stairs, Longest Common Prefix, Reverse Array + 2 SQL: Department Highest Salary,
  Second Highest Salary). Plus `coding_submissions` and per‑test `coding_results`.
- **Endpoints:** `GET /coding/challenges` (filters), `GET /coding/challenges/{id-or-slug}`,
  `POST /coding/challenges/generate` `{topic, category, difficulty}` (AI or fallback,
  new slug with timestamp), `POST /coding/challenges/{id}/submit` `{code, language}`,
  `GET /coding/challenges/{id}/submissions`, `POST /coding/challenges/{id}/hint` `{code}`.

> **Reality check — where code actually runs.** The README says candidate code runs
> **client‑side in WebAssembly (Pyodide / SQLite WASM)**. It does **not**. `CodingEnvironment.tsx`
> POSTs the code to `POST /coding/challenges/{id}/submit`, and `code_executor.execute_code_safely`
> runs it **on the server**:
> - **Python/DSA:** `ast.parse` for a syntax pre‑check, then a wrapper script is written to a
>   `tempfile.TemporaryDirectory` and executed as a subprocess with
>   `python -I -S <script>` (isolated mode, no site) under a **3.0s timeout**; the wrapper
>   parses the test `input` lines into args (`eval` with `__builtins__=None`), calls the last
>   defined function, prints JSON/str; output compared to `expected_output` (JSON‑equality,
>   else case‑insensitive string). Statuses: `Passed` / `Failed` / `Time Limit Exceeded` /
>   `Runtime Error` / `Syntax Error`.
> - **SQL:** a fresh in‑memory `sqlite3` connection, run `sql_schema` (DDL+seed) then the
>   candidate query, compare rows as JSON.
> There is **no editor library** — the UI uses a plain `<textarea>`.
> The AI **hint** endpoint only returns guidance; it never decides pass/fail.

- **Frontend:** `CodingEnvironment.tsx` — problem statement, examples, SQL schema view,
  textarea, "Run/Submit" → shows per‑test results (input/expected/actual/error, ms),
  "Get AI Hint", "Generate similar challenge".

---

### 9.11 Company‑Specific Prep (`company_prep.py`, `company_prep_service.py`, `company_questions_bank.py`)

- **Purpose:** a targeted prep dossier for a company + role (overview, role summary, required
  skills, technical topics, coding topics, HR topics, behavioral prep, **≥25 practice questions**).
- **`VERIFIED_COMPANIES_REGISTRY`:** hard‑coded facts (overview, culture, core skills,
  behavioral focus) for Google, Amazon, Microsoft, Meta, Apple, Netflix, Uber, TCS, Infosys,
  Wipro. Unknown companies → `is_verified_company=False` + a `verification_notes` disclaimer.
- **Endpoints:** `POST /api/v1/company-prep` `{company_name, target_role}`,
  `GET /api/v1/company-prep`, `GET /api/v1/company-prep/{id}`.
- **Flow:** prompt `COMPANY_PREP_PROMPT` (`asyncio.wait_for` 90s) with the verified overview
  as grounding → parse JSON; every practice question is force‑labeled
  `"AI-generated practice question"`; if fewer than 25, top up from
  `get_curated_company_questions(company, role, count=25)`. On Ollama down → `503`; on any
  other error → a fully deterministic plan built from the registry + curated question bank.
- **Frontend:** `pages/CompanyPreparation.tsx` — company/role form, tabbed dossier, saved plans.

---

### 9.12 Live Jobs Hub + Job→Resume Match

Files: `api/v1/jobs.py`, `api/v1/job_match.py`, `services/job_service.py`,
`services/job_match_service.py`, `integrations/jobs/adzuna.py`. Page: `pages/Jobs.tsx`.

- **Search (`search_and_cache_jobs`):** `GET /api/v1/jobs?q=&location=&is_remote=&page=&limit=`.
  Try **Adzuna** (`AdzunaJobProvider.search_jobs` → real HTTP GET to
  `api.adzuna.com/v1/api/jobs/{country}/search/{page}` with `app_id`/`app_key`; normalizes each
  result into `NormalizedJobData`; `is_remote` inferred from text). Each result is **upserted**
  into the local `jobs` table. If Adzuna returns nothing / fails → **DB cache fallback**
  (ILIKE query over the ~30 seeded `VERIFIED_JOB_SEED` rows). If both empty and provider
  failed → `503`.
- **Bookmarks:** `POST/DELETE /api/v1/jobs/{id}/save`, `GET /api/v1/jobs/saved`
  (`saved_jobs`, unique per user+job).
- **Job → Resume Match (`job_match_service.match_resume_to_job`):**
  `POST /api/v1/jobs/{job_id}/match?resume_id=`.
  1. `extract_keywords_from_job` — scan title+description for a fixed
     `COMMON_TECH_KEYWORDS` list.
  2. Overlap with `aggregate_user_skills` → matched/missing.
  3. Deterministic scores: `skill_score = matched/total × 100`,
     `experience_match` and `education_match` from simple keyword heuristics on
     `profile.experience` / `profile.degree`.
  4. **`overall = skill×0.50 + experience×0.25 + education×0.25`**, clamped 20–98.
  5. LLM writes the narrative `explanation` + `recommendations[]` only. Ollama down → `503`.
  6. Persist `JobMatch`. `GET /api/v1/jobs/{job_id}/match` returns the latest.
- **Frontend:** search bar + "Remote only" toggle, job cards (salary, remote badge, "Apply"
  opens `redirect_url`), "Match my resume" panel with score + gaps + tips, saved‑jobs tab.

---

### 9.13 Job Market Analyzer (`job_market.py`, `job_market_service.py`)

- **Purpose:** live aggregate analytics over a real Adzuna result set (no fake data).
- **Endpoint:** `GET /api/v1/job-market/search` with many query filters
  (`query, location, is_remote, workplace_type, experience_level, skills, company, job_type,
  date_posted, use_profile, page, limit`).
- **Flow:** optionally seed query/location from the profile (`use_profile=true`); if Adzuna
  creds missing → return `provider_configured:false` with an explanatory message and empty
  analytics; else call Adzuna, cache jobs, and for each listing derive `workplace_type`
  (Remote/Hybrid/On‑site), `experience_level` (regex on title/desc), and `extracted_skills`
  (match against `KNOWN_TECH_LEXICON`). Apply in‑memory secondary filters.
- **`_compute_analytics_from_real_jobs`:** `Counter`‑based distributions for top skills,
  job titles, locations, workplace, experience, companies, posting‑date trend, and a salary
  summary (avg/min/max) — each metric emits an `insufficient_data` marker when there aren't
  enough samples.
- **Frontend:** `pages/JobMarketAnalyzer.tsx` — filter panel, listing list, bar‑chart‑style
  metric cards, "insufficient data" notes.

---

### 9.14 Learning Resources (`learning_resources.py`, `learning_resource_service.py`)

- **Data:** `VERIFIED_LEARNING_CATALOG` — a long list of **real** URLs (Python docs,
  freeCodeCamp, YouTube courses, official docs for FastAPI/React/Postgres/Docker, …), seeded
  into `learning_resources`. Progress tracked in `user_learning_progress` (`is_saved`,
  `is_completed`).
- **Endpoints:** `GET /api/v1/learning-resources` (filters: `skill_name, difficulty,
  resource_type, search, skill_gap_only`), `GET /learning-resources/recommended`
  (matches the catalog against the user's latest skill‑gap missing skills), and
  `POST /learning-resources/{id}/progress` `{is_saved?, is_completed?}`.
- **Frontend:** `pages/LearningResources.tsx` — filter chips, resource cards with
  source/type/difficulty/hours badges, save + "mark complete".

---

### 9.15 AI Project Recommendations (`projects.py`, `project_service.py`)

- **Purpose:** 4–6 portfolio project blueprints across Beginner/Intermediate/Advanced,
  targeted at the user's skill gaps + target role.
- **Endpoints:** `POST /api/v1/projects/recommendations` (generate),
  `GET /api/v1/projects?difficulty=&status=`, `PATCH /api/v1/projects/{id}/status`
  `{is_saved?, status?}` (status ∈ Not Started / In Progress / Completed).
- **Flow (`generate_personalized_project_recommendations`):** gather profile
  (target/current role, skills), latest `SkillGapReport.missing_skills`, latest roadmap →
  prompt `PROJECT_RECOMMENDATION_PROMPT` (`temperature 0.7`, `num_predict 3000`) → parse a
  JSON array of `{title, difficulty, description, technologies[], features[], skills_learned[],
  expected_outcome}`. Before saving, it **deletes** the user's previous unsaved / Not‑Started
  recommendations so a regenerate replaces them. On Ollama down → `503`; on any other failure
  → 5 hand‑written personalized fallback projects.
- **Frontend:** `pages/ProjectRecommendations.tsx` — difficulty‑grouped cards with
  tech/feature lists and Save / In‑Progress / Completed buttons.

---

### 9.16 Performance Analytics & Placement Readiness (`performance.py`, `readiness.py`, `performance_service.py`)

Both are **100% deterministic, from stored data** (no AI).

- **Performance (`get_user_performance_data`, `GET /api/v1/performance`):** over `completed`
  interview sessions — total, average / best / latest / first→latest improvement,
  average `technical_correctness` and `communication` across all evaluations, per‑category
  averages → `strong_topics` (≥75) / `weak_topics` (<75), and a `score_history` series for the
  chart. Returns `has_enough_data=false` with a message when there are no completed sessions.
- **Readiness (`get_user_readiness_data`, `GET /api/v1/readiness`):** a weighted blend of up
  to 4 components:
  | Component | Source | Raw weight |
  |---|---|---|
  | Resume ATS Score | latest `ResumeAnalysis.ats_score` | 0.25 |
  | Skill Match & Gap | latest `SkillGapReport.match_percentage` (or `min(100, skills×15)`) | 0.25 |
  | Mock Interview Score | performance average | 0.35 |
  | Coding Practice | avg `overall_score` of Coding/DSA‑category interview evaluations | 0.15 |
  Only **available** components count; their weights are **renormalized** to sum to 1, so the
  score is honest about partial data. Bands: **≥80 Job Ready**, **≥65 Nearly Ready**,
  **else Needs Preparation**. Emits targeted `recommendations` for missing/low components.
- **Frontend:** `pages/PerformanceAnalytics.tsx` — score‑progression line, radar‑style metric
  bars, strong/weak topics; readiness gauge + component breakdown + recommendations (also
  surfaced on the Dashboard).

---

### 9.17 Achievements / Badges (`achievements.py`, `achievement_service.py`)

- **9 system achievements** (`SYSTEM_ACHIEVEMENTS`, seeded): first resume, first analysis,
  ATS ≥ 75, first interview, interview ≥ 75%, first passing coding submission, first completed
  learning resource, first completed roadmap item, "score improved across interviews".
- **Endpoints:** `GET /api/v1/achievements` and `POST /api/v1/achievements/evaluate`
  (both run the evaluator).
- **`evaluate_and_get_user_achievements`:** counts real activity (resume uploads, analyses +
  max ATS, completed interviews + max session score + improved?, passed coding submissions,
  completed learning resources, completed roadmap items), maps each to a `UserAchievement`
  `current_progress`, flips `is_earned` + stamps `earned_at` when `progress ≥ threshold`.
  Returns totals + completion %.
- **Frontend:** `pages/Achievements.tsx` — trophy grid, earned vs locked, progress bars.

---

### 9.18 Notifications (`notifications.py`, `notification_service.py`)

- **In‑app only** (these are separate from the SMTP emails). `notifications` +
  `notification_preferences` (5 toggles).
- **`generate_real_state_notifications`** runs on every `GET /api/v1/notifications` and
  creates **non‑duplicate** notifications from real state (checks "does a notification of this
  `type` already exist for the user?"):
  - `roadmap_reminder` — active roadmap has an incomplete item
  - `interview_reminder` — zero completed interviews
  - `coding_reminder` — unsolved challenges remain
  - `resume_suggestion` — latest ATS < 75 or has missing keywords
  - `learning_milestone` — a skill‑gap report with missing skills exists
- **Endpoints:** `GET /notifications`, `PATCH /notifications/{id}/read`,
  `PATCH /notifications/read-all`, `DELETE /notifications/{id}`,
  `GET/PUT /notifications/preferences`.
- **Frontend:** bell + dropdown in `Navbar.tsx` (unread badge, latest 5, click → `link_url`);
  `pages/NotificationsCenter.tsx` (full list), `pages/NotificationPreferences.tsx` (toggles).

---

### 9.19 Admin panel (`admin.py`, `admin_service.py`, `pages/admin/*`)

- Guarded by `get_current_admin_user` (`role=="admin"` or `is_superuser`).
- **Endpoints:**
  - `GET /api/v1/admin/statistics` — real aggregate counts (users, active users,
    resume versions, completed interviews, coding submissions, "job searches" = saved jobs +
    job matches, "AI evaluations" = interview evaluations + resume analyses).
  - `GET /admin/users`, `PATCH /admin/users/{id}/role` `{role?, is_active?}`
    (setting role `admin` also sets `is_superuser=True`), `DELETE /admin/users/{id}`.
  - `GET/POST/DELETE /admin/questions` — manage `question_bank`.
  - `GET/POST/DELETE /admin/resources` — manage `learning_resources`.
- **Frontend:** `pages/admin/AdminLayout.tsx` (nav) + `AdminDashboard` (stat cards),
  `AdminUsers` (table + role/active/delete), `AdminQuestions`, `AdminResources` (CRUD forms).

---

### 9.20 Floating Help Chatbot (`components/chat/PlatformHelpChatbot.tsx`)

- A **client‑side, rule‑based** assistant (no backend, no LLM). Bottom‑right floating button
  with a live "online" beacon. Matches the user's text against a built‑in FAQ knowledge base
  (how to check ATS score, apply to jobs, set up the profile, interview tips, …) and returns
  canned answers with one‑click deep links into the relevant routes.

---

### 9.21 Health check (`health.py`)

`GET /api/v1/health` → `{ status: healthy|degraded, version, database: connected|unavailable,
ollama: connected|unavailable }`. DB is probed with `SELECT 1`; Ollama with
`OllamaProvider.health_check()`. `useHealthCheck` polls this so the UI can show an Ollama/DB
status indicator.

---

## 10. Frontend architecture

### Routing (`src/App.tsx`)
`<AuthProvider>` → `<BrowserRouter>` → one `<Route element={<Layout/>}>` wrapping everything.
Public: `/`, `/login`, `/register`, `/forgot-password`, `/reset-password`.
Everything else is wrapped in `<ProtectedRoute>`. Legacy `/career*` redirect to
`/career-intelligence`. `/admin` uses `AdminLayout` with nested index/`users`/`questions`/`resources`.
`*` → `NotFound`.

Route → page map: `/personal-trainer`→PersonalTrainer, `/dashboard`→Dashboard,
`/career-intelligence`→CareerIntelligence, `/resumes`→Resumes, `/resume-analysis/:id`→ResumeAnalysis,
`/roadmap`→Roadmap, `/jobs`→Jobs, `/question-bank`→QuestionBank, `/interview`→InterviewSetup,
`/interview/:id`→InterviewSession, `/interview/:id/results`→InterviewResults,
`/performance`→PerformanceAnalytics, `/coding`→CodingDirectory, `/coding/:slug`→CodingEnvironment,
`/company-preparation`→CompanyPreparation, `/learning-resources`→LearningResources,
`/projects`→ProjectRecommendations, `/achievements`→Achievements,
`/notifications`(+`/preferences`), `/profile`.

### `Layout` / `Navbar` / `Footer`
`Layout.tsx` renders `Navbar` + `<Outlet/>` + `Footer` + the floating `PlatformHelpChatbot`
and an `ErrorBoundary`. `Navbar.tsx` is a top bar (hamburger, notification bell + dropdown,
profile pill, brand) plus a **slide‑over drawer** grouping every feature link into sections:
Personal Trainer (primary), Core (Dashboard, Roadmap), Career Intelligence (+ sub‑tabs),
Career & Opportunities (Jobs, Resume Studio, Projects), Interview & Practice (Company Prep,
Question Bank, Coding, Mock Interview), Learning & Analytics (Learning Hub, Analytics, Badges),
Account (Profile, Notification Preferences, Admin if admin), Logout.

### Data layer (`src/lib/api.ts`)
- `API_BASE_URL` from `import.meta.env.VITE_API_BASE_URL` (default `http://localhost:8000`).
- `request<T>()` — attaches bearer token, JSON headers, parses the envelope, throws
  `APIError` on non‑2xx.
- Generic `api.get/post/put/delete` + **~90 named helper methods** (one per endpoint), each
  strongly typed with an interface declared at the top of the file. This file is effectively
  the full API contract in TypeScript.
- File upload / download use raw `fetch` with `FormData` / `Blob` (not the JSON wrapper).

### State
- **Auth:** `AuthContext` (token in `localStorage['cc_auth_token']`, `user` from `/auth/me`).
- **Everything else:** local `useState` + `useEffect` per page (`loading`/`error`/`data`
  triads), plus `localStorage` for small UI prefs. No global store, no cache library — pages
  refetch on mount.
- **AI waits:** `components/ui/AILoadingState.tsx` shows a friendly "the local model is
  thinking" state for the slow generative calls.

### Theming
Tailwind v3, dark "surface" + "brand" (indigo/violet) palette, glassmorphism cards,
`tailwind.config.js` defines the custom colors/animations; `index.css` adds a few custom
classes (scrollbars, fade/slide animations).

---

## 11. Background scheduler & email system

**Master switch:** everything here is gated on `SMTP_ENABLED=true`. If false, no scheduler
starts and `send_email` no‑ops.

### `email_service.py`
- `send_email(to, subject, html)` — builds a `MIMEMultipart` and sends via `aiosmtplib`
  (`use_tls` when port 465, `start_tls` when 587). Returns bool, never raises.
- `_fire_and_forget_email` — schedules the send as a background task on the running loop.
- Three richly styled dark HTML templates (shared `_BASE_STYLE`):
  1. **Task completed** — sent instantly from `update_training_task_status` when a task is
     marked `completed` (task, day objective, plan progress bar).
  2. **Morning briefing** — today's agenda + minute estimates + yesterday's recap + progress.
  3. **Evening wrap‑up** — completed vs pending today + a nudge / "day complete" callout.

### `core/scheduler.py`
- `start_scheduler()` builds an `AsyncIOScheduler` with two `CronTrigger`s in
  `REMINDER_TIMEZONE`:
  - `_morning_reminder_job` at `REMINDER_MORNING_TIME` (default 07:00/08:00)
  - `_evening_reminder_job` at `REMINDER_EVENING_TIME` (default 20:00)
  - `misfire_grace_time=3600`, `replace_existing=True`.
- Each job loads **all active `TrainingPlan`s**, and for each user with an email + active
  account: finds "today" (first incomplete day), computes yesterday completed/incomplete and
  overall progress, and sends the corresponding template. Errors are isolated per user; a 2s
  sleep between sends avoids free‑tier SMTP rate limits.
- `stop_scheduler()` on shutdown.

### `scripts/test_smtp.py`
Standalone script: `python scripts/test_smtp.py you@example.com` — verifies SMTP creds by
sending a test message.

---

## 12. Testing

- **Backend:** `pytest` + `pytest-asyncio`. `tests/conftest.py` spins up an **in‑memory
  SQLite** engine, creates/drops all tables per test (`autouse` fixture), provides a
  `db_session` fixture and an `AsyncClient` (`httpx` ASGITransport) with `get_db` overridden.
  One test file per feature (`test_auth.py`, `test_resumes.py`, `test_resume_analysis.py`,
  `test_career_intelligence.py`, `test_personal_trainer.py`, `test_email_scheduler.py`,
  `test_interviews.py`, `test_projects.py`, `test_coding.py`, `test_ollama.py`, …). AI is
  exercised via injected fake providers / the deterministic fallbacks. README cites
  "121 tests passing".
- **Frontend:** no unit tests; `npm run build` (`tsc -b && vite build`) is the type/build gate;
  `npm run lint` runs `oxlint`.

---

## 13. README vs. code — known inconsistencies

Keep these in mind; the code is authoritative.

| README says | Actual code |
|---|---|
| Coding challenges run **client‑side in Pyodide / SQLite WASM** | Run **server‑side** — Python via isolated subprocess (`python -I -S`, 3s timeout), SQL via in‑memory `sqlite3` (`services/code_executor.py`) |
| React **18.3.1**, Vite **8.2**, Lucide icons | `package.json`: React **19.2**, Vite **8.2**, **no** icon library (inline SVG + emoji) |
| FastAPI **0.110.0**, Pydantic **2.6.4** | `requirements.txt`: FastAPI **0.115.\***, Pydantic **2.10.\*** |
| **42** database tables | ~**39** ORM classes in `models/__init__.py` |
| Frontend files `MockInterview.tsx`, `CodingPractice.tsx`, `CareerRoadmap.tsx`, `LearningHub.tsx`, `Notifications.tsx`, `backend/app/core/database.py`, `scripts/seed_data.py` | Actual: `InterviewSetup/Session/Results.tsx`, `CodingDirectory/CodingEnvironment.tsx`, `Roadmap.tsx`, `LearningResources.tsx`, `NotificationsCenter.tsx`, `app/db/session.py`; seeding is inline in `main.py` + services (no `seed_data.py`) |
| "Twice‑daily emails", "Module 15" for both Personal Trainer and Projects | Docstrings reuse module numbers loosely; emails require `SMTP_ENABLED=true` |
| `pymupdf` / `python-docx` implied installed | Imported by `resume_parser.py` but **not** in `requirements.txt` |
| Password reset "sends email" | `/auth/forgot-password` returns the reset token **in the JSON response** (demo convenience) |

---

## 14. Recipe: how to add a new feature module

Follow the existing pattern (say a feature called `notes`):

1. **Model** — `backend/app/models/notes.py`: `class Note(Base)` with `user_id` FK, columns,
   `created_at`. Import it in `app/models/__init__.py` (so `create_all` picks it up).
2. **Schema** — `backend/app/schemas/notes.py`: `NoteCreateRequest`, `NoteResponse`
   (`model_config = ConfigDict(from_attributes=True)`).
3. **Service** — `backend/app/services/notes_service.py`: `async def create_note(db, user,
   req)`, `async def list_notes(db, user)`, etc. Always `.where(Note.user_id == user.id)`.
   If it needs AI: `provider = OllamaProvider(); raw = await provider.generate(prompt,
   format="json"); parsed = extract_and_parse_json(raw)` with a deterministic fallback and a
   `try/except ConnectionError → AppException(503)`.
4. **Router** — `backend/app/api/v1/notes.py`:
   ```python
   router = APIRouter(prefix="/notes", tags=["Notes"])
   @router.get("", response_model=APIEnvelope[list[NoteResponse]])
   async def list_notes_ep(current_user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
       data = await notes_service.list_notes(db, current_user)
       return APIEnvelope(status="success", message="…", data=data)
   ```
5. **Mount** — add `from app.api.v1.notes import router as notes_router` and
   `api_router.include_router(notes_router)` in `app/api/router.py`.
6. **Frontend API** — add typed helpers + interfaces to `frontend/src/lib/api.ts`.
7. **Page** — `frontend/src/pages/Notes.tsx` with the `loading/error/data` pattern; add a
   `<Route path="/notes" element={<ProtectedRoute><Notes/></ProtectedRoute>}/>` in `App.tsx`
   and a link in `Navbar.tsx`.
8. **Test** — `backend/tests/test_notes.py` using the `client` + `db_session` fixtures.

---

## 15. Quick glossary

| Term | Meaning in this project |
|---|---|
| **Envelope** | `{status, message, data}` wrapper on every API response |
| **`APIEnvelope[T]` / `APIResponse[T]`** | the Pydantic generic that produces the envelope |
| **`AppException`** | app's own exception carrying `status_code` + `message`; converted to the error envelope by global handlers |
| **`OllamaProvider`** | the only gateway to the local LLM; does caching, warmup, model fallback |
| **`extract_and_parse_json`** | resilient "get JSON out of messy LLM text" helper |
| **Deterministic fallback** | hand‑written generator used when the LLM is unavailable/invalid so the feature still works |
| **ATS score** | resume score = weighted sum of 5 LLM sub‑scores (structure 20 / skills 30 / experience 25 / education 15 / formatting 10) |
| **Readiness score** | weighted blend of Resume ATS 25 / Skill match 25 / Interview 35 / Coding 15, renormalized over available components |
| **6‑metric rubric** | interview answer scored on technical_correctness, relevance, completeness, communication, structure, clarity |
| **Rollover / carried‑over** | Personal Trainer moving yesterday's unfinished tasks into today |
| **`is_current`** | the "active" version flag on `resume_versions` |
| **`source_type`** | on questions: `standard` (seeded) vs `ai_generated` |
| **Verified company / verified job / verified resource** | curated, hard‑coded, trustworthy seed data (vs. live Adzuna or AI output) |
| **O*NET** | the occupation + weighted‑skill taxonomy (hard‑coded dataset) behind Careers & Skill Gap |
| **Seed on startup** | `jobs` + `coding_challenges` filled in `main.py` lifespan; other catalogs seed lazily on first use |

---

*End of guide. If you internalize §5 (cross‑cutting patterns), §6 (AI layer), and §8
(data model), every one of the ~20 feature sections in §9 will read as the same three moves:
query the user's rows → compute a number deterministically → ask the LLM only for prose,
with a fallback.*
