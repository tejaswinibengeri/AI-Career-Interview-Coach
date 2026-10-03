import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, {
  APIError,
  type CodingAIHintData,
  type CodingChallengeData,
  type CodingSubmissionData,
} from "../lib/api";

type LeftTab = "problem" | "submissions" | "ai_hint";

export default function CodingEnvironment() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const [challenge, setChallenge] = useState<CodingChallengeData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Active Left Pane Tab
  const [activeTab, setActiveTab] = useState<LeftTab>("problem");

  // Code Editor state
  const [code, setCode] = useState<string>("");
  const [executing, setExecuting] = useState<boolean>(false);
  const [latestSubmission, setLatestSubmission] = useState<CodingSubmissionData | null>(null);

  // Submissions history
  const [submissions, setSubmissions] = useState<CodingSubmissionData[]>([]);
  const [loadingSubmissions, setLoadingSubmissions] = useState<boolean>(false);

  // AI Hint state
  const [aiHint, setAiHint] = useState<CodingAIHintData | null>(null);
  const [loadingHint, setLoadingHint] = useState<boolean>(false);

  useEffect(() => {
    if (!slug) return;

    async function fetchChallengeData() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getCodingChallengeDetail(slug as string);

        if (res.data) {
          setChallenge(res.data);
          setCode(res.data.starter_code);
          fetchSubmissions(res.data.id);
        } else {
          setError("Failed to load coding challenge.");
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

    fetchChallengeData();
  }, [slug]);

  const fetchSubmissions = async (chId: number) => {
    setLoadingSubmissions(true);
    try {
      const res = await api.getCodingSubmissions(chId);
      if (res.data) {
        setSubmissions(res.data);
      }
    } catch {
      // Ignore submission fetch errors
    } finally {
      setLoadingSubmissions(false);
    }
  };

  const handleTabIndent = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;

      const newCode = code.substring(0, start) + "    " + code.substring(end);
      setCode(newCode);

      setTimeout(() => {
        target.selectionStart = target.selectionEnd = start + 4;
      }, 0);
    }
  };

  const handleSubmitSolution = async () => {
    if (!challenge) return;

    setExecuting(true);
    setError(null);

    try {
      const res = await api.submitCodingSolution(challenge.id, code, challenge.language);
      if (res.data) {
        setLatestSubmission(res.data);
        if (res.data.status === "Passed") {
          setChallenge((prev) => (prev ? { ...prev, is_solved: true } : prev));
        }
        fetchSubmissions(challenge.id);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to execute code in sandbox.");
      }
    } finally {
      setExecuting(false);
    }
  };

  const handleFetchAIHint = async () => {
    if (!challenge) return;

    setLoadingHint(true);
    try {
      const res = await api.getCodingAIHint(challenge.id, code);
      if (res.data) {
        setAiHint(res.data);
      }
    } catch (err) {
      console.error("AI Hint error:", err);
    } finally {
      setLoadingHint(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 space-y-6 animate-pulse">
        <div className="h-12 w-64 bg-surface-800 rounded-xl" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[600px]">
          <div className="bg-surface-900 rounded-2xl border border-white/5" />
          <div className="bg-surface-900 rounded-2xl border border-white/5" />
        </div>
      </div>
    );
  }

  if (error || !challenge) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-400 mx-auto flex items-center justify-center">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        </div>
        <h2 className="text-lg font-bold text-white">Coding Environment Error</h2>
        <p className="text-xs text-surface-200/70">{error || "Challenge not found."}</p>
        <button
          onClick={() => navigate("/coding")}
          className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors cursor-pointer"
        >
          Back to Coding Directory
        </button>
      </div>
    );
  }

  const lineCount = code.split("\n").length;

  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-surface-900 border border-white/10 rounded-2xl p-4 sm:px-6 shadow-xl">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/coding")}
            className="p-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white transition-colors cursor-pointer"
            title="Back to Challenges"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white">{challenge.title}</h1>
              {challenge.is_solved && (
                <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 text-[10px] font-extrabold border border-emerald-500/30">
                  SOLVED ✓
                </span>
              )}
            </div>
            <p className="text-xs text-surface-200/60 mt-0.5">
              Category: <span className="font-semibold text-surface-200">{challenge.category}</span>
              {" • "}
              Language: <span className="font-semibold text-surface-200">{challenge.language.toUpperCase()}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              challenge.difficulty === "Hard"
                ? "bg-red-500/15 text-red-300 border border-red-500/30"
                : challenge.difficulty === "Medium"
                ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                : "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
            }`}
          >
            {challenge.difficulty}
          </span>

          <button
            onClick={async () => {
              try {
                const res = await api.generateCustomCodingChallenge(challenge.title, challenge.category, challenge.difficulty);
                if (res.data) {
                  navigate(`/coding/${res.data.slug || res.data.id}`);
                }
              } catch {
                navigate("/coding");
              }
            }}
            className="px-3.5 py-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold cursor-pointer transition-all flex items-center gap-1.5"
            title="Generate a similar problem using AI"
          >
            <span>✨ New Similar Challenge</span>
          </button>
        </div>
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Pane (Problem, Submissions, AI Hint) */}
        <div className="lg:col-span-5 bg-surface-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[750px]">
          {/* Tab Controls */}
          <div className="flex border-b border-white/10 bg-surface-950/60 p-2 gap-1">
            {[
              { id: "problem", label: "Problem Statement" },
              { id: "submissions", label: `Submissions (${submissions.length})` },
              { id: "ai_hint", label: "AI Hint 💡" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as LeftTab)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                  activeTab === tab.id
                    ? "bg-surface-800 text-white shadow border border-white/10"
                    : "text-surface-200/60 hover:text-white hover:bg-white/5"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Contents */}
          <div className="p-6 overflow-y-auto flex-1 space-y-6 text-xs text-surface-200 leading-relaxed">
            {activeTab === "problem" && (
              <div className="space-y-5">
                {/* Description */}
                <div className="prose prose-invert max-w-none space-y-3">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider text-[11px]">Problem Description</h3>
                  <div className="whitespace-pre-wrap leading-relaxed bg-surface-950/40 p-4 rounded-xl border border-white/5 font-sans">
                    {challenge.description}
                  </div>
                </div>

                {/* Examples */}
                {challenge.examples && challenge.examples.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider text-[11px]">Examples</h3>
                    {challenge.examples.map((ex, idx) => (
                      <div key={idx} className="p-3.5 rounded-xl bg-surface-800/60 border border-white/5 space-y-2 font-mono text-[11px]">
                        <div>
                          <span className="text-brand-300 font-bold">Input:</span> {ex.input}
                        </div>
                        <div>
                          <span className="text-emerald-400 font-bold">Output:</span> {ex.output}
                        </div>
                        {ex.explanation && (
                          <div className="text-[10px] text-surface-200/60 font-sans border-t border-white/5 pt-1 mt-1">
                            💡 <span className="font-semibold">Explanation:</span> {ex.explanation}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* SQL Schema if applicable */}
                {challenge.sql_schema && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider text-[11px]">Database Schema (SQLite Sandbox)</h3>
                    <pre className="p-3 rounded-xl bg-surface-950 border border-white/5 font-mono text-[11px] text-surface-200/80 overflow-x-auto">
                      {challenge.sql_schema.trim()}
                    </pre>

                  </div>
                )}
              </div>
            )}

            {activeTab === "submissions" && (
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider text-[11px]">Submission History</h3>
                {loadingSubmissions ? (
                  <p className="text-surface-200/50">Loading submissions...</p>
                ) : submissions.length === 0 ? (
                  <p className="text-surface-200/50 italic">No submissions recorded yet for this challenge.</p>
                ) : (
                  <div className="space-y-3">
                    {submissions.map((sub) => (
                      <div
                        key={sub.id}
                        className="p-3.5 rounded-xl bg-surface-800/60 border border-white/5 space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                              sub.status === "Passed"
                                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                : "bg-red-500/20 text-red-300 border border-red-500/30"
                            }`}
                          >
                            {sub.status}
                          </span>
                          <span className="text-[10px] text-surface-200/50">
                            {new Date(sub.submitted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            {" • "}
                            {sub.execution_time_ms ? `${sub.execution_time_ms} ms` : ""}
                          </span>
                        </div>
                        <p className="text-[11px] text-surface-200/80 font-mono">
                          Passed {sub.passed_test_cases}/{sub.total_test_cases} test cases
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "ai_hint" && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-brand-500/10 border border-brand-500/20 space-y-2">
                  <h3 className="text-xs font-bold text-brand-300 uppercase tracking-wider">Ollama AI Coding Coach</h3>
                  <p className="text-xs text-surface-200/80">
                    Ask Ollama AI for algorithm guidance based on your current code. (Ollama provides hints, but does not decide whether test cases pass).
                  </p>
                  <button
                    onClick={handleFetchAIHint}
                    disabled={loadingHint}
                    className="mt-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-md shadow-brand-600/20 transition-all cursor-pointer disabled:opacity-50"
                  >
                    {loadingHint ? "Generating Hint..." : "Request AI Hint 💡"}
                  </button>
                </div>

                {aiHint && (
                  <div className="space-y-4 pt-2">
                    <div className="p-4 rounded-xl bg-surface-800/80 border border-white/10 space-y-1">
                      <h4 className="font-bold text-emerald-400 text-[11px] uppercase tracking-wider">Algorithm Hint</h4>
                      <p className="text-surface-200 leading-relaxed">{aiHint.hint}</p>
                    </div>

                    <div className="p-4 rounded-xl bg-surface-800/80 border border-white/10 space-y-1">
                      <h4 className="font-bold text-purple-400 text-[11px] uppercase tracking-wider">Code Explanation & Approach</h4>
                      <p className="text-surface-200 leading-relaxed whitespace-pre-wrap">{aiHint.explanation}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Pane (Code Editor & Sandbox Execution Results) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-surface-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
            {/* Editor Toolbar */}
            <div className="flex items-center justify-between px-5 py-3 bg-surface-950/80 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500/80 inline-block" />
                <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
                <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
                <span className="text-xs font-mono text-surface-200/60 ml-2">
                  solution.{challenge.language === "sql" ? "sql" : "py"}
                </span>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setCode(challenge.starter_code)}
                  className="px-2.5 py-1 rounded-lg bg-surface-800 hover:bg-surface-700 text-surface-200 text-[11px] font-medium transition-colors cursor-pointer"
                >
                  Reset Code
                </button>
                <span className="text-[11px] text-surface-200/50 font-mono">{lineCount} lines</span>
              </div>
            </div>

            {/* Code Input Textarea */}
            <div className="relative flex">
              <div className="py-4 px-3 text-right text-surface-200/30 select-none font-mono text-xs leading-relaxed bg-surface-950/60 min-w-[40px]">
                {Array.from({ length: lineCount }, (_, i) => i + 1).join("\n")}
              </div>

              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                onKeyDown={handleTabIndent}
                rows={16}
                className="w-full p-4 bg-surface-950 text-emerald-300 font-mono text-xs leading-relaxed focus:outline-none resize-none"
                placeholder="Write your solution code here..."
                spellCheck={false}
              />
            </div>

            {/* Bottom Execution Action Controls */}
            <div className="flex items-center justify-between px-5 py-3.5 bg-surface-900 border-t border-white/10">
              <span className="text-[11px] text-surface-200/50 hidden sm:block">
                Executes inside an isolated sandbox runner (Timeout limit: 3.0s).
              </span>

              <button
                onClick={handleSubmitSolution}
                disabled={executing || !code.trim()}
                id="submit-solution-btn"
                className="w-full sm:w-auto py-2.5 px-6 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-bold text-xs shadow-lg shadow-emerald-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {executing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Sandbox Executing...</span>
                  </>
                ) : (
                  <>
                    <span>Submit Solution</span>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Sandbox Execution Results Panel */}
          {latestSubmission && (
            <div className="bg-surface-900 border border-white/10 rounded-2xl p-5 space-y-4 shadow-2xl animate-fade-in">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="flex items-center gap-3">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase ${
                      latestSubmission.status === "Passed"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "bg-red-500/20 text-red-300 border border-red-500/30"
                    }`}
                  >
                    {latestSubmission.status}
                  </span>
                  <span className="text-xs font-bold text-white">
                    {latestSubmission.passed_test_cases} / {latestSubmission.total_test_cases} Test Cases Passed
                  </span>
                </div>

                {latestSubmission.execution_time_ms !== null && (
                  <span className="text-xs text-surface-200/60 font-mono">
                    Runtime: {latestSubmission.execution_time_ms} ms
                  </span>
                )}
              </div>

              {/* Execution Error Message if syntax/runtime error */}
              {latestSubmission.error_message && (
                <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs font-mono whitespace-pre-wrap">
                  {latestSubmission.error_message}
                </div>
              )}

              {/* Test Case Results Grid */}
              <div className="space-y-3">
                {latestSubmission.results.map((r) => (
                  <div
                    key={r.test_case_index}
                    className={`p-3.5 rounded-xl border text-xs font-mono space-y-2 ${
                      r.passed
                        ? "bg-emerald-950/20 border-emerald-500/20"
                        : "bg-red-950/20 border-red-500/20"
                    }`}
                  >
                    <div className="flex items-center justify-between font-sans">
                      <span className="font-bold text-white">Test Case #{r.test_case_index + 1}</span>
                      <span className={`font-bold ${r.passed ? "text-emerald-400" : "text-red-400"}`}>
                        {r.passed ? "✓ Passed" : "✗ Failed"}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1">
                      <div>
                        <span className="text-surface-200/60 block font-sans">Input:</span>
                        <div className="text-surface-200 bg-surface-950/80 p-2 rounded border border-white/5 truncate">
                          {r.input_data}
                        </div>
                      </div>
                      <div>
                        <span className="text-surface-200/60 block font-sans">Expected Output:</span>
                        <div className="text-emerald-300 bg-surface-950/80 p-2 rounded border border-white/5 truncate">
                          {r.expected_output}
                        </div>
                      </div>
                    </div>

                    {r.actual_output && (
                      <div className="text-[11px]">
                        <span className="text-surface-200/60 block font-sans">Actual Output:</span>
                        <div className={`p-2 rounded border border-white/5 ${r.passed ? "text-emerald-400" : "text-red-300"} bg-surface-950/80`}>
                          {r.actual_output}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
