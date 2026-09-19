"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Sparkles, Lightbulb, CheckCircle2 } from "lucide-react";
import { usePrefersReducedMotion } from "./use-reduced-motion";

export interface DisclosureItem {
  id: string;
  title: string;
  subtitle?: string;
  badge?: string;
  badgeType?: "primary" | "accent" | "success" | "neutral";
  content: React.ReactNode;
  defaultExpanded?: boolean;
}

interface CollapsibleDisclosureProps {
  items?: DisclosureItem[];
  title?: string;
  subtitle?: string;
  badge?: string;
  children?: React.ReactNode;
  defaultOpen?: boolean;
  isOpen?: boolean;
  onToggle?: (isOpen: boolean) => void;
  icon?: React.ReactNode;
  variant?: "card" | "bordered" | "ghost" | "hint";
  className?: string;
}

export function CollapsibleDisclosure({
  title,
  subtitle,
  badge,
  children,
  defaultOpen = false,
  isOpen: controlledIsOpen,
  onToggle,
  icon,
  variant = "bordered",
  className = "",
}: CollapsibleDisclosureProps) {
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const isControlled = controlledIsOpen !== undefined;
  const isOpen = isControlled ? controlledIsOpen : internalOpen;
  const prefersReducedMotion = usePrefersReducedMotion();

  const handleToggle = () => {
    const nextState = !isOpen;
    if (!isControlled) {
      setInternalOpen(nextState);
    }
    if (onToggle) {
      onToggle(nextState);
    }
  };

  const getVariantClasses = () => {
    switch (variant) {
      case "card":
        return "bg-base-100 border border-border shadow-xs hover:border-border-strong";
      case "hint":
        return "bg-accent/5 border border-accent/20 hover:border-accent/40";
      case "ghost":
        return "bg-transparent border border-transparent hover:bg-base-200/50";
      case "bordered":
      default:
        return "bg-base-100 border border-border";
    }
  };

  return (
    <div className={`rounded-xl overflow-hidden transition-colors ${getVariantClasses()} ${className}`}>
      <button
        type="button"
        onClick={handleToggle}
        className="w-full px-4 py-3.5 flex items-center justify-between text-left gap-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary select-none cursor-pointer"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-3 min-w-0">
          {icon && (
            <div className="flex-shrink-0 text-primary">
              {icon}
            </div>
          )}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-xs sm:text-sm text-base-content tracking-tight">
                {title}
              </span>
              {badge && (
                <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-primary/10 text-primary border border-primary/20">
                  {badge}
                </span>
              )}
            </div>
            {subtitle && (
              <p className="text-[11px] text-ink-muted mt-0.5 truncate">
                {subtitle}
              </p>
            )}
          </div>
        </div>

        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.25, ease: "easeInOut" }}
          className="flex-shrink-0 text-ink-muted"
        >
          <ChevronDown className="w-4 h-4" />
        </motion.div>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={prefersReducedMotion ? { opacity: 1, height: "auto" } : { opacity: 0, height: 0 }}
            animate={prefersReducedMotion ? { opacity: 1, height: "auto" } : { opacity: 1, height: "auto" }}
            exit={prefersReducedMotion ? { opacity: 0, height: 0 } : { opacity: 0, height: 0 }}
            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-1 text-xs text-ink-secondary border-t border-border/40">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Sequential Step-by-Step Explanation Accordion (Watermelon UI Progressive Disclosure)
 * Reveals explanation units progressively to mirror teacher pacing.
 */
interface ProgressiveStepDisclosureProps {
  steps: {
    title: string;
    description: string;
    details?: string;
    keyRule?: string;
  }[];
  currentStepIndex?: number;
  className?: string;
}

