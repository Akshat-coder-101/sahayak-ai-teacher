"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import {
  Compass,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Layers,
  BookOpen,
  CheckCircle2,
  Clock,
  Search,
  PlusCircle,
  FolderPlus
} from "lucide-react";

interface UserPathSummary {
  id: string;
  topic_id: string;
  title: string;
  progress_percentage: number;
  node_count: number;
  updated_at?: string;
}

export default function LearningPathHubPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const userId = user?.id || "default-user";

  const [searchTopic, setSearchTopic] = useState("");
  const [activePaths, setActivePaths] = useState<UserPathSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadPaths() {
      if (authLoading) return;
      try {
        setIsLoading(true);
        const data = await api.getUserLearningPaths(userId);
        setActivePaths(data || []);
      } catch {
        setActivePaths([]);
      } finally {
        setIsLoading(false);
      }
    }
    loadPaths();
  }, [userId, authLoading]);

  const handleSynthesize = (topicToGenerate?: string) => {
    const raw = topicToGenerate || searchTopic.trim();
    if (!raw) return;
    const cleanId = raw.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    router.push(`/learning-path/${encodeURIComponent(cleanId)}`);
  };

  const domainBenchmarks = [
    {
      domain: "Computer Science & AI",
      topics: [
        { title: "Machine Learning & Neural Architectures", id: "machine-learning", desc: "Vector math, regression, validation curves, and deep neural backprop." },
        { title: "Binary Search Trees & Recursive Algorithms", id: "binary-search-trees", desc: "Tree traversal, AVL balance properties, and complexity analysis." },
        { title: "Transformer Architecture & Attention", id: "transformer-architecture", desc: "Self-attention matrices, positional encodings, and encoder-decoder stack." }
      ]
    },
    {
      domain: "Physics & Engineering",
      topics: [
        { title: "Principles of Electricity & Circuit Dynamics", id: "electricity", desc: "Coulomb force, Ohm's law, resistivity, and Kirchhoff's loop laws." },
        { title: "Quantum Computing & Information Mechanics", id: "quantum-computing", desc: "Bloch spheres, Hadamard gates, Bell states, and Grover/Shor algorithms." },
        { title: "Thermodynamics & Entropy Mechanics", id: "thermodynamics", desc: "Heat engines, Carnot cycles, state variables, and thermodynamic entropy." }
      ]
    },
    {
      domain: "Natural & Social Sciences",
      topics: [
        { title: "Cellular Respiration & ATP Synthesis", id: "cellular-respiration", desc: "Glycolysis, Krebs cycle, electron transport chain, and chemiosmosis." },
        { title: "Macroeconomic Policy & Inflation Dynamics", id: "macroeconomics", desc: "Fiscal & monetary policy, aggregate demand, interest rates, and Phillips curves." },
        { title: "The Industrial Revolution & Global Modernity", id: "industrial-revolution", desc: "Mechanization, steam power, capital accumulation, and urbanization." }
      ]
    }
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-10 pb-16">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-[#0056D2]/10 via-blue-50/50 to-transparent p-6 sm:p-8 border border-border shadow-2xs">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 border border-blue-200 text-xs font-bold text-primary mb-3">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Dynamic Pedagogical Curriculum DAGs</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-black tracking-tight">
          Explore & Synthesize Any Curriculum
        </h1>
        <p className="text-sm sm:text-base text-ink-secondary mt-2 max-w-2xl font-medium">
          Generate an intelligent, prerequisite-ordered Directed Acyclic Graph (DAG) for any topic. Sahayak dynamically calibrates stages from cognitive intuition to advanced mastery.
        </p>

        {/* Dynamic Topic Synthesizer Input */}
        <div className="mt-6 flex flex-col sm:flex-row gap-3 max-w-2xl">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" />
            <input
              type="text"
              value={searchTopic}
              onChange={(e) => setSearchTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSynthesize()}
              placeholder="Enter any topic (e.g., Quantum Entanglement, Organic Chemistry, French Revolution)..."
              className="w-full pl-10 pr-4 py-3 rounded-lg bg-white border border-border text-black placeholder-ink-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm font-medium shadow-2xs"
            />
          </div>
          <button
            onClick={() => handleSynthesize()}
            disabled={!searchTopic.trim()}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary hover:bg-primary-hover text-white font-bold text-sm shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-40"
          >
            <Compass className="w-4 h-4" />
            <span>Synthesize DAG</span>
          </button>
        </div>
      </div>

      {/* Your Active Curriculum Tracks */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-bold text-black">Your Active Curriculum Tracks</h2>
          </div>
          <Link
            href="/topic"
            className="text-xs font-bold text-primary hover:underline flex items-center gap-1"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>New Lesson Session</span>
          </Link>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-xs text-ink-muted bg-white rounded-lg border border-border animate-pulse">
            Loading your active learning paths...
          </div>
        ) : activePaths.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activePaths.map((p) => (
              <div
                key={p.id}
                className="bg-white rounded-lg p-5 border border-border hover:border-primary shadow-2xs hover:shadow-md transition-all flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between text-xs text-ink-muted mb-2">
                    <span className="font-mono uppercase font-bold text-[10px] bg-canvas-elevated px-2 py-0.5 rounded">
                      {p.node_count > 0 ? `${p.node_count} Nodes` : "Curriculum DAG"}
                    </span>
                    <span className="font-bold text-primary">{p.progress_percentage}% Mastered</span>
                  </div>
                  <h3 className="font-bold text-sm text-black group-hover:text-primary transition-colors">
                    {p.title}
                  </h3>
                </div>

                <div className="mt-4 pt-3 border-t border-border/60">
                  <div className="w-full bg-slate-100 rounded-full h-2 mb-3 overflow-hidden">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(p.progress_percentage, 5)}%` }}
                    />
                  </div>
                  <Link
                    href={`/learning-path/${p.topic_id}`}
                    className="w-full py-2 rounded bg-[#E9F1FC] hover:bg-primary hover:text-white text-primary text-xs font-bold flex items-center justify-center gap-1.5 transition-all"
                  >
                    <span>Open Interactive DAG</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center bg-white rounded-lg border border-dashed border-border space-y-2">
            <p className="text-sm font-semibold text-black">No active curriculum paths yet.</p>
            <p className="text-xs text-ink-muted">
              Choose a benchmark below or enter any topic in the search box above to generate your first custom DAG!
            </p>
          </div>
        )}
      </section>

      {/* Benchmark Curricula by Domain */}
      <section className="space-y-6">
        <div>
          <h2 className="text-lg font-bold text-black flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary" />
            <span>Benchmark Curriculum Tracks</span>
          </h2>
          <p className="text-xs text-ink-secondary mt-0.5 font-medium">
            Pre-calibrated cognitive curricula covering foundational, intermediate, and advanced synthesis tiers.
          </p>
        </div>

        <div className="space-y-6">
          {domainBenchmarks.map((group, idx) => (
            <div key={idx} className="space-y-3">
              <h3 className="text-xs font-extrabold uppercase tracking-wider text-ink-muted">
                {group.domain}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {group.topics.map((t) => (
                  <div
                    key={t.id}
                    onClick={() => handleSynthesize(t.id)}
                    className="bg-white p-4 rounded-lg border border-border hover:border-primary hover:bg-[#E9F1FC]/40 cursor-pointer shadow-2xs hover:shadow-md transition-all flex flex-col justify-between group"
                  >
                    <div>
                      <h4 className="font-bold text-xs text-black group-hover:text-primary transition-colors">
                        {t.title}
                      </h4>
                      <p className="text-[11px] text-ink-muted mt-1 leading-relaxed line-clamp-2">
                        {t.desc}
                      </p>
                    </div>
                    <div className="mt-4 flex items-center text-xs font-bold text-primary gap-1 group-hover:translate-x-0.5 transition-transform">
                      <span>View Learning Path</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
