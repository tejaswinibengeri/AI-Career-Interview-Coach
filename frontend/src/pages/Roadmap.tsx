import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import api, { APIError, type RoadmapData, type RoadmapItemData } from "../lib/api";
import AILoadingState from "../components/ui/AILoadingState";
import LoadingSpinner from "../components/ui/LoadingSpinner";


export default function Roadmap() {
  const [roadmap, setRoadmap] = useState<RoadmapData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOllamaOffline, setIsOllamaOffline] = useState<boolean>(false);

  const loadRoadmap = useCallback(async () => {
    setLoading(true);
    setError(null);
    setIsOllamaOffline(false);

    try {
      const res = await api.getLatestRoadmap();
      if (res.data) {
        setRoadmap(res.data);
      }
    } catch (err) {
      if (err instanceof APIError && err.status === 404) {
        // No active roadmap -> trigger initial generation
        await handleGenerate();
      } else if (err instanceof APIError && err.status === 503) {
        setIsOllamaOffline(true);
        setError("AI Service (Ollama) is currently unavailable.");
      } else if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to load career roadmap.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const [customQuery, setCustomQuery] = useState<string>("");

  const handleGenerate = async (occupationId?: number, query?: string) => {
    setGenerating(true);
    setError(null);
    setIsOllamaOffline(false);

    try {
      const res = await api.generateRoadmap(occupationId, query || customQuery);
      if (res.data) {
        setRoadmap(res.data);
      }
    } catch (err) {
      if (err instanceof APIError && err.status === 503) {
        setIsOllamaOffline(true);
        setError("AI Service (Ollama) is currently offline. Ensure local Ollama service is running.");
      } else if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to generate career roadmap.");
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleCustomSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customQuery.trim()) {
      handleGenerate(undefined, customQuery.trim());
    }
  };



  const handleToggle = async (item: RoadmapItemData) => {
    setTogglingId(item.id);
    try {
      const res = await api.toggleRoadmapItem(item.id, !item.is_completed);
      if (res.data) {
        setRoadmap(res.data);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      }
    } finally {
      setTogglingId(null);
    }
  };

  useEffect(() => {
    loadRoadmap();
  }, [loadRoadmap]);

  if (loading || generating) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <AILoadingState
          title={`Generating Detailed Career Roadmap • ${customQuery.trim() || "Target Role"}`}
          subtitle="Formulating a comprehensive, multi-phase learning path tailored to your requested target role or skill..."
          steps={[
            "Analyzing target role competencies & skill requirements...",
            "Evaluating candidate existing profile & identified skill gaps...",
            "Structuring multi-phase learning milestones & project deliverables...",
            "Finalizing estimated effort schedules & documentation links...",
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
            <p className="text-xs text-surface-200/70">
              The local Ollama LLM service is currently offline. Ensure Ollama is running to generate personalized roadmaps.
            </p>
          </div>
          <div className="pt-2 flex justify-center gap-3">
            <Link to="/career" className="px-4 py-2 rounded-xl bg-surface-800 text-xs font-semibold text-surface-200">
              Back to Careers
            </Link>
            <button onClick={() => handleGenerate()} className="px-5 py-2 rounded-xl bg-brand-600 text-xs font-semibold text-white">
              Retry Generation
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (error || !roadmap) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-lg mx-auto rounded-2xl bg-surface-900 border border-white/10 p-8 text-center space-y-4 shadow-xl">
          <h2 className="text-lg font-bold text-white">No Active Roadmap Found</h2>
          <p className="text-xs text-surface-200/70">{error || "Generate a roadmap to start your structured career progression."}</p>
          <button
            onClick={() => handleGenerate()}
            className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md transition-all"
          >
            Generate Career Roadmap Now
          </button>
        </div>
      </div>
    );
  }

  // Group items by phase
  const groupedPhases: Record<string, RoadmapItemData[]> = {};
  roadmap.items.forEach((item) => {
    if (!groupedPhases[item.phase]) {
      groupedPhases[item.phase] = [];
    }
    groupedPhases[item.phase].push(item);
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Top Header & Custom Roadmap Generator */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs font-semibold">
              AI-Powered Detailed Career Roadmap
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Personalized Career Roadmap
            </h1>
            <p className="text-xs text-surface-300">
              Active Path: <span className="font-bold text-brand-300">{roadmap.target_role}</span> • Step-by-step milestone progression with portfolio deliverables
            </p>
          </div>

          {/* Custom Target Role / Skill Search Bar */}
          <form onSubmit={handleCustomSearchSubmit} className="flex flex-wrap sm:flex-nowrap gap-2.5 w-full lg:w-auto">
            <input
              type="text"
              value={customQuery}
              onChange={(e) => setCustomQuery(e.target.value)}
              placeholder="Target role, skill, project, or language (e.g. Python Developer, FastAPI, AI Engineer)..."
              className="w-full sm:w-96 px-4 py-2.5 rounded-xl bg-surface-800 border border-white/10 text-white placeholder-surface-400 text-xs focus:outline-none focus:border-brand-500 shadow-inner"
            />
            <button
              type="submit"
              disabled={generating}
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 transition-all cursor-pointer whitespace-nowrap flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              Generate Detailed Roadmap
            </button>
          </form>
        </div>

        {/* Quick Role & Skill Presets */}
        <div className="pt-2 border-t border-white/5 space-y-2">
          <p className="text-xs font-bold text-surface-400 uppercase tracking-wider">Quick Suggestions:</p>
          <div className="flex flex-wrap gap-2">
            {[
              "Python Backend Engineer",
              "Full Stack Developer (React + Node)",
              "AI & Machine Learning Engineer",
              "FastAPI Microservices Developer",
              "DevOps & Kubernetes Engineer",
              "PostgreSQL Database Architect",
              "Data Scientist & Analyst",
            ].map((role) => (
              <button
                key={role}
                type="button"
                onClick={() => {
                  setCustomQuery(role);
                  handleGenerate(undefined, role);
                }}
                className="px-3 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 text-xs font-medium border border-white/10 transition-all cursor-pointer hover:border-brand-400"
              >
                + {role}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Visual Progression Banner (Current Skills -> Skill Gap -> Learning Stages -> Projects -> Target Career) */}
      <div className="rounded-2xl bg-gradient-to-r from-surface-900 via-surface-850 to-surface-900 border border-brand-500/20 p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <h3 className="text-base font-bold text-white">{roadmap.title}</h3>
            <p className="text-xs text-surface-200/60 mt-0.5">
              Overall Completion: <span className="font-bold text-brand-300">{roadmap.overall_progress}%</span>
            </p>
          </div>
          <div className="w-full sm:w-48 space-y-1">
            <div className="h-2.5 w-full rounded-full bg-surface-950 overflow-hidden border border-white/10">
              <div
                className="h-full bg-gradient-to-r from-brand-500 to-emerald-400 transition-all duration-500 rounded-full"
                style={{ width: `${roadmap.overall_progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Visual Progression Pipeline */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
          {/* Step 1: Current Skills */}
          <div className="p-3.5 rounded-xl bg-surface-950/80 border border-white/5 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">1. Current Skills</span>
            <div className="flex flex-wrap gap-1">
              {roadmap.current_skills.slice(0, 3).map((s, i) => (
                <span key={i} className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 text-[10px]">
                  {s}
                </span>
              ))}
              {roadmap.current_skills.length === 0 && <span className="text-[10px] text-surface-200/50">Base skills</span>}
            </div>
          </div>

          {/* Step 2: Skill Gap */}
          <div className="p-3.5 rounded-xl bg-surface-950/80 border border-white/5 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400">2. Skill Gap</span>
            <div className="flex flex-wrap gap-1">
              {roadmap.missing_skills.slice(0, 3).map((s, i) => (
                <span key={i} className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 text-[10px]">
                  {s}
                </span>
              ))}
              {roadmap.missing_skills.length === 0 && <span className="text-[10px] text-surface-200/50">Target requirements</span>}
            </div>
          </div>

          {/* Step 3: Learning Stages */}
          <div className="p-3.5 rounded-xl bg-surface-950/80 border border-white/5 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-brand-400">3. Learning Stages</span>
            <p className="text-[11px] font-semibold text-white">{Object.keys(groupedPhases).length} Phases</p>
          </div>

          {/* Step 4: Projects */}
          <div className="p-3.5 rounded-xl bg-surface-950/80 border border-white/5 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400">4. Portfolio Projects</span>
            <p className="text-[11px] font-semibold text-white">Practical Demos</p>
          </div>

          {/* Step 5: Target Role */}
          <div className="p-3.5 rounded-xl bg-brand-600/10 border border-brand-500/30 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-brand-300">5. Target Career</span>
            <p className="text-[11px] font-bold text-white truncate">{roadmap.target_role}</p>
          </div>
        </div>
      </div>

      {/* Main Roadmap Phases & Interactive Items */}
      <div className="space-y-8">
        {Object.entries(groupedPhases).map(([phaseTitle, items], phaseIdx) => (
          <div key={phaseIdx} className="space-y-4">
            <div className="flex items-center gap-3 border-b border-white/10 pb-2">
              <span className="w-8 h-8 rounded-xl bg-brand-500/20 border border-brand-500/40 text-brand-300 font-bold text-xs flex items-center justify-center">
                P{phaseIdx + 1}
              </span>
              <h2 className="text-lg font-bold text-white">{phaseTitle}</h2>
            </div>

            <div className="space-y-4">
              {items.map((item) => {
                const isToggling = togglingId === item.id;

                return (
                  <div
                    key={item.id}
                    className={`rounded-2xl border p-5 sm:p-6 space-y-4 transition-all ${
                      item.is_completed
                        ? "bg-surface-950/60 border-emerald-500/30 opacity-80"
                        : "bg-surface-900/80 border-white/10 hover:border-white/20 shadow-md"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3.5">
                        {/* Interactive Checkbox */}
                        <button
                          type="button"
                          disabled={isToggling}
                          onClick={() => handleToggle(item)}
                          className={`mt-0.5 w-5 h-5 rounded-md border flex items-center justify-center transition-all cursor-pointer ${
                            item.is_completed
                              ? "bg-emerald-500 border-emerald-400 text-surface-950"
                              : "border-white/20 hover:border-brand-400 bg-surface-950"
                          }`}
                        >
                          {isToggling ? (
                            <LoadingSpinner size="sm" />
                          ) : item.is_completed ? (
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                            </svg>
                          ) : null}
                        </button>

                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className={`text-base font-bold ${item.is_completed ? "line-through text-surface-200/60" : "text-white"}`}>
                              {item.skill}
                            </h3>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              item.priority === "High" ? "bg-red-500/20 text-red-300" :
                              item.priority === "Medium" ? "bg-amber-500/20 text-amber-300" : "bg-surface-700 text-surface-300"
                            }`}>
                              {item.priority} Priority
                            </span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-surface-800 text-surface-200/70 border border-white/5">
                              {item.estimated_effort}
                            </span>
                          </div>

                          {item.is_completed && (
                            <p className="text-[11px] font-semibold text-emerald-400">✓ Completed</p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Content Details: Topics, Projects, Resources */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 text-xs border-t border-white/5">
                      {/* Topics */}
                      <div className="space-y-1.5">
                        <h4 className="font-bold text-surface-200 uppercase text-[10px] tracking-wider">Topics to Study</h4>
                        <ul className="space-y-1 text-surface-200/80">
                          {item.topics.map((top, idx) => (
                            <li key={idx} className="flex items-center gap-1.5">
                              <span className="text-brand-400 font-bold">•</span>
                              <span>{top}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Practical Projects */}
                      <div className="space-y-1.5">
                        <h4 className="font-bold text-blue-400 uppercase text-[10px] tracking-wider">Practical Projects</h4>
                        <ul className="space-y-1 text-surface-200/80">
                          {item.projects.map((proj, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <span className="text-blue-400 font-bold">↳</span>
                              <span>{proj}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Trusted Resources / Search Guides */}
                      <div className="space-y-1.5">
                        <h4 className="font-bold text-emerald-400 uppercase text-[10px] tracking-wider">Trusted Resources</h4>
                        <ul className="space-y-1 text-surface-200/80">
                          {item.resources.map((res, idx) => (
                            <li key={idx} className="flex items-center gap-1.5">
                              <svg className="w-3 h-3 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
                              </svg>
                              <span>{res}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
