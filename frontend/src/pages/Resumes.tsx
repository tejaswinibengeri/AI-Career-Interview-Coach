import { useEffect, useState, useRef, type ChangeEvent, type DragEvent } from "react";
import { Link } from "react-router-dom";
import api, {
  APIError,
  type ResumeData,
  type ResumeVersionComparisonData,
  type ResumeVersionHistoryData,
} from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

export default function Resumes() {
  const [resumes, setResumes] = useState<ResumeData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Upload state
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [selectedResumeIdForNewVersion, setSelectedResumeIdForNewVersion] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Text preview modal state
  const [previewText, setPreviewText] = useState<{ title: string; text: string } | null>(null);

  // Expanded version history toggles & loaded data
  const [expandedResumeIds, setExpandedResumeIds] = useState<number[]>([]);
  const [historyDataMap, setHistoryDataMap] = useState<Record<number, ResumeVersionHistoryData>>({});

  // Version Comparison modal state
  const [comparisonModal, setComparisonModal] = useState<{
    resumeId: number;
    v1Id: number;
    v2Id: number;
    data: ResumeVersionComparisonData | null;
    loading: boolean;
  } | null>(null);

  const fetchResumes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<ResumeData[]>("/api/v1/resumes");
      if (response.data) {
        setResumes(response.data);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to fetch resumes.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const fetchVersionHistory = async (resumeId: number) => {
    try {
      const res = await api.getResumeVersionHistory(resumeId);
      if (res.data) {
        setHistoryDataMap((prev) => ({ ...prev, [resumeId]: res.data! }));
      }
    } catch {
      // Ignore version history fetch error
    }
  };

  const toggleExpandHistory = async (resumeId: number) => {
    if (expandedResumeIds.includes(resumeId)) {
      setExpandedResumeIds((prev) => prev.filter((id) => id !== resumeId));
    } else {
      setExpandedResumeIds((prev) => [...prev, resumeId]);
      if (!historyDataMap[resumeId]) {
        await fetchVersionHistory(resumeId);
      }
    }
  };

  const handleCompareVersions = async (resumeId: number, v1Id: number, v2Id: number) => {
    setComparisonModal({ resumeId, v1Id, v2Id, data: null, loading: true });
    try {
      const res = await api.compareResumeVersions(resumeId, v1Id, v2Id);
      if (res.data) {
        setComparisonModal({ resumeId, v1Id, v2Id, data: res.data, loading: false });
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to compare versions.");
      }
      setComparisonModal(null);
    }
  };

  const handleDeleteVersion = async (resumeId: number, versionId: number, versionNum: number) => {
    if (!window.confirm(`Are you sure you want to delete version v${versionNum}?`)) {
      return;
    }

    setError(null);
    setSuccess(null);
    try {
      await api.deleteResumeVersion(resumeId, versionId);
      setSuccess(`Version v${versionNum} deleted successfully.`);
      await fetchResumes();
      await fetchVersionHistory(resumeId);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to delete version.");
      }
    }
  };

  const handleFileSelect = async (file: File) => {
    setError(null);
    setSuccess(null);

    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "docx") {
      setError("Only PDF and DOCX files are supported.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("File size exceeds 10MB limit.");
      return;
    }

    setIsUploading(true);
    try {
      const targetId = selectedResumeIdForNewVersion ?? undefined;
      const res = await api.uploadResume(file, targetId);

      if (res.data) {
        setSuccess(
          targetId
            ? `Successfully uploaded version v${res.data.current_version?.version_number} of '${res.data.title}'!`
            : `Successfully uploaded '${res.data.title}'!`
        );
        setSelectedResumeIdForNewVersion(null);
        await fetchResumes();
        if (targetId) {
          await fetchVersionHistory(targetId);
        }
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to upload resume.");
      }
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const onFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDownload = async (resumeId: number, versionId?: number, fallbackName?: string) => {
    try {
      const { blob, filename } = await api.downloadResumeBlob(resumeId, versionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || fallbackName || "resume";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to download file.");
      }
    }
  };

  const handleDelete = async (resumeId: number, title: string) => {
    if (!window.confirm(`Are you sure you want to delete '${title}'? All uploaded versions will be permanently removed.`)) {
      return;
    }

    setError(null);
    setSuccess(null);
    try {
      await api.delete<null>(`/api/v1/resumes/${resumeId}`);
      setSuccess(`Resume '${title}' deleted successfully.`);
      await fetchResumes();
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to delete resume.");
      }
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatDate = (isoString: string) => {
    try {
      return new Date(isoString).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Resume Management & Version History
          </h1>
          <p className="text-sm text-surface-200/70 mt-1">
            Track resume versions, ATS score improvement trajectories, extracted skills, and side-by-side version comparison.
          </p>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-4 flex items-start gap-3 text-red-400 text-sm animate-fade-in">
          <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <div className="flex-1">{error}</div>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300 cursor-pointer">
            &times;
          </button>
        </div>
      )}

      {success && (
        <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 flex items-start gap-3 text-emerald-400 text-sm animate-fade-in">
          <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="flex-1">{success}</div>
          <button onClick={() => setSuccess(null)} className="text-emerald-400 hover:text-emerald-300 cursor-pointer">
            &times;
          </button>
        </div>
      )}

      {/* File Upload Box */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        className={`relative overflow-hidden rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-200 ${
          isDragOver
            ? "border-brand-400 bg-brand-500/10 shadow-lg shadow-brand-500/20"
            : "border-white/15 bg-surface-900/60 hover:border-brand-500/50 hover:bg-surface-800/40"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={onFileInputChange}
          className="hidden"
          id="resume-file-input"
        />

        <div className="space-y-4 max-w-md mx-auto">
          <div className="w-14 h-14 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 mx-auto flex items-center justify-center shadow-inner">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
            </svg>
          </div>

          <div>
            <h3 className="text-base font-semibold text-white">
              {selectedResumeIdForNewVersion
                ? "Upload New Version to Resume"
                : "Upload Resume Document"}
            </h3>
            <p className="text-xs text-surface-200/60 mt-1">
              Drag and drop your PDF or DOCX file here (max 10MB)
            </p>
          </div>

          {selectedResumeIdForNewVersion && (
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
              <span>Uploading new version for Resume #{selectedResumeIdForNewVersion}</span>
              <button
                type="button"
                onClick={() => setSelectedResumeIdForNewVersion(null)}
                className="font-bold hover:text-white cursor-pointer"
              >
                Cancel
              </button>
            </div>
          )}

          <div>
            <button
              type="button"
              id="btn-trigger-upload"
              disabled={isUploading}
              onClick={() => fileInputRef.current?.click()}
              className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 hover:shadow-brand-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 inline-flex items-center gap-2 cursor-pointer"
            >
              {isUploading ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>Processing & Extracting Text...</span>
                </>
              ) : (
                <span>Select Resume File</span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Resumes List */}
      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-32 rounded-xl bg-surface-800/40 border border-white/5 p-6" />
          ))}
        </div>
      ) : resumes.length === 0 ? (
        <div className="rounded-2xl bg-surface-900/60 border border-dashed border-white/10 p-12 text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-surface-800 text-surface-200/40 mx-auto flex items-center justify-center">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5A3.375 3.375 0 0010.125 2.25H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">Upload your resume to start your career analysis.</h3>
            <p className="text-xs text-surface-200/60">
              Once uploaded, every version is independently tracked with ATS score evolution over time.
            </p>
          </div>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/30 transition-all cursor-pointer inline-flex items-center gap-2"
          >
            Upload Resume Now
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">Your Resumes ({resumes.length})</h2>
          </div>

          <div className="space-y-4">
            {resumes.map((resume) => {
              const cur = resume.current_version;
              const isExpanded = expandedResumeIds.includes(resume.id);
              const history = historyDataMap[resume.id];

              return (
                <div
                  key={resume.id}
                  className="rounded-2xl bg-surface-900/80 border border-white/10 p-6 space-y-4 shadow-md hover:border-white/20 transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    {/* Title & Metadata */}
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-xl bg-surface-800 border border-white/10 text-brand-400 shrink-0">
                        {cur?.file_type === "pdf" ? (
                          <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5A3.375 3.375 0 0010.125 2.25H8.25m2.25 0h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                          </svg>
                        ) : (
                          <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5A3.375 3.375 0 0010.125 2.25H8.25m.75 12 3 3m0 0 3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                          </svg>
                        )}
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-base font-bold text-white">{cur?.filename || resume.title}</h3>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-brand-500/10 border border-brand-500/30 text-brand-300 uppercase">
                            {cur?.file_type || "File"}
                          </span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                            v{cur?.version_number || 1} Current
                          </span>
                        </div>

                        <div className="flex items-center gap-4 text-xs text-surface-200/60">
                          <span>Uploaded: {cur ? formatDate(cur.created_at) : formatDate(resume.created_at)}</span>
                          <span>•</span>
                          <span>Size: {cur ? formatBytes(cur.file_size) : "N/A"}</span>
                          <span>•</span>
                          <span>{resume.versions.length} Total Version{resume.versions.length > 1 ? "s" : ""}</span>
                        </div>
                      </div>
                    </div>

                    {/* Controls */}
                    <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
                      <Link
                        to={`/resume-analysis/${resume.id}`}
                        className="px-3.5 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-xs font-semibold text-white shadow-md shadow-brand-600/30 transition-all flex items-center gap-1.5"
                      >
                        ⚡ AI Analysis
                      </Link>

                      <button
                        type="button"
                        onClick={() => {
                          setSelectedResumeIdForNewVersion(resume.id);
                          fileInputRef.current?.click();
                        }}
                        className="px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs font-semibold text-surface-200 hover:text-white transition-all cursor-pointer"
                      >
                        + New Version
                      </button>

                      <button
                        type="button"
                        onClick={() => handleDownload(resume.id, cur?.id, cur?.filename)}
                        className="px-3 py-1.5 rounded-lg bg-brand-600/20 hover:bg-brand-600/30 border border-brand-500/30 text-xs font-semibold text-brand-300 hover:text-white transition-all cursor-pointer"
                      >
                        Download
                      </button>

                      <button
                        type="button"
                        onClick={() => handleDelete(resume.id, cur?.filename || resume.title)}
                        className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-xs font-semibold text-red-400 hover:text-red-300 transition-all cursor-pointer"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  {/* Version History Trigger */}
                  <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs">
                    <button
                      type="button"
                      onClick={() => toggleExpandHistory(resume.id)}
                      className="text-brand-400 hover:text-brand-300 font-semibold flex items-center gap-1 cursor-pointer"
                    >
                      <span>{isExpanded ? "Hide Version History & Score Progression" : "View Version History & Score Progression"}</span>
                      <svg
                        className={`w-3.5 h-3.5 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                      </svg>
                    </button>
                  </div>

                  {/* Version History & Trajectory Drawer */}
                  {isExpanded && (
                    <div className="pt-3 space-y-4 border-t border-white/5 animate-fade-in">
                      {/* Real Score Trajectory Line */}
                      {history && history.versions.some((v) => v.ats_score !== null) && (
                        <div className="p-4 rounded-xl bg-surface-950/80 border border-white/10 space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-white uppercase tracking-wider">ATS Score Evolution Over Time</span>
                            {history.score_improvement !== undefined && history.score_improvement !== null && (
                              <span
                                className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                                  history.score_improvement >= 0
                                    ? "bg-emerald-500/20 text-emerald-400"
                                    : "bg-red-500/20 text-red-400"
                                }`}
                              >
                                {history.score_improvement >= 0 ? `+${history.score_improvement}` : history.score_improvement} pts improvement
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-3 overflow-x-auto py-2">
                            {history.versions
                              .slice()
                              .reverse()
                              .map((v, idx, arr) => (
                                <div key={v.id} className="flex items-center gap-2 shrink-0">
                                  <div className="px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-center">
                                    <div className="text-[10px] text-surface-200/50 font-semibold">v{v.version_number}</div>
                                    <div className={`text-sm font-extrabold ${v.ats_score !== undefined && v.ats_score !== null ? (v.ats_score >= 75 ? "text-emerald-400" : v.ats_score >= 60 ? "text-amber-400" : "text-red-400") : "text-surface-200/40"}`}>
                                      {v.ats_score !== undefined && v.ats_score !== null ? `${v.ats_score}` : "Not Analyzed"}
                                    </div>
                                  </div>

                                  {idx < arr.length - 1 && (
                                    <span className="text-surface-200/40 font-bold text-sm">→</span>
                                  )}
                                </div>
                              ))}
                          </div>
                        </div>
                      )}

                      {/* Versions List Table */}
                      <div className="space-y-2">
                        <h4 className="text-xs font-bold text-surface-200/80 uppercase tracking-wider">Tracked Versions ({resume.versions.length})</h4>
                        {history ? (
                          history.versions.map((ver) => (
                            <div
                              key={ver.id}
                              className="p-4 rounded-xl bg-surface-800/60 border border-white/5 space-y-3 text-xs"
                            >
                              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                <div className="flex items-center gap-3">
                                  <span className={`px-2.5 py-0.5 rounded font-bold ${ver.is_current ? "bg-emerald-500/20 text-emerald-400" : "bg-surface-700 text-surface-300"}`}>
                                    v{ver.version_number} {ver.is_current ? "(Current)" : ""}
                                  </span>
                                  <span className="text-white font-bold">{ver.filename}</span>
                                  <span className="text-surface-200/50">({formatBytes(ver.file_size)})</span>
                                </div>

                                <div className="flex items-center gap-2">
                                  <span className="text-surface-200/50 text-[11px]">{formatDate(ver.created_at)}</span>
                                  <button
                                    type="button"
                                    onClick={() => handleDownload(resume.id, ver.id, ver.filename)}
                                    className="px-2.5 py-1 rounded bg-brand-600/20 hover:bg-brand-600/40 text-brand-300 text-[11px] font-semibold cursor-pointer"
                                  >
                                    Download
                                  </button>
                                  {history.versions.length > 1 && (
                                    <button
                                      type="button"
                                      onClick={() => handleDeleteVersion(resume.id, ver.id, ver.version_number)}
                                      className="px-2.5 py-1 rounded bg-red-500/10 hover:bg-red-500/30 text-red-400 text-[11px] font-semibold cursor-pointer"
                                    >
                                      Delete Version
                                    </button>
                                  )}
                                </div>
                              </div>

                              {/* Skills & ATS info */}
                              <div className="flex flex-wrap gap-4 pt-1 border-t border-white/5 text-[11px]">
                                <div>
                                  <span className="text-surface-200/50 font-semibold">ATS Score: </span>
                                  <strong className={ver.ats_score ? "text-emerald-400 font-bold" : "text-surface-200/40"}>
                                    {ver.ats_score ? `${ver.ats_score} / 100` : "Not evaluated yet"}
                                  </strong>
                                </div>

                                {ver.skills && ver.skills.length > 0 && (
                                  <div>
                                    <span className="text-surface-200/50 font-semibold">Extracted Skills: </span>
                                    <span className="text-surface-200">{ver.skills.slice(0, 5).join(", ")}{ver.skills.length > 5 ? "..." : ""}</span>
                                  </div>
                                )}
                              </div>

                              {/* Compare buttons if multiple versions exist */}
                              {history.versions.length >= 2 && (
                                <div className="pt-1 flex justify-end">
                                  {history.versions
                                    .filter((v) => v.id !== ver.id)
                                    .map((otherVer) => (
                                      <button
                                        key={otherVer.id}
                                        onClick={() => handleCompareVersions(resume.id, otherVer.id, ver.id)}
                                        className="text-[10px] text-cyan-400 hover:text-cyan-300 font-bold ml-2 underline cursor-pointer"
                                      >
                                        Compare v{otherVer.version_number} vs v{ver.version_number} ⇄
                                      </button>
                                    ))}
                                </div>
                              )}
                            </div>
                          ))
                        ) : (
                          <div className="text-xs text-surface-200/40 italic p-2">Loading version history...</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Version Comparison Modal */}
      {comparisonModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-3xl rounded-2xl bg-surface-900 border border-white/10 p-6 shadow-2xl space-y-5 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>Side-by-Side Version Comparison</span>
              </h3>
              <button
                onClick={() => setComparisonModal(null)}
                className="p-1 rounded-lg text-surface-200/60 hover:text-white hover:bg-white/10 cursor-pointer"
              >
                &times;
              </button>
            </div>

            {comparisonModal.loading ? (
              <div className="py-12 text-center text-xs text-surface-200/60 space-y-2">
                <LoadingSpinner size="md" />
                <p>Analyzing side-by-side version differences...</p>
              </div>
            ) : comparisonModal.data ? (
              <div className="flex-1 overflow-y-auto space-y-5 pr-1">
                {/* Score Delta Highlight */}
                <div className="p-4 rounded-xl bg-surface-950 border border-white/10 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-surface-200/60 font-semibold uppercase tracking-wider block">ATS Score Change</span>
                    <div className="text-sm font-bold text-white mt-0.5">
                      Version v{comparisonModal.data.v1_version_number} ({comparisonModal.data.v1_ats_score ?? "N/A"}) → Version v{comparisonModal.data.v2_version_number} ({comparisonModal.data.v2_ats_score ?? "N/A"})
                    </div>
                  </div>

                  {comparisonModal.data.ats_score_delta !== undefined && comparisonModal.data.ats_score_delta !== null && (
                    <div
                      className={`text-lg font-extrabold px-3.5 py-1.5 rounded-xl border ${
                        comparisonModal.data.ats_score_delta >= 0
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                          : "bg-red-500/20 text-red-400 border-red-500/30"
                      }`}
                    >
                      {comparisonModal.data.ats_score_delta >= 0 ? `+${comparisonModal.data.ats_score_delta}` : comparisonModal.data.ats_score_delta} pts
                    </div>
                  )}

                </div>

                {/* Added & Removed Skills */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-2">
                    <h4 className="font-bold text-emerald-400">Newly Added Skills ({comparisonModal.data.added_skills.length})</h4>
                    {comparisonModal.data.added_skills.length === 0 ? (
                      <p className="text-surface-200/50 italic">No new skills added.</p>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {comparisonModal.data.added_skills.map((s, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-medium">
                            + {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 space-y-2">
                    <h4 className="font-bold text-amber-400">Fixed / Resolved Keywords ({comparisonModal.data.resolved_missing_keywords.length})</h4>
                    {comparisonModal.data.resolved_missing_keywords.length === 0 ? (
                      <p className="text-surface-200/50 italic">No missing keywords resolved.</p>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {comparisonModal.data.resolved_missing_keywords.map((k, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-medium">
                            ✓ {k}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : null}

            <div className="flex justify-end pt-2 border-t border-white/10">
              <button
                onClick={() => setComparisonModal(null)}
                className="px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-xs font-semibold text-white transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Text Preview Modal */}
      {previewText && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-2xl rounded-2xl bg-surface-900 border border-white/10 p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <h3 className="text-base font-bold text-white truncate max-w-md">
                Extracted Text — {previewText.title}
              </h3>
              <button
                onClick={() => setPreviewText(null)}
                className="p-1 rounded-lg text-surface-200/60 hover:text-white hover:bg-white/10 cursor-pointer"
              >
                &times;
              </button>
            </div>

            <div className="flex-1 overflow-y-auto rounded-xl bg-surface-950 p-4 font-mono text-xs text-surface-200/90 leading-relaxed whitespace-pre-wrap border border-white/5">
              {previewText.text}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setPreviewText(null)}
                className="px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-xs font-semibold text-white transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
