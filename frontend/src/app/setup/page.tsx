"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, ParsedStudentInstruction } from "@/lib/api";
import { 
  Sparkles, 
  Clock, 
  Languages, 
  GraduationCap, 
  Sliders, 
  ArrowRight,
  MessageSquare,
  Wand2,
  Loader2,
  BookOpen
} from "lucide-react";
import { useToast } from "@/context/ToastContext";

function SetupForm() {
  const router = useRouter();
  const { showSuccess, showError, showInfo } = useToast();
  const searchParams = useSearchParams();
  const initialTopic = searchParams.get("topic") || "Foundations of Quantum Mechanics";
  const materialId = searchParams.get("materialId") || undefined;
  const filename = searchParams.get("filename") || undefined;
  const initialInstruction = searchParams.get("instruction") || "";

  const [promptText, setPromptText] = useState(initialInstruction || "");
  const [isParsing, setIsParsing] = useState(false);
  const [topic, setTopic] = useState(initialTopic);
  const [targetChapter, setTargetChapter] = useState("");
  const [level, setLevel] = useState("beginner");
  const [goal, setGoal] = useState("understand_concept");
  const [style, setStyle] = useState("visual");
  const [teacherPersonality, setTeacherPersonality] = useState("socratic");
  const [language, setLanguage] = useState("en");
  const [timeBudget, setTimeBudget] = useState(20);
  const [isGenerating, setIsGenerating] = useState(false);

  // Auto-parse if instruction is provided in query params
  useEffect(() => {
    if (initialInstruction) {
      applyParsedInstruction(initialInstruction);
    }
  }, [initialInstruction]);

  const applyParsedInstruction = async (text: string) => {
    if (!text.trim()) return;
    setIsParsing(true);
    try {
      let parsed: ParsedStudentInstruction;
      if (materialId) {
        parsed = await api.parseInstructionForDocument(materialId, text);
      } else {
        // Fallback local regex parsing
        const lower = text.toLowerCase();
        const chMatch = lower.match(/(?:chapter|ch\.?|unit|section)\s*([0-9a-zA-Z_.-]+)/i);
        const timeMatch = lower.match(/(\d+)\s*(?:minutes|mins|min|m\b)/i);
        let lvl = "intermediate";
        if (lower.includes("beginner") || lower.includes("novice") || lower.includes("scratch")) lvl = "beginner";
        else if (lower.includes("advanced") || lower.includes("expert") || lower.includes("rigorous")) lvl = "advanced";

        let lang = "en";
        if (lower.includes("hindi") || lower.includes("हिंदी")) lang = "hi";
        else if (lower.includes("hinglish")) lang = "hinglish";
        else if (lower.includes("tamil")) lang = "ta";
        else if (lower.includes("telugu")) lang = "te";
        else if (lower.includes("bengali")) lang = "bn";
        else if (lower.includes("spanish")) lang = "es";

        let sty = "visual";
        if (lower.includes("example") || lower.includes("analog")) sty = "analogies";
        else if (lower.includes("code") || lower.includes("python")) sty = "code";
        else if (lower.includes("socratic") || lower.includes("question")) sty = "socratic";

        parsed = {
          raw_instruction: text,
          target_chapter: chMatch ? chMatch[1] : undefined,
          time_budget_minutes: timeMatch ? parseInt(timeMatch[1], 10) : 20,
          learner_level: lvl,
          language: lang,
          pedagogical_style: sty,
          include_checkpoints: true,
          include_final_assessment: true,
          simple_examples_requested: true,
          key_focus_topics: []
        };
      }

      if (parsed.learner_level) setLevel(parsed.learner_level);
      if (parsed.time_budget_minutes) setTimeBudget(parsed.time_budget_minutes);
      if (parsed.language) setLanguage(parsed.language);
      if (parsed.pedagogical_style) setStyle(parsed.pedagogical_style);
      if (parsed.target_chapter) setTargetChapter(parsed.target_chapter);

      showInfo("Auto-configured learning profile from your instruction!");
    } catch (err) {
      console.warn("Error parsing prompt:", err);
    } finally {
      setIsParsing(false);
    }
  };

  const handleGenerateLesson = async () => {
    setIsGenerating(true);
    try {
      const plan = await api.createLessonPlan({
        topic: materialId ? undefined : topic,
        material_id: materialId,
        instruction: promptText.trim() || undefined,
        target_chapter: targetChapter.trim() || undefined,
        learner_profile: {
          level,
          goal,
          preferred_style: style,
          language,
          time_budget_minutes: timeBudget,
          teacher_personality: teacherPersonality,
        },
        time_budget_minutes: timeBudget,
        language,
      });

      showSuccess("Personalized lesson generated successfully!");
      router.push(`/lesson/${plan.session_id}`);
    } catch (err: any) {
      const msg = err.message || "Failed to initialize lesson plan";
      showError(msg);
      setIsGenerating(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div>
        <span className="text-xs font-bold uppercase tracking-wider text-primary">
          Personalization Engine
        </span>
        <h1 className="text-3xl font-extrabold text-black mt-1">Configure Learner Profile</h1>
        <p className="text-sm text-ink-secondary mt-1 font-medium">
          {materialId
            ? `Calibrating adaptive lesson plan for uploaded document: "${filename || 'Document'}"`
            : `Personalizing instruction for: "${topic}"`}
        </p>
      </div>

      {/* Natural Language Prompt Assistant Card */}
      <div className="bg-[#F8FAFD] rounded-lg p-5 border border-primary/20 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold uppercase tracking-wider text-black flex items-center gap-2">
            <Wand2 className="w-4 h-4 text-primary" />
            <span>AI Prompt Assistant:</span>
          </label>
          <span className="text-[11px] text-ink-muted font-medium">Type any freeform instruction to auto-tune settings</span>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                applyParsedInstruction(promptText);
              }
            }}
            placeholder="e.g. I am a beginner. Teach me Chapter 4 in 20 minutes in Hindi with simple examples."
            className="flex-1 p-2.5 rounded-lg bg-white border border-border text-xs text-black placeholder-ink-muted focus:outline-none focus:border-primary font-medium"
          />
          <button
            type="button"
            onClick={() => applyParsedInstruction(promptText)}
            disabled={isParsing || !promptText.trim()}
            className="px-4 py-2.5 rounded bg-primary text-white text-xs font-bold hover:bg-primary/90 transition flex items-center gap-1.5 cursor-pointer disabled:opacity-40"
          >
            {isParsing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            <span>Auto-Tune</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg p-6 sm:p-8 border border-border space-y-6 shadow-2xs">
        {/* Target Chapter or Topic if specified */}
        {targetChapter && (
          <div className="p-3 rounded bg-blue-50/60 border border-blue-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-primary" />
              <span className="text-xs font-bold text-black">Targeted Chapter / Section:</span>
              <span className="text-xs font-mono font-bold text-primary bg-white px-2 py-0.5 rounded border border-border">
                {targetChapter}
              </span>
            </div>
            <button
              type="button"
              onClick={() => setTargetChapter("")}
              className="text-[11px] text-ink-muted hover:text-black underline cursor-pointer"
            >
              Clear chapter filter
            </button>
          </div>
        )}

        {/* Knowledge Level */}
        <div>
          <label className="text-xs font-bold uppercase tracking-wider text-black flex items-center gap-2 mb-3">
            <GraduationCap className="w-4 h-4 text-primary" />
            <span>Target Cognitive Level:</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: "beginner", title: "Beginner", desc: "Intuitive mental models, foundational definitions & analogies" },
              { id: "intermediate", title: "Intermediate", desc: "Formal mechanisms, derivations & practical applications" },
              { id: "advanced", title: "Advanced", desc: "Rigorous proofs, edge cases, state spaces & computational execution" },
            ].map((lvl) => (
              <div
                key={lvl.id}
                onClick={() => setLevel(lvl.id)}
                className={`p-3.5 rounded border cursor-pointer transition-all ${
                  level === lvl.id
                    ? "bg-[#E9F1FC] border-primary text-black shadow-2xs"
                    : "bg-white border-border text-ink-secondary hover:border-primary/50 hover:bg-canvas-elevated"
                }`}
              >
                <span className={`font-bold text-xs block ${level === lvl.id ? 'text-primary' : 'text-black'}`}>{lvl.title}</span>
                <p className="text-xs text-ink-muted mt-1 leading-snug">{lvl.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Time Budget */}
        <div>
          <label className="text-xs font-bold uppercase tracking-wider text-black flex items-center gap-2 mb-3">
            <Clock className="w-4 h-4 text-primary" />
            <span>Available Time Budget:</span>
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { mins: 5, label: "5 Minutes", badge: "2 Core Concepts" },
              { mins: 20, label: "20 Minutes", badge: "Structured Lesson" },
              { mins: 60, label: "60 Minutes", badge: "Comprehensive Deep Dive" },
              { mins: 10080, label: "7-Day Path", badge: "Multi-Session DAG" },
            ].map((item) => (
              <div
                key={item.mins}
                onClick={() => setTimeBudget(item.mins)}
                className={`p-3 rounded border text-center cursor-pointer transition-all ${
                  timeBudget === item.mins
                    ? "bg-[#E9F1FC] border-primary text-black shadow-2xs"
                    : "bg-white border-border text-ink-secondary hover:border-primary/50 hover:bg-canvas-elevated"
                }`}
              >
                <span className={`font-bold text-xs block ${timeBudget === item.mins ? 'text-primary' : 'text-black'}`}>{item.label}</span>
                <span className="text-[10px] text-ink-muted font-mono mt-0.5 block">{item.badge}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Teacher Personality, Preferred Style & Language */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-border">
          {/* Teacher Personality */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-black flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-primary" />
              <span>Teacher Personality:</span>
            </label>
            <select
              value={teacherPersonality}
              onChange={(e) => setTeacherPersonality(e.target.value)}
              className="w-full p-2.5 rounded bg-white border border-border text-xs text-black focus:outline-none focus:border-primary font-medium"
            >
              <option value="socratic">Socratic Guide (Deep Reasoning)</option>
              <option value="friendly">Friendly Mentor (Encouraging)</option>
              <option value="strict_coach">Strict Exam Coach (Rigorous)</option>
              <option value="visual">Visual Architect (Models & Diagrams)</option>
            </select>
          </div>

          {/* Preferred Style */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-black flex items-center gap-2 mb-2">
              <Sliders className="w-4 h-4 text-primary" />
              <span>Pedagogical Style:</span>
            </label>
            <select
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="w-full p-2.5 rounded bg-white border border-border text-xs text-black focus:outline-none focus:border-primary font-medium"
            >
              <option value="visual">Visual & Interactive Diagrams</option>
              <option value="analogies">Analogy & Metaphor First</option>
              <option value="socratic">Socratic Questioning</option>
              <option value="code">Code & Computational Demos</option>
            </select>
          </div>

          {/* Language */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-black flex items-center gap-2 mb-2">
              <Languages className="w-4 h-4 text-primary" />
              <span>Instruction Language:</span>
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full p-2.5 rounded bg-white border border-border text-xs text-black focus:outline-none focus:border-primary font-medium"
            >
              <option value="en">English (Global)</option>
              <option value="hi">हिंदी (Hindi)</option>
              <option value="hinglish">Hinglish (Conversational)</option>
              <option value="ta">தமிழ் (Tamil)</option>
              <option value="te">తెలుగు (Telugu)</option>
              <option value="bn">বাংলা (Bengali)</option>
              <option value="es">Español (Spanish)</option>
            </select>
          </div>
        </div>

        {/* Launch Button */}
        <div className="pt-4 border-t border-border flex justify-end">
          <button
            onClick={handleGenerateLesson}
            disabled={isGenerating}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3 rounded bg-black hover:bg-neutral-800 text-white font-bold text-sm shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-40"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isGenerating ? "Synthesizing Adaptive Lesson..." : "Launch AI Teaching Session"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SetupPage() {
  return (
    <Suspense fallback={<div className="text-center py-20 text-ink-muted">Loading Configuration...</div>}>
      <SetupForm />
    </Suspense>
  );
}

