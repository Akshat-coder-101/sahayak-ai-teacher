import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Curriculum DAG & Learning Path",
  description:
    "Explore directed acyclic graph curriculum prerequisites, module milestones, and mastery checkpoints.",
  openGraph: {
    title: "Curriculum Learning Path · Sahayak AI Teacher",
    description: "Explore directed acyclic graph curriculum prerequisites and module milestones.",
  },
};

export default function LearningPathLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
