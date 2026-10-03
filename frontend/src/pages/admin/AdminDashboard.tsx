import { useEffect, useState } from "react";
import api, { APIError, type AdminSystemStatsData } from "../../lib/api";

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminSystemStatsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminStatistics();
      if (res.data) {
        setStats(res.data);
      } else {
        setError("Failed to load admin statistics.");
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Unable to connect to server.");
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 animate-pulse">
        {[1, 2, 3, 4, 5, 6, 7].map((i) => (
          <div key={i} className="h-32 rounded-2xl bg-surface-900 border border-white/5 p-5" />
        ))}
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex justify-between items-center">
        <span>{error || "Failed to load telemetry statistics."}</span>
        <button onClick={fetchStats} className="text-xs font-bold text-red-400 hover:text-red-200 cursor-pointer">
          Retry
        </button>
      </div>
    );
  }

  const statCards = [
    { title: "Total Users", value: stats.total_users, icon: "👥", color: "from-blue-500/20 to-blue-600/5 border-blue-500/30 text-blue-300" },
    { title: "Active Users (30d)", value: stats.active_users, icon: "⚡", color: "from-emerald-500/20 to-emerald-600/5 border-emerald-500/30 text-emerald-300" },
    { title: "Resumes Uploaded", value: stats.resumes, icon: "📄", color: "from-purple-500/20 to-purple-600/5 border-purple-500/30 text-purple-300" },
    { title: "Mock Interviews", value: stats.interviews, icon: "🎙️", color: "from-amber-500/20 to-amber-600/5 border-amber-500/30 text-amber-300" },
    { title: "Coding Submissions", value: stats.coding_submissions, icon: "💻", color: "from-cyan-500/20 to-cyan-600/5 border-cyan-500/30 text-cyan-300" },
    { title: "Job Searches & Matches", value: stats.job_searches, icon: "🎯", color: "from-indigo-500/20 to-indigo-600/5 border-indigo-500/30 text-indigo-300" },
    { title: "AI Evaluations (Ollama)", value: stats.ai_evaluations, icon: "🤖", color: "from-rose-500/20 to-rose-600/5 border-rose-500/30 text-rose-300" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">System Telemetry & Real Aggregated Stats</h2>
          <p className="text-xs text-surface-200/60">Live activity metrics aggregated directly from application database tables</p>
        </div>
        <button
          onClick={fetchStats}
          className="px-3.5 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs text-surface-200 hover:text-white font-semibold transition-colors cursor-pointer"
        >
          ↻ Refresh Stats
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((c) => (
          <div
            key={c.title}
            className={`rounded-2xl p-6 border bg-gradient-to-b space-y-3 shadow-xl ${c.color}`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider opacity-80">{c.title}</span>
              <span className="text-2xl">{c.icon}</span>
            </div>
            <div className="text-3xl font-extrabold text-white tracking-tight">
              {c.value.toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
