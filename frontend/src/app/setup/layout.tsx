import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Configure Learning Session",
  description:
    "Customize learner level, depth, time budget, language, and pedagogical goals for your AI classroom.",
  openGraph: {
    title: "Configure Session · Sahayak AI Teacher",
    description: "Customize learner level, depth, time budget, and pedagogical goals.",
  },
};

export default function SetupLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
