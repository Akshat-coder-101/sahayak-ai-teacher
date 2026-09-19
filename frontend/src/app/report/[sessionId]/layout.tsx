import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Learning Report & Diagnostics",
  description:
    "Comprehensive breakdown of concepts understood, weak areas identified, and recommended revision tracks.",
  openGraph: {
    title: "Learning Report · Sahayak AI Teacher",
    description: "Breakdown of concepts understood, weak areas, and recommended revision tracks.",
  },
};

export default function ReportLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
