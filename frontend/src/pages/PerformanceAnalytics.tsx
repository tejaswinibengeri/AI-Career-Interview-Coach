import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { APIError, type PerformanceData, type ReadinessData } from "../lib/api";

export default function PerformanceAnalytics() {
  const navigate = useNavigate();

  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [perfRes, readRes] = await Promise.all([
          api.getPerformanceAnalytics(),
          api.getPlacementReadiness(),
        ]);

        if (perfRes.data) setPerformance(perfRes.data);
        if (readRes.data) setReadiness(readRes.data);
      } catch (err) {
        if (err instanceof APIError) {
          setError(err.message);
        } else {
          setError("Failed to load performance analytics data.");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-pulse">
        <div className="h-44 bg-surface-900 rounded-2xl border border-white/5" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="h-28 bg-surface-800 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-400 mx-auto flex items-center justify-center">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        </div>
        <h2 className="text-lg font-bold text-white">Error Loading Analytics</h2>
        <p className="text-xs text-surface-200/70">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors cursor-pointer"
        >
          Retry
        </button>
      </div>
    );
  }

  const perf = performance;
  const read = readiness;

  // Chart max score helper
  const maxScoreHistory = perf?.score_history && perf.score_history.length > 0
    ? Math.max(...perf.score_history.map((item) => item.score), 100)
    : 100;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-950 via-surface-900 to-purple-950/60 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs font-semibold">
          Module 11 • Analytics & Readiness
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Interview Performance & Placement Readiness
        </h1>
        <p className="text-sm text-surface-200/80 max-w-3xl leading-relaxed">
          Comprehensive performance analytics derived strictly from real stored database activity. Track your score trajectory, 6-rubric strengths, and transparent placement readiness formula.
        </p>
      </div>

      {/* Top Metrics Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {/* Total Interviews */}
        <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-1 shadow-lg">
          <span className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">Total Interviews</span>
          <p className="text-2xl font-black text-white">{perf?.total_interviews ?? 0}</p>
          <span className="text-[10px] text-surface-200/50 block">Completed Mock Sessions</span>
        </div>

        {/* Average Score */}
        <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-1 shadow-lg">
          <span className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">Average Score</span>
          <p className="text-2xl font-black text-brand-300">
            {perf?.average_score !== null && perf?.average_score !== undefined ? `${perf.average_score}%` : "Not enough data"}
          </p>
          <span className="text-[10px] text-surface-200/50 block">Mean Overall Session Score</span>
        </div>

        {/* Best Score */}
        <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-1 shadow-lg">
          <span className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">Best Score</span>
          <p className="text-2xl font-black text-emerald-400">
            {perf?.best_score !== null && perf?.best_score !== undefined ? `${perf.best_score}%` : "Not enough data"}
          </p>
          <span className="text-[10px] text-surface-200/50 block">Personal Record</span>
        </div>

        {/* Latest Score */}
        <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-1 shadow-lg">
          <span className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">Latest Score</span>
          <p className="text-2xl font-black text-purple-300">
            {perf?.latest_score !== null && perf?.latest_score !== undefined ? `${perf.latest_score}%` : "Not enough data"}
          </p>
          <span className="text-[10px] text-surface-200/50 block">Most Recent Interview</span>
        </div>

        {/* Score Improvement */}
        <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-1 shadow-lg">
          <span className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">Score Improvement</span>
          <p className={`text-2xl font-black ${
            perf?.improvement && perf.improvement > 0
              ? "text-emerald-400"
              : perf?.improvement && perf.improvement < 0
              ? "text-red-400"
              : "text-white"
          }`}>
            {perf?.improvement !== null && perf?.improvement !== undefined
              ? `${perf.improvement > 0 ? "+" : ""}${perf.improvement}%`
              : "Not enough data"}
          </p>
          <span className="text-[10px] text-surface-200/50 block">First vs Latest Session</span>
        </div>

        {/* Technical Score */}
        <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-1 shadow-lg">
          <span className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">Technical Score</span>
          <p className="text-2xl font-black text-cyan-400">
            {perf?.technical_score !== null && perf?.technical_score !== undefined ? `${perf.technical_score}%` : "Not enough data"}
          </p>
          <span className="text-[10px] text-surface-200/50 block">Rubric Technical Mean</span>
        </div>

        {/* Communication Score */}
        <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-1 shadow-lg">
          <span className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">Communication</span>
          <p className="text-2xl font-black text-amber-300">
            {perf?.communication_score !== null && perf?.communication_score !== undefined ? `${perf.communication_score}%` : "Not enough data"}
          </p>
          <span className="text-[10px] text-surface-200/50 block">Rubric Communication Mean</span>
        </div>

        {/* Placement Readiness */}
        <div className="p-4 rounded-xl bg-surface-900 border border-white/10 space-y-1 shadow-lg">
          <span className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">Readiness Score</span>
          <p className="text-2xl font-black text-emerald-400">
            {read?.overall_readiness_score !== null && read?.overall_readiness_score !== undefined ? `${read.overall_readiness_score}%` : "Not Evaluated"}
          </p>
          <span className="text-[10px] text-surface-200/50 block">{read?.level || "Not enough data"}</span>
        </div>
      </div>

      {/* Section 1: Placement Readiness Calculation Breakdown */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-7 space-y-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296a3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
              </svg>
              Transparent Placement Readiness Formula
            </h2>
            <p className="text-xs text-surface-200/60 mt-1">
              Evaluated strictly from available candidate metrics (Resume, Skills, Interview, Coding) using dynamic normalized weights.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`px-3.5 py-1.5 rounded-full text-xs font-extrabold border ${
                read?.overall_readiness_score && read.overall_readiness_score >= 80
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : read?.overall_readiness_score && read.overall_readiness_score >= 65
                  ? "bg-amber-500/10 text-amber-300 border-amber-500/30"
                  : "bg-surface-800 text-surface-200 border-white/10"
              }`}
            >
              {read?.level || "Not Evaluated"}
            </span>
          </div>
        </div>

        <p className="text-xs text-surface-200/90 leading-relaxed bg-surface-800/40 p-4 rounded-xl border border-white/5">
          💬 <span className="font-semibold text-white">Assessor Status:</span> {read?.status_message}
        </p>

        {/* Readiness Components Formula Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {read?.breakdown.map((comp) => (
            <div
              key={comp.key}
              className={`p-4 rounded-xl border transition-all ${
                comp.available
                  ? "bg-surface-800/60 border-white/10"
                  : "bg-surface-950/40 border-dashed border-white/10"
              }`}
            >
              <div className="flex justify-between items-start gap-2">
                <div>
                  <h3 className="text-sm font-bold text-white">{comp.name}</h3>
                  <p className="text-[11px] text-surface-200/60 mt-0.5">
                    Target Weight: {Math.round(comp.raw_weight * 100)}%
                    {comp.available && (
                      <span className="text-brand-300 font-semibold ml-1">
                        (Effective: {comp.effective_weight_percentage}%)
                      </span>
                    )}
                  </p>
                </div>

                <span
                  className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                    comp.available
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-surface-800 text-surface-200/50 border border-white/5"
                  }`}
                >
                  {comp.status}
                </span>
              </div>

              {comp.available && comp.score !== null && comp.score !== undefined ? (
                <div className="mt-3 space-y-1">
                  <div className="w-full h-2 rounded-full bg-surface-700 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-brand-500 to-emerald-400 rounded-full"
                      style={{ width: `${comp.score}%` }}
                    />
                  </div>
                </div>
              ) : (
                <p className="text-[11px] text-surface-200/40 italic mt-2">
                  Not enough data available to include in readiness calculation.
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Recommendations */}
        {read?.recommendations && read.recommendations.length > 0 && (
          <div className="p-4 rounded-xl bg-brand-500/10 border border-brand-500/20 space-y-2">
            <h3 className="text-xs font-bold text-brand-300 uppercase tracking-wider">
              Readiness Action Plan & Next Steps
            </h3>
            <ul className="space-y-1.5 text-xs text-surface-200 list-disc list-inside">
              {read.recommendations.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Section 2: Real Database Score History Chart */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-7 space-y-6 shadow-xl">
        <div className="flex items-center justify-between border-b border-white/5 pb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 005.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
              </svg>
              Interview Score Progression Trajectory
            </h2>
            <p className="text-xs text-surface-200/60 mt-1">
              Actual database session scores plotted chronologically. (Never displays fake history).
            </p>
          </div>
          <span className="text-xs font-medium text-surface-200/60">
            {perf?.score_history.length ?? 0} Real Data Points
          </span>
        </div>

        {!perf?.score_history || perf.score_history.length === 0 ? (
          <div className="text-center py-12 space-y-3 bg-surface-950/40 rounded-xl border border-dashed border-white/10">
            <div className="w-12 h-12 rounded-full bg-surface-800 text-surface-200/40 mx-auto flex items-center justify-center">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <p className="text-sm font-bold text-white">Not enough interview data</p>
            <p className="text-xs text-surface-200/60 max-w-sm mx-auto">
              Complete mock interview sessions in the Mock Interview Room to generate real progression charts.
            </p>
            <button
              onClick={() => navigate("/interview")}
              className="mt-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors cursor-pointer"
            >
              Start First Mock Interview →
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Visual Bar Chart */}
            <div className="h-64 flex items-end justify-around gap-2 pt-6 px-4 bg-surface-950/60 rounded-xl border border-white/5 overflow-x-auto">
              {perf.score_history.map((item) => {
                const heightPct = Math.max(15, Math.round((item.score / maxScoreHistory) * 100));
                return (
                  <div key={item.session_id} className="flex flex-col items-center gap-2 group flex-1 max-w-[80px]">
                    <span className="text-xs font-bold text-emerald-400 group-hover:scale-110 transition-transform">
                      {item.score}%
                    </span>
                    <div
                      className="w-full bg-gradient-to-t from-brand-600 to-emerald-400 rounded-t-lg transition-all duration-500 shadow-lg shadow-brand-500/20 group-hover:from-brand-500 group-hover:to-emerald-300"
                      style={{ height: `${heightPct}%` }}
                    />
                    <span className="text-[10px] text-surface-200/70 font-semibold truncate w-full text-center">
                      Int #{item.interview_number}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Score History Table */}
            <div className="overflow-x-auto border border-white/5 rounded-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-800/80 text-surface-200/70 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Interview #</th>
                    <th className="px-4 py-3">Role</th>
                    <th className="px-4 py-3">Difficulty</th>
                    <th className="px-4 py-3">Score</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-surface-200">
                  {perf.score_history.map((item) => (
                    <tr key={item.session_id} className="hover:bg-surface-800/40 transition-colors">
                      <td className="px-4 py-3 font-bold text-white">Interview {item.interview_number}</td>
                      <td className="px-4 py-3 font-medium">{item.role}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-surface-800 border border-white/10 font-semibold">
                          {item.difficulty}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-extrabold text-emerald-400">{item.score}%</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => navigate(`/interview/${item.session_id}/results`)}
                          className="px-2.5 py-1 rounded-lg bg-surface-700 hover:bg-surface-600 text-white font-medium text-[11px] transition-colors cursor-pointer"
                        >
                          View Report 📊
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Section 3: Topic Strengths & Weaknesses Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strong Topics */}
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 space-y-4 shadow-xl">
          <h2 className="text-base font-bold text-emerald-300 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Strong Topics (≥75% Score)
          </h2>

          {!perf?.strong_topics || perf.strong_topics.length === 0 ? (
            <p className="text-xs text-surface-200/60">Not enough data to categorize strong topics yet.</p>
          ) : (
            <div className="space-y-3">
              {perf.strong_topics.map((t) => (
                <div key={t.topic} className="p-3 rounded-xl bg-surface-800/60 border border-white/5 space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-white">{t.topic}</span>
                    <span className="font-extrabold text-emerald-400">{t.avg_score}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-surface-700 overflow-hidden">
                    <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${t.avg_score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Weak Topics */}
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 space-y-4 shadow-xl">
          <h2 className="text-base font-bold text-amber-300 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
            </svg>
            Weak Topics & Growth Areas
          </h2>

          {!perf?.weak_topics || perf.weak_topics.length === 0 ? (
            <p className="text-xs text-surface-200/60">No weak topic areas identified yet.</p>
          ) : (
            <div className="space-y-3">
              {perf.weak_topics.map((t) => (
                <div key={t.topic} className="p-3 rounded-xl bg-surface-800/60 border border-white/5 space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-white">{t.topic}</span>
                    <span className="font-extrabold text-amber-400">{t.avg_score}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-surface-700 overflow-hidden">
                    <div className="h-full bg-amber-400 rounded-full" style={{ width: `${t.avg_score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
