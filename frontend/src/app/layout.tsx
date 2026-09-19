import type { Metadata, Viewport } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { AuthProvider } from "@/context/AuthContext";
import { ToastProvider } from "@/context/ToastContext";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#0056D2",
};

export const metadata: Metadata = {
  title: {
    default: "Sahayak AI Teacher",
    template: "%s · Sahayak AI Teacher",
  },
  description:
    "Human-like adaptive AI educator delivering multimodal STEM lessons with real-time misconception diagnosis, interactive visual canvas, and speech synthesis.",
  keywords: [
    "AI Teacher",
    "Adaptive Learning",
    "STEM Education",
    "Interactive Classroom",
    "Misconception Diagnosis",
    "Multimodal AI",
  ],
  authors: [{ name: "Sahayak AI Team" }],
  openGraph: {
    title: "Sahayak AI Teacher · Human-Like Adaptive AI Educator",
    description:
      "A state-machine powered AI educator delivering personalized lessons with interactive avatar video, synced visuals, and adaptive misconception reteaching.",
    type: "website",
    locale: "en_US",
    siteName: "Sahayak AI Teacher",
  },
  twitter: {
    card: "summary_large_image",
    title: "Sahayak AI Teacher · Adaptive AI Educator",
    description:
      "Multimodal adaptive AI teacher delivering personalized STEM lessons and interactive demonstrator blackboards.",
  },
  icons: {
    icon: "/icon.svg",
    apple: "/apple-icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="courseraLight">
      <body className="min-h-screen flex flex-col bg-white text-ink-primary antialiased selection:bg-primary-soft selection:text-primary overflow-x-hidden">
        <AuthProvider>
          <ToastProvider>
            <Navbar />
            <main className="flex-1 w-full flex flex-col overflow-x-hidden">
              {children}
            </main>
            <Footer />
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
