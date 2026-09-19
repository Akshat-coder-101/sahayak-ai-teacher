"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, DocumentUploadResponse, ParsedStudentInstruction } from "@/lib/api";
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  ArrowRight, 
  FileCheck, 
  AlertCircle, 
  Sparkles, 
  Clock, 
  BookOpen, 
  Tag, 
  Loader2, 
  ShieldCheck,
  MessageSquare,
  Globe,
  Sliders,
  Check
} from "lucide-react";
import { useToast } from "@/context/ToastContext";

const MAX_FILE_SIZE_MB = 25;
const ALLOWED_EXTENSIONS = ["pdf", "docx", "pptx", "txt", "doc", "ppt"];

const PRESET_PROMPTS = [
  {
    label: "Beginner Hindi (20m, Ch. 4)",
    text: "I am a beginner. Teach me Chapter 4 in 20 minutes. Explain it in Hindi using simple examples. Ask me questions during the lesson and test me at the end."
  },
  {
    label: "5-Min Quick Concept Revision",
    text: "Teach me the core concepts in 5 minutes with concise analogies and a quick check."
  },
  {
    label: "60-Min Deep Dive & Visuals",
    text: "Give me an in-depth 60 minute lesson with interactive visual diagrams, derivations, and a comprehensive final test."
  }
];

