import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, {
  type DailyTrainingViewData,
  type PersonalTrainerSettingsData,
  type TrainingPlanData,
  type TrainingTaskData,
} from "../lib/api";

type GoalDimension = "skill" | "role" | "company";

export default function PersonalTrainer() {
  // Global loading and plan state
  const [loading, setLoading] = useState(true);
  const [investigating, setInvestigating] = useState(false);
  const [investigateStep, setInvestigateStep] = useState(0);
  const [activePlan, setActivePlan] = useState<TrainingPlanData | null>(null);
  const [dailyView, setDailyView] = useState<DailyTrainingViewData | null>(null);
  const [activeTab, setActiveTab] = useState<"daily" | "roadmap">("daily");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Setup Form State
  const [goalDimensions, setGoalDimensions] = useState<GoalDimension[]>(["role"]);
  const [targetRole, setTargetRole] = useState("");
  const [targetSkill, setTargetSkill] = useState("");
  const [targetCompany, setTargetCompany] = useState("");
  const [currentSkills, setCurrentSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState("");
  const [loadingResumeSkills, setLoadingResumeSkills] = useState(false);
  const [experienceLevel, setExperienceLevel] = useState("Intermediate");
  const [dailyHours, setDailyHours] = useState<number>(2.0);
  const [customHours, setCustomHours] = useState("");
  const [targetDeadline, setTargetDeadline] = useState("");
  const [learningPreference, setLearningPreference] = useState("Balanced");

  // Selected Day in Daily view
  const [selectedDayNumber, setSelectedDayNumber] = useState<number>(1);

  // Note Modal State
  const [editingTask, setEditingTask] = useState<TrainingTaskData | null>(null);
  const [taskNote, setTaskNote] = useState("");
  const [savingTask, setSavingTask] = useState(false);

  // Confidence Rating State
  const [confidenceRating, setConfidenceRating] = useState<number | null>(null);
  const [ratingFeedback, setRatingFeedback] = useState("");
  const [submittingRating, setSubmittingRating] = useState(false);
  const [reviewRecommendation, setReviewRecommendation] = useState<string | null>(null);

  // Notification Settings Modal
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [trainerSettings, setTrainerSettings] = useState<PersonalTrainerSettingsData>({
    notifications_enabled: false,
    preferred_time: "09:00",
    notification_channel: "email",
    webhook_configured: false,
  });
  const [savingSettings, setSavingSettings] = useState(false);
  const [triggeringWebhook, setTriggeringWebhook] = useState(false);
  const [webhookResult, setWebhookResult] = useState<{ success: boolean; message: string } | null>(null);

  // Reschedule Dialog State
  const [rescheduleOpen, setRescheduleOpen] = useState(false);
  const [rescheduleHours, setRescheduleHours] = useState("1.0");
  const [rescheduling, setRescheduling] = useState(false);

  // Focus Timer State
  const [activeTimerTask, setActiveTimerTask] = useState<TrainingTaskData | null>(null);
  const [timerSecondsLeft, setTimerSecondsLeft] = useState<number>(0);
  const [timerRunning, setTimerRunning] = useState(false);

  // Investigation step messages
  const investigateMessages = [
    "Investigating your goal...",
    "Analyzing required skills...",
    "Building learning dependencies...",
    "Creating your personalized training plan...",
    "Calculating your daily schedule...",
  ];

  // Load active plan on mount
  useEffect(() => {
    fetchActivePlan();
    fetchTrainerSettings();
  }, []);

  // Timer countdown hook
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (timerRunning && timerSecondsLeft > 0) {
      interval = setInterval(() => {
        setTimerSecondsLeft((prev) => {
          if (prev <= 1) {
            setTimerRunning(false);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [timerRunning, timerSecondsLeft]);

  const fetchActivePlan = async () => {
    try {
      setLoading(true);
      const res = await api.getActiveTrainingPlan();
      if (res.data) {
        setActivePlan(res.data);
        await fetchDailyView(1);
      } else {
        setActivePlan(null);
      }
    } catch {
      setActivePlan(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchDailyView = async (dayNum?: number) => {
    try {
      const res = await api.getDailyTraining(dayNum);
      if (res.data) {
        setDailyView(res.data);
        setSelectedDayNumber(res.data.day_number);
        setConfidenceRating(res.data.current_day.confidence_rating || null);
        setReviewRecommendation(res.data.current_day.ai_review_recommendation || null);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Could not load daily training view.");
    }
  };

  const fetchTrainerSettings = async () => {
    try {
      const res = await api.getTrainerSettings();
      if (res.data) {
        setTrainerSettings(res.data);
      }
    } catch {
      // ignore
    }
  };

  const toggleDimension = (dim: GoalDimension) => {
    if (goalDimensions.includes(dim)) {
      if (goalDimensions.length === 1) return; // keep at least one
      setGoalDimensions(goalDimensions.filter((d) => d !== dim));
    } else {
      setGoalDimensions([...goalDimensions, dim]);
    }
  };

  const handleAddSkill = () => {
    const trimmed = skillInput.trim();
    if (trimmed && !currentSkills.includes(trimmed)) {
      setCurrentSkills([...currentSkills, trimmed]);
      setSkillInput("");
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setCurrentSkills(currentSkills.filter((s) => s !== skillToRemove));
  };

  const handleUseResumeSkills = async () => {
    try {
      setLoadingResumeSkills(true);
      setErrorMessage(null);
      const res = await api.getTrainerResumeSkills();
      if (res.data && res.data.skills.length > 0) {
        // Merge without duplicates
        const combined = Array.from(new Set([...currentSkills, ...res.data.skills]));
        setCurrentSkills(combined);
        setSuccessMessage(`Loaded ${res.data.skills.length} verified skills from your existing resume!`);
      } else {
        setErrorMessage("No extracted resume skills found. You can upload a resume in Resume Studio or enter skills manually.");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load resume skills.");
    } finally {
      setLoadingResumeSkills(false);
    }
  };

  const handleInvestigate = async () => {
    // Validation
    if (goalDimensions.includes("role") && !targetRole.trim()) {
      setErrorMessage("Please enter your target role.");
      return;
    }
    if (goalDimensions.includes("skill") && !targetSkill.trim()) {
      setErrorMessage("Please enter your target skill.");
      return;
    }
    if (goalDimensions.includes("company") && !targetCompany.trim()) {
      setErrorMessage("Please enter your target company.");
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);
    setInvestigating(true);
    setInvestigateStep(0);

    // Animate through step messages
    const stepInterval = setInterval(() => {
      setInvestigateStep((prev) => (prev < investigateMessages.length - 1 ? prev + 1 : prev));
    }, 1200);

    try {
      const payloadHours = customHours ? parseFloat(customHours) || dailyHours : dailyHours;
      const res = await api.investigateGoal({
        goal_dimensions: goalDimensions,
        target_role: goalDimensions.includes("role") ? targetRole.trim() : undefined,
        target_skill: goalDimensions.includes("skill") ? targetSkill.trim() : undefined,
        target_company: goalDimensions.includes("company") ? targetCompany.trim() : undefined,
        current_skills: currentSkills,
        experience_level: experienceLevel,
        daily_hours: payloadHours,
        target_deadline: targetDeadline || undefined,
        learning_preference: learningPreference,
      });

      clearInterval(stepInterval);
      if (res.data) {
        setActivePlan(res.data);
        await fetchDailyView(1);
        setSuccessMessage("Your personalized training plan has been created!");
      }
    } catch (err: any) {
      clearInterval(stepInterval);
      setErrorMessage(err.message || "Failed to generate training plan. Please check your inputs and try again.");
    } finally {
      setInvestigating(false);
    }
  };

  const handleToggleTaskStatus = async (task: TrainingTaskData) => {
    const nextStatus = task.status === "completed" ? "not_started" : "completed";
    try {
      await api.updateTrainingTask(task.id, { status: nextStatus });
      // Refresh current day view and active plan
      await fetchDailyView(selectedDayNumber);
      const planRes = await api.getActiveTrainingPlan();
      if (planRes.data) setActivePlan(planRes.data);
    } catch (err: any) {
      setErrorMessage(err.message || "Could not update task.");
    }
  };

  const handleTaskAction = async (taskId: number, newStatus: string) => {
    try {
      await api.updateTrainingTask(taskId, { status: newStatus });
      await fetchDailyView(selectedDayNumber);
      const planRes = await api.getActiveTrainingPlan();
      if (planRes.data) setActivePlan(planRes.data);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to update task.");
    }
  };

  const handleSaveNote = async () => {
    if (!editingTask) return;
    try {
      setSavingTask(true);
      await api.updateTrainingTask(editingTask.id, {
        status: editingTask.status,
        notes: taskNote,
      });
      setEditingTask(null);
      await fetchDailyView(selectedDayNumber);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to save note.");
    } finally {
      setSavingTask(false);
    }
  };

  const handleQuickReschedule = async () => {
    const hours = parseFloat(rescheduleHours);
    if (isNaN(hours) || hours <= 0) return;
    try {
      setRescheduling(true);
      const res = await api.rescheduleTodayWorkload(hours);
      if (res.data) {
        setDailyView(res.data);
        setSuccessMessage("Your plan has been adjusted based on today's availability.");
        setRescheduleOpen(false);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to reschedule today's workload.");
    } finally {
      setRescheduling(false);
    }
  };

  const handleSubmitConfidence = async (rating: number) => {
    if (!dailyView) return;
    try {
      setSubmittingRating(true);
      const res = await api.submitDayReview(dailyView.current_day.id, rating, ratingFeedback);
      if (res.data) {
        setConfidenceRating(rating);
        setReviewRecommendation(res.data.ai_review_recommendation);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to submit confidence review.");
    } finally {
      setSubmittingRating(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setSavingSettings(true);
      const res = await api.updateTrainerSettings({
        notifications_enabled: trainerSettings.notifications_enabled,
        preferred_time: trainerSettings.preferred_time,
        notification_channel: trainerSettings.notification_channel,
      });
      if (res.data) {
        setTrainerSettings(res.data);
        setSuccessMessage("Notification preferences saved.");
        setSettingsOpen(false);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to save settings.");
    } finally {
      setSavingSettings(false);
    }
  };

  const handleTriggerWebhook = async () => {
    try {
      setTriggeringWebhook(true);
      setWebhookResult(null);
      const res = await api.triggerTrainerWebhook();
      if (res.data) {
        setWebhookResult({
          success: res.data.success,
          message: res.data.message,
        });
      }
    } catch (err: any) {
      setWebhookResult({
        success: false,
        message: err.message || "Failed to trigger n8n notification.",
      });
    } finally {
      setTriggeringWebhook(false);
    }
  };

  const startTaskTimer = (task: TrainingTaskData) => {
    setActiveTimerTask(task);
    setTimerSecondsLeft(task.estimated_minutes * 60);
    setTimerRunning(true);
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-brand-500/20 border border-brand-500/40 flex items-center justify-center animate-spin">
          <span className="text-2xl">🧠</span>
        </div>
        <p className="text-sm font-semibold text-surface-200/70 animate-pulse">
          Loading your Personal Trainer workspace...
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* GLOBAL TOAST ALERTS */}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-red-950/70 border border-red-500/40 text-red-200 text-sm flex items-center justify-between shadow-lg shadow-red-950/30 animate-fade-in">
          <div className="flex items-center gap-3">
            <span className="text-lg">⚠️</span>
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="p-1 hover:bg-white/10 rounded-lg text-red-300"
          >
            ✕
          </button>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-2xl bg-emerald-950/70 border border-emerald-500/40 text-emerald-200 text-sm flex items-center justify-between shadow-lg shadow-emerald-950/30 animate-fade-in">
          <div className="flex items-center gap-3">
            <span className="text-lg">✅</span>
            <span>{successMessage}</span>
          </div>
          <button
            onClick={() => setSuccessMessage(null)}
            className="p-1 hover:bg-white/10 rounded-lg text-emerald-300"
          >
            ✕
          </button>
        </div>
      )}

      {/* ==================================================================== */}
      {/* 1. SETUP / INVESTIGATION VIEW (Shown when no active plan exists)       */}
      {/* ==================================================================== */}
      {!activePlan ? (
        <div className="space-y-8 animate-fade-in">
          {/* Header Banner */}
          <div className="p-8 rounded-3xl bg-gradient-to-br from-surface-900/90 via-surface-950 to-brand-950/40 border border-white/10 shadow-2xl relative overflow-hidden">
            <div className="absolute -right-16 -top-16 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
            <div className="max-w-3xl space-y-3">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-500/20 border border-brand-500/40 text-brand-300 text-xs font-black tracking-wider uppercase">
                <span>🧠</span>
                <span>AI Personal Learning Manager</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                Personal Trainer
              </h1>
              <p className="text-lg font-semibold text-brand-300">
                Build a personalized path to your goal.
              </p>
              <p className="text-sm text-surface-200/70 leading-relaxed">
                Tell us what you want to achieve. AI will investigate your goal, identify prerequisites and missing skills,
                and engineer a detailed day-by-day training schedule tailored strictly to your available daily study hours.
              </p>
            </div>
          </div>

          {/* Configuration Form Card */}
          <div className="p-6 sm:p-8 rounded-3xl bg-surface-900/80 border border-white/10 shadow-xl space-y-8">
            {/* Step 1: Goal Dimensions */}
            <div className="space-y-3">
              <label className="text-xs font-bold text-white uppercase tracking-wider block">
                1. Select Goal Dimension(s)
              </label>
              <div className="flex flex-wrap gap-2.5">
                {(["skill", "role", "company"] as GoalDimension[]).map((dim) => {
                  const isSelected = goalDimensions.includes(dim);
                  return (
                    <button
                      key={dim}
                      type="button"
                      onClick={() => toggleDimension(dim)}
                      className={`px-4 py-2.5 rounded-2xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
                        isSelected
                          ? "bg-brand-600 text-white shadow-md shadow-brand-600/30 border border-brand-400/40"
                          : "bg-surface-800/80 hover:bg-surface-800 text-surface-200/80 border border-white/10"
                      }`}
                    >
                      <span className="text-sm">
                        {dim === "skill" ? "🎯" : dim === "role" ? "💼" : "🏢"}
                      </span>
                      <span className="capitalize">{dim}</span>
                      {isSelected && <span>✓</span>}
                    </button>
                  );
                })}
              </div>
              <p className="text-[11px] text-surface-200/50">
                Select one or combine multiple dimensions (e.g. Role + Company, Skill + Role + Company).
              </p>
            </div>

            {/* Step 2: Dynamic Dimension Target Inputs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {goalDimensions.includes("skill") && (
                <div className="space-y-2 animate-fade-in">
                  <label className="text-xs font-bold text-white block">
                    Target Skill <span className="text-brand-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={targetSkill}
                    onChange={(e) => setTargetSkill(e.target.value)}
                    placeholder="e.g., Python, DSA, Machine Learning, SQL, System Design"
                    className="w-full px-4 py-3 rounded-2xl bg-surface-950 border border-white/10 text-white text-xs placeholder-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors"
                  />
                </div>
              )}

              {goalDimensions.includes("role") && (
                <div className="space-y-2 animate-fade-in">
                  <label className="text-xs font-bold text-white block">
                    Target Role <span className="text-brand-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    placeholder="e.g., AI Engineer, Python Developer, Data Scientist"
                    className="w-full px-4 py-3 rounded-2xl bg-surface-950 border border-white/10 text-white text-xs placeholder-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors"
                  />
                </div>
              )}

              {goalDimensions.includes("company") && (
                <div className="space-y-2 animate-fade-in">
                  <label className="text-xs font-bold text-white block">
                    Target Company <span className="text-brand-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={targetCompany}
                    onChange={(e) => setTargetCompany(e.target.value)}
                    placeholder="e.g., Google, Microsoft, Amazon, TCS"
                    className="w-full px-4 py-3 rounded-2xl bg-surface-950 border border-white/10 text-white text-xs placeholder-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors"
                  />
                </div>
              )}
            </div>

            {/* Step 3: Current Skills & Resume Integration */}
            <div className="space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <label className="text-xs font-bold text-white uppercase tracking-wider block">
                  2. Current Skills
                </label>
                <button
                  type="button"
                  onClick={handleUseResumeSkills}
                  disabled={loadingResumeSkills}
                  className="px-3 py-1.5 rounded-xl bg-brand-500/20 hover:bg-brand-500/30 border border-brand-500/40 text-brand-300 text-xs font-bold transition-all flex items-center gap-1.5 self-start cursor-pointer"
                >
                  <span>📁</span>
                  <span>{loadingResumeSkills ? "Extracting..." : "Use my Resume"}</span>
                </button>
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddSkill())}
                  placeholder="Type a skill and press Enter (e.g. Python, SQL, Git)..."
                  className="flex-1 px-4 py-3 rounded-2xl bg-surface-950 border border-white/10 text-white text-xs placeholder-surface-200/40 focus:outline-none focus:border-brand-500 transition-colors"
                />
                <button
                  type="button"
                  onClick={handleAddSkill}
                  className="px-5 py-3 rounded-2xl bg-surface-800 hover:bg-surface-700 text-white text-xs font-bold border border-white/10 cursor-pointer"
                >
                  Add
                </button>
              </div>

              {currentSkills.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {currentSkills.map((sk) => (
                    <span
                      key={sk}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-800 text-surface-200 border border-white/10 text-xs font-semibold"
                    >
                      <span>{sk}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveSkill(sk)}
                        className="hover:text-red-400 cursor-pointer"
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Step 4: Level, Daily Commitment & Preferences */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Experience Level */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-white block">
                  3. Experience Level
                </label>
                <select
                  value={experienceLevel}
                  onChange={(e) => setExperienceLevel(e.target.value)}
                  className="w-full px-4 py-3 rounded-2xl bg-surface-950 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500 cursor-pointer"
                >
                  <option value="Beginner">Beginner</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Advanced">Advanced</option>
                  <option value="AI Estimate">Let AI estimate my level</option>
                </select>
              </div>

              {/* Daily Available Hours */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-white block">
                  4. Daily Study Availability
                </label>
                <select
                  value={dailyHours}
                  onChange={(e) => {
                    setDailyHours(parseFloat(e.target.value));
                    setCustomHours("");
                  }}
                  className="w-full px-4 py-3 rounded-2xl bg-surface-950 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500 cursor-pointer"
                >
                  <option value={0.5}>30 minutes / day</option>
                  <option value={1.0}>1 hour / day</option>
                  <option value={2.0}>2 hours / day</option>
                  <option value={3.0}>3 hours / day</option>
                  <option value={4.0}>4 hours / day</option>
                  <option value={5.0}>5+ hours / day</option>
                </select>
              </div>

              {/* Learning Preference */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-white block">
                  5. Learning Preference
                </label>
                <select
                  value={learningPreference}
                  onChange={(e) => setLearningPreference(e.target.value)}
                  className="w-full px-4 py-3 rounded-2xl bg-surface-950 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500 cursor-pointer"
                >
                  <option value="Balanced">Balanced (Theory & Practice)</option>
                  <option value="Theory + Practice">Theory + Practice</option>
                  <option value="Mostly Practical">Mostly Practical</option>
                  <option value="Project Based">Project Based</option>
                  <option value="Interview Focused">Interview Focused</option>
                </select>
              </div>
            </div>

            {/* Optional Deadline */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-white block">
                Target Deadline <span className="text-surface-200/40">(Optional)</span>
              </label>
              <input
                type="date"
                value={targetDeadline}
                onChange={(e) => setTargetDeadline(e.target.value)}
                className="w-full sm:w-64 px-4 py-3 rounded-2xl bg-surface-950 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500 cursor-pointer"
              />
              <p className="text-[11px] text-surface-200/50">
                If omitted, AI calculates a realistic duration based on your skill complexity and available hours.
              </p>
            </div>

            {/* CTA Button */}
            <div className="pt-4 border-t border-white/10">
              <button
                type="button"
                onClick={handleInvestigate}
                disabled={investigating}
                className="w-full py-4 rounded-2xl bg-gradient-to-r from-brand-600 via-brand-500 to-indigo-600 hover:opacity-95 text-white font-extrabold text-sm tracking-wide shadow-xl shadow-brand-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {investigating ? (
                  <>
                    <span className="w-5 h-5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                    <span>{investigateMessages[investigateStep]}</span>
                  </>
                ) : (
                  <>
                    <span>🔍</span>
                    <span>INVESTIGATE MY GOAL</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* ==================================================================== */
        /* 2. ACTIVE TRAINING DASHBOARD                                         */
        /* ==================================================================== */
        <div className="space-y-8 animate-fade-in">
          {/* Plan Overview Card */}
          <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-surface-900/95 via-surface-950 to-brand-950/40 border border-white/10 shadow-2xl relative overflow-hidden space-y-6">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2.5 py-1 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/40 text-[10px] font-black uppercase tracking-wider">
                    Active Plan
                  </span>
                  {activePlan.target_company && (
                    <span className="px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 text-[10px] font-bold">
                      🏢 {activePlan.target_company}
                    </span>
                  )}
                  {activePlan.target_role && (
                    <span className="px-2.5 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/40 text-[10px] font-bold">
                      💼 {activePlan.target_role}
                    </span>
                  )}
                </div>
                <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                  {activePlan.title}
                </h1>
                <p className="text-xs text-surface-200/70">
                  Level: <span className="text-white font-bold">{activePlan.experience_level}</span> • Preference: <span className="text-white font-bold">{activePlan.learning_preference}</span>
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2.5 flex-wrap">
                <button
                  type="button"
                  onClick={() => setRescheduleOpen(true)}
                  className="px-3.5 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white border border-white/10 text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
                  title="Adjust workload if you have less time today"
                >
                  <span>⚡</span>
                  <span>Quick Adjust Today</span>
                </button>

                <button
                  type="button"
                  onClick={() => setSettingsOpen(true)}
                  className="px-3.5 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white border border-white/10 text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
                  title="Configure n8n Daily Notifications"
                >
                  <span>⚙️</span>
                  <span>Notifications</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActivePlan(null)}
                  className="px-3.5 py-2 rounded-xl bg-brand-600/30 hover:bg-brand-600/50 text-brand-300 border border-brand-500/40 text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
                >
                  <span>🔄</span>
                  <span>Create New Plan</span>
                </button>
              </div>
            </div>

            {/* Metrics Ribbon */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 border-t border-white/10">
              <div className="p-3.5 rounded-2xl bg-surface-900/60 border border-white/5 space-y-1">
                <span className="text-[10px] uppercase font-bold text-surface-200/60 tracking-wider">Estimated Duration</span>
                <p className="text-lg font-black text-white">{activePlan.estimated_duration_days} Days</p>
              </div>
              <div className="p-3.5 rounded-2xl bg-surface-900/60 border border-white/5 space-y-1">
                <span className="text-[10px] uppercase font-bold text-surface-200/60 tracking-wider">Total Learning</span>
                <p className="text-lg font-black text-white">{activePlan.total_learning_hours} Hours</p>
              </div>
              <div className="p-3.5 rounded-2xl bg-surface-900/60 border border-white/5 space-y-1">
                <span className="text-[10px] uppercase font-bold text-surface-200/60 tracking-wider">Daily Commitment</span>
                <p className="text-lg font-black text-white">{activePlan.daily_hours}h / day</p>
              </div>
              <div className="p-3.5 rounded-2xl bg-surface-900/60 border border-white/5 space-y-1">
                <span className="text-[10px] uppercase font-bold text-surface-200/60 tracking-wider">Overall Progress</span>
                <p className="text-lg font-black text-brand-300">{activePlan.overall_progress}%</p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-bold text-surface-200/70">
                <span>Journey Completion</span>
                <span>{activePlan.overall_progress}%</span>
              </div>
              <div className="w-full h-3 rounded-full bg-surface-800 overflow-hidden p-0.5 border border-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-brand-600 via-brand-400 to-emerald-400 transition-all duration-500 shadow-md"
                  style={{ width: `${Math.min(100, Math.max(0, activePlan.overall_progress))}%` }}
                />
              </div>
            </div>
          </div>

          {/* Navigation Tabs: Daily Workspace vs Full Roadmap */}
          <div className="flex items-center gap-2 border-b border-white/10 pb-3">
            <button
              type="button"
              onClick={() => setActiveTab("daily")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === "daily"
                  ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                  : "text-surface-200/70 hover:text-white hover:bg-white/5"
              }`}
            >
              📅 Daily Workspace
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("roadmap")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === "roadmap"
                  ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                  : "text-surface-200/70 hover:text-white hover:bg-white/5"
              }`}
            >
              🗺️ Full Curriculum Roadmap
            </button>
          </div>

          {/* ================================================================ */}
          {/* TAB 1: DAILY WORKSPACE (Yesterday / Today / Tomorrow Navigation)  */}
          {/* ================================================================ */}
          {activeTab === "daily" && dailyView && (
            <div className="space-y-6 animate-fade-in">
              {/* Day Selector & Carousel Navigation */}
              <div className="p-5 rounded-2xl bg-surface-900/80 border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={selectedDayNumber <= 1}
                    onClick={() => fetchDailyView(selectedDayNumber - 1)}
                    className="px-3 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-white text-xs font-bold border border-white/10 transition-colors disabled:opacity-40 cursor-pointer"
                  >
                    ← Yesterday (Day {selectedDayNumber - 1})
                  </button>

                  <div className="px-4 py-2 rounded-xl bg-brand-500/20 border border-brand-500/40 text-brand-300 text-xs font-extrabold">
                    Day {dailyView.day_number} of {dailyView.total_days}
                  </div>

                  <button
                    type="button"
                    disabled={selectedDayNumber >= dailyView.total_days}
                    onClick={() => fetchDailyView(selectedDayNumber + 1)}
                    className="px-3 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-white text-xs font-bold border border-white/10 transition-colors disabled:opacity-40 cursor-pointer"
                  >
                    Tomorrow (Day {selectedDayNumber + 1}) →
                  </button>
                </div>

                {/* Day jump dropdown */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-surface-200/60 font-medium">Jump to:</span>
                  <select
                    value={selectedDayNumber}
                    onChange={(e) => fetchDailyView(parseInt(e.target.value))}
                    className="px-3 py-1.5 rounded-xl bg-surface-950 border border-white/10 text-white text-xs cursor-pointer focus:outline-none focus:border-brand-500"
                  >
                    {activePlan.days.map((d) => (
                      <option key={d.id} value={d.day_number}>
                        Day {d.day_number}: {d.objective.slice(0, 30)}...
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Dynamic AI Summary Banner */}
              <div className="p-5 rounded-2xl bg-gradient-to-r from-surface-900 via-surface-900/90 to-brand-950/40 border border-brand-500/30 flex items-start gap-3 shadow-lg">
                <span className="text-2xl p-2 rounded-xl bg-surface-950 border border-brand-500/20 shrink-0">
                  🤖
                </span>
                <div className="space-y-1">
                  <h4 className="text-xs font-bold text-brand-300 uppercase tracking-wider">
                    Daily AI Manager Briefing
                  </h4>
                  <p className="text-xs sm:text-sm text-surface-200/90 leading-relaxed font-medium">
                    {dailyView.daily_ai_summary}
                  </p>
                </div>
              </div>

              {/* Workload Status Card */}
              <div className="p-5 rounded-2xl bg-surface-900/80 border border-white/10 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="space-y-1">
                  <span className="text-surface-200/60 uppercase font-bold tracking-wider">Today's Workload</span>
                  <p className="text-base font-black text-white">
                    {Math.floor(dailyView.workload_minutes / 60)}h {dailyView.workload_minutes % 60}m
                  </p>
                </div>
                <div className="space-y-1">
                  <span className="text-surface-200/60 uppercase font-bold tracking-wider">Daily Target</span>
                  <p className="text-base font-black text-white">{dailyView.available_hours} Hours</p>
                </div>
                <div className="space-y-1">
                  <span className="text-surface-200/60 uppercase font-bold tracking-wider">Buffer / Rest Time</span>
                  <p className="text-base font-black text-emerald-400">
                    {dailyView.buffer_minutes} Minutes
                  </p>
                </div>
              </div>

              {/* Day Objective Card */}
              <div className="p-6 rounded-2xl bg-surface-900/80 border border-white/10 space-y-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <span className="text-[10px] font-bold text-brand-400 uppercase tracking-wider">
                      {dailyView.current_day.phase_name}
                    </span>
                    <h3 className="text-lg font-bold text-white">
                      🎯 {dailyView.current_day.objective}
                    </h3>
                  </div>
                  {dailyView.current_day.is_completed && (
                    <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-bold flex items-center gap-1">
                      <span>✓</span>
                      <span>Day Completed</span>
                    </span>
                  )}
                </div>

                {dailyView.current_day.expected_outcome && (
                  <p className="text-xs text-surface-200/80 italic">
                    Expected Outcome: "{dailyView.current_day.expected_outcome}"
                  </p>
                )}

                {dailyView.current_day.topics.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {dailyView.current_day.topics.map((top, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg bg-surface-800 text-surface-200/90 text-[11px] font-medium border border-white/5"
                      >
                        • {top}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Active Timer Pill if running */}
              {activeTimerTask && (
                <div className="p-4 rounded-2xl bg-brand-950/80 border border-brand-500/50 flex items-center justify-between shadow-xl animate-fade-in">
                  <div className="flex items-center gap-3">
                    <span className="text-xl animate-pulse">⏱</span>
                    <div>
                      <h4 className="text-xs font-bold text-white truncate max-w-sm">
                        Focus: {activeTimerTask.title}
                      </h4>
                      <p className="text-[11px] text-brand-300">
                        Target: {activeTimerTask.estimated_minutes} min
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xl font-black text-white font-mono">
                      {formatTimer(timerSecondsLeft)}
                    </span>
                    <button
                      type="button"
                      onClick={() => setTimerRunning(!timerRunning)}
                      className="px-3 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-all cursor-pointer"
                    >
                      {timerRunning ? "Pause" : "Resume"}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setActiveTimerTask(null);
                        setTimerRunning(false);
                      }}
                      className="text-xs text-surface-200/60 hover:text-white cursor-pointer"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              )}

              {/* Granular Task Cards */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider px-1">
                  Today's Training Tasks ({dailyView.current_day.tasks.length})
                </h4>

                <div className="space-y-2.5">
                  {dailyView.current_day.tasks.map((task) => {
                    const isDone = task.status === "completed";
                    const isSkipped = task.status === "skipped";

                    return (
                      <div
                        key={task.id}
                        className={`p-4 rounded-2xl border transition-all space-y-2 ${
                          isDone
                            ? "bg-surface-900/40 border-emerald-500/30 opacity-80"
                            : isSkipped
                            ? "bg-surface-950/40 border-white/5 opacity-50"
                            : "bg-surface-900/90 border-white/10 hover:border-brand-500/40 shadow-md"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          {/* Left: Checkbox + Title */}
                          <div className="flex items-start gap-3 flex-1 min-w-0">
                            <button
                              type="button"
                              onClick={() => handleToggleTaskStatus(task)}
                              className={`mt-0.5 w-5 h-5 rounded-lg border flex items-center justify-center transition-all cursor-pointer shrink-0 ${
                                isDone
                                  ? "bg-emerald-500 border-emerald-400 text-white font-black text-xs"
                                  : "border-white/20 hover:border-brand-400 bg-surface-950"
                              }`}
                              title={isDone ? "Mark Incomplete" : "Mark Complete"}
                            >
                              {isDone && "✓"}
                            </button>

                            <div className="space-y-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <h5
                                  className={`text-xs sm:text-sm font-bold truncate ${
                                    isDone ? "text-emerald-300 line-through" : "text-white"
                                  }`}
                                >
                                  {task.title}
                                </h5>

                                {task.is_carried_over && (
                                  <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                                    ⚠️ Carried Over from Day {task.original_day_number || 1}
                                  </span>
                                )}

                                <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-surface-800 text-surface-200/80 border border-white/5">
                                  {task.task_type === "theory"
                                    ? "📘 Theory"
                                    : task.task_type === "practice"
                                    ? "💻 Practice"
                                    : task.task_type === "project"
                                    ? "🚀 Project"
                                    : "📝 Assessment"}
                                </span>
                              </div>

                              {task.description && (
                                <p className="text-xs text-surface-200/70 line-clamp-2">
                                  {task.description}
                                </p>
                              )}

                              {task.notes && (
                                <div className="p-2 rounded-xl bg-surface-950 border border-white/5 text-[11px] text-brand-300 font-medium mt-1">
                                  📝 Note: {task.notes}
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Right: Time badge + Action Buttons */}
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="px-2.5 py-1 rounded-xl bg-surface-950 border border-white/10 text-xs font-black text-white">
                              ⏱ {task.estimated_minutes} min
                            </span>

                            {/* Start Timer button */}
                            {!isDone && (
                              <button
                                type="button"
                                onClick={() => startTaskTimer(task)}
                                className="p-1.5 rounded-xl bg-surface-800 hover:bg-brand-600 text-surface-200 hover:text-white transition-colors cursor-pointer"
                                title="Start Focus Timer"
                              >
                                ▶
                              </button>
                            )}

                            {/* Add/Edit Note button */}
                            <button
                              type="button"
                              onClick={() => {
                                setEditingTask(task);
                                setTaskNote(task.notes || "");
                              }}
                              className="p-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white transition-colors cursor-pointer"
                              title="Add Personal Note"
                            >
                              ✏️
                            </button>

                            {/* Skip button */}
                            {!isDone && (
                              <button
                                type="button"
                                onClick={() => handleTaskAction(task.id, isSkipped ? "not_started" : "skipped")}
                                className="p-1.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white transition-colors cursor-pointer text-[10px]"
                                title={isSkipped ? "Restore task" : "Skip task"}
                              >
                                {isSkipped ? "Restore" : "Skip"}
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Confidence Rating & Topic Review Widget */}
              <div className="p-6 rounded-2xl bg-surface-900/80 border border-white/10 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                      Topic Mastery & Confidence Evaluation
                    </h4>
                    <p className="text-xs text-surface-200/70">
                      How confident are you with "{dailyView.current_day.objective}"?
                    </p>
                  </div>

                  {/* Rating Stars 1 to 5 */}
                  <div className="flex items-center gap-1.5">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => handleSubmitConfidence(star)}
                        disabled={submittingRating}
                        className={`w-9 h-9 rounded-xl font-bold text-xs transition-all flex items-center justify-center cursor-pointer ${
                          confidenceRating === star
                            ? "bg-amber-500 text-white shadow-md shadow-amber-500/30 scale-105"
                            : "bg-surface-800 hover:bg-surface-700 text-surface-200/80 border border-white/5"
                        }`}
                      >
                        {star}★
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={ratingFeedback}
                    onChange={(e) => setRatingFeedback(e.target.value)}
                    placeholder="Optional reflection: what was tricky or went well?..."
                    className="flex-1 px-3 py-2 rounded-xl bg-surface-950 border border-white/10 text-white text-xs placeholder-surface-200/40 focus:outline-none focus:border-brand-500"
                  />
                </div>

                {reviewRecommendation && (
                  <div className="p-3.5 rounded-xl bg-surface-950 border border-brand-500/30 text-xs text-surface-200/90 leading-relaxed animate-fade-in">
                    <span className="font-bold text-brand-300">💡 AI Recommendation: </span>
                    {reviewRecommendation}
                  </div>
                )}
              </div>

              {/* Cross-Module Integration Bridges */}
              <div className="p-6 rounded-2xl bg-surface-900/50 border border-white/5 space-y-3">
                <h4 className="text-xs font-bold text-surface-200/60 uppercase tracking-wider">
                  Connected CareerCoachAI Modules
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Link
                    to="/question-bank"
                    className="p-3 rounded-xl bg-surface-900 hover:bg-surface-800 border border-white/10 text-xs transition-colors flex items-center gap-2 text-white"
                  >
                    <span>📚</span>
                    <span>Practice Topic in Question Bank</span>
                  </Link>

                  <Link
                    to="/coding"
                    className="p-3 rounded-xl bg-surface-900 hover:bg-surface-800 border border-white/10 text-xs transition-colors flex items-center gap-2 text-white"
                  >
                    <span>💻</span>
                    <span>Solve Related Coding Challenges</span>
                  </Link>

                  <Link
                    to="/interview"
                    className="p-3 rounded-xl bg-surface-900 hover:bg-surface-800 border border-white/10 text-xs transition-colors flex items-center gap-2 text-white"
                  >
                    <span>🎙️</span>
                    <span>Simulate AI Mock Interview</span>
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* TAB 2: FULL CURRICULUM ROADMAP VIEW (Deep Prerequisite Phases)   */}
          {/* ================================================================ */}
          {activeTab === "roadmap" && (
            <div className="space-y-6 animate-fade-in">
              {/* Phases Chain */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {activePlan.phases_summary.map((ph) => (
                  <div
                    key={ph.phase}
                    className="p-5 rounded-2xl bg-surface-900/80 border border-white/10 space-y-2 relative overflow-hidden"
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider bg-brand-500/20 text-brand-300 border border-brand-500/30">
                        Phase {ph.phase}
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-white">{ph.title}</h4>
                    <p className="text-xs text-surface-200/70">{ph.description}</p>
                  </div>
                ))}
              </div>

              {/* All Days Table / Grid */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  All Scheduled Training Days ({activePlan.days.length})
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {activePlan.days.map((day) => (
                    <div
                      key={day.id}
                      onClick={() => {
                        setSelectedDayNumber(day.day_number);
                        setActiveTab("daily");
                        fetchDailyView(day.day_number);
                      }}
                      className="p-4 rounded-2xl bg-surface-900/80 hover:bg-surface-800/80 border border-white/10 hover:border-brand-500/40 transition-all cursor-pointer space-y-2 group"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-black text-brand-400">
                          Day {day.day_number}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-surface-200/60 font-semibold">
                            ⏱ {day.total_planned_minutes} min
                          </span>
                          {day.is_completed ? (
                            <span className="w-2 h-2 rounded-full bg-emerald-400" />
                          ) : (
                            <span className="w-2 h-2 rounded-full bg-surface-700" />
                          )}
                        </div>
                      </div>

                      <h5 className="text-xs sm:text-sm font-bold text-white group-hover:text-brand-300 transition-colors">
                        {day.objective}
                      </h5>

                      <p className="text-[11px] text-surface-200/60">
                        {day.tasks.length} granular tasks • {day.phase_name}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL: ADD / EDIT TASK NOTE                                          */}
      {/* ==================================================================== */}
      {editingTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md p-6 rounded-3xl bg-surface-900 border border-white/10 shadow-2xl space-y-4">
            <h4 className="text-sm font-bold text-white truncate">
              Task Note: {editingTask.title}
            </h4>
            <textarea
              value={taskNote}
              onChange={(e) => setTaskNote(e.target.value)}
              placeholder="Record your takeaways, code snippets, or areas needing review..."
              rows={4}
              className="w-full p-3 rounded-xl bg-surface-950 border border-white/10 text-white text-xs placeholder-surface-200/40 focus:outline-none focus:border-brand-500"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setEditingTask(null)}
                className="px-4 py-2 rounded-xl bg-surface-800 text-surface-200 hover:text-white text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveNote}
                disabled={savingTask}
                className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-md shadow-brand-600/30"
              >
                {savingTask ? "Saving..." : "Save Note"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL: QUICK RESCHEDULE TODAY                                        */}
      {/* ==================================================================== */}
      {rescheduleOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md p-6 rounded-3xl bg-surface-900 border border-white/10 shadow-2xl space-y-4">
            <h4 className="text-sm font-bold text-white">
              ⚡ Recalculate Today's Workload
            </h4>
            <p className="text-xs text-surface-200/70">
              Only have limited study time today? Specify your available hours. AI will prioritize the most critical
              tasks for today and automatically defer the remaining tasks to tomorrow without deleting any progress.
            </p>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-white">Today's Available Hours</label>
              <input
                type="number"
                step="0.25"
                min="0.25"
                max="8"
                value={rescheduleHours}
                onChange={(e) => setRescheduleHours(e.target.value)}
                className="w-full p-3 rounded-xl bg-surface-950 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setRescheduleOpen(false)}
                className="px-4 py-2 rounded-xl bg-surface-800 text-surface-200 hover:text-white text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleQuickReschedule}
                disabled={rescheduling}
                className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-md shadow-brand-600/30"
              >
                {rescheduling ? "Recalculating..." : "Apply Adjustment"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL: NOTIFICATION SETTINGS & n8n WEBHOOK                           */}
      {/* ==================================================================== */}
      {settingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg p-6 sm:p-8 rounded-3xl bg-surface-900 border border-white/10 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h4 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
                <span>⚙️</span>
                <span>Notification Settings</span>
              </h4>
              <button
                type="button"
                onClick={() => setSettingsOpen(false)}
                className="text-surface-200/60 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-xs">
              {/* Enable Daily Toggle */}
              <div className="flex items-center justify-between p-3.5 rounded-2xl bg-surface-950 border border-white/5">
                <div>
                  <span className="font-bold text-white block">Daily Learning Notifications</span>
                  <span className="text-[11px] text-surface-200/60 block">
                    Receive your morning training brief via n8n automation
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={trainerSettings.notifications_enabled}
                  onChange={(e) =>
                    setTrainerSettings({
                      ...trainerSettings,
                      notifications_enabled: e.target.checked,
                    })
                  }
                  className="w-5 h-5 accent-brand-500 cursor-pointer"
                />
              </div>

              {/* Preferred Time */}
              <div className="space-y-1.5">
                <label className="font-bold text-white block">Preferred Notification Time</label>
                <input
                  type="time"
                  value={trainerSettings.preferred_time}
                  onChange={(e) =>
                    setTrainerSettings({ ...trainerSettings, preferred_time: e.target.value })
                  }
                  className="w-full p-3 rounded-xl bg-surface-950 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
                />
              </div>

              {/* Notification Channel */}
              <div className="space-y-1.5">
                <label className="font-bold text-white block">Delivery Channel</label>
                <select
                  value={trainerSettings.notification_channel}
                  onChange={(e) =>
                    setTrainerSettings({ ...trainerSettings, notification_channel: e.target.value })
                  }
                  className="w-full p-3 rounded-xl bg-surface-950 border border-white/10 text-white text-xs focus:outline-none focus:border-brand-500"
                >
                  <option value="email">Email</option>
                  <option value="telegram">Telegram (if configured)</option>
                  <option value="sms">SMS (if configured)</option>
                </select>
              </div>

              {/* n8n Status Card */}
              <div className="p-4 rounded-2xl bg-surface-950 border border-white/5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">n8n Automation Status:</span>
                  {trainerSettings.webhook_configured ? (
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      Configured
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      Not Configured
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-surface-200/60 leading-relaxed">
                  CareerCoachAI dispatches real training day payloads to your configured <code className="text-brand-300">N8N_WEBHOOK_URL</code> in <code className="text-brand-300">.env</code>.
                </p>

                <button
                  type="button"
                  onClick={handleTriggerWebhook}
                  disabled={triggeringWebhook}
                  className="mt-2 w-full py-2.5 rounded-xl bg-surface-800 hover:bg-surface-700 border border-white/10 text-white font-bold text-xs transition-colors flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {triggeringWebhook ? (
                    <span>Dispatching webhook...</span>
                  ) : (
                    <>
                      <span>📡</span>
                      <span>Send Test Notification</span>
                    </>
                  )}
                </button>

                {webhookResult && (
                  <div
                    className={`p-3 rounded-xl text-[11px] mt-2 border ${
                      webhookResult.success
                        ? "bg-emerald-950/60 border-emerald-500/30 text-emerald-200"
                        : "bg-red-950/60 border-red-500/30 text-red-200"
                    }`}
                  >
                    {webhookResult.message}
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
              <button
                type="button"
                onClick={() => setSettingsOpen(false)}
                className="px-4 py-2 rounded-xl bg-surface-800 text-surface-200 hover:text-white text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveSettings}
                disabled={savingSettings}
                className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-md shadow-brand-600/30"
              >
                {savingSettings ? "Saving..." : "Save Preferences"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
