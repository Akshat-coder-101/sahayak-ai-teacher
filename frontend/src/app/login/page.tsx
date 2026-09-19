"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useAuth, PRESET_USERS, UserSession } from "@/context/AuthContext";
import { 
  Sparkles, 
  ArrowRight, 
  CheckCircle2, 
  XCircle,
  Lock, 
  Mail, 
  User, 
  GraduationCap, 
  ShieldCheck,
  Eye,
  EyeOff,
  KeyRound,
  Check
} from "lucide-react";
import Link from "next/link";

interface PasswordCriteria {
  length: boolean;
  hasUpper: boolean;
  hasLower: boolean;
  hasNumber: boolean;
  hasSpecial: boolean;
}

const checkPasswordCriteria = (pwd: string): PasswordCriteria => {
  return {
    length: pwd.length >= 8,
    hasUpper: /[A-Z]/.test(pwd),
    hasLower: /[a-z]/.test(pwd),
    hasNumber: /\d/.test(pwd),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>\-_+=[\]\\\/~`]/.test(pwd),
  };
};

const generateStrongPassword = (): string => {
  const uppers = "ABCDEFGHJKLMNPQRSTUVWXYZ";
  const lowers = "abcdefghijkmnpqrstuvwxyz";
  const digits = "23456789";
  const specials = "!@#$%&*";
  
  let pwd = "";
  pwd += uppers[Math.floor(Math.random() * uppers.length)];
  pwd += lowers[Math.floor(Math.random() * lowers.length)];
  pwd += digits[Math.floor(Math.random() * digits.length)];
  pwd += specials[Math.floor(Math.random() * specials.length)];
  
  const allChars = uppers + lowers + digits + specials;
  for (let i = 0; i < 8; i++) {
    pwd += allChars[Math.floor(Math.random() * allChars.length)];
  }
  return pwd.split("").sort(() => 0.5 - Math.random()).join("");
};

export default function LoginPage() {
  const router = useRouter();
  const { user, login, register, switchUser } = useAuth();
  
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [level, setLevel] = useState<"beginner" | "intermediate" | "advanced">("intermediate");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copiedNotification, setCopiedNotification] = useState(false);

  // If already logged in, route to learning portal
  useEffect(() => {
    if (user) {
      router.push("/");
    }
  }, [user, router]);

  const criteria = checkPasswordCriteria(password);
  const passedCriteriaCount = Object.values(criteria).filter(Boolean).length;
  const isPasswordValid = passedCriteriaCount === 5;

  const handleGeneratePassword = () => {
    const strong = generateStrongPassword();
    setPassword(strong);
    setShowPassword(true);
    setCopiedNotification(true);
    setTimeout(() => setCopiedNotification(false), 2500);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMsg("Please enter both email and password.");
      return;
    }

    if (isSignUp && !isPasswordValid) {
      setErrorMsg("Password does not meet the strong format requirements. Please follow the checklist below.");
      return;
    }

    setErrorMsg(null);
    setIsSubmitting(true);
    try {
      if (isSignUp) {
        await register(email, password, name || undefined, "student", level);
      } else {
        await login(email, password, name || undefined, level);
      }
      router.push("/");
    } catch (err: any) {
      const msg = err.message || err.detail || "Authentication failed. Please check your credentials.";
      setErrorMsg(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectPreset = async (preset: UserSession) => {
    await switchUser(preset);
    router.push("/");
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12 pt-4">
      {/* Header */}
      <div className="text-center max-w-lg mx-auto">
        <h1 className="text-3xl font-extrabold text-black tracking-tight">
          {isSignUp ? "Create Your Account" : "Sign In to Sahayak"}
        </h1>
        <p className="text-sm text-ink-muted mt-2 font-medium leading-relaxed">
          {isSignUp 
            ? "Create your account to access personalized AI lessons, notes, and adaptive learning."
            : "Welcome back! Enter your email and password to continue your personalized lessons."}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
        {/* Form Container (7 cols) */}
        <div className="md:col-span-7 bg-white rounded-lg p-6 sm:p-8 border border-border shadow-2xs space-y-6">
          {/* Tabs */}
          <div className="flex border-b border-border pb-3">
            <button
              type="button"
              onClick={() => {
                setIsSignUp(false);
                setErrorMsg(null);
              }}
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
              onClick={() => {
                setIsSignUp(true);
                setErrorMsg(null);
              }}
              className={`flex-1 text-center py-2 text-sm font-bold transition-colors ${
                isSignUp
                  ? "text-primary border-b-2 border-primary -mb-3.5"
                  : "text-ink-muted hover:text-black"
              }`}
            >
              Sign Up
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
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-bold text-black uppercase tracking-wider block">
                  Password
                </label>
                {isSignUp && (
                  <button
                    type="button"
                    onClick={handleGeneratePassword}
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:text-primary-dark transition-colors"
                  >
                    <KeyRound className="w-3 h-3 text-primary" />
                    <span>Generate Strong Password</span>
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full text-xs pl-9 pr-10 py-2.5 rounded bg-white border border-border text-black placeholder-ink-muted focus:outline-none focus:border-primary font-medium"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-black transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {copiedNotification && (
                <p className="text-[11px] text-emerald-600 font-bold mt-1 flex items-center gap-1">
                  <Check className="w-3 h-3" />
                  <span>Generated compliant strong password!</span>
                </p>
              )}

              {/* Live Password Strength & Criteria (Registration Mode) */}
              {isSignUp && (
                <div className="mt-3 p-3 rounded-lg bg-canvas-elevated border border-border space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-ink-secondary">Password Strength:</span>
                    <span className={`font-bold ${
                      passedCriteriaCount === 5 ? "text-emerald-600" :
                      passedCriteriaCount >= 3 ? "text-amber-600" : "text-rose-600"
                    }`}>
                      {passedCriteriaCount === 5 ? "Strong & Secure ✓" :
                       passedCriteriaCount >= 3 ? "Medium" : "Weak"}
                    </span>
                  </div>

                  {/* Strength Bar */}
                  <div className="w-full bg-border h-1.5 rounded-full overflow-hidden flex gap-1">
                    {[1, 2, 3, 4, 5].map((step) => (
                      <div
                        key={step}
                        className={`h-full flex-1 transition-all ${
                          passedCriteriaCount >= step
                            ? passedCriteriaCount === 5
                              ? "bg-emerald-500"
                              : passedCriteriaCount >= 3
                              ? "bg-amber-500"
                              : "bg-rose-500"
                            : "bg-neutral-200"
                        }`}
                      />
                    ))}
                  </div>

                  {/* Criteria Checklist */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-[11px] pt-1">
                    <div className={`flex items-center gap-1.5 ${criteria.length ? "text-emerald-600 font-bold" : "text-ink-muted"}`}>
                      {criteria.length ? <CheckCircle2 className="w-3 h-3 shrink-0" /> : <XCircle className="w-3 h-3 shrink-0 text-neutral-400" />}
                      <span>8+ characters</span>
                    </div>
                    <div className={`flex items-center gap-1.5 ${criteria.hasUpper ? "text-emerald-600 font-bold" : "text-ink-muted"}`}>
                      {criteria.hasUpper ? <CheckCircle2 className="w-3 h-3 shrink-0" /> : <XCircle className="w-3 h-3 shrink-0 text-neutral-400" />}
                      <span>One uppercase (A-Z)</span>
                    </div>
                    <div className={`flex items-center gap-1.5 ${criteria.hasLower ? "text-emerald-600 font-bold" : "text-ink-muted"}`}>
                      {criteria.hasLower ? <CheckCircle2 className="w-3 h-3 shrink-0" /> : <XCircle className="w-3 h-3 shrink-0 text-neutral-400" />}
                      <span>One lowercase (a-z)</span>
                    </div>
                    <div className={`flex items-center gap-1.5 ${criteria.hasNumber ? "text-emerald-600 font-bold" : "text-ink-muted"}`}>
                      {criteria.hasNumber ? <CheckCircle2 className="w-3 h-3 shrink-0" /> : <XCircle className="w-3 h-3 shrink-0 text-neutral-400" />}
                      <span>One number (0-9)</span>
                    </div>
                    <div className={`flex items-center gap-1.5 ${criteria.hasSpecial ? "text-emerald-600 font-bold" : "text-ink-muted"} sm:col-span-2`}>
                      {criteria.hasSpecial ? <CheckCircle2 className="w-3 h-3 shrink-0" /> : <XCircle className="w-3 h-3 shrink-0 text-neutral-400" />}
                      <span>One special symbol (!@#$%^&*...)</span>
                    </div>
                  </div>
                </div>
              )}
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
              disabled={isSubmitting || (isSignUp && !isPasswordValid)}
              className={`w-full py-3 rounded text-white font-bold text-xs shadow-md transition-all flex items-center justify-center gap-2 mt-4 ${
                isSignUp && !isPasswordValid
                  ? "bg-neutral-400 cursor-not-allowed"
                  : "bg-black hover:bg-neutral-800 hover:scale-[1.01] active:scale-[0.99]"
              }`}
            >
              <span>
                {isSubmitting 
                  ? "Please wait..." 
                  : isSignUp 
                  ? "Create Account" 
                  : "Sign In"}
              </span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="pt-2 text-center text-xs text-ink-muted">
            <ShieldCheck className="w-4 h-4 inline-block text-primary mr-1" />
            <span>Secure encrypted session with privacy-first storage</span>
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
              Select any pre-configured learner profile to test adaptation and personalized DAGs instantly with pre-seeded credentials.
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
                    <p className="text-[11px] text-ink-muted truncate">{preset.email}</p>
                  </div>
                  {isCurrent && (
                    <CheckCircle2 className="w-4 h-4 text-primary shrink-0" />
                  )}
                </div>
              );
            })}
          </div>

          <div className="pt-2 text-[11px] text-ink-muted">
            Each persona has independent curriculum node states, misconception logs, and course histories in Supabase PostgreSQL.
          </div>
        </div>
      </div>
    </div>
  );
}