export default function UploadPage() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isGeneratingLesson, setIsGeneratingLesson] = useState(false);
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);
  const [studentInstruction, setStudentInstruction] = useState(
    "I am a beginner. Teach me Chapter 4 in 20 minutes. Explain it in Hindi using simple examples. Ask me questions during the lesson and test me at the end."
  );
  const [isParsingInstruction, setIsParsingInstruction] = useState(false);
  const [parsedInstruction, setParsedInstruction] = useState<ParsedStudentInstruction | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateSelectedFile = (selectedFile: File): boolean => {
    const ext = selectedFile.name.split(".").pop()?.toLowerCase() || "";
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      const msg = `Unsupported file type ".${ext}". Please upload a PDF, DOCX, PPTX, or TXT file.`;
      setError(msg);
      showError(msg);
      return false;
    }
    if (selectedFile.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      const msg = `File exceeds the maximum allowed size of ${MAX_FILE_SIZE_MB}MB.`;
      setError(msg);
      showError(msg);
      return false;
    }
    if (selectedFile.size === 0) {
      const msg = "Selected file is empty.";
      setError(msg);
      showError(msg);
      return false;
    }
    setError(null);
    return true;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      if (validateSelectedFile(f)) {
        setFile(f);
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const f = e.dataTransfer.files[0];
      if (validateSelectedFile(f)) {
        setFile(f);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a valid document to upload.");
      return;
    }

    setIsUploading(true);
    setError(null);
    try {
      const res = await api.uploadDocument(file);
      setUploadResult(res);
      showSuccess(`Successfully ingested "${res.filename}" with ${res.chunk_count} semantic chunks.`);
    } catch (err: any) {
      const msg = err.message || "Failed to parse and vectorize document";
      setError(msg);
      showError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleParseInstruction = async (text: string) => {
    if (!uploadResult?.document_id || !text.trim()) return;
    setIsParsingInstruction(true);
    try {
      const res = await api.parseInstructionForDocument(uploadResult.document_id, text);
      setParsedInstruction(res);
    } catch (err) {
      console.warn("Could not parse instruction:", err);
    } finally {
      setIsParsingInstruction(false);
    }
  };

  const handleGenerateLesson = async () => {
    if (!uploadResult?.document_id) return;
    setIsGeneratingLesson(true);
    setError(null);
    try {
      const plan = await api.planLessonFromDocument(uploadResult.document_id, {
        instruction: studentInstruction.trim() || undefined,
        time_budget_minutes: parsedInstruction?.time_budget_minutes || 20,
        language: parsedInstruction?.language || "en",
        target_chapter: parsedInstruction?.target_chapter || undefined
      });
      showSuccess(`Grounded lesson generated with ${plan.segments.length} progressive segments.`);
      router.push(`/lesson/${plan.session_id}`);
    } catch (err: any) {
      const msg = err.message || "Failed to generate grounded lesson plan";
      setError(msg);
      showError(msg);
      setIsGeneratingLesson(false);
    }
  };

  const handleProceedToSetup = () => {
    if (uploadResult?.document_id) {
      router.push(`/setup?materialId=${uploadResult.document_id}&filename=${encodeURIComponent(uploadResult.filename)}&instruction=${encodeURIComponent(studentInstruction)}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-primary">
            RAG Ingestion Pipeline
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-[#0F7B3F] font-mono font-bold border border-emerald-200">
            Zero-Hallucination Grounded
          </span>
        </div>
        <h1 className="text-3xl font-extrabold text-black mt-1">Upload Learning Material</h1>
        <p className="text-sm text-ink-secondary mt-1 font-medium">
          Upload PDF, DOCX, PPTX, or TXT notes. Our semantic chunker indexes your material into vector storage with strict chunk-level citations.
        </p>
      </div>

      {/* Drag & Drop Upload Zone */}
      {!uploadResult ? (
        <div className="space-y-6">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-border hover:border-primary rounded-xl p-10 text-center bg-white transition-all cursor-pointer relative shadow-2xs hover:shadow-md"
          >
            <input
              type="file"
              accept=".pdf,.docx,.doc,.pptx,.ppt,.txt"
              onChange={handleFileChange}
              className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
            />

            <div className="flex flex-col items-center">
              <div className="w-16 h-16 rounded-xl bg-[#E9F1FC] text-primary flex items-center justify-center mb-4">
                <UploadCloud className="w-8 h-8" />
              </div>
              <h3 className="text-base font-bold text-black">
                {file ? file.name : "Drag & drop files here, or click to browse"}
              </h3>
              <p className="text-xs text-ink-muted mt-1.5 font-medium">
                Supports PDF, DOCX, PPTX, TXT up to 25MB
              </p>

              {file && (
                <div className="mt-4 px-3.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-[#0F7B3F] text-xs font-bold flex items-center gap-1.5">
                  <FileCheck className="w-4 h-4 text-[#0F7B3F]" />
                  <span>{(file.size / 1024 / 1024).toFixed(2)} MB Selected</span>
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-xs text-[#C21E1E] font-semibold flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-[#C21E1E] flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <button
              onClick={handleUpload}
              disabled={isUploading || !file}
              className="w-full sm:w-auto px-7 py-3 rounded bg-black hover:bg-neutral-800 text-white font-bold text-sm shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-40 flex items-center justify-center gap-2 cursor-pointer"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Chunking & Vectorizing Document...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Ingest & Vectorize Document</span>
                </>
              )}
            </button>

            <span className="text-xs text-ink-muted font-medium flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-primary" />
              Strict Anti-Hallucination Grounding Enforced
            </span>
          </div>
        </div>
      ) : (
        /* Ingestion Success & Document Outline Visualizer */
        <div className="space-y-6 animate-in fade-in duration-200">
          <div className="bg-white rounded-lg p-6 border border-border space-y-5 shadow-2xs">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="w-6 h-6 text-[#0F7B3F]" />
                <div>
                  <h3 className="font-bold text-base text-black">{uploadResult.detected_title}</h3>
                  <p className="text-xs text-ink-muted flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5" />
                    {uploadResult.filename}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs font-bold text-[#0F7B3F] block">{uploadResult.chunk_count} Semantic Chunks</span>
                <p className="text-[11px] text-ink-muted">{uploadResult.page_count} Pages / Sections</p>
              </div>
            </div>

            {/* Key Topics Detected */}
            {uploadResult.key_topics && uploadResult.key_topics.length > 0 && (
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-ink-muted block mb-2.5">
                  Detected Core Topics & Learning Units:
                </span>
                <div className="flex flex-wrap gap-2">
                  {uploadResult.key_topics.map((topic, i) => (
                    <div key={i} className="px-3 py-1.5 rounded-lg bg-[#E9F1FC] text-primary text-xs font-semibold flex items-center gap-1.5 border border-primary/20">
                      <Tag className="w-3 h-3 text-primary" />
                      <span>{topic}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Natural Language Instruction Input */}
            <div className="pt-2 border-t border-border space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-black flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-primary" />
                  <span>Student Instructions for AI Teacher:</span>
                </label>
                <span className="text-[11px] text-ink-muted font-medium">Natural language prompt</span>
              </div>

              <textarea
                value={studentInstruction}
                onChange={(e) => {
                  setStudentInstruction(e.target.value);
                  if (parsedInstruction) setParsedInstruction(null);
                }}
                rows={3}
                placeholder="e.g. I am a beginner. Teach me Chapter 4 in 20 minutes. Explain it in Hindi using simple examples. Ask me questions during the lesson and test me at the end."
                className="w-full p-3.5 rounded-lg bg-neutral-50 border border-border text-xs text-black placeholder-ink-muted focus:outline-none focus:border-primary focus:bg-white font-medium leading-relaxed"
              />

              {/* Quick Prompt Presets */}
              <div className="space-y-1.5">
                <span className="text-[11px] font-semibold text-ink-muted">Quick Prompts:</span>
                <div className="flex flex-wrap gap-2">
                  {PRESET_PROMPTS.map((p, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setStudentInstruction(p.text);
                        handleParseInstruction(p.text);
                      }}
                      className="px-2.5 py-1 text-[11px] rounded bg-neutral-100 hover:bg-neutral-200 text-ink-primary font-medium transition cursor-pointer border border-neutral-200"
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Parsed Intent Chips */}
              {parsedInstruction && (
                <div className="p-3 rounded bg-blue-50/60 border border-blue-200 flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-bold text-primary flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5" /> Recognized Intent:
                  </span>
                  {parsedInstruction.target_chapter && (
                    <span className="px-2 py-0.5 rounded bg-white font-mono text-[11px] font-bold text-ink-primary border border-border">
                      Chapter: {parsedInstruction.target_chapter}
                    </span>
                  )}
                  <span className="px-2 py-0.5 rounded bg-white font-mono text-[11px] font-bold text-ink-primary border border-border">
                    Time: {parsedInstruction.time_budget_minutes}m
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white font-mono text-[11px] font-bold text-ink-primary border border-border">
                    Level: {parsedInstruction.learner_level}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white font-mono text-[11px] font-bold text-ink-primary border border-border">
                    Language: {parsedInstruction.language.toUpperCase()}
                  </span>
                </div>
              )}
            </div>

            {/* Document Grounding Notice */}
            <div className="p-3.5 rounded bg-emerald-50/50 border border-emerald-200 text-xs text-ink-secondary flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 text-[#0F7B3F] mt-0.5 flex-shrink-0" />
              <div className="text-xs">
                <strong className="text-[#0F7B3F] font-bold">Grounded Pipeline Ready:</strong> All planned segments, Hindi/English explanations, interactive checkpoints, and final quizzes will be generated exclusively from this document's verified content with chunk-level citations.
              </div>
            </div>
          </div>

          {error && (
            <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-xs text-[#C21E1E] font-semibold flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-[#C21E1E] flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex flex-col sm:flex-row justify-end gap-3">
            <button
              onClick={() => {
                setUploadResult(null);
                setFile(null);
                setParsedInstruction(null);
              }}
              disabled={isGeneratingLesson}
              className="px-5 py-2.5 rounded border border-border bg-white text-xs font-semibold text-ink-secondary hover:text-black hover:bg-canvas-elevated cursor-pointer"
            >
              Upload Different File
            </button>

            <button
              onClick={handleProceedToSetup}
              disabled={isGeneratingLesson}
              className="px-5 py-2.5 rounded border border-border bg-white text-xs font-semibold text-ink-primary hover:bg-canvas-elevated cursor-pointer"
            >
              Custom Setup
            </button>

            <button
              onClick={handleGenerateLesson}
              disabled={isGeneratingLesson}
              className="flex items-center justify-center gap-2 px-7 py-2.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-sm shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] cursor-pointer disabled:opacity-50"
            >
              {isGeneratingLesson ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Synthesizing Adaptive Lesson...</span>
                </>
              ) : (
                <>
                  <span>Start AI Teacher Lesson</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

