/**
 * Universal Cross-Platform Runner for AI Career & Interview Coach
 * Starts both Backend (FastAPI) and Frontend (Vite + React) with unified logging and clean process management.
 */

import { spawn, execSync } from "node:child_process";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const backendDir = path.join(rootDir, "backend");
const frontendDir = path.join(rootDir, "frontend");

const isWin = process.platform === "win32";

console.log("\n=======================================================");
console.log("   🚀 AI Career & Interview Coach - Quick Launch");
console.log("=======================================================\n");

// 1. Detect Python command
function getPythonCommand() {
  const venvPythonWin = path.join(backendDir, "venv", "Scripts", "python.exe");
  const venvPythonUnix = path.join(backendDir, "venv", "bin", "python");

  if (fs.existsSync(venvPythonWin)) return venvPythonWin;
  if (fs.existsSync(venvPythonUnix)) return venvPythonUnix;

  // System python
  const candidates = isWin ? ["python", "py", "python3"] : ["python3", "python"];
  for (const cmd of candidates) {
    try {
      execSync(`${cmd} --version`, { stdio: "ignore" });
      return cmd;
    } catch {
      // try next
    }
  }
  return null;
}

const pythonCmd = getPythonCommand();
if (!pythonCmd) {
  console.error("❌ Python 3 was not found on your system!");
  console.error("   Please install Python from https://www.python.org/downloads/ and ensure it is added to your PATH.\n");
  process.exit(1);
}

// 1b. Ensure backend dependencies installed
try {
  execSync(`"${pythonCmd}" -c "import fastapi, uvicorn, sqlalchemy, aiosqlite"`, { stdio: "ignore" });
} catch {
  console.log("📦 Installing Python backend requirements (fastapi, uvicorn, sqlalchemy, etc.)...");
  try {
    execSync(`"${pythonCmd}" -m pip install -r requirements.txt`, { cwd: backendDir, stdio: "inherit", shell: true });
    console.log("✅ Python dependencies installed successfully.\n");
  } catch (err) {
    console.warn("⚠️  Could not automatically install pip requirements:", err.message);
    console.log("   Proceeding with launch...\n");
  }
}

// 2. Ensure frontend dependencies installed
const nodeModulesPath = path.join(frontendDir, "node_modules");
if (!fs.existsSync(nodeModulesPath)) {
  console.log("📦 Installing frontend dependencies (node_modules)...");
  try {
    execSync("npm install", { cwd: frontendDir, stdio: "inherit", shell: true });
    console.log("✅ Frontend dependencies installed successfully.\n");
  } catch (err) {
    console.error("❌ Failed to install frontend dependencies:", err.message);
    process.exit(1);
  }
}

// 3. Ensure backend .env exists
const backendEnv = path.join(backendDir, ".env");
const backendEnvExample = path.join(backendDir, ".env.example");
const rootEnv = path.join(rootDir, ".env");

if (!fs.existsSync(backendEnv)) {
  if (fs.existsSync(backendEnvExample)) {
    fs.copyFileSync(backendEnvExample, backendEnv);
    console.log("⚙️  Created backend/.env from .env.example");
  } else if (fs.existsSync(rootEnv)) {
    fs.copyFileSync(rootEnv, backendEnv);
    console.log("⚙️  Created backend/.env from root .env");
  }
}

// 4. Start Backend Server
console.log("🔧 Starting FastAPI Backend (http://127.0.0.1:8000)...");
const backendProcess = spawn(
  pythonCmd,
  ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
  {
    cwd: backendDir,
    shell: isWin,
    stdio: ["ignore", "pipe", "pipe"],
  }
);

backendProcess.stdout.on("data", (data) => {
  const line = data.toString().trim();
  if (line) console.log(`\x1b[36m[Backend]\x1b[0m ${line}`);
});

backendProcess.stderr.on("data", (data) => {
  const line = data.toString().trim();
  if (line) console.log(`\x1b[33m[Backend]\x1b[0m ${line}`);
});

backendProcess.on("error", (err) => {
  console.error("❌ Backend process error:", err.message);
});

// 5. Start Frontend Dev Server
console.log("🎨 Starting Vite Frontend (http://localhost:5173)...");
const npmCmd = isWin ? "npm.cmd" : "npm";
const frontendProcess = spawn(npmCmd, ["run", "dev"], {
  cwd: frontendDir,
  shell: true,
  stdio: ["ignore", "pipe", "pipe"],
});

frontendProcess.stdout.on("data", (data) => {
  const line = data.toString().trim();
  if (line) console.log(`\x1b[32m[Frontend]\x1b[0m ${line}`);
});

frontendProcess.stderr.on("data", (data) => {
  const line = data.toString().trim();
  if (line) console.log(`\x1b[35m[Frontend]\x1b[0m ${line}`);
});

frontendProcess.on("error", (err) => {
  console.error("❌ Frontend process error:", err.message);
});

console.log("\n=======================================================");
console.log("   🌟 Services Started!");
console.log("   👉 Frontend:  http://localhost:5173");
console.log("   👉 Backend:   http://127.0.0.1:8000");
console.log("   👉 API Docs:  http://127.0.0.1:8000/docs");
console.log("   👉 Demo User: demo@example.com / Password123!");
console.log("   Press Ctrl+C at any time to shut down.");
console.log("=======================================================\n");

// Optional: Open browser automatically after 2.5 seconds
setTimeout(() => {
  const openCmd = isWin ? "start http://localhost:5173" : process.platform === "darwin" ? "open http://localhost:5173" : "xdg-open http://localhost:5173";
  try {
    execSync(openCmd, { stdio: "ignore" });
  } catch {
    // ignore if browser cannot be launched
  }
}, 2500);

// Graceful cleanup
function cleanup() {
  console.log("\n🛑 Stopping servers...");
  try {
    if (isWin) {
      if (backendProcess.pid) execSync(`taskkill /pid ${backendProcess.pid} /T /F`, { stdio: "ignore" });
      if (frontendProcess.pid) execSync(`taskkill /pid ${frontendProcess.pid} /T /F`, { stdio: "ignore" });
    } else {
      backendProcess.kill("SIGTERM");
      frontendProcess.kill("SIGTERM");
    }
  } catch {
    // ignore cleanup errors
  }
  process.exit(0);
}

process.on("SIGINT", cleanup);
process.on("SIGTERM", cleanup);
