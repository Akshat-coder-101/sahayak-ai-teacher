"use client";

import React from "react";
import { 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle2, 
  Lightbulb 
} from "lucide-react";

interface StickyAdaptiveBottomBarProps {
  currentSegmentId: number;
  totalSegments: number;
  isReteachActive: boolean;
  adaptiveMessage?: string;
  onPrevious: () => void;
  onNextOrSubmit: () => void;
  onRequestSimplerExplanation: () => void;
  primaryCtaText?: string;
}

export default function StickyAdaptiveBottomBar({
  currentSegmentId,
  totalSegments,
  isReteachActive,
  adaptiveMessage = "Concept active. Need a simpler analogy or alternative explanation?",
  onPrevious,
  onNextOrSubmit,
  onRequestSimplerExplanation,
  primaryCtaText = "Next Item",
}: StickyAdaptiveBottomBarProps) {
  const isFirst = currentSegmentId <= 1;
  const isLast = currentSegmentId >= totalSegments;

  return (
    <div className="sticky bottom-0 z-30 w-full bg-white border-t border-border coursera-sticky-shadow h-16 px-4 sm:px-8 flex items-center justify-between gap-3">
      {/* Left: Previous Button */}
      <button
        onClick={onPrevious}
        disabled={isFirst}
        className="flex items-center gap-1.5 px-4 py-2 rounded border border-border bg-white hover:bg-canvas-elevated text-xs font-semibold text-ink-primary disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Previous</span>
      </button>

      {/* Center: Coursera-style AI Intervention Notice */}
      <div className="flex-1 max-w-xl mx-2 flex items-center justify-center gap-2 text-center">
        <div className="flex items-center gap-2 px-3 py-1 rounded bg-[#FFF1E6] text-[#B75F00] text-xs font-medium border border-orange-200">
          <Lightbulb className="w-3.5 h-3.5 shrink-0 text-accent" />
          <span className="truncate max-w-[220px] sm:max-w-md text-[11px] sm:text-xs">
            {isReteachActive 
              ? "Adaptive Reteach in progress with new analogy"
              : adaptiveMessage}
          </span>
          <button
            onClick={onRequestSimplerExplanation}
            className="hidden md:inline-flex items-center gap-1 text-[10px] underline font-bold hover:opacity-80 ml-1 text-accent"
          >
            <span>Simpler Explanation?</span>
          </button>
        </div>
      </div>

      {/* Right: Black Primary CTA Button (Coursera Signature) */}
      <button
        onClick={onNextOrSubmit}
        className="flex items-center gap-2 px-6 py-2.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-xs shadow-2xs transition-all hover:scale-[1.01] active:scale-[0.99] shrink-0"
      >
        <span>{isLast ? "Complete Lesson & Take Quiz" : primaryCtaText}</span>
        {isLast ? (
          <CheckCircle2 className="w-4 h-4 text-highlight" />
        ) : (
          <ArrowRight className="w-4 h-4" />
        )}
      </button>
    </div>
  );
}
