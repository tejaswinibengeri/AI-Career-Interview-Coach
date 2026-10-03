import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api, { APIError, type LearningResourceData } from "../lib/api";

type TabMode = "recommended" | "all" | "saved" | "completed";

const RESOURCE_TYPES = ["All", "Video", "Documentation", "Course", "Certification", "Book"];
const DIFFICULTIES = ["All", "Beginner", "Intermediate", "Advanced"];
const COMMON_SKILLS = [
  "All",
  "Python",
  "FastAPI",
  "React",
  "SQL",
  "Docker",
  "AWS",
  "TypeScript",
  "JavaScript",
  "System Design",
  "DSA",
  "AI",
  "Data Science",
  "Java",
  "Spring Boot",
  "Node.js",
  "Django",
  "Kubernetes",
  "MongoDB",
  "Git",
  "Angular",
  "Vue.js",
  "Go",
  "Rust",
  "C++",
  "Flutter",
  "Redis",
  "GraphQL",
  "Cybersecurity",
  "DevOps",
  "Next.js",
  "Terraform",
  "Linux",
  "HTML/CSS",
];

const ROLE_PRESETS = [
  { label: "🐍 Python Developer", skill: "Python" },
  { label: "⚡ FastAPI Backend", skill: "FastAPI" },
  { label: "⚛️ React Frontend", skill: "React" },
  { label: "🤖 AI & Machine Learning", skill: "AI" },
  { label: "📊 Data Science", skill: "Data Science" },
  { label: "☕ Java Spring Boot", skill: "Java" },
  { label: "☁️ DevOps & AWS", skill: "AWS" },
  { label: "🧠 DSA & System Design", skill: "DSA" },
  { label: "📱 Flutter Mobile", skill: "Flutter" },
];

