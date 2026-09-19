"use client";

import Link from "next/link";
import { 
  Sparkles, 
  UploadCloud, 
  BookOpen, 
  BrainCircuit, 
  ShieldCheck, 
  TrendingUp, 
  Languages, 
  Layers, 
  RefreshCw, 
  ArrowRight, 
  CheckCircle2, 
  PlayCircle 
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative pt-6 pb-10 text-center overflow-hidden">
        {/* Subtle Coursera Blue Ambient Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-blue-100/60 via-blue-50/40 to-transparent blur-[80px] pointer-events-none -z-10" />

        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#E9F1FC] border border-blue-200 text-xs font-bold text-primary mb-6 shadow-2xs">
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
          AI Innovation Hackathon 2026 · Adaptive AI Educator
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-black max-w-4xl mx-auto leading-tight sm:leading-none">
          Not Just a Chatbot. <br />
          <span className="text-primary">
            A True Adaptive AI Teacher.
          </span>
        </h1>

        <p className="mt-6 text-base sm:text-lg text-ink-secondary max-w-2xl mx-auto leading-relaxed font-medium">
          Sahayak AI Teacher executes full pedagogical cycles: understand, plan, explain, demonstrate, question, evaluate, and dynamically adapt on misconceptions with fresh analogies.
        </p>

        {/* Dual Primary Actions */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
          <Link
            href="/upload"
            className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-6 py-3.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-sm shadow-md transition-all hover:scale-[1.02] active:scale-[0.98] group"
          >
            <UploadCloud className="w-5 h-5 group-hover:-translate-y-0.5 transition-transform" />
            <span>Upload Learning Material</span>
          </Link>

          <Link
            href="/topic"
            className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-6 py-3.5 rounded bg-white border-2 border-primary text-primary hover:bg-[#E9F1FC] font-bold text-sm transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <BookOpen className="w-5 h-5 text-primary" />
            <span>Teach Me Any Topic</span>
          </Link>
        </div>

        {/* Live Metrics Row */}
        <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl mx-auto">
          <div className="p-4 rounded-lg bg-white border border-border text-center shadow-2xs hover:shadow-md transition-shadow">
            <span className="text-2xl font-extrabold text-primary">10-State</span>
            <p className="text-xs text-ink-muted mt-1 font-semibold">Teacher Agent FSM</p>
          </div>
          <div className="p-4 rounded-lg bg-white border border-border text-center shadow-2xs hover:shadow-md transition-shadow">
            <span className="text-2xl font-extrabold text-[#0284C8]">4 Domain</span>
            <p className="text-xs text-ink-muted mt-1 font-semibold">Visual Routers</p>
          </div>
          <div className="p-4 rounded-lg bg-white border border-border text-center shadow-2xs hover:shadow-md transition-shadow">
            <span className="text-2xl font-extrabold text-[#0F7B3F]">Zero</span>
            <p className="text-xs text-ink-muted mt-1 font-semibold">Hallucination RAG</p>
          </div>
          <div className="p-4 rounded-lg bg-white border border-border text-center shadow-2xs hover:shadow-md transition-shadow">
            <span className="text-2xl font-extrabold text-accent">3 Lang</span>
            <p className="text-xs text-ink-muted mt-1 font-semibold">Mid-Lesson Switch</p>
          </div>
        </div>
      </section>

      {/* Teacher State Machine Architecture Card */}
      <section className="bg-white rounded-xl p-8 sm:p-10 border border-border shadow-xs relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-primary">
              The Heart of Sahayak
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-black mt-1">
              Deterministic Teacher State Machine
            </h2>
            <p className="text-sm text-ink-secondary mt-1 font-medium">
              Unlike chatbots that simply react, Sahayak orchestrates deliberate instructional sequences.
            </p>
          </div>

          <Link
            href="/topic"
            className="inline-flex items-center gap-2 text-xs font-bold text-primary hover:text-primary-hover transition-colors"
          >
            <span>Experience Live Pipeline</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Visual Pipeline Nodes */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {[
            { step: "01", name: "Understand", desc: "Learner level & topic parsing" },
            { step: "02", name: "Plan", desc: "Time & concept budget allocation" },
            { step: "03", name: "Explain", desc: "Avatar video + audio script" },
            { step: "04", name: "Demonstrate", desc: "LaTeX / Plot / SVG / Code" },
            { step: "05", name: "Question", desc: "Inline checkpoint pause" },
            { step: "06", name: "Evaluate", desc: "Misconception classifier" },
            { step: "07", name: "Adapt", desc: "Reteach with fresh analogy" },
            { step: "08", name: "Assess", desc: "Targeted quiz & report" },
          ].map((item, i) => (
            <div 
              key={i} 
              className="p-3.5 rounded-lg bg-canvas-elevated border border-border hover:border-primary hover:bg-[#E9F1FC] transition-all text-center group cursor-pointer"
            >
              <span className="text-[11px] font-mono font-bold text-ink-muted group-hover:text-primary">{item.step}</span>
              <h3 className="font-bold text-xs text-black mt-1">{item.name}</h3>
              <p className="text-[11px] text-ink-secondary mt-1 leading-tight">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 4 Subject-Aware Renderers Showcase */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto">
          <span className="text-xs font-bold uppercase tracking-wider text-primary">
            Beyond Talking Heads
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-black mt-1">
            Subject-Aware Visual Routers
          </h2>
          <p className="text-sm text-ink-secondary mt-2 font-medium">
            Every concept is automatically matched with the highest-fidelity pedagogical visualizer.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg border border-border shadow-2xs hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded bg-[#E9F1FC] text-primary flex items-center justify-center mb-4">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-black">Math & Physics</h3>
            <p className="text-xs text-ink-secondary mt-2 leading-relaxed">
              LaTeX mathematical derivations, 2D/3D dynamic coordinate charts, trajectory analysis, and step-by-step calculus solvers.
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg border border-border shadow-2xs hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded bg-emerald-50 text-[#0F7B3F] flex items-center justify-center mb-4">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-black">Biology & Sciences</h3>
            <p className="text-xs text-ink-secondary mt-2 leading-relaxed">
              Interactive high-resolution SVG diagrams with clickable structural hotspots, anatomical roles, and cellular mechanisms.
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg border border-border shadow-2xs hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded bg-amber-50 text-[#B75F00] flex items-center justify-center mb-4">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-black">History & Chronology</h3>
            <p className="text-xs text-ink-secondary mt-2 leading-relaxed">
              Interactive chronological timelines, milestone nodes, epoch categorizations, and geopolitical impact maps.
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg border border-border shadow-2xs hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded bg-[#E9F1FC] text-primary flex items-center justify-center mb-4">
              <PlayCircle className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-black">Computer Science</h3>
            <p className="text-xs text-ink-secondary mt-2 leading-relaxed">
              Real code sandbox runner with isolated Python execution, actual standard output stream, and algorithmic trace steps.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="rounded-xl bg-[#E9F1FC] p-8 sm:p-12 border border-blue-200 text-center relative overflow-hidden">
        <h2 className="text-2xl sm:text-4xl font-extrabold text-black tracking-tight">
          Ready to Experience the Future of AI Education?
        </h2>
        <p className="text-sm text-ink-secondary max-w-xl mx-auto mt-3 font-medium">
          Upload any lecture notes, syllabus PDF, or input a custom topic to launch your personalized interactive teaching session.
        </p>

        <div className="mt-8 flex justify-center gap-4">
          <Link
            href="/upload"
            className="px-8 py-3.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-sm shadow-md transition-all hover:scale-105 active:scale-95"
          >
            Launch Demo Now
          </Link>
        </div>
      </section>
    </div>
  );
}
