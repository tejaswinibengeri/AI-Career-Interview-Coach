import { useEffect, useState } from "react";

interface AILoadingStateProps {
  title?: string;
  subtitle?: string;
  steps?: string[];
}

export default function AILoadingState({
  title = "AI Engine Active",
  subtitle = "Synthesizing hyper-personalized career intelligence...",
  steps = [
    "Connecting to Ollama neural pipeline...",
    "Analyzing profile vector data...",
    "Evaluating target occupation benchmarks...",
    "Formulating optimal recommendations...",
  ],
}: AILoadingStateProps) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % steps.length);
    }, 1400);

    return () => clearInterval(interval);
  }, [steps.length]);

  return (
    <div className="relative overflow-hidden rounded-2xl bg-surface-900 border border-brand-500/30 p-8 sm:p-12 text-center space-y-6 shadow-2xl shadow-brand-500/10 animate-fade-in my-6">
      {/* Dynamic Background Mesh Grid & Glow */}
      <div className="absolute inset-0 bg-gradient-to-tr from-brand-600/10 via-purple-600/5 to-transparent pointer-events-none" />
      <div className="absolute -top-24 -left-24 w-48 h-48 bg-brand-500/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-purple-500/20 rounded-full blur-3xl animate-pulse" />

      {/* Pulsating Orb Icon */}
      <div className="relative mx-auto w-20 h-20 flex items-center justify-center">
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-brand-500 to-purple-500 animate-ping opacity-25" />
        <div className="relative w-16 h-16 rounded-full bg-gradient-to-tr from-brand-600 to-purple-600 border border-white/20 shadow-lg shadow-brand-500/40 flex items-center justify-center text-3xl animate-bounce">
          ✨
        </div>
      </div>

      {/* Text Info */}
      <div className="space-y-2 relative z-10 max-w-md mx-auto">
        <h3 className="text-xl font-extrabold text-white tracking-tight flex items-center justify-center gap-2">
          <span>{title}</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        </h3>
        <p className="text-xs text-surface-200/70">{subtitle}</p>
      </div>

      {/* Step Progress Ticker */}
      <div className="relative z-10 max-w-sm mx-auto space-y-3">
        <div className="h-1.5 w-full bg-surface-800 rounded-full overflow-hidden border border-white/5">
          <div className="h-full bg-gradient-to-r from-brand-500 via-purple-500 to-emerald-400 rounded-full animate-pulse w-full transform origin-left transition-all duration-700" />
        </div>

        <div className="min-h-[24px] text-xs font-mono text-brand-300 font-semibold flex items-center justify-center gap-2 bg-surface-800/80 px-3 py-1.5 rounded-xl border border-brand-500/20 shadow-inner">
          <span className="animate-spin text-brand-400 text-sm">⚡</span>
          <span>{steps[currentStep]}</span>
        </div>
      </div>
    </div>
  );
}
