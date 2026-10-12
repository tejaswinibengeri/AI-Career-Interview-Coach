import { useEffect, useState } from "react";
import api, { APIError, type AdminSettingsData } from "../../lib/api";

export default function AdminSettings() {
  const [settings, setSettings] = useState<AdminSettingsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminSettings();
      if (res.data) {
        setSettings(res.data);
      } else {
        setError("Failed to load settings.");
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

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">Platform Settings & Operational Parameters</h2>
          <p className="text-xs text-surface-200/60">
            System configuration, LLM parameters, database engine settings, and security controls.
          </p>
        </div>
        <button
          onClick={fetchSettings}
          disabled={loading}
          className="px-3.5 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs text-surface-200 hover:text-white font-semibold transition-colors cursor-pointer"
        >
          ↻ Refresh Settings
        </button>
      </div>

      {loading ? (
        <div className="p-8 text-center text-xs text-surface-200/60">Loading platform configuration...</div>
      ) : error || !settings ? (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex justify-between items-center">
          <span>{error || "Failed to load platform settings."}</span>
          <button onClick={fetchSettings} className="underline font-bold">Retry</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* AI Inference Engine Configuration */}
          <div className="rounded-2xl p-6 border bg-surface-900/60 border-white/10 space-y-4 shadow-xl">
            <div className="flex items-center gap-2 text-white font-bold text-sm">
              <span className="text-brand-400">🤖</span>
              <span>AI Engine & LLM Configuration</span>
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-surface-200/70">Inference Engine</span>
                <span className="font-mono text-emerald-400 font-semibold">Ollama Local</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-surface-200/70">Active LLM Model</span>
                <span className="font-mono text-brand-300 font-bold">{settings.ollama_model}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-surface-200/70">Ollama API Host</span>
                <span className="font-mono text-surface-200">{settings.ollama_base_url}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-surface-200/70">Privacy Protocol</span>
                <span className="font-mono text-emerald-400 font-semibold">100% Offline / Local</span>
              </div>
            </div>
          </div>

          {/* Security & Authentication */}
          <div className="rounded-2xl p-6 border bg-surface-900/60 border-white/10 space-y-4 shadow-xl">
            <div className="flex items-center gap-2 text-white font-bold text-sm">
              <span className="text-amber-400">🛡️</span>
              <span>Security & Access Governance</span>
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-surface-200/70">JWT Token Expiry</span>
                <span className="font-mono text-white font-bold">{settings.jwt_expiration_minutes} minutes</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-surface-200/70">User Registrations</span>
                <span className="font-mono text-emerald-400 font-semibold">
                  {settings.registration_enabled ? "Open (Public)" : "Restricted"}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-surface-200/70">Password Encryption</span>
                <span className="font-mono text-white">bcrypt (12 rounds)</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-surface-200/70">App Environment</span>
                <span className="font-mono text-brand-300 uppercase">{settings.environment}</span>
              </div>
            </div>
          </div>

          {/* Database & Storage */}
          <div className="rounded-2xl p-6 border bg-surface-900/60 border-white/10 space-y-4 shadow-xl md:col-span-2">
            <div className="flex items-center gap-2 text-white font-bold text-sm">
              <span className="text-blue-400">🗄️</span>
              <span>Storage & Database Connection</span>
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-surface-200/70">Database URL (Masked)</span>
                <span className="font-mono text-surface-200 font-bold">{settings.database_url_masked}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-surface-200/70">Application Release</span>
                <span className="font-mono text-white">{settings.app_name} v{settings.app_version}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
