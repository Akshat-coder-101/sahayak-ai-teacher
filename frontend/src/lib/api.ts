const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";

export interface Citation {
  chunk_id?: string;
  chapter: string;
  page?: number;
  section?: string;
  quote?: string;
  snippet: string;
  confidence: number;
}

export interface SourceCitation {
  chunk_id: string;
  page?: number;
  quote: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  detected_title: string;
  key_topics: string[];
}

export interface CheckpointQuestion {
  id: string;
  type: string;
  question: string;
  options?: string[];
  correct_answer: string;
  hints?: string[];
  concept_tested: string;
}

export interface VisualDecision {
  subject: string;
  concept_type: string;
  pedagogical_goal: string;
  visual_needed: string;
  visual_type: string;
  reason: string;
  generation_method: string;
  complexity: string;
  observation_prompt: string;
  knowledge_check: string;
}

export interface LessonSegmentPlan {
  id: number;
  concept: string;
  depth: string;
  est_minutes: number;
  visual_type: string;
  visual_decision?: VisualDecision;
  checkpoint_question: CheckpointQuestion;
  summary: string;
  source_citations?: SourceCitation[];
  citations?: Citation[];
}

export interface LessonPlan {
  session_id: string;
  topic: string;
  objectives: string[];
  time_budget_minutes: number;
  learner_level: string;
  language: string;
  segments: LessonSegmentPlan[];
  final_assessment: {
    type: string;
    question_count: number;
  };
  material_id?: string;
  document_id?: string;
}

export interface VisualSpec {
  type: string;
  title: string;
  payload: any;
  decision?: VisualDecision;
}

export interface CaptionItem {
  start_sec: number;
  end_sec: number;
  text: string;
}

export interface LessonSegmentRender {
  segment_id: number;
  session_id: string;
  concept: string;
  spoken_script: string;
  on_screen_text: string;
  visual_spec: VisualSpec;
  visual_decision?: VisualDecision;
  audio_url?: string;
  avatar_video_url?: string;
  video_url?: string;
  captions: CaptionItem[];
  citations: Citation[];
  checkpoint_question: CheckpointQuestion;
  analogies_used: string[];
  language: string;
  is_reteach: boolean;
}

export interface TeachingDecisionState {
  current_concept: string;
  student_understanding: "mastery" | "partial" | "misconception" | "no_understanding";
  confidence: number;
  action: string;
  reason: string;
  next_step: string;
  remaining_time_minutes: number;
}

export interface ParsedStudentInstruction {
  raw_instruction: string;
  target_chapter?: string;
  time_budget_minutes: number;
  language: string;
  learner_level: string;
  pedagogical_style: string;
  include_checkpoints: boolean;
  include_final_assessment: boolean;
  simple_examples_requested: boolean;
  key_focus_topics: string[];
}

export interface InteractionResponse {
  action: "advance" | "reteach";
  classification: "correct" | "partially_correct" | "misconception" | "no_understanding";
  feedback: string;
  misconception_name?: string;
  new_analogy?: string;
  new_example?: string;
  new_checkpoint_question?: CheckpointQuestion;
  reteach_segment?: LessonSegmentRender;
  next_segment_id?: number;
  transcript?: string;
  answer_text?: string;
  audio_url?: string;
  decision_state?: TeachingDecisionState;
}

export interface ConceptAssessmentWeight {
  concept_name: string;
  importance: string;
  lesson_performance: string;
  weight: number;
  target_cognitive_level: string;
  recommended_question_type: string;
}

export interface AssessmentBlueprint {
  session_id: string;
  topic: string;
  concepts: ConceptAssessmentWeight[];
  total_questions: number;
  difficulty: string;
  prerequisites: string[];
}

export interface QuizQuestion {
  id: string;
  type: string;
  concept: string;
  question: string;
  options?: string[];
  correct_answer: string;
  explanation: string;
  cognitive_level?: string;
  rubric_criteria?: string[];
  sample_solution_steps?: string[];
  chunk_id?: string;
  segment_id?: number;
}

export interface Quiz {
  quiz_id: string;
  session_id: string;
  topic: string;
  questions: QuizQuestion[];
  blueprint?: AssessmentBlueprint;
}

