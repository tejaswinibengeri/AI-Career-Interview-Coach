import { useEffect, useState } from "react";
import api, { APIError, type QuestionData } from "../../lib/api";

export default function AdminQuestions() {
  const [questions, setQuestions] = useState<QuestionData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [showForm, setShowForm] = useState<boolean>(false);
  const [category, setCategory] = useState<string>("Technical");
  const [topic, setTopic] = useState<string>("Python");
  const [difficulty, setDifficulty] = useState<string>("Medium");
  const [questionText, setQuestionText] = useState<string>("");
  const [sampleAnswer, setSampleAnswer] = useState<string>("");
  const [explanation, setExplanation] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);

  useEffect(() => {
    fetchQuestions();
  }, []);

  const fetchQuestions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminQuestions();
      if (res.data) {
        setQuestions(res.data);
      } else {
        setError("Failed to load questions.");
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

  const handleCreateQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!questionText.trim()) return;

    setSubmitting(true);
    try {
      const res = await api.createAdminQuestion({
        category,
        topic,
        difficulty,
        question_text: questionText.trim(),
        sample_answer: sampleAnswer.trim() || undefined,
        explanation: explanation.trim() || undefined,
      });

      if (res.data) {
        setQuestions([res.data, ...questions]);
        setShowForm(false);
        setQuestionText("");
        setSampleAnswer("");
        setExplanation("");
      }
    } catch {
      // Ignore error
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteQuestion = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this question?")) return;
    try {
      await api.deleteAdminQuestion(id);
      setQuestions(questions.filter((q) => q.id !== id));
    } catch {
      // Ignore error
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Question Bank Moderation</h2>
          <p className="text-xs text-surface-200/60">Manage technical, HR, and behavioral interview questions</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition-colors cursor-pointer"
        >
          {showForm ? "Cancel" : "+ Add Question"}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Question Form */}
      {showForm && (
        <form onSubmit={handleCreateQuestion} className="bg-surface-900 border border-white/10 rounded-2xl p-6 space-y-4 shadow-2xl animate-fade-in">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">New Question item</h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-surface-200 mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs"
              >
                <option value="Technical">Technical</option>
                <option value="HR">HR</option>
                <option value="Behavioral">Behavioral</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-200 mb-1">Topic</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-200 mb-1">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs"
              >
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-200 mb-1">Question Prompt</label>
            <textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              rows={3}
              className="w-full p-3 rounded-xl bg-surface-800 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-200 mb-1">Sample Answer / Solution Guide (Optional)</label>
            <textarea
              value={sampleAnswer}
              onChange={(e) => setSampleAnswer(e.target.value)}
              rows={2}
              className="w-full p-3 rounded-xl bg-surface-800 border border-white/10 text-white text-xs"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={submitting || !questionText.trim()}
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition-colors cursor-pointer disabled:opacity-50"
            >
              {submitting ? "Saving..." : "Save Question to Bank"}
            </button>
          </div>
        </form>
      )}

      {/* Questions List */}
      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-surface-900 rounded-2xl border border-white/5" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {questions.map((q) => (
            <div
              key={q.id}
              className="bg-surface-900 border border-white/10 rounded-2xl p-5 space-y-3 shadow-xl flex items-start justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-300 text-[10px] font-bold">
                    {q.category}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-surface-800 border border-white/10 text-surface-200 text-[10px] font-medium">
                    {q.role}
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                      q.difficulty === "Hard"
                        ? "bg-red-500/15 text-red-300"
                        : q.difficulty === "Medium"
                        ? "bg-amber-500/15 text-amber-300"
                        : "bg-emerald-500/15 text-emerald-300"
                    }`}
                  >
                    {q.difficulty}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white leading-relaxed">{q.question}</h3>
                {q.explanation && (
                  <p className="text-xs text-surface-200/60 line-clamp-2 italic">Guide: {q.explanation}</p>
                )}
              </div>


              <button
                onClick={() => handleDeleteQuestion(q.id)}
                className="p-2 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500/20 text-xs font-bold transition-colors cursor-pointer"
                title="Delete Question"
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
