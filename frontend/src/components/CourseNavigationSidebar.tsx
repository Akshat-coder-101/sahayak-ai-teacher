"use client";

import React from "react";
import { 
  Check, 
  Circle, 
  Lock, 
  Play, 
  Clock, 
  ChevronRight, 
  Sparkles,
  BookOpen
} from "lucide-react";
import { LessonPlan, LessonSegmentPlan } from "@/lib/api";

interface CourseNavigationSidebarProps {
  lessonPlan: LessonPlan;
  currentSegmentId: number;
  completedSegmentIds: number[];
  onSelectSegment: (segmentId: number) => void;
  isOpen: boolean;
  onToggle: () => void;
}

export default function CourseNavigationSidebar({
  lessonPlan,
  currentSegmentId,
  completedSegmentIds,
  onSelectSegment,
  isOpen,
  onToggle,
}: CourseNavigationSidebarProps) {
  const total = lessonPlan.segments.length;
  const completedCount = completedSegmentIds.length;
  const progressPercent = Math.round((completedCount / (total || 1)) * 100);

  return (
    <aside
      className={`transition-all duration-300 ease-in-out flex flex-col h-full shrink-0 border-r border-border bg-white z-30 ${
        isOpen
          ? "w-72 sm:w-80 translate-x-0 opacity-100 relative shadow-sm"
          : "w-0 -translate-x-full overflow-hidden border-none opacity-0 pointer-events-none absolute lg:relative"
      }`}
    >
      {/* Sidebar Header */}
      <div className="p-4 border-b border-border bg-white">
        <div className="flex items-center justify-between mb-2">
          <span className="uppercase tracking-wider text-[10px] font-bold text-primary flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5" />
            <span>Course Syllabus</span>
          </span>
          <button
            onClick={onToggle}
            className="p-1.5 rounded-md hover:bg-canvas-elevated text-ink-muted hover:text-ink-primary transition-colors flex items-center gap-1 text-xs font-semibold"
            aria-label="Collapse navigation sidebar"
            title="Collapse Syllabus"
          >
            <span className="text-[11px] text-ink-muted hidden sm:inline">Hide</span>
            <ChevronRight className="w-3.5 h-3.5 rotate-180" />
          </button>
        </div>

        <h2 className="font-bold text-sm text-ink-primary line-clamp-2 leading-snug">
          {lessonPlan.topic}
        </h2>

        {/* Coursera-style 8px Progress Bar */}
        <div className="mt-3 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-ink-secondary font-medium">Course Progress</span>
            <span className="font-bold text-ink-primary">{progressPercent}%</span>
          </div>
          <div className="w-full h-2 bg-[#E8E8E8] rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-[11px] text-ink-muted pt-0.5">
            <span>{completedCount} of {total} completed</span>
            <span className="flex items-center gap-1 font-mono">
              <Clock className="w-3 h-3" />
              {lessonPlan.time_budget_minutes}m
            </span>
          </div>
        </div>
      </div>

      {/* Module / Lesson Tree */}
      <div className="flex-1 overflow-y-auto py-2 scrollbar-thin">
        <div className="space-y-0.5">
          {lessonPlan.segments.map((seg) => {
            const isCurrent = seg.id === currentSegmentId;
            const isCompleted = completedSegmentIds.includes(seg.id);
            const isLocked = seg.id > currentSegmentId && !isCompleted && !completedSegmentIds.includes(seg.id - 1) && seg.id !== 1;

            return (
              <button
                key={seg.id}
                onClick={() => !isLocked && onSelectSegment(seg.id)}
                disabled={isLocked}
                className={`w-full text-left px-4 py-3 transition-colors flex items-start gap-3 relative ${
                  isCurrent
                    ? "bg-[#E9F1FC] border-l-4 border-primary text-ink-primary font-bold"
                    : isCompleted
                    ? "hover:bg-canvas-elevated text-ink-secondary"
                    : isLocked
                    ? "opacity-40 cursor-not-allowed text-[#8A8A8A]"
                    : "hover:bg-canvas-elevated text-[#1F1F1F]"
                }`}
              >
                {/* Coursera-style Status Icon: Mastered = Black check + #0F7B3F dot */}
                <div className="mt-0.5 shrink-0 flex items-center justify-center">
                  {isCompleted ? (
                    <div className="w-4 h-4 rounded-full bg-[#0F7B3F] text-white flex items-center justify-center">
                      <Check className="w-2.5 h-2.5 stroke-[3]" />
                    </div>
                  ) : isCurrent ? (
                    <div className="w-4 h-4 rounded-full bg-primary text-white flex items-center justify-center">
                      <Play className="w-2 h-2 fill-current ml-0.5" />
                    </div>
                  ) : isLocked ? (
                    <Lock className="w-3.5 h-3.5 text-[#8A8A8A]" />
                  ) : (
                    <Circle className="w-3.5 h-3.5 text-border-strong" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1 mb-0.5">
                    <span className="text-[11px] font-semibold text-ink-muted">
                      Part {String(seg.id).padStart(2, "0")}
                    </span>
                    <span className="text-[10px] text-ink-muted font-mono">
                      {seg.est_minutes || 5} min
                    </span>
                  </div>
                  <p className={`text-xs leading-snug line-clamp-2 ${
                    isCurrent ? "text-primary font-bold" : "text-ink-secondary"
                  }`}>
                    {seg.concept}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom Floating Ask AI Tutor Card */}
      <div className="p-3 border-t border-border bg-white">
        <button
          onClick={() => alert("Coursera-style AI Teaching Assistant prompted.")}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded border border-border bg-white hover:bg-canvas-elevated text-ink-primary font-semibold text-xs transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5 text-accent" />
          <span>Ask AI Teaching Assistant</span>
        </button>
      </div>
    </aside>
  );
}
