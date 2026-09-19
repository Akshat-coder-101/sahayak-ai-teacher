"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, LearningReport } from "@/lib/api";
import Link from "next/link";
import RelatedVideos from "@/components/RelatedVideos";
import { 
  Award, 
  Check, 
  AlertTriangle, 
  ArrowRight, 
  RotateCcw, 
  Sparkles, 
  Clock, 
  CheckSquare, 
  Compass,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  TrendingUp,
  FileText
} from "lucide-react";

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [report, setReport] = useState<LearningReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadReport() {
      try {
        setIsLoading(true);
        const data = await api.getReport(sessionId);
        setReport(data);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    if (sessionId) loadReport();
  }, [sessionId]);

  if (isLoading) {
    return (
      <div className="py-24 text-center space-y-4">
        <div className="w-14 h-14 rounded bg-[#E9F1FC] text-primary flex items-center justify-center mx-auto animate-pulse">
          <Award className="w-7 h-7" />
        </div>
        <h2 className="text-lg font-bold text-black">Compiling Diagnostic Learning Report</h2>
        <p className="text-xs text-ink-muted">
          Evaluating concept-level mastery states, prerequisite readiness, and actionable revision tasks.
        </p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="py-20 max-w-md mx-auto text-center space-y-4 bg-white rounded-xl border border-border p-8 shadow-2xs">
        <div className="w-12 h-12 rounded-full bg-canvas-elevated flex items-center justify-center mx-auto text-ink-muted">
          <Award className="w-6 h-6" />
        </div>
        <h3 className="font-bold text-sm text-black">No Report Available Yet</h3>
        <p className="text-xs text-ink-secondary">
          No learning diagnostics have been generated for this session. Complete a topic lesson and assessment to view your personalized analytics.
        </p>
        <div className="pt-2 flex justify-center gap-3">
          <Link
            href="/topic"
            className="px-4 py-2 rounded-lg bg-black text-white font-bold text-xs shadow-2xs"
          >
            Start a Lesson
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

  const isReady = report.is_ready_for_next_topic ?? (report.score_percent >= 70);

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Top Banner */}
      <div className="bg-white rounded-lg p-6 sm:p-8 border border-border shadow-2xs">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center sm:text-left">
            <span className="text-xs px-2.5 py-0.5 rounded bg-[#E9F1FC] text-primary font-bold">
              Diagnostic Learning Report
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-black">{report.topic}</h1>
            <p className="text-xs text-ink-muted flex items-center justify-center sm:justify-start gap-4 font-medium">
              <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {report.time_spent_minutes} Minutes Session</span>
              <span>•</span>
              <span>Generated on {new Date(report.generated_at || Date.now()).toLocaleDateString()}</span>
            </p>
          </div>

          {/* Mastery Score Badge */}
          <div className="flex flex-col items-center p-5 rounded-lg bg-canvas-elevated border border-border shadow-2xs min-w-[140px]">
            <span className="text-xs text-ink-muted uppercase font-bold">Overall Score</span>
            <span className="text-4xl font-black text-primary mt-1">
              {Math.round(report.score_percent)}%
            </span>
            <span className={`text-[10px] px-2 py-0.5 rounded font-bold mt-1 border ${
              isReady ? "bg-emerald-50 text-[#0F7B3F] border-emerald-200" : "bg-amber-50 text-amber-800 border-amber-200"
            }`}>
              {isReady ? "Mastery Achieved" : "Revision Required"}
            </span>
          </div>
        </div>
      </div>

      {/* Progression Readiness Banner */}
      <div className={`rounded-lg p-5 border flex items-start gap-4 shadow-2xs ${
        isReady ? "bg-emerald-50/70 border-emerald-300" : "bg-amber-50/80 border-amber-300"
      }`}>
        {isReady ? (
          <ShieldCheck className="w-6 h-6 text-[#0F7B3F] shrink-0 mt-0.5" />
        ) : (
          <ShieldAlert className="w-6 h-6 text-amber-700 shrink-0 mt-0.5" />
        )}
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-sm text-black">
              {isReady ? "Ready to Advance to Next Curriculum Milestone" : "Targeted Revision Required Before Advancing"}
            </h3>
            <span className={`text-[10px] px-2 py-0.2 rounded font-mono font-bold uppercase ${
              isReady ? "bg-[#0F7B3F] text-white" : "bg-amber-700 text-white"
            }`}>
              {isReady ? "Prerequisites Cleared" : "Prerequisite Block"}
            </span>
          </div>
          <p className="text-xs text-ink-secondary leading-relaxed">
            {report.readiness_reason || (
              isReady 
                ? "You have demonstrated strong conceptual understanding with no blocking misconceptions. You are cleared to proceed to next curriculum topics."
                : "Foundational conceptual gaps were identified. Complete the targeted revision exercises below before moving to dependent topics."
            )}
          </p>
        </div>
      </div>

      {/* Concept-Level Mastery Grid */}
      {report.concept_masteries && report.concept_masteries.length > 0 && (
        <div className="bg-white rounded-lg p-6 border border-border space-y-4 shadow-2xs">
          <div className="flex items-center justify-between pb-3 border-b border-border flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h3 className="font-bold text-sm text-black">Concept-Level Mastery Breakdown</h3>
            </div>
            <span className="text-xs text-ink-muted font-medium">
              {report.concept_masteries.length} Taught Concepts Evaluated
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {report.concept_masteries.map((cm, idx) => {
              const statusColor = 
                cm.mastery === "mastered"
                  ? "bg-emerald-50 text-[#0F7B3F] border-emerald-300"
                  : cm.mastery === "strong"
                  ? "bg-blue-50 text-blue-700 border-blue-200"
                  : cm.mastery === "developing"
                  ? "bg-amber-50 text-amber-800 border-amber-300"
                  : cm.mastery === "misunderstood"
                  ? "bg-orange-50 text-orange-800 border-orange-300"
                  : "bg-rose-50 text-rose-800 border-rose-300";

              return (
                <div key={idx} className="p-4 rounded-lg bg-canvas-elevated border border-border space-y-2.5">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-xs text-black truncate max-w-[200px]">{cm.concept}</h4>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold uppercase border ${statusColor}`}>
                      {cm.mastery}
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${
                        cm.score_percent >= 80 ? "bg-[#0F7B3F]" : cm.score_percent >= 60 ? "bg-blue-600" : "bg-amber-600"
                      }`}
                      style={{ width: `${Math.max(5, cm.score_percent)}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-ink-muted font-mono">
                    <span>Mastery: {Math.round(cm.score_percent)}%</span>
                    <span>Confidence: {Math.round(cm.confidence * 100)}%</span>
                  </div>

                  {/* Evidence trail */}
                  {cm.evidence && cm.evidence.length > 0 && (
                    <div className="pt-2 border-t border-border text-[11px] text-ink-secondary space-y-1">
                      <span className="font-bold text-[10px] text-slate-500 uppercase tracking-wider block">Diagnostic Evidence:</span>
                      {cm.evidence.slice(0, 2).map((ev, evIdx) => (
                        <p key={evIdx} className="truncate text-slate-600">• {ev}</p>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Actionable Revision Tasks */}
      <div className="bg-white rounded-lg p-6 border border-border space-y-4 shadow-2xs">
        <div className="flex items-center justify-between pb-3 border-b border-border flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-primary" />
            <h3 className="font-bold text-sm text-black">Actionable Revision Directives</h3>
          </div>
          <span className="text-xs text-ink-muted">
            {report.actionable_revision_tasks?.length || report.recommended_revision.length} Tasks
          </span>
        </div>

        <div className="space-y-2.5">
          {report.actionable_revision_tasks && report.actionable_revision_tasks.length > 0 ? (
            report.actionable_revision_tasks.map((task, i) => (
              <div key={i} className="p-3.5 rounded bg-canvas-elevated border border-border flex items-start justify-between gap-3 text-xs text-ink-secondary hover:border-primary/50 transition-colors">
                <div className="flex items-start gap-2.5">
                  <span className="font-mono text-primary font-bold mt-0.5">{i + 1}.</span>
                  <div className="space-y-0.5">
                    <p className="font-semibold text-black">{task.action}</p>
                    <p className="text-[11px] text-ink-muted font-mono">Target: {task.concept} • Segment {task.segment_id} (Page {task.page || 1})</p>
                  </div>
                </div>
                <Link
                  href={`/lesson/${sessionId}`}
                  className="px-3 py-1 rounded bg-white border border-border text-primary font-bold text-[11px] hover:bg-[#E9F1FC] transition-colors shrink-0"
                >
                  Review
                </Link>
              </div>
            ))
          ) : (
            report.recommended_revision.map((rec, i) => (
              <div key={i} className="p-3 rounded bg-canvas-elevated border border-border text-xs text-ink-secondary flex items-start gap-2.5 font-medium">
                <span className="font-mono text-primary font-bold">{i + 1}.</span>
                <span>{rec}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Document Gap Map (Missed Concepts & Linked Citations) */}
      {report.gap_map && report.gap_map.length > 0 && (
        <div className="bg-white rounded-lg p-6 border border-border space-y-4 shadow-2xs">
          <div className="flex items-center justify-between pb-3 border-b border-border flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse"></span>
              <h3 className="font-bold text-sm text-black">Diagnostic Gap Map & Verified Citations</h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 text-[#B75F00] font-bold border border-amber-200">
              {report.gap_map.length} Document Links
            </span>
          </div>

          <div className="space-y-3">
            {report.gap_map.map((gap, i) => (
              <div key={i} className="p-4 rounded-lg bg-canvas-elevated border border-border space-y-2.5 hover:border-primary/50 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-primary px-2 py-0.5 rounded bg-[#E9F1FC]">
                      Gap #{i + 1}
                    </span>
                    <h4 className="font-bold text-xs text-black">{gap.concept}</h4>
                  </div>
                  {gap.segment_id && (
                    <Link
                      href={`/lesson/${sessionId}`}
                      className="inline-flex items-center gap-1 text-[11px] text-primary font-bold hover:underline"
                    >
                      <span>Review Segment {gap.segment_id}</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  )}
                </div>

                {gap.citation && (
                  <div className="p-2.5 rounded bg-white border border-border/80 text-xs text-ink-secondary space-y-1">
                    <div className="flex items-center justify-between text-[11px] text-ink-muted font-mono">
                      <span>Source: {gap.citation.chapter || "Document Reference"}</span>
                      <span>Page {gap.citation.page || 1}</span>
                    </div>
                    {(gap.citation.quote || gap.citation.snippet) && (
                      <blockquote className="text-xs italic text-ink-primary border-l-2 border-primary pl-2 my-1">
                        "{gap.citation.quote || gap.citation.snippet}"
                      </blockquote>
                    )}
                  </div>
                )}

                <p className="text-xs text-ink-secondary font-medium">
                  👉 <strong className="text-black">Action:</strong> {gap.recommendation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suggested Next Topics in Learning Path */}
      <div className="bg-white rounded-lg p-6 border border-border space-y-4 shadow-2xs">
        <div className="flex items-center justify-between pb-3 border-b border-border flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-primary" />
            <h3 className="font-bold text-sm text-black">
              {isReady ? "Recommended Next Topics in Learning Path" : "Remediation & Milestone Topics"}
            </h3>
          </div>
          <Link
            href={`/learning-path/${encodeURIComponent(report.topic.toLowerCase().replace(/\s+/g, '-'))}`}
            className="text-xs text-primary hover:underline font-bold flex items-center gap-1"
          >
            <span>View Full Curriculum DAG</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {report.suggested_next_topics.map((t, i) => (
            <Link
              key={i}
              href={`/setup?topic=${encodeURIComponent(t)}`}
              className="p-4 rounded bg-white border border-border hover:border-primary hover:bg-[#E9F1FC] transition-all hover:scale-[1.01] group shadow-2xs"
            >
              <span className="text-[10px] text-primary font-bold">Milestone {i + 1}</span>
              <h4 className="font-bold text-xs text-black group-hover:text-primary transition-colors mt-1">
                {t}
              </h4>
            </Link>
          ))}
        </div>
      </div>

      {/* Curated YouTube Video Explanations for Revision & Deep Dives */}
      <RelatedVideos
        topic={report.weak_areas && report.weak_areas.length > 0 ? report.weak_areas[0] : report.topic}
        sessionId={sessionId}
        context={`Targeted revision for ${report.topic}: ${report.weak_areas?.join(', ') || 'Conceptual mastery'}`}
      />

      {/* Actions */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-border">
        <Link
          href={`/lesson/${sessionId}`}
          className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded border border-border hover:bg-canvas-elevated text-xs font-semibold text-ink-primary transition-colors min-h-[42px]"
        >
          <RotateCcw className="w-4 h-4 text-primary" />
          <span>Revise This Lesson</span>
        </Link>

        <Link
          href={isReady ? "/topic" : `/lesson/${sessionId}`}
          className="w-full sm:w-auto flex items-center justify-center gap-2 px-7 py-3 rounded bg-black hover:bg-neutral-800 text-white font-bold text-sm shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] min-h-[44px]"
        >
          <Sparkles className="w-4 h-4" />
          <span>{isReady ? "Start Next Curriculum Topic" : "Start Targeted Revision"}</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}
