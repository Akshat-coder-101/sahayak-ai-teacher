"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { 
  BookOpen, 
  Sparkles, 
  ArrowRight, 
  TrendingUp, 
  Layers, 
  Calendar, 
  FileCode, 
  Compass 
} from "lucide-react";

export default function TopicPage() {
  const router = useRouter();
  const [topic, setTopic] = useState("");

  const suggestedTopics = [
    { title: "Newton's Laws of Motion & Conservation", domain: "Physics", icon: TrendingUp, color: "text-[#0056D2]" },
    { title: "Cellular Respiration & ATP Synthesis", domain: "Biology", icon: Layers, color: "text-[#0F7B3F]" },
    { title: "The Industrial Revolution & Global Modernity", domain: "History", icon: Calendar, color: "text-[#B75F00]" },
    { title: "Binary Search Trees & Recursive Algorithms", domain: "Computer Science", icon: FileCode, color: "text-[#0056D2]" },
    { title: "Quantum Entanglement & Superposition", domain: "Physics", icon: Sparkles, color: "text-[#0056D2]" },
    { title: "Transformer Architecture & Attention Mechanisms", domain: "AI / ML", icon: Compass, color: "text-accent" },
  ];

  const handleStart = (selectedTopic?: string) => {
    const finalTopic = selectedTopic || topic.trim();
    if (!finalTopic) return;
    router.push(`/setup?topic=${encodeURIComponent(finalTopic)}`);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div>
        <span className="text-xs font-bold uppercase tracking-wider text-primary">
          Curriculum Generator
        </span>
        <h1 className="text-3xl font-extrabold text-black mt-1">Teach Me Any Topic</h1>
        <p className="text-sm text-ink-secondary mt-1 font-medium">
          Input any academic or professional subject. Sahayak will synthesize a customized pedagogical lesson plan matching your cognitive level and time budget.
        </p>
      </div>

      {/* Main Topic Input Box */}
      <div className="bg-white rounded-lg p-6 border border-border space-y-4 shadow-2xs">
        <label className="text-xs font-bold uppercase tracking-wider text-black block">
          What concept would you like to master?
        </label>
        
        <div className="relative">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleStart()}
            placeholder="e.g., Photosynthesis and Light-Dependent Reactions"
            className="w-full px-4 py-3.5 rounded bg-white border border-border text-black placeholder-ink-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-base font-medium transition-all"
          />
        </div>

        <div className="flex justify-end">
          <button
            onClick={() => handleStart()}
            disabled={!topic.trim()}
            className="flex items-center gap-2 px-6 py-3 rounded bg-black hover:bg-neutral-800 text-white font-bold text-sm shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-40"
          >
            <span>Proceed to Learner Profile</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Recommended Topics Grid */}
      <div>
        <span className="text-xs font-bold uppercase tracking-wider text-ink-muted block mb-3">
          Popular Benchmark Topics for Hackathon Evaluation:
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {suggestedTopics.map((item, i) => {
            const Icon = item.icon;
            return (
              <div
                key={i}
                onClick={() => handleStart(item.title)}
                className="bg-white p-4 rounded-lg border border-border hover:border-primary hover:bg-[#E9F1FC] cursor-pointer transition-all hover:scale-[1.01] flex items-center justify-between group shadow-2xs"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded bg-canvas-elevated flex items-center justify-center">
                    <Icon className={`w-5 h-5 ${item.color}`} />
                  </div>
                  <div>
                    <h3 className="font-bold text-xs text-black group-hover:text-primary transition-colors">
                      {item.title}
                    </h3>
                    <span className="text-[11px] text-ink-muted font-medium">{item.domain}</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-ink-muted group-hover:text-primary transition-colors" />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
