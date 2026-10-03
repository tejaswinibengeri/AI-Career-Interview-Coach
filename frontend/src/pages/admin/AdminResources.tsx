import { useEffect, useState } from "react";
import api, { APIError, type LearningResourceData } from "../../lib/api";

export default function AdminResources() {
  const [resources, setResources] = useState<LearningResourceData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [showForm, setShowForm] = useState<boolean>(false);
  const [title, setTitle] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [url, setUrl] = useState<string>("");
  const [skillName, setSkillName] = useState<string>("");
  const [category, setCategory] = useState<string>("Official Doc");
  const [difficulty, setDifficulty] = useState<string>("Intermediate");
  const [resourceType, setResourceType] = useState<string>("Course");
  const [submitting, setSubmitting] = useState<boolean>(false);

  useEffect(() => {
    fetchResources();
  }, []);

  const fetchResources = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminResources();
      if (res.data) {
        setResources(res.data);
      } else {
        setError("Failed to load learning resources.");
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

  const handleCreateResource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !url.trim() || !skillName.trim()) return;

    setSubmitting(true);
    try {
      const res = await api.createAdminResource({
        title: title.trim(),
        description: description.trim(),
        url: url.trim(),
        skill_name: skillName.trim(),
        category,
        difficulty,
        resource_type: resourceType,
      });

      if (res.data) {
        setResources([res.data, ...resources]);
        setShowForm(false);
        setTitle("");
        setDescription("");
        setUrl("");
        setSkillName("");
      }
    } catch {
      // Ignore error
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteResource = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this resource?")) return;
    try {
      await api.deleteAdminResource(id);
      setResources(resources.filter((r) => r.id !== id));
    } catch {
      // Ignore error
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Verified Learning Resources Catalog</h2>
          <p className="text-xs text-surface-200/60">Manage accredited documentation, YouTube courses, and official provider URLs</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition-colors cursor-pointer"
        >
          {showForm ? "Cancel" : "+ Add Resource"}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Resource Form */}
      {showForm && (
        <form onSubmit={handleCreateResource} className="bg-surface-900 border border-white/10 rounded-2xl p-6 space-y-4 shadow-2xl animate-fade-in">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">New Verified Resource</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-surface-200 mb-1">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-200 mb-1">Target Skill Name</label>
              <input
                type="text"
                value={skillName}
                onChange={(e) => setSkillName(e.target.value)}
                placeholder="e.g. Python, FastAPI, React"
                className="w-full p-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-200 mb-1">Verified URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://..."
              className="w-full p-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs font-mono"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-surface-200 mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs"
              >
                <option value="Official Doc">Official Doc</option>
                <option value="YouTube">YouTube</option>
                <option value="freeCodeCamp">freeCodeCamp</option>
                <option value="Coursera">Coursera</option>
                <option value="edX">edX</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-200 mb-1">Resource Type</label>
              <select
                value={resourceType}
                onChange={(e) => setResourceType(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs"
              >
                <option value="Course">Course</option>
                <option value="Documentation">Documentation</option>
                <option value="Video">Video</option>
                <option value="Certification">Certification</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-200 mb-1">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-surface-800 border border-white/10 text-white text-xs"
              >
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-200 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full p-3 rounded-xl bg-surface-800 border border-white/10 text-white text-xs"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={submitting || !title.trim() || !url.trim()}
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition-colors cursor-pointer disabled:opacity-50"
            >
              {submitting ? "Saving..." : "Save Verified Resource"}
            </button>
          </div>
        </form>
      )}

      {/* Resources List */}
      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-surface-900 rounded-2xl border border-white/5" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {resources.map((r) => (
            <div
              key={r.id}
              className="bg-surface-900 border border-white/10 rounded-2xl p-5 space-y-2 shadow-xl flex items-start justify-between gap-4"
            >
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-300 text-[10px] font-bold">
                    {r.skill_name}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-surface-800 border border-white/10 text-surface-200 text-[10px] font-medium">
                    {r.resource_type}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 text-[10px] font-bold">
                    ✓ Verified
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white">{r.title}</h3>
                <p className="text-xs text-surface-200/70">{r.description}</p>
                <a
                  href={r.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[11px] font-mono text-brand-300 hover:underline block truncate"
                >
                  {r.url}
                </a>
              </div>

              <button
                onClick={() => handleDeleteResource(r.id)}
                className="p-2 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500/20 text-xs font-bold transition-colors cursor-pointer"
                title="Delete Resource"
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
