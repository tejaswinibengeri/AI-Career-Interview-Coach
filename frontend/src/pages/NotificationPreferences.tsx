import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { APIError, type NotificationPreferenceData } from "../lib/api";

export default function NotificationPreferences() {
  const [pref, setPref] = useState<NotificationPreferenceData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getNotificationPreferences();
      if (res.data) {
        setPref(res.data);
      } else {
        setError("Failed to load notification preferences.");
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

  const handleToggle = (key: keyof NotificationPreferenceData) => {
    if (!pref) return;
    setPref({
      ...pref,
      [key]: !pref[key],
    });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pref) return;

    setSaving(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await api.updateNotificationPreferences({
        enable_roadmap_reminders: pref.enable_roadmap_reminders,
        enable_interview_reminders: pref.enable_interview_reminders,
        enable_coding_reminders: pref.enable_coding_reminders,
        enable_resume_suggestions: pref.enable_resume_suggestions,
        enable_learning_milestones: pref.enable_learning_milestones,
      });

      if (res.data) {
        setPref(res.data);
        setSuccessMsg("Notification preferences updated successfully!");
        setTimeout(() => setSuccessMsg(null), 4000);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to update preferences.");
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 space-y-6 animate-pulse">
        <div className="h-10 w-48 bg-surface-800 rounded-xl" />
        <div className="h-64 bg-surface-900 rounded-2xl border border-white/5" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      <div className="flex items-center gap-3">
        <Link
          to="/notifications"
          className="p-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white transition-colors cursor-pointer"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
        </Link>
        <div>
          <h1 className="text-2xl font-extrabold text-white">Notification Preferences</h1>
          <p className="text-xs text-surface-200/70">Customize which real-state notifications you receive</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm font-semibold">
          ✓ {successMsg}
        </div>
      )}

      <form onSubmit={handleSave} className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl">
        <div className="space-y-4 divide-y divide-white/5">
          {[
            {
              key: "enable_roadmap_reminders" as keyof NotificationPreferenceData,
              title: "Career Roadmap Reminders",
              description: "Receive progress alerts and next-topic prompts for active learning roadmaps.",
              icon: "🗺️",
            },
            {
              key: "enable_interview_reminders" as keyof NotificationPreferenceData,
              title: "Mock Interview Practice",
              description: "Receive practice reminders to maintain and improve interview readiness scores.",
              icon: "🎙️",
            },
            {
              key: "enable_coding_reminders" as keyof NotificationPreferenceData,
              title: "Coding Practice Reminders",
              description: "Receive reminders to solve interactive Python, SQL, and DSA coding challenges.",
              icon: "💻",
            },
            {
              key: "enable_resume_suggestions" as keyof NotificationPreferenceData,
              title: "Resume ATS Suggestions",
              description: "Get alerted when your resume score falls below 75 or missing keywords are detected.",
              icon: "📄",
            },
            {
              key: "enable_learning_milestones" as keyof NotificationPreferenceData,
              title: "Skill Gap Learning Milestones",
              description: "Get notified when verified learning resources are matched to candidate skill gaps.",
              icon: "📚",
            },
          ].map((item, idx) => (
            <div key={item.key} className={`flex items-center justify-between pt-4 ${idx === 0 ? "pt-0" : ""}`}>
              <div className="flex items-start gap-4 pr-4">
                <div className="w-10 h-10 rounded-2xl bg-surface-800 border border-white/10 flex items-center justify-center text-xl shrink-0 mt-0.5">
                  {item.icon}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">{item.title}</h3>
                  <p className="text-xs text-surface-200/70 leading-relaxed">{item.description}</p>
                </div>
              </div>

              {/* Toggle Switch */}
              <button
                type="button"
                onClick={() => handleToggle(item.key)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  pref?.[item.key] ? "bg-brand-600" : "bg-surface-800"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    pref?.[item.key] ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>

        <div className="pt-4 border-t border-white/10 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-bold text-sm shadow-xl shadow-brand-600/30 transition-all cursor-pointer disabled:opacity-50"
          >
            {saving ? "Saving Preferences..." : "Save Preferences"}
          </button>
        </div>
      </form>
    </div>
  );
}
