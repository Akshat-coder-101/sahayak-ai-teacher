from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
import uuid

def get_utc_now():
    return datetime.now(timezone.utc)

# --- Learner Profile Schemas ---
class LearnerProfileCreate(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Learner"
    level: str = "beginner" # beginner | intermediate | advanced
    goal: str = "understand_concept" # exam_prep | conceptual | interview | deep_dive
    preferred_style: str = "visual" # visual | analogies | socratic | code
    language: str = "en" # en | hi | hinglish
    time_budget_minutes: int = 20 # 5 | 20 | 60 | 10080 (7-day)
    depth: str = "standard" # quick | standard | comprehensive
    teacher_personality: str = "socratic" # socratic | friendly | strict_coach | visual

class RelevantLearnerContext(BaseModel):
    user_id: str = "default-user"
    student_level: str = "beginner"
    target_topic: str = ""
    goal: str = "understand_concept"
    preferred_style: str = "visual"
    teacher_personality: str = "socratic" # socratic | friendly | strict_coach | visual
    strong_concepts: List[str] = Field(default_factory=list)
    weak_concepts: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)
    prerequisite_status: Dict[str, str] = Field(default_factory=dict)
    recent_performance: Dict[str, Any] = Field(default_factory=dict)
    pedagogical_instructions: List[str] = Field(default_factory=list)

class LearningRecommendationResult(BaseModel):
    action: str = "MOVE_TO_NEXT_TOPIC" # CONTINUE_CURRENT_TOPIC | REVISE_CONCEPT | PRACTICE_CONCEPT | REASSESS | MOVE_TO_NEXT_TOPIC | SKIP_ALREADY_MASTERED_TOPIC | REVIEW_PREREQUISITE
    topic_id: str
    node_id: Optional[str] = None
    node_title: Optional[str] = None
    reason: str = ""
    evidence: List[str] = Field(default_factory=list)
    prerequisite_gap: Optional[str] = None
    explanation: str = ""

class LearnerProfile(LearnerProfileCreate):
    topics_studied: List[str] = []
    concepts_studied: List[str] = []
    scores_history: List[Dict[str, Any]] = []
    strong_concepts: List[str] = []
    weak_concepts: List[str] = []
    misunderstood_concepts: List[str] = []
    concept_masteries: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    current_learning_path_id: Optional[str] = None
    current_topic: Optional[str] = None
    completed_topics: List[str] = []
    in_progress_topics: List[str] = []
    recommended_next_topic: Optional[str] = None
    recommended_action: Optional[str] = None
    prerequisite_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    active_paths: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=get_utc_now)

# --- Ingestion & RAG Schemas ---
class IngestResponse(BaseModel):
    material_id: str
    filename: str
    total_pages_or_sections: int
    chunks_count: int
    chapters: List[Dict[str, Any]]
    preview: str

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    detected_title: str
    key_topics: List[str]

class Citation(BaseModel):
    chunk_id: Optional[str] = None
    chapter: str = "General"
    page: Optional[int] = None
    section: Optional[str] = None
    quote: Optional[str] = None
    snippet: str = ""
    confidence: float = 0.95

class SourceCitation(BaseModel):
    chunk_id: str
    page: Optional[int] = 1
    quote: str

# --- Lesson Planner Schemas ---
class CheckpointQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "mcq" # mcq | short_answer | problem_solving
    question: str = ""
    options: Optional[List[str]] = None
    correct_answer: str = ""
    hints: Optional[List[str]] = None
    concept_tested: str = ""

class VisualDecision(BaseModel):
    subject: str = "general" # "mathematics" | "physics" | "biology" | "history" | "computer_science" | "general"
    concept_type: str = "conceptual_model" # "quantitative_derivation" | "force_dynamics" | "cellular_process" | "chronological_sequence" | "algorithmic_procedure" | "conceptual_model"
    pedagogical_goal: str = ""
    visual_needed: str = "recommended" # "required" | "recommended" | "optional" | "not_useful"
    visual_type: str = "labeled-diagram" # "equation/graph" | "free_body_diagram" | "labeled-diagram" | "process_cycle" | "timeline/map" | "code+execution" | "array_state" | "none"
    reason: str = ""
    generation_method: str = "svg_diagram" # "interactive_chart" | "svg_diagram" | "timeline_component" | "code_sandbox" | "latex_derivation"
    complexity: str = "simple" # "simple" | "intermediate" | "advanced"
    observation_prompt: str = ""
    knowledge_check: str = ""

class LessonSegmentPlan(BaseModel):
    id: int
    concept: str
    depth: str = "beginner"
    est_minutes: int = 4
    visual_type: str = "labeled-diagram" # equation/graph | labeled-diagram | timeline/map | code+execution | free_body_diagram | process_cycle | array_state
    visual_decision: Optional[VisualDecision] = None
    checkpoint_question: CheckpointQuestion
    summary: str = ""
    source_citations: List[SourceCitation] = []
    citations: List[Citation] = []

