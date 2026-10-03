import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api, { APIError } from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState(() => searchParams.get("token") || "");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!token.trim()) {
      setError("Password reset token is required.");
      return;
    }

    if (newPassword.length < 6) {
      setError("New password must be at least 6 characters.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post("/api/v1/auth/reset-password", {
        token: token.trim(),
        new_password: newPassword,
      });

      setSuccess(true);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to reset password. The token may be expired or invalid.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-16rem)] flex items-center justify-center px-4 py-12 sm:px-6 lg:px-8 animate-fade-in">
      <div className="w-full max-w-md">
        <div className="relative">
          <div className="absolute -inset-1 bg-gradient-to-r from-brand-600 to-indigo-500 rounded-3xl blur-xl opacity-20 pointer-events-none" />

          <div className="relative glass rounded-2xl border border-white/10 p-8 sm:p-10 shadow-2xl bg-surface-900/80 backdrop-blur-xl">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20 mb-4 shadow-inner">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
                Set new password
              </h1>
              <p className="text-sm text-surface-200/70 mt-2">
                Enter your reset token and your desired new password
              </p>
            </div>

            {/* Error Banner */}
            {error && (
              <div className="mb-6 rounded-xl bg-red-500/10 border border-red-500/20 p-4 flex items-start gap-3 text-red-400 text-sm animate-fade-in">
                <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            {/* Success Screen */}
            {success ? (
              <div className="space-y-6 text-center animate-fade-in">
                <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-6 text-center">
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 mb-3">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                    </svg>
                  </div>
                  <h3 className="text-base font-semibold text-white mb-1">
                    Password Reset Successful!
                  </h3>
                  <p className="text-sm text-surface-200/70">
                    Your password has been securely updated. You can now sign in with your new credentials.
                  </p>
                </div>

                <Link
                  to="/login"
                  id="reset-login-link"
                  className="block w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white text-sm font-semibold shadow-lg shadow-brand-600/30 transition-all text-center cursor-pointer"
                >
                  Sign In Now
                </Link>
              </div>
            ) : (
              /* Form */
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label
                    htmlFor="reset-token"
                    className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-1.5"
                  >
                    Reset Token
                  </label>
                  <input
                    id="reset-token"
                    type="text"
                    required
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="Paste your reset token here"
                    className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 font-mono focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                  />
                </div>

                <div>
                  <label
                    htmlFor="reset-new-password"
                    className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-1.5"
                  >
                    New Password
                  </label>
                  <input
                    id="reset-new-password"
                    type="password"
                    required
                    autoComplete="new-password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Min. 6 characters"
                    className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                  />
                </div>

                <div>
                  <label
                    htmlFor="reset-confirm-password"
                    className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-1.5"
                  >
                    Confirm New Password
                  </label>
                  <input
                    id="reset-confirm-password"
                    type="password"
                    required
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter new password"
                    className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                  />
                </div>

                <button
                  type="submit"
                  id="reset-submit-btn"
                  disabled={isSubmitting}
                  className="w-full py-3.5 px-4 mt-2 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white text-sm font-semibold shadow-lg shadow-brand-600/30 hover:shadow-brand-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer"
                >
                  {isSubmitting ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span>Updating password...</span>
                    </>
                  ) : (
                    <span>Update Password</span>
                  )}
                </button>

                <div className="pt-4 border-t border-white/5 text-center">
                  <Link
                    to="/login"
                    className="text-sm text-surface-200/70 hover:text-white transition-colors"
                  >
                    Cancel and Return to Sign In
                  </Link>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
