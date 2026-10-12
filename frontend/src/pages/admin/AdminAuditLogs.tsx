import { useEffect, useState } from "react";
import api, { APIError, type AdminAuditLogData } from "../../lib/api";

export default function AdminAuditLogs() {
  const [logs, setLogs] = useState<AdminAuditLogData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>("ALL");

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminAuditLogs();
      if (res.data) {
        setLogs(res.data);
      } else {
        setError("Failed to load audit logs.");
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Unable to connect to server.");
      }
    } finally {
      setLoading(false);
    }
  };

  const getEventBadge = (type: string) => {
    switch (type) {
      case "USER_REGISTERED":
        return "bg-blue-500/15 border-blue-500/30 text-blue-300";
      case "INTERVIEW_SESSION":
        return "bg-amber-500/15 border-amber-500/30 text-amber-300";
      case "CODING_SUBMISSION":
        return "bg-emerald-500/15 border-emerald-500/30 text-emerald-300";
      default:
        return "bg-purple-500/15 border-purple-500/30 text-purple-300";
    }
  };

  const filteredLogs = filterType === "ALL" ? logs : logs.filter((l) => l.event_type === filterType);

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">System Security & Audit Activity Logs</h2>
          <p className="text-xs text-surface-200/60">
            Real chronological event timeline of user registrations, evaluations, and administrative activity.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-surface-900 border border-white/10 text-xs text-white focus:outline-none focus:border-brand-500"
          >
            <option value="ALL">All Event Types</option>
            <option value="USER_REGISTERED">User Registrations</option>
            <option value="INTERVIEW_SESSION">Interview Sessions</option>
            <option value="CODING_SUBMISSION">Coding Submissions</option>
          </select>
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs text-surface-200 hover:text-white font-semibold transition-colors cursor-pointer"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-xs text-surface-200/60">Loading audit trail...</div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex justify-between items-center">
          <span>{error}</span>
          <button onClick={fetchLogs} className="underline font-bold">Retry</button>
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="p-8 text-center rounded-2xl bg-surface-900/40 border border-white/5 text-xs text-surface-200/60">
          No audit activity found matching this filter.
        </div>
      ) : (
        <div className="rounded-2xl border border-white/10 overflow-hidden bg-surface-900/60 shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-800/80 text-surface-200/80 border-b border-white/10 uppercase tracking-wider font-semibold text-[10px]">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Event Type</th>
                  <th className="py-3 px-4">Activity Description</th>
                  <th className="py-3 px-4">Actor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredLogs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 font-mono text-surface-200/70 whitespace-nowrap">
                      {formatDate(log.timestamp)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded-full border text-[10px] font-bold ${getEventBadge(log.event_type)}`}>
                        {log.event_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-white font-medium">
                      {log.description}
                    </td>
                    <td className="py-3 px-4 text-surface-200/70 font-mono text-[11px] whitespace-nowrap">
                      {log.actor}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
