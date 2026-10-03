import { useEffect, useState } from "react";
import api, { APIError, type ProjectRecommendationData } from "../lib/api";
import AILoadingState from "../components/ui/AILoadingState";

type FilterDifficulty = "All" | "Beginner" | "Intermediate" | "Advanced";
type FilterStatus = "All" | "Saved" | "In Progress" | "Completed";

export default function ProjectRecommendations() {
  const [projects, setProjects] = useState<ProjectRecommendationData[]>([]);
  const [selectedDifficulty, setSelectedDifficulty] = useState<FilterDifficulty>("All");
  const [selectedStatus, setSelectedStatus] = useState<FilterStatus>("All");

  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProjects();
  }, [selectedDifficulty, selectedStatus]);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const diff = selectedDifficulty !== "All" ? selectedDifficulty : undefined;
      const stat = selectedStatus !== "All" && selectedStatus !== "Saved" ? selectedStatus : undefined;

      const res = await api.getProjectRecommendations(diff, stat);
      if (res.data) {
        let list = res.data;
        if (selectedStatus === "Saved") {
          list = list.filter((p) => p.is_saved);
        }
        setProjects(list);
      } else {
        setError("Failed to load project recommendations.");
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

  const handleGenerateRecommendations = async () => {
    setGenerating(true);
    setError(null);
    try {
      const res = await api.generateProjectRecommendations();
      if (res.data) {
        // Reset filter to All so user immediately sees all generated tiers
        setSelectedDifficulty("All");
        setSelectedStatus("All");
        await fetchProjects();
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to generate project recommendations.");
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleUpdateStatus = async (projectId: number, newStatus: string) => {
    try {
      const res = await api.updateProjectStatus(projectId, { status: newStatus });
      if (res.data) {
        setProjects((prev) =>
          prev.map((p) => (p.id === projectId ? { ...p, status: res.data!.status } : p))
        );
      }
    } catch {
      // Ignore update error
    }
  };

  const handleToggleSave = async (projectId: number, currentSaved: boolean) => {
    try {
      const res = await api.updateProjectStatus(projectId, { is_saved: !currentSaved });
      if (res.data) {
        setProjects((prev) =>
          prev.map((p) => (p.id === projectId ? { ...p, is_saved: res.data!.is_saved } : p))
        );
      }
    } catch {
      // Ignore save error
    }
  };

  const inProgressCount = projects.filter((p) => p.status === "In Progress").length;
  const completedCount = projects.filter((p) => p.status === "Completed").length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-950 via-surface-900 to-purple-950/60 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-semibold">
              Module 15 • AI Portfolio Project Coach
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Personalized AI Project Recommendations
            </h1>
            <p className="text-sm text-surface-200/80 max-w-2xl leading-relaxed">
              Portfolio projects generated using your actual target career, skills, skill gaps, and roadmap milestones. Build real deliverables to prove job readiness.
            </p>
          </div>

          <button
            onClick={handleGenerateRecommendations}
            disabled={generating}
            className="px-5 py-3 rounded-xl bg-gradient-to-r from-brand-600 to-purple-600 hover:from-brand-500 hover:to-purple-500 text-white font-extrabold text-xs shadow-lg shadow-purple-600/20 transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2 whitespace-nowrap self-start sm:self-auto"
          >
            {generating ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Generating AI Projects...</span>
              </>
            ) : (
              <>
                <span>Generate New Recommendations 🪄</span>
              </>
            )}
          </button>
        </div>

        <div className="flex flex-wrap gap-4 pt-2 text-xs border-t border-white/5">
          <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
            Total Recommended Projects: <span className="font-bold text-white">{projects.length}</span>
          </div>
          <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
            In Progress: <span className="font-bold text-blue-400">{inProgressCount}</span>
          </div>
          <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
            Completed: <span className="font-bold text-emerald-400">{completedCount}</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => fetchProjects()} className="text-xs font-bold text-red-400 hover:text-red-200 cursor-pointer">
            Retry
          </button>
        </div>
      )}

      {/* Filter Tabs Toolbar */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-4 sm:p-5 space-y-4 shadow-xl">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Difficulty Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
            <span className="text-xs text-surface-200/60 font-medium mr-1">Tier:</span>
            {(["All", "Beginner", "Intermediate", "Advanced"] as FilterDifficulty[]).map((diff) => (
              <button
                key={diff}
                onClick={() => setSelectedDifficulty(diff)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  selectedDifficulty === diff
                    ? "bg-brand-600 text-white shadow-md shadow-brand-600/20"
                    : "bg-surface-800 text-surface-200/70 hover:bg-surface-700 hover:text-white"
                }`}
              >
                {diff}
              </button>
            ))}
          </div>

          {/* Status Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto">
            <span className="text-xs text-surface-200/60 font-medium mr-1">Status:</span>
            {(["All", "Saved", "In Progress", "Completed"] as FilterStatus[]).map((stat) => (
              <button
                key={stat}
                onClick={() => setSelectedStatus(stat)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer whitespace-nowrap ${
                  selectedStatus === stat
                    ? "bg-surface-700 text-white border border-white/20 font-bold"
                    : "bg-surface-800/60 text-surface-200/60 hover:text-white"
                }`}
              >
                {stat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Projects Grid */}
      {generating ? (
        <AILoadingState
          title="Generating AI Project Recommendations"
          subtitle="Analyzing candidate skills, target role, and roadmap milestones..."
          steps={[
            "Processing career goals and skill gap vectors...",
            "Designing beginner, intermediate & advanced project tiers...",
            "Specifying technology stacks and feature architecture...",
            "Calculating expected learning outcomes...",
          ]}
        />
      ) : loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 bg-surface-900 rounded-2xl border border-white/5" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-surface-800 text-surface-200/40 mx-auto flex items-center justify-center">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l5.653-4.655m3.03-2.496l3.03-2.496m0 0l-5.877-5.877A2.652 2.652 0 003 6.75l5.877 5.877" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-white">No Project Recommendations Yet</h3>
          <p className="text-xs text-surface-200/60 max-w-sm mx-auto">
            Click "Generate New Recommendations 🪄" to generate portfolio projects tailored to your target role and skill gaps.
          </p>
          <button
            onClick={handleGenerateRecommendations}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition-colors cursor-pointer"
          >
            Generate AI Recommendations 🪄
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {projects.map((p) => (
            <div
              key={p.id}
              className="bg-surface-900 border border-white/10 hover:border-white/20 rounded-2xl p-6 space-y-4 shadow-xl flex flex-col justify-between transition-all"
            >
              <div className="space-y-3">
                {/* Header Tags */}
                <div className="flex items-center justify-between gap-2">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider ${
                      p.difficulty === "Advanced"
                        ? "bg-purple-500/15 text-purple-300 border border-purple-500/30"
                        : p.difficulty === "Intermediate"
                        ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                        : "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                    }`}
                  >
                    {p.difficulty} Project
                  </span>

                  <span
                    className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                      p.status === "Completed"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : p.status === "In Progress"
                        ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                        : "bg-surface-800 text-surface-200/60 border border-white/5"
                    }`}
                  >
                    {p.status}
                  </span>
                </div>

                {/* Title & Description */}
                <div>
                  <h3 className="text-base font-bold text-white hover:text-brand-300 transition-colors">
                    {p.title}
                  </h3>
                  <p className="text-xs text-surface-200/70 leading-relaxed mt-1">
                    {p.description}
                  </p>
                </div>

                {/* Technologies */}
                {p.technologies && p.technologies.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-[10px] font-semibold text-surface-200/50 uppercase tracking-wider block">Tech Stack</span>
                    <div className="flex flex-wrap gap-1.5">
                      {p.technologies.map((t, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-surface-800 border border-white/10 text-[11px] font-mono text-brand-300">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Features */}
                {p.features && p.features.length > 0 && (
                  <div className="space-y-1 text-xs">
                    <span className="text-[10px] font-semibold text-surface-200/50 uppercase tracking-wider block">Key Features</span>
                    <ul className="list-disc list-inside text-surface-200/80 space-y-0.5">
                      {p.features.map((f, idx) => (
                        <li key={idx}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Skills Learned */}
                {p.skills_learned && p.skills_learned.length > 0 && (
                  <div className="space-y-1 text-xs">
                    <span className="text-[10px] font-semibold text-cyan-300 uppercase tracking-wider block">Closes Skill Gaps</span>
                    <div className="flex flex-wrap gap-1">
                      {p.skills_learned.map((sk, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-[10px] font-bold">
                          ✓ {sk}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Expected Outcome */}
                {p.expected_outcome && (
                  <div className="p-3 rounded-xl bg-surface-950/60 border border-white/5 text-xs text-surface-200/80">
                    💡 <span className="font-bold text-white">Expected Deliverable:</span> {p.expected_outcome}
                  </div>
                )}
              </div>

              {/* Action Controls */}
              <div className="flex items-center justify-between pt-4 border-t border-white/5 gap-2">
                <button
                  onClick={() => handleToggleSave(p.id, p.is_saved)}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition-colors cursor-pointer ${
                    p.is_saved
                      ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                      : "bg-surface-800 text-surface-200/60 border-white/10 hover:text-white"
                  }`}
                >
                  {p.is_saved ? "★ Saved" : "☆ Save Project"}
                </button>

                <div className="flex items-center gap-1.5">
                  {p.status !== "In Progress" && (
                    <button
                      onClick={() => handleUpdateStatus(p.id, "In Progress")}
                      className="px-3 py-1.5 rounded-xl bg-blue-600/30 hover:bg-blue-600 border border-blue-500/30 text-blue-300 hover:text-white text-xs font-bold transition-all cursor-pointer"
                    >
                      Start Project 🚀
                    </button>
                  )}

                  {p.status !== "Completed" && (
                    <button
                      onClick={() => handleUpdateStatus(p.id, "Completed")}
                      className="px-3 py-1.5 rounded-xl bg-emerald-600/30 hover:bg-emerald-600 border border-emerald-500/30 text-emerald-300 hover:text-white text-xs font-bold transition-all cursor-pointer"
                    >
                      Mark Complete ✓
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
