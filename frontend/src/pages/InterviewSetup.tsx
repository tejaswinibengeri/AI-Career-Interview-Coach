import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { APIError, type InterviewSessionData, type ProfileData } from "../lib/api";

const POPULAR_ROLES = [
  "Software Engineer",
  "Python Backend Developer",
  "Full Stack Engineer (React + Node)",
  "AI & Machine Learning Engineer",
  "FastAPI & Cloud Engineer",
  "Data Scientist & Analyst",
  "DevOps & Kubernetes Engineer",
  "PostgreSQL Database Architect",
  "Mobile App Developer (Flutter/React Native)",
];

export default function InterviewSetup() {
  const navigate = useNavigate();
  const [role, setRole] = useState<string>("Software Engineer");
  const [difficulty, setDifficulty] = useState<string>("Medium");
  const [totalQuestions, setTotalQuestions] = useState<number>(3);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [pastSessions, setPastSessions] = useState<InterviewSessionData[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(true);

  // Load user profile for prefilling role and past sessions history
  useEffect(() => {
    async function loadInitialData() {
      setLoadingHistory(true);
      try {
        const [profRes, sessionsRes] = await Promise.allSettled([
          api.get<ProfileData>("/api/v1/profile"),
          api.getUserInterviews(),
        ]);

        if (profRes.status === "fulfilled" && profRes.value.data) {
          const p = profRes.value.data;
          if (p.target_role) {
            setRole(p.target_role);
          } else if (p.current_role) {
            setRole(p.current_role);
          }
        }

        if (sessionsRes.status === "fulfilled" && sessionsRes.value.data) {
          setPastSessions(sessionsRes.value.data);
        }
      } catch (err) {
        console.error("Error loading interview setup data:", err);
      } finally {
        setLoadingHistory(false);
      }
    }

    loadInitialData();
  }, []);

  const handleStartInterview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!role.trim()) {
      setError("Please select or specify a target job role.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.createInterviewSession({
        role: role.trim(),
        difficulty,
        total_questions: totalQuestions,
      });

      if (response.data) {
        navigate(`/interview/${response.data.id}`);
      } else {
        setError("Failed to create interview session.");
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("An error occurred while creating the interview session.");
      }
    } finally {
      setLoading(false);
    }
  };

  const completedCount = pastSessions.filter((s) => s.status === "completed").length;
  const scoredSessions = pastSessions.filter((s) => s.overall_score !== null && s.overall_score !== undefined);
  const avgScore = scoredSessions.length
    ? Math.round(scoredSessions.reduce((acc, s) => acc + (s.overall_score || 0), 0) / scoredSessions.length)
    : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-900/60 via-surface-900 to-purple-950/40 border border-white/10 p-6 sm:p-8 shadow-2xl">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs font-semibold">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 003-3V4.5a3 3 0 10-6 0v8.25a3 3 0 003 3z" />
            </svg>
            Module 10 • AI Mock Interview Room
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Practice Real-Time Interviews with Ollama AI
          </h1>
          <p className="text-sm text-surface-200/80 leading-relaxed">
            Select your target role and difficulty to simulate a live interview. Get evaluated across 6 key metrics: Technical Correctness, Relevance, Completeness, Communication, Structure, and Clarity.
          </p>
        </div>

        {/* Dynamic Stats Badges */}
        <div className="mt-6 pt-6 border-t border-white/10 grid grid-cols-2 sm:grid-cols-3 gap-4">
          <div className="bg-surface-800/50 backdrop-blur-md rounded-xl p-3.5 border border-white/5">
            <p className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">Completed Sessions</p>
            <p className="text-xl font-bold text-white mt-1">{completedCount}</p>
          </div>
          <div className="bg-surface-800/50 backdrop-blur-md rounded-xl p-3.5 border border-white/5">
            <p className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">Average Score</p>
            <p className="text-xl font-bold text-emerald-400 mt-1">{avgScore > 0 ? `${avgScore}%` : "N/A"}</p>
          </div>
          <div className="col-span-2 sm:col-span-1 bg-surface-800/50 backdrop-blur-md rounded-xl p-3.5 border border-white/5">
            <p className="text-[11px] font-medium text-surface-200/60 uppercase tracking-wider">AI Provider Status</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-semibold text-surface-200">Ollama Connected</span>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 flex-shrink-0 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-xs text-red-400 hover:text-red-200 font-semibold cursor-pointer">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Grid: Form Setup + Past Sessions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Configure Form */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-7 space-y-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                </svg>
                Configure Interview Session
              </h2>
              <span className="text-xs text-surface-200/60">Step 1 of 3</span>
            </div>

            <form onSubmit={handleStartInterview} className="space-y-6">
              {/* Target Role Input */}
              <div className="space-y-3">
                <label htmlFor="interview-role-input" className="block text-xs font-semibold text-surface-200 uppercase tracking-wider">
                  Target Job Role
                </label>
                <input
                  id="interview-role-input"
                  type="text"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="e.g. Senior Frontend Engineer"
                  className="w-full px-4 py-3 rounded-xl bg-surface-800 border border-white/10 text-white placeholder-surface-200/40 text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                  required
                />
                <div className="flex flex-wrap gap-2 pt-1">
                  <span className="text-[11px] text-surface-200/50 self-center">Popular choices:</span>
                  {POPULAR_ROLES.map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setRole(r)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-colors cursor-pointer ${
                        role === r
                          ? "bg-brand-500/20 text-brand-300 border border-brand-500/30"
                          : "bg-surface-800 hover:bg-surface-700 text-surface-200/70 border border-white/5"
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>

              {/* Difficulty Selection */}
              <div className="space-y-3">
                <label className="block text-xs font-semibold text-surface-200 uppercase tracking-wider">
                  Select Difficulty
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { level: "Easy", desc: "Core basics & foundational questions" },
                    { level: "Medium", desc: "Standard industry depth & scenarios" },
                    { level: "Hard", desc: "Complex architecture & deep edge cases" },
                  ].map((item) => (
                    <button
                      key={item.level}
                      type="button"
                      onClick={() => setDifficulty(item.level)}
                      className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                        difficulty === item.level
                          ? "bg-brand-500/15 border-brand-500 text-white shadow-lg shadow-brand-500/10"
                          : "bg-surface-800/60 border-white/10 text-surface-200/70 hover:border-white/20 hover:text-white"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold">{item.level}</span>
                        {difficulty === item.level && (
                          <span className="w-2 h-2 rounded-full bg-brand-400" />
                        )}
                      </div>
                      <p className="text-[11px] mt-1 text-surface-200/60 leading-tight">{item.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Total Questions Selection */}
              <div className="space-y-3">
                <label className="block text-xs font-semibold text-surface-200 uppercase tracking-wider">
                  Number of Questions
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { count: 3, label: "3 Questions", tag: "Quick Warmup" },
                    { count: 5, label: "5 Questions", tag: "Standard Session" },
                    { count: 10, label: "10 Questions", tag: "Full Interview" },
                  ].map((item) => (
                    <button
                      key={item.count}
                      type="button"
                      onClick={() => setTotalQuestions(item.count)}
                      className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                        totalQuestions === item.count
                          ? "bg-brand-500/15 border-brand-500 text-white shadow-lg shadow-brand-500/10"
                          : "bg-surface-800/60 border-white/10 text-surface-200/70 hover:border-white/20 hover:text-white"
                      }`}
                    >
                      <p className="text-sm font-bold">{item.label}</p>
                      <p className="text-[11px] mt-0.5 text-brand-300/80 font-medium">{item.tag}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  id="start-interview-submit-btn"
                  className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-bold text-sm shadow-xl shadow-brand-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Generating Role Questions...</span>
                    </>
                  ) : (
                    <>
                      <span>Start Interview Session</span>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                      </svg>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: History & Past Sessions */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 space-y-5 shadow-xl">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Interview History
              </h2>
              <span className="text-xs text-surface-200/60">{pastSessions.length} total</span>
            </div>

            {loadingHistory ? (
              <div className="space-y-3 py-4 animate-pulse">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 bg-surface-800/50 rounded-xl border border-white/5" />
                ))}
              </div>
            ) : pastSessions.length === 0 ? (
              <div className="text-center py-10 space-y-3">
                <div className="w-12 h-12 rounded-full bg-surface-800 text-surface-200/40 mx-auto flex items-center justify-center">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 003-3V4.5a3 3 0 10-6 0v8.25a3 3 0 003 3z" />
                  </svg>
                </div>
                <p className="text-xs font-medium text-surface-200/70">No mock interviews completed yet.</p>
                <p className="text-[11px] text-surface-200/50">Start your first interview session above to get instant AI rubric feedback.</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
                {pastSessions.map((session) => (
                  <div
                    key={session.id}
                    className="p-4 rounded-xl bg-surface-800/60 border border-white/5 hover:border-white/15 transition-all space-y-2.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="text-sm font-bold text-white">{session.role}</h3>
                        <p className="text-[11px] text-surface-200/60 mt-0.5">
                          {new Date(session.created_at).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                          {" • "}
                          {session.total_questions} Questions
                        </p>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          session.difficulty === "Hard"
                            ? "bg-red-500/10 text-red-300 border border-red-500/20"
                            : session.difficulty === "Medium"
                            ? "bg-amber-500/10 text-amber-300 border border-amber-500/20"
                            : "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                        }`}
                      >
                        {session.difficulty}
                      </span>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-white/5 text-xs">
                      {session.status === "completed" ? (
                        <div className="flex items-center gap-1.5">
                          <span className="text-[11px] text-surface-200/60">Score:</span>
                          <span className="font-bold text-emerald-400">
                            {session.overall_score !== null ? `${session.overall_score}%` : "Evaluated"}
                          </span>
                        </div>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-[11px] text-amber-400 font-medium">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                          In Progress ({session.current_question_index}/{session.total_questions})
                        </span>
                      )}

                      {session.status === "completed" ? (
                        <button
                          onClick={() => navigate(`/interview/${session.id}/results`)}
                          className="px-3 py-1 rounded-lg bg-surface-700 hover:bg-surface-600 text-white font-medium text-[11px] transition-colors cursor-pointer"
                        >
                          View Results 📊
                        </button>
                      ) : (
                        <button
                          onClick={() => navigate(`/interview/${session.id}`)}
                          className="px-3 py-1 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-medium text-[11px] transition-colors cursor-pointer"
                        >
                          Resume →
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
