import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import api, { APIError, type AuthResponseData } from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || "/dashboard";

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError("Please fill in all required fields.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await api.post<AuthResponseData>("/api/v1/auth/login", {
        email: email.trim(),
        password,
      });

      if (response.data) {
        login(response.data);
        const isAdmin = response.data.user?.role === "admin" || response.data.user?.is_superuser;
        const destination = from !== "/dashboard" ? from : (isAdmin ? "/admin" : "/dashboard");
        navigate(destination, { replace: true });
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-16rem)] flex items-center justify-center px-4 py-12 sm:px-6 lg:px-8 animate-fade-in">
      <div className="w-full max-w-md">
        {/* Glow backdrop decoration */}
        <div className="relative">
          <div className="absolute -inset-1 bg-gradient-to-r from-brand-600 to-brand-400 rounded-3xl blur-xl opacity-20 pointer-events-none" />

          {/* Card Container */}
          <div className="relative glass rounded-2xl border border-white/10 p-8 sm:p-10 shadow-2xl bg-surface-900/80 backdrop-blur-xl">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20 mb-4 shadow-inner">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
                Welcome back
              </h1>
              <p className="text-sm text-surface-200/70 mt-2">
                Sign in to your CareerCoach AI account
              </p>
            </div>

            {/* Error Banner */}
            {error && (
              <div
                id="login-error-banner"
                className="mb-6 rounded-xl bg-red-500/10 border border-red-500/20 p-4 flex items-start gap-3 text-red-400 text-sm animate-fade-in"
              >
                <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            {/* Quick Demo Credentials */}
            <div className="mb-6 p-3.5 rounded-xl bg-surface-800/60 border border-brand-500/20 text-xs">
              <p className="text-surface-200/70 font-medium mb-2.5 flex items-center justify-between">
                <span>⚡ Quick Demo Logins:</span>
                <span className="text-[10px] text-brand-400 font-mono">1-Click Fill</span>
              </p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  id="btn-demo-candidate"
                  onClick={() => {
                    setEmail("demo@example.com");
                    setPassword("Password123!");
                  }}
                  className="px-2.5 py-1.5 rounded-lg bg-brand-500/15 hover:bg-brand-500/25 border border-brand-500/30 text-brand-300 font-medium text-center transition-all cursor-pointer"
                >
                  Candidate Demo
                </button>
                <button
                  type="button"
                  id="btn-demo-admin"
                  onClick={() => {
                    setEmail("admin@example.com");
                    setPassword("AdminPassword123!");
                  }}
                  className="px-2.5 py-1.5 rounded-lg bg-purple-500/15 hover:bg-purple-500/25 border border-purple-500/30 text-purple-300 font-medium text-center transition-all cursor-pointer"
                >
                  Admin Demo
                </button>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label
                  htmlFor="login-email"
                  className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2"
                >
                  Email Address
                </label>
                <div className="relative">
                  <input
                    id="login-email"
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-3 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label
                    htmlFor="login-password"
                    className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80"
                  >
                    Password
                  </label>
                  <Link
                    to="/forgot-password"
                    className="text-xs font-medium text-brand-400 hover:text-brand-300 transition-colors"
                  >
                    Forgot password?
                  </Link>
                </div>
                <input
                  id="login-password"
                  type="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-3 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <button
                type="submit"
                id="login-submit-btn"
                disabled={isSubmitting}
                className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white text-sm font-semibold shadow-lg shadow-brand-600/30 hover:shadow-brand-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer mt-2"
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <span>Sign In</span>
                )}
              </button>
            </form>

            {/* Footer */}
            <div className="mt-8 pt-6 border-t border-white/5 text-center">
              <p className="text-sm text-surface-200/60">
                Don't have an account?{" "}
                <Link
                  to="/register"
                  className="font-medium text-brand-400 hover:text-brand-300 transition-colors"
                >
                  Create one now
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
