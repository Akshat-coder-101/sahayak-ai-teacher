import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Upload Course Material (RAG Ingestion)",
  description:
    "Ingest textbooks, lecture notes, and syllabus PDFs for zero-hallucination grounded curriculum lessons.",
  openGraph: {
    title: "Upload Course Material · Sahayak AI Teacher",
    description: "Ingest textbooks and lecture notes for zero-hallucination grounded curriculum lessons.",
  },
};

export default function UploadLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