class FinalAssessmentSpec(BaseModel):
    type: str = "quiz"
    question_count: int = 4
    difficulty: str = "adaptive"

class LessonPlan(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    objectives: List[str]
    time_budget_minutes: int
    learner_level: str
    language: str
    segments: List[LessonSegmentPlan]
    final_assessment: FinalAssessmentSpec
    material_id: Optional[str] = None
    document_id: Optional[str] = None

class ParsedStudentInstruction(BaseModel):
    raw_instruction: str = ""
    target_chapter: Optional[str] = None # e.g. "Chapter 4"
    time_budget_minutes: int = 20
    language: str = "en" # en | hi | hinglish | ta | te | bn | es
    learner_level: str = "beginner" # beginner | intermediate | advanced
    pedagogical_style: str = "visual" # visual | analogies | socratic | code
    include_checkpoints: bool = True
    include_final_assessment: bool = True
    simple_examples_requested: bool = True
    key_focus_topics: List[str] = Field(default_factory=list)

class InstructionPlanRequest(BaseModel):
    document_id: Optional[str] = None
    material_id: Optional[str] = None
    instruction: str = ""
    learner_profile: Optional[LearnerProfileCreate] = None
    time_budget_minutes: Optional[int] = None
    language: Optional[str] = None

class LessonPlanRequest(BaseModel):
    topic: Optional[str] = None
    material_id: Optional[str] = None
    document_id: Optional[str] = None
    instruction: Optional[str] = None
    target_chapter: Optional[str] = None
    learner_profile: Optional[LearnerProfileCreate] = None
    time_budget_minutes: Optional[int] = 20
    language: Optional[str] = "en"

# --- Visual Specs ---
class MathPhysicsPayload(BaseModel):
    equations: List[str]
    plot_type: str = "2d_function"
    plot_title: str
    plot_x_label: str
    plot_y_label: str
    plot_data: Dict[str, Any]
    step_by_step: List[str]

class BiologyDiagramPayload(BaseModel):
    diagram_title: str
    svg_code: str
    labels: List[Dict[str, Any]]
    key_takeaways: List[str]

class HistoryTimelinePayload(BaseModel):
    timeline_title: str
    events: List[Dict[str, Any]]
    map_context: Optional[Dict[str, Any]] = None

class CodeExecutionPayload(BaseModel):
    language: str = "python"
    code: str
    stdin: Optional[str] = ""
    expected_output: Optional[str] = None
    explanation_steps: List[str]

class VisualSpec(BaseModel):
    type: str
    title: str
    payload: Dict[str, Any]
    decision: Optional[VisualDecision] = None

# --- Rendered Segment Schemas ---
class CaptionItem(BaseModel):
    start_sec: float
    end_sec: float
    text: str

class LessonSegmentRender(BaseModel):
    segment_id: int
    session_id: str
    concept: str
    spoken_script: str
    on_screen_text: str
    visual_spec: VisualSpec
    visual_decision: Optional[VisualDecision] = None
    audio_url: Optional[str] = None
    avatar_video_url: Optional[str] = None
    video_url: Optional[str] = None
    video_status: Optional[str] = "unavailable"
    captions: List[CaptionItem] = []
    citations: List[Citation] = []
    checkpoint_question: CheckpointQuestion
    analogies_used: List[str] = []
    language: str = "en"
    is_reteach: bool = False

# --- Interaction & Misconception Schemas ---
class StudentAnswerRequest(BaseModel):
    session_id: str
    segment_id: int
    student_answer: str
    is_demo_mode: bool = False
    force_misconception: bool = False
    hints_used: Optional[int] = 0
    confidence_rating: Optional[int] = None

class TeachingDecisionState(BaseModel):
    current_concept: str
    student_understanding: str # "mastery" | "partial" | "misconception" | "no_understanding"
    confidence: float = 0.8
    action: str # "advance" | "reteach" | "simplify" | "give_example" | "deepen" | "assess"
    reason: str = ""
    next_step: str = "" # "next_concept" | "explain_with_analogy" | "simpler_example" | "switch_visual" | "final_assessment"
    remaining_time_minutes: int = 15

class InteractionResponse(BaseModel):
    action: str
    classification: str
    feedback: str
    misconception_name: Optional[str] = None
    new_analogy: Optional[str] = None
    new_example: Optional[str] = None
    new_checkpoint_question: Optional[CheckpointQuestion] = None
    reteach_segment: Optional[LessonSegmentRender] = None
    next_segment_id: Optional[int] = None
    transcript: Optional[str] = None
    answer_text: Optional[str] = None
    audio_url: Optional[str] = None
    decision_state: Optional[TeachingDecisionState] = None

class LanguageSwitchRequest(BaseModel):
    session_id: str
    target_language: str
    current_segment_id: int

# --- Assessment & Report Schemas ---
class ConceptAssessmentWeight(BaseModel):
    concept_name: str
    importance: str = "high" # high | medium | low
    lesson_performance: str = "strong" # strong | moderate | struggled | not_evaluated
    weight: float = 0.25
    target_cognitive_level: str = "understand" # recall | understand | apply | analyze
    recommended_question_type: str = "mcq" # mcq | conceptual | short_answer | practical_problem

class AssessmentBlueprint(BaseModel):
    session_id: str
    topic: str
    concepts: List[ConceptAssessmentWeight] = Field(default_factory=list)
    total_questions: int = 4
    difficulty: str = "intermediate"
    prerequisites: List[str] = Field(default_factory=list)

class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "mcq" # mcq | conceptual | short_answer | practical_problem
    concept: str
    question: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str
    cognitive_level: str = "understand" # recall | understand | apply | analyze
    rubric_criteria: Optional[List[str]] = None
    sample_solution_steps: Optional[List[str]] = None
    chunk_id: Optional[str] = None
    segment_id: Optional[int] = None

class Quiz(BaseModel):
    quiz_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    topic: str
    questions: List[QuizQuestion]
    blueprint: Optional[AssessmentBlueprint] = None

class StudentQuizSubmission(BaseModel):
    session_id: str
    answers: Union[Dict[str, str], List[Dict[str, Any]]]

class QuestionGradeResult(BaseModel):
    question_id: str
    concept: str
    is_correct: bool
    evaluation_status: str = "correct" # correct | partially_correct | incorrect | misconception
    partial_score: float = 1.0 # 0.0 to 1.0
    student_answer: str
    correct_answer: str
    feedback: str
    understood_points: List[str] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    misconception_identified: Optional[str] = None

class QuizGradeResponse(BaseModel):
    session_id: str
    total_score: float # Supports partial scores e.g. 3.5
    max_score: int
    score_percentage: float
    results: List[QuestionGradeResult]

class ConceptMasteryItem(BaseModel):
    concept: str
    mastery: str = "strong" # mastered | strong | developing | weak | misunderstood | not_assessed
    score_percent: float = 0.0
    confidence: float = 0.85
    evidence: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)
    revision_needed: bool = False

