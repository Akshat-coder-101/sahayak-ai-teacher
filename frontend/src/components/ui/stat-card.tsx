"use client";

import React, { useEffect, useState } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { usePrefersReducedMotion } from "./use-reduced-motion";

export interface StatCardProps {
  title: string;
  value: number | string;
  numericValue?: number;
  suffix?: string;
  prefix?: string;
  subtext?: string;
  icon?: LucideIcon;
  color?: string;
  badge?: string;
  isEmpty?: boolean;
  className?: string;
}

export function StatCard({
  title,
  value,
  numericValue,
  suffix = "",
  prefix = "",
  subtext,
  icon: Icon,
  color = "text-primary",
  badge,
  isEmpty = false,
  className = "",
}: StatCardProps) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => Math.round(latest));
  const [displayNumber, setDisplayNumber] = useState<number | string>(
    typeof numericValue === "number" ? 0 : value
  );

  useEffect(() => {
    if (typeof numericValue === "number" && !isEmpty) {
      if (prefersReducedMotion) {
        setDisplayNumber(numericValue);
        return;
      }

      const controls = animate(count, numericValue, {
        duration: 1.2,
        ease: [0.16, 1, 0.3, 1],
        onUpdate: (latest) => {
          setDisplayNumber(Math.round(latest));
        },
      });

      return () => controls.stop();
    } else {
      setDisplayNumber(value);
    }
  }, [numericValue, value, isEmpty, prefersReducedMotion, count]);

  return (
    <div
      className={`bg-base-100 p-5 rounded-xl border border-border space-y-2.5 shadow-2xs hover:shadow-md hover:border-border-strong transition-all ${className}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-ink-muted font-bold tracking-tight">
          {title}
        </span>
        <div className="flex items-center gap-1.5">
          {badge && (
            <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-base-200 text-ink-secondary">
              {badge}
            </span>
          )}
          {Icon && <Icon className={`w-4 h-4 ${color} flex-shrink-0`} />}
        </div>
      </div>

      <div className="flex items-baseline gap-1">
        {prefix && (
          <span className="text-lg font-bold text-base-content/70">{prefix}</span>
        )}
        <span className="text-2xl sm:text-3xl font-black text-base-content font-mono tracking-tight">
          {typeof numericValue === "number" && !isEmpty
            ? displayNumber
            : value}
        </span>
        {suffix && (
          <span className="text-xs sm:text-sm font-bold text-ink-muted ml-0.5">
            {suffix}
          </span>
        )}
      </div>

      {subtext && (
        <p className="text-[11px] text-ink-muted leading-tight font-medium">
          {subtext}
        </p>
      )}
    </div>
  );
}
