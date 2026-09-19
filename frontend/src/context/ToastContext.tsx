"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from "lucide-react";
import { usePrefersReducedMotion } from "@/components/ui/use-reduced-motion";

export type ToastType = "success" | "error" | "info" | "warning";

export interface ToastMessage {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType, duration?: number) => void;
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  showInfo: (message: string) => void;
  showWarning: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const prefersReducedMotion = usePrefersReducedMotion();

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = "info", duration = 4000) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: ToastMessage = { id, message, type, duration };

      setToasts((prev) => [...prev.slice(-3), newToast]); // keep max 4 toasts

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const showSuccess = useCallback((msg: string) => showToast(msg, "success"), [showToast]);
  const showError = useCallback((msg: string) => showToast(msg, "error"), [showToast]);
  const showInfo = useCallback((msg: string) => showToast(msg, "info"), [showToast]);
  const showWarning = useCallback((msg: string) => showToast(msg, "warning"), [showToast]);

  const getToastIcon = (type: ToastType) => {
    switch (type) {
      case "success":
        return <CheckCircle2 className="w-4 h-4 text-[#0F7B3F] shrink-0" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-[#C21E1E] shrink-0" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-accent shrink-0" />;
      case "info":
      default:
        return <Info className="w-4 h-4 text-primary shrink-0" />;
    }
  };

  const getToastStyle = (type: ToastType) => {
    switch (type) {
      case "success":
        return "bg-white border-emerald-300 text-ink-primary shadow-lg ring-1 ring-emerald-500/20";
      case "error":
        return "bg-white border-rose-300 text-ink-primary shadow-lg ring-1 ring-rose-500/20";
      case "warning":
        return "bg-white border-orange-300 text-ink-primary shadow-lg ring-1 ring-orange-500/20";
      case "info":
      default:
        return "bg-white border-blue-300 text-ink-primary shadow-lg ring-1 ring-blue-500/20";
    }
  };

  return (
    <ToastContext.Provider value={{ showToast, showSuccess, showError, showInfo, showWarning }}>
      {children}

      {/* Floating Toast Notification Container */}
      <div
        className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none max-w-sm w-full px-4 sm:px-0"
        aria-live="polite"
      >
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={prefersReducedMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 20, scale: 0.95 }}
              animate={prefersReducedMotion ? { opacity: 1, y: 0 } : { opacity: 1, y: 0, scale: 1 }}
              exit={prefersReducedMotion ? { opacity: 0 } : { opacity: 0, y: 10, scale: 0.9 }}
              transition={{ duration: 0.2 }}
              className={`pointer-events-auto p-3.5 rounded-xl border flex items-center justify-between gap-3 ${getToastStyle(
                toast.type
              )}`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                {getToastIcon(toast.type)}
                <p className="text-xs font-semibold leading-snug break-words">
                  {toast.message}
                </p>
              </div>

              <button
                type="button"
                onClick={() => removeToast(toast.id)}
                className="text-ink-muted hover:text-black p-1 rounded transition-colors shrink-0"
                aria-label="Dismiss notification"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    // Fallback safe dummy if used outside provider
    return {
      showToast: (m: string) => console.log(m),
      showSuccess: (m: string) => console.log(m),
      showError: (m: string) => console.error(m),
      showInfo: (m: string) => console.log(m),
      showWarning: (m: string) => console.warn(m),
    };
  }
  return context;
}