class GapMapItem(BaseModel):
    concept: str
    segment_id: Optional[int] = None
    citation: Optional[Citation] = None
    recommendation: str

class LearningReport(BaseModel):
    session_id: str
    user_id: str
    topic: str
    score_percent: float
    time_spent_minutes: int
    concepts_understood: List[str]
    weak_areas: List[str]
    misconceptions_encountered: List[str]
    recommended_revision: List[str]
    suggested_next_topics: List[str]
    concept_masteries: List[ConceptMasteryItem] = Field(default_factory=list)
    is_ready_for_next_topic: bool = True
    readiness_reason: str = ""
    actionable_revision_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    gap_map: List[GapMapItem] = []
    generated_at: datetime = Field(default_factory=get_utc_now)

# --- Learning Path Curriculum DAG ---
class PathNode(BaseModel):
    id: str
    title: str
    description: str
    estimated_hours: float = 1.0
    difficulty: str = "beginner" # beginner | intermediate | advanced
    prerequisites: List[str] = Field(default_factory=list)
    completed: bool = False
    score: Optional[float] = None
    status: str = "available" # locked | available | in_progress | completed | mastered | needs_revision | skipped
    concepts: List[str] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)
    prerequisite_reason: Optional[str] = None
    recommended_action: Optional[str] = None

class LearningPath(BaseModel):
    topic_id: str
    user_id: Optional[str] = "default-user"
    subject: Optional[str] = None
    goal: Optional[str] = "understand_concept"
    title: str
    description: str
    nodes: List[PathNode]
    edges: List[Dict[str, str]]
    completion_percentage: float = 0.0
    current_node_id: Optional[str] = None
    recommended_next_node_id: Optional[str] = None
    recommendation: Optional[LearningRecommendationResult] = None
    prerequisite_gaps: List[str] = Field(default_factory=list)

# --- Video Export Job Schemas ---
class ExportJobResponse(BaseModel):
    job_id: str
    session_id: str
    status: str # queued, processing, completed, failed
    progress: int = 0
    video_url: Optional[str] = None
    error_message: Optional[str] = None

class ExportJobStatusResponse(BaseModel):
    job_id: str
    session_id: str
    status: str
    progress: int
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# --- Advanced Features Schemas (Requirement 18) ---

class TeacherPersonalityConfig(BaseModel):
    personality: str # socratic | friendly | strict_coach | visual
    title: str
    description: str
    tone: str
    question_frequency: str # high | medium | focused
    explanation_style: str # guided | conversational | direct | visual
    feedback_style: str # constructive | encouraging | strict | visual_scaffolded

