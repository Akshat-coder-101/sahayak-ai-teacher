"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useAuth, PRESET_USERS, UserSession } from "@/context/AuthContext";
import { 
  Sparkles, 
  ArrowRight, 
  CheckCircle2, 
  Lock, 
  Mail, 
  User, 
  GraduationCap, 
  ShieldCheck 
} from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const { user, login, register, switchUser } = useAuth();
  
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [level, setLevel] = useState<"beginner" | "intermediate" | "advanced">("intermediate");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setErrorMsg(null);
    setIsSubmitting(true);
    try {
      if (isSignUp) {
        await register(email, password || "password123", name || undefined, "student", level);
      } else {
        await login(email, password || "password123", name || undefined, level);
      }
      router.push("/dashboard");
    } catch (err: any) {
      setErrorMsg(err.message || "Authentication failed. Please check your credentials.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectPreset = async (preset: UserSession) => {
    await switchUser(preset);
    router.push("/dashboard");
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="text-center max-w-lg mx-auto">
        <span className="text-xs font-bold uppercase tracking-wider text-primary">
          Sahayak Authentication
        </span>
        <h1 className="text-3xl font-extrabold text-black mt-1">
          {isSignUp ? "Create Learner Account" : "Welcome to Sahayak"}
        </h1>
        <p className="text-xs text-ink-muted mt-1 font-medium">
          Access personalized adaptive curricula, synchronized AI lessons, and persistent mastery analytics.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
        {/* Form Container (7 cols) */}
        <div className="md:col-span-7 bg-white rounded-lg p-6 sm:p-8 border border-border shadow-2xs space-y-6">
          {/* Tabs */}
          <div className="flex border-b border-border pb-3">
            <button
              type="button"
              onClick={() => setIsSignUp(false)}
              className={`flex-1 text-center py-2 text-sm font-bold transition-colors ${
                !isSignUp
                  ? "text-primary border-b-2 border-primary -mb-3.5"
                  : "text-ink-muted hover:text-black"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setIsSignUp(true)}
              className={`flex-1 text-center py-2 text-sm font-bold transition-colors ${
                isSignUp
                  ? "text-primary border-b-2 border-primary -mb-3.5"
                  : "text-ink-muted hover:text-black"
              }`}
            >
              New Registration
            </button>
          </div>

          {errorMsg && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded font-medium">
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <div>
                <label className="text-xs font-bold text-black uppercase tracking-wider block mb-1.5">
                  Full Name
                </label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Pranjal Mishra"
                    className="w-full text-xs pl-9 pr-3 py-2.5 rounded bg-white border border-border text-black placeholder-ink-muted focus:outline-none focus:border-primary font-medium"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-xs font-bold text-black uppercase tracking-wider block mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="student@university.edu"
                  className="w-full text-xs pl-9 pr-3 py-2.5 rounded bg-white border border-border text-black placeholder-ink-muted focus:outline-none focus:border-primary font-medium"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-black uppercase tracking-wider block mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full text-xs pl-9 pr-3 py-2.5 rounded bg-white border border-border text-black placeholder-ink-muted focus:outline-none focus:border-primary font-medium"
                />
              </div>
            </div>

            {isSignUp && (
              <div>
                <label className="text-xs font-bold text-black uppercase tracking-wider block mb-1.5">
                  Initial Cognitive Baseline
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(["beginner", "intermediate", "advanced"] as const).map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => setLevel(lvl)}
                      className={`p-2 rounded border text-xs font-bold capitalize transition-colors ${
                        level === lvl
                          ? "bg-[#E9F1FC] border-primary text-primary"
                          : "bg-white border-border text-ink-secondary hover:bg-canvas-elevated"
                      }`}
                    >
                      {lvl}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <button
              type="submit"
              className="w-full py-3 rounded bg-black hover:bg-neutral-800 text-white font-bold text-xs shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-2 mt-4"
            >
              <span>{isSignUp ? "Create Free Account" : "Sign In to Dashboard"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="pt-2 text-center text-xs text-ink-muted">
            <ShieldCheck className="w-4 h-4 inline-block text-primary mr-1" />
            <span>Encrypted local session with privacy-first storage</span>
          </div>
        </div>

        {/* Instant One-Click Demo Personas (5 cols) */}
        <div className="md:col-span-5 bg-white rounded-lg p-6 border border-border shadow-2xs space-y-4">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-accent font-mono">
              Instant Demo Evaluator
            </span>
            <h3 className="font-bold text-sm text-black mt-0.5">
              1-Click Persona Switcher
            </h3>
            <p className="text-xs text-ink-muted mt-1">
              Select any pre-configured learner profile to test adaptation and personalized DAGs instantly.
            </p>
          </div>

          <div className="space-y-2.5">
            {PRESET_USERS.map((preset) => {
              const isCurrent = user?.id === preset.id;
              return (
                <div
                  key={preset.id}
                  onClick={() => handleSelectPreset(preset)}
                  className={`p-3 rounded border cursor-pointer transition-all flex items-center gap-3 ${
                    isCurrent
                      ? "bg-[#E9F1FC] border-primary shadow-2xs"
                      : "bg-white border-border hover:border-primary/50 hover:bg-canvas-elevated"
                  }`}
                >
                  <div className="relative w-10 h-10 rounded-full overflow-hidden border border-border shrink-0">
                    <Image
                      src={preset.avatar}
                      alt={preset.name}
                      width={40}
                      height={40}
                      className="w-full h-full object-cover"
                      unoptimized
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-black truncate">{preset.name}</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-canvas-elevated text-primary font-bold capitalize border border-border">
                        {preset.level}
                      </span>
                    </div>
                    <p className="text-[11px] text-ink-muted truncate">{preset.role}</p>
                  </div>
                  {isCurrent && (
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0" />
                  )}
                </div>
              );
            })}
          </div>

          <div className="pt-2 text-[11px] text-ink-muted">
            Each persona has independent curriculum node states, misconception logs, and course histories.
          </div>
        </div>
      </div>
    </div>
  );
}
