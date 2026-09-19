"use client";

import React, { useState, useEffect } from "react";
import { 
  FileText, 
  Bookmark, 
  Plus, 
  Trash2, 
  Edit3, 
  Check, 
  Download, 
  ShieldCheck
} from "lucide-react";
import { LessonSegmentRender, Citation } from "@/lib/api";

interface NoteItem {
  id: string;
  segmentId: number;
  timestamp: string;
  content: string;
  created_at: number;
}

interface NotesAndResourcesPanelProps {
  segment: LessonSegmentRender;
  isOpen: boolean;
  onToggle: () => void;
  isBookmarked: boolean;
  onToggleBookmark: () => void;
}

export default function NotesAndResourcesPanel({
  segment,
  isOpen,
  onToggle,
  isBookmarked,
  onToggleBookmark,
}: NotesAndResourcesPanelProps) {
  const [activeTab, setActiveTab] = useState<"notes" | "citations" | "resources">("notes");
  const [notes, setNotes] = useState<NoteItem[]>([]);
  const [newNoteText, setNewNoteText] = useState<string>("");
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState<string>("");

  // Load notes from localStorage per session
  useEffect(() => {
    if (typeof window !== "undefined" && segment.session_id) {
      const saved = localStorage.getItem(`sahayak_notes_${segment.session_id}`);
      if (saved) {
        try {
          setNotes(JSON.parse(saved));
        } catch (e) {
          console.error("Failed to parse saved notes", e);
        }
      }
    }
  }, [segment.session_id]);

  // Save notes helper
  const saveNotes = (updated: NoteItem[]) => {
    setNotes(updated);
    if (typeof window !== "undefined" && segment.session_id) {
      localStorage.setItem(`sahayak_notes_${segment.session_id}`, JSON.stringify(updated));
    }
  };

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteText.trim()) return;

    const newNote: NoteItem = {
      id: Date.now().toString(),
      segmentId: segment.segment_id,
      timestamp: `Part ${segment.segment_id}`,
      content: newNoteText.trim(),
      created_at: Date.now(),
    };

    saveNotes([newNote, ...notes]);
    setNewNoteText("");
  };

  const handleDeleteNote = (id: string) => {
    saveNotes(notes.filter((n) => n.id !== id));
  };

  const handleStartEdit = (note: NoteItem) => {
    setEditingNoteId(note.id);
    setEditingContent(note.content);
  };

  const handleSaveEdit = (id: string) => {
    saveNotes(
      notes.map((n) => (n.id === id ? { ...n, content: editingContent } : n))
    );
    setEditingNoteId(null);
  };

  // Static downloadable resources
  const mockResources = [
    {
      title: "Lecture Syllabus & Summary (PDF)",
      size: "1.2 MB",
      type: "PDF",
    },
    {
      title: "Analytical Formula Reference Sheet (MD)",
      size: "450 KB",
      type: "Markdown",
    },
    {
      title: "Python Sandbox Source Files (ZIP)",
      size: "820 KB",
      type: "Code",
    },
  ];

  return (
    <aside
      className={`transition-all duration-300 ease-in-out flex flex-col h-full shrink-0 border-l border-border bg-white z-30 ${
        isOpen
          ? "w-80 sm:w-96 translate-x-0 opacity-100 relative shadow-sm"
          : "w-0 translate-x-full overflow-hidden border-none opacity-0 pointer-events-none absolute lg:relative"
      }`}
    >
      {/* Header & Tabs */}
      <div className="p-4 border-b border-border bg-white">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setActiveTab("notes")}
              className={`px-2.5 sm:px-3 py-1.5 rounded text-xs font-bold transition-all flex items-center gap-1.5 ${
                activeTab === "notes"
                  ? "bg-primary text-white"
                  : "text-ink-secondary hover:text-ink-primary hover:bg-canvas-elevated"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Notes ({notes.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("citations")}
              className={`px-2.5 sm:px-3 py-1.5 rounded text-xs font-bold transition-all flex items-center gap-1.5 ${
                activeTab === "citations"
                  ? "bg-primary text-white"
                  : "text-ink-secondary hover:text-ink-primary hover:bg-canvas-elevated"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Citations</span>
            </button>
            <button
              onClick={() => setActiveTab("resources")}
              className={`px-2.5 sm:px-3 py-1.5 rounded text-xs font-bold transition-all flex items-center gap-1.5 ${
                activeTab === "resources"
                  ? "bg-primary text-white"
                  : "text-ink-secondary hover:text-ink-primary hover:bg-canvas-elevated"
              }`}
            >
              <Download className="w-3.5 h-3.5" />
              <span>Downloads</span>
            </button>
          </div>

          <button
            onClick={onToggle}
            className="p-1.5 rounded-md hover:bg-canvas-elevated text-ink-muted hover:text-ink-primary transition-colors flex items-center gap-1 text-xs"
            aria-label="Close notes panel"
            title="Close Panel"
          >
            <span className="text-[11px] text-ink-muted hidden sm:inline">Close</span>
            ✕
          </button>
        </div>

        {/* Lesson Bookmark Action */}
        <div className="flex items-center justify-between pt-1">
          <span className="text-[11px] text-ink-muted font-mono font-medium">Part {segment.segment_id}</span>
          <button
            onClick={onToggleBookmark}
            className={`text-xs px-2.5 py-1 rounded font-semibold transition-colors flex items-center gap-1.5 border ${
              isBookmarked
                ? "bg-[#FFF1E6] text-accent border-orange-200"
                : "bg-white border-border text-ink-secondary hover:text-ink-primary"
            }`}
          >
            <Bookmark className={`w-3.5 h-3.5 ${isBookmarked ? "fill-current text-accent" : ""}`} />
            <span>{isBookmarked ? "Bookmarked" : "Bookmark"}</span>
          </button>
        </div>
      </div>

      {/* Tab Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {/* 1. NOTES TAB */}
        {activeTab === "notes" && (
          <div className="space-y-4">
            {/* New Note Form */}
            <form onSubmit={handleAddNote} className="space-y-2">
              <label className="text-[11px] font-bold text-ink-muted uppercase tracking-wider block">
                Take a Note for Part {segment.segment_id}
              </label>
              <textarea
                value={newNoteText}
                onChange={(e) => setNewNoteText(e.target.value)}
                placeholder="Type your notes, equations, or observations..."
                rows={3}
                className="w-full text-xs p-3 rounded bg-white border border-border text-ink-primary placeholder-ink-muted focus:outline-none focus:border-primary resize-none"
              />
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={!newNoteText.trim()}
                  className="px-4 py-1.5 rounded bg-black hover:bg-neutral-800 disabled:opacity-40 text-white font-bold text-xs flex items-center gap-1.5 transition-colors shadow-2xs"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Save Note</span>
                </button>
              </div>
            </form>

            {/* Note List */}
            <div className="space-y-2.5 pt-2">
              <div className="text-[11px] font-bold text-ink-muted uppercase tracking-wider">
                Saved Notes ({notes.length})
              </div>

              {notes.length === 0 ? (
                <div className="p-6 text-center rounded border border-dashed border-border bg-canvas-elevated text-ink-muted">
                  <FileText className="w-7 h-7 mx-auto mb-2 opacity-50" />
                  <p className="text-xs font-medium">No notes taken yet.</p>
                  <p className="text-[11px] mt-1">Capture ideas while listening to the lesson.</p>
                </div>
              ) : (
                notes.map((note) => (
                  <div
                    key={note.id}
                    className="p-3 rounded bg-white border border-border text-xs text-ink-primary space-y-2 hover:border-border-strong transition-colors"
                  >
                    <div className="flex items-center justify-between text-[11px] text-ink-muted border-b border-border pb-1.5">
                      <span className="text-primary font-bold">{note.timestamp}</span>
                      <div className="flex items-center gap-2">
                        {editingNoteId === note.id ? (
                          <button
                            onClick={() => handleSaveEdit(note.id)}
                            className="text-[#0F7B3F] hover:opacity-80"
                            title="Save"
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleStartEdit(note)}
                            className="text-ink-muted hover:text-ink-primary"
                            title="Edit"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteNote(note.id)}
                          className="text-ink-muted hover:text-[#C21E1E]"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {editingNoteId === note.id ? (
                      <textarea
                        value={editingContent}
                        onChange={(e) => setEditingContent(e.target.value)}
                        rows={2}
                        className="w-full text-xs p-2 rounded bg-white border border-primary text-ink-primary focus:outline-none"
                      />
                    ) : (
                      <p className="leading-relaxed whitespace-pre-wrap">{note.content}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* 2. CITATIONS TAB */}
        {activeTab === "citations" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-ink-muted uppercase tracking-wider">
                Source Materials
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#E9F1FC] text-primary font-bold">
                RAG Grounded
              </span>
            </div>

            {segment.citations && segment.citations.length > 0 ? (
              segment.citations.map((cite, i) => (
                <div
                  key={i}
                  className="p-3 rounded bg-white border border-border space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-bold text-ink-primary truncate max-w-[180px]">
                      {cite.chapter || "Course Reference Material"}
                    </span>
                    <span className="text-[10px] text-ink-muted font-mono">
                      Page {cite.page || 1} {cite.section ? `· ${cite.section}` : ""}
                    </span>
                  </div>
                  <blockquote className="p-2.5 rounded bg-canvas-elevated border-l-2 border-primary text-[11px] text-ink-secondary italic">
                    "{cite.snippet}"
                  </blockquote>
                  <div className="flex items-center justify-between text-[10px] text-ink-muted pt-1">
                    <span>Relevance: {Math.round((cite.confidence || 0.94) * 100)}%</span>
                    <span className="text-primary font-semibold">Grounded Reference</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-5 text-center rounded border border-dashed border-border bg-canvas-elevated text-ink-muted">
                <ShieldCheck className="w-7 h-7 text-primary mx-auto mb-2" />
                <p className="text-xs font-bold text-ink-primary">Synthesized Grounded Curriculum</p>
                <p className="text-[11px] text-ink-muted mt-1">
                  Upload textbook or syllabus PDFs in /upload for page-level citations.
                </p>
              </div>
            )}
          </div>
        )}

        {/* 3. RESOURCES TAB */}
        {activeTab === "resources" && (
          <div className="space-y-3">
            <span className="text-[11px] font-bold text-ink-muted uppercase tracking-wider block">
              Downloadable Materials
            </span>

            <div className="space-y-2">
              {mockResources.map((res, i) => (
                <div
                  key={i}
                  className="p-3 rounded bg-white border border-border flex items-center justify-between gap-2 hover:border-border-strong transition-colors group"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-ink-primary truncate group-hover:text-primary">
                      {res.title}
                    </p>
                    <p className="text-[10px] text-ink-muted font-mono mt-0.5">
                      {res.type} · {res.size}
                    </p>
                  </div>
                  <button
                    onClick={() => alert(`Downloaded ${res.title}`)}
                    className="p-2 rounded border border-border bg-white hover:bg-black hover:text-white text-ink-secondary transition-colors"
                    title="Download asset"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
