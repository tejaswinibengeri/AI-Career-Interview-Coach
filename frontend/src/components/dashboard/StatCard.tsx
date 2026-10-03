import React from "react";
import { Link } from "react-router-dom";

interface StatCardProps {
  title: string;
  icon: React.ReactNode;
  badgeText?: string;
  badgeType?: "success" | "warning" | "neutral" | "brand";
  isEmpty: boolean;
  emptyStateText: string;
  actionText?: string;
  actionLink?: string;
  children?: React.ReactNode;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  icon,
  badgeText,
  badgeType = "neutral",
  isEmpty,
  emptyStateText,
  actionText,
  actionLink,
  children,
}) => {
  const badgeStyles = {
    success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    neutral: "bg-surface-700/50 text-surface-300 border-white/10",
    brand: "bg-brand-500/10 text-brand-300 border-brand-500/30",
  };

  return (
    <div className="flex flex-col justify-between rounded-xl bg-surface-900/70 border border-white/10 p-5 shadow-md hover:border-white/20 transition-all duration-200 group">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-surface-800 border border-white/5 text-brand-400 group-hover:text-brand-300 transition-colors">
              {icon}
            </div>
            <h3 className="text-base font-semibold text-white tracking-tight">{title}</h3>
          </div>
          {badgeText && (
            <span
              className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${badgeStyles[badgeType]}`}
            >
              {badgeText}
            </span>
          )}
        </div>

        {/* Content Body */}
        {isEmpty ? (
          <div className="py-6 px-4 rounded-lg bg-surface-800/40 border border-dashed border-white/10 text-center space-y-2">
            <svg
              className="w-8 h-8 mx-auto text-surface-200/30"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m6 4.5h3m-6 3h6m-9-9h18"
              />
            </svg>
            <p className="text-xs text-surface-200/60 font-medium">{emptyStateText}</p>
          </div>
        ) : (
          <div className="space-y-3">{children}</div>
        )}
      </div>

      {/* Action Footer if provided */}
      {actionText && actionLink && (
        <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-end">
          <Link
            to={actionLink}
            className="text-xs font-semibold text-brand-400 hover:text-brand-300 flex items-center gap-1 transition-colors"
          >
            {actionText}
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </div>
      )}
    </div>
  );
};
