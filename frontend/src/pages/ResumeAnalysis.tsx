import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import api, { APIError, type ResumeAnalysisData, type ResumeData } from "../lib/api";
import AILoadingState from "../components/ui/AILoadingState";


export default function ResumeAnalysis() {
  const { id } = useParams<{ id: string }>();
  const resumeId = Number(id);

  const [resume, setResume] = useState<ResumeData | null>(null);
  const [analysis, setAnalysis] = useState<ResumeAnalysisData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isOllamaOffline, setIsOllamaOffline] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    if (!resumeId) return;
    setLoading(true);
    setError(null);
    setIsOllamaOffline(false);

    try {
      // Fetch resume metadata
      const resData = await api.get<ResumeData>(`/api/v1/resumes/${resumeId}`);
      if (resData.data) {
        setResume(resData.data);
      }

      // Fetch existing analysis if present
      try {
        const resAnalysis = await api.getResumeAnalysis(resumeId);
        if (resAnalysis.data) {
          setAnalysis(resAnalysis.data);
        }
      } catch (err) {
        if (err instanceof APIError && err.status === 404) {
          // No analysis existing yet — trigger first time analysis
          await runAnalysis();
        } else if (err instanceof APIError && err.status === 503) {
          setIsOllamaOffline(true);
          setError("AI Analysis Service (Ollama) is currently offline.");
        } else if (err instanceof APIError) {
          setError(err.message);
        }
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to load resume details.");
      }
    } finally {
      setLoading(false);
    }
  }, [resumeId]);

  const runAnalysis = async (force: boolean = false) => {
    if (!resumeId) return;
    setAnalyzing(true);
    setError(null);
    setIsOllamaOffline(false);

    try {
      const res = await api.analyzeResume(resumeId, undefined, force);
      if (res.data) {
        setAnalysis(res.data);
      }
    } catch (err) {
      if (err instanceof APIError && err.status === 503) {
        setIsOllamaOffline(true);
        setError("AI Analysis Service (Ollama) is currently unavailable. Ensure Ollama is running.");
      } else if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred during AI analysis.");
      }
    } finally {
      setAnalyzing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [loadData]);

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

  if (loading || analyzing) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <AILoadingState
          title="Ollama AI Resume ATS Evaluation"
          subtitle="Extracting skills, inspecting section formatting, and scoring ATS compatibility..."
          steps={[
            "Parsing resume document text & section headers...",
            "Comparing extracted skills against candidate target role...",
            "Calculating overall ATS score, formatting & impact rubrics...",
            "Synthesizing actionable resume improvement suggestions...",
          ]}
        />
      </div>
    );
  }

  if (isOllamaOffline) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-xl mx-auto rounded-2xl bg-surface-900 border border-amber-500/30 p-8 text-center space-y-5 shadow-2xl">
          <div className="w-14 h-14 rounded-2xl bg-amber-500/10 text-amber-400 mx-auto flex items-center justify-center border border-amber-500/20">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
            </svg>
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-bold text-white">AI Service Unavailable (Ollama)</h2>
            <p className="text-xs text-surface-200/70 leading-relaxed">
              The local Ollama LLM provider is currently offline or unreachable at <code className="text-amber-300">http://localhost:11434</code>. Please ensure the Ollama service is running.
            </p>
          </div>

          <div className="pt-2 flex items-center justify-center gap-3">
            <Link
              to="/resumes"
              className="px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-xs font-semibold text-surface-200 hover:text-white transition-all"
            >
              Back to Resumes
            </Link>
            <button
              onClick={() => runAnalysis(true)}
              className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-xs font-semibold text-white transition-all shadow-md shadow-brand-600/30 cursor-pointer"
            >
              Retry AI Analysis
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-lg mx-auto rounded-2xl bg-surface-900 border border-red-500/30 p-8 text-center space-y-4 shadow-xl">
          <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-400 mx-auto flex items-center justify-center">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-white">Analysis Failed</h2>
          <p className="text-xs text-surface-200/70">{error || "Could not analyze resume."}</p>
          <div className="pt-2 flex justify-center gap-3">
            <Link to="/resumes" className="px-4 py-2 rounded-xl bg-surface-800 text-xs font-semibold text-surface-200">
              Back to Resumes
            </Link>
            <button onClick={() => runAnalysis(true)} className="px-4 py-2 rounded-xl bg-brand-600 text-xs font-semibold text-white">
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  const breakdown = analysis.scoring_breakdown;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Top Header Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link to="/resumes" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 mb-2 font-medium">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
            Back to Resumes
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            ATS Resume Analysis & Feedback
          </h1>
          <p className="text-xs text-surface-200/70 mt-1">
            Evaluated for: <span className="font-semibold text-white">{resume?.current_version?.filename || resume?.title}</span> • Analyzed on {formatDate(analysis.created_at)}
          </p>
        </div>

        <button
          onClick={() => runAnalysis(true)}
          disabled={analyzing}
          className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 hover:shadow-brand-500/50 transition-all cursor-pointer flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Re-Analyze with AI
        </button>
      </div>

      {/* 1. ATS Score & Rubric Component Banner */}
      <div className="rounded-2xl bg-gradient-to-br from-surface-900 via-surface-800 to-surface-900 border border-brand-500/20 p-6 sm:p-8 shadow-xl grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
        {/* Gauge Card */}
        <div className="flex flex-col items-center justify-center text-center space-y-3 lg:border-r border-white/10 lg:pr-8">
          <div className="relative w-36 h-36 flex items-center justify-center rounded-full bg-surface-950 border-4 border-brand-500/30 shadow-inner">
            <div className="text-center">
              <span className="text-4xl font-extrabold text-white">{analysis.ats_score}%</span>
              <p className="text-[10px] uppercase tracking-wider font-bold text-brand-400 mt-1">ATS Match</p>
            </div>
          </div>
          <p className="text-xs text-surface-200/70 font-medium max-w-xs">
            Overall Applicant Tracking System compatibility score computed via weighted evaluation rubric.
          </p>
        </div>

        {/* Scoring Rubric Breakdown */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Transparent Rubric Breakdown</h3>
            <span className="text-[11px] text-surface-200/50">Weighted Algorithm</span>
          </div>

          <div className="space-y-3 text-xs">
            {/* Structure */}
            <div className="space-y-1">
              <div className="flex justify-between font-semibold">
                <span className="text-surface-200/80">Structure & Completeness (20%)</span>
                <span className="text-white">{breakdown.structure_score}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-950 overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: `${breakdown.structure_score}%` }} />
              </div>
            </div>

            {/* Skills */}
            <div className="space-y-1">
              <div className="flex justify-between font-semibold">
                <span className="text-surface-200/80">Skills & Keywords Density (30%)</span>
                <span className="text-white">{breakdown.skills_score}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-950 overflow-hidden">
                <div className="h-full bg-brand-400 rounded-full" style={{ width: `${breakdown.skills_score}%` }} />
              </div>
            </div>

            {/* Experience */}
            <div className="space-y-1">
              <div className="flex justify-between font-semibold">
                <span className="text-surface-200/80">Work Experience & Impact (25%)</span>
                <span className="text-white">{breakdown.experience_score}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-950 overflow-hidden">
                <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${breakdown.experience_score}%` }} />
              </div>
            </div>

            {/* Education */}
            <div className="space-y-1">
              <div className="flex justify-between font-semibold">
                <span className="text-surface-200/80">Education & Certifications (15%)</span>
                <span className="text-white">{breakdown.education_score}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-950 overflow-hidden">
                <div className="h-full bg-purple-400 rounded-full" style={{ width: `${breakdown.education_score}%` }} />
              </div>
            </div>

            {/* Formatting */}
            <div className="space-y-1">
              <div className="flex justify-between font-semibold">
                <span className="text-surface-200/80">Formatting & Readability (10%)</span>
                <span className="text-white">{breakdown.formatting_score}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-950 overflow-hidden">
                <div className="h-full bg-amber-400 rounded-full" style={{ width: `${breakdown.formatting_score}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Skills Inventory */}
      <div className="rounded-xl bg-surface-900/80 border border-white/10 p-6 space-y-4 shadow-md">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l5.654-4.654m0 0l3.03-2.496c.384-.317.626-.74.766-1.208m-4.562 1.95L3 4.5l3-3 7.653 7.653" />
          </svg>
          Extracted Skills Inventory ({analysis.skills.length})
        </h3>

        {analysis.skills.length === 0 ? (
          <p className="text-xs text-surface-200/60 italic">No skills extracted from document.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {analysis.skills.map((skill) => (
              <span
                key={skill.id}
                className="px-3 py-1 rounded-lg bg-surface-800 border border-white/10 text-xs font-semibold text-brand-300 flex items-center gap-1.5"
              >
                <span>{skill.skill_name}</span>
                {skill.category && (
                  <span className="text-[10px] text-surface-200/50 uppercase tracking-wider font-normal">
                    ({skill.category})
                  </span>
                )}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 3. Strengths & Weaknesses Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <div className="rounded-xl bg-surface-900/80 border border-emerald-500/20 p-6 space-y-4 shadow-md">
          <h3 className="text-base font-bold text-emerald-400 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Key Strengths ({analysis.strengths.length})
          </h3>
          {analysis.strengths.length === 0 ? (
            <p className="text-xs text-surface-200/70 italic">
              Demonstrates solid domain competency and structured academic/technical background.
            </p>
          ) : (
            <ul className="space-y-2 text-xs">
              {analysis.strengths.map((str, idx) => (
                <li key={idx} className="flex items-start gap-2 text-surface-200">
                  <span className="text-emerald-400 font-bold">•</span>
                  <span>{str}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Weaknesses */}
        <div className="rounded-xl bg-surface-900/80 border border-amber-500/20 p-6 space-y-4 shadow-md">
          <h3 className="text-base font-bold text-amber-400 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            Areas for Improvement ({analysis.weaknesses.length})
          </h3>
          {analysis.weaknesses.length === 0 ? (
            <p className="text-xs text-surface-200/70 italic">
              Consider adding more quantifiable metrics (e.g. % performance increase) to work and project bullet points.
            </p>
          ) : (
            <ul className="space-y-2 text-xs">
              {analysis.weaknesses.map((weak, idx) => (
                <li key={idx} className="flex items-start gap-2 text-surface-200">
                  <span className="text-amber-400 font-bold">•</span>
                  <span>{weak}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* 4. Missing Keywords Card */}
      {analysis.missing_keywords.length > 0 && (
        <div className="rounded-xl bg-surface-900/80 border border-brand-500/20 p-6 space-y-3 shadow-md">
          <h3 className="text-base font-bold text-brand-300 flex items-center gap-2">
            <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
            </svg>
            Missing Industry Keywords
          </h3>
          <p className="text-xs text-surface-200/70">
            Consider adding these relevant keywords to pass ATS screening algorithms:
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            {analysis.missing_keywords.map((kw, idx) => (
              <span key={idx} className="px-3 py-1 rounded-lg bg-surface-800 border border-white/10 text-xs font-semibold text-amber-300">
                + {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 5. Recommendations & Suggestions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Content Recommendations */}
        <div className="rounded-xl bg-surface-900/80 border border-white/10 p-6 space-y-4 shadow-md">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
            </svg>
            Improvement Recommendations
          </h3>
          {analysis.improvement_recommendations.length === 0 ? (
            <p className="text-xs text-surface-200/70 italic">
              Include specific metric outcomes (e.g. latency reductions, scale handled) and add direct links to live GitHub repositories.
            </p>
          ) : (
            <ul className="space-y-2 text-xs">
              {analysis.improvement_recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2 text-surface-200">
                  <span className="text-brand-400 font-bold">{idx + 1}.</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Formatting & Grammar */}
        <div className="rounded-xl bg-surface-900/80 border border-white/10 p-6 space-y-4 shadow-md">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
            </svg>
            Formatting & Grammar Suggestions
          </h3>
          <div className="space-y-3 text-xs">
            {analysis.formatting_suggestions.length === 0 && analysis.grammar_suggestions.length === 0 ? (
              <p className="text-xs text-surface-200/70 italic">
                Resume layout and grammar are cleanly formatted and optimized for standard ATS parsers.
              </p>
            ) : (
              <>
                {analysis.formatting_suggestions.map((fmt, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-surface-800/50 border border-white/5 text-surface-200">
                    <span className="font-semibold text-amber-300">Formatting:</span> {fmt}
                  </div>
                ))}
                {analysis.grammar_suggestions.map((grm, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-surface-800/50 border border-white/5 text-surface-200">
                    <span className="font-semibold text-blue-300">Grammar:</span> {grm}
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