export interface QuestionGradeResult {
  question_id: string;
  concept: string;
  is_correct: boolean;
  evaluation_status?: string;
  partial_score?: number;
  student_answer: string;
  correct_answer: string;
  feedback: string;
  understood_points?: string[];
  missing_points?: string[];
  misconception_identified?: string;
}

export interface QuizGradeResponse {
  session_id: string;
  total_score: number;
  max_score: number;
  score_percentage: number;
  results: QuestionGradeResult[];
}

export interface ConceptMasteryItem {
  concept: string;
  mastery: "mastered" | "strong" | "developing" | "weak" | "misunderstood" | "not_assessed";
  score_percent: number;
  confidence: number;
  evidence: string[];
  misconceptions: string[];
  revision_needed: boolean;
}

export interface GapMapItem {
  concept: string;
  segment_id?: number;
  citation?: Citation;
  recommendation: string;
}

export interface ActionableRevisionTask {
  concept: string;
  segment_id: number;
  action: string;
  page?: number;
  status: string;
}

export interface LearningReport {
  session_id: string;
  user_id: string;
  topic: string;
  score_percent: number;
  time_spent_minutes: number;
  concepts_understood: string[];
  weak_areas: string[];
  misconceptions_encountered: string[];
  recommended_revision: string[];
  suggested_next_topics: string[];
  concept_masteries?: ConceptMasteryItem[];
  is_ready_for_next_topic?: boolean;
  readiness_reason?: string;
  actionable_revision_tasks?: ActionableRevisionTask[];
  gap_map?: GapMapItem[];
  generated_at: string;
}

export interface LearningRecommendationResult {
  action: "CONTINUE_CURRENT_TOPIC" | "REVISE_CONCEPT" | "PRACTICE_CONCEPT" | "REASSESS" | "MOVE_TO_NEXT_TOPIC" | "SKIP_ALREADY_MASTERED_TOPIC" | "REVIEW_PREREQUISITE";
  topic_id: string;
  node_id?: string;
  node_title?: string;
  reason: string;
  evidence: string[];
  prerequisite_gap?: string;
  explanation: string;
}

export interface PathNode {
  id: string;
  title: string;
  description: string;
  estimated_hours: number;
  difficulty: "beginner" | "intermediate" | "advanced";
  prerequisites: string[];
  completed: boolean;
  score?: number;
  status?: "locked" | "available" | "in_progress" | "completed" | "mastered" | "needs_revision" | "skipped";
  concepts?: string[];
  objectives?: string[];
  prerequisite_reason?: string;
  recommended_action?: string;
}

export interface LearningPath {
  topic_id: string;
  user_id?: string;
  subject?: string;
  goal?: string;
  title: string;
  description: string;
  nodes: PathNode[];
  edges: { from: string; to: string }[];
  completion_percentage: number;
  current_node_id?: string;
  recommended_next_node_id?: string;
  recommendation?: LearningRecommendationResult;
  prerequisite_gaps?: string[];
}

export interface LearnerProfile {
  user_id: string;
  name: string;
  level: string;
  goal: string;
  preferred_style: string;
  language: string;
  time_budget_minutes: number;
  depth: string;
  topics_studied: string[];
  concepts_studied?: string[];
  scores_history: any[];
  strong_concepts: string[];
  weak_concepts: string[];
  misunderstood_concepts?: string[];
  concept_masteries?: Record<string, any>;
  current_learning_path_id?: string;
  current_topic?: string;
  completed_topics?: string[];
  in_progress_topics?: string[];
  recommended_next_topic?: string;
  recommended_action?: string;
  prerequisite_gaps?: Array<{ concept: string; status: string; recommended_action: string }>;
  active_paths?: Array<{ topic_id: string; title: string; progress_percentage: number; total_nodes: number; completed_nodes: number }>;
}

/**
 * Universal response handler that parses canonical backend error shapes:
 * { "error": { "code": string, "message": string, "path": string } }
 */
let memoryToken: string | null = null;

export function setAuthToken(token: string | null) {
  memoryToken = token;
  if (typeof window !== "undefined") {
    if (token) {
      localStorage.setItem("sahayak_auth_token", token);
    } else {
      localStorage.removeItem("sahayak_auth_token");
    }
  }
}

