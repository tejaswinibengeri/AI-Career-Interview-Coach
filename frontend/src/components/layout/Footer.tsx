/**
 * Site footer with branding.
 */
export default function Footer() {
  return (
    <footer className="border-t border-white/5 mt-auto">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-surface-200/50">
            &copy; {new Date().getFullYear()} CareerCoach
            <span className="text-brand-400">AI</span>. All rights reserved.
          </p>
          <p className="text-xs text-surface-200/30">
            AI-powered career coaching &amp; interview preparation
          </p>
        </div>
      </div>
    </footer>
  );
}
