/**
 * Premium loading spinner with pulsing brand gradient.
 */
export default function LoadingSpinner({ size = "md", label }: { size?: "sm" | "md" | "lg"; label?: string }) {
  const sizes = {
    sm: "h-5 w-5 border-2",
    md: "h-8 w-8 border-[3px]",
    lg: "h-12 w-12 border-4",
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3" role="status" aria-label={label ?? "Loading"}>
      <div
        className={`${sizes[size]} rounded-full border-brand-400/30 border-t-brand-400 animate-spin`}
      />
      {label && (
        <span className="text-sm text-surface-200/60 animate-pulse-soft">{label}</span>
      )}
    </div>
  );
}
