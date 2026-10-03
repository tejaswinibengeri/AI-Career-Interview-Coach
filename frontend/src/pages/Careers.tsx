import { useEffect, useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import api, { APIError, type OccupationData } from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

export default function Careers() {
  const navigate = useNavigate();

  const [query, setQuery] = useState<string>("");
  const [careers, setCareers] = useState<OccupationData[]>([]);
  const [selectedCareer, setSelectedCareer] = useState<OccupationData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzingGap, setAnalyzingGap] = useState<boolean>(false);
  const [settingGoal, setSettingGoal] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [goalSuccess, setGoalSuccess] = useState<string | null>(null);

  const fetchCareers = useCallback(async (searchQuery: string = "") => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.searchCareers(searchQuery);
      if (res.data) {
        setCareers(res.data);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to fetch occupation dataset.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCareers();
  }, [fetchCareers]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchCareers(query);
  };

  const handleSetGoal = async (careerId: number) => {
    setSettingGoal(true);
    setGoalSuccess(null);
    setError(null);
    try {
      const res = await api.setCareerGoal(careerId);
      if (res.data) {
        setGoalSuccess(`Target career goal set to '${res.data.title}'!`);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to set career goal.");
      }
    } finally {
      setSettingGoal(false);
    }
  };

  const handleAnalyzeGap = async (careerId: number) => {
    setAnalyzingGap(true);
    setError(null);
    try {
      await api.generateSkillGap(careerId);
      navigate("/career/skill-gap");
    } catch (err) {
      if (err instanceof APIError && err.status === 503) {
        setError("AI Service (Ollama) is currently offline. Ensure Ollama is running to generate AI skill gap reports.");
      } else if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to run skill gap analysis.");
      }
      setAnalyzingGap(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Career Selection & O*NET Occupations
          </h1>
          <p className="text-xs text-surface-200/70 mt-1">
            Explore standard O*NET industry roles and analyze how your skills compare against real occupation requirements.
          </p>
        </div>

        <Link
          to="/career/skill-gap"
          className="px-4 py-2.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs font-semibold text-brand-300 hover:text-white transition-all self-start md:self-auto flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
          </svg>
          View Latest Skill Gap Report
        </Link>
      </div>

      {/* Notifications */}
      {goalSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
          <span>{goalSuccess}</span>
          <button onClick={() => setGoalSuccess(null)} className="font-bold text-white">&times;</button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-bold text-white">&times;</button>
        </div>
      )}

      {/* Search Input Bar */}
      <form onSubmit={handleSearchSubmit} className="relative max-w-2xl">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search occupations (e.g., Software Developer, Data Scientist, DevOps, AI)..."
          className="w-full pl-11 pr-24 py-3.5 rounded-2xl bg-surface-900 border border-white/10 text-white text-xs placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-all shadow-inner"
        />
        <svg className="w-5 h-5 text-surface-200/40 absolute left-4 top-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <button
          type="submit"
          className="absolute right-2 top-2 bottom-2 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md transition-all cursor-pointer"
        >
          Search
        </button>
      </form>

      {/* Main Career Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-56 rounded-2xl bg-surface-900/60 border border-white/5 p-6" />
          ))}
        </div>
      ) : careers.length === 0 ? (
        <div className="rounded-2xl bg-surface-900/60 border border-dashed border-white/10 p-12 text-center space-y-3">
          <p className="text-sm font-bold text-white">No occupations found matching "{query}".</p>
          <button
            onClick={() => { setQuery(""); fetchCareers(""); }}
            className="px-4 py-2 rounded-xl bg-surface-800 text-xs text-brand-300 font-semibold cursor-pointer"
          >
            Clear Search Filter
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {careers.map((career) => (
            <div
              key={career.id}
              className="rounded-2xl bg-surface-900/80 border border-white/10 p-6 space-y-4 shadow-md hover:border-brand-500/40 transition-all flex flex-col justify-between group"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-surface-800 text-brand-400 border border-white/10 uppercase tracking-wider">
                      SOC {career.code}
                    </span>
                    <h3 className="text-base font-bold text-white mt-1 group-hover:text-brand-300 transition-colors">
                      {career.title}
                    </h3>
                  </div>
                  <span className="px-2.5 py-1 rounded-lg bg-brand-500/10 text-brand-300 text-[10px] font-semibold shrink-0">
                    {career.industry}
                  </span>
                </div>

                <p className="text-xs text-surface-200/70 line-clamp-3 leading-relaxed">
                  {career.description}
                </p>

                {/* Skills tags preview */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {career.skills.slice(0, 4).map((sk, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded bg-surface-800 text-[10px] font-medium text-surface-200/80 border border-white/5"
                    >
                      {sk.name}
                    </span>
                  ))}
                  {career.skills.length > 4 && (
                    <span className="text-[10px] text-surface-200/50 self-center">
                      +{career.skills.length - 4} more
                    </span>
                  )}
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="pt-4 border-t border-white/5 flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedCareer(career)}
                  className="text-xs text-surface-200/70 hover:text-white font-medium transition-colors"
                >
                  View Details
                </button>

                <button
                  type="button"
                  disabled={analyzingGap}
                  onClick={() => handleAnalyzeGap(career.id)}
                  className="px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/20 transition-all cursor-pointer flex items-center gap-1.5"
                >
                  {analyzingGap ? <LoadingSpinner size="sm" /> : null}
                  <span>Skill Gap AI</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Career Details Modal */}
      {selectedCareer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-3xl rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-6 max-h-[90vh] flex flex-col">
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-brand-500/10 text-brand-300 border border-brand-500/30 uppercase">
                  O*NET SOC {selectedCareer.code}
                </span>
                <h2 className="text-xl font-bold text-white mt-1">{selectedCareer.title}</h2>
                <p className="text-xs text-surface-200/60">{selectedCareer.industry}</p>
              </div>
              <button
                onClick={() => setSelectedCareer(null)}
                className="p-1 rounded-lg text-surface-200/60 hover:text-white hover:bg-white/10"
              >
                &times;
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-5 pr-2">
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">Occupation Description</h4>
                <p className="text-xs text-surface-200/80 leading-relaxed bg-surface-950 p-4 rounded-xl border border-white/5">
                  {selectedCareer.description}
                </p>
              </div>

              <div className="space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  Required Skill Profile ({selectedCareer.skills.length})
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {selectedCareer.skills.map((sk, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-surface-800/60 border border-white/5 flex items-center justify-between text-xs"
                    >
                      <div className="space-y-0.5">
                        <span className="font-semibold text-white">{sk.name}</span>
                        <p className="text-[10px] text-surface-200/50 uppercase">{sk.category}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-[11px] font-bold text-brand-300">{sk.importance}%</span>
                        <p className="text-[10px] text-surface-200/50">Importance</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="pt-4 border-t border-white/10 flex flex-col sm:flex-row items-center justify-end gap-3">
              <button
                type="button"
                disabled={settingGoal}
                onClick={() => handleSetGoal(selectedCareer.id)}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs font-semibold text-surface-200 hover:text-white transition-all cursor-pointer"
              >
                {settingGoal ? "Setting Goal..." : "Set as Target Career Goal"}
              </button>

              <button
                type="button"
                disabled={analyzingGap}
                onClick={() => handleAnalyzeGap(selectedCareer.id)}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 transition-all cursor-pointer flex items-center justify-center gap-2"
              >
                {analyzingGap ? <LoadingSpinner size="sm" /> : null}
                <span>Run Skill Gap AI Analysis</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
