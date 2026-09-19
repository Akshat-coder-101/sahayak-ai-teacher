"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, Quiz, QuizGradeResponse } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { recordSessionCompletion } from "@/lib/analytics";
import Link from "next/link";
import { 
  GraduationCap, 
  Check, 
  XCircle, 
  ArrowRight, 
  Sparkles,
  BookOpen,
  HelpCircle,
  Calculator,
  FileText,
  Layers,
  AlertTriangle,
  Lightbulb
} from "lucide-react";

export default function AssessmentPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const { showSuccess, showError } = useToast();
  const sessionId = params.sessionId as string;

  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [gradeResult, setGradeResult] = useState<QuizGradeResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function fetchQuiz() {
      try {
        setIsLoading(true);
        const data = await api.getQuiz(sessionId);
        setQuiz(data);
      } catch (err: any) {
        console.error(err);
        showError("Could not load assessment questions for this session.");
      } finally {
        setIsLoading(false);
      }
    }
    if (sessionId) fetchQuiz();
  }, [sessionId, showError]);

  const handleSelectOption = (questionId: string, option: string) => {
    if (gradeResult) return;
    setAnswers((prev) => ({ ...prev, [questionId]: option }));
  };

  const handleTextAnswerChange = (questionId: string, text: string) => {
    if (gradeResult) return;
    setAnswers((prev) => ({ ...prev, [questionId]: text }));
  };

  const handleGradeQuiz = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quiz) return;

    setIsSubmitting(true);
    try {
      const res = await api.gradeQuiz({
        session_id: sessionId,
        answers,
      });
      setGradeResult(res);
      showSuccess(`Diagnostic evaluation complete! Score: ${Math.round(res.score_percentage)}%`);

      recordSessionCompletion(user?.id || "default-user", {
        topic: quiz.topic,
        score: Math.round(res.score_percentage),
        timeMinutes: 20,
        misconceptionsCount: res.results.filter((r) => r.evaluation_status === "misconception" || !r.is_correct).length,
        status: "Completed",
        date: "Today",
      });
    } catch (err: any) {
      console.error(err);
      showError("Failed to submit and grade assessment. Please retry.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleProceedToReport = () => {
    router.push(`/report/${sessionId}`);
  };

  if (isLoading) {
    return (
      <div className="py-24 text-center space-y-4">
        <div className="w-14 h-14 rounded bg-[#E9F1FC] text-primary flex items-center justify-center mx-auto animate-pulse">
          <GraduationCap className="w-7 h-7" />
        </div>
        <h2 className="text-lg font-bold text-black">Synthesizing Assessment Blueprint</h2>
        <p className="text-xs text-ink-muted">
          Evaluating taught concepts, checkpoint performance, and cognitive levels for rigorous diagnosis.
        </p>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="py-20 max-w-md mx-auto text-center space-y-4 bg-white rounded-xl border border-border p-8 shadow-2xs">
        <div className="w-12 h-12 rounded-full bg-canvas-elevated flex items-center justify-center mx-auto text-ink-muted">
          <BookOpen className="w-6 h-6" />
        </div>
        <h3 className="font-bold text-sm text-black">No Active Assessment Found</h3>
        <p className="text-xs text-ink-secondary">
          No diagnostic quiz was generated for this session ID. Start a lesson to unlock targeted mastery assessments.
        </p>
        <div className="pt-2 flex justify-center gap-3">
          <Link
            href="/topic"
            className="px-4 py-2 rounded-lg bg-black text-white font-bold text-xs shadow-2xs"
          >
            Explore Topics
          </Link>
          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-lg border border-border text-ink-primary font-bold text-xs hover:bg-canvas-elevated"
          >
            Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const answeredCount = Object.values(answers).filter((a) => a && a.trim().length > 0).length;

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <span className="text-xs px-2.5 py-0.5 rounded bg-[#E9F1FC] text-primary font-bold">
            Post-Lesson Diagnostic Assessment
          </span>
          {quiz.blueprint && (
            <span className="text-xs px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-mono font-medium border border-indigo-200">
              Blueprint Difficulty: {quiz.blueprint.difficulty}
            </span>
          )}
        </div>
        <h1 className="text-3xl font-extrabold text-black">{quiz.topic}</h1>
        <p className="text-sm text-ink-secondary mt-1 font-medium">
          Answer the questions below to evaluate conceptual depth, identify potential misconceptions, and generate your personalized learning report.
        </p>
      </div>

      {/* Grade Banner if completed */}
      {gradeResult && (
        <div className="bg-white rounded-lg p-6 border border-emerald-300 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm animate-in fade-in duration-200">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-emerald-50 border-2 border-[#0F7B3F] text-[#0F7B3F] flex items-center justify-center font-black text-xl">
              {Math.round(gradeResult.score_percentage)}%
            </div>
            <div>
              <h3 className="font-bold text-base text-black">Diagnostic Evaluation Complete</h3>
              <p className="text-xs text-ink-secondary">
                Earned {gradeResult.total_score} of {gradeResult.max_score} points across concept milestones.
              </p>
            </div>
          </div>

          <button
            onClick={handleProceedToReport}
            className="flex items-center gap-2 px-6 py-2.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-xs shadow-md transition-all hover:scale-[1.01] active:scale-[0.99]"
          >
            <span>View Mastery & Learning Report</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Questions Stack */}
      <form onSubmit={handleGradeQuiz} className="space-y-6">
        {quiz.questions.map((q, idx) => {
          const result = gradeResult?.results.find((r) => r.question_id === q.id);
          const studentAns = answers[q.id] || "";
          const isMCQ = q.type === "mcq" && q.options && q.options.length > 0;

          return (
            <div
              key={q.id}
              className={`bg-white rounded-lg p-6 border transition-all shadow-2xs ${
                result
                  ? result.evaluation_status === "correct"
                    ? "border-emerald-300 bg-emerald-50/20"
                    : result.evaluation_status === "partially_correct"
                    ? "border-amber-300 bg-amber-50/20"
                    : result.evaluation_status === "misconception"
                    ? "border-orange-300 bg-orange-50/20"
                    : "border-rose-300 bg-rose-50/20"
                  : "border-border"
              }`}
            >
              {/* Question Header */}
              <div className="flex items-center justify-between pb-3 border-b border-border mb-3 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-primary">
                    Question {idx + 1} · {q.concept}
                  </span>
                  <span className="text-[10px] px-2 py-0.2 rounded bg-slate-100 text-slate-700 font-mono uppercase">
                    {q.type.replace(/_/g, " ")} • {q.cognitive_level || "understand"}
                  </span>
                </div>

                {result && (
                  <span className={`text-xs font-bold flex items-center gap-1 ${
                    result.evaluation_status === "correct"
                      ? "text-[#0F7B3F]"
                      : result.evaluation_status === "partially_correct"
                      ? "text-amber-700"
                      : result.evaluation_status === "misconception"
                      ? "text-orange-700"
                      : "text-[#C21E1E]"
                  }`}>
                    {result.evaluation_status === "correct" ? (
                      <Check className="w-4 h-4 stroke-[3]" />
                    ) : result.evaluation_status === "partially_correct" ? (
                      <Layers className="w-4 h-4 text-amber-600" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                    <span className="capitalize">
                      {result.evaluation_status?.replace(/_/g, " ") || (result.is_correct ? "Correct" : "Needs Review")}
                    </span>
                    {result.partial_score !== undefined && (
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white border border-slate-200 ml-1">
                        +{result.partial_score}/1.0
                      </span>
                    )}
                  </span>
                )}
              </div>

              <p className="text-sm font-semibold text-black mb-4 leading-relaxed">{q.question}</p>

              {/* Rubric Criteria Guideline if open-ended */}
              {!isMCQ && q.rubric_criteria && q.rubric_criteria.length > 0 && !result && (
                <div className="mb-3 p-2.5 rounded bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-2">
                  <Lightbulb className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-[10px] text-slate-700 uppercase tracking-wider block">Evaluation Rubric:</span>
                    <span className="text-[11px]">{q.rubric_criteria.join(" • ")}</span>
                  </div>
                </div>
              )}

              {/* MCQ Options vs Open-Ended Inputs */}
              {isMCQ ? (
                <div className="space-y-2">
                  {q.options!.map((opt, optIdx) => {
                    const isSelected = studentAns === opt;
                    return (
                      <button
                        key={optIdx}
                        type="button"
                        onClick={() => handleSelectOption(q.id, opt)}
                        disabled={!!gradeResult}
                        className={`w-full text-left p-3 rounded border text-xs transition-all ${
                          isSelected
                            ? "bg-[#E9F1FC] border-primary text-primary font-bold shadow-2xs"
                            : "bg-white border-border text-ink-secondary hover:border-primary/50 hover:bg-canvas-elevated"
                        }`}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="space-y-2">
                  <textarea
                    rows={3}
                    value={studentAns}
                    onChange={(e) => handleTextAnswerChange(q.id, e.target.value)}
                    disabled={!!gradeResult}
                    placeholder={
                      q.type === "practical_problem"
                        ? "Show your derivation steps and final numerical result..."
                        : "Explain your reasoning clearly in your own words..."
                    }
                    className="w-full p-3 rounded border border-border text-xs text-ink-primary bg-white focus:outline-none focus:border-primary transition-all disabled:bg-slate-50 font-sans"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                    <span>{studentAns.trim().length > 0 ? "Response entered" : "Required response"}</span>
                    <span>{studentAns.trim().split(/\s+/).filter(Boolean).length} words</span>
                  </div>
                </div>
              )}

              {/* Diagnostic Feedback Breakdown */}
              {result && (
                <div className="mt-4 pt-3 border-t border-border space-y-2 text-xs">
                  <p className="text-ink-secondary leading-relaxed font-medium">
                    <span className="font-bold text-black">Feedback: </span>
                    {result.feedback}
                  </p>

                  {/* Understood Points */}
                  {result.understood_points && result.understood_points.length > 0 && (
                    <div className="flex items-start gap-1.5 text-emerald-800 text-[11px] bg-emerald-50/80 p-2 rounded border border-emerald-200">
                      <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold uppercase tracking-wider text-[10px] block">Accurate Intuition:</span>
                        <span>{result.understood_points.join("; ")}</span>
                      </div>
                    </div>
                  )}

                  {/* Missing Reasoning Points */}
                  {result.missing_points && result.missing_points.length > 0 && (
                    <div className="flex items-start gap-1.5 text-amber-800 text-[11px] bg-amber-50/80 p-2 rounded border border-amber-200">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold uppercase tracking-wider text-[10px] block">Missing Reasoning Steps:</span>
                        <span>{result.missing_points.join("; ")}</span>
                      </div>
                    </div>
                  )}

                  {/* Misconception Alert */}
                  {result.misconception_identified && (
                    <div className="flex items-start gap-1.5 text-orange-950 text-[11px] bg-orange-50 p-2 rounded border border-orange-200">
                      <HelpCircle className="w-3.5 h-3.5 text-orange-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold uppercase tracking-wider text-[10px] text-orange-800 block">Underlying Misconception:</span>
                        <span>{result.misconception_identified}</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Submit Quiz CTA */}
        {!gradeResult && (
          <div className="flex items-center justify-between pt-4 border-t border-border flex-wrap gap-3">
            <span className="text-xs text-slate-500 font-medium">
              {answeredCount} of {quiz.questions.length} questions completed
            </span>
            <button
              type="submit"
              disabled={isSubmitting || answeredCount < quiz.questions.length}
              className="flex items-center gap-2 px-8 py-3 rounded bg-black hover:bg-neutral-800 text-white font-bold text-sm shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-40 min-h-[44px]"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isSubmitting ? "Evaluating Conceptual Understanding..." : "Submit & Grade Assessment"}</span>
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
