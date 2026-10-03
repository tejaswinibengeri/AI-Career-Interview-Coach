import { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { APIError, type SkillGapReportData } from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

export default function SkillGap() {
  const navigate = useNavigate();
  const [report, setReport] = useState<SkillGapReportData | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadLatestReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getLatestSkillGap();
      if (res.data) {
        setReport(res.data);
      }
    } catch (err) {
      if (err instanceof APIError && err.status === 404) {
        setError("NO_REPORT");
      } else if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to load skill gap report.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLatestReport();
  }, [loadLatestReport]);

  const formatDate = (isoString: string) => {
    try {
      return new Date(isoString).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 mx-auto flex items-center justify-center shadow-lg animate-pulse">
          <LoadingSpinner size="lg" />
        </div>
        <h2 className="text-xl font-bold text-white">Loading Skill Gap Report...</h2>
      </div>
    );
  }

  if (error === "NO_REPORT" || !report) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-lg mx-auto rounded-2xl bg-surface-900 border border-white/10 p-8 text-center space-y-5 shadow-xl">
          <div className="w-14 h-14 rounded-full bg-brand-500/10 text-brand-400 mx-auto flex items-center justify-center border border-brand-500/20">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-bold text-white">No Skill Gap Analysis Yet</h2>
            <p className="text-xs text-surface-200/70">
              Select a target occupation from our O*NET dataset to compare your actual skills and generate a personalized skill gap analysis.
            </p>
          </div>

          <Link
            to="/career"
            className="inline-block px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 transition-all"
          >
            Browse Careers & Run Analysis
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link to="/career" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 mb-2 font-medium">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
            Back to Careers
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Skill Gap Analysis Report
          </h1>
          <p className="text-xs text-surface-200/70 mt-1">
            Target Occupation: <span className="font-semibold text-white">{report.occupation_title}</span> • Evaluated on {formatDate(report.created_at)}
          </p>
        </div>

        <Link
          to="/career"
          className="px-4 py-2.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs font-semibold text-surface-200 hover:text-white transition-all self-start sm:self-auto cursor-pointer"
        >
          Analyze Another Career
        </Link>
      </div>

      {/* Match Percentage Banner */}
      <div className="rounded-2xl bg-gradient-to-br from-surface-900 via-surface-800 to-surface-900 border border-brand-500/20 p-6 sm:p-8 shadow-xl grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        <div className="flex flex-col items-center justify-center text-center space-y-2 md:border-r border-white/10 md:pr-6">
          <div className="relative w-32 h-32 flex items-center justify-center rounded-full bg-surface-950 border-4 border-brand-500/30 shadow-inner">
            <div className="text-center">
              <span className="text-3xl font-extrabold text-white">{report.match_percentage}%</span>
              <p className="text-[10px] uppercase font-bold text-brand-400">Role Readiness</p>
            </div>
          </div>
        </div>

        <div className="md:col-span-2 space-y-3">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-white">Career Alignment Summary</h3>
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
              report.match_percentage >= 75 ? "bg-emerald-500/20 text-emerald-300" :
              report.match_percentage >= 50 ? "bg-amber-500/20 text-amber-300" : "bg-red-500/20 text-red-300"
            }`}>
              {report.match_percentage >= 75 ? "High Readiness Match" :
               report.match_percentage >= 50 ? "Moderate Alignment" : "Skill Gap Action Required"}
            </span>
          </div>

          <p className="text-xs text-surface-200/80 leading-relaxed bg-surface-950/60 p-4 rounded-xl border border-white/5">
            {report.ai_explanation}
          </p>
        </div>
      </div>

      {/* Skills Comparison Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Strong Skills */}
        <div className="rounded-2xl bg-surface-900/80 border border-emerald-500/20 p-6 space-y-4 shadow-md">
          <h3 className="text-sm font-bold text-emerald-400 flex items-center justify-between">
            <span>Strong Matched Skills</span>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-xs font-bold">{report.strong_skills.length}</span>
          </h3>

          {report.strong_skills.length === 0 ? (
            <p className="text-xs text-surface-200/50 italic">No strong skill matches identified yet.</p>
          ) : (
            <div className="space-y-2">
              {report.strong_skills.map((sk, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-surface-800/60 border border-white/5 flex items-center justify-between text-xs">
                  <span className="font-semibold text-white">{sk.name}</span>
                  <span className="text-[10px] text-emerald-400 font-medium">Matched</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Intermediate Skills */}
        <div className="rounded-2xl bg-surface-900/80 border border-blue-500/20 p-6 space-y-4 shadow-md">
          <h3 className="text-sm font-bold text-blue-400 flex items-center justify-between">
            <span>Intermediate Skills</span>
            <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-xs font-bold">{report.intermediate_skills.length}</span>
          </h3>

          {report.intermediate_skills.length === 0 ? (
            <p className="text-xs text-surface-200/50 italic">No intermediate skills detected.</p>
          ) : (
            <div className="space-y-2">
              {report.intermediate_skills.map((sk, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-surface-800/60 border border-white/5 flex items-center justify-between text-xs">
                  <span className="font-semibold text-white">{sk.name}</span>
                  <span className="text-[10px] text-blue-300 font-medium">Partial</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Missing Skills */}
        <div className="rounded-2xl bg-surface-900/80 border border-amber-500/20 p-6 space-y-4 shadow-md">
          <h3 className="text-sm font-bold text-amber-400 flex items-center justify-between">
            <span>Missing Target Skills</span>
            <span className="px-2 py-0.5 rounded-full bg-amber-500/10 text-xs font-bold">{report.missing_skills.length}</span>
          </h3>

          {report.missing_skills.length === 0 ? (
            <p className="text-xs text-emerald-400 font-semibold">All required occupation skills matched!</p>
          ) : (
            <div className="space-y-2">
              {report.missing_skills.map((sk, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-surface-800/60 border border-white/5 flex items-center justify-between text-xs">
                  <span className="font-semibold text-white">{sk.name}</span>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      sk.priority === "High" ? "bg-red-500/20 text-red-300" :
                      sk.priority === "Medium" ? "bg-amber-500/20 text-amber-300" : "bg-surface-700 text-surface-300"
                    }`}>
                      {sk.priority || "Required"} Priority
                    </span>
                    <button
                      onClick={() => navigate(`/learning-resources?skill=${encodeURIComponent(sk.name)}`)}
                      className="px-2.5 py-1 rounded-lg bg-brand-600/30 hover:bg-brand-600 border border-brand-500/30 text-brand-300 hover:text-white text-[10px] font-bold transition-all cursor-pointer"
                    >
                      Learn Skill 📚
                    </button>
                  </div>
                </div>

              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recommended Step-by-Step Learning Order */}
      <div className="rounded-2xl bg-surface-900/80 border border-white/10 p-6 sm:p-8 space-y-6 shadow-md">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          AI-Recommended Learning Roadmap
        </h3>

        {report.learning_order.length === 0 ? (
          <p className="text-xs text-surface-200/60 italic">No learning steps required — your profile aligns with target role requirements.</p>
        ) : (
          <div className="space-y-4">
            {report.learning_order.map((step, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-surface-800/60 border border-white/5 flex items-start gap-4 text-xs">
                <div className="w-8 h-8 rounded-xl bg-brand-500/20 border border-brand-500/40 text-brand-300 font-bold flex items-center justify-center shrink-0">
                  {step.step || idx + 1}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-white">{step.skill_name}</h4>
                    {step.priority && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-surface-700 text-surface-200">
                        {step.priority} Priority
                      </span>
                    )}
                  </div>
                  <p className="text-surface-200/70 leading-relaxed">{step.rationale}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