export default function LearningResources() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialSkill = searchParams.get("skill") || "All";

  const [activeTab, setActiveTab] = useState<TabMode>("all");
  const [resources, setResources] = useState<LearningResourceData[]>([]);

  // Filter states
  const [selectedSkill, setSelectedSkill] = useState<string>(initialSkill);
  const [selectedType, setSelectedType] = useState<string>("All");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchResources();
  }, [activeTab, selectedSkill, selectedType, selectedDifficulty]);

  const fetchResources = async () => {
    setLoading(true);
    setError(null);
    try {
      const isGapOnly = activeTab === "recommended";
      const sk = selectedSkill !== "All" ? selectedSkill : undefined;
      const diff = selectedDifficulty !== "All" ? selectedDifficulty : undefined;
      const type = selectedType !== "All" ? selectedType : undefined;
      const q = searchQuery.trim() ? searchQuery.trim() : undefined;

      const res = await api.getLearningResources({
        skill_name: sk,
        difficulty: diff,
        resource_type: type,
        search: q,
        skill_gap_only: isGapOnly,
      });

      if (res.data) {
        let filtered = res.data;
        if (activeTab === "saved") {
          filtered = filtered.filter((r) => r.is_saved);
        } else if (activeTab === "completed") {
          filtered = filtered.filter((r) => r.is_completed);
        }
        setResources(filtered);
      } else {
        setError("Failed to load learning resources.");
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

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchResources();
  };

  const handleSelectRolePreset = (skill: string) => {
    setSelectedSkill(skill);
    setSearchParams({ skill });
  };

  const handleToggleSave = async (resourceId: number, currentSaved: boolean) => {
    try {
      const res = await api.updateLearningResourceProgress(resourceId, { is_saved: !currentSaved });
      if (res.data) {
        setResources((prev) =>
          prev.map((r) => (r.id === resourceId ? { ...r, is_saved: res.data!.is_saved } : r))
        );
      }
    } catch {
      // Ignore toggle errors
    }
  };

  const handleToggleComplete = async (resourceId: number, currentCompleted: boolean) => {
    try {
      const res = await api.updateLearningResourceProgress(resourceId, { is_completed: !currentCompleted });
      if (res.data) {
        setResources((prev) =>
          prev.map((r) => (r.id === resourceId ? { ...r, is_completed: res.data!.is_completed } : r))
        );
      }
    } catch {
      // Ignore toggle errors
    }
  };

  const recommendedCount = resources.filter((r) => r.is_recommended_for_gap).length;
  const completedCount = resources.filter((r) => r.is_completed).length;
  const videoCount = resources.filter((r) => r.resource_type === "Video" || r.source === "YouTube").length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-950 via-surface-900 to-indigo-950/60 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-semibold">
          Verified Learning & Video Tutorials Hub
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Role & Skill Learning Hub
        </h1>
        <p className="text-sm text-surface-200/80 max-w-3xl leading-relaxed">
          Explore curated full courses, verified YouTube video tutorials (freeCodeCamp, Traversy Media, etc.), official documentation, and certifications for your target role and skill gaps.
        </p>

        {/* Quick Role Selectors */}
        <div className="pt-2">
          <p className="text-xs font-bold text-surface-300 mb-2 uppercase tracking-wider">Quick Target Role / Topic Selection:</p>
          <div className="flex flex-wrap gap-2">
            {ROLE_PRESETS.map((preset) => (
              <button
                key={preset.skill}
                onClick={() => handleSelectRolePreset(preset.skill)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                  selectedSkill === preset.skill
                    ? "bg-brand-600 text-white shadow-lg shadow-brand-600/30 scale-105 border border-brand-400"
                    : "bg-surface-800/90 text-surface-200 border border-white/10 hover:bg-surface-700 hover:text-white"
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-4 pt-2 text-xs">
          <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
            Total Catalog: <span className="font-bold text-white">{resources.length}</span>
          </div>
          <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
            🎥 Video Tutorials: <span className="font-bold text-red-400">{videoCount}</span>
          </div>
          <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
            Skill Gap Matches: <span className="font-bold text-cyan-300">{recommendedCount}</span>
          </div>
          <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
            Completed: <span className="font-bold text-emerald-400">{completedCount}</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => fetchResources()} className="text-xs font-bold text-red-400 hover:text-red-200 cursor-pointer">
            Retry
          </button>
        </div>
      )}

      {/* Main Filter & Navigation Bar */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-5 space-y-4 shadow-xl">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-white/5">
          {[
            { id: "all", label: "📚 All Verified Resources" },
            { id: "recommended", label: "🎯 Recommended for Skill Gap" },
            { id: "saved", label: "⭐ Saved Bookmarks" },
            { id: "completed", label: "✓ Completed" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabMode)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === tab.id
                  ? "bg-brand-600 text-white shadow-md shadow-brand-600/20"
                  : "bg-surface-800 text-surface-200/70 hover:bg-surface-700 hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Filters Toolbar */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center pt-1">
          {/* Skill Filter */}
          <div className="md:col-span-3">
            <select
              value={selectedSkill}
              onChange={(e) => setSelectedSkill(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
            >
              <option value="All">All Skills & Topics ({COMMON_SKILLS.length - 1})</option>
              {COMMON_SKILLS.filter((s) => s !== "All").map((s) => (
                <option key={s} value={s}>
                  Skill: {s}
                </option>
              ))}
            </select>
          </div>

          {/* Type Filter */}
          <div className="md:col-span-3">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
            >
              <option value="All">All Resource Types</option>
              {RESOURCE_TYPES.filter((t) => t !== "All").map((t) => (
                <option key={t} value={t}>
                  Type: {t}
                </option>
              ))}
            </select>
          </div>

          {/* Difficulty Filter */}
          <div className="md:col-span-2">
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
            >
              <option value="All">All Difficulties</option>
              {DIFFICULTIES.filter((d) => d !== "All").map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          {/* Search Bar */}
          <div className="md:col-span-4">
            <form onSubmit={handleSearchSubmit} className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search skill, topic, role (e.g. Python, Hooks)..."
                className="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-white text-xs placeholder-surface-400 focus:outline-none focus:border-brand-500"
              />
              <button
                type="submit"
                className="px-3.5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors cursor-pointer"
              >
                Find
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Resources Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-pulse">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-44 rounded-2xl bg-surface-900 border border-white/5 p-5 space-y-3" />
          ))}
        </div>
      ) : resources.length === 0 ? (
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-surface-800 text-surface-200/40 mx-auto flex items-center justify-center">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-white">No Learning Resources Found</h3>
          <p className="text-xs text-surface-200/60 max-w-sm mx-auto">
            {activeTab === "recommended"
              ? "No specific missing skill gaps match the current filter criteria."
              : "Try resetting your search filters or selecting 'All Skills'."}
          </p>
          <button
            onClick={() => {
              setSelectedSkill("All");
              setSelectedType("All");
              setSelectedDifficulty("All");
              setSearchQuery("");
              setActiveTab("all");
            }}
            className="px-4 py-2 rounded-xl bg-brand-600 text-white text-xs font-semibold hover:bg-brand-500 cursor-pointer"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {resources.map((r) => {
            const isYouTube = r.source === "YouTube" || r.url.includes("youtube.com");
            return (
              <div
                key={r.id}
                className={`bg-surface-900 border ${
                  isYouTube ? "border-red-500/20 hover:border-red-500/40" : "border-white/10 hover:border-white/20"
                } rounded-2xl p-5 space-y-4 shadow-xl flex flex-col justify-between transition-all hover:translate-y-[-2px]`}
              >
                <div className="space-y-2.5">
                  {/* Badges Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {isYouTube && (
                        <span className="px-2.5 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/30 text-[10px] font-extrabold flex items-center gap-1">
                          ▶ YouTube Video
                        </span>
                      )}
                      {r.is_recommended_for_gap && (
                        <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 text-[10px] font-extrabold">
                          🎯 Skill Gap Pick
                        </span>
                      )}
                      <span className="px-2.5 py-0.5 rounded-full bg-surface-800 text-surface-200 border border-white/10 text-[10px] font-semibold">
                        {r.skill_name}
                      </span>
                    </div>

                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        r.difficulty === "Advanced"
                          ? "bg-red-500/15 text-red-300 border border-red-500/30"
                          : r.difficulty === "Intermediate"
                          ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                          : "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                      }`}
                    >
                      {r.difficulty}
                    </span>
                  </div>

                  {/* Title */}
                  <h3 className="text-base font-bold text-white hover:text-brand-300 transition-colors">
                    {r.title}
                  </h3>

                  {/* Description */}
                  <p className="text-xs text-surface-200/70 leading-relaxed line-clamp-2">
                    {r.description}
                  </p>

                  {/* Source & Type details */}
                  <div className="flex items-center gap-3 text-[11px] text-surface-400 pt-1">
                    <span>Source: <strong className="text-surface-200">{r.source}</strong></span>
                    <span>Type: <strong className="text-surface-200">{r.resource_type}</strong></span>
                    {r.estimated_hours && <span>~{r.estimated_hours} hrs</span>}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-3 border-t border-white/5 gap-2">
                  <a
                    href={r.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`px-4 py-2 rounded-xl text-white font-semibold text-xs shadow-md transition-all flex items-center gap-1.5 ${
                      isYouTube
                        ? "bg-red-600 hover:bg-red-500 shadow-red-600/20"
                        : "bg-brand-600 hover:bg-brand-500 shadow-brand-600/20"
                    }`}
                  >
                    <span>{isYouTube ? "▶ Watch on YouTube" : "Open Resource ↗"}</span>
                  </a>

                  <div className="flex items-center gap-1.5">
                    {/* Save Bookmark Button */}
                    <button
                      onClick={() => handleToggleSave(r.id, r.is_saved)}
                      className={`px-3 py-1.5 rounded-xl border text-xs transition-colors cursor-pointer ${
                        r.is_saved
                          ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                          : "bg-surface-800 text-surface-300 border-white/10 hover:text-white"
                      }`}
                      title={r.is_saved ? "Remove Bookmark" : "Save Bookmark"}
                    >
                      {r.is_saved ? "★ Saved" : "☆ Save"}
                    </button>

                    {/* Mark Complete Button */}
                    <button
                      onClick={() => handleToggleComplete(r.id, r.is_completed)}
                      className={`px-3 py-1.5 rounded-xl border text-xs transition-colors cursor-pointer ${
                        r.is_completed
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                          : "bg-surface-800 text-surface-300 border-white/10 hover:text-white"
                      }`}
                      title={r.is_completed ? "Completed" : "Mark as Complete"}
                    >
                      {r.is_completed ? "✓ Done" : "Mark Complete"}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

