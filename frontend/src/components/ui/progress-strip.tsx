"use client";

import React from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Sparkles, Lightbulb, Gauge, BookOpen } from "lucide-react";
import { usePrefersReducedMotion } from "./use-reduced-motion";

export interface ProgressStripProps {
  currentSegmentId: number;
  totalSegments: number;
  hintsUsed?: number;
  confidenceRating?: number;
  isReteach?: boolean;
  topic?: string;
  className?: string;
}

export function ProgressStrip({
  currentSegmentId,
  totalSegments,
  hintsUsed = 0,
  confidenceRating,
  isReteach = false,
  topic,
  className = "",
}: ProgressStripProps) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const safeTotal = Math.max(totalSegments, 1);
  const progressPercent = Math.min(100, Math.round((currentSegmentId / safeTotal) * 100));

  return (
    <div
      className={`px-4 py-3 rounded-xl bg-base-100 border border-border shadow-2xs space-y-2.5 ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          <BookOpen className="w-3.5 h-3.5 text-primary" />
          <span className="font-bold text-base-content tracking-tight">
            Curriculum Progress:
          </span>
          <span className="font-mono font-bold text-primary">
            Part {currentSegmentId} of {totalSegments}
          </span>
          {topic && (
            <span className="text-ink-muted text-[11px] truncate max-w-[200px] hidden md:inline">
              · {topic}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {isReteach && (
            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold font-mono bg-accent/10 text-accent border border-accent/20 flex items-center gap-1 animate-pulse">
              <Sparkles className="w-3 h-3" />
              Adaptive Reteach
            </span>
          )}

          {hintsUsed > 0 && (
            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold font-mono bg-base-200 text-ink-secondary flex items-center gap-1">
              <Lightbulb className="w-3 h-3 text-accent" />
              {hintsUsed} Hint{hintsUsed > 1 ? "s" : ""}
            </span>
          )}

          {confidenceRating && (
            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold font-mono bg-primary/10 text-primary border border-primary/20 flex items-center gap-1">
              <Gauge className="w-3 h-3" />
              Pacing {confidenceRating}/5
            </span>
          )}

          <span className="text-[11px] font-mono font-bold text-ink-muted">
            {progressPercent}% Complete
          </span>
        </div>
      </div>

      {/* Progress Bar Track */}
      <div className="h-2 w-full bg-base-200 rounded-full overflow-hidden border border-border/80">
        <motion.div
          className="h-full bg-primary rounded-full"
          style={{ width: `${progressPercent}%` }}
          transition={
            prefersReducedMotion
              ? { duration: 0 }
              : { type: "spring", stiffness: 200, damping: 25 }
          }
        />
      </div>
    </div>
  );
}