# Flashcards
class FlashcardItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    front: str
    back: str
    concept: str
    difficulty: str = "medium" # easy | medium | hard
    card_type: str = "concept" # definition | formula | concept | qa | example | misconception
    misconception_addressed: Optional[str] = None
    review_status: Optional[str] = "unseen" # unseen | correct | incorrect | needs_review

class FlashcardSet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default-user"
    topic: str
    cards: List[FlashcardItem] = Field(default_factory=list)
    mastery_focus: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=get_utc_now)

class FlashcardReviewRequest(BaseModel):
    user_id: str = "default-user"
    card_id: str
    concept: str
    result: str # correct | incorrect | needs_review

# Automatic Notes
class StudyNotes(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default-user"
    topic: str
    key_ideas: List[str] = Field(default_factory=list)
    definitions: List[Dict[str, str]] = Field(default_factory=list)
    formulas_and_rules: List[Dict[str, str]] = Field(default_factory=list)
    concrete_examples: List[Dict[str, str]] = Field(default_factory=list)
    common_mistakes: List[Dict[str, str]] = Field(default_factory=list)
    summary_markdown: str
    generated_at: datetime = Field(default_factory=get_utc_now)

# Personalized Homework
class HomeworkTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str # practice | challenge | design | conceptual_explanation
    title: str
    instruction: str
    target_concept: str
    difficulty_tier: str # foundational | standard | challenge
    guided_steps: Optional[List[str]] = None
    expected_output_hint: Optional[str] = None

class HomeworkAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default-user"
    topic: str
    tier: str # remedial | standard | advanced
    rationale: str
    tasks: List[HomeworkTask] = Field(default_factory=list)
    suggested_completion_minutes: int = 25
    created_at: datetime = Field(default_factory=get_utc_now)

# Exam Preparation Mode
class ExamPrepMilestone(BaseModel):
    phase: str # Foundation & High-Yield | Targeted Weak Areas | Practice & Speed | Mock Exam & Final Polish
    day_range: str
    focus_topics: List[str]
    weak_areas_addressed: List[str]
    recommended_activities: List[str]
    mock_test_scheduled: bool = False

class ExamPrepPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default-user"
    subject: str
    days_until_exam: int
    target_score_percent: float = 90.0
    daily_study_hours: float = 1.5
    high_weight_topics: List[str] = Field(default_factory=list)
    weak_areas_prioritized: List[str] = Field(default_factory=list)
    strong_areas: List[str] = Field(default_factory=list)
    milestones: List[ExamPrepMilestone] = Field(default_factory=list)
    strategy_summary: str
    created_at: datetime = Field(default_factory=get_utc_now)

class ExamPrepRequest(BaseModel):
    user_id: str = "default-user"
    subject: str
    days_until_exam: int = 14
    target_score_percent: float = 90.0
    daily_study_hours: float = 1.5

# Automatic Study Planner
class StudyPlanTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    activity_type: str # learn | practice | flashcards | revision | assessment
    duration_minutes: int
    concept_or_node: str
    completed: bool = False

class StudyPlanDay(BaseModel):
    day_number: int
    day_label: str
    total_minutes: int
    tasks: List[StudyPlanTask] = Field(default_factory=list)

class StudyPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default-user"
    topic_id: str
    topic_title: str
    total_days: int
    daily_budget_minutes: int
    current_day: int = 1
    days: List[StudyPlanDay] = Field(default_factory=list)
    auto_adjusted: bool = False
    adjustment_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_now)

class StudyPlanRequest(BaseModel):
    user_id: str = "default-user"
    topic_id: str
    daily_minutes: int = 60
    target_days: int = 7

class StudyPlanRecalculateRequest(BaseModel):
    user_id: str = "default-user"
    plan_id: Optional[str] = None
    topic_id: str
    missed_up_to_day: int = 1

# Learning Analytics
class ScoreHistoryPoint(BaseModel):
    topic: str
    score: float
    date: str

class LearningAnalyticsData(BaseModel):
    user_id: str
    name: str
    overall_mastery_percent: float
    total_study_minutes: int
    lessons_completed: int
    questions_answered: int
    topics_mastered_count: int
    learning_trajectory: str # improving | stable | struggling | recovering_after_revision
    trajectory_reason: str
    strong_concepts: List[str] = Field(default_factory=list)
    weak_concepts: List[str] = Field(default_factory=list)
    misunderstood_concepts: List[str] = Field(default_factory=list)
    recent_scores: List[ScoreHistoryPoint] = Field(default_factory=list)
    actionable_recommendations: List[str] = Field(default_factory=list)
    current_learning_path: Optional[str] = None

# Revision Request
class RevisionSessionRequest(BaseModel):
    user_id: str = "default-user"
    topic: Optional[str] = None

