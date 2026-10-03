import { useEffect, useState, useCallback } from "react";
import { useSearchParams, Link } from "react-router-dom";
import api, {
  APIError,
  type JobDescriptionAnalysisData,
  type ResumeJdMatchData,
  type ResumeJdMatchHistoryItemData,
  type CoverLetterHistoryItemData,
  type ColdEmailHistoryItemData,
  type ResumeData,
} from "../lib/api";
import AILoadingState from "../components/ui/AILoadingState";
import LoadingSpinner from "../components/ui/LoadingSpinner";

type ActiveTab = "analyzer" | "match" | "cover-letter" | "cold-email";

export default function CareerIntelligence() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = (searchParams.get("tab") as ActiveTab) || "analyzer";
  const [activeTab, setActiveTab] = useState<ActiveTab>(
    ["analyzer", "match", "cover-letter", "cold-email"].includes(initialTab) ? initialTab : "analyzer"
  );

  // Synchronize query param
  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  // Shared state across tabs (e.g. pasted JD carried between tools)
  const [sharedJdText, setSharedJdText] = useState<string>("");
  const [sharedJobTitle, setSharedJobTitle] = useState<string>("");
  const [sharedCompany, setSharedCompany] = useState<string>("");

  // Resumes list for matching & cover letter & cold email
  const [resumes, setResumes] = useState<ResumeData[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [loadingResumes, setLoadingResumes] = useState<boolean>(true);

  // --------------------------------------------------------------------------
  // Tab 1: JD Analyzer State
  // --------------------------------------------------------------------------
  const [analyzerInput, setAnalyzerInput] = useState<string>("");
  const [analyzingJd, setAnalyzingJd] = useState<boolean>(false);
  const [jdAnalysisResult, setJdAnalysisResult] = useState<JobDescriptionAnalysisData | null>(null);
  const [analyzerError, setAnalyzerError] = useState<string | null>(null);

  // --------------------------------------------------------------------------
  // Tab 2: Resume -> JD Match State
  // --------------------------------------------------------------------------
  const [matchingResume, setMatchingResume] = useState<boolean>(false);
  const [matchResult, setMatchResult] = useState<ResumeJdMatchData | null>(null);
  const [matchError, setMatchError] = useState<string | null>(null);
  const [matchHistory, setMatchHistory] = useState<ResumeJdMatchHistoryItemData[]>([]);
  const [showHistoryModal, setShowHistoryModal] = useState<boolean>(false);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  // --------------------------------------------------------------------------
  // Tab 3: Cover Letter Generator State
  // --------------------------------------------------------------------------
  const [clJobTitle, setClJobTitle] = useState<string>("");
  const [clCompany, setClCompany] = useState<string>("");
  const [clTone, setClTone] = useState<string>("Professional");
  const [clLength, setClLength] = useState<string>("Standard");
  const [generatingCl, setGeneratingCl] = useState<boolean>(false);
  const [editableLetter, setEditableLetter] = useState<string>("");
  const [clError, setClError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);
  const [clHistory, setClHistory] = useState<CoverLetterHistoryItemData[]>([]);

  // --------------------------------------------------------------------------
  // Tab 4: Cold Email Generator State
  // --------------------------------------------------------------------------
  const [ceJobTitle, setCeJobTitle] = useState<string>("");
  const [ceCompany, setCeCompany] = useState<string>("");
  const [ceRecruiterName, setCeRecruiterName] = useState<string>("");
  const [ceRecruiterEmail, setCeRecruiterEmail] = useState<string>("");
  const [ceJobDescription, setCeJobDescription] = useState<string>("");
  const [ceResumeId, setCeResumeId] = useState<number | null>(null);
  const [ceMatchId, setCeMatchId] = useState<number | null>(null);
  const [ceEmailType, setCeEmailType] = useState<string>("Recruiter Outreach");
  const [ceTone, setCeTone] = useState<string>("Professional");
  const [ceLength, setCeLength] = useState<string>("Short");
  const [ceCompanyInfo, setCeCompanyInfo] = useState<string>("");
  const [cePortfolioUrl, setCePortfolioUrl] = useState<string>("");
  const [ceGithubUrl, setCeGithubUrl] = useState<string>("");
  const [ceLinkedinUrl, setCeLinkedinUrl] = useState<string>("");
  const [ceAdditionalContext, setCeAdditionalContext] = useState<string>("");
  const [ceShowAdvanced, setCeShowAdvanced] = useState<boolean>(false);
  const [generatingCe, setGeneratingCe] = useState<boolean>(false);
  const [regeneratingCeSubject, setRegeneratingCeSubject] = useState<boolean>(false);
  const [generatedCeId, setGeneratedCeId] = useState<number | null>(null);
  const [ceSubject, setCeSubject] = useState<string>("");
  const [ceBody, setCeBody] = useState<string>("");
  const [ceError, setCeError] = useState<string | null>(null);
  const [ceCopySuccess, setCeCopySuccess] = useState<boolean>(false);
  const [ceHistory, setCeHistory] = useState<ColdEmailHistoryItemData[]>([]);
  const [showCeHistoryModal, setShowCeHistoryModal] = useState<boolean>(false);
  const [savingCeEdits, setSavingCeEdits] = useState<boolean>(false);
  const [saveCeSuccess, setSaveCeSuccess] = useState<boolean>(false);

  // Load user resumes
  const loadInitialData = useCallback(async () => {
    setLoadingResumes(true);
    try {
      const res = await api.getResumes();
      if (res.data) {
        setResumes(res.data);
        if (res.data.length > 0) {
          setSelectedResumeId(res.data[0].id);
        }
      }
    } catch {
      // Handled silently
    } finally {
      setLoadingResumes(false);
    }
  }, []);

  const loadMatchHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const res = await api.getResumeJdMatches();
      if (res.data) {
        setMatchHistory(res.data);
      }
    } catch {
      // Ignore background history failure
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  const loadCoverLetterHistory = useCallback(async () => {
    try {
      const res = await api.getCoverLetters();
      if (res.data) {
        setClHistory(res.data);
      }
    } catch {
      // Ignore background fetch error
    }
  }, []);

  const loadColdEmailHistory = useCallback(async () => {
    try {
      const res = await api.getColdEmailHistory();
      if (res.data) {
        setCeHistory(res.data);
      }
    } catch {
      // Ignore background fetch error
    }
  }, []);

  useEffect(() => {
    loadInitialData();
    loadMatchHistory();
    loadCoverLetterHistory();
    loadColdEmailHistory();
  }, [loadInitialData, loadMatchHistory, loadCoverLetterHistory, loadColdEmailHistory]);

  // ===========================================================================
  // Tab 1 Action Handlers
  // ===========================================================================
  const handleAnalyzeJd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!analyzerInput.trim() || analyzerInput.trim().length < 20) {
      setAnalyzerError("Please paste a complete job description (minimum 20 characters).");
      return;
    }
    setAnalyzingJd(true);
    setAnalyzerError(null);

    try {
      const res = await api.analyzeJobDescription(analyzerInput.trim());
      if (res.data) {
        setJdAnalysisResult(res.data);
        setSharedJdText(analyzerInput.trim());
        if (res.data.job_title) {
          setSharedJobTitle(res.data.job_title);
          setClJobTitle(res.data.job_title);
        }
        if (res.data.company) {
          setSharedCompany(res.data.company);
          setClCompany(res.data.company);
        }
      }
    } catch (err) {
      if (err instanceof APIError) {
        setAnalyzerError(err.message);
      } else {
        setAnalyzerError("AI analysis failed. Please verify Ollama is running.");
      }
    } finally {
      setAnalyzingJd(false);
    }
  };

  const handleSendToMatch = () => {
    handleTabChange("match");
  };

  const handleSendToCoverLetter = () => {
    if (jdAnalysisResult?.job_title) setClJobTitle(jdAnalysisResult.job_title);
    if (jdAnalysisResult?.company) setClCompany(jdAnalysisResult.company);
    handleTabChange("cover-letter");
  };

  // ===========================================================================
  // Tab 2 Action Handlers (Resume -> JD Match)
  // ===========================================================================
  const handleRunMatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedResumeId) {
      setMatchError("Please select an uploaded resume to evaluate.");
      return;
    }
    if (!sharedJdText.trim() || sharedJdText.trim().length < 20) {
      setMatchError("Please paste a target Job Description (minimum 20 characters).");
      return;
    }

    setMatchingResume(true);
    setMatchError(null);

    try {
      const res = await api.matchResumeToJD({
        resume_id: selectedResumeId,
        job_description: sharedJdText.trim(),
        job_title: sharedJobTitle.trim() || undefined,
        company_name: sharedCompany.trim() || undefined,
      });
      if (res.data) {
        setMatchResult(res.data);
        await loadMatchHistory();
      }
    } catch (err) {
      if (err instanceof APIError) {
        setMatchError(err.message);
      } else {
        setMatchError("Resume matching failed. Verify Ollama is running.");
      }
    } finally {
      setMatchingResume(false);
    }
  };

  const handleSelectPastMatch = async (matchId: number) => {
    try {
      const res = await api.getResumeJdMatchDetail(matchId);
      if (res.data) {
        setMatchResult(res.data);
        setShowHistoryModal(false);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setMatchError(err.message);
      }
    }
  };

  // ===========================================================================
  // Tab 3 Action Handlers (Cover Letter Generator)
  // ===========================================================================
  const handleGenerateCoverLetter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedResumeId) {
      setClError("Please select your uploaded resume.");
      return;
    }
    if (!clJobTitle.trim()) {
      setClError("Please specify the target job title.");
      return;
    }
    if (!clCompany.trim()) {
      setClError("Please specify the target company name.");
      return;
    }
    if (!sharedJdText.trim() || sharedJdText.trim().length < 20) {
      setClError("Please provide the Job Description.");
      return;
    }

    setGeneratingCl(true);
    setClError(null);
    setCopySuccess(false);

    try {
      const res = await api.generateCoverLetter({
        resume_id: selectedResumeId,
        job_description: sharedJdText.trim(),
        job_title: clJobTitle.trim(),
        company_name: clCompany.trim(),
        tone: clTone,
        length: clLength,
      });
      if (res.data) {
        setEditableLetter(res.data.content);
        await loadCoverLetterHistory();
      }
    } catch (err) {
      if (err instanceof APIError) {
        setClError(err.message);
      } else {
        setClError("Cover letter generation failed. Verify Ollama is running.");
      }
    } finally {
      setGeneratingCl(false);
    }
  };

  const handleCopyLetter = async () => {
    if (!editableLetter) return;
    try {
      await navigator.clipboard.writeText(editableLetter);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2500);
    } catch {
      // Fallback
      setCopySuccess(false);
    }
  };

  const handleDownloadLetter = () => {
    if (!editableLetter) return;
    const blob = new Blob([editableLetter], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const cleanTitle = (clJobTitle || "Cover_Letter").replace(/[^a-zA-Z0-9]/g, "_");
    link.download = `${cleanTitle}_Cover_Letter.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // ===========================================================================
  // Tab 4 Action Handlers (Cold Email Generator)
  // ===========================================================================
  const handleGenerateColdEmail = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!ceJobTitle.trim()) {
      setCeError("Target Job Title is required.");
      return;
    }
    if (!ceCompany.trim()) {
      setCeError("Company Name is required.");
      return;
    }

    setGeneratingCe(true);
    setCeError(null);
    setCeCopySuccess(false);

    try {
      const res = await api.generateColdEmail({
        job_title: ceJobTitle.trim(),
        company_name: ceCompany.trim(),
        resume_id: ceResumeId ?? (selectedResumeId || undefined),
        match_id: ceMatchId || undefined,
        job_description: ceJobDescription.trim() || sharedJdText.trim() || undefined,
        recruiter_name: ceRecruiterName.trim() || undefined,
        recruiter_email: ceRecruiterEmail.trim() || undefined,
        company_info: ceCompanyInfo.trim() || undefined,
        portfolio_url: cePortfolioUrl.trim() || undefined,
        github_url: ceGithubUrl.trim() || undefined,
        linkedin_url: ceLinkedinUrl.trim() || undefined,
        additional_context: ceAdditionalContext.trim() || undefined,
        email_type: ceEmailType,
        tone: ceTone,
        length: ceLength,
      });

      if (res.data) {
        setGeneratedCeId(res.data.id || null);
        setCeSubject(res.data.subject);
        setCeBody(res.data.body);
        await loadColdEmailHistory();
      }
    } catch (err) {
      if (err instanceof APIError) {
        setCeError(err.message);
      } else {
        setCeError("Cold email generation failed. Please verify Ollama is running.");
      }
    } finally {
      setGeneratingCe(false);
    }
  };

  const handleRegenerateSubject = async () => {
    if (!ceJobTitle.trim() || !ceCompany.trim()) return;
    setRegeneratingCeSubject(true);
    try {
      const res = await api.regenerateColdEmailSubject({
        job_title: ceJobTitle.trim(),
        company_name: ceCompany.trim(),
        candidate_name: undefined,
        key_skills: matchResult?.matched_skills.slice(0, 3) || [],
        email_type: ceEmailType,
      });
      if (res.data && res.data.subject) {
        setCeSubject(res.data.subject);
      }
    } catch {
      // Keep existing subject
    } finally {
      setRegeneratingCeSubject(false);
    }
  };

  const handleCopyColdEmail = async () => {
    if (!ceBody && !ceSubject) return;
    const fullText = `Subject: ${ceSubject}\n\n${ceBody}`;
    try {
      await navigator.clipboard.writeText(fullText);
      setCeCopySuccess(true);
      setTimeout(() => setCeCopySuccess(false), 2500);
    } catch {
      setCeCopySuccess(false);
    }
  };

  const handleDownloadColdEmail = () => {
    if (!ceBody && !ceSubject) return;
    const fullText = `Subject: ${ceSubject}\n\n${ceBody}`;
    const blob = new Blob([fullText], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const cleanTitle = (ceJobTitle || "Cold_Email").replace(/[^a-zA-Z0-9]/g, "_");
    link.download = `${cleanTitle}_Cold_Email.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleOpenEmailClient = () => {
    if (!ceSubject && !ceBody) return;
    const recipient = ceRecruiterEmail.trim();
    const mailtoUrl = `mailto:${encodeURIComponent(recipient)}?subject=${encodeURIComponent(ceSubject)}&body=${encodeURIComponent(ceBody)}`;
    window.location.href = mailtoUrl;
  };

  const handleSaveColdEmailEdits = async () => {
    if (!generatedCeId || !ceSubject.trim() || !ceBody.trim()) return;
    setSavingCeEdits(true);
    try {
      await api.updateColdEmail(generatedCeId, {
        subject: ceSubject.trim(),
        body: ceBody.trim(),
        recruiter_name: ceRecruiterName.trim() || undefined,
        recruiter_email: ceRecruiterEmail.trim() || undefined,
      });
      setSaveCeSuccess(true);
      setTimeout(() => setSaveCeSuccess(false), 2500);
      await loadColdEmailHistory();
    } catch (err) {
      if (err instanceof APIError) {
        setCeError(err.message);
      }
    } finally {
      setSavingCeEdits(false);
    }
  };

  const handleClearColdEmail = () => {
    setCeSubject("");
    setCeBody("");
    setGeneratedCeId(null);
  };

  const handleSelectPastColdEmail = async (id: number) => {
    try {
      const res = await api.getColdEmailDetail(id);
      if (res.data) {
        setGeneratedCeId(res.data.id || null);
        setCeJobTitle(res.data.job_title);
        setCeCompany(res.data.company_name);
        if (res.data.recruiter_name) setCeRecruiterName(res.data.recruiter_name);
        if (res.data.recruiter_email) setCeRecruiterEmail(res.data.recruiter_email);
        setCeEmailType(res.data.email_type);
        setCeTone(res.data.tone);
        setCeLength(res.data.length);
        setCeSubject(res.data.subject);
        setCeBody(res.data.body);
        setShowCeHistoryModal(false);
      }
    } catch {
      // Handled silently
    }
  };

  const handleDeleteColdEmail = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteColdEmail(id);
      await loadColdEmailHistory();
      if (generatedCeId === id) {
        handleClearColdEmail();
      }
    } catch {
      // Handled silently
    }
  };

  // Cross-tab hand-off actions
  const handleSendToColdEmail = () => {
    if (jdAnalysisResult?.job_title) setCeJobTitle(jdAnalysisResult.job_title);
    if (jdAnalysisResult?.company) setCeCompany(jdAnalysisResult.company);
    if (analyzerInput) setCeJobDescription(analyzerInput);
    handleTabChange("cold-email");
  };

  const handleSendMatchToColdEmail = () => {
    if (matchResult) {
      if (matchResult.job_title) setCeJobTitle(matchResult.job_title);
      if (matchResult.company_name) setCeCompany(matchResult.company_name);
      if (matchResult.resume_id) setCeResumeId(matchResult.resume_id);
      setCeMatchId(matchResult.id);
      if (sharedJdText) setCeJobDescription(sharedJdText);
    }
    handleTabChange("cold-email");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-3xl p-2 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
              🧠
            </span>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Career Intelligence
              </h1>
              <p className="text-xs sm:text-sm text-surface-200/70 mt-0.5">
                Targeted AI career-analysis workspace: Job Description Analyzer, Resume → JD Match, Cover Letter Generator, and Cold Email Generator.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Tabs Switcher */}
        <div className="flex items-center p-1.5 rounded-2xl bg-surface-900 border border-white/10 self-start sm:self-auto shadow-inner">
          <button
            type="button"
            onClick={() => handleTabChange("analyzer")}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeTab === "analyzer"
                ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                : "text-surface-200/70 hover:text-white hover:bg-white/5"
            }`}
          >
            <span>📋</span>
            <span>JD Analyzer</span>
          </button>

          <button
            type="button"
            onClick={() => handleTabChange("match")}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeTab === "match"
                ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                : "text-surface-200/70 hover:text-white hover:bg-white/5"
            }`}
          >
            <span>🎯</span>
            <span>Resume → JD Match</span>
          </button>

          <button
            type="button"
            onClick={() => handleTabChange("cover-letter")}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeTab === "cover-letter"
                ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                : "text-surface-200/70 hover:text-white hover:bg-white/5"
            }`}
          >
            <span>✍️</span>
            <span>Cover Letter</span>
          </button>

          <button
            type="button"
            onClick={() => handleTabChange("cold-email")}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeTab === "cold-email"
                ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                : "text-surface-200/70 hover:text-white hover:bg-white/5"
            }`}
          >
            <span>📧</span>
            <span>Cold Email</span>
          </button>
        </div>
      </div>

      {/* =====================================================================
          TAB 1: JOB DESCRIPTION ANALYZER
         ===================================================================== */}
      {activeTab === "analyzer" && (
        <div className="space-y-8 animate-fade-in">
          {/* Input Form Box */}
          <div className="rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 space-y-6 shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>Job Description Analyzer</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                    Ollama Powered
                  </span>
                </h2>
                <p className="text-xs text-surface-200/70 mt-1">
                  Paste any target Job Description below. Ollama extracts explicit requirements without inventing unstated qualifications.
                </p>
              </div>

              {sharedJdText && !analyzerInput && (
                <button
                  type="button"
                  onClick={() => setAnalyzerInput(sharedJdText)}
                  className="text-xs text-brand-400 hover:text-brand-300 underline font-medium"
                >
                  Load Current JD
                </button>
              )}
            </div>

            {analyzerError && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300 space-y-1">
                <p className="font-bold">Analysis Notice</p>
                <p>{analyzerError}</p>
              </div>
            )}

            <form onSubmit={handleAnalyzeJd} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                  Target Job Description Text
                </label>
                <textarea
                  rows={8}
                  value={analyzerInput}
                  onChange={(e) => setAnalyzerInput(e.target.value)}
                  placeholder="Paste complete job description, duties, requirements, and tech stack here..."
                  className="w-full rounded-xl bg-surface-950 border border-white/10 p-4 text-xs text-white placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors font-mono leading-relaxed"
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-[11px] text-surface-200/50">
                  {analyzerInput.length} characters
                </span>

                <button
                  type="submit"
                  disabled={analyzingJd || !analyzerInput.trim()}
                  className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-md shadow-brand-600/30 flex items-center gap-2 cursor-pointer"
                >
                  {analyzingJd ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span>Extracting Intelligence...</span>
                    </>
                  ) : (
                    <>
                      <span>✨</span>
                      <span>Analyze Job Description</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Loading Animation */}
          {analyzingJd && (
            <AILoadingState
              title="Deconstructing Job Description"
              subtitle="Ollama is extracting strictly verified requirements, technologies, and responsibilities..."
              steps={[
                "Reading raw job description context...",
                "Extracting mandatory vs preferred qualifications...",
                "Mapping technical framework & skill requirements...",
                "Compiling structured keyword taxonomy...",
              ]}
            />
          )}

          {/* Structured Analysis Results */}
          {jdAnalysisResult && !analyzingJd && (
            <div className="space-y-6 animate-fade-in">
              {/* Role Header Banner */}
              <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-950/60 to-surface-900 border border-brand-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-brand-400">
                    Verified Extraction
                  </span>
                  <h3 className="text-xl font-extrabold text-white mt-0.5">
                    {jdAnalysisResult.job_title || "Target Role Position"}
                  </h3>
                  {jdAnalysisResult.company && (
                    <p className="text-xs text-surface-200/80 mt-0.5">
                      Company: <span className="text-brand-300 font-semibold">{jdAnalysisResult.company}</span>
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleSendToMatch}
                    className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-md shadow-brand-600/30 transition-all flex items-center gap-1.5"
                  >
                    <span>🎯 Match With My Resume →</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleSendToCoverLetter}
                    className="px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-white text-xs font-bold transition-all flex items-center gap-1.5"
                  >
                    <span>✍️ Generate Cover Letter</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleSendToColdEmail}
                    className="px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-white text-xs font-bold transition-all flex items-center gap-1.5"
                  >
                    <span>📧 Draft Cold Email</span>
                  </button>
                </div>
              </div>

              {/* Grid of Extracted Requirements */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 1. Required Skills */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-red-400" />
                      Required Skills
                    </h4>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-surface-800 text-surface-200/70">
                      {jdAnalysisResult.required_skills.length} items
                    </span>
                  </div>

                  {jdAnalysisResult.required_skills.length === 0 ? (
                    <p className="text-xs text-surface-200/50 italic">None explicitly listed in description.</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {jdAnalysisResult.required_skills.map((s, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs font-medium"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* 2. Preferred Skills */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-blue-400" />
                      Preferred / Bonus Skills
                    </h4>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-surface-800 text-surface-200/70">
                      {jdAnalysisResult.preferred_skills.length} items
                    </span>
                  </div>

                  {jdAnalysisResult.preferred_skills.length === 0 ? (
                    <p className="text-xs text-surface-200/50 italic">No secondary skills specified.</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {jdAnalysisResult.preferred_skills.map((s, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-medium"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* 3. Technologies & Tools */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-purple-400" />
                    Technologies & Frameworks
                  </h4>
                  {jdAnalysisResult.technologies.length === 0 ? (
                    <p className="text-xs text-surface-200/50 italic">No specific technologies detected.</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {jdAnalysisResult.technologies.map((t, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-medium"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* 4. Experience Requirements */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    Experience & Seniority
                  </h4>
                  {jdAnalysisResult.experience.length === 0 ? (
                    <p className="text-xs text-surface-200/50 italic">No explicit years of experience stated.</p>
                  ) : (
                    <ul className="space-y-1.5 text-xs text-surface-200/80 list-disc list-inside">
                      {jdAnalysisResult.experience.map((e, i) => (
                        <li key={i}>{e}</li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* 5. Key Responsibilities */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3 md:col-span-2">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-400" />
                    Key Responsibilities
                  </h4>
                  {jdAnalysisResult.responsibilities.length === 0 ? (
                    <p className="text-xs text-surface-200/50 italic">No responsibilities broken out.</p>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {jdAnalysisResult.responsibilities.map((r, i) => (
                        <div
                          key={i}
                          className="p-2.5 rounded-xl bg-surface-950 border border-white/5 text-xs text-surface-200/90 flex items-start gap-2"
                        >
                          <span className="text-amber-400 font-bold shrink-0">•</span>
                          <span>{r}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 6. Education & Certifications */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Education & Certifications
                  </h4>
                  <div className="space-y-2 text-xs text-surface-200/80">
                    <div>
                      <span className="text-surface-200/50 font-bold uppercase text-[10px] block">Education:</span>
                      {jdAnalysisResult.education.length > 0 ? (
                        <p>{jdAnalysisResult.education.join(", ")}</p>
                      ) : (
                        <p className="italic text-surface-200/40">Not specified</p>
                      )}
                    </div>
                    <div>
                      <span className="text-surface-200/50 font-bold uppercase text-[10px] block">Certifications:</span>
                      {jdAnalysisResult.certifications.length > 0 ? (
                        <p>{jdAnalysisResult.certifications.join(", ")}</p>
                      ) : (
                        <p className="italic text-surface-200/40">None specified</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* 7. Soft Skills & Keywords */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Keywords & Soft Competencies
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {jdAnalysisResult.keywords.concat(jdAnalysisResult.soft_skills).map((k, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded bg-surface-800 text-surface-200/80 border border-white/5 text-[11px]"
                      >
                        #{k}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 2: RESUME -> JD MATCH
         ===================================================================== */}
      {activeTab === "match" && (
        <div className="space-y-8 animate-fade-in">
          {/* Comparison Setup Panel */}
          <div className="rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 space-y-6 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>Resume → Job Description Match</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    Skill Gap & ATS Intelligence
                  </span>
                </h2>
                <p className="text-xs text-surface-200/70 mt-1">
                  Evaluate your verified resume credentials against any target Job Description and uncover skill alignment.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setShowHistoryModal(true)}
                className="px-3.5 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs font-semibold text-brand-300 hover:text-white transition-all flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
              >
                <span>🕒</span>
                <span>Previous Matches ({matchHistory.length})</span>
              </button>
            </div>

            {matchError && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300">
                {matchError}
              </div>
            )}

            <form onSubmit={handleRunMatch} className="space-y-5">
              {/* 1. Select Resume */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                  1. Select Uploaded Resume
                </label>
                {loadingResumes ? (
                  <div className="h-10 rounded-xl bg-surface-950 animate-pulse" />
                ) : resumes.length === 0 ? (
                  <div className="p-4 rounded-xl bg-surface-950 border border-white/10 text-xs text-surface-200/70 flex items-center justify-between">
                    <span>No uploaded resumes found.</span>
                    <Link to="/resumes" className="text-brand-400 hover:text-brand-300 font-bold">
                      Upload in Resume Studio →
                    </Link>
                  </div>
                ) : (
                  <select
                    value={selectedResumeId ?? ""}
                    onChange={(e) => setSelectedResumeId(Number(e.target.value))}
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white focus:outline-none focus:border-brand-500"
                  >
                    {resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.title} ({r.current_version ? r.current_version.filename : "Active"})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* 2. Job Description Input */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    2. Target Job Description
                  </label>
                  {sharedJdText && (
                    <span className="text-[11px] text-emerald-400 font-semibold">
                      ✓ Job description loaded ({sharedJdText.length} chars)
                    </span>
                  )}
                </div>
                <textarea
                  rows={6}
                  value={sharedJdText}
                  onChange={(e) => setSharedJdText(e.target.value)}
                  placeholder="Paste target job requirements, qualifications, or responsibilities..."
                  className="w-full rounded-xl bg-surface-950 border border-white/10 p-4 text-xs text-white placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors font-mono leading-relaxed"
                />
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={matchingResume || !selectedResumeId || !sharedJdText.trim()}
                  className="px-8 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-lg shadow-brand-600/30 flex items-center gap-2 cursor-pointer"
                >
                  {matchingResume ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span>Evaluating Compatibility...</span>
                    </>
                  ) : (
                    <>
                      <span>⚡</span>
                      <span>Run AI Match & Skill Gap Analysis</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Loading Animation */}
          {matchingResume && (
            <AILoadingState
              title="Evaluating Resume Against Job Description"
              subtitle="Comparing candidate skills, keywords, and verified achievements against target criteria..."
              steps={[
                "Reading parsed resume work history & credentials...",
                "Comparing keyword & technology density...",
                "Detecting verified matches vs missing proficiencies...",
                "Calculating dimensional match scores & actionable suggestions...",
              ]}
            />
          )}

          {/* Match Evaluation Results */}
          {matchResult && !matchingResume && (
            <div className="space-y-6 animate-fade-in">
              {/* Top Score Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 sm:gap-4">
                {/* Overall Score */}
                <div className="p-4 rounded-2xl bg-surface-900 border border-brand-500/30 text-center space-y-1 col-span-2 sm:col-span-1 shadow-lg shadow-brand-500/5">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-brand-400">
                    Overall Match
                  </span>
                  <div className="text-3xl font-black text-white">
                    {Math.round(matchResult.overall_score)}%
                  </div>
                  <div className="h-1.5 w-full bg-surface-800 rounded-full overflow-hidden mt-1">
                    <div
                      className="h-full bg-gradient-to-r from-brand-500 to-emerald-400 rounded-full"
                      style={{ width: `${matchResult.overall_score}%` }}
                    />
                  </div>
                </div>

                {/* Skills Match */}
                <div className="p-4 rounded-2xl bg-surface-900 border border-white/10 text-center space-y-1">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-surface-200/60">
                    Skills Match
                  </span>
                  <div className="text-2xl font-bold text-white">
                    {Math.round(matchResult.skills_score)}%
                  </div>
                  <div className="h-1.5 w-full bg-surface-800 rounded-full overflow-hidden mt-1">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: `${matchResult.skills_score}%` }} />
                  </div>
                </div>

                {/* Keyword Match */}
                <div className="p-4 rounded-2xl bg-surface-900 border border-white/10 text-center space-y-1">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-surface-200/60">
                    Keyword Density
                  </span>
                  <div className="text-2xl font-bold text-white">
                    {Math.round(matchResult.keyword_score)}%
                  </div>
                  <div className="h-1.5 w-full bg-surface-800 rounded-full overflow-hidden mt-1">
                    <div className="h-full bg-purple-500 rounded-full" style={{ width: `${matchResult.keyword_score}%` }} />
                  </div>
                </div>

                {/* Experience Match */}
                <div className="p-4 rounded-2xl bg-surface-900 border border-white/10 text-center space-y-1">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-surface-200/60">
                    Experience
                  </span>
                  <div className="text-2xl font-bold text-white">
                    {Math.round(matchResult.experience_score)}%
                  </div>
                  <div className="h-1.5 w-full bg-surface-800 rounded-full overflow-hidden mt-1">
                    <div className="h-full bg-amber-500 rounded-full" style={{ width: `${matchResult.experience_score}%` }} />
                  </div>
                </div>

                {/* Responsibility Match */}
                <div className="p-4 rounded-2xl bg-surface-900 border border-white/10 text-center space-y-1">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-surface-200/60">
                    Duties Match
                  </span>
                  <div className="text-2xl font-bold text-white">
                    {Math.round(matchResult.responsibility_score)}%
                  </div>
                  <div className="h-1.5 w-full bg-surface-800 rounded-full overflow-hidden mt-1">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${matchResult.responsibility_score}%` }} />
                  </div>
                </div>
              </div>

              {/* Skills Breakdown 3 Columns */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* 1. Matched Skills */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-emerald-500/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>✓</span>
                      <span>Matched Skills</span>
                    </h4>
                    <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300">
                      {matchResult.matched_skills.length}
                    </span>
                  </div>
                  <p className="text-[11px] text-surface-200/60">
                    Verified in both your resume and the target Job Description.
                  </p>
                  <div className="space-y-1.5">
                    {matchResult.matched_skills.length === 0 ? (
                      <p className="text-xs text-surface-200/50 italic">No exact skill matches identified.</p>
                    ) : (
                      matchResult.matched_skills.map((s, i) => (
                        <div
                          key={i}
                          className="px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 font-medium flex items-center gap-2"
                        >
                          <span className="font-bold">✓</span>
                          <span>{s}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* 2. Missing Skills */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-red-500/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>✗</span>
                      <span>Missing from Resume</span>
                    </h4>
                    <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-red-500/10 text-red-300">
                      {matchResult.missing_skills.length}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-[10px] text-red-300">
                    <strong>Note:</strong> Means "the skill was not found in the provided resume" — not that you definitely lack it.
                  </div>
                  <div className="space-y-1.5">
                    {matchResult.missing_skills.length === 0 ? (
                      <p className="text-xs text-surface-200/50 italic">No missing core skills detected.</p>
                    ) : (
                      matchResult.missing_skills.map((s, i) => (
                        <div
                          key={i}
                          className="px-3 py-1.5 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 font-medium flex items-center gap-2"
                        >
                          <span className="font-bold">✗</span>
                          <span>{s}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* 3. Partial Matches */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-amber-500/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>△</span>
                      <span>Partial Matches</span>
                    </h4>
                    <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-amber-500/10 text-amber-300">
                      {matchResult.partial_matches.length}
                    </span>
                  </div>
                  <p className="text-[11px] text-surface-200/60">
                    Related or adjacent domain proficiencies demonstrated on resume.
                  </p>
                  <div className="space-y-1.5">
                    {matchResult.partial_matches.length === 0 ? (
                      <p className="text-xs text-surface-200/50 italic">None</p>
                    ) : (
                      matchResult.partial_matches.map((s, i) => (
                        <div
                          key={i}
                          className="px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 font-medium flex items-center gap-2"
                        >
                          <span className="font-bold">△</span>
                          <span>{s}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Experience, Gaps, and Improvement Suggestions */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Relevant Experience */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Relevant Experience
                  </h4>
                  <ul className="space-y-2 text-xs text-surface-200/80">
                    {matchResult.relevant_experience.map((e, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-brand-400 font-bold">•</span>
                        <span>{e}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Potential Gaps */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Potential Gaps
                  </h4>
                  <ul className="space-y-2 text-xs text-surface-200/80">
                    {matchResult.potential_gaps.map((g, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-red-400 font-bold">•</span>
                        <span>{g}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Improvement Suggestions */}
                <div className="p-5 rounded-2xl bg-surface-900 border border-white/10 space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Actionable Recommendations
                  </h4>
                  <ul className="space-y-2 text-xs text-surface-200/80">
                    {matchResult.improvement_suggestions.map((s, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-emerald-400 font-bold">💡</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Ready to Reach Out Cold Email Card */}
              <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-950/60 to-surface-900 border border-brand-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg">
                <div>
                  <h4 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>📧</span>
                    <span>Ready to reach out to recruiters?</span>
                  </h4>
                  <p className="text-xs text-surface-200/70 mt-1">
                    Convert these {matchResult.matched_skills.length} verified matched skills and experience insights into a tailored cold outreach email.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleSendMatchToColdEmail}
                  className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-all shadow-md shadow-brand-600/30 shrink-0 flex items-center gap-1.5 cursor-pointer"
                >
                  <span>✉️ Draft Cold Email with Match Insights →</span>
                </button>
              </div>
            </div>
          )}

          {/* History Drawer / Modal */}
          {showHistoryModal && (
            <div className="fixed inset-0 z-50 overflow-hidden flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
              <div className="w-full max-w-xl rounded-2xl bg-surface-950 border border-white/10 p-6 space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <h3 className="text-sm font-bold text-white">Previous Match Evaluations</h3>
                  <button
                    type="button"
                    onClick={() => setShowHistoryModal(false)}
                    className="text-surface-200/60 hover:text-white text-sm"
                  >
                    ✕
                  </button>
                </div>

                {loadingHistory ? (
                  <div className="py-8 text-center">
                    <LoadingSpinner size="md" />
                  </div>
                ) : matchHistory.length === 0 ? (
                  <p className="text-xs text-surface-200/60 py-6 text-center">No match history yet.</p>
                ) : (
                  <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                    {matchHistory.map((item) => (
                      <div
                        key={item.id}
                        onClick={() => handleSelectPastMatch(item.id)}
                        className="p-3 rounded-xl bg-surface-900 hover:bg-surface-800 border border-white/5 cursor-pointer transition-colors flex items-center justify-between"
                      >
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-white truncate">
                            {item.job_title || "Target Role"}
                          </p>
                          <p className="text-[11px] text-surface-200/60 truncate">
                            Resume: {item.resume_title} • {new Date(item.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="text-sm font-black text-brand-400">
                            {Math.round(item.overall_score)}%
                          </span>
                          <span className="block text-[10px] text-surface-200/50">Overall</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 3: COVER LETTER GENERATOR
         ===================================================================== */}
      {activeTab === "cover-letter" && (
        <div className="space-y-8 animate-fade-in">
          {/* Cover Letter Input Form */}
          <div className="rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 space-y-6 shadow-xl">
            <div>
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>AI Cover Letter Generator</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                    Grounded in Verified Resume
                  </span>
                </h2>
                {clHistory.length > 0 && (
                  <span className="text-[11px] text-surface-200/60">
                    Saved letters: {clHistory.length}
                  </span>
                )}
              </div>
              <p className="text-xs text-surface-200/70 mt-1">
                Generates a professional cover letter using exclusively your verified resume and target Job Description. No unearned facts or hallucinated metrics.
              </p>
            </div>

            {clError && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300">
                {clError}
              </div>
            )}

            <form onSubmit={handleGenerateCoverLetter} className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Resume Selector */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    Source Resume
                  </label>
                  <select
                    value={selectedResumeId ?? ""}
                    onChange={(e) => setSelectedResumeId(Number(e.target.value))}
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white focus:outline-none focus:border-brand-500"
                  >
                    {resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.title} ({r.current_version ? r.current_version.filename : "Active"})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Target Role Title */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    Target Role Title
                  </label>
                  <input
                    type="text"
                    value={clJobTitle}
                    onChange={(e) => setClJobTitle(e.target.value)}
                    placeholder="e.g. Senior Backend Engineer"
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white focus:outline-none focus:border-brand-500"
                  />
                </div>

                {/* Company Name */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    Company Name
                  </label>
                  <input
                    type="text"
                    value={clCompany}
                    onChange={(e) => setClCompany(e.target.value)}
                    placeholder="e.g. Stripe, TechScale Corp"
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white focus:outline-none focus:border-brand-500"
                  />
                </div>

                {/* Tone & Length Selectors */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                      Tone
                    </label>
                    <select
                      value={clTone}
                      onChange={(e) => setClTone(e.target.value)}
                      className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white focus:outline-none focus:border-brand-500"
                    >
                      <option value="Professional">Professional</option>
                      <option value="Confident">Confident</option>
                      <option value="Concise">Concise</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                      Length
                    </label>
                    <select
                      value={clLength}
                      onChange={(e) => setClLength(e.target.value)}
                      className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white focus:outline-none focus:border-brand-500"
                    >
                      <option value="Short">Short (~150-200 words)</option>
                      <option value="Standard">Standard (~250-350 words)</option>
                      <option value="Detailed">Detailed (~400-500 words)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Job Description Textarea */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                  Target Job Description Text
                </label>
                <textarea
                  rows={5}
                  value={sharedJdText}
                  onChange={(e) => setSharedJdText(e.target.value)}
                  placeholder="Paste job description to tailor the cover letter against..."
                  className="w-full rounded-xl bg-surface-950 border border-white/10 p-4 text-xs text-white placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 font-mono"
                />
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={generatingCl || !selectedResumeId || !clJobTitle.trim() || !clCompany.trim() || !sharedJdText.trim()}
                  className="px-8 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-lg shadow-brand-600/30 flex items-center gap-2 cursor-pointer"
                >
                  {generatingCl ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span>Composing Cover Letter...</span>
                    </>
                  ) : (
                    <>
                      <span>✨</span>
                      <span>Generate Tailored Cover Letter</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Loading Animation */}
          {generatingCl && (
            <AILoadingState
              title="Synthesizing Verified Cover Letter"
              subtitle="Grounded strictly in your resume achievements and aligned with the job description..."
              steps={[
                "Matching resume accomplishments to job duties...",
                "Drafting engaging opening tailored to company...",
                "Verifying strict anti-hallucination constraints...",
                "Polishing prose and professional formatting...",
              ]}
            />
          )}

          {/* Generated Cover Letter Workspace */}
          {editableLetter && !generatingCl && (
            <div className="rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 space-y-6 shadow-2xl animate-fade-in">
              {/* Status Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
                <div className="flex items-center gap-2.5">
                  <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                    AI-generated cover letter
                  </span>
                  <span className="text-xs text-surface-200/60">
                    Tone: {clTone} • Length: {clLength}
                  </span>
                </div>

                {/* Actions: Regenerate, Copy, Download */}
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleGenerateCoverLetter}
                    className="px-3 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white border border-white/10 text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer"
                    title="Regenerate"
                  >
                    <span>🔄</span>
                    <span>Regenerate</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyLetter}
                    className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer ${
                      copySuccess
                        ? "bg-emerald-600 text-white border-emerald-500"
                        : "bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white border-white/10"
                    }`}
                  >
                    <span>{copySuccess ? "✓" : "📋"}</span>
                    <span>{copySuccess ? "Copied!" : "Copy"}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleDownloadLetter}
                    className="px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-all shadow-md shadow-brand-600/30 flex items-center gap-1 cursor-pointer"
                  >
                    <span>💾</span>
                    <span>Download (.txt)</span>
                  </button>
                </div>
              </div>

              {/* Notice */}
              <p className="text-[11px] text-surface-200/60 italic">
                You can directly edit the letter content below before copying or downloading.
              </p>

              {/* Editable Textarea */}
              <textarea
                rows={16}
                value={editableLetter}
                onChange={(e) => setEditableLetter(e.target.value)}
                className="w-full rounded-xl bg-surface-950 border border-white/10 p-5 text-sm text-white focus:outline-none focus:border-brand-500 transition-colors font-sans leading-relaxed resize-y"
              />
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 4: COLD EMAIL GENERATOR
         ===================================================================== */}
      {activeTab === "cold-email" && (
        <div className="space-y-8 animate-fade-in">
          {/* Main Setup Card */}
          <div className="rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 space-y-6 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>AI Cold Email Generator</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                    Recruiter & Hiring Outreach
                  </span>
                </h2>
                <p className="text-xs text-surface-200/70 mt-1">
                  Compose high-converting professional outreach emails grounded in your real credentials without hallucinated facts.
                </p>
              </div>

              {/* History button */}
              <button
                type="button"
                onClick={() => setShowCeHistoryModal(true)}
                className="px-3.5 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-xs font-semibold text-brand-300 hover:text-white transition-all flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
              >
                <span>🕒</span>
                <span>Previous Emails ({ceHistory.length})</span>
              </button>
            </div>

            {/* Match Reuse Banner */}
            {ceMatchId && (
              <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="text-sm">🎯</span>
                  <div className="text-xs">
                    <span className="font-bold text-purple-300">Reusing Match Insights:</span>{" "}
                    <span className="text-surface-200/80">
                      Cold email will automatically incorporate verified matched skills and experience from your Resume → JD match evaluation.
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setCeMatchId(null)}
                  className="text-[11px] text-purple-300 hover:text-white underline font-semibold shrink-0 cursor-pointer"
                  title="Unlink match evaluation"
                >
                  Unlink Match
                </button>
              </div>
            )}

            {ceError && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300">
                {ceError}
              </div>
            )}

            <form onSubmit={handleGenerateColdEmail} className="space-y-6">
              {/* Row 1: Target Role & Company Name (Required) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider flex items-center gap-1">
                    <span>Target Job Title</span>
                    <span className="text-red-400 font-bold">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={ceJobTitle}
                    onChange={(e) => setCeJobTitle(e.target.value)}
                    placeholder="e.g. Senior Python Developer"
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3.5 text-xs text-white placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider flex items-center gap-1">
                    <span>Company Name</span>
                    <span className="text-red-400 font-bold">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={ceCompany}
                    onChange={(e) => setCeCompany(e.target.value)}
                    placeholder="e.g. Stripe, OpenAI, TechCorp"
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3.5 text-xs text-white placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors"
                  />
                </div>
              </div>

              {/* Row 2: Recruiter Contact Info (Optional) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    Recruiter / Contact Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={ceRecruiterName}
                    onChange={(e) => setCeRecruiterName(e.target.value)}
                    placeholder="e.g. Sarah Jenkins (Leave blank for general salutation)"
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3.5 text-xs text-white placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                      Recruiter Email (Optional)
                    </label>
                    {!ceRecruiterEmail.trim() && (
                      <span className="text-[10px] text-surface-200/50 italic">
                        Recruiter email not provided
                      </span>
                    )}
                  </div>
                  <input
                    type="email"
                    value={ceRecruiterEmail}
                    onChange={(e) => setCeRecruiterEmail(e.target.value)}
                    placeholder="e.g. sjenkins@company.com"
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3.5 text-xs text-white placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors"
                  />
                </div>
              </div>

              {/* Row 3: Resume Selection & Context */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                  Candidate Resume Grounding
                </label>
                {loadingResumes ? (
                  <div className="h-10 rounded-xl bg-surface-950 animate-pulse" />
                ) : resumes.length === 0 ? (
                  <div className="p-4 rounded-xl bg-surface-950 border border-white/10 text-xs text-surface-200/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="text-amber-400 font-bold">ℹ</span>
                      <span>No resume uploaded yet. Upload a resume to create a more personalized email.</span>
                    </div>
                    <Link to="/resumes" className="text-brand-400 hover:text-brand-300 font-bold shrink-0">
                      Upload in Resume Studio →
                    </Link>
                  </div>
                ) : (
                  <select
                    value={ceResumeId !== null ? ceResumeId : (selectedResumeId ?? "")}
                    onChange={(e) => {
                      const val = e.target.value;
                      setCeResumeId(val ? Number(val) : null);
                    }}
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white focus:outline-none focus:border-brand-500"
                  >
                    {resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.title} ({r.current_version ? r.current_version.filename : "Active Resume"})
                      </option>
                    ))}
                    <option value="">None (Use Candidate Profile & User-Provided Details)</option>
                  </select>
                )}
              </div>

              {/* Row 4: Job Description (Optional) */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    Target Job Description (Optional)
                  </label>
                  {!ceJobDescription.trim() ? (
                    <span className="text-[10px] text-surface-200/50 italic">
                      Add a Job Description to personalize this outreach
                    </span>
                  ) : (
                    <span className="text-[10px] text-emerald-400 font-semibold">
                      ✓ Job description provided ({ceJobDescription.length} chars)
                    </span>
                  )}
                </div>
                <textarea
                  rows={4}
                  value={ceJobDescription}
                  onChange={(e) => setCeJobDescription(e.target.value)}
                  placeholder="Paste relevant job requirements, tech stack, or qualifications to align the outreach pitch..."
                  className="w-full rounded-xl bg-surface-950 border border-white/10 p-3.5 text-xs text-white placeholder:text-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors font-mono leading-relaxed"
                />
              </div>

              {/* Collapsible: Links & Company Information */}
              <div className="rounded-xl border border-white/10 bg-surface-950/60 overflow-hidden">
                <button
                  type="button"
                  onClick={() => setCeShowAdvanced(!ceShowAdvanced)}
                  className="w-full p-3.5 flex items-center justify-between text-xs font-bold text-surface-200 hover:text-white transition-colors cursor-pointer"
                >
                  <span className="flex items-center gap-2">
                    <span>🔗</span>
                    <span>Portfolio, Links & Additional Context</span>
                    <span className="text-[10px] font-normal text-surface-200/50">(Optional)</span>
                  </span>
                  <span className="text-xs">{ceShowAdvanced ? "▲ Hide" : "▼ Show"}</span>
                </button>

                {ceShowAdvanced && (
                  <div className="p-4 border-t border-white/10 space-y-4 animate-fade-in bg-surface-950/90">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-[11px] font-semibold text-surface-200/80 block">Portfolio URL</label>
                        <input
                          type="url"
                          value={cePortfolioUrl}
                          onChange={(e) => setCePortfolioUrl(e.target.value)}
                          placeholder="https://myportfolio.dev"
                          className="w-full rounded-lg bg-surface-900 border border-white/10 p-2.5 text-xs text-white focus:outline-none focus:border-brand-500"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <label className="text-[11px] font-semibold text-surface-200/80 block">GitHub URL</label>
                        <input
                          type="url"
                          value={ceGithubUrl}
                          onChange={(e) => setCeGithubUrl(e.target.value)}
                          placeholder="https://github.com/username"
                          className="w-full rounded-lg bg-surface-900 border border-white/10 p-2.5 text-xs text-white focus:outline-none focus:border-brand-500"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <label className="text-[11px] font-semibold text-surface-200/80 block">LinkedIn URL</label>
                        <input
                          type="url"
                          value={ceLinkedinUrl}
                          onChange={(e) => setCeLinkedinUrl(e.target.value)}
                          placeholder="https://linkedin.com/in/username"
                          className="w-full rounded-lg bg-surface-900 border border-white/10 p-2.5 text-xs text-white focus:outline-none focus:border-brand-500"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-[11px] font-semibold text-surface-200/80 block">Company News / Context</label>
                        <input
                          type="text"
                          value={ceCompanyInfo}
                          onChange={(e) => setCeCompanyInfo(e.target.value)}
                          placeholder="e.g. Recently raised Series B, launched AI platform"
                          className="w-full rounded-lg bg-surface-900 border border-white/10 p-2.5 text-xs text-white focus:outline-none focus:border-brand-500"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <label className="text-[11px] font-semibold text-surface-200/80 block">Custom Message Notes</label>
                        <input
                          type="text"
                          value={ceAdditionalContext}
                          onChange={(e) => setCeAdditionalContext(e.target.value)}
                          placeholder="e.g. Available immediately, interested in the team's distributed systems focus"
                          className="w-full rounded-lg bg-surface-900 border border-white/10 p-2.5 text-xs text-white focus:outline-none focus:border-brand-500"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Row 5: Outreach Options (Type, Tone, Length) */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    Email Type
                  </label>
                  <select
                    value={ceEmailType}
                    onChange={(e) => setCeEmailType(e.target.value)}
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white focus:outline-none focus:border-brand-500"
                  >
                    <option value="Recruiter Outreach">Recruiter Outreach</option>
                    <option value="Hiring Manager Outreach">Hiring Manager Outreach</option>
                    <option value="General HR Inquiry">General HR Inquiry</option>
                    <option value="Networking / Referral Request">Networking / Referral Request</option>
                    <option value="Job Application Follow-up">Job Application Follow-up</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    Tone
                  </label>
                  <select
                    value={ceTone}
                    onChange={(e) => setCeTone(e.target.value)}
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white focus:outline-none focus:border-brand-500"
                  >
                    <option value="Professional">Professional (Default)</option>
                    <option value="Friendly">Friendly</option>
                    <option value="Confident">Confident</option>
                    <option value="Concise">Concise</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    Length
                  </label>
                  <select
                    value={ceLength}
                    onChange={(e) => setCeLength(e.target.value)}
                    className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white focus:outline-none focus:border-brand-500"
                  >
                    <option value="Short">Short (Concise ~30-45s read)</option>
                    <option value="Standard">Standard (Detailed background)</option>
                  </select>
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={generatingCe || !ceJobTitle.trim() || !ceCompany.trim()}
                  className="px-8 py-3.5 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-lg shadow-brand-600/30 flex items-center gap-2 cursor-pointer"
                >
                  {generatingCe ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span>Generating Grounded Cold Email...</span>
                    </>
                  ) : (
                    <>
                      <span>⚡</span>
                      <span>Generate Cold Email</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Loading Animation */}
          {generatingCe && (
            <AILoadingState
              title="Generating Personalized Cold Email"
              subtitle="Ollama is tailoring outreach based strictly on your verified background and target role..."
              steps={[
                "Reading verified credentials & technical strengths...",
                "Mapping value proposition to target company...",
                "Enforcing anti-hallucination & factual integrity constraints...",
                "Formulating high-converting subject line & crisp call to action...",
              ]}
            />
          )}

          {/* Generated Email Interactive Workspace */}
          {(ceSubject || ceBody) && !generatingCe && (
            <div className="rounded-2xl bg-surface-900 border border-white/10 p-6 sm:p-8 space-y-6 shadow-2xl animate-fade-in">
              {/* Header & Meta */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
                <div className="flex items-center gap-2.5">
                  <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                    📧 {ceEmailType}
                  </span>
                  <span className="text-xs text-surface-200/60">
                    Tone: {ceTone} • Length: {ceLength}
                  </span>
                </div>

                {/* Main Action Bar */}
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleGenerateColdEmail()}
                    className="px-3 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white border border-white/10 text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer"
                    title="Regenerate email with current settings"
                  >
                    <span>🔄</span>
                    <span>Regenerate</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyColdEmail}
                    className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer ${
                      ceCopySuccess
                        ? "bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-600/30"
                        : "bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white border-white/10"
                    }`}
                  >
                    <span>{ceCopySuccess ? "✓" : "📋"}</span>
                    <span>{ceCopySuccess ? "Email copied successfully." : "Copy Email"}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleDownloadColdEmail}
                    className="px-3 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white border border-white/10 text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer"
                    title="Download as text file"
                  >
                    <span>📥</span>
                    <span>Download TXT</span>
                  </button>

                  {generatedCeId && (
                    <button
                      type="button"
                      onClick={handleSaveColdEmailEdits}
                      disabled={savingCeEdits}
                      className="px-3 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white border border-white/10 text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer"
                      title="Save edits to database"
                    >
                      <span>{saveCeSuccess ? "✓" : "💾"}</span>
                      <span>{saveCeSuccess ? "Saved!" : "Save Changes"}</span>
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={handleClearColdEmail}
                    className="px-3 py-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white border border-white/10 text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer"
                    title="Clear editor"
                  >
                    <span>⌫</span>
                    <span>Clear</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleOpenEmailClient}
                    className="px-4 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-all shadow-md shadow-brand-600/30 flex items-center gap-1.5 cursor-pointer"
                    title="Open draft in your local email client (Thunderbird, Outlook, Apple Mail)"
                  >
                    <span>✉️</span>
                    <span>Open in Email Client</span>
                  </button>
                </div>
              </div>

              {/* Recruiter Email Status Notice */}
              {!ceRecruiterEmail.trim() && (
                <div className="p-3 rounded-xl bg-surface-950 border border-amber-500/20 text-xs text-amber-300 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span>⚠️</span>
                    <span>No recruiter email provided. You can add one before opening your email client.</span>
                  </div>
                  <input
                    type="email"
                    value={ceRecruiterEmail}
                    onChange={(e) => setCeRecruiterEmail(e.target.value)}
                    placeholder="Enter email here..."
                    className="w-56 rounded-lg bg-surface-900 border border-white/10 px-2.5 py-1 text-xs text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
              )}

              {/* Subject Line Field + Regenerate Subject Button */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    Subject Line
                  </label>
                  <button
                    type="button"
                    onClick={handleRegenerateSubject}
                    disabled={regeneratingCeSubject}
                    className="text-xs text-brand-400 hover:text-brand-300 font-semibold flex items-center gap-1 cursor-pointer"
                  >
                    <span>↻</span>
                    <span>{regeneratingCeSubject ? "Generating..." : "Regenerate Subject"}</span>
                  </button>
                </div>
                <input
                  type="text"
                  value={ceSubject}
                  onChange={(e) => setCeSubject(e.target.value)}
                  className="w-full rounded-xl bg-surface-950 border border-white/10 p-3 text-xs text-white font-medium focus:outline-none focus:border-brand-500"
                />
              </div>

              {/* Editable Body Textarea */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-surface-200 uppercase tracking-wider block">
                    Email Body
                  </label>
                  <span className="text-[11px] text-surface-200/60 italic">
                    Editable text editor — customize and review before reaching out.
                  </span>
                </div>
                <textarea
                  rows={14}
                  value={ceBody}
                  onChange={(e) => setCeBody(e.target.value)}
                  className="w-full rounded-xl bg-surface-950 border border-white/10 p-5 text-sm text-white focus:outline-none focus:border-brand-500 transition-colors font-sans leading-relaxed resize-y"
                />
              </div>

              <div className="flex items-center justify-between text-[11px] text-surface-200/50 pt-2 border-t border-white/5">
                <span>
                  Privacy notice: CareerCoachAI never sends automatic or bulk emails. All outreach requires manual review and explicit user send.
                </span>
                {saveCeSuccess && (
                  <span className="text-emerald-400 font-semibold">✓ Saved to history</span>
                )}
              </div>
            </div>
          )}

          {/* Cold Email History Modal */}
          {showCeHistoryModal && (
            <div className="fixed inset-0 z-50 overflow-hidden flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
              <div className="w-full max-w-xl rounded-2xl bg-surface-950 border border-white/10 p-6 space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-white">Previous Cold Outreach Emails</h3>
                    <p className="text-[11px] text-surface-200/60 mt-0.5">Your personal saved outreach history</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowCeHistoryModal(false)}
                    className="text-surface-200/60 hover:text-white text-sm cursor-pointer p-1"
                  >
                    ✕
                  </button>
                </div>

                {ceHistory.length === 0 ? (
                  <p className="text-xs text-surface-200/60 py-6 text-center">No saved cold outreach emails yet.</p>
                ) : (
                  <div className="space-y-2 max-h-80 overflow-y-auto pr-1 custom-scrollbar">
                    {ceHistory.map((item) => (
                      <div
                        key={item.id}
                        onClick={() => handleSelectPastColdEmail(item.id)}
                        className="p-3.5 rounded-xl bg-surface-900 hover:bg-surface-800 border border-white/5 cursor-pointer transition-colors flex items-center justify-between gap-3 group"
                      >
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-white truncate">
                            {item.job_title} • {item.company_name}
                          </p>
                          <p className="text-[11px] text-surface-200/60 truncate mt-0.5">
                            {item.subject}
                          </p>
                          <div className="flex items-center gap-2 text-[10px] text-surface-200/40 mt-1">
                            <span>{item.email_type}</span>
                            <span>•</span>
                            <span>{new Date(item.created_at).toLocaleDateString()}</span>
                            {item.recruiter_name && (
                              <>
                                <span>•</span>
                                <span>To: {item.recruiter_name}</span>
                              </>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            onClick={(e) => handleDeleteColdEmail(item.id, e)}
                            className="p-1.5 rounded-lg bg-surface-950 hover:bg-red-500/20 text-surface-200/50 hover:text-red-300 transition-colors text-xs"
                            title="Delete email"
                          >
                            🗑
                          </button>
                          <span className="text-xs text-brand-400 group-hover:text-white font-bold">
                            Open →
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

