"use client";

import { useState } from "react";
import { VisualSpec, VisualDecision, api } from "@/lib/api";
import { 
  Play, 
  Terminal, 
  Layers, 
  TrendingUp, 
  Calendar, 
  FileCode,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Compass,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Info,
  ArrowRight
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine
} from "recharts";
import katex from "katex";

interface VisualRendererProps {
  visualSpec: VisualSpec;
}

function KaTeXMath({ formula, inline = true }: { formula: string; inline?: boolean }) {
  try {
    const cleanFormula = formula.replace(/^\$+|\$+$/g, "").trim();
    const html = katex.renderToString(cleanFormula, {
      throwOnError: false,
      displayMode: !inline,
    });
    return (
      <span
        className="max-w-full overflow-x-auto inline-block align-middle scrollbar-thin"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  } catch {
    return <span className="font-mono text-xs max-w-full overflow-x-auto inline-block">{formula}</span>;
  }
}

function DecisionInspector({ decision }: { decision?: VisualDecision }) {
  const [isOpen, setIsOpen] = useState(false);
  if (!decision) return null;

  return (
    <div className="mb-3 rounded-lg border border-indigo-100 bg-gradient-to-r from-indigo-50/70 via-blue-50/50 to-purple-50/70 text-xs overflow-hidden transition-all shadow-2xs">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 flex items-center justify-between font-semibold text-indigo-950 hover:bg-indigo-100/40 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-600 shrink-0" />
          <span className="font-bold text-xs">AI Visual Planning & Pedagogical Decision</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-600 text-white font-mono uppercase tracking-wider">
            {decision.subject} • {decision.visual_needed}
          </span>
        </div>
        <div className="flex items-center gap-1 text-indigo-600 font-medium text-xs">
          <span>{isOpen ? "Hide Details" : "Inspect Reasoning"}</span>
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {isOpen && (
        <div className="px-3.5 py-3 border-t border-indigo-100/80 bg-white/90 space-y-2.5 text-ink-secondary text-xs leading-relaxed animate-in fade-in-50 duration-200">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div className="p-2 rounded bg-slate-50 border border-slate-200/70">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Concept Type & Goal</span>
              <p className="font-semibold text-ink-primary mt-0.5 capitalize">{decision.concept_type.replace(/_/g, " ")}</p>
              <p className="text-[11px] text-ink-muted mt-0.5">{decision.pedagogical_goal}</p>
            </div>
            <div className="p-2 rounded bg-slate-50 border border-slate-200/70">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Pedagogical Rationale</span>
              <p className="text-[11px] text-ink-primary mt-0.5">{decision.reason}</p>
            </div>
          </div>

          {decision.observation_prompt && (
            <div className="p-2.5 rounded bg-blue-50/80 border border-blue-200 flex items-start gap-2">
              <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wider block">Teacher Observation Prompt</span>
                <p className="text-xs text-blue-950 font-medium italic mt-0.5">"{decision.observation_prompt}"</p>
              </div>
            </div>
          )}

          {decision.knowledge_check && (
            <div className="p-2 rounded bg-amber-50/70 border border-amber-200 flex items-start gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider block">Intuition Check Target</span>
                <p className="text-xs text-amber-950 font-medium mt-0.5">{decision.knowledge_check}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function VisualRenderer({ visualSpec }: VisualRendererProps) {
  const { type, title, payload, decision } = visualSpec;
  const [selectedHotspot, setSelectedHotspot] = useState<any>(null);
  const [selectedStage, setSelectedStage] = useState<any>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [codeOutput, setCodeOutput] = useState<string>(payload?.output || payload?.stdout || "Ready to execute Python script...");
  const [executionSuccess, setExecutionSuccess] = useState<boolean | null>(null);

  // 1. PHYSICS FREE-BODY VECTOR DIAGRAM
  if (type === "free_body_diagram") {
    const equations = payload?.equations || ["\\Sigma F = F_{app} - f_k = m a"];
    const forces = payload?.forces || [];
    const steps = payload?.step_by_step || [];

    return (
      <div className="bg-white rounded-lg p-4 sm:p-5 border border-border flex flex-col h-full shadow-2xs hover:shadow-md transition-shadow max-w-full overflow-hidden">
        <DecisionInspector decision={decision} />

        <div className="flex items-center justify-between pb-3 border-b border-border mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <Compass className="w-5 h-5 text-rose-600 shrink-0" />
            <h3 className="font-bold text-sm text-ink-primary truncate">{title}</h3>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded bg-rose-50 text-rose-700 font-bold border border-rose-200 shrink-0">
            Physics Vector Mechanics
          </span>
        </div>

        {/* Governing Vector Force Equation */}
        <div className="mb-3 p-3 rounded bg-slate-900 text-white border border-slate-800 max-w-full overflow-hidden">
          <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1.5 font-mono">
            Newton's Second Law & Net Force Balance:
          </span>
          <div className="flex flex-wrap gap-2 items-center overflow-x-auto max-w-full py-0.5">
            {equations.map((eq: string, idx: number) => (
              <div key={idx} className="px-3 py-1 rounded bg-slate-800 text-rose-300 text-sm font-semibold border border-slate-700">
                <KaTeXMath formula={eq} />
              </div>
            ))}
          </div>
        </div>

        {/* Vector SVG Diagram */}
        <div className="relative rounded bg-white border border-border overflow-x-auto max-w-full flex items-center justify-center p-2 min-h-[220px]">
          {payload?.svg_code ? (
            <div 
              className="w-full h-full flex items-center justify-center overflow-x-auto max-w-full"
              dangerouslySetInnerHTML={{ __html: payload.svg_code }} 
            />
          ) : (
            <div className="text-center p-6 text-ink-muted">
              <Compass className="w-10 h-10 text-rose-600 mx-auto mb-2 opacity-80" />
              <p className="text-xs font-semibold">Free Body Vector Diagram</p>
            </div>
          )}
        </div>

        {/* Forces Breakdown Pills */}
        {forces.length > 0 && (
          <div className="mt-3">
            <span className="text-xs font-bold text-ink-secondary block mb-1.5">Interacting Force Vectors:</span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {forces.map((f: any, idx: number) => (
                <div key={idx} className="p-2 rounded bg-slate-50 border border-slate-200 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-ink-primary font-mono">{f.name}</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-white text-slate-700 border border-slate-200 font-mono">{f.val}</span>
                  </div>
                  <span className="text-[11px] text-ink-muted mt-0.5 block">{f.dir}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step-by-step derivation */}
        {steps.length > 0 && (
          <div className="mt-3 pt-2 border-t border-border">
            <span className="text-xs font-bold text-ink-secondary block mb-1">Dynamical Derivation:</span>
            <ul className="space-y-1 text-xs text-ink-secondary">
              {steps.map((st: string, idx: number) => (
                <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                  <span className="text-rose-600 font-bold mt-0.5">•</span>
                  <span><KaTeXMath formula={st} /></span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // 2. BIOLOGICAL PROCESS CYCLE (e.g., Photosynthesis / Krebs)
  if (type === "process_cycle") {
    const stages = payload?.stages || [];
    const takeaways = payload?.key_takeaways || [];

    return (
      <div className="bg-white rounded-lg p-4 sm:p-5 border border-border flex flex-col h-full shadow-2xs hover:shadow-md transition-shadow max-w-full overflow-hidden">
        <DecisionInspector decision={decision} />

        <div className="flex items-center justify-between pb-3 border-b border-border mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <RefreshCw className="w-5 h-5 text-emerald-600 shrink-0" />
            <h3 className="font-bold text-sm text-ink-primary truncate">{title}</h3>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold border border-emerald-200 shrink-0">
            Biochemical Process Cycle
          </span>
        </div>

        {/* Process Cycle SVG */}
        <div className="relative rounded bg-white border border-border overflow-x-auto max-w-full flex items-center justify-center p-2 min-h-[200px]">
          {payload?.svg_code ? (
            <div 
              className="w-full h-full flex items-center justify-center overflow-x-auto max-w-full"
              dangerouslySetInnerHTML={{ __html: payload.svg_code }} 
            />
          ) : (
            <div className="text-center p-6 text-ink-muted">
              <RefreshCw className="w-10 h-10 text-emerald-600 mx-auto mb-2 opacity-80" />
              <p className="text-xs font-semibold">Biochemical Cycle Visualizer</p>
            </div>
          )}
        </div>

        {/* Interactive Stages Carousel/Cards */}
        {stages.length > 0 && (
          <div className="mt-3">
            <span className="text-xs font-bold text-ink-secondary block mb-1.5">Cycle Phases & Energetics:</span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {stages.map((stg: any, idx: number) => (
                <div 
                  key={idx}
                  onClick={() => setSelectedStage(stg)}
                  className={`p-2.5 rounded border text-left cursor-pointer transition-all ${
                    selectedStage?.name === stg.name
                      ? "bg-emerald-50 border-emerald-500 text-ink-primary shadow-2xs scale-[1.01]"
                      : "bg-white border-border hover:border-emerald-300 text-ink-secondary"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-emerald-800">{stg.name}</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-900 font-mono">Stage {stg.id || idx + 1}</span>
                  </div>
                  <p className="text-[11px] text-ink-muted mt-1 leading-relaxed">{stg.desc}</p>
                  {(stg.inputs || stg.outputs) && (
                    <div className="mt-1.5 pt-1.5 border-t border-emerald-100 flex items-center justify-between text-[10px] font-mono">
                      <span className="text-slate-600">In: {stg.inputs}</span>
                      <ArrowRight className="w-3 h-3 text-emerald-500 inline" />
                      <span className="text-emerald-700 font-bold">Out: {stg.outputs}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key takeaways */}
        {takeaways.length > 0 && (
          <div className="mt-3 pt-2 border-t border-border">
            <span className="text-xs font-bold text-ink-secondary block mb-1">Biological Invariants:</span>
            <ul className="space-y-1 text-xs text-ink-secondary">
              {takeaways.map((tk: string, idx: number) => (
                <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                  <span className="text-emerald-600 font-bold mt-0.5">•</span>
                  <span>{tk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // 3. MATH & PHYSICS ROUTER (KaTeX + Real Recharts Coordinate Chart)
  if (type === "equation/graph" || type.includes("math") || type.includes("physics")) {
    const xs = payload?.x_values || [-4, -3, -2, -1, 0, 1, 2, 3, 4];
    const ys = payload?.y_values || [16, 9, 4, 1, 0, 1, 4, 9, 16];
    const equations = payload?.equations || ["f(x) = x^2"];
    const steps = payload?.step_by_step || [];

    const chartData = xs.map((xVal: number, i: number) => ({
      x: xVal,
      y: ys[i] !== undefined ? ys[i] : 0,
    }));

    return (
      <div className="bg-white rounded-lg p-4 sm:p-5 border border-border flex flex-col h-full shadow-2xs hover:shadow-md transition-shadow max-w-full overflow-hidden">
        <DecisionInspector decision={decision} />

        <div className="flex items-center justify-between pb-3 border-b border-border mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <TrendingUp className="w-5 h-5 text-primary shrink-0" />
            <h3 className="font-bold text-sm text-ink-primary truncate">{title}</h3>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded bg-[#E9F1FC] text-primary font-bold border border-blue-200 shrink-0">
            Analytical Coordinates & Plots
          </span>
        </div>

        {/* Governing Analytical Formula with KaTeX */}
        <div className="mb-3 p-3 rounded bg-canvas-elevated border border-border max-w-full overflow-hidden">
          <span className="text-[11px] uppercase font-bold text-ink-muted tracking-wider block mb-1.5">
            Governing Analytical Formula (LaTeX Rendered):
          </span>
          <div className="flex flex-wrap gap-2 items-center overflow-x-auto max-w-full py-1">
            {equations.map((eq: string, idx: number) => (
              <div 
                key={idx} 
                className="px-3 py-1.5 rounded bg-white text-primary border border-blue-200 shadow-2xs text-sm font-semibold flex items-center max-w-full overflow-x-auto"
              >
                <KaTeXMath formula={eq} />
              </div>
            ))}
          </div>
        </div>

        {/* Real Dynamic Recharts Plot Canvas */}
        <div className="relative flex-1 min-h-[220px] rounded bg-white border border-border p-3 flex flex-col justify-center max-w-full overflow-hidden">
          <div className="text-center mb-1">
            <span className="text-xs font-bold text-ink-primary font-mono">{payload?.plot_title || "Dynamic State Trajectory"}</span>
          </div>

          <div className="w-full h-44 overflow-x-auto max-w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis 
                  dataKey="x" 
                  stroke="#64748B" 
                  fontSize={10} 
                  tickLine={false} 
                  label={{ value: payload?.x_label || "x (Input)", position: "insideBottom", offset: -5, fontSize: 10, fill: "#64748B" }}
                />
                <YAxis 
                  stroke="#64748B" 
                  fontSize={10} 
                  tickLine={false}
                  label={{ value: payload?.y_label || "f(x)", angle: -90, position: "insideLeft", fontSize: 10, fill: "#64748B" }}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: "#0F172A", color: "#F8FAFC", borderRadius: "6px", fontSize: "11px", fontWeight: "bold" }}
                  itemStyle={{ color: "#38BDF8" }}
                  formatter={(val: any) => [`${val}`, payload?.y_label || "f(x)"]}
                  labelFormatter={(lbl: any) => `x = ${lbl}`}
                />
                <ReferenceLine y={0} stroke="#94A3B8" strokeWidth={1.5} />
                <ReferenceLine x={0} stroke="#94A3B8" strokeWidth={1.5} />
                <Line 
                  type="monotone" 
                  dataKey="y" 
                  stroke="#0056D2" 
                  strokeWidth={2.5} 
                  dot={{ r: 3, fill: "#0056D2", strokeWidth: 1, stroke: "#FFFFFF" }} 
                  activeDot={{ r: 5, fill: "#F97316" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Step-by-Step Analytical Derivation with KaTeX */}
        {steps.length > 0 && (
          <div className="mt-3 pt-2 border-t border-border">
            <span className="text-xs font-bold text-ink-secondary block mb-1">Analytical Derivation:</span>
            <ul className="space-y-1 text-xs text-ink-secondary">
              {steps.map((st: string, idx: number) => (
                <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span><KaTeXMath formula={st} /></span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // 4. BIOLOGY & LIFE SCIENCES ROUTER
  if (type === "labeled-diagram" || type.includes("bio") || type.includes("diagram")) {
    const labels = payload?.labels || [];

    return (
      <div className="bg-white rounded-lg p-4 sm:p-5 border border-border flex flex-col h-full shadow-2xs hover:shadow-md transition-shadow max-w-full overflow-hidden">
        <DecisionInspector decision={decision} />

        <div className="flex items-center justify-between pb-3 border-b border-border mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <Layers className="w-5 h-5 text-[#0F7B3F] shrink-0" />
            <h3 className="font-bold text-sm text-ink-primary truncate">{title}</h3>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded bg-emerald-50 text-[#0F7B3F] font-bold border border-emerald-200 shrink-0">
            Biology & Life Sciences
          </span>
        </div>

        {/* Interactive SVG Diagram */}
        <div className="relative rounded bg-white border border-border overflow-x-auto max-w-full flex items-center justify-center p-3 min-h-[200px]">
          {payload?.svg_code ? (
            <div 
              className="w-full h-full flex items-center justify-center overflow-x-auto max-w-full"
              dangerouslySetInnerHTML={{ __html: payload.svg_code }} 
            />
          ) : (
            <div className="text-center p-6 text-ink-muted">
              <Layers className="w-10 h-10 text-[#0F7B3F] mx-auto mb-2 opacity-80" />
              <p className="text-xs font-semibold">Interactive Labeled Structural Model</p>
            </div>
          )}
        </div>

        {/* Interactive Hotspot Pills */}
        {labels.length > 0 && (
          <div className="mt-3">
            <span className="text-xs font-bold text-ink-secondary block mb-1.5">Structural Components:</span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {labels.map((item: any, idx: number) => (
                <div 
                  key={idx}
                  onClick={() => setSelectedHotspot(item)}
                  className={`p-2.5 rounded border text-left cursor-pointer transition-all ${
                    selectedHotspot?.name === item.name
                      ? "bg-emerald-50 border-[#0F7B3F] text-ink-primary shadow-2xs scale-[1.02]"
                      : "bg-white border-border hover:border-emerald-300 text-ink-secondary"
                  }`}
                >
                  <p className="font-bold text-xs text-[#0F7B3F] flex items-center gap-1 font-mono">
                    <span className="w-2 h-2 rounded-full bg-[#0F7B3F]"></span>
                    {item.name}
                  </p>
                  <p className="text-[11px] text-ink-muted mt-1 line-clamp-2">{item.role}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // 5. CHRONOLOGY & HISTORY ROUTER
  if (type === "timeline/map" || type.includes("timeline") || type.includes("history")) {
    const events = payload?.events || [];

    return (
      <div className="bg-white rounded-lg p-4 sm:p-5 border border-border flex flex-col h-full shadow-2xs hover:shadow-md transition-shadow max-w-full overflow-hidden">
        <DecisionInspector decision={decision} />

        <div className="flex items-center justify-between pb-3 border-b border-border mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <Calendar className="w-5 h-5 text-[#B75F00] shrink-0" />
            <h3 className="font-bold text-sm text-ink-primary truncate">{title}</h3>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded bg-amber-50 text-[#B75F00] font-bold border border-amber-200 shrink-0">
            Chronology & History
          </span>
        </div>

        {/* Timeline Events Stack */}
        <div className="relative flex-1 overflow-y-auto pr-2 space-y-3 pl-4 border-l-2 border-amber-300 ml-2 max-h-[340px] max-w-full overflow-x-hidden">
          {events.map((ev: any, idx: number) => (
            <div key={idx} className="relative group">
              <div className="absolute -left-[23px] top-1.5 w-3.5 h-3.5 rounded-full bg-[#B75F00] border-2 border-white group-hover:scale-125 transition-transform shadow-2xs" />
              
              <div className="p-3 rounded bg-white border border-border group-hover:border-amber-400 transition-colors">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono font-bold text-[#B75F00]">{ev.year}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-amber-50 text-[#B75F00] font-bold border border-amber-200">{ev.tag}</span>
                </div>
                <h4 className="font-bold text-xs text-ink-primary">{ev.title}</h4>
                <p className="text-xs text-ink-secondary mt-1 leading-relaxed">{ev.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // 6. COMPUTER SCIENCE & CODE EXECUTION ROUTER
  const code = payload?.code || "# Python Code Demonstration\nimport math\n\ndef compute_kinetic_energy(mass_kg, velocity_mps):\n    return 0.5 * mass_kg * (velocity_mps ** 2)\n\nprint('Kinetic Energy:', compute_kinetic_energy(1200, 25), 'Joules')";
  
  const handleRunCode = async () => {
    setIsExecuting(true);
    setExecutionSuccess(null);
    try {
      const res = await api.runPythonCode(code);
      setExecutionSuccess(res.success);
      setCodeOutput(res.output || res.stdout || res.stderr || "Process completed with 0 outputs.");
    } catch (err: any) {
      setExecutionSuccess(false);
      setCodeOutput(`Execution Error: ${err.message || err}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg p-4 sm:p-5 border border-border flex flex-col h-full shadow-2xs hover:shadow-md transition-shadow max-w-full overflow-hidden">
      <DecisionInspector decision={decision} />

      <div className="flex items-center justify-between pb-3 border-b border-border mb-3 flex-wrap gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <FileCode className="w-5 h-5 text-primary shrink-0" />
          <h3 className="font-bold text-sm text-ink-primary truncate">{title}</h3>
        </div>
        <button
          onClick={handleRunCode}
          disabled={isExecuting}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded bg-primary hover:bg-primary-hover text-white font-mono font-bold text-xs transition-all shadow-2xs hover:scale-105 active:scale-95 disabled:opacity-50 min-h-[40px]"
        >
          {isExecuting ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5 fill-current" />
          )}
          <span>{isExecuting ? "Running Sandbox..." : "Run Python"}</span>
        </button>
      </div>

      {/* Code Editor Panel */}
      <div className="rounded bg-canvas-elevated border border-border overflow-hidden mb-3 max-w-full">
        <div className="bg-white px-3 py-1.5 border-b border-border flex items-center justify-between text-[11px] text-ink-muted font-mono flex-wrap gap-1">
          <span className="text-primary font-bold">sandbox_execution.py</span>
          <span>Python 3 Sandbox</span>
        </div>
        <pre className="p-3 text-xs font-mono text-ink-primary overflow-x-auto leading-relaxed max-h-[160px] max-w-full">
          <code>{code}</code>
        </pre>
      </div>

      {/* Terminal Output */}
      <div className="flex-1 rounded bg-canvas-elevated border border-border p-3 font-mono text-xs text-ink-secondary flex flex-col justify-start max-w-full overflow-hidden">
        <div className="flex items-center justify-between text-[10px] text-ink-muted mb-1 border-b border-border pb-1 font-bold">
          <div className="flex items-center gap-1.5">
            <Terminal className="w-3 h-3 text-primary" />
            <span>Captured Standard Output</span>
          </div>
          {executionSuccess !== null && (
            <span className={`flex items-center gap-1 ${executionSuccess ? "text-emerald-600" : "text-rose-600"}`}>
              {executionSuccess ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
              {executionSuccess ? "Exit Code 0" : "Execution Failed"}
            </span>
          )}
        </div>
        <pre className={`text-xs whitespace-pre-wrap font-mono mt-1 font-bold max-w-full overflow-x-auto ${
          executionSuccess === false ? "text-rose-600" : "text-primary"
        }`}>
          {codeOutput}
        </pre>
      </div>
    </div>
  );
}