export function getAuthToken(): string | null {
  if (memoryToken) return memoryToken;
  if (typeof window !== "undefined") {
    memoryToken = localStorage.getItem("sahayak_auth_token");
  }
  return memoryToken;
}

export async function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const token = getAuthToken();
  const headers = new Headers(init?.headers || {});
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const modifiedInit: RequestInit = {
    ...init,
    headers,
    credentials: init?.credentials || "include",
  };
  return fetch(input, modifiedInit);
}

async function handleApiResponse<T = any>(res: Response, fallbackError: string): Promise<T> {
  if (!res.ok) {
    let errorMsg = fallbackError;
    try {
      const data = await res.json();
      if (data?.error?.message) {
        errorMsg = data.error.message;
      } else if (typeof data?.detail === "string") {
        errorMsg = data.detail;
      } else if (data?.message) {
        errorMsg = data.message;
      }
    } catch {
      errorMsg = `${fallbackError} (Status ${res.status})`;
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export const api = {
  // Document Upload & RAG Grounded Lessons
  uploadDocument: async (file: File): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await authFetch(`${API_BASE_URL}/documents/upload`, {
      method: "POST",
      body: formData,
    });
    return handleApiResponse<DocumentUploadResponse>(res, "Failed to upload and vectorize document");
  },

  parseInstructionForDocument: async (
    documentId: string,
    instruction: string
  ): Promise<ParsedStudentInstruction> => {
    const res = await authFetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}/parse-instruction`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instruction }),
    });
    return handleApiResponse<ParsedStudentInstruction>(res, "Failed to parse student instruction");
  },

  planLessonFromDocument: async (
    documentId: string,
    opts?: {
      time_budget_minutes?: number;
      language?: string;
      learner_profile?: any;
      instruction?: string;
      target_chapter?: string;
    }
  ): Promise<LessonPlan> => {
    const res = await authFetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(opts || {}),
    });
    return handleApiResponse<LessonPlan>(res, "Failed to generate grounded lesson from document");
  },

  // Ingest
  ingestFile: async (formData: FormData) => {
    const res = await authFetch(`${API_BASE_URL}/ingest`, {
      method: "POST",
      body: formData,
    });
    return handleApiResponse(res, "Failed to ingest and parse file");
  },

  // Lesson
  createLessonPlan: async (payload: {
    topic?: string;
    material_id?: string;
    document_id?: string;
    instruction?: string;
    target_chapter?: string;
    learner_profile?: any;
    time_budget_minutes?: number;
    language?: string;
  }): Promise<LessonPlan> => {
    const res = await authFetch(`${API_BASE_URL}/lesson/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleApiResponse<LessonPlan>(res, "Failed to create lesson plan");
  },

  getLessonPlan: async (sessionId: string): Promise<LessonPlan> => {
    const res = await authFetch(`${API_BASE_URL}/lesson/plan/${sessionId}`);
    return handleApiResponse<LessonPlan>(res, "Failed to fetch lesson plan");
  },

  renderSegment: async (
    segmentId: number,
    sessionId: string,
    language?: string
  ): Promise<LessonSegmentRender> => {
    const langParam = language ? `&language=${encodeURIComponent(language)}` : "";
    const res = await authFetch(
      `${API_BASE_URL}/lesson/segment/${segmentId}/render?session_id=${sessionId}${langParam}`,
      { method: "POST" }
    );
    return handleApiResponse<LessonSegmentRender>(res, "Failed to render lesson segment");
  },

  switchLanguage: async (payload: {
    session_id: string;
    target_language: string;
    current_segment_id: number;
  }): Promise<LessonSegmentRender> => {
    const res = await authFetch(`${API_BASE_URL}/lesson/language-switch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleApiResponse<LessonSegmentRender>(res, "Failed to switch audio/video language");
  },

  // Interactivity & Misconceptions
  submitAnswer: async (payload: {
    session_id: string;
    segment_id: number;
    student_answer: string;
    is_demo_mode?: boolean;
    force_misconception?: boolean;
    hints_used?: number;
    confidence_rating?: number;
  }): Promise<InteractionResponse> => {
    const res = await authFetch(`${API_BASE_URL}/interact/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleApiResponse<InteractionResponse>(res, "Failed to submit checkpoint answer");
  },

  submitVoiceAnswer: async (formData: FormData): Promise<InteractionResponse> => {
    const res = await authFetch(`${API_BASE_URL}/interact/voice-answer`, {
      method: "POST",
      body: formData,
    });
    return handleApiResponse<InteractionResponse>(res, "Failed to evaluate voice answer");
  },

  requestSimplification: async (
    sessionId: string,
    segmentId: number,
    query?: string
  ): Promise<InteractionResponse> => {
    const res = await authFetch(`${API_BASE_URL}/interact/request-simplification`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        segment_id: segmentId,
        user_query: query || "Can you explain this more simply with another analogy?",
      }),
    });
    return handleApiResponse<InteractionResponse>(res, "Failed to request adaptive simplification");
  },

  runPythonCode: async (
    code: string,
    timeoutSeconds: number = 5
  ): Promise<{ success: boolean; output?: string; stdout?: string; stderr?: string }> => {
    const res = await authFetch(`${API_BASE_URL}/sandbox/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, timeout_seconds: timeoutSeconds }),
    });
    return handleApiResponse(res, "Failed to execute Python sandbox code");
  },

  // Assessment & Report
  getBlueprint: async (sessionId: string): Promise<AssessmentBlueprint> => {
    const res = await authFetch(`${API_BASE_URL}/assess/blueprint/${sessionId}`);
    return handleApiResponse<AssessmentBlueprint>(res, "Failed to fetch assessment blueprint");
  },

  getQuiz: async (sessionId: string): Promise<Quiz> => {
    const res = await authFetch(`${API_BASE_URL}/assess/quiz/${sessionId}`, {
      method: "POST",
    });
    return handleApiResponse<Quiz>(res, "Failed to generate comprehensive quiz");
  },

  gradeQuiz: async (payload: {
    session_id: string;
    answers: Record<string, string>;
  }): Promise<QuizGradeResponse> => {
    const res = await authFetch(`${API_BASE_URL}/assess/grade`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleApiResponse<QuizGradeResponse>(res, "Failed to grade assessment quiz");
  },

  getReport: async (sessionId: string): Promise<LearningReport> => {
    const res = await authFetch(`${API_BASE_URL}/report/${sessionId}`);
    return handleApiResponse<LearningReport>(res, "Failed to fetch mastery report");
  },

  // Profile & Path
  getProfile: async (userId: string = "default-user"): Promise<LearnerProfile> => {
    const res = await authFetch(`${API_BASE_URL}/profile/${userId}`);
    return handleApiResponse<LearnerProfile>(res, "Failed to fetch learner profile");
  },

  getLearnerProfile: async (userId: string = "default-user"): Promise<LearnerProfile> => {
    const res = await authFetch(`${API_BASE_URL}/profile/${userId}`);
    return handleApiResponse<LearnerProfile>(res, "Failed to fetch learner profile");
  },

  getLearningHistory: async (userId: string = "default-user"): Promise<any[]> => {
    const res = await authFetch(`${API_BASE_URL}/profile/${userId}/learning-history`);
    return handleApiResponse<any[]>(res, "Failed to fetch learning history");
  },

  getUserLearningPaths: async (
    userId: string = "default-user"
  ): Promise<Array<{ id: string; topic_id: string; title: string; progress_percentage: number; node_count: number; updated_at?: string }>> => {
    const res = await authFetch(`${API_BASE_URL}/learning-path?user_id=${userId}`);
    return handleApiResponse<Array<{ id: string; topic_id: string; title: string; progress_percentage: number; node_count: number; updated_at?: string }>>(
      res,
      "Failed to fetch user learning paths"
    );
  },

  getLearningPath: async (
    topicId: string,
    userId: string = "default-user"
  ): Promise<LearningPath> => {
    const res = await authFetch(
      `${API_BASE_URL}/learning-path/${encodeURIComponent(topicId)}?user_id=${userId}`
    );
    return handleApiResponse<LearningPath>(res, "Failed to fetch pedagogical learning path");
  },

  generateLearningPath: async (
    topic: string,
    userId: string = "default-user",
    goal: string = "understand_concept",
    learnerLevel: string = "beginner"
  ): Promise<LearningPath> => {
    const res = await authFetch(`${API_BASE_URL}/learning-path/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, user_id: userId, goal, learner_level: learnerLevel })
    });
    return handleApiResponse<LearningPath>(res, "Failed to generate learning path");
  },

  getNextTopicRecommendation: async (
    topicId: string,
    userId: string = "default-user"
  ): Promise<LearningRecommendationResult> => {
    const res = await authFetch(`${API_BASE_URL}/learning-path/${encodeURIComponent(topicId)}/next?user_id=${userId}`);
    return handleApiResponse<LearningRecommendationResult>(res, "Failed to fetch next topic recommendation");
  },

  regenerateLearningPath: async (
    topicId: string,
    userId: string = "default-user",
    goal: string = "understand_concept",
    learnerLevel: string = "beginner"
  ): Promise<LearningPath> => {
    const res = await authFetch(`${API_BASE_URL}/learning-path/${encodeURIComponent(topicId)}/regenerate?user_id=${userId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic: topicId, user_id: userId, goal, learner_level: learnerLevel, force_regenerate: true })
    });
    return handleApiResponse<LearningPath>(res, "Failed to regenerate learning path");
  },

  togglePathNode: async (
    topicId: string,
    nodeId: string,
    userId: string = "default-user"
  ): Promise<LearningPath> => {
    const res = await authFetch(
      `${API_BASE_URL}/learning-path/${encodeURIComponent(
        topicId
      )}/toggle-node/${nodeId}?user_id=${userId}`,
      { method: "POST" }
    );
    return handleApiResponse<LearningPath>(res, "Failed to toggle learning node completion");
  },

  // YouTube Grounded Video Recommendations
  getRelatedVideos: async (
    topic: string,
    language: string = "en",
    opts?: { segment_id?: number; session_id?: string; context?: string }
  ): Promise<RelatedVideosResponse> => {
    const params = new URLSearchParams({
      topic,
      language,
      ...(opts?.segment_id ? { segment_id: String(opts.segment_id) } : {}),
      ...(opts?.session_id ? { session_id: opts.session_id } : {}),
      ...(opts?.context ? { context: opts.context } : {}),
    });
    const res = await authFetch(`${API_BASE_URL}/videos/recommend?${params.toString()}`);
    return handleApiResponse<RelatedVideosResponse>(res, "Failed to fetch related educational videos");
  },

  // Lesson MP4 Video Export Pipeline
  exportLessonVideo: async (sessionId: string): Promise<ExportJobResponse> => {
    const res = await authFetch(`${API_BASE_URL}/lesson/${sessionId}/export`, {
      method: "POST",
    });
    return handleApiResponse<ExportJobResponse>(res, "Failed to start lesson video export");
  },

  getExportJobStatus: async (jobId: string): Promise<ExportJobStatusResponse> => {
    const res = await authFetch(`${API_BASE_URL}/lesson/export/${jobId}/status`);
    return handleApiResponse<ExportJobStatusResponse>(res, "Failed to fetch export job status");
  },

  getExportDownloadUrl: (jobId: string): string => {
    return `${API_BASE_URL}/lesson/export/${jobId}/download`;
  },

  // --- Advanced Study Tools (Requirement 18) ---

  // 1. Teacher Personalities
  getTeacherPersonalities: async (): Promise<TeacherPersonalityConfig[]> => {
    const res = await authFetch(`${API_BASE_URL}/study-tools/personalities`);
    return handleApiResponse<TeacherPersonalityConfig[]>(res, "Failed to fetch teacher personalities");
  },

  setTeacherPersonality: async (userId: string, personality: string): Promise<any> => {
    const res = await authFetch(`${API_BASE_URL}/study-tools/personalities/select?user_id=${encodeURIComponent(userId)}&personality=${encodeURIComponent(personality)}`, {
      method: "POST",
    });
    return handleApiResponse<any>(res, "Failed to set teacher personality");
  },

  // 2. Revision Mode
  createRevisionSession: async (userId: string, topic?: string): Promise<any> => {
    const res = await authFetch(`${API_BASE_URL}/study-tools/revision-session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, topic }),
    });
    return handleApiResponse<any>(res, "Failed to generate revision session");
  },

  // 3. Flashcards
  generateFlashcards: async (topic: string, userId: string = "default-user", sessionId?: string): Promise<FlashcardSet> => {
    const params = new URLSearchParams({
      topic,
      user_id: userId,
      ...(sessionId ? { session_id: sessionId } : {}),
    });
    const res = await authFetch(`${API_BASE_URL}/study-tools/flashcards/generate?${params.toString()}`, {
      method: "POST",
    });
    return handleApiResponse<FlashcardSet>(res, "Failed to generate flashcards");
  },

  reviewFlashcard: async (userId: string, cardId: string, concept: string, result: "correct" | "incorrect" | "needs_review"): Promise<any> => {
    const res = await authFetch(`${API_BASE_URL}/study-tools/flashcards/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, card_id: cardId, concept, result }),
    });
    return handleApiResponse<any>(res, "Failed to record flashcard review");
  },

  // 4. Automatic Notes
  generateNotes: async (topic: string, userId: string = "default-user", sessionId?: string): Promise<StudyNotes> => {
    const params = new URLSearchParams({
      topic,
      user_id: userId,
      ...(sessionId ? { session_id: sessionId } : {}),
    });
    const res = await authFetch(`${API_BASE_URL}/study-tools/notes/generate?${params.toString()}`, {
      method: "POST",
    });
    return handleApiResponse<StudyNotes>(res, "Failed to generate study notes");
  },

  // 5. Personalized Homework
  generateHomework: async (topic: string, userId: string = "default-user", sessionId?: string): Promise<HomeworkAssignment> => {
    const params = new URLSearchParams({
      topic,
      user_id: userId,
      ...(sessionId ? { session_id: sessionId } : {}),
    });
    const res = await authFetch(`${API_BASE_URL}/study-tools/homework/generate?${params.toString()}`, {
      method: "POST",
    });
    return handleApiResponse<HomeworkAssignment>(res, "Failed to generate personalized homework");
  },

  // 6. Exam Preparation Mode
  generateExamPrep: async (request: ExamPrepRequest): Promise<ExamPrepPlan> => {
    const res = await authFetch(`${API_BASE_URL}/study-tools/exam-prep/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return handleApiResponse<ExamPrepPlan>(res, "Failed to generate exam prep plan");
  },

  // 7. Automatic Study Planner
  generateStudyPlan: async (request: StudyPlanRequest): Promise<StudyPlan> => {
    const res = await authFetch(`${API_BASE_URL}/study-tools/study-plan/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return handleApiResponse<StudyPlan>(res, "Failed to generate study plan");
  },

  recalculateStudyPlan: async (request: StudyPlanRecalculateRequest): Promise<StudyPlan> => {
    const res = await authFetch(`${API_BASE_URL}/study-tools/study-plan/recalculate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return handleApiResponse<StudyPlan>(res, "Failed to recalculate study plan");
  },

  // 8. Learning Analytics
  getLearningAnalytics: async (userId: string): Promise<LearningAnalyticsData> => {
    const res = await authFetch(`${API_BASE_URL}/study-tools/analytics/${encodeURIComponent(userId)}`);
    return handleApiResponse<LearningAnalyticsData>(res, "Failed to fetch learning analytics");
  },

  // 9. Authentication & User Profile
  login: async (email: string, password: string) => {
    const res = await authFetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await handleApiResponse(res, "Login failed");
    if (data?.access_token) {
      setAuthToken(data.access_token);
    }
    return data;
  },

  register: async (payload: { email: string; password: string; name?: string; role?: string; level?: string }) => {
    const res = await authFetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await handleApiResponse(res, "Registration failed");
    if (data?.access_token) {
      setAuthToken(data.access_token);
    }
    return data;
  },

  logout: async () => {
    setAuthToken(null);
    try {
      await authFetch(`${API_BASE_URL}/auth/logout`, { method: "POST" });
    } catch {
      // ignore network errors on logout
    }
  },

  getMe: async () => {
    const res = await authFetch(`${API_BASE_URL}/auth/me`);
    return handleApiResponse(res, "Failed to fetch active session");
  },
};

export interface ExportJobResponse {
  job_id: string;
  session_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  video_url?: string;
  error_message?: string;
}

export interface ExportJobStatusResponse {
  job_id: string;
  session_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  video_url?: string;
  error_message?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RelatedVideo {
  video_id: string;
  title: string;
  channel: string;
  thumbnail_url: string;
  embed_url: string;
  watch_url: string;
  duration: string;
}

export interface RelatedVideosResponse {
  source: "youtube" | "cache" | "fallback";
  videos: RelatedVideo[];
  search_url: string;
}

// --- Advanced Feature Schemas (Requirement 18) ---

export interface TeacherPersonalityConfig {
  personality: string;
  title: string;
  description: string;
  tone: string;
  question_frequency: string;
  explanation_style: string;
  feedback_style: string;
}

export interface FlashcardItem {
  id: string;
  front: string;
  back: string;
  concept: string;
  difficulty: "easy" | "medium" | "hard";
  card_type: "definition" | "formula" | "concept" | "qa" | "example" | "misconception";
  misconception_addressed?: string;
  review_status?: "unseen" | "correct" | "incorrect" | "needs_review";
}

export interface FlashcardSet {
  id: string;
  user_id: string;
  topic: string;
  cards: FlashcardItem[];
  mastery_focus: string[];
  created_at: string;
}

export interface StudyNotes {
  id: string;
  user_id: string;
  topic: string;
  key_ideas: string[];
  definitions: Array<{ term: string; definition: string }>;
  formulas_and_rules: Array<{ name: string; expression: string; note: string }>;
  concrete_examples: Array<{ title: string; explanation: string }>;
  common_mistakes: Array<{ mistake: string; how_to_avoid: string }>;
  summary_markdown: string;
  generated_at: string;
}

export interface HomeworkTask {
  id: string;
  task_type: "practice" | "challenge" | "design" | "conceptual_explanation";
  title: string;
  instruction: string;
  target_concept: string;
  difficulty_tier: "foundational" | "standard" | "challenge";
  guided_steps?: string[];
  expected_output_hint?: string;
}

export interface HomeworkAssignment {
  id: string;
  user_id: string;
  topic: string;
  tier: "remedial" | "standard" | "advanced";
  rationale: string;
  tasks: HomeworkTask[];
  suggested_completion_minutes: number;
  created_at: string;
}

export interface ExamPrepMilestone {
  phase: string;
  day_range: string;
  focus_topics: string[];
  weak_areas_addressed: string[];
  recommended_activities: string[];
  mock_test_scheduled: boolean;
}

export interface ExamPrepPlan {
  id: string;
  user_id: string;
  subject: string;
  days_until_exam: number;
  target_score_percent: number;
  daily_study_hours: number;
  high_weight_topics: string[];
  weak_areas_prioritized: string[];
  strong_areas: string[];
  milestones: ExamPrepMilestone[];
  strategy_summary: string;
  created_at: string;
}

export interface ExamPrepRequest {
  user_id: string;
  subject: string;
  days_until_exam?: number;
  target_score_percent?: number;
  daily_study_hours?: number;
}

export interface StudyPlanTask {
  id: string;
  title: string;
  activity_type: "learn" | "practice" | "flashcards" | "revision" | "assessment";
  duration_minutes: number;
  concept_or_node: string;
  completed?: boolean;
}

export interface StudyPlanDay {
  day_number: number;
  day_label: string;
  total_minutes: number;
  tasks: StudyPlanTask[];
}

export interface StudyPlan {
  id: string;
  user_id: string;
  topic_id: string;
  topic_title: string;
  total_days: number;
  daily_budget_minutes: number;
  current_day: number;
  days: StudyPlanDay[];
  auto_adjusted: boolean;
  adjustment_reason?: string;
  created_at: string;
}

export interface StudyPlanRequest {
  user_id: string;
  topic_id: string;
  daily_minutes?: number;
  target_days?: number;
}

export interface StudyPlanRecalculateRequest {
  user_id: string;
  plan_id?: string;
  topic_id: string;
  missed_up_to_day: number;
}

export interface ScoreHistoryPoint {
  topic: string;
  score: number;
  date: string;
}

export interface LearningAnalyticsData {
  user_id: string;
  name: string;
  overall_mastery_percent: number;
  total_study_minutes: number;
  lessons_completed: number;
  questions_answered: number;
  topics_mastered_count: number;
  learning_trajectory: "improving" | "stable" | "struggling" | "recovering_after_revision";
  trajectory_reason: string;
  strong_concepts: string[];
  weak_concepts: string[];
  misunderstood_concepts: string[];
  recent_scores: ScoreHistoryPoint[];
  actionable_recommendations: string[];
  current_learning_path?: string;
}