export function ProgressiveStepDisclosure({
  steps,
  currentStepIndex = 0,
  className = "",
}: ProgressiveStepDisclosureProps) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const [expandedIndex, setExpandedIndex] = useState<number | null>(currentStepIndex);

  return (
    <div className={`space-y-2.5 ${className}`}>
      {steps.map((step, idx) => {
        const isRevealed = idx <= currentStepIndex;
        const isExpanded = expandedIndex === idx;

        return (
          <div
            key={idx}
            className={`rounded-lg border transition-all duration-200 ${
              isRevealed
                ? "bg-base-100 border-border shadow-2xs"
                : "bg-base-200/40 border-dashed border-border opacity-60"
            }`}
          >
            <button
              type="button"
              onClick={() => isRevealed && setExpandedIndex(isExpanded ? null : idx)}
              disabled={!isRevealed}
              className="w-full px-4 py-3 flex items-center justify-between text-left gap-3 select-none"
            >
              <div className="flex items-center gap-3">
                <span
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold font-mono transition-colors ${
                    isRevealed
                      ? isExpanded
                        ? "bg-primary text-white"
                        : "bg-primary/10 text-primary"
                      : "bg-base-300 text-ink-muted"
                  }`}
                >
                  {idx + 1}
                </span>
                <div>
                  <h4 className="font-bold text-xs text-base-content">
                    {step.title}
                  </h4>
                  <p className="text-[11px] text-ink-muted truncate max-w-sm">
                    {step.description}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {isRevealed ? (
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-50 text-success font-bold font-mono flex items-center gap-1 border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3" />
                    Unlocked
                  </span>
                ) : (
                  <span className="text-[10px] text-ink-muted font-mono">Paced</span>
                )}
                <motion.div
                  animate={{ rotate: isExpanded ? 180 : 0 }}
                  transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.2 }}
                >
                  <ChevronDown className="w-4 h-4 text-ink-muted" />
                </motion.div>
              </div>
            </button>

            <AnimatePresence initial={false}>
              {isRevealed && isExpanded && (
                <motion.div
                  initial={prefersReducedMotion ? { opacity: 1, height: "auto" } : { opacity: 0, height: 0 }}
                  animate={prefersReducedMotion ? { opacity: 1, height: "auto" } : { opacity: 1, height: "auto" }}
                  exit={prefersReducedMotion ? { opacity: 0, height: 0 } : { opacity: 0, height: 0 }}
                  transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.25 }}
                  className="overflow-hidden"
                >
                  <div className="px-4 pb-3.5 pt-1 border-t border-border/50 text-xs text-ink-secondary space-y-2">
                    <p className="leading-relaxed whitespace-pre-wrap">{step.details || step.description}</p>
                    {step.keyRule && (
                      <div className="p-2.5 rounded bg-base-200 border-l-2 border-primary text-[11px] font-medium text-base-content">
                        <strong className="text-primary font-semibold mr-1">Core Rule:</strong>
                        {step.keyRule}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Functional Hint Disclosure for Pedagogical Checkpoints
 * Fires onHintUsed when opened, which increments the session's hintsUsed counter
 * and embeds it in the next /interact/answer payload.
 */
interface HintDisclosureProps {
  hints: string[];
  hintsUsed: number;
  onHintUsed: () => void;
  className?: string;
}

export function HintDisclosure({
  hints,
  hintsUsed,
  onHintUsed,
  className = "",
}: HintDisclosureProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [hasTriggeredEvent, setHasTriggeredEvent] = useState(false);
  const prefersReducedMotion = usePrefersReducedMotion();

  const handleToggle = () => {
    const nextOpen = !isOpen;
    setIsOpen(nextOpen);
    if (nextOpen && !hasTriggeredEvent) {
      setHasTriggeredEvent(true);
      onHintUsed();
    }
  };

  if (!hints || hints.length === 0) return null;

  return (
    <div className={`rounded-lg border border-accent/25 bg-accent/5 overflow-hidden transition-colors ${className}`}>
      <button
        type="button"
        onClick={handleToggle}
        className="w-full px-3.5 py-2.5 flex items-center justify-between text-left gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent select-none cursor-pointer"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-accent flex-shrink-0" />
          <span className="text-xs font-bold text-base-content">
            {isOpen ? "Hide Pedagogical Hint" : "Show Checkpoint Hint"}
          </span>
          <span className="text-[10px] px-1.5 py-0.2 rounded bg-accent/15 text-accent font-mono font-bold">
            {hints.length} available
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {hintsUsed > 0 && (
            <span className="text-[10px] text-ink-muted font-mono font-semibold">
              ({hintsUsed} used)
            </span>
          )}
          <motion.div
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.2 }}
            className="text-accent"
          >
            <ChevronDown className="w-3.5 h-3.5" />
          </motion.div>
        </div>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={prefersReducedMotion ? { opacity: 1, height: "auto" } : { opacity: 0, height: 0 }}
            animate={prefersReducedMotion ? { opacity: 1, height: "auto" } : { opacity: 1, height: "auto" }}
            exit={prefersReducedMotion ? { opacity: 0, height: 0 } : { opacity: 0, height: 0 }}
            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-3.5 pb-3 pt-1 border-t border-accent/20 space-y-1.5">
              {hints.map((hint, i) => (
                <div key={i} className="text-xs text-base-content flex items-start gap-2 bg-base-100 p-2.5 rounded border border-border/60">
                  <span className="text-accent font-bold font-mono text-[11px] mt-0.5">#{i + 1}</span>
                  <p className="leading-relaxed">{hint}</p>
                </div>
              ))}
              <p className="text-[10px] text-ink-muted italic pt-0.5">
                💡 Hint usage is tracked to calibrate adaptive recommendations in your learning report.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
