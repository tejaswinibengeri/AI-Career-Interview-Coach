import type { ActivityItem } from "../../lib/api";

interface RecentActivityListProps {
  activities: ActivityItem[];
}

export const RecentActivityList: React.FC<RecentActivityListProps> = ({ activities }) => {
  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "account_created":
        return (
          <div className="p-1.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM3 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 019.374 21c-2.331 0-4.512-.645-6.374-1.766z" />
            </svg>
          </div>
        );
      case "profile_updated":
        return (
          <div className="p-1.5 rounded-full bg-brand-500/20 text-brand-400 border border-brand-500/30">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="p-1.5 rounded-full bg-surface-700 text-surface-300 border border-white/10">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
    }
  };

  return (
    <div className="rounded-xl bg-surface-900/70 border border-white/10 p-5 shadow-md space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
          <svg className="w-4 h-4 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Recent Activity
        </h3>
        <span className="text-xs text-surface-200/60 font-medium">Real-time log</span>
      </div>

      {activities.length === 0 ? (
        <p className="text-xs text-surface-200/60 italic py-4 text-center">No recent activity logged.</p>
      ) : (
        <div className="space-y-3 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-white/5">
          {activities.map((act) => (
            <div key={act.id} className="relative flex items-start gap-3 pl-1 group">
              <div className="shrink-0 relative z-10">{getActivityIcon(act.activity_type)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-white truncate">{act.title}</p>
                  <span className="text-[10px] text-surface-200/50 shrink-0">
                    {formatDate(act.timestamp)}
                  </span>
                </div>
                <p className="text-xs text-surface-200/70 truncate">{act.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
