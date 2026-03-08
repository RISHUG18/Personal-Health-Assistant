/* Week 6 – Global Toast Notification System */
"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { X, CheckCircle, AlertTriangle, Info, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

// ── Types ─────────────────────────────────────
export type ToastVariant = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number; // ms, default 4000
}

interface ToastContextValue {
  toasts: Toast[];
  toast: (t: Omit<Toast, "id">) => void;
  dismiss: (id: string) => void;
}

// ── Context ───────────────────────────────────
const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  // Return no-ops during SSR prerender (provider not yet mounted)
  if (!ctx) return { toasts: [], toast: () => {}, dismiss: () => {} } as ToastContextValue;
  return ctx;
}

// ── Provider ──────────────────────────────────
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback((t: Omit<Toast, "id">) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts((prev) => [...prev.slice(-4), { ...t, id }]); // max 5 toasts
    const duration = t.duration ?? 4000;
    if (duration > 0) {
      setTimeout(() => dismiss(id), duration);
    }
  }, [dismiss]);

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
      <ToastContainer toasts={toasts} dismiss={dismiss} />
    </ToastContext.Provider>
  );
}

// ── Container ─────────────────────────────────
function ToastContainer({ toasts, dismiss }: { toasts: Toast[]; dismiss: (id: string) => void }) {
  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-24 md:bottom-6 right-4 z-[9999] flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} dismiss={dismiss} />
      ))}
    </div>
  );
}

// ── Individual Toast ──────────────────────────
const ICON: Record<ToastVariant, React.ReactNode> = {
  success: <CheckCircle size={15} className="text-emerald-400 flex-shrink-0" />,
  error:   <XCircle    size={15} className="text-red-400 flex-shrink-0" />,
  warning: <AlertTriangle size={15} className="text-amber-400 flex-shrink-0" />,
  info:    <Info       size={15} className="text-blue-400 flex-shrink-0" />,
};

const BORDER: Record<ToastVariant, string> = {
  success: "border-emerald-700/50",
  error:   "border-red-700/50",
  warning: "border-amber-700/50",
  info:    "border-blue-700/50",
};

function ToastItem({ toast, dismiss }: { toast: Toast; dismiss: (id: string) => void }) {
  const variant = toast.variant ?? "info";
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // tiny delay so the enter animation fires
    const t = setTimeout(() => setVisible(true), 10);
    return () => clearTimeout(t);
  }, []);

  return (
    <div
      className={cn(
        "flex items-start gap-3 bg-slate-800 border rounded-xl px-4 py-3 shadow-xl",
        "transition-all duration-300",
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
        BORDER[variant]
      )}
    >
      {ICON[variant]}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white">{toast.title}</p>
        {toast.description && (
          <p className="text-xs text-slate-400 mt-0.5">{toast.description}</p>
        )}
      </div>
      <button
        onClick={() => dismiss(toast.id)}
        className="text-slate-500 hover:text-slate-200 transition-colors flex-shrink-0"
      >
        <X size={13} />
      </button>
    </div>
  );
}
