import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import api, { APIError, type ForgotPasswordData } from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resetData, setResetData] = useState<ForgotPasswordData | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await api.post<ForgotPasswordData>(
        "/api/v1/auth/forgot-password",
        { email: email.trim() }
      );

      if (response.data) {
        setResetData(response.data);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to initiate password reset. Please try again.");
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
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
                Reset your password
              </h1>
              <p className="text-sm text-surface-200/70 mt-2">
                Enter your account email to receive a password reset token
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

            {/* Success View */}
            {resetData ? (
              <div className="space-y-6 animate-fade-in text-center">
                <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 text-left">
                  <h3 className="text-sm font-semibold text-emerald-400 mb-1 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                    </svg>
                    Reset token generated!
                  </h3>
                  <p className="text-xs text-surface-200/80 mb-3">
                    A password reset token was generated for <span className="text-white font-medium">{resetData.email}</span>.
                  </p>

                  {resetData.reset_token && (
                    <div className="bg-surface-950/80 p-3 rounded-lg border border-white/5 space-y-2">
                      <span className="text-[11px] text-surface-200/50 uppercase font-mono block">Reset Token:</span>
                      <code className="text-xs text-brand-300 break-all select-all font-mono block">
                        {resetData.reset_token}
                      </code>
                    </div>
                  )}
                </div>

                <Link
                  to={`/reset-password?token=${encodeURIComponent(resetData.reset_token || "")}`}
                  className="block w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white text-sm font-semibold shadow-lg shadow-brand-600/30 transition-all text-center"
                >
                  Proceed to Reset Password
                </Link>

                <div className="pt-2">
                  <Link
                    to="/login"
                    className="text-sm text-surface-200/70 hover:text-white transition-colors"
                  >
                    Back to Sign In
                  </Link>
                </div>
              </div>
            ) : (
              /* Form */
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label
                    htmlFor="forgot-email"
                    className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2"
                  >
                    Account Email
                  </label>
                  <input
                    id="forgot-email"
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-3 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                  />
                </div>

                <button
                  type="submit"
                  id="forgot-submit-btn"
                  disabled={isSubmitting}
                  className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white text-sm font-semibold shadow-lg shadow-brand-600/30 hover:shadow-brand-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer"
                >
                  {isSubmitting ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span>Sending instructions...</span>
                    </>
                  ) : (
                    <span>Generate Reset Token</span>
                  )}
                </button>

                <div className="pt-4 border-t border-white/5 text-center">
                  <Link
                    to="/login"
                    className="text-sm text-surface-200/70 hover:text-white transition-colors flex items-center justify-center gap-1.5"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
                    </svg>
                    Back to Sign In
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
