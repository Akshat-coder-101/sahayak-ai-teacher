"use client";

import { ToggleLeft, ToggleRight, Sparkles, UserCheck } from "lucide-react";

interface DemoModeToggleProps {
  isDemoMode: boolean;
  onToggle: (val: boolean) => void;
}

export default function DemoModeToggle({
  isDemoMode,
  onToggle,
}: DemoModeToggleProps) {
  return (
    <button
      type="button"
      onClick={() => onToggle(!isDemoMode)}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-mono transition-all ${
        isDemoMode
          ? "bg-amber-500/15 border-amber-500/40 text-amber-300 ring-1 ring-amber-500/20 font-semibold"
          : "bg-canvas-elevated border-border-scholastic-subtle text-text-scholastic-secondary hover:text-text-scholastic-primary"
      }`}
      title="Toggle demo mode to simulate student misconception and trigger the 20% rubric reteach loop"
    >
      {isDemoMode ? (
        <ToggleRight className="w-4 h-4 text-amber-400" />
      ) : (
        <ToggleLeft className="w-4 h-4 text-text-scholastic-muted" />
      )}
      <span className="flex items-center gap-1">
        <Sparkles className="w-3 h-3 text-amber-400" />
        <span>Presenter Demo Mode: <strong>{isDemoMode ? "ON" : "OFF"}</strong></span>
      </span>
    </button>
  );
}
