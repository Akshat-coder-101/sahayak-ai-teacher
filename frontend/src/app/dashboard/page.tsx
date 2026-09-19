"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import {
  api,
  TeacherPersonalityConfig,
  FlashcardSet,
  StudyNotes,
  HomeworkAssignment,
  ExamPrepPlan,
  StudyPlan,
  LearningAnalyticsData
} from "@/lib/api";
import {
  TrendingUp,
  Award,
  Clock,
  BrainCircuit,
  Target,
  Sparkles,
  ArrowRight,
  RotateCcw,
  BookOpen,
  Compass,
  FileText,
  Layers,
  GraduationCap,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Zap,
  ChevronRight,
  ChevronLeft,
  RefreshCw,
  Copy,
  Download
} from "lucide-react";
import { StatCard } from "@/components/ui";

type ActiveTab = "analytics" | "personality" | "revision" | "flashcards" | "notes" | "homework" | "examprep" | "planner";

export default function DashboardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { showSuccess, showError, showInfo } = useToast();
  const userId = user?.id || "default-user";

  const [activeTab, setActiveTab] = useState<ActiveTab>("analytics");
  const [isLoading, setIsLoading] = useState(false);

  // Analytics state
  const [analytics, setAnalytics] = useState<LearningAnalyticsData | null>(null);

  // Teacher Personality state
  const [personalities, setPersonalities] = useState<TeacherPersonalityConfig[]>([]);
  const [selectedPersonality, setSelectedPersonality] = useState("socratic");

  // Revision state
  const [revisionTopic, setRevisionTopic] = useState("Machine Learning");
  const [revisionSession, setRevisionSession] = useState<any | null>(null);

  // Flashcards state
  const [flashcardTopic, setFlashcardTopic] = useState("Machine Learning");
  const [flashcards, setFlashcards] = useState<FlashcardSet | null>(null);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);

  // Notes state
  const [notesTopic, setNotesTopic] = useState("Machine Learning");
  const [notes, setNotes] = useState<StudyNotes | null>(null);

  // Homework state
  const [homeworkTopic, setHomeworkTopic] = useState("Machine Learning");
  const [homework, setHomework] = useState<HomeworkAssignment | null>(null);

  // Exam prep state
  const [examSubject, setExamSubject] = useState("Physics");
  const [examDays, setExamDays] = useState(14);
  const [targetScore, setTargetScore] = useState(90);
  const [examPlan, setExamPlan] = useState<ExamPrepPlan | null>(null);

  // Study planner state
  const [planTopic, setPlanTopic] = useState("Machine Learning");
  const [planDays, setPlanDays] = useState(7);
  const [studyPlan, setStudyPlan] = useState<StudyPlan | null>(null);

  // Available topics for dynamic switching
  const [availableTopics, setAvailableTopics] = useState<string[]>([
    "Machine Learning",
    "Principles of Electricity",
    "Quantum Computing",
    "Cellular Respiration"
  ]);

  const switchActiveTopic = (newTopic: string) => {
    setRevisionTopic(newTopic);
    setFlashcardTopic(newTopic);
    setNotesTopic(newTopic);
    setHomeworkTopic(newTopic);
    setPlanTopic(newTopic);
    setExamSubject(newTopic);
    showInfo(`Active study topic switched to: ${newTopic}`);
  };

  // Initial load
  useEffect(() => {
    loadDashboardData();
    loadPersonalities();
  }, [userId]);

  const loadDashboardData = async () => {
    try {
      const [analyticsData, profileData, pathsData] = await Promise.allSettled([
        api.getLearningAnalytics(userId),
        api.getLearnerProfile(userId),
        api.getUserLearningPaths(userId)
      ]);

      const topicsSet = new Set<string>();

      if (analyticsData.status === "fulfilled" && analyticsData.value) {
        setAnalytics(analyticsData.value);
        if (analyticsData.value.current_learning_path) {
          topicsSet.add(analyticsData.value.current_learning_path);
        }
      }

      if (profileData.status === "fulfilled" && profileData.value) {
        if (profileData.value.current_topic) topicsSet.add(profileData.value.current_topic);
        (profileData.value.topics_studied || []).forEach(t => topicsSet.add(t));
        (profileData.value.completed_topics || []).forEach(t => topicsSet.add(t));
      }

      if (pathsData.status === "fulfilled" && pathsData.value) {
        (pathsData.value || []).forEach(p => topicsSet.add(p.title || p.topic_id));
      }

      // Default benchmarks
      ["Machine Learning", "Principles of Electricity", "Quantum Computing", "Cellular Respiration"].forEach(t => topicsSet.add(t));

      const finalTopics = Array.from(topicsSet).filter(Boolean);
      setAvailableTopics(finalTopics);

      // Auto-select latest topic if available
      const latestTopic = finalTopics[0];
      if (latestTopic) {
        setRevisionTopic(latestTopic);
        setFlashcardTopic(latestTopic);
        setNotesTopic(latestTopic);
        setHomeworkTopic(latestTopic);
        setPlanTopic(latestTopic);
        setExamSubject(latestTopic);
      }
    } catch (err) {
      console.warn("Dashboard data initialization error:", err);
    }
  };

  const loadPersonalities = async () => {
    try {
      const list = await api.getTeacherPersonalities();
      setPersonalities(list);
    } catch (err) {
      console.warn("Personalities fetch error:", err);
    }
  };

  const handleSelectPersonality = async (key: string) => {
    setSelectedPersonality(key);
    try {
      await api.setTeacherPersonality(userId, key);
      showSuccess(`Teacher personality set to ${key.replace("_", " ")}!`);
    } catch (err) {
      showError("Failed to update teacher personality");
    }
  };

  const handleGenerateRevision = async () => {
    setIsLoading(true);
    try {
      const session = await api.createRevisionSession(userId, revisionTopic);
      setRevisionSession(session);
      showSuccess("Targeted revision session created!");
    } catch (err) {
      showError("Failed to create revision session");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateFlashcards = async () => {
    setIsLoading(true);
    try {
      const fc = await api.generateFlashcards(flashcardTopic, userId);
      setFlashcards(fc);
      setCurrentCardIndex(0);
      setIsFlipped(false);
      showSuccess(`Generated ${fc.cards.length} targeted flashcards!`);
    } catch (err) {
      showError("Failed to generate flashcards");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReviewFlashcard = async (result: "correct" | "incorrect" | "needs_review") => {
    if (!flashcards || !flashcards.cards[currentCardIndex]) return;
    const currentCard = flashcards.cards[currentCardIndex];
    try {
      await api.reviewFlashcard(userId, currentCard.id, currentCard.concept, result);
      showInfo(`Review recorded (${result}). Mastery updated!`);
      loadDashboardData();
      // Advance to next card
      if (currentCardIndex < flashcards.cards.length - 1) {
        setCurrentCardIndex(prev => prev + 1);
        setIsFlipped(false);
      }
    } catch (err) {
      showError("Failed to record review");
    }
  };

  const handleGenerateNotes = async () => {
    setIsLoading(true);
    try {
      const data = await api.generateNotes(notesTopic, userId);
      setNotes(data);
      showSuccess("Revision notes generated successfully!");
    } catch (err) {
      showError("Failed to generate notes");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateHomework = async () => {
    setIsLoading(true);
    try {
      const data = await api.generateHomework(homeworkTopic, userId);
      setHomework(data);
      showSuccess(`Generated ${data.tier} homework assignment!`);
    } catch (err) {
      showError("Failed to generate homework");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateExamPrep = async () => {
    setIsLoading(true);
    try {
      const data = await api.generateExamPrep({
        user_id: userId,
        subject: examSubject,
        days_until_exam: examDays,
        target_score_percent: targetScore,
        daily_study_hours: 1.5,
      });
      setExamPlan(data);
      showSuccess("Exam preparation track generated!");
    } catch (err) {
      showError("Failed to generate exam prep plan");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateStudyPlan = async () => {
    setIsLoading(true);
    try {
      const data = await api.generateStudyPlan({
        user_id: userId,
        topic_id: planTopic,
        daily_minutes: 60,
        target_days: planDays,
      });
      setStudyPlan(data);
      showSuccess("Study plan generated!");
    } catch (err) {
      showError("Failed to generate study plan");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRecalculatePlan = async () => {
    if (!studyPlan) return;
    setIsLoading(true);
    try {
      const data = await api.recalculateStudyPlan({
        user_id: userId,
        topic_id: planTopic,
        missed_up_to_day: 2,
      });
      setStudyPlan(data);
      showSuccess("Schedule dynamically rebalanced for missed sessions!");
    } catch (err) {
      showError("Failed to recalculate study plan");
    } finally {
      setIsLoading(false);
    }
  };

  const currentCard = flashcards?.cards?.[currentCardIndex];

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-primary">
              Adaptive Learning Intelligence
            </span>
            <span className="text-xs px-2 py-0.5 rounded bg-canvas-elevated text-ink-muted font-mono font-medium">
              Student: {analytics?.name || user?.name || "Learner"}
            </span>
            {analytics?.learning_trajectory && (
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                analytics.learning_trajectory === "improving"
                  ? "bg-emerald-100 text-emerald-800"
                  : analytics.learning_trajectory === "recovering_after_revision"
                  ? "bg-blue-100 text-blue-800"
                  : analytics.learning_trajectory === "struggling"
                  ? "bg-amber-100 text-amber-800"
                  : "bg-neutral-100 text-neutral-800"
              }`}>
                {analytics.learning_trajectory.replace(/_/g, " ")}
              </span>
            )}
          </div>
          <h1 className="text-3xl font-extrabold text-black mt-1">Learning Hub & Advanced Tools</h1>
          <p className="text-sm text-ink-secondary mt-1 font-medium">
            Personalized revision, flashcards, notes, homework, exam tracks, and dynamic study planning powered by continuous mastery tracking.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/topic"
            className="flex items-center gap-1.5 px-4 py-2.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-xs shadow-md transition-all hover:scale-[1.01] active:scale-[0.99]"
          >
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            <span>Launch Lesson</span>
          </Link>
        </div>
      </div>

      {/* Active Study Topic Switcher Strip */}
      <div className="bg-[#E9F1FC]/70 rounded-xl p-3.5 sm:p-4 border border-blue-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs">
        <div className="flex items-center gap-2 flex-wrap">
          <Target className="w-4 h-4 text-primary shrink-0" />
          <span className="text-xs font-bold text-black uppercase tracking-wider">Active Study Topic:</span>
          <span className="text-xs font-extrabold text-primary bg-white px-3 py-1 rounded-md border border-blue-200 shadow-2xs">
            {revisionTopic || "General Studies"}
          </span>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap w-full sm:w-auto">
          <span className="text-[11px] font-semibold text-ink-muted mr-1">Switch Topic:</span>
          {availableTopics.slice(0, 4).map((t, idx) => (
            <button
              key={idx}
              onClick={() => switchActiveTopic(t)}
              className={`text-xs px-2.5 py-1 rounded font-medium transition-all ${
                revisionTopic === t
                  ? "bg-primary text-white font-bold shadow-2xs"
                  : "bg-white text-ink-secondary hover:text-black border border-border hover:border-primary"
              }`}
            >
              {t.split(":")[0].split("&")[0].trim()}
            </button>
          ))}
          <Link
            href="/learning-path"
            className="text-xs text-primary hover:underline font-bold ml-1 flex items-center gap-0.5"
          >
            <span>All Paths</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto border-b border-border pb-2">
        {[
          { id: "analytics", label: "Learning Analytics", icon: TrendingUp },
          { id: "personality", label: "Teacher Personality", icon: Sparkles },
          { id: "revision", label: "Revision Mode", icon: RotateCcw },
          { id: "flashcards", label: "Flashcards Deck", icon: Layers },
          { id: "notes", label: "Revision Notes", icon: FileText },
          { id: "homework", label: "Personalized Homework", icon: Target },
          { id: "examprep", label: "Exam Prep Track", icon: GraduationCap },
          { id: "planner", label: "Study Planner", icon: Calendar },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as ActiveTab)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${
                isActive
                  ? "bg-primary text-white shadow-sm"
                  : "bg-white text-ink-secondary hover:text-black hover:bg-neutral-100 border border-border"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: LEARNING ANALYTICS */}
      {activeTab === "analytics" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Overall Mastery"
              value={`${analytics?.overall_mastery_percent || 0}%`}
              numericValue={analytics?.overall_mastery_percent || 0}
              suffix="%"
              subtext="Calibrated across concept attempts"
              icon={Award}
              color="text-primary"
            />
            <StatCard
              title="Active Study Time"
              value={`${analytics?.total_study_minutes || 0} min`}
              numericValue={analytics?.total_study_minutes || 0}
              suffix=" min"
              subtext="Total duration across sessions"
              icon={Clock}
              color="text-blue-600"
            />
            <StatCard
              title="Questions Answered"
              value={`${analytics?.questions_answered || 0}`}
              numericValue={analytics?.questions_answered || 0}
              subtext="Checkpoints & Quiz problems"
              icon={BrainCircuit}
              color="text-emerald-600"
            />
            <StatCard
              title="Concepts Mastered"
              value={`${analytics?.topics_mastered_count || 0}`}
              numericValue={analytics?.topics_mastered_count || 0}
              subtext="Demonstrated >75% consistency"
              icon={CheckCircle2}
              color="text-purple-600"
            />
          </div>

          {/* Trajectory & Breakdown Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Knowledge Breakdown */}
            <div className="bg-white rounded-lg p-6 border border-border space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-black flex items-center gap-2">
                <Target className="w-4 h-4 text-primary" />
                <span>Concept Mastery Map</span>
              </h2>

              <div className="space-y-3">
                <div>
                  <span className="text-xs font-bold text-emerald-800 flex items-center gap-1.5 mb-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Strong Concepts ({analytics?.strong_concepts.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {analytics?.strong_concepts && analytics.strong_concepts.length > 0 ? (
                      analytics.strong_concepts.map((c, i) => (
                        <span key={i} className="text-xs px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-medium">
                          ✓ {c}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-ink-muted italic">Complete lessons to establish strong concepts</span>
                    )}
                  </div>
                </div>

                <div className="pt-2 border-t border-border">
                  <span className="text-xs font-bold text-amber-800 flex items-center gap-1.5 mb-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    Needs Improvement / Revision ({analytics?.weak_concepts.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {analytics?.weak_concepts && analytics.weak_concepts.length > 0 ? (
                      analytics.weak_concepts.map((c, i) => (
                        <span key={i} className="text-xs px-2.5 py-1 rounded bg-amber-50 text-amber-900 border border-amber-200 font-medium">
                          ⚠ {c}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-ink-muted italic">No weak concepts detected!</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Actionable Recommendations */}
            <div className="bg-white rounded-lg p-6 border border-border space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-black flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <span>Actionable Recommendations</span>
              </h2>
              <div className="space-y-2.5">
                {analytics?.actionable_recommendations.map((rec, i) => (
                  <div key={i} className="p-3 rounded-lg bg-canvas-elevated border border-border text-xs text-ink-secondary flex items-start gap-2.5">
                    <Zap className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <span>{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: TEACHER PERSONALITIES */}
      {activeTab === "personality" && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg p-6 border border-border">
            <h2 className="text-base font-bold text-black mb-1">Select Teacher Personality</h2>
            <p className="text-xs text-ink-secondary mb-6">
              Choose your preferred teaching archetype. All personalities share the exact same factual curriculum correctness while adapting explanation style, question cadence, and feedback tone.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {personalities.map((p) => {
                const isSelected = selectedPersonality === p.personality;
                return (
                  <div
                    key={p.personality}
                    onClick={() => handleSelectPersonality(p.personality)}
                    className={`p-5 rounded-lg border text-left cursor-pointer transition-all ${
                      isSelected
                        ? "bg-[#E9F1FC] border-primary shadow-sm"
                        : "bg-white border-border hover:border-primary/50 hover:bg-canvas-elevated"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className={`font-bold text-sm ${isSelected ? "text-primary" : "text-black"}`}>
                        {p.title}
                      </h3>
                      {isSelected && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-primary text-white font-bold">
                          ACTIVE
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-ink-secondary mb-3 leading-relaxed">
                      {p.description}
                    </p>
                    <div className="flex flex-wrap gap-1.5 text-[10px] text-ink-muted">
                      <span className="px-2 py-0.5 rounded bg-white/70 border border-border font-mono">
                        Tone: {p.tone}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-white/70 border border-border font-mono">
                        Questions: {p.question_frequency}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: REVISION MODE */}
      {activeTab === "revision" && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg p-6 border border-border">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-base font-bold text-black">Targeted Revision Mode</h2>
                <p className="text-xs text-ink-secondary mt-0.5">
                  Inspects your weak & misunderstood concepts to build a laser-focused remediation lesson instead of repeating mastered content.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={revisionTopic}
                  onChange={(e) => setRevisionTopic(e.target.value)}
                  placeholder="Subject / Topic..."
                  className="px-3 py-2 rounded bg-canvas-elevated border border-border text-xs text-black focus:outline-none focus:border-primary"
                />
                <button
                  onClick={handleGenerateRevision}
                  disabled={isLoading}
                  className="px-4 py-2 rounded bg-primary text-white font-bold text-xs hover:bg-blue-600 transition-all flex items-center gap-1.5"
                >
                  <RotateCcw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
                  <span>Generate Revision</span>
                </button>
              </div>
            </div>

            {revisionSession ? (
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
                  <span className="text-xs font-bold text-amber-900 block mb-1">Targeted Weak Concepts:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {revisionSession.weak_concepts_targeted?.map((c: string, idx: number) => (
                      <span key={idx} className="text-xs px-2.5 py-0.5 rounded bg-white border border-amber-300 text-amber-900 font-semibold">
                        ⚠ {c}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-black">Revision Segments</h3>
                  {revisionSession.segments?.map((seg: any) => (
                    <div key={seg.segment_id} className="p-4 rounded-lg bg-canvas-elevated border border-border space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-primary">Segment {seg.segment_id}: {seg.title}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-mono">Focus: {seg.key_concept}</span>
                      </div>
                      <p className="text-xs text-ink-secondary">{seg.teaching_goal}</p>
                      {seg.checkpoint_question && (
                        <div className="p-3 rounded bg-white border border-border text-xs space-y-1 mt-2">
                          <span className="font-bold text-black block">Remediation Check: {seg.checkpoint_question.question}</span>
                          <span className="text-[11px] text-ink-muted block">Correct Principle: {seg.checkpoint_question.correct_answer}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-ink-muted text-xs">
                Click "Generate Revision" to create a targeted session for your weak concepts.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: FLASHCARDS DECK */}
      {activeTab === "flashcards" && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg p-6 border border-border">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-base font-bold text-black">Interactive Flashcards Hub</h2>
                <p className="text-xs text-ink-secondary mt-0.5">
                  Grounded in your actual lesson materials and prioritized by weak concepts. Review answers to update concept mastery in real time.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={flashcardTopic}
                  onChange={(e) => setFlashcardTopic(e.target.value)}
                  placeholder="Topic..."
                  className="px-3 py-2 rounded bg-canvas-elevated border border-border text-xs text-black focus:outline-none focus:border-primary"
                />
                <button
                  onClick={handleGenerateFlashcards}
                  disabled={isLoading}
                  className="px-4 py-2 rounded bg-primary text-white font-bold text-xs hover:bg-blue-600 transition-all flex items-center gap-1.5"
                >
                  <Layers className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
                  <span>Generate Deck</span>
                </button>
              </div>
            </div>

            {flashcards && currentCard ? (
              <div className="max-w-xl mx-auto space-y-6">
                {/* Progress bar */}
                <div className="flex items-center justify-between text-xs text-ink-muted font-medium">
                  <span>Card {currentCardIndex + 1} of {flashcards.cards.length}</span>
                  <span className="capitalize px-2 py-0.5 rounded bg-canvas-elevated border border-border text-[10px]">
                    {currentCard.card_type} • {currentCard.difficulty}
                  </span>
                </div>

                {/* Flip card */}
                <div
                  onClick={() => setIsFlipped(!isFlipped)}
                  className={`min-h-[220px] p-8 rounded-xl border flex flex-col items-center justify-center text-center cursor-pointer transition-all shadow-sm ${
                    isFlipped
                      ? "bg-[#F0FDF4] border-emerald-300 text-emerald-950"
                      : "bg-[#F8FAFC] border-blue-200 text-slate-900 hover:border-primary"
                  }`}
                >
                  <span className="text-[10px] uppercase tracking-wider font-bold text-ink-muted mb-2 block">
                    {isFlipped ? "ANSWER / EXPLANATION" : "QUESTION / PROMPT (Click to Flip)"}
                  </span>
                  <p className="text-base font-bold leading-relaxed">
                    {isFlipped ? currentCard.back : currentCard.front}
                  </p>
                  {isFlipped && currentCard.misconception_addressed && (
                    <span className="mt-4 text-xs text-amber-800 bg-amber-50 px-3 py-1 rounded border border-amber-200 block">
                      ⚠ Clarification: {currentCard.misconception_addressed}
                    </span>
                  )}
                </div>

                {/* Controls & Review Feedback */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        if (currentCardIndex > 0) {
                          setCurrentCardIndex(prev => prev - 1);
                          setIsFlipped(false);
                        }
                      }}
                      disabled={currentCardIndex === 0}
                      className="p-2 rounded border border-border bg-white text-ink-secondary hover:text-black disabled:opacity-40"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        if (currentCardIndex < flashcards.cards.length - 1) {
                          setCurrentCardIndex(prev => prev + 1);
                          setIsFlipped(false);
                        }
                      }}
                      disabled={currentCardIndex === flashcards.cards.length - 1}
                      className="p-2 rounded border border-border bg-white text-ink-secondary hover:text-black disabled:opacity-40"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>

                  {isFlipped && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleReviewFlashcard("incorrect")}
                        className="px-3 py-1.5 rounded bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 text-xs font-bold"
                      >
                        Needs Work
                      </button>
                      <button
                        onClick={() => handleReviewFlashcard("needs_review")}
                        className="px-3 py-1.5 rounded bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 text-xs font-bold"
                      >
                        Uncertain
                      </button>
                      <button
                        onClick={() => handleReviewFlashcard("correct")}
                        className="px-3 py-1.5 rounded bg-emerald-600 text-white hover:bg-emerald-700 text-xs font-bold"
                      >
                        Mastered ✓
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-ink-muted text-xs">
                Click "Generate Deck" to create structured flashcards grounded in your learning topics.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 5: AUTOMATIC REVISION NOTES */}
      {activeTab === "notes" && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg p-6 border border-border">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-base font-bold text-black">Smart Revision Notes</h2>
                <p className="text-xs text-ink-secondary mt-0.5">
                  Generates concise, structured revision notes with definitions, formulas, concrete examples, and common traps.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={notesTopic}
                  onChange={(e) => setNotesTopic(e.target.value)}
                  placeholder="Topic..."
                  className="px-3 py-2 rounded bg-canvas-elevated border border-border text-xs text-black focus:outline-none focus:border-primary"
                />
                <button
                  onClick={handleGenerateNotes}
                  disabled={isLoading}
                  className="px-4 py-2 rounded bg-primary text-white font-bold text-xs hover:bg-blue-600 transition-all flex items-center gap-1.5"
                >
                  <FileText className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
                  <span>Generate Notes</span>
                </button>
              </div>
            </div>

            {notes ? (
              <div className="space-y-6">
                {/* Key Ideas */}
                <div className="p-4 rounded-lg bg-blue-50 border border-blue-200 space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-blue-900">Key Ideas</h3>
                  <ul className="list-disc list-inside text-xs text-blue-950 space-y-1">
                    {notes.key_ideas.map((k, i) => (
                      <li key={i}>{k}</li>
                    ))}
                  </ul>
                </div>

                {/* Formulas & Rules */}
                {notes.formulas_and_rules.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-black">Formulas & Governing Rules</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {notes.formulas_and_rules.map((f, i) => (
                        <div key={i} className="p-3 rounded bg-canvas-elevated border border-border text-xs space-y-1">
                          <span className="font-bold text-black block">{f.name}</span>
                          <code className="text-primary font-mono text-xs font-bold block bg-white px-2 py-1 rounded border border-border">
                            {f.expression}
                          </code>
                          <span className="text-[11px] text-ink-muted block">{f.note}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Common Mistakes */}
                {notes.common_mistakes.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-amber-900">Common Traps & Mistakes to Avoid</h3>
                    <div className="space-y-2">
                      {notes.common_mistakes.map((m, i) => (
                        <div key={i} className="p-3 rounded bg-amber-50 border border-amber-200 text-xs space-y-1">
                          <span className="font-bold text-amber-950 block">⚠ {m.mistake}</span>
                          <span className="text-[11px] text-amber-900 block font-medium">Resolution: {m.how_to_avoid}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-ink-muted text-xs">
                Click "Generate Notes" to create revision-ready structured summaries.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 6: PERSONALIZED HOMEWORK */}
      {activeTab === "homework" && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg p-6 border border-border">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-base font-bold text-black">Adaptive Homework Generator</h2>
                <p className="text-xs text-ink-secondary mt-0.5">
                  Difficulty tier automatically adapts to your demonstrated mastery (Advanced Challenge vs Guided Stepped Practice).
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={homeworkTopic}
                  onChange={(e) => setHomeworkTopic(e.target.value)}
                  placeholder="Topic..."
                  className="px-3 py-2 rounded bg-canvas-elevated border border-border text-xs text-black focus:outline-none focus:border-primary"
                />
                <button
                  onClick={handleGenerateHomework}
                  disabled={isLoading}
                  className="px-4 py-2 rounded bg-primary text-white font-bold text-xs hover:bg-blue-600 transition-all flex items-center gap-1.5"
                >
                  <Target className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
                  <span>Generate Homework</span>
                </button>
              </div>
            </div>

            {homework ? (
              <div className="space-y-4">
                <div className={`p-4 rounded-lg border flex items-center justify-between ${
                  homework.tier === "advanced"
                    ? "bg-purple-50 border-purple-200 text-purple-950"
                    : homework.tier === "remedial"
                    ? "bg-amber-50 border-amber-200 text-amber-950"
                    : "bg-blue-50 border-blue-200 text-blue-950"
                }`}>
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider block">
                      Tier: {homework.tier} Assignment
                    </span>
                    <p className="text-xs mt-0.5">{homework.rationale}</p>
                  </div>
                  <span className="text-xs font-mono px-2.5 py-1 rounded bg-white border border-border font-bold">
                    Est. {homework.suggested_completion_minutes} min
                  </span>
                </div>

                <div className="space-y-3">
                  {homework.tasks.map((task, idx) => (
                    <div key={task.id} className="p-4 rounded-lg bg-canvas-elevated border border-border space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-black">Task {idx + 1}: {task.title}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-white border border-border uppercase font-mono font-bold">
                          {task.task_type}
                        </span>
                      </div>
                      <p className="text-xs text-ink-secondary leading-relaxed">{task.instruction}</p>
                      {task.guided_steps && (
                        <div className="p-3 rounded bg-white border border-border text-xs space-y-1">
                          <span className="font-bold text-primary block">Guided Steps:</span>
                          <ul className="list-decimal list-inside text-ink-secondary space-y-0.5">
                            {task.guided_steps.map((step, sIdx) => (
                              <li key={sIdx}>{step}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-ink-muted text-xs">
                Click "Generate Homework" to produce tailored practice aligned with your current mastery.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 7: EXAM PREPARATION MODE */}
      {activeTab === "examprep" && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg p-6 border border-border">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-base font-bold text-black">Exam Preparation Mode</h2>
                <p className="text-xs text-ink-secondary mt-0.5">
                  Grounded exam track prioritizing high-weight topics, weak areas, timed speed drills, and mock tests.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <input
                  type="text"
                  value={examSubject}
                  onChange={(e) => setExamSubject(e.target.value)}
                  placeholder="Subject..."
                  className="px-3 py-2 rounded bg-canvas-elevated border border-border text-xs text-black focus:outline-none focus:border-primary w-32"
                />
                <input
                  type="number"
                  value={examDays}
                  onChange={(e) => setExamDays(parseInt(e.target.value, 10))}
                  placeholder="Days..."
                  className="px-3 py-2 rounded bg-canvas-elevated border border-border text-xs text-black focus:outline-none focus:border-primary w-20"
                />
                <button
                  onClick={handleGenerateExamPrep}
                  disabled={isLoading}
                  className="px-4 py-2 rounded bg-primary text-white font-bold text-xs hover:bg-blue-600 transition-all flex items-center gap-1.5"
                >
                  <GraduationCap className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
                  <span>Build Exam Track</span>
                </button>
              </div>
            </div>

            {examPlan ? (
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-indigo-50 border border-indigo-200 text-xs text-indigo-950">
                  <span className="font-bold block mb-1">Strategy Overview:</span>
                  <p>{examPlan.strategy_summary}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {examPlan.milestones.map((m, idx) => (
                    <div key={idx} className="p-4 rounded-lg bg-canvas-elevated border border-border space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-black">{m.phase}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-primary/10 text-primary font-mono font-bold">
                          {m.day_range}
                        </span>
                      </div>
                      <div className="text-xs text-ink-secondary space-y-1">
                        <span className="font-medium text-black block">Focus Areas: {m.focus_topics.join(", ")}</span>
                        <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                          {m.recommended_activities.map((act, aIdx) => (
                            <li key={aIdx}>{act}</li>
                          ))}
                        </ul>
                      </div>
                      {m.mock_test_scheduled && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-800">
                          <CheckCircle2 className="w-3 h-3" /> Mock Assessment Scheduled
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-ink-muted text-xs">
                Enter your exam timeline and target score to generate a tailored preparation plan.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 8: AUTOMATIC STUDY PLANNER */}
      {activeTab === "planner" && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg p-6 border border-border">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-base font-bold text-black">Dynamic Study Planner</h2>
                <p className="text-xs text-ink-secondary mt-0.5">
                  Converts curriculum nodes and revision needs into a realistic day-by-day plan. Recalculates dynamically if you fall behind.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={planTopic}
                  onChange={(e) => setPlanTopic(e.target.value)}
                  placeholder="Topic..."
                  className="px-3 py-2 rounded bg-canvas-elevated border border-border text-xs text-black focus:outline-none focus:border-primary"
                />
                <button
                  onClick={handleGenerateStudyPlan}
                  disabled={isLoading}
                  className="px-4 py-2 rounded bg-primary text-white font-bold text-xs hover:bg-blue-600 transition-all flex items-center gap-1.5"
                >
                  <Calendar className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
                  <span>Generate Plan</span>
                </button>
              </div>
            </div>

            {studyPlan ? (
              <div className="space-y-4">
                {studyPlan.auto_adjusted && (
                  <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center gap-2">
                    <RefreshCw className="w-4 h-4 text-amber-600 shrink-0" />
                    <span>{studyPlan.adjustment_reason}</span>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-black">
                    {studyPlan.topic_title} — {studyPlan.total_days} Day Schedule ({studyPlan.daily_budget_minutes} min/day)
                  </span>
                  <button
                    onClick={handleRecalculatePlan}
                    className="px-3 py-1.5 rounded bg-canvas-elevated border border-border hover:bg-white text-xs font-bold text-ink-secondary hover:text-black flex items-center gap-1.5 transition-all shadow-2xs"
                  >
                    <RefreshCw className="w-3.5 h-3.5 text-primary" />
                    <span>Recalculate (Missed Days)</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {studyPlan.days.map((day) => (
                    <div key={day.day_number} className="p-4 rounded-lg bg-canvas-elevated border border-border space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-black">{day.day_label}</span>
                        <span className="text-[10px] text-ink-muted font-mono">{day.total_minutes}m</span>
                      </div>
                      <div className="space-y-1.5">
                        {day.tasks.map((t) => (
                          <div key={t.id} className="p-2 rounded bg-white border border-border text-xs flex items-center justify-between">
                            <span className="font-medium text-black truncate">{t.title}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-canvas-elevated text-ink-muted font-mono">
                              {t.duration_minutes}m
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-ink-muted text-xs">
                Click "Generate Plan" to convert your topic into a structured daily learning schedule.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
