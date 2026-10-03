import { useEffect, useState } from "react";
import api, { type HealthData } from "../lib/api";

interface HealthState {
  loading: boolean;
  data: HealthData | null;
  error: string | null;
}

/**
 * Hook to check backend health status.
 * Polls on mount and optionally at a given interval.
 */
export function useHealthCheck(intervalMs: number = 0): HealthState {
  const [state, setState] = useState<HealthState>({
    loading: true,
    data: null,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        setState((prev) => ({ ...prev, loading: true, error: null }));
        const response = await api.get<HealthData>("/api/v1/health");
        if (!cancelled) {
          setState({ loading: false, data: response.data ?? null, error: null });
        }
      } catch (err) {
        if (!cancelled) {
          setState({
            loading: false,
            data: null,
            error: err instanceof Error ? err.message : "Health check failed",
          });
        }
      }
    }

    check();

    let timer: ReturnType<typeof setInterval> | undefined;
    if (intervalMs > 0) {
      timer = setInterval(check, intervalMs);
    }

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [intervalMs]);

  return state;
}
