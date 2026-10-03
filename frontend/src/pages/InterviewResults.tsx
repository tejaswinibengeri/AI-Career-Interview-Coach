import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { APIError, type InterviewResultsData } from "../lib/api";

export default function InterviewResults() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [results, setResults] = useState<InterviewResultsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedQuestion, setExpandedQuestion] = useState<number | null>(null);

  const sessionId = id ? parseInt(id, 10) : NaN;

  useEffect(() => {
    if (isNaN(sessionId)) {
      setError("Invalid session ID.");
      setLoading(false);
      return;
    }

    async function fetchResults() {
      try {
        setLoading(true);
        setError(null);
        const res = await api.getInterviewResults(sessionId);
        if (res.data) {
          setResults(res.data);
          if (res.data.questions_transcript.length > 0) {
            setExpandedQuestion(res.data.questions_transcript[0].id);
          }
        } else {
          setError("Failed to load interview results.");
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
    }

    fetchResults();
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12 space-y-8 animate-pulse">
        <div className="h-48 bg-surface-900 rounded-2xl border border-white/5" />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-28 bg-surface-800 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-400 mx-auto flex items-center justify-center">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        </div>
        <h2 className="text-lg font-bold text-white">Results Not Available</h2>
        <p className="text-xs text-surface-200/70">{error || "Interview evaluation report not found."}</p>
        <button
          onClick={() => navigate("/interview")}
          className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors cursor-pointer"
        >
          Back to Interview Room
        </button>
      </div>
    );
  }

  const getScoreBadgeColor = (score: number) => {
    if (score >= 85) return "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";
    if (score >= 70) return "text-amber-400 border-amber-500/30 bg-amber-500/10";
    return "text-red-400 border-red-500/30 bg-red-500/10";
  };

  const getPerformanceLabel = (score: number) => {
    if (score >= 85) return "Outstanding Performance";
    if (score >= 70) return "Solid Competency";
    return "Needs Practice & Review";
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate("/interview")}
          className="flex items-center gap-2 text-xs font-semibold text-surface-200/70 hover:text-white transition-colors cursor-pointer"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back to Interview Dashboard
        </button>

        <button
          onClick={() => window.print()}
          className="px-3.5 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs font-semibold text-surface-200 hover:text-white transition-all cursor-pointer flex items-center gap-1.5"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12.1227H7.231a1.125 1.125 0 01-1.12-1.227L6.34 18m11.32 0H6.34" />
          </svg>
          Print Report
        </button>
      </div>

      {/* Hero Score Card */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-950 via-surface-900 to-purple-950/60 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs font-semibold">
              Module 10 • Final Report
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {results.role} Mock Interview Performance
            </h1>
            <p className="text-xs text-surface-200/70">
              Completed on{" "}
              {results.completed_at
                ? new Date(results.completed_at).toLocaleDateString(undefined, {
                    month: "long",
                    day: "numeric",
                    year: "numeric",
                  })
                : "Today"}
              {" • "}
              Difficulty: <span className="font-semibold text-white">{results.difficulty}</span>
            </p>
            <p className="text-sm text-surface-200/90 leading-relaxed pt-2 border-t border-white/10">
              {results.summary_feedback}
            </p>
          </div>

          {/* Big Score Gauge */}
          <div className="flex-shrink-0 flex flex-col items-center justify-center p-6 rounded-2xl bg-surface-950/70 border border-white/10 text-center min-w-[200px]">
            <span className="text-[11px] font-semibold text-surface-200/60 uppercase tracking-wider">Overall Score</span>
            <span className="text-4xl sm:text-5xl font-black text-emerald-400 mt-1">{results.overall_score}%</span>
            <span className={`mt-2 px-3 py-1 rounded-full text-xs font-bold border ${getScoreBadgeColor(results.overall_score)}`}>
              {getPerformanceLabel(results.overall_score)}
            </span>
          </div>
        </div>
      </div>

      {/* 6-Metric Rubric Breakdown */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-7 space-y-6 shadow-xl">
        <div className="border-b border-white/5 pb-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
            6-Metric Scoring Rubric Breakdown
          </h2>
          <p className="text-xs text-surface-200/60 mt-1">
            Consistent evaluation generated by Ollama AI based on your actual submitted answers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(results.metrics_breakdown).map(([metricName, score]) => (
            <div key={metricName} className="p-4 rounded-xl bg-surface-800/60 border border-white/5 space-y-2.5">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-white">{metricName}</span>
                <span className="font-extrabold text-brand-300">{score}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-surface-700 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    score >= 80 ? "bg-emerald-400" : score >= 60 ? "bg-amber-400" : "bg-red-400"
                  }`}
                  style={{ width: `${score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Strengths & Improvements */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 space-y-4 shadow-xl">
          <h2 className="text-base font-bold text-emerald-300 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Key Demonstrated Strengths
          </h2>
          {results.strengths.length === 0 ? (
            <p className="text-xs text-surface-200/60">No specific strengths recorded.</p>
          ) : (
            <ul className="space-y-2">
              {results.strengths.map((s, idx) => (
                <li key={idx} className="flex items-start gap-2 text-xs text-surface-200">
                  <span className="text-emerald-400 font-bold">•</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Improvements */}
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 space-y-4 shadow-xl">
          <h2 className="text-base font-bold text-amber-300 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
            </svg>
            Actionable Areas for Growth
          </h2>
          {results.improvements.length === 0 ? (
            <p className="text-xs text-surface-200/60">No specific improvement areas recorded.</p>
          ) : (
            <ul className="space-y-2">
              {results.improvements.map((imp, idx) => (
                <li key={idx} className="flex items-start gap-2 text-xs text-surface-200">
                  <span className="text-amber-400 font-bold">•</span>
                  <span>{imp}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Full Question Transcript */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-7 space-y-6 shadow-xl">
        <div className="border-b border-white/5 pb-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5A3.375 3.375 0 0010.125 2.25H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            Full Question & Evaluation Transcript
          </h2>
        </div>

        <div className="space-y-4">
          {results.questions_transcript.map((q, idx) => {
            const isExpanded = expandedQuestion === q.id;
            const ev = q.evaluation;

            return (
              <div
                key={q.id}
                className="border border-white/10 rounded-xl bg-surface-800/40 overflow-hidden transition-all"
              >
                <button
                  onClick={() => setExpandedQuestion(isExpanded ? null : q.id)}
                  className="w-full p-4 text-left flex items-center justify-between gap-4 hover:bg-surface-800/80 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-lg bg-surface-700 flex items-center justify-center text-xs font-bold text-white">
                      Q{idx + 1}
                    </span>
                    <div>
                      <h3 className="text-sm font-bold text-white max-w-2xl truncate">{q.question_text}</h3>
                      <p className="text-[11px] text-surface-200/60 mt-0.5">Category: {q.category}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    {ev && (
                      <span className="text-sm font-extrabold text-emerald-400">{ev.overall_score}%</span>
                    )}
                    <span className="text-xs text-surface-200/50">{isExpanded ? "▲" : "▼"}</span>
                  </div>
                </button>

                {isExpanded && (
                  <div className="p-5 border-t border-white/5 bg-surface-900/60 space-y-4 text-xs">
                    {/* User Answer */}
                    <div className="space-y-1">
                      <h4 className="font-bold text-surface-200 uppercase tracking-wider text-[11px]">Candidate Answer</h4>
                      <div className="p-3 rounded-lg bg-surface-800 border border-white/5 text-surface-200 whitespace-pre-wrap font-sans">
                        {q.user_answer || "No response recorded."}
                      </div>
                    </div>

                    {/* AI Feedback */}
                    {ev && (
                      <div className="space-y-3 pt-2 border-t border-white/5">
                        <div className="p-3.5 rounded-lg bg-brand-500/10 border border-brand-500/20 space-y-1">
                          <h4 className="font-bold text-brand-300 uppercase tracking-wider text-[11px]">Ollama Feedback</h4>
                          <p className="text-surface-200 leading-relaxed">{ev.feedback}</p>
                        </div>

                        {/* Ideal Answer Guide */}
                        {ev.ideal_answer && (
                          <div className="space-y-1">
                            <h4 className="font-bold text-emerald-400 uppercase tracking-wider text-[11px]">Ideal Sample Answer Guide</h4>
                            <div className="p-3 rounded-lg bg-surface-950 border border-white/5 text-surface-200/90 whitespace-pre-wrap font-mono">
                              {ev.ideal_answer}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="flex justify-center gap-4 pt-4">
        <button
          onClick={() => navigate("/interview")}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-bold text-sm shadow-xl shadow-brand-600/30 transition-all cursor-pointer"
        >
          Start Another Mock Interview →
        </button>
      </div>
    </div>
  );
}
