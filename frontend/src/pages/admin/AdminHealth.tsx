import { useEffect, useState } from "react";
import api, { APIError, type HealthData } from "../../lib/api";

export default function AdminHealth() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>("");

  useEffect(() => {
    fetchHealth();
  }, []);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getHealth();
      if (res.data) {
        setHealth(res.data);
        setLastChecked(new Date().toLocaleTimeString());
      } else {
        setError("Failed to fetch system health data.");
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Unable to connect to backend server.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">Platform Health & Service Status</h2>
          <p className="text-xs text-surface-200/60">
            Real-time ping and operational readiness checks for core system infrastructure.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastChecked && (
            <span className="text-[11px] text-surface-200/60 font-mono">
              Last checked: {lastChecked}
            </span>
          )}
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs text-surface-200 hover:text-white font-semibold transition-colors cursor-pointer disabled:opacity-50"
          >
            {loading ? "Checking..." : "↻ Re-check Status"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchHealth} className="text-xs underline font-bold cursor-pointer">
            Retry
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Main API Status */}
          <div className="rounded-2xl p-6 border bg-surface-900/80 border-white/10 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-surface-200/70">
                Core API Server
              </span>
              <span className="text-xl">⚡</span>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`w-3.5 h-3.5 rounded-full ${
                  health?.status === "healthy" ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                }`}
              />
              <span className="text-xl font-extrabold text-white capitalize">
                {health?.status || "Unknown"}
              </span>
            </div>
            <div className="pt-2 border-t border-white/5 text-xs text-surface-200/60 space-y-1">
              <div>Version: <span className="font-mono text-white">{health?.version || "1.0.0"}</span></div>
              <div>Protocol: <span className="font-mono text-emerald-400">FastAPI Async (HTTP/1.1)</span></div>
            </div>
          </div>

          {/* Database Status */}
          <div className="rounded-2xl p-6 border bg-surface-900/80 border-white/10 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-surface-200/70">
                Database Engine
              </span>
              <span className="text-xl">🗄️</span>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`w-3.5 h-3.5 rounded-full ${
                  health?.database === "connected" ? "bg-emerald-400" : "bg-red-400"
                }`}
              />
              <span className="text-xl font-extrabold text-white capitalize">
                {health?.database || "Disconnected"}
              </span>
            </div>
            <div className="pt-2 border-t border-white/5 text-xs text-surface-200/60 space-y-1">
              <div>Dialect: <span className="font-mono text-white">SQLAlchemy Async Engine</span></div>
              <div>Connection Pool: <span className="font-mono text-emerald-400">Active</span></div>
            </div>
          </div>

          {/* Ollama AI Service Status */}
          <div className="rounded-2xl p-6 border bg-surface-900/80 border-white/10 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-surface-200/70">
                Ollama AI Inference
              </span>
              <span className="text-xl">🤖</span>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`w-3.5 h-3.5 rounded-full ${
                  health?.ollama === "connected" ? "bg-emerald-400" : "bg-amber-400"
                }`}
              />
              <span className="text-xl font-extrabold text-white capitalize">
                {health?.ollama || "Unavailable"}
              </span>
            </div>
            <div className="pt-2 border-t border-white/5 text-xs text-surface-200/60 space-y-1">
              <div>Default Model: <span className="font-mono text-white">llama3.2:3b</span></div>
              <div>Endpoint: <span className="font-mono text-surface-200/80">http://localhost:11434</span></div>
            </div>
          </div>
        </div>
      )}

      {/* Infrastructure Guidance */}
      <div className="p-5 rounded-2xl bg-surface-900/40 border border-white/5 space-y-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-surface-200">
          Admin Operational Notes
        </h3>
        <p className="text-xs text-surface-200/70 leading-relaxed">
          The platform operates locally with zero cloud dependencies for local privacy. If Ollama shows as &quot;unavailable&quot;, ensure the Ollama desktop service is launched and the model <code className="text-brand-300 font-mono">llama3.2:3b</code> is pulled via terminal (<code className="text-brand-300 font-mono">ollama run llama3.2:3b</code>).
        </p>
      </div>
    </div>
  );
}
