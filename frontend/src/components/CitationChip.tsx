"use client";

import { Citation } from "@/lib/api";
import { ShieldCheck, FileText, ChevronDown, ChevronUp, Copy, Check } from "lucide-react";
import { useState } from "react";

interface CitationChipProps {
  citations?: Citation[];
}

export default function CitationChip({ citations }: CitationChipProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  if (!citations || citations.length === 0) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-ink-muted py-1 font-mono">
        <ShieldCheck className="w-3.5 h-3.5 text-primary" />
        <span>Grounded learning material</span>
      </div>
    );
  }

  const primary = citations[0];

  const handleCopyQuote = (quote: string, index: number) => {
    navigator.clipboard.writeText(quote);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="space-y-1.5 w-full max-w-xl">
      {/* Coursera-style pill-shaped chip: #E9F1FC background, #0056D2 text, 12px */}
      <button 
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#E9F1FC] text-primary text-xs font-semibold cursor-pointer hover:bg-blue-100 transition-colors select-none text-left"
      >
        <ShieldCheck className="w-3.5 h-3.5 text-primary flex-shrink-0" />
        <span>
          Source: {primary.chapter || "Document Material"} (Page {primary.page || 1})
        </span>
        {citations.length > 1 && (
          <span className="text-[10px] px-1.5 py-0.2 bg-blue-200/60 rounded-full font-bold">
            +{citations.length - 1} more
          </span>
        )}
        {isExpanded ? (
          <ChevronUp className="w-3 h-3 text-primary flex-shrink-0 ml-0.5" />
        ) : (
          <ChevronDown className="w-3 h-3 text-primary flex-shrink-0 ml-0.5" />
        )}
      </button>

      {/* Expanded Citations Accordion */}
      {isExpanded && (
        <div className="p-3.5 rounded-lg bg-white border border-border space-y-3 shadow-xs animate-in fade-in slide-in-from-top-1 duration-150">
          <div className="flex items-center justify-between text-xs font-bold text-primary pb-1.5 border-b border-border">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-primary" />
              Verified Document Excerpts & Citations
            </span>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-[#0F7B3F] border border-emerald-200">
              Zero-Hallucination
            </span>
          </div>

          <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
            {citations.map((cite, index) => {
              const quoteText = cite.quote || cite.snippet || "Document reference";
              const isCopied = copiedIndex === index;

              return (
                <div key={index} className="text-xs space-y-1.5 bg-canvas-elevated p-3 rounded-md border border-border hover:border-primary/40 transition-colors">
                  <div className="flex items-center justify-between text-xs font-medium text-ink-primary">
                    <span className="flex items-center gap-1.5 font-bold text-primary truncate max-w-[240px]">
                      <FileText className="w-3.5 h-3.5 flex-shrink-0" />
                      {cite.chapter || "Document Reference"}
                    </span>
                    <div className="flex items-center gap-2 text-ink-muted text-[11px] font-mono">
                      <span>Page {cite.page || 1}</span>
                      {cite.chunk_id && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-base-200 text-ink-muted font-mono" title={`Chunk ID: ${cite.chunk_id}`}>
                          {cite.chunk_id.slice(0, 8)}...
                        </span>
                      )}
                    </div>
                  </div>

                  <blockquote className="text-xs text-ink-secondary italic border-l-2 border-primary pl-2.5 my-1.5 leading-relaxed bg-white/70 py-1 pr-1.5 rounded-r">
                    "{quoteText}"
                  </blockquote>

                  <div className="flex justify-end pt-1">
                    <button
                      type="button"
                      onClick={() => handleCopyQuote(quoteText, index)}
                      className="text-[10px] text-ink-muted hover:text-primary flex items-center gap-1 font-mono transition-colors cursor-pointer"
                    >
                      {isCopied ? (
                        <>
                          <Check className="w-3 h-3 text-success" />
                          <span>Copied quote</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy quote</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
