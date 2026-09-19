import Link from "next/link";
import { GraduationCap, ShieldCheck, Mail, Phone } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-canvas-surface py-10 mt-auto text-ink-secondary text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-6 border-b border-border/60">
          {/* Brand & Mission */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/25 text-primary flex items-center justify-center shrink-0">
              <GraduationCap className="w-5 h-5 text-primary" />
            </div>
            <div>
              <span className="font-heading text-sm font-bold text-ink-primary block">
                Sahayak AI Teacher
              </span>
              <p className="text-[11px] text-ink-muted">
                AI Innovation Hackathon 2026 · Adaptive Multimodal AI Educator
              </p>
            </div>
          </div>

          {/* Quick Navigation Links */}
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-semibold">
            <Link href="/topic" className="hover:text-primary transition-colors py-1">
              Explore Topics
            </Link>
            <Link href="/upload" className="hover:text-primary transition-colors py-1">
              RAG Ingestion
            </Link>
            <Link href="/learning-path" className="hover:text-primary transition-colors py-1">
              Curriculum DAGs
            </Link>
            <Link href="/dashboard" className="hover:text-primary transition-colors py-1">
              Analytics Dashboard
            </Link>
          </div>
        </div>

        {/* Contact & Compliance Strip */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-[11px]">
          <div className="flex flex-wrap items-center gap-4 text-ink-secondary">
            <a
              href="mailto:support@sahayak.ai"
              className="flex items-center gap-1.5 hover:text-primary transition-colors py-1 font-medium"
            >
              <Mail className="w-3.5 h-3.5 text-primary" />
              <span>support@sahayak.ai</span>
            </a>
            <span className="hidden sm:inline text-border">•</span>
            <a
              href="tel:+18005550199"
              className="flex items-center gap-1.5 hover:text-primary transition-colors py-1 font-medium"
            >
              <Phone className="w-3.5 h-3.5 text-primary" />
              <span>+1 (800) 555-0199</span>
            </a>
            <span className="hidden sm:inline text-border">•</span>
            <span className="flex items-center gap-1 text-primary font-mono font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" />
              Zero-Hallucination Grounded RAG
            </span>
          </div>

          <div className="text-ink-muted font-mono">
            © 2026 Sahayak AI. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
}
