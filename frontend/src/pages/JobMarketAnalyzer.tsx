import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import api, {
  APIError,
  type JobMarketSearchResponseData,
  type JobMarketListingData,
  type JobMarketAnalyticsData,
  type ProfileData,
} from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

export default function JobMarketAnalyzer() {
  // Search and Filter State
  const [query, setQuery] = useState<string>("");
  const [location, setLocation] = useState<string>("");
  const [workplaceType, setWorkplaceType] = useState<string>("All");
  const [experienceLevel, setExperienceLevel] = useState<string>("All");
  const [skills, setSkills] = useState<string>("");
  const [company, setCompany] = useState<string>("");
  const [jobType, setJobType] = useState<string>("All");
  const [datePosted, setDatePosted] = useState<string>("all");
  const [useProfile, setUseProfile] = useState<boolean>(false);

  // Response data
  const [searchResponse, setSearchResponse] = useState<JobMarketSearchResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Candidate profile for comparison
  const [profile, setProfile] = useState<ProfileData | null>(null);

  // Fetch candidate profile for "Use My Profile" toggle
  useEffect(() => {
    async function fetchProfile() {
      try {
        const res = await api.getProfile();
        if (res.data) {
          setProfile(res.data);
        }
      } catch {
        // Silently continue if profile fetch fails
      }
    }
    fetchProfile();
  }, []);

  // Main search function
  const executeSearch = useCallback(
    async (overrideUseProfile?: boolean) => {
      setLoading(true);
      setError(null);

      const activeUseProfile = overrideUseProfile !== undefined ? overrideUseProfile : useProfile;

      try {
        const res = await api.searchJobMarket({
          query: query.trim() || undefined,
          location: location.trim() || undefined,
          workplace_type: workplaceType !== "All" ? workplaceType : undefined,
          experience_level: experienceLevel !== "All" ? experienceLevel : undefined,
          skills: skills.trim() || undefined,
          company: company.trim() || undefined,
          job_type: jobType !== "All" ? jobType : undefined,
          date_posted: datePosted !== "all" ? datePosted : undefined,
          use_profile: activeUseProfile,
        });

        if (res.data) {
          setSearchResponse(res.data);
        }
      } catch (err) {
        if (err instanceof APIError) {
          setError(err.message);
        } else {
          setError("Failed to query live job market data.");
        }
      } finally {
        setLoading(false);
      }
    },
    [query, location, workplaceType, experienceLevel, skills, company, jobType, datePosted, useProfile]
  );

  // Initial load
  useEffect(() => {
    executeSearch();
  }, [executeSearch]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch();
  };

  const handleToggleProfile = () => {
    const nextVal = !useProfile;
    setUseProfile(nextVal);
    executeSearch(nextVal);
  };

  const analytics: JobMarketAnalyticsData | null = searchResponse?.analytics || null;
  const jobs: JobMarketListingData[] = searchResponse?.jobs || [];
  const liveAvailable = searchResponse?.live_data_available ?? false;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-3xl p-2 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
              📊
            </span>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Job Market Analyzer
              </h1>
              <p className="text-xs sm:text-sm text-surface-200/70 mt-0.5">
                Real-time external job market intelligence, live skill demand distributions, and verified opportunities.
              </p>
            </div>
          </div>
        </div>

        {/* Profile Enhancement Pill */}
        {profile && (
          <div className="flex items-center gap-3 p-2 rounded-2xl bg-surface-900 border border-white/10 self-start md:self-auto">
            <div className="text-left">
              <span className="text-[10px] font-extrabold text-surface-200/60 uppercase tracking-wider block">
                Profile Integration
              </span>
              <span className="text-xs text-brand-300 font-semibold truncate max-w-[180px] block">
                {profile.target_role || profile.current_role || "Candidate Profile"}
              </span>
            </div>

            <button
              type="button"
              onClick={handleToggleProfile}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                useProfile
                  ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                  : "bg-surface-800 text-surface-200/80 hover:text-white border border-white/10"
              }`}
            >
              {useProfile ? "✓ Using Profile" : "Use My Profile"}
            </button>
          </div>
        )}
      </div>

      {/* Multi-tier Filter Bar */}
      <div className="rounded-2xl bg-surface-900 border border-white/10 p-5 sm:p-6 space-y-4 shadow-xl">
        <form onSubmit={handleSearchSubmit} className="space-y-4">
          {/* Main Search Row */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
            <div className="md:col-span-5 relative">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Job title, technology, or keywords (e.g. Python, React)..."
                className="w-full rounded-xl bg-surface-950 border border-white/10 px-4 py-2.5 text-xs text-white placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500"
              />
            </div>

            <div className="md:col-span-4 relative">
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="City, State, or Country (e.g. New York, Austin)..."
                className="w-full rounded-xl bg-surface-950 border border-white/10 px-4 py-2.5 text-xs text-white placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500"
              />
            </div>

            <div className="md:col-span-3 flex items-center gap-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-md shadow-brand-600/30 flex items-center justify-center gap-2 cursor-pointer"
              >
                {loading ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span>Searching...</span>
                  </>
                ) : (
                  <>
                    <span>🔍</span>
                    <span>Search Market</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Secondary Detailed Filters Row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 pt-2 border-t border-white/5">
            {/* Workplace Type */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-surface-200/60 uppercase tracking-wider block">
                Workplace
              </label>
              <select
                value={workplaceType}
                onChange={(e) => setWorkplaceType(e.target.value)}
                className="w-full rounded-lg bg-surface-950 border border-white/10 p-2 text-xs text-white focus:outline-none focus:border-brand-500"
              >
                <option value="All">All Types</option>
                <option value="Remote">Remote</option>
                <option value="Hybrid">Hybrid</option>
                <option value="On-site">On-site</option>
              </select>
            </div>

            {/* Seniority */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-surface-200/60 uppercase tracking-wider block">
                Experience
              </label>
              <select
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                className="w-full rounded-lg bg-surface-950 border border-white/10 p-2 text-xs text-white focus:outline-none focus:border-brand-500"
              >
                <option value="All">All Levels</option>
                <option value="Entry / Junior">Entry / Junior</option>
                <option value="Mid-Level">Mid-Level</option>
                <option value="Senior">Senior</option>
                <option value="Lead / Principal">Lead / Principal</option>
              </select>
            </div>

            {/* Specific Skills */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-surface-200/60 uppercase tracking-wider block">
                Specific Skills
              </label>
              <input
                type="text"
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
                placeholder="e.g. Docker, SQL"
                className="w-full rounded-lg bg-surface-950 border border-white/10 p-2 text-xs text-white focus:outline-none focus:border-brand-500"
              />
            </div>

            {/* Company */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-surface-200/60 uppercase tracking-wider block">
                Company
              </label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Amazon, Stripe"
                className="w-full rounded-lg bg-surface-950 border border-white/10 p-2 text-xs text-white focus:outline-none focus:border-brand-500"
              />
            </div>

            {/* Job Type */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-surface-200/60 uppercase tracking-wider block">
                Job Type
              </label>
              <select
                value={jobType}
                onChange={(e) => setJobType(e.target.value)}
                className="w-full rounded-lg bg-surface-950 border border-white/10 p-2 text-xs text-white focus:outline-none focus:border-brand-500"
              >
                <option value="All">All Job Types</option>
                <option value="Full-time">Full-time</option>
                <option value="Part-time">Part-time</option>
                <option value="Contract">Contract</option>
              </select>
            </div>

            {/* Date Posted */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-surface-200/60 uppercase tracking-wider block">
                Date Posted
              </label>
              <select
                value={datePosted}
                onChange={(e) => setDatePosted(e.target.value)}
                className="w-full rounded-lg bg-surface-950 border border-white/10 p-2 text-xs text-white focus:outline-none focus:border-brand-500"
              >
                <option value="all">Anytime</option>
                <option value="24h">Past 24 hours</option>
                <option value="7d">Past 7 days</option>
                <option value="30d">Past 30 days</option>
              </select>
            </div>
          </div>
        </form>
      </div>

      {/* Error or Notice Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300 space-y-1">
          <p className="font-bold">Market Search Error</p>
          <p>{error}</p>
        </div>
      )}

      {/* Unconfigured Provider Notice (Real Data Guarantee) */}
      {!liveAvailable && !loading && (
        <div className="p-6 rounded-2xl bg-surface-900 border border-amber-500/30 text-center space-y-3 shadow-lg">
          <div className="w-12 h-12 rounded-full bg-amber-500/10 text-amber-400 mx-auto flex items-center justify-center text-xl font-bold border border-amber-500/30">
            ⚠️
          </div>
          <div className="space-y-1 max-w-lg mx-auto">
            <h3 className="text-sm font-bold text-white">Live Job Data Notice</h3>
            <p className="text-xs text-surface-200/70">
              {searchResponse?.status_message || "Live job data is currently unavailable. Please configure external job provider credentials."}
            </p>
            <p className="text-[11px] text-surface-200/50 pt-2">
              CareerCoachAI strictly displays real-world external job openings and never manufactures fabricated job openings or imaginary statistics.
            </p>
          </div>
        </div>
      )}

      {/* Loading Spinner */}
      {loading && (
        <div className="py-16 text-center space-y-4">
          <LoadingSpinner size="lg" />
          <p className="text-xs text-surface-200/60">Fetching live market records & computing metrics...</p>
        </div>
      )}

      {/* =====================================================================
          JOB MARKET ANALYTICS DASHBOARD (Calculated strictly from real data)
         ===================================================================== */}
      {liveAvailable && !loading && analytics && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>Live Market Intelligence</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Calculated from {analytics.total_matching_jobs} live positions
              </span>
            </h2>
            <span className="text-xs text-surface-200/50">Provider: {searchResponse?.provider_name}</span>
          </div>

          {/* Top High-level Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {/* Total Jobs */}
            <div className="p-4 rounded-2xl bg-surface-900 border border-white/10 text-center space-y-1">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-surface-200/60">
                Total Matching Jobs
              </span>
              <div className="text-3xl font-black text-white">{analytics.total_matching_jobs}</div>
              <span className="text-[10px] text-surface-200/40">Verified open positions</span>
            </div>

            {/* Remote % */}
            <div className="p-4 rounded-2xl bg-surface-900 border border-white/10 text-center space-y-1">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-surface-200/60">
                Remote Distribution
              </span>
              <div className="text-3xl font-black text-brand-400">
                {analytics.workplace_distribution.find((w) => w.name === "Remote")?.percentage ?? 0}%
              </div>
              <span className="text-[10px] text-surface-200/40">Of analyzed positions</span>
            </div>

            {/* Top In-Demand Skill */}
            <div className="p-4 rounded-2xl bg-surface-900 border border-white/10 text-center space-y-1">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-surface-200/60">
                Most In-Demand Skill
              </span>
              <div className="text-xl font-bold text-purple-300 truncate">
                {analytics.top_skills.length > 0 ? analytics.top_skills[0].name : "N/A"}
              </div>
              <span className="text-[10px] text-surface-200/40">
                {analytics.top_skills.length > 0 ? `${analytics.top_skills[0].count} mentions` : "Calculating"}
              </span>
            </div>

            {/* Average Salary (if real data supports it) */}
            <div className="p-4 rounded-2xl bg-surface-900 border border-white/10 text-center space-y-1">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-surface-200/60">
                Market Salary Benchmark
              </span>
              {analytics.salary_summary ? (
                <>
                  <div className="text-xl font-bold text-emerald-400">
                    ${(analytics.salary_summary.avg_salary / 1000).toFixed(0)}k
                  </div>
                  <span className="text-[10px] text-surface-200/40">
                    Avg across {analytics.salary_summary.samples_count} listings
                  </span>
                </>
              ) : (
                <>
                  <div className="text-xs font-medium text-surface-200/50 py-1.5">
                    Not enough live data to calculate this metric.
                  </div>
                  <span className="text-[10px] text-surface-200/30">Salaries omitted by employers</span>
                </>
              )}
            </div>
          </div>

          {/* Visual Breakdown Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 1. Skill Demand */}
            <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center justify-between">
                <span>Top Requested Skills</span>
                <span className="text-[10px] font-normal text-surface-200/50">Frequency</span>
              </h4>

              {analytics.top_skills.length === 0 ? (
                <p className="text-xs text-surface-200/50 italic py-4 text-center">
                  Not enough live data to calculate this metric.
                </p>
              ) : (
                <div className="space-y-2">
                  {analytics.top_skills.slice(0, 7).map((s, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-white">{s.name}</span>
                        <span className="text-surface-200/60 font-mono">
                          {s.count} ({s.percentage}%)
                        </span>
                      </div>
                      <div className="h-1.5 w-full bg-surface-950 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-brand-500 to-indigo-400 rounded-full"
                          style={{ width: `${s.percentage ?? 10}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 2. Top Job Titles */}
            <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center justify-between">
                <span>Common Role Titles</span>
                <span className="text-[10px] font-normal text-surface-200/50">Openings</span>
              </h4>

              {analytics.top_job_titles.length === 0 ? (
                <p className="text-xs text-surface-200/50 italic py-4 text-center">
                  Not enough live data to calculate this metric.
                </p>
              ) : (
                <div className="space-y-2">
                  {analytics.top_job_titles.slice(0, 7).map((t, i) => (
                    <div
                      key={i}
                      className="p-2 rounded-xl bg-surface-950 border border-white/5 flex items-center justify-between text-xs"
                    >
                      <span className="font-medium text-surface-200 truncate pr-2">{t.name}</span>
                      <span className="px-2 py-0.5 rounded bg-surface-800 text-brand-300 font-bold shrink-0">
                        {t.count}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 3. Workplace & Seniority Split */}
            <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-4">
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2">
                  Workplace Breakdown
                </h4>
                <div className="space-y-2">
                  {analytics.workplace_distribution.map((w, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className="text-surface-200/80">{w.name}</span>
                      <span className="font-bold text-white">{w.count} ({w.percentage}%)</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-3 border-t border-white/5">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2">
                  Seniority Distribution
                </h4>
                <div className="space-y-2">
                  {analytics.experience_distribution.map((e, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className="text-surface-200/80">{e.name}</span>
                      <span className="font-bold text-white">{e.count} ({e.percentage}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          REAL JOB OPPORTUNITIES LIST
         ===================================================================== */}
      {liveAvailable && !loading && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white">
              Real Job Opportunities ({jobs.length})
            </h3>
            <span className="text-xs text-surface-200/50">Direct employer & platform postings</span>
          </div>

          {jobs.length === 0 ? (
            <div className="p-10 rounded-2xl bg-surface-900 border border-white/10 text-center space-y-2">
              <p className="text-sm font-bold text-white">No jobs matched your exact filters.</p>
              <p className="text-xs text-surface-200/60">
                Try widening your location or clearing specific skill constraints.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {jobs.map((job, idx) => (
                <div
                  key={job.external_id || idx}
                  className="p-5 rounded-2xl bg-surface-900 border border-white/10 hover:border-brand-500/30 transition-all space-y-3 shadow-sm flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <h4 className="text-sm font-bold text-white hover:text-brand-300 transition-colors line-clamp-1">
                          {job.title}
                        </h4>
                        <p className="text-xs font-medium text-brand-400 mt-0.5">{job.company}</p>
                      </div>

                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase shrink-0 ${
                          job.workplace_type === "Remote"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : job.workplace_type === "Hybrid"
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                            : "bg-surface-800 text-surface-200/70 border border-white/10"
                        }`}
                      >
                        {job.workplace_type}
                      </span>
                    </div>

                    {/* Location & Seniority */}
                    <div className="flex items-center gap-3 text-[11px] text-surface-200/60">
                      <span>📍 {job.location}</span>
                      {job.experience_level && <span>• {job.experience_level}</span>}
                    </div>

                    {/* Description Snippet */}
                    <p className="text-xs text-surface-200/80 line-clamp-3 leading-relaxed">
                      {job.description}
                    </p>

                    {/* Extracted Skill Tags */}
                    {job.extracted_skills.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {job.extracted_skills.slice(0, 5).map((s, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded bg-surface-950 border border-white/5 text-[10px] text-surface-200/70"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Footer Actions */}
                  <div className="pt-4 border-t border-white/5 flex items-center justify-between gap-2 mt-2">
                    {job.salary_min && job.salary_max ? (
                      <span className="text-xs font-bold text-emerald-400">
                        ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}
                      </span>
                    ) : (
                      <span className="text-[11px] text-surface-200/40 italic">Salary not specified</span>
                    )}

                    <div className="flex items-center gap-2">
                      <Link
                        to="/career-intelligence?tab=match"
                        className="px-3 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-[11px] font-semibold text-brand-300 hover:text-white transition-all"
                        title="Evaluate against this job in Career Intelligence"
                      >
                        Match In Intelligence →
                      </Link>

                      <a
                        href={job.redirect_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-[11px] font-bold shadow-sm transition-all"
                      >
                        Apply / View ↗
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
