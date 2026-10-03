import { useEffect, useState } from "react";
import api, { APIError, type AchievementSummaryData } from "../lib/api";


type StatusTab = "All" | "Earned" | "Locked";
const CATEGORIES = ["All", "Resume", "Interview", "Coding", "Learning", "Roadmap", "Growth"];

export default function Achievements() {
  const [summary, setSummary] = useState<AchievementSummaryData | null>(null);
  const [selectedTab, setSelectedTab] = useState<StatusTab>("All");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAchievements();
  }, []);

  const fetchAchievements = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAchievements();
      if (res.data) {
        setSummary(res.data);
      } else {
        setError("Failed to load achievements.");
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

  const handleReevaluate = async () => {
    setLoading(true);
    try {
      const res = await api.evaluateAchievements();
      if (res.data) {
        setSummary(res.data);
      }
    } catch {
      // Ignore evaluation error
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return "";
    try {
      return new Date(isoString).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return isoString;
    }
  };

  const filteredAchievements = summary?.achievements.filter((a) => {
    if (selectedTab === "Earned" && !a.is_earned) return false;
    if (selectedTab === "Locked" && a.is_earned) return false;
    if (selectedCategory !== "All" && a.category !== selectedCategory) return false;
    return true;
  }) || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-950 via-surface-900 to-amber-950/60 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-semibold">
              Module 18 • Automated Mastery & Activity Badges
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Achievements & Career Badges
            </h1>
            <p className="text-sm text-surface-200/80 max-w-2xl leading-relaxed">
              Badges are automatically awarded based on your actual activity across resume uploads, interview performances, coding challenges, and roadmap milestones.
            </p>
          </div>

          <button
            onClick={handleReevaluate}
            className="px-4 py-2.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-white font-semibold text-xs transition-colors cursor-pointer self-start sm:self-auto"
          >
            ↻ Check Badges Status
          </button>
        </div>

        {/* Progress Metric Bar */}
        {summary && (
          <div className="flex flex-wrap gap-4 pt-2 text-xs border-t border-white/5">
            <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
              Total Badges: <span className="font-bold text-white">{summary.total_achievements}</span>
            </div>
            <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
              Earned Badges: <span className="font-bold text-amber-300">{summary.earned_count}</span>
            </div>
            <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
              Mastery Progress: <span className="font-bold text-emerald-400">{summary.completion_percentage}%</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => fetchAchievements()} className="text-xs font-bold text-red-400 hover:text-red-200 cursor-pointer">
            Retry
          </button>
        </div>
      )}

      {/* Filter Tabs Toolbar */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-4 sm:p-5 space-y-4 shadow-xl">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Status Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
            {(["All", "Earned", "Locked"] as StatusTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setSelectedTab(tab)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                  selectedTab === tab
                    ? "bg-brand-600 text-white shadow-md shadow-brand-600/20"
                    : "bg-surface-800 text-surface-200/70 hover:bg-surface-700 hover:text-white"
                }`}
              >
                {tab === "Earned" ? "🎉 Earned" : tab === "Locked" ? "🔒 Locked" : "All Badges"}
              </button>
            ))}
          </div>

          {/* Category Dropdown */}
          <div className="w-full md:w-48">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  Category: {c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Achievements Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 animate-pulse">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-48 rounded-2xl bg-surface-900 border border-white/5 p-5 space-y-3" />
          ))}
        </div>
      ) : filteredAchievements.length === 0 ? (
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-surface-800 text-surface-200/40 mx-auto flex items-center justify-center text-xl">
            🏆
          </div>
          <h3 className="text-base font-bold text-white">No Achievements Found</h3>
          <p className="text-xs text-surface-200/60 max-w-sm mx-auto">
            {selectedTab === "Earned"
              ? "You haven't earned badges in this view yet. Complete resume uploads or mock interviews to earn them automatically!"
              : "No achievements match the selected filter criteria."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredAchievements.map((ach) => {
            const pct = Math.min(Math.round((ach.current_progress / ach.threshold) * 100), 100);

            return (
              <div
                key={ach.id}
                className={`rounded-2xl p-6 space-y-4 shadow-xl flex flex-col justify-between transition-all border ${
                  ach.is_earned
                    ? "bg-gradient-to-b from-surface-900 to-amber-950/20 border-amber-500/30 hover:border-amber-500/50 shadow-amber-500/5"
                    : "bg-surface-900/60 border-white/10 opacity-75 hover:opacity-100"
                }`}
              >
                <div className="space-y-3">
                  {/* Badge Icon & Category */}
                  <div className="flex items-center justify-between">
                    <div
                      className={`w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shadow-inner border ${
                        ach.is_earned
                          ? "bg-amber-500/20 border-amber-500/40 text-amber-300 shadow-amber-500/20"
                          : "bg-surface-800 border-white/10 text-surface-200/40"
                      }`}
                    >
                      {ach.icon}
                    </div>

                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                        ach.is_earned
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : "bg-surface-800 text-surface-200/60 border border-white/5"
                      }`}
                    >
                      {ach.is_earned ? "🎉 Earned" : "🔒 Locked"}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <div>
                    <div className="text-[10px] font-semibold text-surface-200/50 uppercase tracking-wider">
                      {ach.category}
                    </div>
                    <h3 className="text-base font-bold text-white mt-0.5">
                      {ach.title}
                    </h3>
                    <p className="text-xs text-surface-200/70 leading-relaxed mt-1">
                      {ach.description}
                    </p>
                  </div>
                </div>

                {/* Progress Bar & Earned Info */}
                <div className="space-y-2 pt-3 border-t border-white/5">
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-surface-200/60 font-medium">Progress</span>
                    <span className="font-bold text-white">
                      {ach.current_progress} / {ach.threshold}
                    </span>
                  </div>

                  <div className="w-full h-2 rounded-full bg-surface-800 overflow-hidden border border-white/5">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        ach.is_earned
                          ? "bg-gradient-to-r from-amber-400 to-emerald-400"
                          : "bg-brand-500/60"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>

                  {ach.is_earned && ach.earned_at && (
                    <div className="text-[10px] text-amber-300/80 font-medium text-right pt-0.5">
                      Unlocked on {formatDate(ach.earned_at)}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
