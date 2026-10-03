import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { APIError, type NotificationListData } from "../lib/api";


type FilterTab = "All" | "Unread" | "Read";

export default function NotificationsCenter() {
  const navigate = useNavigate();
  const [data, setData] = useState<NotificationListData | null>(null);
  const [activeTab, setActiveTab] = useState<FilterTab>("All");

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getNotifications();
      if (res.data) {
        setData(res.data);
      } else {
        setError("Failed to load notifications.");
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

  const handleMarkAsRead = async (id: number) => {
    try {
      const res = await api.readNotification(id);
      if (res.data && data) {
        setData({
          unread_count: Math.max(0, data.unread_count - 1),
          notifications: data.notifications.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
        });
      }
    } catch {
      // Ignore error
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.readAllNotifications();
      if (data) {
        setData({
          unread_count: 0,
          notifications: data.notifications.map((n) => ({ ...n, is_read: true })),
        });
      }
    } catch {
      // Ignore error
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteNotification(id);
      if (data) {
        const target = data.notifications.find((n) => n.id === id);
        const unreadDelta = target && !target.is_read ? 1 : 0;
        setData({
          unread_count: Math.max(0, data.unread_count - unreadDelta),
          notifications: data.notifications.filter((n) => n.id !== id),
        });
      }
    } catch {
      // Ignore error
    }
  };

  const formatDate = (isoString: string) => {
    try {
      return new Date(isoString).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "roadmap_reminder":
        return "🗺️";
      case "interview_reminder":
        return "🎙️";
      case "coding_reminder":
        return "💻";
      case "resume_suggestion":
        return "📄";
      case "learning_milestone":
        return "📚";
      default:
        return "🔔";
    }
  };

  const filteredList = data?.notifications.filter((n) => {
    if (activeTab === "Unread") return !n.is_read;
    if (activeTab === "Read") return n.is_read;
    return true;
  }) || [];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-950 via-surface-900 to-indigo-950/60 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold">
              Module 19 • In-App Notifications Center
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Notifications & Activity Alerts
            </h1>
            <p className="text-sm text-surface-200/80 max-w-2xl leading-relaxed">
              Real application state notifications corresponding to your roadmap, mock interview schedules, coding practice, and ATS resume improvements.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            {data && data.unread_count > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors cursor-pointer"
              >
                ✓ Mark All Read
              </button>
            )}
            <Link
              to="/notifications/preferences"
              className="px-4 py-2.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-white font-semibold text-xs transition-colors cursor-pointer"
            >
              ⚙️ Preferences
            </Link>
          </div>
        </div>

        {data && (
          <div className="flex items-center gap-4 pt-2 text-xs border-t border-white/5">
            <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
              Unread Alerts: <span className="font-bold text-red-400">{data.unread_count}</span>
            </div>
            <div className="px-3.5 py-1.5 rounded-xl bg-surface-800/80 border border-white/10 font-medium text-surface-200">
              Total Notifications: <span className="font-bold text-white">{data.notifications.length}</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => fetchNotifications()} className="text-xs font-bold text-red-400 hover:text-red-200 cursor-pointer">
            Retry
          </button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-4 sm:p-5 flex items-center justify-between shadow-xl">
        <div className="flex items-center gap-2">
          {(["All", "Unread", "Read"] as FilterTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === tab
                  ? "bg-brand-600 text-white shadow-md shadow-brand-600/20"
                  : "bg-surface-800 text-surface-200/70 hover:bg-surface-700 hover:text-white"
              }`}
            >
              {tab} {tab === "Unread" && data?.unread_count ? `(${data.unread_count})` : ""}
            </button>
          ))}
        </div>
      </div>

      {/* Notifications List */}
      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-2xl bg-surface-900 border border-white/5 p-5" />
          ))}
        </div>
      ) : filteredList.length === 0 ? (
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-surface-800 text-surface-200/40 mx-auto flex items-center justify-center text-xl">
            🔔
          </div>
          <h3 className="text-base font-bold text-white">No Notifications</h3>
          <p className="text-xs text-surface-200/60 max-w-sm mx-auto">
            You're all caught up! No notifications match the selected view.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredList.map((n) => (
            <div
              key={n.id}
              className={`rounded-2xl p-5 border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl ${
                !n.is_read
                  ? "bg-surface-900 border-brand-500/30 shadow-brand-500/5"
                  : "bg-surface-900/60 border-white/10 opacity-80 hover:opacity-100"
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-2xl bg-surface-800 border border-white/10 flex items-center justify-center text-xl shrink-0">
                  {getNotificationIcon(n.type)}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-bold text-white">{n.title}</h3>
                    {!n.is_read && (
                      <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" title="Unread" />
                    )}
                  </div>
                  <p className="text-xs text-surface-200/80 leading-relaxed">{n.message}</p>
                  <span className="text-[10px] text-surface-200/50 block pt-0.5">{formatDate(n.created_at)}</span>
                </div>
              </div>

              {/* Action Controls */}
              <div className="flex items-center gap-2 self-end sm:self-center">
                {n.link_url && (
                  <button
                    onClick={() => {
                      if (!n.is_read) handleMarkAsRead(n.id);
                      navigate(n.link_url!);
                    }}
                    className="px-3.5 py-1.5 rounded-xl bg-brand-600/20 hover:bg-brand-600/40 text-brand-300 hover:text-white border border-brand-500/30 text-xs font-bold transition-all cursor-pointer whitespace-nowrap"
                  >
                    Open Action ↗
                  </button>
                )}

                {!n.is_read && (
                  <button
                    onClick={() => handleMarkAsRead(n.id)}
                    className="p-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200/70 hover:text-white border border-white/10 text-xs cursor-pointer"
                    title="Mark as Read"
                  >
                    ✓ Read
                  </button>
                )}

                <button
                  onClick={() => handleDelete(n.id)}
                  className="p-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 text-xs cursor-pointer"
                  title="Delete Notification"
                >
                  &times;
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
