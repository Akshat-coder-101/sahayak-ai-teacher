import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Explore Curriculum Topics",
  description:
    "Choose from STEM curriculum tracks across Physics, Mathematics, Biology, Chemistry, and Computer Science.",
  openGraph: {
    title: "Explore Topics · Sahayak AI Teacher",
    description: "Choose from STEM curriculum tracks across Physics, Math, Biology, and Computer Science.",
  },
};

export default function TopicLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
