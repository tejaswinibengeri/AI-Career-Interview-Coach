import { useEffect, useState, useCallback } from "react";
import api, { APIError, type QuestionData } from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

const CATEGORIES = [
  "All",
  "Technical",
  "HR",
  "Behavioral",
  "Coding",
  "DSA",
  "SQL",
  "Aptitude",
  "Role-specific",
];

const DIFFICULTIES = ["All", "Easy", "Medium", "Hard"];

export default function QuestionBank() {
  const [query, setQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("All");
  const [roleFilter, setRoleFilter] = useState<string>("");

  const [activeTab, setActiveTab] = useState<"all" | "ai" | "saved">("all");
  const [questions, setQuestions] = useState<QuestionData[]>([]);
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  const [loading, setLoading] = useState<boolean>(true);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Random practice question drawer
  const [randomQuestion, setRandomQuestion] = useState<QuestionData | null>(null);
  const [randomLoading, setRandomLoading] = useState<boolean>(false);
  const [showRandomModal, setShowRandomModal] = useState<boolean>(false);

  // AI question generation modal
  const [showGenModal, setShowGenModal] = useState<boolean>(false);
  const [genTopic, setGenTopic] = useState<string>("");
  const [genCategory, setGenCategory] = useState<string>("Technical");
  const [genDifficulty, setGenDifficulty] = useState<string>("Medium");
  const [genRole, setGenRole] = useState<string>("Software Engineer");
  const [genCount, setGenCount] = useState<number>(3);
  const [generating, setGenerating] = useState<boolean>(false);
  const [genError, setGenError] = useState<string | null>(null);

  const fetchQuestions = useCallback(async () => {
    setLoading(true);
    setError(null);

    const cat = selectedCategory !== "All" ? selectedCategory : undefined;
    const diff = selectedDifficulty !== "All" ? selectedDifficulty : undefined;
    const sourceType = activeTab === "ai" ? "ai_generated" : undefined;
    const savedOnly = activeTab === "saved";

    try {
      const res = await api.getQuestions(
        cat,
        diff,
        roleFilter || undefined,
        query || undefined,
        sourceType,
        savedOnly,
        1,
        100
      );
      if (res.data) {
        setQuestions(res.data);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to load interview questions.");
      }
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, selectedDifficulty, roleFilter, query, activeTab]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  const handleToggleExpand = (id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleToggleSave = async (q: QuestionData) => {
    setSavingId(q.id);
    try {
      if (q.is_saved) {
        const res = await api.unsaveQuestion(q.id);
        if (res.data) {
          updateQuestionSavedState(q.id, false);
        }
      } else {
        const res = await api.saveQuestion(q.id);
        if (res.data) {
          updateQuestionSavedState(q.id, true);
        }
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      }
    } finally {
      setSavingId(null);
    }
  };

  const updateQuestionSavedState = (qId: number, isSaved: boolean) => {
    setQuestions((prev) =>
      prev.map((item) => (item.id === qId ? { ...item, is_saved: isSaved } : item))
    );
    if (randomQuestion && randomQuestion.id === qId) {
      setRandomQuestion({ ...randomQuestion, is_saved: isSaved });
    }
  };

  const handleGetRandom = async () => {
    setRandomLoading(true);
    setShowRandomModal(true);
    setRandomQuestion(null);

    const cat = selectedCategory !== "All" ? selectedCategory : undefined;
    const diff = selectedDifficulty !== "All" ? selectedDifficulty : undefined;

    try {
      const res = await api.getRandomQuestion(cat, diff, roleFilter || undefined);
      if (res.data) {
        setRandomQuestion(res.data);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      }
    } finally {
      setRandomLoading(false);
    }
  };

  const handleGenerateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setGenError(null);

    try {
      const res = await api.generateAIQuestions({
        topic: genTopic || undefined,
        category: genCategory,
        difficulty: genDifficulty,
        role: genRole,
        count: genCount,
      });

      if (res.data && res.data.length > 0) {
        setShowGenModal(false);
        // Clear active filters so generated questions are visible immediately
        setSelectedCategory("All");
        setSelectedDifficulty("All");
        setRoleFilter("");
        setQuery("");
        setActiveTab("ai");
        const newItems = res.data;
        setQuestions((prev) => [
          ...newItems,
          ...prev.filter((p) => !newItems.some((n) => n.id === p.id)),
        ]);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setGenError(err.message);
      } else {
        setGenError("Failed to generate AI questions. Please try again.");
      }
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Interview Question Bank
          </h1>
          <p className="text-xs text-surface-200/70 mt-1">
            Master technical, behavioral, DSA, SQL, and AI-generated practice questions.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={handleGetRandom}
            className="px-4 py-2.5 rounded-xl bg-surface-900 hover:bg-surface-800 border border-white/10 text-white text-xs font-semibold shadow-md transition-all cursor-pointer flex items-center gap-1.5"
          >
            <span>🎲 Random Practice</span>
          </button>

          <button
            type="button"
            onClick={() => setShowGenModal(true)}
            className="px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 transition-all cursor-pointer flex items-center gap-1.5"
          >
            <span>✨ Generate AI Questions</span>
          </button>
        </div>
      </div>

      {/* Tabs & Search Filters */}
      <div className="rounded-2xl bg-surface-900 border border-white/10 p-4 sm:p-6 space-y-4 shadow-xl">
        <div className="flex items-center gap-2 border-b border-white/10 pb-3 flex-wrap">
          <button
            type="button"
            onClick={() => setActiveTab("all")}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "all"
                ? "bg-brand-600 text-white shadow-md"
                : "text-surface-200/70 hover:text-white hover:bg-white/5"
            }`}
          >
            All Questions
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("ai")}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === "ai"
                ? "bg-brand-600 text-white shadow-md"
                : "text-surface-200/70 hover:text-white hover:bg-white/5"
            }`}
          >
            <span>AI Practice Questions</span>
            <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 text-[10px] font-bold">
              AI
            </span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("saved")}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "saved"
                ? "bg-brand-600 text-white shadow-md"
                : "text-surface-200/70 hover:text-white hover:bg-white/5"
            }`}
          >
            ★ Bookmarked Favorites
          </button>
        </div>

        {/* Search Inputs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Keyword Query */}
          <div className="lg:col-span-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search question text or concepts..."
              className="w-full px-4 py-2 rounded-xl bg-surface-950 border border-white/10 text-white text-xs placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-all"
            />
          </div>

          {/* Role Filter */}
          <div>
            <input
              type="text"
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              placeholder="Role filter (e.g. Frontend)..."
              className="w-full px-3 py-2 rounded-xl bg-surface-950 border border-white/10 text-white text-xs placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-all"
            />
          </div>

          {/* Category Dropdown */}
          <div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-surface-950 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500 transition-all"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  Category: {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Difficulty Dropdown */}
          <div>
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-surface-950 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500 transition-all"
            >
              {DIFFICULTIES.map((diff) => (
                <option key={diff} value={diff}>
                  Difficulty: {diff}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-bold text-white">&times;</button>
        </div>
      )}

      {/* Main Question List */}
      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 rounded-2xl bg-surface-900/60 border border-white/5 p-6" />
          ))}
        </div>
      ) : questions.length === 0 ? (
        <div className="rounded-2xl bg-surface-900/60 border border-dashed border-white/10 p-12 text-center space-y-3">
          <p className="text-sm font-bold text-white">No interview questions found matching your filters.</p>
          <p className="text-xs text-surface-200/60">
            Try adjusting your search criteria or click &quot;Generate AI Questions&quot; to synthesize custom practice items.
          </p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                setSelectedCategory("All");
                setSelectedDifficulty("All");
                setRoleFilter("");
                setQuery("");
                setActiveTab("all");
              }}
              className="px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-white text-xs font-semibold cursor-pointer transition-all"
            >
              Reset Filters
            </button>
            <button
              type="button"
              onClick={() => setShowGenModal(true)}
              className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 cursor-pointer transition-all"
            >
              ✨ Generate AI Questions
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {questions.map((q) => {
            const isExpanded = expandedIds.has(q.id);
            const isSaving = savingId === q.id;

            return (
              <div
                key={q.id}
                className="rounded-2xl bg-surface-900/80 border border-white/10 p-5 sm:p-6 space-y-4 shadow-md hover:border-brand-500/30 transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    {/* Badges: Category, Difficulty, AI Source Label */}
                    <div className="flex items-center gap-2 flex-wrap text-[10px] font-bold">
                      <span className="px-2.5 py-0.5 rounded bg-surface-800 text-brand-300 border border-white/10">
                        {q.category}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded ${
                          q.difficulty === "Easy"
                            ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                            : q.difficulty === "Medium"
                            ? "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                            : "bg-red-500/10 text-red-300 border border-red-500/30"
                        }`}
                      >
                        {q.difficulty}
                      </span>

                      {/* Prominent Mandatory AI Source Label */}
                      <span
                        className={`px-2.5 py-0.5 rounded flex items-center gap-1 ${
                          q.source_type === "ai_generated"
                            ? "bg-purple-500/15 text-purple-300 border border-purple-500/30"
                            : "bg-surface-800 text-surface-300 border border-white/5"
                        }`}
                      >
                        {q.source_type === "ai_generated" && "🤖 "}
                        {q.source_label}
                      </span>
                    </div>

                    {/* Question Title */}
                    <h3 className="text-base font-bold text-white leading-snug">{q.question}</h3>

                    {/* Tags */}
                    {q.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {q.tags.map((tag, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded bg-surface-950 text-surface-200/70 text-[10px] font-medium"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Bookmark Button */}
                  <button
                    type="button"
                    disabled={isSaving}
                    onClick={() => handleToggleSave(q)}
                    className={`p-2 rounded-xl border transition-all cursor-pointer ${
                      q.is_saved
                        ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
                        : "bg-surface-800 border-white/10 text-surface-200/60 hover:text-white hover:bg-surface-700"
                    }`}
                  >
                    {isSaving ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <svg
                        className="w-4 h-4"
                        fill={q.is_saved ? "currentColor" : "none"}
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z"
                        />
                      </svg>
                    )}
                  </button>
                </div>

                {/* Explanation Toggle */}
                {q.explanation && (
                  <div className="pt-2 border-t border-white/5 space-y-2">
                    <button
                      type="button"
                      onClick={() => handleToggleExpand(q.id)}
                      className="text-xs font-semibold text-brand-400 hover:text-brand-300 transition-colors flex items-center gap-1 cursor-pointer"
                    >
                      <span>{isExpanded ? "Hide Answer Guide & Explanation" : "View Answer Guide & Explanation"}</span>
                      <svg
                        className={`w-3.5 h-3.5 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                      </svg>
                    </button>

                    {isExpanded && (
                      <div className="p-4 rounded-xl bg-surface-950 border border-white/5 text-xs text-surface-200/80 leading-relaxed whitespace-pre-wrap animate-fade-in">
                        {q.explanation}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Random Question Practice Modal */}
      {showRandomModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-xl rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-6">
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-brand-400">
                  Random Practice Mode
                </span>
                <h2 className="text-lg font-bold text-white">Question Spotlight</h2>
              </div>
              <button
                onClick={() => setShowRandomModal(false)}
                className="p-1 rounded-lg text-surface-200/60 hover:text-white hover:bg-white/10"
              >
                &times;
              </button>
            </div>

            {randomLoading ? (
              <div className="py-8 text-center space-y-3">
                <LoadingSpinner size="lg" />
                <p className="text-xs text-surface-200/60">Selecting random practice question...</p>
              </div>
            ) : randomQuestion ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-[10px] font-bold">
                  <span className="px-2 py-0.5 rounded bg-surface-800 text-brand-300">
                    {randomQuestion.category}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300">
                    {randomQuestion.difficulty}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300">
                    {randomQuestion.source_label}
                  </span>
                </div>

                <h3 className="text-base font-bold text-white">{randomQuestion.question}</h3>

                {randomQuestion.explanation && (
                  <div className="p-4 rounded-xl bg-surface-950 border border-white/5 text-xs text-surface-200/80 leading-relaxed whitespace-pre-wrap">
                    <span className="font-bold text-white block mb-1">Answer Guide:</span>
                    {randomQuestion.explanation}
                  </div>
                )}
              </div>
            ) : null}

            <div className="pt-4 border-t border-white/10 flex justify-between gap-3">
              <button
                type="button"
                onClick={handleGetRandom}
                className="px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-white text-xs font-semibold transition-all cursor-pointer"
              >
                Next Random Question 🎲
              </button>

              <button
                type="button"
                onClick={() => setShowRandomModal(false)}
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md transition-all cursor-pointer"
              >
                Done Practice
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generate AI Questions Modal */}
      {showGenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-950/80 backdrop-blur-sm animate-fade-in">
          <form
            onSubmit={handleGenerateSubmit}
            className="w-full max-w-lg rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-5"
          >
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div>
                <h2 className="text-lg font-bold text-white">Generate AI Practice Questions</h2>
                <p className="text-xs text-surface-200/60 mt-0.5">
                  Synthesize custom practice items explicitly marked as &quot;AI-generated practice question&quot;.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowGenModal(false)}
                className="p-1 rounded-lg text-surface-200/60 hover:text-white hover:bg-white/10"
              >
                &times;
              </button>
            </div>

            {genError && (
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
                {genError}
              </div>
            )}

            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-surface-200/70 font-medium mb-1">Target Job Role</label>
                <input
                  type="text"
                  value={genRole}
                  onChange={(e) => setGenRole(e.target.value)}
                  placeholder="e.g. Frontend Engineer, Data Analyst..."
                  className="w-full px-3 py-2 rounded-xl bg-surface-950 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-surface-200/70 font-medium mb-1">Category</label>
                  <select
                    value={genCategory}
                    onChange={(e) => setGenCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-surface-950 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                  >
                    {CATEGORIES.filter((c) => c !== "All").map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-surface-200/70 font-medium mb-1">Difficulty</label>
                  <select
                    value={genDifficulty}
                    onChange={(e) => setGenDifficulty(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-surface-950 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                  >
                    {DIFFICULTIES.filter((d) => d !== "All").map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-surface-200/70 font-medium mb-1">Specific Topic / Technology</label>
                <input
                  type="text"
                  value={genTopic}
                  onChange={(e) => setGenTopic(e.target.value)}
                  placeholder="e.g. System Architecture, Redux, PostgreSQL Indexing..."
                  className="w-full px-3 py-2 rounded-xl bg-surface-950 border border-white/10 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-surface-200 font-medium">Number of Questions (Up to 25)</label>
                  <span className="font-bold text-brand-300 bg-brand-500/20 px-2 py-0.5 rounded text-[11px] border border-brand-500/30">
                    {genCount} Questions
                  </span>
                </div>
                <div className="flex items-center gap-2 mb-2">
                  {[5, 10, 15, 20, 25].map((cnt) => (
                    <button
                      key={cnt}
                      type="button"
                      onClick={() => setGenCount(cnt)}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                        genCount === cnt
                          ? "bg-brand-600 text-white shadow-md shadow-brand-600/30 border border-brand-400"
                          : "bg-surface-950 text-surface-300 hover:bg-surface-800 border border-white/10"
                      }`}
                    >
                      {cnt}
                    </button>
                  ))}
                </div>
                <input
                  type="range"
                  min={1}
                  max={25}
                  value={genCount}
                  onChange={(e) => setGenCount(parseInt(e.target.value))}
                  className="w-full accent-brand-500 cursor-pointer"
                />
              </div>

            </div>

            <div className="pt-4 border-t border-white/10 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowGenModal(false)}
                className="px-4 py-2 rounded-xl bg-surface-800 text-surface-200 text-xs font-semibold"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={generating}
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md transition-all flex items-center gap-1.5"
              >
                {generating ? <LoadingSpinner size="sm" /> : "Generate Questions"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
