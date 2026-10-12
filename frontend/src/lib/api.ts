/**
 * API client — typed fetch wrapper for backend communication.
 *
 * Base URL is read from the VITE_API_BASE_URL environment variable.
 * All responses follow the standard { status, data, message } envelope.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface APIResponse<T = unknown> {
  status: "success" | "error";
  data?: T;
  message: string;
  details?: unknown;
}

export interface HealthData {
  status: string;
  version: string;
  database: string;
  ollama: string;
}

export interface ProfileData {
  id: number;
  user_id: number;
  education?: string | null;
  degree?: string | null;
  graduation_year?: number | null;
  experience?: string | null;
  current_role?: string | null;
  target_role?: string | null;
  skills: string[];
  preferred_location?: string | null;
  work_preference?: string | null;
  career_goal?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserData {
  id: number;
  email: string;
  name: string;
  is_active: boolean;
  role?: string;
  is_superuser?: boolean;
  created_at: string;
  profile?: ProfileData | null;
}


export interface AuthResponseData {
  access_token: string;
  token_type: string;
  user: UserData;
}

export interface ForgotPasswordData {
  email: string;
  reset_token?: string | null;
}

export interface ProfileSummary {
  name: string;
  email: string;
  current_role?: string | null;
  target_role?: string | null;
  education?: string | null;
  degree?: string | null;
  graduation_year?: number | null;
  experience?: string | null;
  preferred_location?: string | null;
  work_preference?: string | null;
  completion_percentage: number;
}

export interface ResumeSummary {
  has_resume: boolean;
  filename?: string | null;
  uploaded_at?: string | null;
  latest_ats_score?: number | null;
  status: string;
}

export interface SkillProgressSummary {
  total_skills: number;
  skills: string[];
}

export interface InterviewStatsSummary {
  total_mock_interviews: number;
  average_score?: number | null;
  last_interview_date?: string | null;
}

export interface CodingStatsSummary {
  total_problems_solved: number;
  streak_days: number;
  last_practiced_date?: string | null;
}

export interface PlacementReadinessSummary {
  readiness_score?: number | null;
  level?: string | null;
  status_message: string;
}

export interface ActivityItem {
  id: string;
  activity_type: string;
  title: string;
  description: string;
  timestamp: string;
}

export interface DashboardData {
  welcome_message: string;
  profile: ProfileSummary;
  career_goal?: string | null;
  resume: ResumeSummary;
  skills: SkillProgressSummary;
  interviews: InterviewStatsSummary;
  coding: CodingStatsSummary;
  placement_readiness: PlacementReadinessSummary;
  recent_activity: ActivityItem[];
}

export interface ResumeVersionData {
  id: number;
  version_number: number;
  filename: string;
  file_size: number;
  file_type: string;
  mime_type: string;
  extracted_text?: string | null;
  is_current: boolean;
  created_at: string;
}

export interface ResumeData {
  id: number;
  user_id: number;
  title: string;
  current_version?: ResumeVersionData | null;
  versions: ResumeVersionData[];
  created_at: string;
  updated_at: string;
}

export interface ResumeSkillData {
  id: number;
  skill_name: string;
  category: string;
  proficiency_level?: string | null;
}

export interface ResumeAnalysisData {
  id: number;
  resume_id: number;
  resume_version_id: number;
  user_id: number;
  ats_score: number;
  scoring_breakdown: {
    overall_ats_score: number;
    structure_score: number;
    skills_score: number;
    experience_score: number;
    education_score: number;
    formatting_score: number;
    weights: Record<string, number>;
    rubric_description: string;
  };
  experience_summary?: string | null;
  education_summary?: string | null;
  project_summary?: string | null;
  certifications: string[];
  strengths: string[];
  weaknesses: string[];
  missing_keywords: string[];
  grammar_suggestions: string[];
  formatting_suggestions: string[];
  improvement_recommendations: string[];
  skills: ResumeSkillData[];
  created_at: string;
}

export interface CareerSkillData {
  name: string;
  category: string;
  importance: number;
  level: number;
}

export interface OccupationData {
  id: number;
  code: string;
  title: string;
  description: string;
  industry: string;
  skills: CareerSkillData[];
}

export interface SkillGapItem {
  name: string;
  category: string;
  importance: number;
  level: number;
  priority?: "High" | "Medium" | "Low";
}

export interface LearningStepItem {
  step: number;
  skill_name: string;
  priority?: string;
  rationale: string;
}

export interface SkillGapReportData {
  id: number;
  user_id: number;
  occupation_id: number;
  occupation_title: string;
  match_percentage: number;
  strong_skills: SkillGapItem[];
  intermediate_skills: SkillGapItem[];
  missing_skills: SkillGapItem[];
  learning_order: LearningStepItem[];
  ai_explanation: string;
  created_at: string;
}

export interface RoadmapItemData {
  id: number;
  roadmap_id: number;
  phase: string;
  skill: string;
  topics: string[];
  projects: string[];
  resources: string[];
  priority: string;
  estimated_effort: string;
  is_completed: boolean;
  completed_at?: string | null;
}

export interface RoadmapData {
  id: number;
  user_id: number;
  occupation_id?: number | null;
  title: string;
  target_role: string;
  overall_progress: number;
  is_active: boolean;
  items: RoadmapItemData[];
  current_skills: string[];
  missing_skills: string[];
  created_at: string;
  updated_at: string;
}

export interface JobData {
  id: number;
  external_id: string;
  provider: string;
  title: string;
  company: string;
  location: string;
  is_remote: boolean;
  description: string;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string | null;
  redirect_url: string;
  posted_at?: string | null;
  is_saved: boolean;
  created_at: string;
}

export interface JobMatchData {
  id: number;
  user_id: number;
  job_id: number;
  resume_id?: number | null;
  match_score: number;
  experience_match: number;
  education_match: number;
  matched_skills: string[];
  missing_skills: string[];
  explanation: string;
  recommendations: string[];
  created_at: string;
}

export interface QuestionData {
  id: number;
  question: string;
  category: string;
  difficulty: string;
  role: string;
  tags: string[];
  source_type: string;
  source_label: string;
  explanation?: string | null;
  is_saved: boolean;
  created_at: string;
}

export interface InterviewEvaluationData {
  id: number;
  answer_id: number;
  technical_correctness: number;
  relevance: number;
  completeness: number;
  communication: number;
  structure: number;
  clarity: number;
  overall_score: number;
  feedback: string;
  strengths: string[];
  improvements: string[];
  ideal_answer?: string | null;
  evaluated_at: string;
}

export interface InterviewQuestionData {
  id: number;
  question_text: string;
  category: string;
  difficulty: string;
  question_order: number;
  explanation?: string | null;
  user_answer?: string | null;
  evaluation?: InterviewEvaluationData | null;
}

export interface InterviewSessionData {
  id: number;
  user_id: number;
  role: string;
  difficulty: string;
  status: "in_progress" | "completed" | "abandoned";
  total_questions: number;
  current_question_index: number;
  overall_score?: number | null;
  summary_feedback?: string | null;
  current_question?: InterviewQuestionData | null;
  questions: InterviewQuestionData[];
  created_at: string;
  completed_at?: string | null;
}

export interface InterviewResultsData {
  session_id: number;
  user_id: number;
  role: string;
  difficulty: string;
  overall_score: number;
  metrics_breakdown: Record<string, number>;
  summary_feedback: string;
  strengths: string[];
  improvements: string[];
  questions_transcript: InterviewQuestionData[];
  completed_at?: string | null;
}

export interface ScoreHistoryItem {
  interview_number: number;
  session_id: number;
  role: string;
  difficulty: string;
  score: number;
  date?: string | null;
}

export interface TopicPerformanceItem {
  topic: string;
  avg_score: number;
  questions_count: number;
}

export interface PerformanceData {
  total_interviews: number;
  average_score?: number | null;
  best_score?: number | null;
  latest_score?: number | null;
  improvement?: number | null;
  technical_score?: number | null;
  communication_score?: number | null;
  weak_topics: TopicPerformanceItem[];
  strong_topics: TopicPerformanceItem[];
  score_history: ScoreHistoryItem[];
  has_enough_data: boolean;
  status_message: string;
}

export interface ReadinessMetricComponent {
  key: string;
  name: string;
  available: boolean;
  score?: number | null;
  raw_weight: number;
  effective_weight_percentage: number;
  status: string;
}

export interface ReadinessData {
  overall_readiness_score?: number | null;
  level: string;
  status_message: string;
  available_metrics_count: number;
  total_metrics_count: number;
  breakdown: ReadinessMetricComponent[];
  recommendations: string[];
}

export interface CodingResultData {
  test_case_index: number;
  input_data: string;
  expected_output: string;
  passed: boolean;
  actual_output?: string | null;
  error_output?: string | null;
  execution_time_ms: number;
}

export interface CodingSubmissionData {
  id: number;
  user_id: number;
  challenge_id: number;
  language: string;
  code: string;
  status: string;
  passed_test_cases: number;
  total_test_cases: number;
  execution_time_ms?: number | null;
  error_message?: string | null;
  results: CodingResultData[];
  submitted_at: string;
}

export interface CodingChallengeData {
  id: number;
  title: string;
  slug: string;
  category: string;
  difficulty: string;
  description: string;
  starter_code: string;
  language: string;
  examples: Array<{ input: string; output: string; explanation?: string | null }>;
  sample_test_cases: Array<{ input: string; expected_output: string }>;
  explanation?: string | null;
  sql_schema?: string | null;
  is_solved: boolean;
  created_at: string;
}

export interface CodingAIHintData {
  hint: string;
  explanation: string;
}

export interface PracticeQuestionItemData {
  question_text: string;
  category: string;
  difficulty: string;
  label: string;
  sample_answer_points: string[];
}

export interface TechnicalTopicItemData {
  topic: string;
  description: string;
  importance: string;
}

export interface BehavioralPrepItemData {
  principle: string;
  advice: string;
  example_prompt: string;
}

export interface CompanyPrepData {
  id: number;
  user_id: number;
  company_name: string;
  target_role: string;
  is_verified_company: boolean;
  verification_notes?: string | null;
  company_overview: string;
  role_summary: string;
  required_skills: string[];
  technical_prep_topics: TechnicalTopicItemData[];
  coding_topics: string[];
  hr_topics: string[];
  behavioral_prep: BehavioralPrepItemData[];
  practice_questions: PracticeQuestionItemData[];
  created_at: string;
}

export interface LearningResourceData {
  id: number;
  title: string;
  description: string;
  url: string;
  source: string;
  resource_type: string;
  skill_name: string;
  difficulty: string;
  estimated_hours?: number | null;
  is_verified: boolean;
  is_saved: boolean;
  is_completed: boolean;
  is_recommended_for_gap: boolean;
  created_at: string;
}

export interface ProjectRecommendationData {
  id: number;
  user_id: number;
  title: string;
  description: string;
  difficulty: string;
  target_role?: string | null;
  technologies: string[];
  features: string[];
  skills_learned: string[];
  expected_outcome: string;
  is_saved: boolean;
  status: string;
  created_at: string;
}

export interface TrainingTaskData {
  id: number;
  day_id: number;
  title: string;
  description?: string | null;
  task_type: "theory" | "practice" | "project" | "assessment";
  estimated_minutes: number;
  status: "not_started" | "in_progress" | "completed" | "skipped" | "rescheduled";
  order_index: number;
  is_carried_over: boolean;
  original_day_number?: number | null;
  notes?: string | null;
  time_spent_minutes?: number | null;
  completed_at?: string | null;
}

export interface TrainingDayData {
  id: number;
  plan_id: number;
  day_number: number;
  phase_name: string;
  objective: string;
  topics: string[];
  expected_outcome?: string | null;
  total_planned_minutes: number;
  is_completed: boolean;
  completed_at?: string | null;
  confidence_rating?: number | null;
  ai_review_recommendation?: string | null;
  tasks: TrainingTaskData[];
}

export interface TrainingPhaseSummary {
  phase: number;
  title: string;
  description: string;
}

export interface TrainingPlanData {
  id: number;
  user_id: number;
  title: string;
  goal_dimensions: string[];
  target_skill?: string | null;
  target_role?: string | null;
  target_company?: string | null;
  current_skills: string[];
  experience_level: string;
  daily_hours: number;
  learning_preference: string;
  target_deadline?: string | null;
  estimated_duration_days: number;
  total_learning_hours: number;
  overall_progress: number;
  is_active: boolean;
  phases_summary: TrainingPhaseSummary[];
  created_at: string;
  updated_at: string;
  days: TrainingDayData[];
}

export interface DailyTrainingViewData {
  plan_id: number;
  goal_title: string;
  day_number: number;
  total_days: number;
  current_day: TrainingDayData;
  yesterday_summary: {
    has_yesterday: boolean;
    completed: string[];
    incomplete: string[];
  };
  tomorrow_preview?: {
    day_number: number;
    objective: string;
    total_minutes: number;
    task_count: number;
  } | null;
  daily_ai_summary: string;
  available_hours: number;
  workload_minutes: number;
  available_minutes: number;
  buffer_minutes: number;
  overall_progress: number;
}

export interface ResumeSkillsData {
  skills: string[];
  source: string;
}

export interface PersonalTrainerSettingsData {
  notifications_enabled: boolean;
  preferred_time: string;
  notification_channel: string;
  webhook_configured: boolean;
}

export interface N8nWebhookTriggerData {
  success: boolean;
  message: string;
  webhook_configured: boolean;
  payload?: any;
  webhook_status_code?: number | null;
}

export interface ResumeVersionHistoryItemData {
  id: number;
  version_number: number;
  filename: string;

  file_size: number;
  file_type: string;
  mime_type: string;
  is_current: boolean;
  ats_score?: number | null;
  skills: string[];
  strengths: string[];
  weaknesses: string[];
  missing_keywords: string[];
  created_at: string;
}

export interface ResumeVersionHistoryData {
  resume_id: number;
  title: string;
  total_versions: number;
  score_improvement?: number | null;
  versions: ResumeVersionHistoryItemData[];
}

export interface ResumeVersionComparisonData {
  resume_id: number;
  v1_version_id: number;
  v1_version_number: number;
  v1_filename: string;
  v1_ats_score?: number | null;
  v1_skills: string[];

  v2_version_id: number;
  v2_version_number: number;
  v2_filename: string;
  v2_ats_score?: number | null;
  v2_skills: string[];

  ats_score_delta?: number | null;
  added_skills: string[];
  removed_skills: string[];
  resolved_missing_keywords: string[];
}

export interface AchievementData {
  id: number;
  slug: string;
  title: string;
  description: string;
  icon: string;
  category: string;
  threshold: number;
  current_progress: number;
  is_earned: boolean;
  earned_at?: string | null;
}

export interface AchievementSummaryData {
  total_achievements: number;
  earned_count: number;
  completion_percentage: number;
  achievements: AchievementData[];
}

export interface NotificationData {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: string;
  link_url?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListData {
  unread_count: number;
  notifications: NotificationData[];
}

export interface NotificationPreferenceData {
  user_id: number;
  enable_roadmap_reminders: boolean;
  enable_interview_reminders: boolean;
  enable_coding_reminders: boolean;
  enable_resume_suggestions: boolean;
  enable_learning_milestones: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminSystemStatsData {
  total_users: number;
  active_users: number;
  resumes: number;
  interviews: number;
  coding_submissions: number;
  job_searches: number;
  ai_evaluations: number;
}

export interface AdminUserData {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface AdminAuditLogData {
  timestamp: string;
  event_type: string;
  description: string;
  actor: string;
}

export interface AdminSettingsData {
  app_name: string;
  app_version: string;
  environment: string;
  ollama_model: string;
  ollama_base_url: string;
  jwt_expiration_minutes: number;
  database_url_masked: string;
  registration_enabled: boolean;
}

// --- Career Intelligence Interfaces ---
export interface JobDescriptionAnalysisData {
  job_title?: string | null;
  company?: string | null;
  required_skills: string[];
  preferred_skills: string[];
  technologies: string[];
  experience: string[];
  responsibilities: string[];
  education: string[];
  certifications: string[];
  soft_skills: string[];
  keywords: string[];
}

export interface ResumeJdMatchData {
  id: number;
  resume_id?: number | null;
  resume_title: string;
  job_title?: string | null;
  company_name?: string | null;
  job_description_snippet?: string | null;
  overall_score: number;
  skills_score: number;
  keyword_score: number;
  experience_score: number;
  responsibility_score: number;
  matched_skills: string[];
  missing_skills: string[];
  partial_matches: string[];
  relevant_experience: string[];
  potential_gaps: string[];
  improvement_suggestions: string[];
  target_occupation_title?: string | null;
  created_at: string;
}

export interface ResumeJdMatchHistoryItemData {
  id: number;
  resume_id?: number | null;
  resume_title: string;
  job_title?: string | null;
  company_name?: string | null;
  overall_score: number;
  skills_score: number;
  created_at: string;
}

export interface CoverLetterData {
  id?: number | null;
  job_title: string;
  company_name: string;
  tone: string;
  length: string;
  content: string;
  label: string;
  created_at: string;
}

export interface CoverLetterHistoryItemData {
  id: number;
  job_title: string;
  company_name: string;
  tone: string;
  length: string;
  created_at: string;
}

export interface ColdEmailData {
  id?: number | null;
  job_title: string;
  company_name: string;
  recruiter_name?: string | null;
  recruiter_email?: string | null;
  email_type: string;
  tone: string;
  length: string;
  subject: string;
  body: string;
  created_at: string;
}

export interface ColdEmailHistoryItemData {
  id: number;
  job_title: string;
  company_name: string;
  email_type: string;
  recruiter_name?: string | null;
  recruiter_email?: string | null;
  subject: string;
  created_at: string;
}

export interface ColdEmailGeneratePayload {
  job_title: string;
  company_name: string;
  resume_id?: number | null;
  match_id?: number | null;
  job_description?: string;
  recruiter_name?: string;
  recruiter_email?: string;
  company_info?: string;
  portfolio_url?: string;
  github_url?: string;
  linkedin_url?: string;
  additional_context?: string;
  email_type?: string;
  tone?: string;
  length?: string;
}


// --- Job Market Analyzer Interfaces ---
export interface JobMarketMetricItemData {
  name: string;
  count: number;
  percentage?: number | null;
}

export interface JobMarketAnalyticsData {
  total_matching_jobs: number;
  top_skills: JobMarketMetricItemData[];
  top_technologies: JobMarketMetricItemData[];
  top_job_titles: JobMarketMetricItemData[];
  location_distribution: JobMarketMetricItemData[];
  workplace_distribution: JobMarketMetricItemData[];
  experience_distribution: JobMarketMetricItemData[];
  company_distribution: JobMarketMetricItemData[];
  posting_trends: JobMarketMetricItemData[];
  salary_summary?: {
    avg_salary: number;
    min_salary: number;
    max_salary: number;
    currency: string;
    samples_count: number;
  } | null;
  insufficient_data_metrics: string[];
}

export interface JobMarketListingData {
  id?: number | null;
  external_id: string;
  provider: string;
  title: string;
  company: string;
  location: string;
  is_remote: boolean;
  workplace_type: string;
  description: string;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string | null;
  redirect_url: string;
  posted_at?: string | null;
  extracted_skills: string[];
  experience_level?: string | null;
}

export interface JobMarketSearchResponseData {
  live_data_available: boolean;
  provider_configured: boolean;
  provider_name: string;
  status_message: string;
  total_results: number;
  page: number;
  limit: number;
  jobs: JobMarketListingData[];
  analytics?: JobMarketAnalyticsData | null;
}











export class APIError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "APIError";
    this.status = status;
    this.details = details;
  }
}

// Token management helpers
export const TOKEN_STORAGE_KEY = "cc_auth_token";

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch {
    // Ignore localStorage errors (e.g. private mode)
  }
}

export function removeStoredToken(): void {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // Ignore localStorage errors
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<APIResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`;

  const token = getStoredToken();
  const authHeaders: Record<string, string> = token
    ? { Authorization: `Bearer ${token}` }
    : {};

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...authHeaders,
    ...options.headers,
  };

  try {
    const response = await fetch(url, { ...options, headers });
    let body: any = {};
    const text = await response.text();
    if (text) {
      try {
        body = JSON.parse(text);
      } catch {
        body = { message: text };
      }
    }

    if (!response.ok) {
      throw new APIError(
        body?.message || `Request failed with status ${response.status}`,
        response.status,
        body?.details
      );
    }

    return body as APIResponse<T>;
  } catch (error) {
    if (error instanceof APIError) throw error;

    throw new APIError(
      error instanceof Error ? error.message : "Network error",
      0
    );
  }
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),

  post: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: "DELETE" }),

  getResumes: () => request<ResumeData[]>("/api/v1/resumes"),

  getProfile: () => request<ProfileData>("/api/v1/profile"),

  searchJobs: (query: string = "", location: string = "", isRemote: boolean = false, page: number = 1, limit: number = 20) => {
    const params = new URLSearchParams();
    if (query) params.append("q", query);
    if (location) params.append("location", location);
    if (isRemote) params.append("is_remote", "true");
    params.append("page", page.toString());
    params.append("limit", limit.toString());
    return request<JobData[]>(`/api/v1/jobs?${params.toString()}`);
  },

  getJobDetail: (id: number) => {
    return request<JobData>(`/api/v1/jobs/${id}`);
  },

  saveJob: (id: number) => {
    return request<JobData>(`/api/v1/jobs/${id}/save`, { method: "POST" });
  },

  unsaveJob: (id: number) => {
    return request<JobData>(`/api/v1/jobs/${id}/save`, { method: "DELETE" });
  },

  getSavedJobs: () => {
    return request<JobData[]>("/api/v1/jobs/saved");
  },

  matchResumeToJob: (jobId: number, resumeId?: number) => {
    const q = resumeId ? `?resume_id=${resumeId}` : "";
    return request<JobMatchData>(`/api/v1/jobs/${jobId}/match${q}`, { method: "POST" });
  },

  getJobMatch: (jobId: number) => {
    return request<JobMatchData>(`/api/v1/jobs/${jobId}/match`);
  },

  getQuestions: (
    category?: string,
    difficulty?: string,
    role?: string,
    q?: string,
    sourceType?: string,
    savedOnly: boolean = false,
    page: number = 1,
    limit: number = 20
  ) => {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (difficulty) params.append("difficulty", difficulty);
    if (role) params.append("role", role);
    if (q) params.append("q", q);
    if (sourceType) params.append("source_type", sourceType);
    if (savedOnly) params.append("saved_only", "true");
    params.append("page", page.toString());
    params.append("limit", limit.toString());
    return request<QuestionData[]>(`/api/v1/questions?${params.toString()}`);
  },

  getRandomQuestion: (category?: string, difficulty?: string, role?: string) => {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (difficulty) params.append("difficulty", difficulty);
    if (role) params.append("role", role);
    return request<QuestionData>(`/api/v1/questions/random?${params.toString()}`);
  },

  generateAIQuestions: (payload: { topic?: string; category?: string; difficulty?: string; role?: string; count?: number }) => {
    return request<QuestionData[]>("/api/v1/questions/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  saveQuestion: (id: number) => {
    return request<QuestionData>(`/api/v1/questions/${id}/save`, { method: "POST" });
  },

  unsaveQuestion: (id: number) => {
    return request<QuestionData>(`/api/v1/questions/${id}/save`, { method: "DELETE" });
  },

  generateRoadmap: (occupationId?: number, customQuery?: string) => {
    return request<RoadmapData>("/api/v1/roadmap/generate", {
      method: "POST",
      body: JSON.stringify({ occupation_id: occupationId, custom_query: customQuery }),
    });
  },


  getLatestRoadmap: () => {
    return request<RoadmapData>("/api/v1/roadmap/latest");
  },

  toggleRoadmapItem: (itemId: number, isCompleted: boolean) => {
    return request<RoadmapData>(`/api/v1/roadmap/items/${itemId}/toggle`, {
      method: "PUT",
      body: JSON.stringify({ is_completed: isCompleted }),
    });
  },

  searchCareers: (query: string = "", limit: number = 20) => {
    const q = query ? `?q=${encodeURIComponent(query)}&limit=${limit}` : `?limit=${limit}`;
    return request<OccupationData[]>(`/api/v1/careers${q}`);
  },

  getCareerDetail: (id: number) => {
    return request<OccupationData>(`/api/v1/careers/${id}`);
  },

  generateSkillGap: (occupationId: number) => {
    return request<SkillGapReportData>("/api/v1/career/skill-gap", {
      method: "POST",
      body: JSON.stringify({ occupation_id: occupationId }),
    });
  },

  getLatestSkillGap: () => {
    return request<SkillGapReportData>("/api/v1/career/skill-gap/latest");
  },

  setCareerGoal: (occupationId: number) => {
    return request<OccupationData>("/api/v1/career/goal", {
      method: "POST",
      body: JSON.stringify({ occupation_id: occupationId }),
    });
  },

  analyzeResume: (id: number, versionId?: number, force: boolean = false) => {
    const params = new URLSearchParams();
    if (versionId) params.append("version_id", versionId.toString());
    if (force) params.append("force", "true");
    const query = params.toString() ? `?${params.toString()}` : "";
    return request<ResumeAnalysisData>(`/api/v1/resumes/${id}/analyze${query}`, { method: "POST" });
  },

  getResumeAnalysis: (id: number) => {
    return request<ResumeAnalysisData>(`/api/v1/resumes/${id}/analysis`);
  },

  uploadResume: async (file: File, resumeId?: number): Promise<APIResponse<ResumeData>> => {
    const formData = new FormData();
    formData.append("file", file);
    if (resumeId) {
      formData.append("resume_id", resumeId.toString());
    }

    const url = `${API_BASE_URL}/api/v1/resumes`;
    const token = getStoredToken();
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    try {
      const response = await fetch(url, {
        method: "POST",
        headers,
        body: formData,
      });

      let body: any = {};
      const text = await response.text();
      if (text) {
        try {
          body = JSON.parse(text);
        } catch {
          body = { message: text };
        }
      }
      if (!response.ok) {
        throw new APIError(body?.message || "Upload failed", response.status, body?.details);
      }
      return body as APIResponse<ResumeData>;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError(error instanceof Error ? error.message : "Upload network error", 0);
    }
  },

  downloadResumeBlob: async (resumeId: number, versionId?: number): Promise<{ blob: Blob; filename: string }> => {
    const query = versionId ? `?version_id=${versionId}` : "";
    const url = `${API_BASE_URL}/api/v1/resumes/${resumeId}/download${query}`;
    const token = getStoredToken();
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    const response = await fetch(url, { headers });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ message: "Download failed" }));
      throw new APIError(body.message || "Download failed", response.status);
    }

    const disposition = response.headers.get("content-disposition");
    let filename = "resume";
    if (disposition && disposition.includes("filename=")) {
      filename = disposition.split("filename=")[1].replace(/["']/g, "");
    }

    const blob = await response.blob();
    return { blob, filename };
  },

  createInterviewSession: (payload: { role: string; difficulty: string; total_questions?: number }) => {
    return request<InterviewSessionData>("/api/v1/interviews", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getUserInterviews: () => {
    return request<InterviewSessionData[]>("/api/v1/interviews");
  },

  getInterviewSession: (id: number) => {
    return request<InterviewSessionData>(`/api/v1/interviews/${id}`);
  },

  submitInterviewAnswer: (id: number, questionId: number, userAnswer: string) => {
    return request<InterviewSessionData>(`/api/v1/interviews/${id}/answer`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, user_answer: userAnswer }),
    });
  },

  getInterviewResults: (id: number) => {
    return request<InterviewResultsData>(`/api/v1/interviews/${id}/results`);
  },

  getPerformanceAnalytics: () => {
    return request<PerformanceData>("/api/v1/performance");
  },

  getPlacementReadiness: () => {
    return request<ReadinessData>("/api/v1/readiness");
  },

  getCodingChallenges: (category?: string, difficulty?: string, search?: string) => {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (difficulty) params.append("difficulty", difficulty);
    if (search) params.append("search", search);
    const q = params.toString() ? `?${params.toString()}` : "";
    return request<CodingChallengeData[]>(`/api/v1/coding/challenges${q}`);
  },

  generateCustomCodingChallenge: (topic: string, category: string = "Python", difficulty: string = "Medium") => {
    return request<CodingChallengeData>("/api/v1/coding/challenges/generate", {
      method: "POST",
      body: JSON.stringify({ topic, category, difficulty }),
    });
  },



  getCodingChallengeDetail: (identifier: string) => {
    return request<CodingChallengeData>(`/api/v1/coding/challenges/${identifier}`);
  },

  submitCodingSolution: (id: number, code: string, language: string = "python") => {
    return request<CodingSubmissionData>(`/api/v1/coding/challenges/${id}/submit`, {
      method: "POST",
      body: JSON.stringify({ code, language }),
    });
  },

  getCodingSubmissions: (id: number) => {
    return request<CodingSubmissionData[]>(`/api/v1/coding/challenges/${id}/submissions`);
  },

  getCodingAIHint: (id: number, code: string) => {
    return request<CodingAIHintData>(`/api/v1/coding/challenges/${id}/hint`, {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  },

  generateCompanyPrepPlan: (companyName: string, targetRole: string) => {
    return request<CompanyPrepData>("/api/v1/company-prep", {
      method: "POST",
      body: JSON.stringify({ company_name: companyName, target_role: targetRole }),
    });
  },

  getSavedCompanyPrepPlans: () => {
    return request<CompanyPrepData[]>("/api/v1/company-prep");
  },

  getCompanyPrepPlanDetail: (id: number) => {
    return request<CompanyPrepData>(`/api/v1/company-prep/${id}`);
  },

  getLearningResources: (filterParams?: {
    skill_name?: string;
    difficulty?: string;
    resource_type?: string;
    search?: string;
    skill_gap_only?: boolean;
  }) => {
    const params = new URLSearchParams();
    if (filterParams?.skill_name) params.append("skill_name", filterParams.skill_name);
    if (filterParams?.difficulty) params.append("difficulty", filterParams.difficulty);
    if (filterParams?.resource_type) params.append("resource_type", filterParams.resource_type);
    if (filterParams?.search) params.append("search", filterParams.search);
    if (filterParams?.skill_gap_only) params.append("skill_gap_only", "true");
    const q = params.toString() ? `?${params.toString()}` : "";
    return request<LearningResourceData[]>(`/api/v1/learning-resources${q}`);
  },

  getRecommendedLearningResources: () => {
    return request<LearningResourceData[]>("/api/v1/learning-resources/recommended");
  },

  updateLearningResourceProgress: (id: number, payload: { is_saved?: boolean; is_completed?: boolean }) => {
    return request<LearningResourceData>(`/api/v1/learning-resources/${id}/progress`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  generateProjectRecommendations: () => {
    return request<ProjectRecommendationData[]>("/api/v1/projects/recommendations", {
      method: "POST",
    });
  },

  getProjectRecommendations: (difficulty?: string, statusFilter?: string) => {
    const params = new URLSearchParams();
    if (difficulty) params.append("difficulty", difficulty);
    if (statusFilter) params.append("status", statusFilter);
    const q = params.toString() ? `?${params.toString()}` : "";
    return request<ProjectRecommendationData[]>(`/api/v1/projects${q}`);
  },

  updateProjectStatus: (id: number, payload: { is_saved?: boolean; status?: string }) => {
    return request<ProjectRecommendationData>(`/api/v1/projects/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  getResumeVersionHistory: (resumeId: number) => {
    return request<ResumeVersionHistoryData>(`/api/v1/resumes/${resumeId}/history`);
  },

  compareResumeVersions: (resumeId: number, v1Id: number, v2Id: number) => {
    return request<ResumeVersionComparisonData>(`/api/v1/resumes/${resumeId}/compare?v1=${v1Id}&v2=${v2Id}`);
  },

  deleteResumeVersion: (resumeId: number, versionId: number) => {
    return request<void>(`/api/v1/resumes/${resumeId}/versions/${versionId}`, {
      method: "DELETE",
    });
  },

  getAchievements: () => {
    return request<AchievementSummaryData>("/api/v1/achievements");
  },

  evaluateAchievements: () => {
    return request<AchievementSummaryData>("/api/v1/achievements/evaluate", {
      method: "POST",
    });
  },

  getNotifications: () => {
    return request<NotificationListData>("/api/v1/notifications");
  },

  readNotification: (id: number) => {
    return request<NotificationData>(`/api/v1/notifications/${id}/read`, {
      method: "PATCH",
    });
  },

  readAllNotifications: () => {
    return request<void>("/api/v1/notifications/read-all", {
      method: "PATCH",
    });
  },

  deleteNotification: (id: number) => {
    return request<void>(`/api/v1/notifications/${id}`, {
      method: "DELETE",
    });
  },

  getNotificationPreferences: () => {
    return request<NotificationPreferenceData>("/api/v1/notifications/preferences");
  },

  updateNotificationPreferences: (payload: Partial<NotificationPreferenceData>) => {
    return request<NotificationPreferenceData>("/api/v1/notifications/preferences", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  getAdminStatistics: () => {
    return request<AdminSystemStatsData>("/api/v1/admin/statistics");
  },

  getAdminUsers: () => {
    return request<AdminUserData[]>("/api/v1/admin/users");
  },

  updateAdminUserRole: (id: number, payload: { role?: string; is_active?: boolean }) => {
    return request<AdminUserData>(`/api/v1/admin/users/${id}/role`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  deleteAdminUser: (id: number) => {
    return request<void>(`/api/v1/admin/users/${id}`, {
      method: "DELETE",
    });
  },

  getAdminQuestions: () => {
    return request<QuestionData[]>("/api/v1/admin/questions");
  },

  createAdminQuestion: (payload: { category: string; topic: string; difficulty: string; question_text: string; sample_answer?: string; explanation?: string }) => {
    return request<QuestionData>("/api/v1/admin/questions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  deleteAdminQuestion: (id: number) => {
    return request<void>(`/api/v1/admin/questions/${id}`, {
      method: "DELETE",
    });
  },

  getAdminResources: () => {
    return request<LearningResourceData[]>("/api/v1/admin/resources");
  },

  createAdminResource: (payload: { title: string; description: string; url: string; skill_name: string; category?: string; difficulty?: string; resource_type?: string }) => {
    return request<LearningResourceData>("/api/v1/admin/resources", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  deleteAdminResource: (id: number) => {
    return request<void>(`/api/v1/admin/resources/${id}`, {
      method: "DELETE",
    });
  },

  getAdminAuditLogs: () => {
    return request<AdminAuditLogData[]>("/api/v1/admin/audit-logs");
  },

  getAdminSettings: () => {
    return request<AdminSettingsData>("/api/v1/admin/settings");
  },

  getHealth: () => {
    return request<HealthData>("/api/v1/health");
  },

  // --- Career Intelligence Methods ---
  analyzeJobDescription: (job_description: string) => {
    return request<JobDescriptionAnalysisData>("/api/v1/career-intelligence/analyze-jd", {
      method: "POST",
      body: JSON.stringify({ job_description }),
    });
  },

  matchResumeToJD: (payload: {
    resume_id: number;
    job_description: string;
    job_title?: string;
    company_name?: string;
    target_occupation_id?: number;
  }) => {
    return request<ResumeJdMatchData>("/api/v1/career-intelligence/match", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getResumeJdMatches: () => {
    return request<ResumeJdMatchHistoryItemData[]>("/api/v1/career-intelligence/matches");
  },

  getResumeJdMatchDetail: (id: number) => {
    return request<ResumeJdMatchData>(`/api/v1/career-intelligence/matches/${id}`);
  },

  generateCoverLetter: (payload: {
    resume_id: number;
    job_description: string;
    job_title: string;
    company_name: string;
    tone?: string;
    length?: string;
  }) => {
    return request<CoverLetterData>("/api/v1/career-intelligence/cover-letter", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getCoverLetters: () => {
    return request<CoverLetterHistoryItemData[]>("/api/v1/career-intelligence/cover-letters");
  },

  // --- Cold Email Generator Methods ---
  generateColdEmail: (payload: ColdEmailGeneratePayload) => {
    return request<ColdEmailData>("/api/v1/career-intelligence/cold-email/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  regenerateColdEmailSubject: (payload: {
    job_title: string;
    company_name: string;
    candidate_name?: string;
    key_skills?: string[];
    email_type?: string;
  }) => {
    return request<{ subject: string }>("/api/v1/career-intelligence/cold-email/regenerate-subject", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getColdEmailHistory: () => {
    return request<ColdEmailHistoryItemData[]>("/api/v1/career-intelligence/cold-email/history");
  },

  getColdEmailDetail: (id: number) => {
    return request<ColdEmailData>(`/api/v1/career-intelligence/cold-email/${id}`);
  },

  updateColdEmail: (id: number, payload: { subject: string; body: string; recruiter_name?: string; recruiter_email?: string }) => {
    return request<ColdEmailData>(`/api/v1/career-intelligence/cold-email/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteColdEmail: (id: number) => {
    return request<boolean>(`/api/v1/career-intelligence/cold-email/${id}`, {
      method: "DELETE",
    });
  },

  // --- Job Market Analyzer Methods ---
  searchJobMarket: (filters?: {
    query?: string;
    location?: string;
    is_remote?: boolean;
    workplace_type?: string;
    experience_level?: string;
    skills?: string;
    company?: string;
    job_type?: string;
    date_posted?: string;
    use_profile?: boolean;
    page?: number;
    limit?: number;
  }) => {
    const params = new URLSearchParams();
    if (filters?.query) params.append("query", filters.query);
    if (filters?.location) params.append("location", filters.location);
    if (filters?.is_remote) params.append("is_remote", "true");
    if (filters?.workplace_type) params.append("workplace_type", filters.workplace_type);
    if (filters?.experience_level) params.append("experience_level", filters.experience_level);
    if (filters?.skills) params.append("skills", filters.skills);
    if (filters?.company) params.append("company", filters.company);
    if (filters?.job_type) params.append("job_type", filters.job_type);
    if (filters?.date_posted) params.append("date_posted", filters.date_posted);
    if (filters?.use_profile) params.append("use_profile", "true");
    if (filters?.page) params.append("page", filters.page.toString());
    if (filters?.limit) params.append("limit", filters.limit.toString());
    const q = params.toString() ? `?${params.toString()}` : "";
    return request<JobMarketSearchResponseData>(`/api/v1/job-market/search${q}`);
  },

  // --- Personal Trainer Methods ---
  getTrainerResumeSkills: () => {
    return request<ResumeSkillsData>("/api/v1/personal-trainer/resume-skills");
  },

  investigateGoal: (payload: {
    goal_dimensions: string[];
    target_skill?: string;
    target_role?: string;
    target_company?: string;
    current_skills: string[];
    experience_level?: string;
    daily_hours?: number;
    target_deadline?: string;
    learning_preference?: string;
  }) => {
    return request<TrainingPlanData>("/api/v1/personal-trainer/investigate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getActiveTrainingPlan: () => {
    return request<TrainingPlanData | null>("/api/v1/personal-trainer/active");
  },

  getDailyTraining: (dayNumber?: number) => {
    const url = dayNumber
      ? `/api/v1/personal-trainer/daily/${dayNumber}`
      : "/api/v1/personal-trainer/daily";
    return request<DailyTrainingViewData>(url);
  },

  updateTrainingTask: (
    taskId: number,
    payload: {
      status: string;
      notes?: string;
      time_spent_minutes?: number;
    }
  ) => {
    return request<TrainingTaskData>(`/api/v1/personal-trainer/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  rescheduleTodayWorkload: (availableHours: number) => {
    return request<DailyTrainingViewData>("/api/v1/personal-trainer/reschedule-today", {
      method: "POST",
      body: JSON.stringify({ available_hours: availableHours }),
    });
  },

  submitDayReview: (dayId: number, confidenceRating: number, feedback?: string) => {
    return request<{ day_id: number; confidence_rating: number; ai_review_recommendation: string }>(
      `/api/v1/personal-trainer/days/${dayId}/review`,
      {
        method: "POST",
        body: JSON.stringify({ confidence_rating: confidenceRating, feedback }),
      }
    );
  },

  getTrainerSettings: () => {
    return request<PersonalTrainerSettingsData>("/api/v1/personal-trainer/settings");
  },

  updateTrainerSettings: (payload: {
    notifications_enabled: boolean;
    preferred_time: string;
    notification_channel: string;
  }) => {
    return request<PersonalTrainerSettingsData>("/api/v1/personal-trainer/settings", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  triggerTrainerWebhook: () => {
    return request<N8nWebhookTriggerData>("/api/v1/personal-trainer/notify-webhook", {
      method: "POST",
    });
  },
};

export default api;
