"use client";

import { InteractionResponse } from "@/lib/api";
import { Sparkles, ArrowRight, Lightbulb, Compass, RotateCcw } from "lucide-react";

interface MisconceptionModalProps {
  interaction: InteractionResponse;
  onContinueReteach: () => void;
}

export default function MisconceptionModal({
  interaction,
  onContinueReteach,
}: MisconceptionModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="max-w-xl w-full bg-white rounded-lg p-6 border border-border shadow-xl space-y-5 animate-in zoom-in-95 duration-150">
        {/* Header Badge */}
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-[#FFF1E6] border border-orange-200 text-accent flex items-center justify-center">
              <Lightbulb className="w-5 h-5 text-accent" />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-accent">
                Adaptive AI Intervention
              </span>
              <h3 className="text-base font-bold text-ink-primary">
                Misconception Detected · Fresh Analogy Ready
              </h3>
            </div>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-[#FFF1E6] text-accent font-bold border border-orange-200">
            FSM Adaptation
          </span>
        </div>

        {/* Diagnosis Box */}
        <div className="p-4 rounded bg-canvas-elevated border border-border space-y-2">
          <span className="text-xs font-bold text-ink-primary uppercase tracking-wider block">
            Pedagogical Diagnosis
          </span>
          <p className="text-xs text-ink-secondary leading-relaxed">
            {interaction.feedback}
          </p>
          {interaction.misconception_name && (
            <div className="pt-2 text-xs text-accent font-semibold flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-accent" />
              <span>Diagnosed Gap: {interaction.misconception_name}</span>
            </div>
          )}
        </div>

        {/* Fresh Analogy Callout */}
        <div className="p-4 rounded bg-[#FFF1E6] border-l-4 border-accent space-y-1">
          <div className="flex items-center gap-2 text-accent text-xs font-bold">
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            <span>Alternative Physical Analogy:</span>
          </div>
          <p className="text-xs text-ink-primary italic leading-relaxed">
            "{interaction.new_analogy || "Let's rethink this using a different intuitive mental model."}"
          </p>
        </div>

        {/* Action Buttons: Coursera Black primary */}
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-ink-muted">
            The AI Teacher will re-explain with this model
          </span>
          <button
            onClick={onContinueReteach}
            className="flex items-center gap-2 px-5 py-2.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-xs transition-colors shadow-2xs"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Begin Reteach</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
