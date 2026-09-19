"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Gauge, ArrowRight, CheckCircle, RefreshCw } from "lucide-react";
import { usePrefersReducedMotion } from "./use-reduced-motion";

export interface AdaptiveSliderProps {
  value: number; // 1 to 5
  onChange: (val: number) => void;
  onRequestSimplification?: () => void;
  onConfirmConfidence?: (val: number) => void;
  isReteaching?: boolean;
  className?: string;
}

const CONFIDENCE_LEVELS = [
  {
    level: 1,
    label: "Too Fast",
    detail: "Struggling with core concept; need simpler analogy",
    color: "text-[#C21E1E]",
    badgeBg: "bg-rose-50 border-rose-200 text-[#C21E1E]",
    action: "reteach",
    actionLabel: "Request Simpler Analogy",
  },
  {
    level: 2,
    label: "Need Help",
    detail: "Partially grasped; would benefit from a simpler breakdown",
    color: "text-accent",
    badgeBg: "bg-orange-50 border-orange-200 text-accent",
    action: "reteach",
    actionLabel: "Request Simpler Step",
  },
  {
    level: 3,
    label: "Paced Well",
    detail: "Understood standard explanation; ready for checkpoint",
    color: "text-primary",
    badgeBg: "bg-blue-50 border-blue-200 text-primary",
    action: "advance",
    actionLabel: "Continue at Normal Pace",
  },
  {
    level: 4,
    label: "Clear",
    detail: "Solid comprehension of principles & math/diagrams",
    color: "text-success",
    badgeBg: "bg-emerald-50 border-emerald-200 text-success",
    action: "advance",
    actionLabel: "Advance Confidently",
  },
  {
    level: 5,
    label: "High Mastery",
    detail: "Fully grasped; ready for advanced challenge questions",
    color: "text-success",
    badgeBg: "bg-emerald-50 border-emerald-200 text-success",
    action: "advance",
    actionLabel: "Advance to Next Module",
  },
];

export function AdaptiveSlider({
  value,
  onChange,
  onRequestSimplification,
  onConfirmConfidence,
  isReteaching = false,
  className = "",
}: AdaptiveSliderProps) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const currentLevel = CONFIDENCE_LEVELS.find((l) => l.level === value) || CONFIDENCE_LEVELS[2];
  const isLowConfidence = value <= 2;

  const percentage = ((value - 1) / 4) * 100;

  return (
    <div className={`p-4 sm:p-5 rounded-xl bg-base-100 border border-border shadow-2xs space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-3">
        <div className="flex items-center gap-2">
          <Gauge className="w-4 h-4 text-primary" />
          <span className="font-bold text-xs sm:text-sm text-base-content">
            Adaptive Comprehension & Pacing Gauge
          </span>
        </div>
        <span
          className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold font-mono border ${currentLevel.badgeBg}`}
        >
          {value}/5 · {currentLevel.label}
        </span>
      </div>

      {/* Slider Interactive Track (Watermelon UI Animated Slider) */}
      <div className="space-y-3 pt-1">
        <div className="relative py-2 select-none">
          {/* Background Track */}
          <div className="h-3 w-full bg-base-200 rounded-full overflow-hidden border border-border relative">
            <motion.div
              className={`h-full rounded-full transition-colors ${
                value <= 2
                  ? "bg-accent"
                  : value === 3
                  ? "bg-primary"
                  : "bg-success"
              }`}
              style={{ width: `${percentage}%` }}
              transition={prefersReducedMotion ? { duration: 0 } : { type: "spring", stiffness: 300, damping: 30 }}
            />
          </div>

          {/* HTML5 Native Range for Accessible Dragging */}
          <input
            type="range"
            min={1}
            max={5}
            step={1}
            value={value}
            onChange={(e) => onChange(Number(e.target.value))}
            aria-label="Adaptive confidence rating"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
          />

          {/* Stepped Tick Marks */}
          <div className="flex justify-between items-center px-1 mt-2">
            {CONFIDENCE_LEVELS.map((item) => (
              <button
                key={item.level}
                type="button"
                onClick={() => onChange(item.level)}
                className={`flex flex-col items-center gap-1 group focus:outline-none ${
                  value === item.level ? "font-bold" : "opacity-60 hover:opacity-100"
                }`}
              >
                <div
                  className={`w-2.5 h-2.5 rounded-full transition-all ${
                    value >= item.level
                      ? value <= 2
                        ? "bg-accent scale-110"
                        : value === 3
                        ? "bg-primary scale-110"
                        : "bg-success scale-110"
                      : "bg-base-300"
                  }`}
                />
                <span className="text-[10px] font-mono text-ink-muted group-hover:text-base-content hidden sm:inline">
                  {item.level}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Context Detail Card */}
        <div className="p-3 rounded-lg bg-base-200/60 border border-border/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className={`text-xs font-bold ${currentLevel.color}`}>
                {currentLevel.label} ({value} of 5)
              </span>
              <span className="text-[10px] text-ink-muted">· Real-time adaptation</span>
            </div>
            <p className="text-xs text-ink-secondary leading-snug">
              {currentLevel.detail}
            </p>
          </div>

          {/* Functional Adaptive Action Button */}
          {isLowConfidence ? (
            <button
              type="button"
              onClick={onRequestSimplification}
              disabled={isReteaching}
              className="flex-shrink-0 flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-accent text-white font-bold text-xs shadow-xs hover:opacity-90 active:scale-95 transition-all disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isReteaching ? "animate-spin" : ""}`} />
              <span>{isReteaching ? "Generating Simpler Analogy..." : currentLevel.actionLabel}</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => onConfirmConfidence && onConfirmConfidence(value)}
              className="flex-shrink-0 flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-primary text-white font-bold text-xs shadow-xs hover:bg-primary-hover active:scale-95 transition-all cursor-pointer"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>{currentLevel.actionLabel}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
