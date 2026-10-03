import { Link } from "react-router-dom";
import type { ProfileSummary } from "../../lib/api";

interface WelcomeBannerProps {
  welcomeMessage: string;
  profile: ProfileSummary;
  careerGoal?: string | null;
}

export const WelcomeBanner: React.FC<WelcomeBannerProps> = ({
  welcomeMessage,
  profile,
  careerGoal,
}) => {
  const completionPercentage = profile.completion_percentage;

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-900/80 via-surface-800 to-surface-900 border border-brand-500/20 p-6 md:p-8 shadow-xl">
      {/* Background ambient lighting */}
      <div className="absolute -top-24 -right-24 h-64 w-64 rounded-full bg-brand-500/10 blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 h-64 w-64 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />

      <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div className="space-y-3 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/30 text-xs font-semibold text-brand-300">
            <span className="h-2 w-2 rounded-full bg-brand-400 animate-pulse" />
            Dashboard Overview
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
            {welcomeMessage}
          </h1>
          <p className="text-sm sm:text-base text-surface-200/80 leading-relaxed">
            {careerGoal ? (
              <span className="italic">"{careerGoal}"</span>
            ) : (
              <span className="text-surface-200/60 italic">
                No career goal set yet. Visit your profile to set target roles and aspirations.
              </span>
            )}
          </p>
        </div>

        {/* Profile Completion Card Widget */}
        <div className="shrink-0 w-full lg:w-80 rounded-xl bg-surface-900/60 backdrop-blur-sm border border-white/10 p-4 space-y-3">
          <div className="flex items-center justify-between text-xs font-medium">
            <span className="text-surface-200/80">Profile Completion</span>
            <span className="font-bold text-brand-300">{completionPercentage}%</span>
          </div>

          {/* Progress bar */}
          <div className="h-2.5 w-full rounded-full bg-surface-800 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-brand-500 to-emerald-400 transition-all duration-500"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>

          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] text-surface-200/60">
              {completionPercentage === 100
                ? "Profile fully configured!"
                : "Complete profile for better matches"}
            </span>
            <Link
              to="/profile"
              className="text-xs font-semibold text-brand-400 hover:text-brand-300 hover:underline flex items-center gap-1 transition-colors"
            >
              Edit Profile
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
