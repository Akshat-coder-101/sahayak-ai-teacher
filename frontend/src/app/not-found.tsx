import Link from "next/link";
import { Compass, Home, LayoutDashboard, Sparkles, BookOpen } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4 py-16 max-w-2xl mx-auto space-y-6">
      <div className="w-16 h-16 rounded-2xl bg-primary-soft text-primary flex items-center justify-center mx-auto shadow-xs border border-primary/20">
        <Compass className="w-8 h-8 animate-pulse text-primary" />
      </div>

      <div className="space-y-2">
        <span className="text-xs font-bold uppercase tracking-wider text-primary font-mono">
          404 · Pedagogical Path Not Found
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-black tracking-tight">
          Page or Curriculum Missing
        </h1>
        <p className="text-sm text-ink-secondary max-w-md mx-auto leading-relaxed">
          The educational session or curriculum node you are trying to reach does not exist or has been completed.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-black hover:bg-neutral-800 text-white font-bold text-xs shadow-md transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          <Home className="w-4 h-4" />
          <span>Return Home</span>
        </Link>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary hover:bg-primary-hover text-white font-bold text-xs shadow-md transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          <LayoutDashboard className="w-4 h-4" />
          <span>View Dashboard</span>
        </Link>
        <Link
          href="/topic"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-border bg-white hover:bg-canvas-elevated text-ink-primary font-bold text-xs transition-colors"
        >
          <BookOpen className="w-4 h-4 text-accent" />
          <span>Explore Topics</span>
        </Link>
      </div>
    </div>
  );
}
