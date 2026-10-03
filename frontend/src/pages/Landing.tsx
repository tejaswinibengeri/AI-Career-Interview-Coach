import { useHealthCheck } from "../hooks/useHealthCheck";
import LoadingSpinner from "../components/ui/LoadingSpinner";

/**
 * Landing page — premium hero section with feature highlights and live status.
 */
export default function Landing() {
  const health = useHealthCheck(30000); // refresh every 30s

  const features = [
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 0 1-.825-.242m9.345-8.334a2.126 2.126 0 0 0-.476-.095 48.64 48.64 0 0 0-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0 0 11.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
        </svg>
      ),
      title: "Mock Interviews",
      description: "Practice with AI-powered interview simulations tailored to your target role and industry.",
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
        </svg>
      ),
      title: "Resume Analysis",
      description: "Get intelligent feedback on your resume with actionable suggestions for improvement.",
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
        </svg>
      ),
      title: "Career Roadmap",
      description: "Build a personalized career development plan with milestones and skill tracking.",
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5" />
        </svg>
      ),
      title: "Skill Assessment",
      description: "Evaluate your technical and soft skills with AI-driven assessments and feedback.",
    },
  ];

  return (
    <div className="relative overflow-hidden">
      {/* Gradient background orbs */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full bg-brand-600/10 blur-[120px]" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-brand-400/8 blur-[100px]" />
      </div>

      {/* ============================================================
          Hero Section
          ============================================================ */}
      <section className="relative px-4 sm:px-6 lg:px-8 pt-20 pb-24 sm:pt-28 sm:pb-32">
        <div className="mx-auto max-w-4xl text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-medium text-brand-300 mb-8 animate-fade-in">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-brand-400"></span>
            </span>
            AI-Powered Career Platform
          </div>

          {/* Heading */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.1] mb-6 animate-slide-up">
            Your AI Partner for{" "}
            <span className="gradient-text">Career Success</span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-surface-200/60 max-w-2xl mx-auto mb-10 animate-slide-up" style={{ animationDelay: "0.1s" }}>
            Prepare for interviews, optimize your resume, and chart your career
            path — all powered by intelligent AI coaching.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up" style={{ animationDelay: "0.2s" }}>
            <button className="btn-primary text-base px-8 py-3.5" id="cta-get-started">
              Get Started
            </button>
            <button className="btn-secondary text-base px-8 py-3.5" id="cta-learn-more">
              Learn More
            </button>
          </div>
        </div>
      </section>

      {/* ============================================================
          Feature Grid
          ============================================================ */}
      <section className="px-4 sm:px-6 lg:px-8 pb-20">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-14">
            <h2 className="text-2xl sm:text-3xl font-bold mb-3">
              Everything you need to <span className="gradient-text">land your dream job</span>
            </h2>
            <p className="text-surface-200/50 max-w-xl mx-auto">
              A comprehensive suite of AI-powered tools designed to accelerate your career growth.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {features.map((feat, i) => (
              <div
                key={feat.title}
                className="glass glow rounded-2xl p-6 group hover:border-brand-400/30 transition-all duration-300 hover:-translate-y-1 animate-slide-up"
                style={{ animationDelay: `${0.1 * (i + 1)}s` }}
              >
                <div className="h-11 w-11 rounded-xl bg-brand-600/15 flex items-center justify-center text-brand-400 mb-4 group-hover:bg-brand-600/25 transition-colors">
                  {feat.icon}
                </div>
                <h3 className="font-semibold text-white mb-2">{feat.title}</h3>
                <p className="text-sm text-surface-200/50 leading-relaxed">{feat.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================
          System Status
          ============================================================ */}
      <section className="px-4 sm:px-6 lg:px-8 pb-20">
        <div className="mx-auto max-w-2xl">
          <div className="glass glow rounded-2xl p-6">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
              </svg>
              System Status
            </h3>

            {health.loading ? (
              <div className="py-4">
                <LoadingSpinner size="sm" label="Checking services..." />
              </div>
            ) : health.error ? (
              <div className="flex items-center gap-3 text-sm">
                <StatusDot color="red" />
                <span className="text-red-400">Backend unreachable</span>
                <span className="text-surface-200/40 ml-auto text-xs">{health.error}</span>
              </div>
            ) : (
              <div className="space-y-3">
                <StatusRow label="API Server" status="connected" version={health.data?.version} />
                <StatusRow label="Database" status={health.data?.database ?? "unavailable"} />
                <StatusRow label="AI Engine (Ollama)" status={health.data?.ollama ?? "unavailable"} />
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Helper Sub-components                                              */
/* ------------------------------------------------------------------ */

function StatusDot({ color }: { color: "green" | "yellow" | "red" }) {
  const colors = {
    green: "bg-emerald-400",
    yellow: "bg-amber-400",
    red: "bg-red-400",
  };
  return (
    <span className="relative flex h-2.5 w-2.5">
      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${colors[color]} opacity-75`} />
      <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${colors[color]}`} />
    </span>
  );
}

function StatusRow({ label, status, version }: { label: string; status: string; version?: string }) {
  const dotColor = status === "connected" ? "green" : "red";
  return (
    <div className="flex items-center gap-3 text-sm">
      <StatusDot color={dotColor} />
      <span className="text-surface-200/80">{label}</span>
      <span className={`ml-auto text-xs font-medium ${status === "connected" ? "text-emerald-400" : "text-surface-200/40"}`}>
        {status}
      </span>
      {version && <span className="text-xs text-surface-200/30">v{version}</span>}
    </div>
  );
}
