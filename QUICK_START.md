# 🚀 Quick Start Guide (Extracted Project)

Welcome to the **AI Career & Interview Coach** platform!

Everything has been configured so anyone who extracts this folder can run the full application with **zero manual configuration**.

---

## ⚡ Method 1: Instant 1-Click Launch (Recommended)

### On Windows:
Double-click **`run.bat`** (or `start.bat`) in this root folder.

### On macOS / Linux:
Open Terminal in this folder and run:
```bash
chmod +x run.sh
./run.sh
```

### Or using npm (Any OS):
```bash
npm start
```
*(or `npm run dev`)*

> **What happens automatically:**
> - Checks Python 3 and Node.js.
> - Auto-installs backend & frontend dependencies if missing.
> - Automatically initializes SQLite database & tables.
> - Auto-seeds demo user accounts, verified job listings, and coding challenges.
> - Launches Backend (`http://127.0.0.1:8000`) and Frontend (`http://localhost:5173`).
> - Opens your default browser automatically to `http://localhost:5173`!

---

## 🔑 Demo Login Credentials

You don't even need to register or type passwords! On the login page, click the **"Quick Demo Logins"** buttons:

| Role | Email | Password |
|---|---|---|
| **Candidate Demo** | `demo@example.com` | `Password123!` |
| **System Administrator** | `admin@example.com` | `AdminPassword123!` |

*(Or register a new account on `/register` anytime)*

---

## 🌐 URLs & Services

- **Frontend Web Application:** [http://localhost:5173](http://localhost:5173)
- **FastAPI Interactive API Docs (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **API Redoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Backend Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🛠️ Method 2: Manual Terminal Launch (Optional)

If you prefer running frontend and backend in separate terminal tabs:

### Terminal 1: Backend
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2: Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🤖 Ollama (Optional)
The application includes high-speed deterministic fallbacks for core features if Ollama is not installed. To enable local AI models:
1. Download Ollama from [https://ollama.com](https://ollama.com)
2. Run: `ollama run llama3.2:3b` (or `llama3`)
3. The backend will automatically detect and warm up the model!
