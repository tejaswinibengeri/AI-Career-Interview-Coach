import { useEffect, useState } from "react";
import api, { APIError, type DashboardData } from "../lib/api";
import { WelcomeBanner } from "../components/dashboard/WelcomeBanner";
import { StatCard } from "../components/dashboard/StatCard";
import { RecentActivityList } from "../components/dashboard/RecentActivityList";

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<DashboardData>("/api/v1/dashboard");
      if (response.data) {
        setData(response.data);
      } else {
        setError("Failed to load dashboard data.");
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Unable to connect to the server. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-pulse">
        {/* Banner Skeleton */}
        <div className="h-48 rounded-2xl bg-surface-800/60 border border-white/5" />

        {/* Cards Skeleton Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-44 rounded-xl bg-surface-800/40 border border-white/5 p-5 space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-700/50" />
                <div className="h-4 w-32 bg-surface-700/50 rounded" />
              </div>
              <div className="h-12 bg-surface-700/30 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="max-w-md mx-auto rounded-2xl bg-surface-900 border border-red-500/30 p-6 text-center space-y-4 shadow-xl">
          <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-400 mx-auto flex items-center justify-center">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-white">Error Loading Dashboard</h2>
          <p className="text-xs text-surface-200/70">{error || "An unexpected error occurred."}</p>
          <button
            onClick={fetchDashboard}
            className="px-4 py-2 rounded-lg text-xs font-semibold text-white bg-brand-600 hover:bg-brand-500 transition-colors shadow-md shadow-brand-600/30 cursor-pointer"
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  const { profile, resume, skills, interviews, coding, placement_readiness, recent_activity } = data;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* 1. Welcome Banner */}
      <WelcomeBanner
        welcomeMessage={data.welcome_message}
        profile={profile}
        careerGoal={data.career_goal}
      />

      {/* 2. Primary Metrics & Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <StatCard
          title="Career Profile"
          badgeText={`${profile.completion_percentage}% Complete`}
          badgeType={profile.completion_percentage === 100 ? "success" : "brand"}
          isEmpty={false}
          emptyStateText=""
          actionText="Edit Profile"
          actionLink="/profile"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          }
        >
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-white/5">
              <span className="text-surface-200/60">Target Role</span>
              <span className="font-semibold text-white truncate max-w-[160px]">
                {profile.target_role || "Not specified"}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/5">
              <span className="text-surface-200/60">Current Status</span>
              <span className="font-medium text-surface-200 truncate max-w-[160px]">
                {profile.current_role || "Not specified"}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/5">
              <span className="text-surface-200/60">Education</span>
              <span className="font-medium text-surface-200 truncate max-w-[160px]">
                {profile.degree || profile.education || "Not specified"}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-surface-200/60">Work Preference</span>
              <span className="font-medium text-surface-200">
                {profile.work_preference || "Not specified"}
              </span>
            </div>
          </div>
        </StatCard>

        {/* Skills Card */}
        <StatCard
          title="Skills Inventory"
          badgeText={`${skills.total_skills} Skills`}
          badgeType={skills.total_skills > 0 ? "brand" : "neutral"}
          isEmpty={skills.total_skills === 0}
          emptyStateText="No skills added yet. Update your profile to showcase technical expertise."
          actionText="Manage Skills"
          actionLink="/profile"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l5.654-4.654m0 0l3.03-2.496c.384-.317.626-.74.766-1.208m-4.562 1.95L3 4.5l3-3 7.653 7.653" />
            </svg>
          }
        >
          <div className="flex flex-wrap gap-1.5 pt-1">
            {skills.skills.map((skill, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded-md bg-brand-500/10 border border-brand-500/20 text-brand-300 text-[11px] font-medium"
              >
                {skill}
              </span>
            ))}
          </div>
        </StatCard>

        {/* Resume Status Card (Explicit Empty State) */}
        <StatCard
          title="Resume Analysis"
          badgeText={resume.has_resume ? "Analyzed" : "No Resume"}
          badgeType={resume.has_resume ? "success" : "neutral"}
          isEmpty={!resume.has_resume}
          emptyStateText="No resume analyzed yet."
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5A3.375 3.375 0 0010.125 2.25H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          }
        />

        {/* ATS Score Card (Explicit Empty State) */}
        <StatCard
          title="Latest ATS Score"
          badgeText={resume.latest_ats_score !== null ? `${resume.latest_ats_score}%` : "Pending"}
          badgeType={resume.latest_ats_score !== null ? "success" : "neutral"}
          isEmpty={resume.latest_ats_score === null}
          emptyStateText="No ATS score available yet."
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
          }
        />

        {/* Mock Interview Stats Card (Explicit Empty State) */}
        <StatCard
          title="Mock Interviews"
          badgeText={`${interviews.total_mock_interviews} Taken`}
          badgeType={interviews.total_mock_interviews > 0 ? "success" : "neutral"}
          isEmpty={interviews.total_mock_interviews === 0}
          emptyStateText="No mock interviews taken yet."
          actionText="Start Practice"
          actionLink="/interview"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 003-3V4.5a3 3 0 10-6 0v8.25a3 3 0 003 3z" />
            </svg>
          }
        />


        {/* Coding Statistics Card (Explicit Empty State) */}
        <StatCard
          title="Coding Practice"
          badgeText={`${coding.total_problems_solved} Solved`}
          badgeType={coding.total_problems_solved > 0 ? "success" : "neutral"}
          isEmpty={coding.total_problems_solved === 0}
          emptyStateText="No coding problems solved yet."
          actionText="Solve Problems"
          actionLink="/coding"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
            </svg>
          }
        />


        {/* Placement Readiness Card (Explicit Empty State) */}
        <StatCard
          title="Placement Readiness"
          badgeText={placement_readiness.readiness_score !== null && placement_readiness.readiness_score !== undefined ? `${placement_readiness.readiness_score}%` : (placement_readiness.level || "Not Evaluated")}
          badgeType={placement_readiness.readiness_score !== null ? "success" : "neutral"}
          isEmpty={placement_readiness.readiness_score === null}
          emptyStateText="No placement assessment completed yet."
          actionText="View Analytics"
          actionLink="/performance"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
            </svg>
          }
        />

      </div>

      {/* 3. Recent Activity Section */}
      <div className="max-w-3xl">
        <RecentActivityList activities={recent_activity} />
      </div>
    </div>
  );
}
