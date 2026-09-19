import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Analytics Dashboard",
  description:
    "Track mastery trajectories, completed curriculum sessions, and misconception resolutions in real-time.",
  openGraph: {
    title: "Analytics Dashboard · Sahayak AI Teacher",
    description: "Track mastery trajectories, completed curriculum sessions, and misconception resolutions.",
  },
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
