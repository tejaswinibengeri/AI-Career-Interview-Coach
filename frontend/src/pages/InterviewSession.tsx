import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { APIError, type InterviewEvaluationData, type InterviewSessionData } from "../lib/api";
import { useVoiceInterview } from "../hooks/useVoiceInterview";
import AILoadingState from "../components/ui/AILoadingState";

export default function InterviewSession() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<InterviewSessionData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Active answer state
  const [userAnswer, setUserAnswer] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  // Voice Mode state
  const [voiceModeEnabled, setVoiceModeEnabled] = useState<boolean>(false);
  const {
    isVoiceSupported,
    isSpeaking,
    isListening,
    voiceError,
    setVoiceError,
    speakText,
    stopSpeaking,
    startListening,
    stopListening,
    cancelVoice,
  } = useVoiceInterview();


  // Active evaluation response for current step feedback
  const [lastEvaluation, setLastEvaluation] = useState<InterviewEvaluationData | null>(null);
  const [showIdealAnswer, setShowIdealAnswer] = useState<boolean>(false);

  // Live timer for current question
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  useEffect(() => {
    setElapsedSeconds(0);
    const interval = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [session?.current_question_index]);

  const sessionId = id ? parseInt(id, 10) : NaN;

  // Fetch session state by ID
  const fetchSession = async () => {
    if (isNaN(sessionId)) {
      setError("Invalid session ID.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.getInterviewSession(sessionId);
      if (res.data) {
        setSession(res.data);
        if (res.data.status === "completed") {
          navigate(`/interview/${sessionId}/results`, { replace: true });
        }
      } else {
        setError("Failed to load interview session.");
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

  useEffect(() => {
    fetchSession();
  }, [id]);

  const currentQ = session?.current_question;

  // Auto-speak question when voice mode is ON and new question appears
  useEffect(() => {
    if (voiceModeEnabled && currentQ && !lastEvaluation) {
      speakText(currentQ.question_text);
    }
    return () => {
      stopSpeaking();
    };
  }, [currentQ?.id, voiceModeEnabled, lastEvaluation]);

  const handleSubmitAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentQ || !session) return;

    if (isListening) {
      stopListening();
    }
    stopSpeaking();

    if (!userAnswer.trim() || userAnswer.trim().length < 5) {
      setEvalError("Please speak or type a substantive answer before submitting.");
      return;
    }

    setSubmitting(true);
    setEvalError(null);

    try {
      const res = await api.submitInterviewAnswer(session.id, currentQ.id, userAnswer.trim());
      if (res.data) {
        setSession(res.data);
        const justAnswered = res.data.questions.find((q) => q.id === currentQ.id);
        if (justAnswered?.evaluation) {
          setLastEvaluation(justAnswered.evaluation);
          if (voiceModeEnabled) {
            speakText(`Score: ${justAnswered.evaluation.overall_score} percent. ${justAnswered.evaluation.feedback}`);
          }
        } else {
          setLastEvaluation(null);
        }

        setUserAnswer("");

        if (res.data.status === "completed") {
          setTimeout(() => {
            navigate(`/interview/${session.id}/results`);
          }, 4000);
        }
      }
    } catch (err) {
      if (err instanceof APIError) {
        setEvalError(err.message);
      } else {
        setEvalError("Failed to evaluate answer. Please verify Ollama is running and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextQuestion = () => {
    cancelVoice();
    setLastEvaluation(null);
    setShowIdealAnswer(false);
    if (session && session.status === "completed") {
      navigate(`/interview/${session.id}/results`);
    }
  };

  const handleToggleVoiceRecording = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening((text) => {
        setUserAnswer(text);
      });
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

  if (error || !session) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-400 mx-auto flex items-center justify-center">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        </div>
        <h2 className="text-lg font-bold text-white">Interview Session Error</h2>
        <p className="text-xs text-surface-200/70">{error || "Session not found."}</p>
        <button
          onClick={() => navigate("/interview")}
          className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors cursor-pointer"
        >
          Back to Interview Room
        </button>
      </div>
    );
  }

  const progressPercent = Math.round(
    (session.current_question_index / session.total_questions) * 100
  );

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Session Progress Header */}
      <div className="bg-surface-900 border border-white/10 rounded-2xl p-5 sm:p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                cancelVoice();
                navigate("/interview");
              }}
              className="p-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white transition-colors cursor-pointer"
              title="Return to Interview Setup"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
            </button>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white">{session.role} Interview</h1>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    session.difficulty === "Hard"
                      ? "bg-red-500/15 text-red-300 border border-red-500/30"
                      : session.difficulty === "Medium"
                      ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                      : "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                  }`}
                >
                  {session.difficulty}
                </span>
              </div>
              <p className="text-xs text-surface-200/60 mt-0.5">
                Question {Math.min(session.current_question_index + 1, session.total_questions)} of {session.total_questions}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Live Question Timer Badge */}
            <div className="px-3 py-1.5 rounded-xl bg-surface-800 border border-white/10 text-brand-300 font-mono text-xs font-bold flex items-center gap-1.5 shadow-inner">
              <span>⏱️</span>
              <span>
                {Math.floor(elapsedSeconds / 60)
                  .toString()
                  .padStart(2, "0")}
                :{(elapsedSeconds % 60).toString().padStart(2, "0")}
              </span>
            </div>

            {/* Voice Mode Toggle Switch */}
            {isVoiceSupported ? (
              <button
                type="button"
                onClick={() => {
                  const nextVal = !voiceModeEnabled;
                  setVoiceModeEnabled(nextVal);
                  if (!nextVal) cancelVoice();
                }}
                className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  voiceModeEnabled
                    ? "bg-purple-600/20 text-purple-300 border-purple-500/40 shadow-md shadow-purple-600/20"
                    : "bg-surface-800 text-surface-200/60 border-white/10 hover:text-white"
                }`}
              >
                <span>🎙️ Voice Mode: {voiceModeEnabled ? "ON" : "OFF"}</span>
              </button>
            ) : (
              <span className="text-[11px] text-surface-200/40 italic">Voice Mode Unsupported in this browser</span>
            )}

            <div className="flex items-center gap-3">
              <span className="text-xs font-medium text-surface-200/70">{progressPercent}%</span>
              <div className="w-24 h-2.5 rounded-full bg-surface-800 overflow-hidden border border-white/5">
                <div
                  className="h-full bg-gradient-to-r from-brand-500 to-emerald-400 transition-all duration-500"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {submitting ? (
        <AILoadingState
          title="Ollama AI Evaluating Answer"
          subtitle="Analyzing technical correctness, communication clarity, and candidate depth..."
          steps={[
            "Evaluating response against optimal scoring benchmarks...",
            "Computing communication clarity and technical accuracy scores...",
            "Synthesizing constructive feedback and key improvements...",
            "Formulating ideal sample answer...",
          ]}
        />
      ) : lastEvaluation ? (
        /* Evaluation View */
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl animate-fade-in">

          <div className="flex items-center justify-between border-b border-white/5 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-bold text-lg">
                ✓
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Answer Evaluated via Ollama AI</h2>
                <p className="text-xs text-surface-200/60">Rubric breakdown for Question #{session.current_question_index}</p>
              </div>
            </div>

            <div className="text-right">
              <span className="text-[11px] text-surface-200/60 uppercase tracking-wider block">Score</span>
              <span className="text-2xl font-extrabold text-emerald-400">{lastEvaluation.overall_score}%</span>
            </div>
          </div>

          {/* 6 Rubric Metrics Grid */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-surface-200 uppercase tracking-wider">Evaluation Rubric</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { name: "Technical Correctness", score: lastEvaluation.technical_correctness },
                { name: "Relevance", score: lastEvaluation.relevance },
                { name: "Completeness", score: lastEvaluation.completeness },
                { name: "Communication", score: lastEvaluation.communication },
                { name: "Structure", score: lastEvaluation.structure },
                { name: "Clarity", score: lastEvaluation.clarity },
              ].map((m) => (
                <div key={m.name} className="p-3 rounded-xl bg-surface-800/60 border border-white/5 space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-surface-200/70 font-medium truncate">{m.name}</span>
                    <span className="font-bold text-white">{m.score}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-surface-700 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        m.score >= 80 ? "bg-emerald-400" : m.score >= 60 ? "bg-amber-400" : "bg-red-400"
                      }`}
                      style={{ width: `${m.score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Detailed Feedback & Analysis */}
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-brand-500/10 border border-brand-500/20 space-y-1">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-brand-300 uppercase tracking-wider">AI Assessor Feedback</h4>
                {voiceModeEnabled && (
                  <button
                    type="button"
                    onClick={() => speakText(lastEvaluation.feedback)}
                    className="text-xs text-brand-300 hover:text-white font-semibold cursor-pointer"
                  >
                    🔊 Read Feedback
                  </button>
                )}
              </div>
              <p className="text-sm text-surface-200 leading-relaxed">{lastEvaluation.feedback}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {lastEvaluation.strengths && lastEvaluation.strengths.length > 0 && (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-2">
                  <h4 className="text-xs font-bold text-emerald-300 uppercase tracking-wider">👍 Key Strengths</h4>
                  <ul className="space-y-1 text-xs text-surface-200/90 list-disc list-inside">
                    {lastEvaluation.strengths.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}

              {lastEvaluation.improvements && lastEvaluation.improvements.length > 0 && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 space-y-2">
                  <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider">💡 Areas for Improvement</h4>
                  <ul className="space-y-1 text-xs text-surface-200/90 list-disc list-inside">
                    {lastEvaluation.improvements.map((imp, i) => (
                      <li key={i}>{imp}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Ideal Answer Dropdown */}
            {lastEvaluation.ideal_answer && (
              <div className="border border-white/10 rounded-xl overflow-hidden bg-surface-800/40">
                <button
                  onClick={() => setShowIdealAnswer(!showIdealAnswer)}
                  className="w-full px-4 py-3 text-left font-semibold text-xs text-surface-200 hover:text-white flex items-center justify-between transition-colors cursor-pointer"
                >
                  <span>View Sample Ideal Answer Guide</span>
                  <span>{showIdealAnswer ? "▲ Hide" : "▼ Show"}</span>
                </button>
                {showIdealAnswer && (
                  <div className="p-4 border-t border-white/5 bg-surface-950/60 text-xs text-surface-200/90 leading-relaxed font-mono whitespace-pre-wrap">
                    {lastEvaluation.ideal_answer}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="pt-2">
            <button
              onClick={handleNextQuestion}
              className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-bold text-sm shadow-xl shadow-brand-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              {session.status === "completed" ? (
                <span>View Final Performance Report 🎉</span>
              ) : (
                <span>Next Question ({session.current_question_index + 1}/{session.total_questions}) →</span>
              )}
            </button>
          </div>
        </div>
      ) : currentQ ? (
        /* Active Question Display */
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl">
          {/* Question Header & Voice Controls */}
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-lg bg-brand-500/15 border border-brand-500/30 text-brand-300 text-xs font-bold">
                Question {currentQ.question_order + 1}
              </span>
              <span className="px-3 py-1 rounded-lg bg-surface-800 border border-white/10 text-surface-200 text-xs font-medium">
                {currentQ.category}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {/* TTS Read Aloud Button */}
              <button
                type="button"
                onClick={() => {
                  if (isSpeaking) stopSpeaking();
                  else speakText(currentQ.question_text);
                }}
                className={`px-3 py-1 rounded-lg border text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                  isSpeaking
                    ? "bg-purple-600/30 text-purple-300 border-purple-500/40 animate-pulse"
                    : "bg-surface-800 text-surface-200/80 border-white/10 hover:text-white"
                }`}
              >
                <span>{isSpeaking ? "🔊 Speaking..." : "🔊 Read Aloud"}</span>
              </button>
            </div>
          </div>

          {/* Question Text Prompt */}
          <div className="p-5 rounded-xl bg-surface-800/80 border border-white/10 space-y-2">
            <h2 className="text-lg sm:text-xl font-bold text-white leading-snug">
              {currentQ.question_text}
            </h2>
            <details className="group pt-2 border-t border-white/5">
              <summary className="cursor-pointer text-xs font-semibold text-brand-300 hover:text-brand-200 inline-flex items-center gap-1.5 transition-colors">
                <span>💡 Need a hint on how to structure your response?</span>
              </summary>
              <div className="mt-2 p-3 rounded-lg bg-surface-950/80 border border-brand-500/20 text-xs text-surface-200 space-y-1 animate-fade-in">
                <span className="font-bold text-brand-400 block text-[11px] uppercase tracking-wider">STAR & Technical Framework</span>
                <p>1. State the core concept or architectural principle clearly.</p>
                <p>2. Give a practical real-world scenario or code design pattern.</p>
                <p>3. Explain trade-offs, edge cases, and performance considerations.</p>
              </div>
            </details>

          </div>

          {/* Voice Error & Mic Warnings */}
          {voiceError && (
            <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex justify-between items-center">
              <span>⚠️ {voiceError}</span>
              <button onClick={() => setVoiceError(null)} className="text-amber-400 font-bold hover:text-amber-200 cursor-pointer">
                &times;
              </button>
            </div>
          )}

          {evalError && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs space-y-1">
              <span className="font-bold block">Ollama AI Evaluation Issue:</span>
              <p>{evalError}</p>
            </div>
          )}

          {/* User Answer Controls & Speech Input */}
          <form onSubmit={handleSubmitAnswer} className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <div className="flex items-center gap-2">
                  <label htmlFor="user-answer-textarea" className="font-semibold text-surface-200 uppercase tracking-wider">
                    Candidate Answer
                  </label>
                  {isListening && (
                    <span className="px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/30 text-[10px] font-extrabold animate-pulse">
                      🔴 Live Voice Transcribing...
                    </span>
                  )}
                </div>

                {/* Microphone Record Button */}
                <button
                  type="button"
                  onClick={handleToggleVoiceRecording}
                  disabled={!isVoiceSupported}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-extrabold transition-all cursor-pointer flex items-center gap-1.5 ${
                    isListening
                      ? "bg-red-600 text-white border-red-400 shadow-lg shadow-red-600/30 animate-pulse"
                      : "bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border-purple-500/40"
                  }`}
                >
                  <span>{isListening ? "⏹️ Stop Recording" : "🎙️ Speak Answer (STT)"}</span>
                </button>
              </div>

              <textarea
                id="user-answer-textarea"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder={
                  isListening
                    ? "Speak into your microphone now... Your spoken response will be transcribed here live."
                    : "Type or speak your candidate response here..."
                }
                rows={8}
                className={`w-full p-4 rounded-xl bg-surface-800 border text-white placeholder-surface-200/40 text-sm leading-relaxed focus:outline-none transition-all font-sans ${
                  isListening
                    ? "border-red-500/60 ring-1 ring-red-500/60"
                    : "border-white/10 focus:border-brand-500"
                }`}
                required
              />
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
              <div className="text-[11px] text-surface-200/50 hidden sm:block">
                Voice input is optional. You may type, speak, or edit text before submitting.
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <button
                  type="button"
                  disabled={submitting}
                  onClick={async () => {
                    setUserAnswer("I would like to skip this question and review the sample answer.");
                    // auto submit skip message
                    try {
                      setSubmitting(true);
                      setEvalError(null);
                      const res = await api.submitInterviewAnswer(
                        sessionId,
                        currentQ.id,
                        "Skipped by candidate. Please provide feedback and ideal answer guide."
                      );
                      if (res.data) {
                        setSession(res.data);
                        const justAnswered = res.data.questions.find((q) => q.id === currentQ.id);
                        if (justAnswered?.evaluation) {
                          setLastEvaluation(justAnswered.evaluation);
                          if (voiceModeEnabled && justAnswered.evaluation.feedback) {
                            speakText(justAnswered.evaluation.feedback);
                          }
                        }
                        setUserAnswer("");
                      }
                    } catch (err) {
                      if (err instanceof APIError) {
                        setEvalError(err.message);
                      }
                    } finally {
                      setSubmitting(false);
                    }
                  }}
                  className="py-3 px-4 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-300 hover:text-white font-semibold text-xs border border-white/10 transition-all cursor-pointer"
                >
                  Skip Question ↷
                </button>

                <button
                  type="submit"
                  disabled={submitting || !userAnswer.trim()}
                  id="submit-answer-btn"
                  className="flex-1 sm:flex-none py-3 px-6 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-bold text-sm shadow-xl shadow-brand-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {submitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Evaluating Answer...</span>
                    </>
                  ) : (
                    <>
                      <span>Submit Answer for AI Evaluation</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      ) : (
        <div className="bg-surface-900 border border-white/10 rounded-2xl p-8 text-center space-y-4">
          <h2 className="text-xl font-bold text-white">All questions answered!</h2>
          <p className="text-sm text-surface-200/70">Your mock interview evaluation is ready.</p>
          <button
            onClick={() => navigate(`/interview/${session.id}/results`)}
            className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-sm transition-colors cursor-pointer"
          >
            View Final Performance Report 📊
          </button>
        </div>
      )}
    </div>
  );
}
