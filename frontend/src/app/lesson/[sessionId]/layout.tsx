import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Adaptive Classroom Lesson",
  description:
    "Interactive AI teacher delivering paced concept explanations, synced demonstrator visual canvas, and adaptive reteaching.",
  openGraph: {
    title: "Adaptive Classroom Lesson · Sahayak AI Teacher",
    description: "Interactive AI teacher delivering paced concept explanations and synced demonstrator canvas.",
  },
};

export default function LessonLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
