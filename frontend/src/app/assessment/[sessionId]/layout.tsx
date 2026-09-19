import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pedagogical Assessment & Diagnostic Quiz",
  description:
    "Evaluate concept mastery through adaptive multi-tier quizzes with instant feedback and misconception detection.",
  openGraph: {
    title: "Pedagogical Assessment · Sahayak AI Teacher",
    description: "Evaluate concept mastery through adaptive quizzes with instant feedback.",
  },
};

export default function AssessmentLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
