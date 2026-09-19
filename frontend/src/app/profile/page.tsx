"use client";

import { useEffect, useState } from "react";
import { api, LearnerProfile } from "@/lib/api";
import Link from "next/link";
import { 
  User, 
  Award, 
  History, 
  Compass, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  BookOpen, 
  Sparkles,
  Flame,
  Target,
  Clock
} from "lucide-react";

export default function ProfilePage() {
  const [profile, setProfile] = useState<LearnerProfile | null>(null);
  const [learningHistory, setLearningHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setIsLoading(true);
        const [profileData, histData] = await Promise.all([
          api.getProfile("default-user"),
          api.getLearningHistory("default-user")
        ]);
        setProfile(profileData);
        setLearningHistory(histData);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  if (isLoading) {
    return (
      <div className="py-24 text-center text-ink-muted">Loading Learner Profile & Diagnostics...</div>
    );
  }

  if (!profile) return null;

  const conceptMasteries = profile.concept_masteries || {};
  const masteryEntries = Object.entries(conceptMasteries);

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      {/* Header Profile Card */}
      <div className="bg-white rounded-lg p-6 sm:p-8 border border-border shadow-2xs">
        <div className="flex flex-col sm:flex-row items-center gap-6">
          <div className="w-16 h-16 rounded-full bg-[#E9F1FC] border border-blue-200 flex items-center justify-center shrink-0">
            <User className="w-8 h-8 text-primary" />
          </div>

          <div className="space-y-1.5 text-center sm:text-left flex-1">
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
              <h1 className="text-2xl font-bold text-black">{profile.name}</h1>
              <span className="text-xs px-2.5 py-0.5 rounded bg-[#E9F1FC] text-primary font-bold capitalize">
                {profile.level} Level
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-canvas-elevated border border-border text-ink-secondary font-semibold capitalize">
                {profile.preferred_style} Style
              </span>
            </div>
            <p className="text-xs text-ink-muted font-medium flex flex-wrap items-center justify-center sm:justify-start gap-3">
              <span>Goal: <strong className="text-black capitalize">{profile.goal?.replace("_", " ") || "Understand Concept"}</strong></span>
              <span>•</span>
              <span>Language: <strong className="text-black uppercase">{profile.language}</strong></span>
              <span>•</span>
              <span>Sessions Completed: <strong className="text-black">{profile.scores_history.length}</strong></span>
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-2.5">
            <Link
              href="/learning-path"
              className="px-4 py-2.5 rounded bg-canvas-elevated hover:bg-white text-ink-secondary hover:text-black border border-border font-bold text-xs flex items-center gap-1.5 transition-all shadow-2xs"
            >
              <Compass className="w-4 h-4 text-primary" />
              <span>Curriculum Paths</span>
            </Link>
            <Link
              href="/topic"
              className="px-5 py-2.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-xs shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center gap-1.5"
            >
              <Sparkles className="w-4 h-4 text-accent" />
              <span>Start New Lesson</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Recommended Next Action Banner */}
      {profile.recommended_action && (
        <div className={`p-5 rounded-lg border ${
          profile.recommended_action === "REVISE_CONCEPT"
            ? "bg-amber-50/70 border-amber-200"
            : "bg-[#E9F1FC]/70 border-blue-200"
        } shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4`}>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Target className={`w-4 h-4 ${profile.recommended_action === "REVISE_CONCEPT" ? "text-[#B75F00]" : "text-primary"}`} />
              <span className={`text-xs font-bold uppercase tracking-wide ${
                profile.recommended_action === "REVISE_CONCEPT" ? "text-[#B75F00]" : "text-primary"
              }`}>
                AI Learning Recommendation
              </span>
            </div>
            <h3 className="text-base font-bold text-black">
              {profile.recommended_next_topic || "Continue Learning"}
            </h3>
            <p className="text-xs text-ink-secondary leading-relaxed">
              {profile.recommended_action === "REVISE_CONCEPT"
                ? "Targeted revision is recommended before advancing to downstream topics."
                : "All prerequisite foundations are satisfied. Ready to continue your structured curriculum."}
            </p>
          </div>

          <Link
            href={`/setup?topic=${encodeURIComponent(profile.recommended_next_topic?.replace(/^Revision:\s*/i, "") || "Foundations")}`}
            className="px-4 py-2.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-xs shrink-0 flex items-center gap-1.5 transition-colors shadow-2xs"
          >
            <span>{profile.recommended_action === "REVISE_CONCEPT" ? "Launch Revision Lesson" : "Continue Topic"}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Granular Concept Mastery Grid */}
      <div className="bg-white rounded-lg p-6 border border-border space-y-4 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="font-bold text-sm text-black flex items-center gap-2">
              <Award className="w-4 h-4 text-primary" />
              <span>Evidence-Based Knowledge Model</span>
            </h3>
            <p className="text-xs text-ink-muted mt-0.5">
              Persistent tracking of concepts demonstrated across checkpoint exercises and comprehensive assessments.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-[11px] font-bold">
            <span className="px-2 py-0.5 rounded bg-emerald-50 text-[#0F7B3F] border border-emerald-200">Mastered ({profile.strong_concepts.length})</span>
            <span className="px-2 py-0.5 rounded bg-amber-50 text-[#B75F00] border border-amber-200">Developing/Weak ({profile.weak_concepts.length})</span>
            {profile.misunderstood_concepts && profile.misunderstood_concepts.length > 0 && (
              <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">Misconceptions ({profile.misunderstood_concepts.length})</span>
            )}
          </div>
        </div>

        {masteryEntries.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
            {masteryEntries.map(([conceptName, data]: [string, any]) => {
              const state = data.mastery || "developing";
              const isMastered = state === "mastered" || state === "strong";
              const isMisconception = state === "misunderstood" || (data.misconceptions && data.misconceptions.length > 0);

              let badgeStyle = "bg-blue-50 text-primary border-blue-200";
              if (isMastered) badgeStyle = "bg-emerald-50 text-[#0F7B3F] border-emerald-200";
              else if (isMisconception) badgeStyle = "bg-rose-50 text-rose-700 border-rose-200";
              else if (state === "weak" || state === "developing") badgeStyle = "bg-amber-50 text-[#B75F00] border-amber-200";

              return (
                <div key={conceptName} className="p-3.5 rounded bg-canvas-elevated border border-border space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-bold text-xs text-black leading-tight">{conceptName}</h4>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase border ${badgeStyle} shrink-0`}>
                      {state}
                    </span>
                  </div>

                  {data.assessment_score !== undefined && (
                    <div className="flex items-center justify-between text-[11px] text-ink-muted">
                      <span>Assessment Score:</span>
                      <strong className="text-black">{data.assessment_score}%</strong>
                    </div>
                  )}

                  {data.misconceptions && data.misconceptions.length > 0 && (
                    <div className="text-[11px] text-rose-700 bg-rose-50 p-1.5 rounded border border-rose-100 flex items-start gap-1">
                      <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
                      <span>{data.misconceptions[0]}</span>
                    </div>
                  )}

                  {data.evidence && data.evidence.length > 0 && (
                    <p className="text-[10px] text-ink-muted italic truncate">
                      Evidence: {data.evidence[0]}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-6 text-center text-xs text-ink-muted italic border border-dashed border-border rounded">
            No concepts evaluated yet. Complete your first interactive AI lesson and assessment to build your knowledge model.
          </div>
        )}
      </div>

      {/* Active Curriculum Tracks & Learning History */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Active Learning Paths */}
        <div className="bg-white rounded-lg p-6 border border-border space-y-4 shadow-2xs">
          <h3 className="font-bold text-sm text-black flex items-center gap-2">
            <Compass className="w-4 h-4 text-primary" />
            <span>Active Curriculum Paths</span>
          </h3>

          <div className="space-y-3">
            {profile.active_paths && profile.active_paths.length > 0 ? (
              profile.active_paths.map((p, idx) => (
                <div key={idx} className="p-3.5 rounded bg-canvas-elevated border border-border space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-xs text-black">{p.title || p.topic_id}</h4>
                    <span className="font-mono text-xs font-bold text-primary">{p.progress_percentage}%</span>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="w-full h-1.5 bg-neutral-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${p.progress_percentage}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-ink-muted pt-1">
                    <span>{p.completed_nodes} / {p.total_nodes} modules completed</span>
                    <Link
                      href={`/learning-path/${p.topic_id}`}
                      className="text-primary hover:underline font-bold flex items-center gap-0.5"
                    >
                      <span>View Path</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-ink-muted italic">
                <p>No active paths started.</p>
                <Link href="/learning-path" className="text-primary hover:underline font-semibold block mt-1">
                  Explore Curriculum Paths &rarr;
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Chronological Learning Trajectory */}
        <div className="bg-white rounded-lg p-6 border border-border space-y-4 shadow-2xs">
          <h3 className="font-bold text-sm text-black flex items-center gap-2">
            <History className="w-4 h-4 text-primary" />
            <span>Learning Trajectory</span>
          </h3>

          <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
            {learningHistory.length > 0 ? (
              learningHistory.map((h, i) => (
                <div key={i} className="p-3 rounded bg-canvas-elevated border border-border flex items-center justify-between text-xs">
                  <div className="space-y-0.5">
                    <h4 className="font-bold text-black">{h.topic}</h4>
                    <span className="text-[10px] text-ink-muted block">{h.date?.split("T")[0] || h.date}</span>
                    {h.concepts_mastered && h.concepts_mastered.length > 0 && (
                      <span className="text-[10px] text-[#0F7B3F] font-semibold block">
                        Mastered: {h.concepts_mastered.join(", ")}
                      </span>
                    )}
                  </div>
                  <span className="font-mono font-bold text-[#0F7B3F] bg-emerald-50 px-2 py-1 rounded border border-emerald-200">
                    {h.score}%
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-ink-muted italic">No past sessions recorded yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
