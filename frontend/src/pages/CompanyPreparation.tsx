import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { APIError, type CompanyPrepData } from "../lib/api";
import AILoadingState from "../components/ui/AILoadingState";

const PRESET_COMPANIES = [
  "Google",
  "Amazon",
  "Microsoft",
  "Meta",
  "Apple",
  "Netflix",
  "Uber",
  "Tata Consultancy Services (TCS)",
  "Infosys",
  "Wipro",
  "Custom Company...",
];

const PRESET_ROLES = [
  "Software Engineer",
  "Backend Engineer",
  "Full Stack Engineer",
  "Frontend Engineer",
  "AI & Machine Learning Engineer",
  "Data Engineer",
  "DevOps Engineer",
  "Cloud Solutions Architect",
  "Custom Role...",
];

export default function CompanyPreparation() {
  const navigate = useNavigate();

  const [companyName, setCompanyName] = useState<string>("Google");
  const [customCompany, setCustomCompany] = useState<string>("");
  const [targetRole, setTargetRole] = useState<string>("Software Engineer");
  const [customRole, setCustomRole] = useState<string>("");

  const [currentPlan, setCurrentPlan] = useState<CompanyPrepData | null>(null);
  const [savedPlans, setSavedPlans] = useState<CompanyPrepData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filter state for practice questions
  const [selectedQuestionCategory, setSelectedQuestionCategory] = useState<string>("All");
  const [revealedQuestionIndices, setRevealedQuestionIndices] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchSavedPlans();
  }, []);

  const triggerGeneration = async (cName: string, tRole: string) => {
    setLoading(true);
    setError(null);
    setSelectedQuestionCategory("All");
    setRevealedQuestionIndices(new Set());

    try {
      const res = await api.generateCompanyPrepPlan(cName, tRole);
      if (res.data) {
        setCurrentPlan(res.data);
        const historyRes = await api.getSavedCompanyPrepPlans();
        if (historyRes.data) {
          setSavedPlans(historyRes.data);
        }
      } else {
        setError("Failed to generate company preparation plan.");
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Unable to generate preparation plan. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchSavedPlans = async () => {
    try {
      const res = await api.getSavedCompanyPrepPlans();
      if (res.data && res.data.length > 0) {
        setSavedPlans(res.data);
        if (!currentPlan) {
          setCurrentPlan(res.data[0]);
        }
      } else if (!currentPlan) {
        await triggerGeneration(companyName, targetRole);
      }
    } catch {
      if (!currentPlan) {
        await triggerGeneration(companyName, targetRole);
      }
    }
  };

  const handleGeneratePlan = async (e: React.FormEvent) => {
    e.preventDefault();

    const selectedCompany = companyName === "Custom Company..." ? customCompany.trim() : companyName;
    const selectedRole = targetRole === "Custom Role..." ? customRole.trim() : targetRole;

    if (!selectedCompany || !selectedRole) {
      setError("Please provide both company name and target role.");
      return;
    }

    await triggerGeneration(selectedCompany, selectedRole);
  };

  const toggleAnswerReveal = (index: number) => {
    setRevealedQuestionIndices((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const toggleAllAnswers = () => {
    if (!currentPlan) return;
    if (revealedQuestionIndices.size === currentPlan.practice_questions.length) {
      setRevealedQuestionIndices(new Set());
    } else {
      setRevealedQuestionIndices(new Set(currentPlan.practice_questions.map((_, i) => i)));
    }
  };

  const plan = currentPlan;

  // Extract unique question categories
  const questionCategories = plan
    ? ["All", ...Array.from(new Set(plan.practice_questions.map((q) => q.category || "General")))]
    : ["All"];

  const filteredQuestions = plan
    ? plan.practice_questions.filter((q) =>
        selectedQuestionCategory === "All" ? true : q.category === selectedQuestionCategory
      )
    : [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-950 via-surface-900 to-indigo-950/60 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs font-semibold">
          Module 13 • Company-Specific Interview Prep
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Target Company & Role Interview Preparation
        </h1>
        <p className="text-sm text-surface-200/80 max-w-3xl leading-relaxed">
          Master company-specific engineering culture, technical expectations, system design focus, behavioral frameworks, and hundreds of targeted practice questions with 1-click model answers.
        </p>
      </div>

      {/* Input Generator Form */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 shadow-xl space-y-5">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          Select Target Company & Role
        </h2>

        <form onSubmit={handleGeneratePlan} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          {/* Company Selection */}
          <div className="md:col-span-5 space-y-1.5">
            <label className="text-xs font-semibold text-surface-200/80 block">Target Company</label>
            <select
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
            >
              {PRESET_COMPANIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>

            {companyName === "Custom Company..." && (
              <input
                type="text"
                value={customCompany}
                onChange={(e) => setCustomCompany(e.target.value)}
                placeholder="Enter company name (e.g. Stripe, Uber, OpenAI)..."
                className="w-full px-3.5 py-2 rounded-xl bg-surface-800 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500 mt-2"
              />
            )}
          </div>

          {/* Role Selection */}
          <div className="md:col-span-5 space-y-1.5">
            <label className="text-xs font-semibold text-surface-200/80 block">Target Role</label>
            <select
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
            >
              {PRESET_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>

            {targetRole === "Custom Role..." && (
              <input
                type="text"
                value={customRole}
                onChange={(e) => setCustomRole(e.target.value)}
                placeholder="Enter role title (e.g. Site Reliability Engineer)..."
                className="w-full px-3.5 py-2 rounded-xl bg-surface-800 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500 mt-2"
              />
            )}
          </div>

          {/* Submit Action */}
          <div className="md:col-span-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-lg shadow-brand-600/20 transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              {loading ? "Generating..." : "Generate Plan 🚀"}
            </button>
          </div>
        </form>

        {error && <p className="text-xs font-semibold text-red-400">{error}</p>}
      </div>

      {/* Saved History Drawer / Select list */}
      {savedPlans.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2 text-xs">
          <span className="text-surface-200/60 font-medium whitespace-nowrap">Recent Plans:</span>
          {savedPlans.map((p) => (
            <button
              key={p.id}
              onClick={() => setCurrentPlan(p)}
              className={`px-3 py-1.5 rounded-xl border text-xs transition-all cursor-pointer whitespace-nowrap ${
                currentPlan?.id === p.id
                  ? "bg-brand-600 text-white border-brand-500 font-bold"
                  : "bg-surface-800 text-surface-200/80 border-white/10 hover:border-white/20"
              }`}
            >
              {p.company_name} ({p.target_role})
            </button>
          ))}
        </div>
      )}

      {loading && (
        <AILoadingState
          title={`Analyzing ${companyName === "Custom Company..." ? customCompany || "Custom Company" : companyName}`}
          subtitle="Fetching verified corporate intelligence and generating tailored interview prep..."
          steps={[
            "Checking verified public corporate knowledge registry...",
            "Analyzing core technical and cultural competencies...",
            "Formulating HR & behavioral interview strategies...",
            "Generating AI practice question prompts with detailed model answers...",
          ]}
        />
      )}

      {/* Output Plan Display */}
      {plan && !loading && (
        <div className="space-y-6 animate-fade-in">
          {/* Verification Status Banner */}
          <div
            className={`p-4 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
              plan.is_verified_company
                ? "bg-emerald-950/30 border-emerald-500/30 text-emerald-200"
                : "bg-amber-950/30 border-amber-500/30 text-amber-200"
            }`}
          >
            <div className="flex items-start gap-3">
              <span className="text-xl">{plan.is_verified_company ? "✓" : "⚠️"}</span>
              <div>
                <h3 className="text-sm font-bold">
                  {plan.is_verified_company
                    ? `Verified Public Company Overview for ${plan.company_name}`
                    : `Unverified Company Disclaimer for ${plan.company_name}`}
                </h3>
                <p className="text-xs opacity-80 mt-0.5">
                  {plan.verification_notes ||
                    "Company facts verified against official public corporate databases."}
                </p>
              </div>
            </div>

            <button
              onClick={() => navigate("/interview")}
              className="px-3.5 py-1.5 rounded-xl bg-surface-900 hover:bg-surface-800 border border-white/10 text-white font-bold text-xs transition-colors cursor-pointer whitespace-nowrap self-start sm:self-auto"
            >
              Start AI Mock Interview 🎙️
            </button>
          </div>

          {/* Section 1: Company Overview & Role Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Overview */}
            <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 space-y-3 shadow-xl">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider text-[11px] text-brand-300">
                Company Overview & Engineering Culture
              </h2>
              <p className="text-xs text-surface-200 leading-relaxed bg-surface-950/40 p-4 rounded-xl border border-white/5">
                {plan.company_overview}
              </p>
            </div>

            {/* Role Expectations */}
            <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 space-y-3 shadow-xl">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider text-[11px] text-purple-300">
                Target Role Expectations ({plan.target_role})
              </h2>
              <p className="text-xs text-surface-200 leading-relaxed bg-surface-950/40 p-4 rounded-xl border border-white/5">
                {plan.role_summary}
              </p>

              {/* Skills */}
              <div className="pt-2">
                <span className="text-[11px] font-semibold text-surface-200/60 block mb-2">Required Key Competencies:</span>
                <div className="flex flex-wrap gap-1.5">
                  {plan.required_skills.map((skill, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-surface-800 border border-white/10 text-xs font-semibold text-surface-200">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Technical Preparation & Coding Topics */}
          <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-7 space-y-5 shadow-xl">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
              </svg>
              Technical & Coding Preparation Roadmap
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Technical Topics */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-surface-200/70 uppercase tracking-wider">Core Technical Focus Areas</h3>
                {plan.technical_prep_topics.map((t, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-surface-800/60 border border-white/5 space-y-1 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white">{t.topic}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] bg-brand-500/10 text-brand-300 border border-brand-500/20 font-bold">
                        {t.importance} Priority
                      </span>
                    </div>
                    <p className="text-surface-200/70">{t.description}</p>
                  </div>
                ))}
              </div>

              {/* Coding Topics */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-surface-200/70 uppercase tracking-wider">Essential Coding Topics</h3>
                <div className="p-4 rounded-xl bg-surface-800/60 border border-white/5 space-y-2">
                  <h4 className="font-bold text-emerald-300 uppercase tracking-wider text-[11px]">Key Problem Patterns</h4>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {plan.coding_topics.map((topic, idx) => (
                      <span key={idx} className="px-2.5 py-1 rounded-lg bg-surface-700 text-surface-200 text-xs font-medium">
                        {topic}
                      </span>
                    ))}
                  </div>
                  <p className="text-[11px] text-surface-400 pt-2">
                    Practice these topics directly in our isolated Coding Sandbox system.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: HR & Behavioral Preparation */}
          <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-7 space-y-5 shadow-xl">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
              HR & Behavioral Preparation Framework
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {/* HR Topics */}
              <div className="p-4 rounded-xl bg-surface-800/60 border border-white/5 space-y-2">
                <h3 className="font-bold text-amber-300 uppercase tracking-wider text-[11px]">Common HR Questions</h3>
                <ul className="space-y-2 list-disc list-inside text-surface-200">
                  {plan.hr_topics.map((hr, idx) => (
                    <li key={idx}>{hr}</li>
                  ))}
                </ul>
              </div>

              {/* Behavioral Principles */}
              <div className="space-y-3">
                {plan.behavioral_prep.map((b, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-surface-800/60 border border-white/5 space-y-1">
                    <span className="font-bold text-purple-300 block">{b.principle}</span>
                    <p className="text-surface-200/80">{b.advice}</p>
                    <p className="text-[11px] text-surface-400 italic border-t border-white/5 pt-1 mt-1">
                      Prompt: "{b.example_prompt}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Section 4: Targeted Practice Questions with 1-Click Answers */}
          <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-7 space-y-5 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-4">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M12 18h.008v.008H12V18z" />
                  </svg>
                  Targeted Practice Questions ({plan.practice_questions.length} Total)
                </h2>
                <p className="text-xs text-surface-400 mt-0.5">
                  Detailed practice questions customized for {plan.company_name} ({plan.target_role}) with 1-click model answers.
                </p>
              </div>

              {/* Global Answer Toggle Button */}
              <div className="flex items-center gap-2">
                <button
                  onClick={toggleAllAnswers}
                  className="px-3 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-brand-300 border border-brand-500/30 text-xs font-semibold cursor-pointer transition-all"
                >
                  {revealedQuestionIndices.size === plan.practice_questions.length
                    ? "🙈 Hide All Answers"
                    : "💡 Reveal All Answers"}
                </button>
              </div>
            </div>

            {/* Category Filter Tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              {questionCategories.map((cat) => {
                const count =
                  cat === "All"
                    ? plan.practice_questions.length
                    : plan.practice_questions.filter((q) => q.category === cat).length;
                return (
                  <button
                    key={cat}
                    onClick={() => setSelectedQuestionCategory(cat)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
                      selectedQuestionCategory === cat
                        ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                        : "bg-surface-800 text-surface-300 hover:bg-surface-700 hover:text-white"
                    }`}
                  >
                    <span>{cat}</span>
                    <span className="px-1.5 py-0.2 rounded-full bg-white/10 text-[10px] font-bold">
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="space-y-4">
              {filteredQuestions.map((pq, idx) => {
                const isRevealed = revealedQuestionIndices.has(idx);
                return (
                  <div key={idx} className="p-5 rounded-2xl bg-surface-800/60 border border-white/5 space-y-3 shadow-md">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      {/* Mandatory Label Badge */}
                      <span className="px-2.5 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/30 text-[10px] font-extrabold uppercase">
                        {pq.label || "AI-generated practice question"}
                      </span>

                      <div className="flex items-center gap-2 text-[10px]">
                        <span className="px-2.5 py-0.5 rounded bg-brand-500/20 text-brand-300 font-semibold border border-brand-500/30">
                          {pq.category}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded font-bold ${
                            pq.difficulty === "Hard"
                              ? "bg-red-500/20 text-red-300 border border-red-500/30"
                              : pq.difficulty === "Medium"
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                              : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          }`}
                        >
                          {pq.difficulty}
                        </span>
                      </div>
                    </div>

                    <h3 className="text-sm font-bold text-white leading-snug">{pq.question_text}</h3>

                    {/* 1-Click Model Answer Reveal Button */}
                    <div>
                      <button
                        type="button"
                        onClick={() => toggleAnswerReveal(idx)}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer ${
                          isRevealed
                            ? "bg-brand-600 text-white border-brand-500 shadow-md shadow-brand-600/30"
                            : "bg-brand-600/15 hover:bg-brand-600/25 border-brand-500/30 text-brand-300"
                        }`}
                      >
                        <span>{isRevealed ? "Hide Solution" : "💡 1-Click Answer & Explanation"}</span>
                        <svg
                          className={`w-3.5 h-3.5 transition-transform ${isRevealed ? "rotate-180" : ""}`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                        </svg>
                      </button>

                      {isRevealed && (
                        <div className="mt-3 p-4 rounded-xl bg-surface-950/90 border border-brand-500/30 space-y-2 text-xs animate-fade-in shadow-inner">
                          <span className="text-[11px] font-bold text-brand-300 uppercase tracking-wider block">
                            Detailed Model Solution & Technical Key Points
                          </span>
                          <ul className="list-disc list-inside text-surface-200 space-y-1.5 leading-relaxed">
                            {pq.sample_answer_points && pq.sample_answer_points.length > 0 ? (
                              pq.sample_answer_points.map((pt, i) => (
                                <li key={i}>{pt}</li>
                              ))
                            ) : (
                              <li>Provide a clear, structured technical explanation with architectural trade-offs and code examples where applicable.</li>
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
