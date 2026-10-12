import { Link, Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

export default function AdminLayout() {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();

  const isAdmin = user?.role === "admin" || user?.is_superuser;

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!isAdmin) {
    return (
      <div className="max-w-md mx-auto px-4 py-20 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-400 mx-auto flex items-center justify-center text-xl">
          🔒
        </div>
        <h2 className="text-xl font-bold text-white">Access Denied</h2>
        <p className="text-xs text-surface-200/70">
          You do not have administrative privileges to access the Admin Panel. Backend authorization is strictly enforced.
        </p>
        <Link
          to="/dashboard"
          className="inline-block px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors cursor-pointer"
        >
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const tabs = [
    { to: "/admin/statistics", label: "📊 System Statistics" },
    { to: "/admin/users", label: "👥 Manage Users" },
    { to: "/admin/questions", label: "❓ Question Bank" },
    { to: "/admin/resources", label: "📚 Learning Catalog" },
    { to: "/admin/health", label: "🖥️ System Health" },
    { to: "/admin/audit", label: "🛡️ Audit Logs" },
    { to: "/admin/settings", label: "⚙️ Platform Settings" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Admin Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-950 via-surface-900 to-red-950/40 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-300 text-xs font-semibold">
              Module 20 • Platform Administration & Governance
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Admin Control Center
            </h1>
            <p className="text-sm text-surface-200/80 max-w-2xl leading-relaxed">
              Real system telemetry, user role authorization, question bank moderation, and verified learning catalog management.
            </p>
          </div>

          <div className="px-3.5 py-2 rounded-xl bg-surface-800/80 border border-white/10 text-xs text-emerald-400 font-bold self-start sm:self-auto flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Admin Session Active ({user?.email})</span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 pt-2 overflow-x-auto border-t border-white/5">
          {tabs.map((t) => {
            const isActive = location.pathname === t.to || (t.to === "/admin/statistics" && location.pathname === "/admin");
            return (
              <Link
                key={t.to}
                to={t.to}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                  isActive
                    ? "bg-brand-600 text-white shadow-md shadow-brand-600/20"
                    : "bg-surface-800 text-surface-200/70 hover:bg-surface-700 hover:text-white"
                }`}
              >
                {t.label}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Main Outlet Container */}
      <Outlet />
    </div>
  );
}
