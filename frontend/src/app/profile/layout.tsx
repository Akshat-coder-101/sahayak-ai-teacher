import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Learner Profile & Calibration",
  description:
    "View your learning history, calibrated mastery domains, and cognitive strengths.",
  openGraph: {
    title: "Learner Profile · Sahayak AI Teacher",
    description: "View your learning history, calibrated mastery domains, and cognitive strengths.",
  },
};

export default function ProfileLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
