import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import api, { APIError, type AuthResponseData } from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validations
    if (!name.trim() || !email.trim() || !password) {
      setError("Please fill in all required fields.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await api.post<AuthResponseData>("/api/v1/auth/register", {
        name: name.trim(),
        email: email.trim(),
        password,
      });

      if (response.data) {
        login(response.data);
        navigate("/profile", { replace: true });
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Registration failed. Please try again.");
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
          <div className="absolute -inset-1 bg-gradient-to-r from-brand-500 to-indigo-600 rounded-3xl blur-xl opacity-20 pointer-events-none" />

          {/* Card Container */}
          <div className="relative glass rounded-2xl border border-white/10 p-8 sm:p-10 shadow-2xl bg-surface-900/80 backdrop-blur-xl">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20 mb-4 shadow-inner">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM3 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 9.374 21c-2.331 0-4.512-.645-6.374-1.765Z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
                Create an account
              </h1>
              <p className="text-sm text-surface-200/70 mt-2">
                Join CareerCoach AI and elevate your career preparation
              </p>
            </div>

            {/* Error Banner */}
            {error && (
              <div
                id="register-error-banner"
                className="mb-6 rounded-xl bg-red-500/10 border border-red-500/20 p-4 flex items-start gap-3 text-red-400 text-sm animate-fade-in"
              >
                <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="register-name"
                  className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-1.5"
                >
                  Full Name
                </label>
                <input
                  id="register-name"
                  type="text"
                  required
                  autoComplete="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Alex Mercer"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <div>
                <label
                  htmlFor="register-email"
                  className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-1.5"
                >
                  Email Address
                </label>
                <input
                  id="register-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="alex@example.com"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <div>
                <label
                  htmlFor="register-password"
                  className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-1.5"
                >
                  Password
                </label>
                <input
                  id="register-password"
                  type="password"
                  required
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min. 6 characters"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <div>
                <label
                  htmlFor="register-confirm-password"
                  className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-1.5"
                >
                  Confirm Password
                </label>
                <input
                  id="register-confirm-password"
                  type="password"
                  required
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <button
                type="submit"
                id="register-submit-btn"
                disabled={isSubmitting}
                className="w-full py-3.5 px-4 mt-2 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white text-sm font-semibold shadow-lg shadow-brand-600/30 hover:shadow-brand-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span>Creating account...</span>
                  </>
                ) : (
                  <span>Create Account</span>
                )}
              </button>
            </form>

            {/* Footer */}
            <div className="mt-8 pt-6 border-t border-white/5 text-center">
              <p className="text-sm text-surface-200/60">
                Already have an account?{" "}
                <Link
                  to="/login"
                  className="font-medium text-brand-400 hover:text-brand-300 transition-colors"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
