import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { APIError, type CodingChallengeData } from "../lib/api";

const CATEGORIES = ["All", "DSA", "Python", "SQL", "Arrays & Strings", "Dynamic Programming", "Trees & Graphs"];
const DIFFICULTIES = ["All", "Easy", "Medium", "Hard"];

export default function CodingDirectory() {
  const navigate = useNavigate();

  const [challenges, setChallenges] = useState<CodingChallengeData[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [showGenModal, setShowGenModal] = useState<boolean>(false);
  const [genTopic, setGenTopic] = useState<string>("");
  const [genCategory, setGenCategory] = useState<string>("Python");
  const [genDifficulty, setGenDifficulty] = useState<string>("Medium");
  const [generating, setGenerating] = useState<boolean>(false);

  const fetchChallenges = async () => {
    setLoading(true);
    setError(null);
    try {
      const cat = selectedCategory !== "All" ? selectedCategory : undefined;
      const diff = selectedDifficulty !== "All" ? selectedDifficulty : undefined;
      const q = searchQuery.trim() ? searchQuery.trim() : undefined;

      const res = await api.getCodingChallenges(cat, diff, q);
      if (res.data) {
        setChallenges(res.data);
      } else {
        setError("Failed to load coding challenges.");
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

  const handleGenerateAIChallenge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!genTopic.trim()) return;

    setGenerating(true);
    setError(null);
    try {
      const res = await api.generateCustomCodingChallenge(genTopic.trim(), genCategory, genDifficulty);
      if (res.data) {
        setShowGenModal(false);
        setGenTopic("");
        navigate(`/coding/${res.data.slug || res.data.id}`);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to generate custom coding challenge.");
      }
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    fetchChallenges();
  }, [selectedCategory, selectedDifficulty]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchChallenges();
  };

  const solvedCount = challenges.filter((c) => c.is_solved).length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-950 via-surface-900 to-emerald-950/40 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
          Module 12 • Coding Challenge Sandbox System
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Coding Practice & Technical Sandbox
        </h1>
        <p className="text-sm text-surface-200/80 max-w-3xl leading-relaxed">
          Solve LeetCode-style algorithmic challenges in Python, write complex SQL queries, or generate custom AI problems tailored to any specific topic.
        </p>

        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 text-xs">
          <div className="flex flex-wrap gap-3">
            <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
              Total Challenges: <span className="font-bold text-white">{challenges.length}</span>
            </div>
            <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
              Solved Problems: <span className="font-bold text-emerald-400">{solvedCount}</span>
            </div>
          </div>

          <button
            onClick={() => setShowGenModal(true)}
            className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/30 transition-all cursor-pointer flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Generate Custom AI Challenge
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => fetchChallenges()} className="text-xs font-bold text-red-400 hover:text-red-200 cursor-pointer">
            Retry
          </button>
        </div>
      )}

      {/* Filters Bar */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-5 space-y-4 shadow-xl">
        <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-white/5">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                selectedCategory === cat
                  ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                  : "bg-surface-800 text-surface-300 hover:bg-surface-700 hover:text-white"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
          <div className="sm:col-span-4">
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
            >
              {DIFFICULTIES.map((d) => (
                <option key={d} value={d}>
                  Difficulty: {d}
                </option>
              ))}
            </select>
          </div>

          <div className="sm:col-span-8">
            <form onSubmit={handleSearchSubmit} className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search coding challenge by name, topic..."
                className="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-white text-xs placeholder-surface-400 focus:outline-none focus:border-brand-500"
              />
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors cursor-pointer"
              >
                Search
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Challenge Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-pulse">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-40 rounded-2xl bg-surface-900 border border-white/5 p-5 space-y-3" />
          ))}
        </div>
      ) : challenges.length === 0 ? (
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-surface-800 text-surface-400 mx-auto flex items-center justify-center">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-white">No Challenges Found</h3>
          <p className="text-xs text-surface-400 max-w-sm mx-auto">
            Try resetting your search query or generate a new AI challenge for any topic!
          </p>
          <button
            onClick={() => setShowGenModal(true)}
            className="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-500 cursor-pointer"
          >
            + Generate AI Challenge
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {challenges.map((ch) => (
            <div
              key={ch.id}
              className="bg-surface-900 border border-white/10 hover:border-white/20 rounded-2xl p-5 space-y-3.5 transition-all shadow-xl flex flex-col justify-between hover:translate-y-[-2px]"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white hover:text-brand-300 transition-colors">
                      {ch.title}
                    </h3>
                    {ch.is_solved && (
                      <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center text-xs font-bold" title="Solved">
                        ✓
                      </span>
                    )}
                  </div>

                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                      ch.difficulty === "Hard"
                        ? "bg-red-500/15 text-red-300 border border-red-500/30"
                        : ch.difficulty === "Medium"
                        ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                        : "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                    }`}
                  >
                    {ch.difficulty}
                  </span>
                </div>

                <p className="text-xs text-surface-200/70 line-clamp-2 leading-relaxed">
                  {ch.description.replace(/```[\s\S]*?```/g, "").replace(/`/g, "")}
                </p>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-white/5">
                <span className="px-2.5 py-1 rounded-lg bg-surface-800 border border-white/10 text-[11px] font-medium text-surface-200">
                  {ch.category} ({ch.language.toUpperCase()})
                </span>

                <button
                  onClick={() => navigate(`/coding/${ch.slug}`)}
                  className="px-4 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs shadow-md shadow-brand-600/20 transition-all cursor-pointer flex items-center gap-1.5"
                >
                  <span>{ch.is_solved ? "Solve Again" : "Solve Challenge"}</span>
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AI Custom Challenge Generator Modal */}
      {showGenModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-surface-900 border border-white/10 rounded-2xl max-w-lg w-full p-6 space-y-6 shadow-2xl animate-scale-in">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>✨</span> Generate Custom AI Coding Challenge
              </h2>
              <button onClick={() => setShowGenModal(false)} className="text-surface-200/60 hover:text-white text-lg">
                ✕
              </button>
            </div>

            <form onSubmit={handleGenerateAIChallenge} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-surface-200 mb-1">Target Skill, Topic or Technology</label>
                <input
                  type="text"
                  required
                  value={genTopic}
                  onChange={(e) => setGenTopic(e.target.value)}
                  placeholder="e.g. FastAPI Middleware, PostgreSQL Indexing, Binary Trees, System Design Cache..."
                  className="w-full px-4 py-2.5 rounded-xl bg-surface-800 border border-white/10 text-white placeholder-surface-200/40 text-xs focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-semibold text-surface-200 mb-1">Category</label>
                  <select
                    value={genCategory}
                    onChange={(e) => setGenCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                  >
                    <option value="Python">Python</option>
                    <option value="SQL">SQL / PostgreSQL</option>
                    <option value="DSA">Data Structures (DSA)</option>
                    <option value="System Design">System Design</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-surface-200 mb-1">Difficulty</label>
                  <select
                    value={genDifficulty}
                    onChange={(e) => setGenDifficulty(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-white/10 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowGenModal(false)}
                  className="px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-xs font-semibold text-surface-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generating}
                  className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md transition-all flex items-center gap-2 cursor-pointer"
                >
                  {generating ? "Generating AI Challenge..." : "Generate & Open Challenge"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

