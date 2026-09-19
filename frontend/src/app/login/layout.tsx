import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Learner Account Selection",
  description:
    "Sign in or select preset learner profiles with pre-calibrated learning histories and goals.",
  openGraph: {
    title: "Learner Selection · Sahayak AI Teacher",
    description: "Sign in or select preset learner profiles with pre-calibrated learning histories.",
  },
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
