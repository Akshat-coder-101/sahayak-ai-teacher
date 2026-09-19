"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, LearningPath } from "@/lib/api";
import LearningPathDAG from "@/components/LearningPathDAG";
import { Compass, Sparkles, Search, ArrowRight } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function LearningPathPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  
  const rawTopicId = (params.topicId as string) || "quantum-computing";
  const topicId = decodeURIComponent(rawTopicId);

  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [customTopicInput, setCustomTopicInput] = useState<string>("");

  useEffect(() => {
    async function loadPath() {
      try {
        setIsLoading(true);
        const data = await api.getLearningPath(topicId, user?.id || "default-user");
        setLearningPath(data);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    if (topicId) loadPath();
  }, [topicId, user?.id]);

  const handleGenerateCustomPath = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customTopicInput.trim()) return;
    const cleanId = customTopicInput.trim().toLowerCase().replace(/\s+/g, "-");
    router.push(`/learning-path/${encodeURIComponent(cleanId)}`);
    setCustomTopicInput("");
  };

  const sampleSubjects = [
    { title: "Linear Algebra & Vector Spaces", id: "linear-algebra" },
    { title: "Cellular Respiration & ATP", id: "cellular-respiration" },
    { title: "Neural Networks & Deep Learning", id: "neural-networks" },
    { title: "Quantum Computing & Qubits", id: "quantum-computing" },
    { title: "Industrial Revolution & Economy", id: "industrial-revolution" },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Dynamic Topic Search & Generator Bar */}
      <div className="bg-white rounded-lg p-4 sm:p-5 border border-border shadow-2xs space-y-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h2 className="font-bold text-sm text-black flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              <span>Dynamic Curriculum Generator</span>
            </h2>
            <p className="text-xs text-ink-muted mt-0.5">
              Type any topic to synthesize a new 6-stage Bloom's Taxonomy learning path with prerequisites.
            </p>
          </div>

          {/* Quick Subject Chips */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <span className="text-[11px] font-bold text-ink-muted uppercase mr-1 font-mono">Popular:</span>
            {sampleSubjects.map((s) => (
              <button
                key={s.id}
                onClick={() => router.push(`/learning-path/${s.id}`)}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors border ${
                  topicId === s.id
                    ? "bg-primary text-white border-primary"
                    : "bg-canvas-elevated hover:bg-white text-ink-secondary border-border"
                }`}
              >
                {s.title.split("&")[0].trim()}
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleGenerateCustomPath} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
            <input
              type="text"
              value={customTopicInput}
              onChange={(e) => setCustomTopicInput(e.target.value)}
              placeholder="Enter ANY subject (e.g., Photosynthesis, Transformer Attention, Game Theory, Blockchain)..."
              className="w-full text-xs pl-9 pr-3 py-2.5 rounded bg-white border border-border text-black placeholder-ink-muted focus:outline-none focus:border-primary font-medium"
            />
          </div>
          <button
            type="submit"
            disabled={!customTopicInput.trim()}
            className="px-5 py-2.5 rounded bg-black hover:bg-neutral-800 disabled:opacity-40 text-white font-bold text-xs flex items-center gap-1.5 transition-colors shadow-2xs shrink-0"
          >
            <span>Synthesize DAG</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>

      {/* Loading or DAG View */}
      {isLoading ? (
        <div className="py-20 text-center space-y-4 bg-white rounded-lg border border-border p-8">
          <div className="w-12 h-12 rounded-full bg-[#E9F1FC] text-primary flex items-center justify-center mx-auto animate-pulse">
            <Compass className="w-6 h-6 animate-spin" />
          </div>
          <h2 className="text-base font-bold text-black">Synthesizing Pedagogical Curriculum DAG...</h2>
          <p className="text-xs text-ink-muted max-w-sm mx-auto">
            Structuring prerequisite dependencies, difficulty tiers, and mastery nodes for "{topicId.replace(/-/g, ' ')}".
          </p>
        </div>
      ) : learningPath ? (
        <LearningPathDAG initialPath={learningPath} />
      ) : (
        <div className="py-20 text-center text-ink-muted bg-white rounded-lg border border-border p-8">
          <p className="font-semibold text-black">Unable to assemble learning path.</p>
          <p className="text-xs mt-1">Please try searching for another topic above.</p>
        </div>
      )}
    </div>
  );
}
