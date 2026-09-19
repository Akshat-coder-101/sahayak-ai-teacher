"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LearningPath, PathNode, api } from "@/lib/api";
import { 
  Check, 
  Circle, 
  ArrowDown, 
  Sparkles, 
  Clock, 
  Award, 
  BookOpen, 
  PlayCircle, 
  Lock, 
  AlertTriangle, 
  ArrowRight,
  RefreshCw,
  Info
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import RelatedVideos from "@/components/RelatedVideos";

interface LearningPathDAGProps {
  initialPath: LearningPath;
}

export default function LearningPathDAG({ initialPath }: LearningPathDAGProps) {
  const router = useRouter();
  const { user } = useAuth();
  
  const [path, setPath] = useState<LearningPath>(initialPath);
  const [activeNode, setActiveNode] = useState<PathNode | null>(path.nodes[0] || null);
  const [isUpdating, setIsUpdating] = useState<boolean>(false);

  const handleToggleNode = async (nodeId: string) => {
    try {
      setIsUpdating(true);
      const updated = await api.togglePathNode(path.topic_id, nodeId, user?.id || "default-user");
      setPath(updated);
      const n = updated.nodes.find((item) => item.id === nodeId);
      if (n) setActiveNode(n);
    } catch (err) {
      console.error(err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleLaunchLesson = (node: PathNode) => {
    router.push(`/setup?topic=${encodeURIComponent(node.title.replace(/^\d+\.\s*/, ""))}`);
  };

  const rec = path.recommendation;

  return (
    <div className="space-y-6">
      {/* Path Header */}
      <div className="bg-white rounded-lg p-6 border border-border shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#E9F1FC] text-primary font-bold">
                Bloom's Taxonomy Prerequisite Graph
              </span>
              <span className="text-xs text-ink-muted">{path.nodes.length} Pedagogical Stages</span>
            </div>
            <h1 className="text-2xl font-bold text-black tracking-tight">{path.title}</h1>
            <p className="text-xs text-ink-secondary mt-1 max-w-2xl leading-relaxed font-medium">{path.description}</p>
          </div>

          <div className="flex items-center gap-4 bg-canvas-elevated p-4 rounded-lg border border-border shrink-0">
            <div className="text-right">
              <span className="text-xs text-ink-muted block font-medium">Curriculum Mastery</span>
              <span className="text-xl font-extrabold text-primary">{path.completion_percentage}%</span>
            </div>
            <div className="w-12 h-12 rounded-full bg-[#E9F1FC] border-2 border-primary flex items-center justify-center font-bold text-xs text-primary">
              {path.nodes.filter((n) => n.status === "completed" || n.status === "mastered").length}/{path.nodes.length}
            </div>
          </div>
        </div>
      </div>

      {/* AI Recommendation & Explainability Banner */}
      {rec && (
        <div className={`p-4 sm:p-5 rounded-lg border ${
          rec.action === "REVISE_CONCEPT"
            ? "bg-amber-50/80 border-amber-200"
            : "bg-[#E9F1FC]/80 border-blue-200"
        } shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4`}>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Sparkles className={`w-4 h-4 ${rec.action === "REVISE_CONCEPT" ? "text-[#B75F00]" : "text-primary"}`} />
              <span className={`text-xs font-bold uppercase tracking-wide ${
                rec.action === "REVISE_CONCEPT" ? "text-[#B75F00]" : "text-primary"
              }`}>
                Recommended Next Action: {rec.action.replace(/_/g, " ")}
              </span>
            </div>
            <h3 className="text-sm font-bold text-black">
              {rec.node_title || rec.topic_id}
            </h3>
            <p className="text-xs text-ink-secondary leading-relaxed max-w-3xl">
              {rec.explanation || rec.reason}
            </p>
          </div>

          {rec.node_id && (
            <button
              onClick={() => {
                const target = path.nodes.find((n) => n.id === rec.node_id);
                if (target) handleLaunchLesson(target);
              }}
              className="px-4 py-2.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-xs shrink-0 flex items-center gap-1.5 transition-all shadow-2xs"
            >
              <span>{rec.action === "REVISE_CONCEPT" ? "Start Revision Lesson" : "Start Next Lesson"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* Interactive DAG Nodes Graph & Detail Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Nodes Timeline Column (7 cols) */}
        <div className="lg:col-span-7 space-y-3">
          {path.nodes.map((node, index) => {
            const isSelected = activeNode?.id === node.id;
            const isLocked = node.status === "locked";
            const isNeedsRevision = node.status === "needs_revision";
            const isMastered = node.status === "mastered";
            const isCompleted = node.status === "completed" || isMastered;

            return (
              <div key={node.id} className="relative">
                {/* Node Card */}
                <div
                  onClick={() => setActiveNode(node)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-white border-primary shadow-md scale-[1.01]"
                      : isLocked
                      ? "bg-neutral-50/80 border-border opacity-85 hover:opacity-100"
                      : isNeedsRevision
                      ? "bg-amber-50/40 border-amber-200 hover:border-amber-300"
                      : "bg-white border-border hover:border-primary/60 hover:bg-canvas-elevated"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (!isLocked) handleToggleNode(node.id);
                        }}
                        disabled={isLocked}
                        className={`w-11 h-11 rounded flex items-center justify-center transition-all shrink-0 ${
                          isMastered
                            ? "bg-[#0F7B3F] text-white shadow-2xs"
                            : isNeedsRevision
                            ? "bg-amber-100 text-[#B75F00] border border-amber-300"
                            : isLocked
                            ? "bg-neutral-200 text-neutral-400 cursor-not-allowed"
                            : isCompleted
                            ? "bg-emerald-600 text-white"
                            : "bg-canvas-elevated text-ink-muted hover:bg-white border border-border"
                        }`}
                        title={isLocked ? "Prerequisites Incomplete" : isCompleted ? "Mark as Incomplete" : "Mark as Completed"}
                      >
                        {isMastered ? (
                          <Check className="w-5 h-5 stroke-[3]" />
                        ) : isNeedsRevision ? (
                          <AlertTriangle className="w-5 h-5" />
                        ) : isLocked ? (
                          <Lock className="w-4 h-4" />
                        ) : isCompleted ? (
                          <Check className="w-5 h-5 stroke-[3]" />
                        ) : (
                          <Circle className="w-5 h-5" />
                        )}
                      </button>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className={`text-sm font-bold truncate ${
                            isCompleted ? "text-ink-muted" : "text-black"
                          }`}>
                            {node.title}
                          </h3>
                          {isLocked && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-200 text-neutral-600 font-bold uppercase">
                              Locked
                            </span>
                          )}
                          {isNeedsRevision && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-[#B75F00] font-bold uppercase">
                              Needs Revision
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2 text-xs text-ink-muted mt-0.5">
                          <span className="capitalize font-medium">{node.difficulty}</span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" /> {node.estimated_hours}h
                          </span>
                          {node.prerequisites.length > 0 && (
                            <>
                              <span>•</span>
                              <span className="text-[11px] truncate text-ink-muted">
                                Req: {node.prerequisites.join(", ")}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    {node.score !== undefined && node.score !== null && (
                      <span className={`text-xs px-2 py-1 rounded font-bold border shrink-0 ${
                        node.score >= 85
                          ? "bg-emerald-50 text-[#0F7B3F] border-emerald-200"
                          : "bg-amber-50 text-[#B75F00] border-amber-200"
                      }`}>
                        {node.score}% Score
                      </span>
                    )}
                  </div>

                  {isLocked && node.prerequisite_reason && (
                    <div className="mt-2 text-[11px] text-ink-muted bg-neutral-100 p-2 rounded flex items-center gap-1.5">
                      <Info className="w-3.5 h-3.5 text-neutral-500 shrink-0" />
                      <span>{node.prerequisite_reason}</span>
                    </div>
                  )}
                </div>

                {/* Edge Indicator */}
                {index < path.nodes.length - 1 && (
                  <div className="flex justify-center my-1 text-ink-muted">
                    <ArrowDown className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Selected Node Deep Dive (5 cols) */}
        <div className="lg:col-span-5">
          {activeNode ? (
            <div className="bg-white rounded-lg p-6 border border-border sticky top-24 space-y-4 shadow-2xs">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <span className="text-xs font-bold uppercase tracking-wider text-primary">
                  Module Inspector
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded bg-canvas-elevated text-ink-secondary font-semibold capitalize border border-border">
                  {activeNode.difficulty} Level
                </span>
              </div>

              <h2 className="text-lg font-bold text-black">{activeNode.title}</h2>
              <p className="text-xs text-ink-secondary leading-relaxed font-medium">{activeNode.description}</p>

              {activeNode.concepts && activeNode.concepts.length > 0 && (
                <div>
                  <span className="text-xs font-bold text-black block mb-1.5">Target Concepts:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {activeNode.concepts.map((c, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 rounded bg-canvas-elevated border border-border text-ink-secondary font-medium">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="p-3.5 rounded bg-canvas-elevated border border-border space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-ink-muted">Estimated Duration:</span>
                  <span className="text-black font-semibold">{activeNode.estimated_hours} Hours</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-ink-muted">Prerequisites:</span>
                  <span className="text-primary font-semibold">
                    {activeNode.prerequisites.length > 0 ? activeNode.prerequisites.join(", ") : "None (Foundational)"}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-ink-muted">State:</span>
                  <span className={`font-bold capitalize ${
                    activeNode.status === "mastered"
                      ? "text-[#0F7B3F]"
                      : activeNode.status === "needs_revision"
                      ? "text-[#B75F00]"
                      : activeNode.status === "locked"
                      ? "text-neutral-500"
                      : "text-primary"
                  }`}>
                    {activeNode.status?.replace("_", " ") || "Available"}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2 pt-1">
                <button
                  onClick={() => handleLaunchLesson(activeNode)}
                  disabled={activeNode.status === "locked"}
                  className={`w-full py-2.5 rounded font-bold text-xs flex items-center justify-center gap-2 shadow-2xs transition-colors ${
                    activeNode.status === "locked"
                      ? "bg-neutral-200 text-neutral-400 cursor-not-allowed"
                      : "bg-black hover:bg-neutral-800 text-white"
                  }`}
                >
                  <PlayCircle className="w-4 h-4 text-accent" />
                  <span>
                    {activeNode.status === "needs_revision" 
                      ? "Launch Targeted Revision Lesson" 
                      : "Launch AI Interactive Lesson"}
                  </span>
                </button>

                {!activeNode.status?.includes("locked") && (
                  <button
                    onClick={() => handleToggleNode(activeNode.id)}
                    disabled={isUpdating}
                    className={`w-full py-2 rounded font-semibold text-xs border transition-colors ${
                      activeNode.completed
                        ? "bg-white hover:bg-canvas-elevated text-ink-secondary border-border"
                        : "bg-emerald-50 hover:bg-emerald-100 text-[#0F7B3F] border-emerald-300 font-bold"
                    }`}
                  >
                    {activeNode.completed ? "Mark as Incomplete" : "Mark as Completed"}
                  </button>
                )}
              </div>

              {/* YouTube Grounded Educational Explanations */}
              <div className="pt-2 border-t border-border">
                <RelatedVideos
                  topic={activeNode.concepts && activeNode.concepts.length > 0 ? activeNode.concepts[0] : activeNode.title.replace(/^\d+\.\s*/, "")}
                  context={activeNode.description}
                />
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg p-8 text-center text-ink-muted border border-border">
              <BookOpen className="w-8 h-8 text-ink-muted mx-auto mb-2" />
              <p className="text-xs font-medium">Select any curriculum node to inspect details.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
