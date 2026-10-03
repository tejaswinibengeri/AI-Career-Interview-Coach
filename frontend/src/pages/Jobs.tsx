import { useEffect, useState, useCallback } from "react";
import api, { APIError, type JobData, type JobMatchData } from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

export default function Jobs() {
  const [query, setQuery] = useState<string>("");
  const [location, setLocation] = useState<string>("");
  const [isRemote, setIsRemote] = useState<boolean>(false);

  const [activeTab, setActiveTab] = useState<"search" | "saved">("search");
  const [jobs, setJobs] = useState<JobData[]>([]);
  const [savedJobs, setSavedJobs] = useState<JobData[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobData | null>(null);

  const [matchModalJob, setMatchModalJob] = useState<JobData | null>(null);
  const [jobMatchData, setJobMatchData] = useState<JobMatchData | null>(null);
  const [matchingJobId, setMatchingJobId] = useState<number | null>(null);
  const [matchError, setMatchError] = useState<string | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isProviderUnavailable, setIsProviderUnavailable] = useState<boolean>(false);

  const fetchJobs = useCallback(async (q: string = "", loc: string = "", remote: boolean = false) => {
    setLoading(true);
    setError(null);
    setIsProviderUnavailable(false);

    try {
      const res = await api.searchJobs(q, loc, remote);
      if (res.data) {
        setJobs(res.data);
      }
    } catch (err) {
      if (err instanceof APIError && err.status === 503) {
        setIsProviderUnavailable(true);
        setError("Job search is temporarily unavailable. Please try again later.");
      } else if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to fetch job listings.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchSavedJobs = useCallback(async () => {
    try {
      const res = await api.getSavedJobs();
      if (res.data) {
        setSavedJobs(res.data);
      }
    } catch {
      // Ignore background bookmark fetch errors
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    fetchSavedJobs();
  }, [fetchJobs, fetchSavedJobs]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveTab("search");
    fetchJobs(query, location, isRemote);
  };

  const handleToggleSave = async (job: JobData) => {
    setSavingId(job.id);
    try {
      if (job.is_saved) {
        const res = await api.unsaveJob(job.id);
        if (res.data) {
          updateJobSavedState(job.id, false);
        }
      } else {
        const res = await api.saveJob(job.id);
        if (res.data) {
          updateJobSavedState(job.id, true);
        }
      }
      await fetchSavedJobs();
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      }
    } finally {
      setSavingId(null);
    }
  };

  const handleMatchResume = async (job: JobData) => {
    setMatchingJobId(job.id);
    setMatchModalJob(job);
    setJobMatchData(null);
    setMatchError(null);

    try {
      const res = await api.matchResumeToJob(job.id);
      if (res.data) {
        setJobMatchData(res.data);
      }
    } catch (err) {
      if (err instanceof APIError && err.status === 503) {
        setMatchError("AI Service (Ollama) is currently offline. Ensure Ollama is running to calculate resume match.");
      } else if (err instanceof APIError) {
        setMatchError(err.message);
      } else {
        setMatchError("Failed to calculate resume-to-job match.");
      }
    } finally {
      setMatchingJobId(null);
    }
  };

  const updateJobSavedState = (jobId: number, isSaved: boolean) => {
    setJobs((prev) =>
      prev.map((j) => (j.id === jobId ? { ...j, is_saved: isSaved } : j))
    );
    if (selectedJob && selectedJob.id === jobId) {
      setSelectedJob({ ...selectedJob, is_saved: isSaved });
    }
  };

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return null;
    try {
      return new Date(isoString).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return null;
    }
  };

  const formatSalary = (min?: number | null, max?: number | null, currency: string = "USD") => {
    if (!min && !max) return null;
    const symbol = currency === "USD" ? "$" : currency;
    if (min && max) {
      return `${symbol}${min.toLocaleString()} - ${symbol}${max.toLocaleString()}/yr`;
    }
    if (min) return `From ${symbol}${min.toLocaleString()}/yr`;
    return `Up to ${symbol}${max?.toLocaleString()}/yr`;
  };

  const displayedJobs = activeTab === "search" ? jobs : savedJobs;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Real Job Search & Listings
          </h1>
          <p className="text-xs text-surface-200/70 mt-1">
            Search live authentic opportunities directly from external job provider APIs.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1 bg-surface-900 border border-white/10 p-1 rounded-xl shrink-0 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setActiveTab("search")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "search"
                ? "bg-brand-600 text-white shadow-md"
                : "text-surface-200/70 hover:text-white hover:bg-white/5"
            }`}
          >
            Live Search
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab("saved"); fetchSavedJobs(); }}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === "saved"
                ? "bg-brand-600 text-white shadow-md"
                : "text-surface-200/70 hover:text-white hover:bg-white/5"
            }`}
          >
            <span>Saved Bookmarks</span>
            {savedJobs.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-white/20 text-[10px] font-bold">
                {savedJobs.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Search & Filter Form */}
      <form onSubmit={handleSearchSubmit} className="rounded-2xl bg-surface-900 border border-white/10 p-4 sm:p-6 space-y-4 shadow-xl">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Keyword Search */}
          <div className="lg:col-span-2">
            <label className="block text-[11px] font-medium text-surface-200/60 mb-1">Job Role / Keyword</label>
            <div className="relative">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Software Engineer, Python Developer, Data Scientist..."
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-950 border border-white/10 text-white text-xs placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-all"
              />
              <svg className="w-4 h-4 text-surface-200/40 absolute left-3.5 top-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
            </div>
          </div>

          {/* Location Search */}
          <div>
            <label className="block text-[11px] font-medium text-surface-200/60 mb-1">Location</label>
            <div className="relative">
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="City, State, or Country"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-950 border border-white/10 text-white text-xs placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-all"
              />
              <svg className="w-4 h-4 text-surface-200/40 absolute left-3.5 top-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
              </svg>
            </div>
          </div>

          {/* Remote Toggle & Search Button */}
          <div className="flex items-center gap-3 pt-5">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={isRemote}
                onChange={(e) => setIsRemote(e.target.checked)}
                className="w-4 h-4 rounded border-white/20 bg-surface-950 text-brand-500 focus:ring-0 cursor-pointer"
              />
              <span className="text-xs font-semibold text-surface-200">Remote Only</span>
            </label>

            <button
              type="submit"
              className="flex-1 py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 transition-all cursor-pointer text-center"
            >
              Find Jobs
            </button>
          </div>
        </div>
      </form>

      {/* Generic Error Message Banner */}
      {error && !isProviderUnavailable && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-bold text-white">&times;</button>
        </div>
      )}

      {/* Required Provider Error Message Banner */}
      {isProviderUnavailable && (
        <div className="rounded-2xl bg-surface-900 border border-amber-500/30 p-8 text-center space-y-3 shadow-xl">
          <div className="w-12 h-12 rounded-full bg-amber-500/10 text-amber-400 mx-auto flex items-center justify-center border border-amber-500/20">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-white">Job Search Temporarily Unavailable</h2>
          <p className="text-xs text-amber-300 font-medium max-w-md mx-auto leading-relaxed">
            Job search is temporarily unavailable. Please try again later.
          </p>
        </div>
      )}

      {/* Main Job Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-48 rounded-2xl bg-surface-900/60 border border-white/5 p-6" />
          ))}
        </div>
      ) : !isProviderUnavailable && displayedJobs.length === 0 ? (
        <div className="rounded-2xl bg-surface-900/60 border border-dashed border-white/10 p-12 text-center space-y-3">
          <p className="text-sm font-bold text-white">
            {activeTab === "saved"
              ? "You have not saved any jobs yet."
              : "No job listings found matching your search criteria."}
          </p>
          <p className="text-xs text-surface-200/60">
            {activeTab === "saved"
              ? "Browse live search listings and click the bookmark icon to save jobs for later."
              : "Try broadening your keyword or location filters."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {displayedJobs.map((job) => {
            const isSaving = savingId === job.id;
            const salaryText = formatSalary(job.salary_min, job.salary_max, job.salary_currency || "USD");

            return (
              <div
                key={job.id}
                className="rounded-2xl bg-surface-900/80 border border-white/10 p-6 space-y-4 shadow-md hover:border-brand-500/40 transition-all flex flex-col justify-between group"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-surface-800 text-brand-300 border border-white/10 uppercase tracking-wider">
                          {job.provider}
                        </span>
                        {job.is_remote && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                            Remote
                          </span>
                        )}
                        {job.posted_at && (
                          <span className="text-[10px] text-surface-200/50">
                            Posted {formatDate(job.posted_at)}
                          </span>
                        )}
                      </div>

                      <h3 className="text-base font-bold text-white group-hover:text-brand-300 transition-colors">
                        {job.title}
                      </h3>
                      <p className="text-xs font-medium text-surface-200/80">{job.company}</p>
                    </div>

                    {/* Bookmark Toggle Icon */}
                    <button
                      type="button"
                      disabled={isSaving}
                      onClick={() => handleToggleSave(job)}
                      className={`p-2 rounded-xl border transition-all cursor-pointer ${
                        job.is_saved
                          ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
                          : "bg-surface-800 border-white/10 text-surface-200/60 hover:text-white hover:bg-surface-700"
                      }`}
                    >
                      {isSaving ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <svg className="w-4 h-4" fill={job.is_saved ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
                        </svg>
                      )}
                    </button>
                  </div>

                  {/* Metadata Chips: Location & Salary */}
                  <div className="flex flex-wrap items-center gap-3 text-xs text-surface-200/70">
                    <div className="flex items-center gap-1">
                      <svg className="w-3.5 h-3.5 text-surface-200/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                      </svg>
                      <span>{job.location}</span>
                    </div>

                    {salaryText && (
                      <div className="flex items-center gap-1 text-emerald-400 font-semibold">
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-6h6" />
                        </svg>
                        <span>{salaryText}</span>
                      </div>
                    )}
                  </div>

                  {/* Description Snippet */}
                  <p className="text-xs text-surface-200/70 line-clamp-3 leading-relaxed">
                    {job.description}
                  </p>
                </div>

                {/* Card Actions */}
                <div className="pt-4 border-t border-white/5 flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setSelectedJob(job)}
                      className="text-xs text-surface-200/70 hover:text-white font-medium transition-colors"
                    >
                      View Details
                    </button>

                    <button
                      type="button"
                      disabled={matchingJobId === job.id}
                      onClick={() => handleMatchResume(job)}
                      className="px-3 py-1.5 rounded-xl bg-brand-500/20 hover:bg-brand-500/30 text-brand-300 border border-brand-500/30 text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer"
                    >
                      {matchingJobId === job.id ? <LoadingSpinner size="sm" /> : "⚡ Match My Resume"}
                    </button>
                  </div>

                  <a
                    href={job.redirect_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/20 transition-all flex items-center gap-1.5"
                  >
                    <span>Apply Now</span>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                    </svg>
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Detailed Job Modal */}
      {selectedJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-2xl rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-6 max-h-[85vh] flex flex-col">
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-surface-800 text-brand-300 uppercase">
                    {selectedJob.provider}
                  </span>
                  {selectedJob.is_remote && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                      Remote
                    </span>
                  )}
                </div>
                <h2 className="text-xl font-bold text-white">{selectedJob.title}</h2>
                <p className="text-xs text-surface-200/70">{selectedJob.company} • {selectedJob.location}</p>
              </div>
              <button
                onClick={() => setSelectedJob(null)}
                className="p-1 rounded-lg text-surface-200/60 hover:text-white hover:bg-white/10"
              >
                &times;
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
              {formatSalary(selectedJob.salary_min, selectedJob.salary_max, selectedJob.salary_currency || "USD") && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-300">
                  Salary Range: {formatSalary(selectedJob.salary_min, selectedJob.salary_max, selectedJob.salary_currency || "USD")}
                </div>
              )}

              <div className="space-y-2">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">Job Description</h4>
                <p className="text-xs text-surface-200/80 leading-relaxed whitespace-pre-wrap bg-surface-950 p-4 rounded-xl border border-white/5">
                  {selectedJob.description}
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-white/10 flex items-center justify-between gap-3 flex-wrap">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleToggleSave(selectedJob)}
                  className={`px-4 py-2.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer ${
                    selectedJob.is_saved
                      ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
                      : "bg-surface-800 border-white/10 text-surface-200 hover:text-white"
                  }`}
                >
                  {selectedJob.is_saved ? "★ Saved" : "☆ Save"}
                </button>

                <button
                  type="button"
                  disabled={matchingJobId === selectedJob.id}
                  onClick={() => handleMatchResume(selectedJob)}
                  className="px-4 py-2.5 rounded-xl bg-brand-500/20 hover:bg-brand-500/30 text-brand-300 border border-brand-500/30 text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer"
                >
                  {matchingJobId === selectedJob.id ? <LoadingSpinner size="sm" /> : "⚡ Match My Resume"}
                </button>
              </div>

              <a
                href={selectedJob.redirect_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 transition-all inline-flex items-center gap-2"
              >
                <span>Apply on Official Website</span>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Resume-to-Job Match Analysis Modal */}
      {matchModalJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-2xl rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-6 max-h-[85vh] flex flex-col">
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-brand-400">
                  Resume-to-Job Compatibility Analysis
                </span>
                <h2 className="text-xl font-bold text-white">{matchModalJob.title}</h2>
                <p className="text-xs text-surface-200/70">{matchModalJob.company}</p>
              </div>
              <button
                onClick={() => { setMatchModalJob(null); setJobMatchData(null); }}
                className="p-1 rounded-lg text-surface-200/60 hover:text-white hover:bg-white/10"
              >
                &times;
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-6 pr-2">
              {matchingJobId === matchModalJob.id ? (
                <div className="py-12 text-center space-y-4">
                  <div className="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 mx-auto flex items-center justify-center animate-pulse">
                    <LoadingSpinner size="lg" />
                  </div>
                  <h3 className="text-sm font-bold text-white">Analyzing Resume & Job Compatibility...</h3>
                  <p className="text-xs text-surface-200/60 max-w-sm mx-auto">
                    Computing deterministic skill overlap and generating AI match explanation via Ollama.
                  </p>
                </div>
              ) : matchError ? (
                <div className="p-6 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-center space-y-3">
                  <p className="text-xs font-semibold text-amber-300">{matchError}</p>
                </div>
              ) : jobMatchData ? (
                <div className="space-y-6">
                  {/* Score Circular Banner */}
                  <div className="rounded-2xl bg-gradient-to-r from-surface-950 to-surface-850 border border-white/10 p-6 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-inner">
                    <div className="flex items-center gap-4">
                      <div className={`w-20 h-20 rounded-2xl flex items-center justify-center font-extrabold text-2xl border shadow-lg ${
                        jobMatchData.match_score >= 80 ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" :
                        jobMatchData.match_score >= 60 ? "bg-amber-500/10 text-amber-400 border-amber-500/30" : "bg-red-500/10 text-red-400 border-red-500/30"
                      }`}>
                        {jobMatchData.match_score}%
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-white">Overall Compatibility</h4>
                        <p className="text-xs text-surface-200/60 mt-0.5">
                          {jobMatchData.match_score >= 80 ? "Strong candidate alignment for this position." :
                           jobMatchData.match_score >= 60 ? "Moderate alignment with a few missing skill gaps." : "Potential skill gaps for this job role."}
                        </p>
                      </div>
                    </div>

                    <div className="w-full sm:w-44 space-y-3 text-xs">
                      <div>
                        <div className="flex justify-between text-[11px] font-semibold text-surface-200/70 mb-1">
                          <span>Experience Match</span>
                          <span>{jobMatchData.experience_match}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-surface-950 overflow-hidden">
                          <div className="h-full bg-brand-500 rounded-full" style={{ width: `${jobMatchData.experience_match}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-[11px] font-semibold text-surface-200/70 mb-1">
                          <span>Education Match</span>
                          <span>{jobMatchData.education_match}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-surface-950 overflow-hidden">
                          <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${jobMatchData.education_match}%` }} />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Skills Grid: Matched & Missing */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-surface-950 border border-white/5 space-y-2">
                      <h5 className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">
                        ✓ Matched Skills ({jobMatchData.matched_skills.length})
                      </h5>
                      <div className="flex flex-wrap gap-1.5">
                        {jobMatchData.matched_skills.map((s, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 text-xs font-medium border border-emerald-500/20">
                            {s}
                          </span>
                        ))}
                        {jobMatchData.matched_skills.length === 0 && <span className="text-xs text-surface-200/50">No exact match found</span>}
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-surface-950 border border-white/5 space-y-2">
                      <h5 className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                        ⚠ Missing Skills ({jobMatchData.missing_skills.length})
                      </h5>
                      <div className="flex flex-wrap gap-1.5">
                        {jobMatchData.missing_skills.map((s, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 text-xs font-medium border border-amber-500/20">
                            {s}
                          </span>
                        ))}
                        {jobMatchData.missing_skills.length === 0 && <span className="text-xs text-surface-200/50">No critical gaps identified</span>}
                      </div>
                    </div>
                  </div>

                  {/* AI Explanation Narrative */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider">AI Compatibility Explanation</h4>
                    <p className="text-xs text-surface-200/80 leading-relaxed bg-surface-950 p-4 rounded-xl border border-white/5">
                      {jobMatchData.explanation}
                    </p>
                  </div>

                  {/* Recommendations */}
                  {jobMatchData.recommendations.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-brand-300 uppercase tracking-wider">Tailored Resume Recommendations</h4>
                      <ul className="space-y-1.5 text-xs text-surface-200/80 bg-surface-950 p-4 rounded-xl border border-white/5">
                        {jobMatchData.recommendations.map((rec, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-brand-400 font-bold">•</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : null}
            </div>

            <div className="pt-4 border-t border-white/10 flex justify-end">
              <a
                href={matchModalJob.redirect_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 transition-all inline-flex items-center gap-2"
              >
                <span>Apply for this Job</span>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
