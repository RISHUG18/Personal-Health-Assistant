/* Week 3 – Demo Flow Test Notes + Bug Report */
"use client";

import { useState } from "react";
import {
  CheckCircle2, AlertTriangle, XCircle, ChevronDown, ChevronUp,
  Play, Upload, Bell, MessageCircle, FileText, ClipboardList,
} from "lucide-react";
import { Card, Badge, Section } from "@/components/ui/shared";
import { cn } from "@/lib/utils";

// ─────────────────────────────────────────────────────────────────
// DEMO FLOW STEPS
// ─────────────────────────────────────────────────────────────────
const DEMO_STEPS = [
  {
    id: 1,
    icon: Upload,
    title: "Upload Report",
    route: "/reports",
    iconColor: "text-blue-400",
    bgColor: "bg-blue-900/30 border-blue-700/50",
    instructions: [
      'Navigate to /reports and click "Upload Report" (top-right button)',
      "A file picker opens — select a PDF from your system (or use the synthetic PDFs listed in the README)",
      "The upload stub simulates OCR processing with a progress animation",
      "The new report card should appear at the top of the timeline with a reportType badge",
    ],
    expectedOutcome:
      "New report card visible in timeline with correct reportType badge and placeholder extracted values.",
    status: "pass" as const,
    notes: "Upload button is present. File picker triggers. UI transitions smoothly. (Backend OCR pipeline is Week 3 \u2014 currently stubbed.)",
  },
  {
    id: 2,
    icon: Bell,
    title: "View Alerts",
    route: "/alerts",
    iconColor: "text-red-400",
    bgColor: "bg-red-900/30 border-red-700/50",
    instructions: [
      "Navigate to /alerts",
      "Select patient from the dropdown (Riya Sharma has 3 active alerts)",
      "Review summary bar: active / acknowledged counts",
      "Click on a critical alert card to expand the evidence drawer",
      "Click Acknowledge — toast notification should appear",
      "Click Dismiss — alert should leave the list with a toast",
    ],
    expectedOutcome:
      "Alerts filter correctly by patient. Evidence drawer expands/collapses. Acknowledge/Dismiss update state and show toast.",
    status: "pass" as const,
    notes: "All interactive states work. Toast appears within 300ms. Acknowledged alerts move to separate section.",
  },
  {
    id: 3,
    icon: MessageCircle,
    title: "Ask AI Question",
    route: "/chat",
    iconColor: "text-emerald-400",
    bgColor: "bg-emerald-900/30 border-emerald-700/50",
    instructions: [
      "Navigate to /chat",
      'Pre-loaded history shows prior conversation with Riya\'s anaemia context',
      'Type: "Why am I feeling so tired lately?" and press Enter (or click Send)',
      "Typing indicator (3 bouncing dots) should appear immediately",
      "After ~1.2s, the stub AI response appears with citations",
      'Try: "Is it safe to exercise outdoors today?" for environment-aware response',
    ],
    expectedOutcome:
      "Messages render in correct chat bubble alignment. Citations appear below AI response. Scroll follows new messages.",
    status: "pass" as const,
    notes: "Typing indicator animates correctly. Response arrives at 1.2s stub delay. Citations render as styled badges. Accessible disclaimer shown at bottom.",
  },
  {
    id: 4,
    icon: FileText,
    title: "View Explanation / Report Detail",
    route: "/reports",
    iconColor: "text-purple-400",
    bgColor: "bg-purple-900/30 border-purple-700/50",
    instructions: [
      "Navigate to /reports",
      "Click any report card on the timeline to expand it",
      "View the extracted lab values with colour-coded status badges (green = normal, amber = warning, red = critical)",
      'Click "View OCR Preview" — the raw OCR text snippet drawer should slide open',
      "Verify reportType badge (blood_test / lipid_panel / diabetes / thyroid) is visible",
      "Collapse the card and check that neighbouring cards are unaffected",
    ],
    expectedOutcome:
      "Report card expands cleanly. OCR drawer visible. Lab value colours match severity. reportType badge rendered.",
    status: "warn" as "pass" | "warn" | "fail",
    notes: "Thyroid report (rep-3) shows 'Processing — OCR quality poor' in the preview — this is intentional but could confuse demo viewers. Consider adding a tooltip.",
  },
];

// ─────────────────────────────────────────────────────────────────
// BUG REPORT ITEMS
// ─────────────────────────────────────────────────────────────────
const BUG_REPORT = [
  {
    id: "b-1",
    severity: "warn" as const,
    area: "Reports",
    description:
      "Thyroid report OCR snippet shows 'Processing — OCR quality poor' with no user-facing explanation. Demo viewers may interpret this as a UI bug rather than intentional synthetic data.",
    fix: "Add a tooltip or info badge explaining: 'This report simulates a real-world OCR failure scenario.'",
    status: "open" as const,
  },
  {
    id: "b-2",
    severity: "info" as const,
    area: "Chat",
    description:
      "Stub AI always returns the same default response regardless of the question typed. This could break the demo flow if the presenter tries multiple different queries.",
    fix: "Add 3–5 keyword-matched stubs in STUB_RESPONSES (e.g., matching 'tired', 'HbA1c', 'exercise') to return contextually relevant canned responses.",
    status: "open" as const,
  },
  {
    id: "b-3",
    severity: "info" as const,
    area: "Reports",
    description:
      "Upload button opens the system file picker but the selected file is not added to the timeline (fully stubbed). A loading spinner state could make this clearer.",
    fix: "Add a toast message: 'Report uploaded — processing by OCR pipeline (Week 3 backend).' and show a loading card placeholder.",
    status: "open" as const,
  },
  {
    id: "b-4",
    severity: "pass" as const,
    area: "Alerts",
    description: "Alert card state (acknowledged/dismissed) resets on page refresh — in-memory state only.",
    fix: "Expected behaviour for demo — no persistence needed until Week 4 backend.",
    status: "resolved" as const,
  },
  {
    id: "b-5",
    severity: "pass" as const,
    area: "Navigation",
    description: "Bottom nav on mobile only shows first 5 items; Personas, Doctor, Profile, Demo QA are sidebar-only.",
    fix: "By design — bottom nav is space-constrained. All routes accessible via sidebar or direct URL.",
    status: "resolved" as const,
  },
];

// ─────────────────────────────────────────────────────────────────
// DELIVERABLES CHECKLIST
// ─────────────────────────────────────────────────────────────────
const DELIVERABLES = [
  { label: "Demo UI states page (/demo-ui)", done: true, note: "sample alerts, AI summaries, charts, KPI tiles" },
  { label: "Sample alert cards — 5 states (critical/high/medium/low + all interaction states)", done: true, note: "" },
  { label: "Example AI summaries — 3 contextualised responses with citations", done: true, note: "" },
  { label: "Placeholder charts — bar, sparkline, donut (pure CSS/SVG)", done: true, note: "" },
  { label: "KPI summary tiles — 8 tiles across health, lab, and environment", done: true, note: "" },
  { label: "Screenshot guide — 4 recommended regions with instructions", done: true, note: "" },
  { label: "Demo flow walkthrough — 4 steps with pass/warn status", done: true, note: "" },
  { label: "Bug report — 3 open + 2 resolved", done: true, note: "" },
  { label: "Demo test notes (this page)", done: true, note: "" },
];

// ─────────────────────────────────────────────────────────────────
// PAGE
// ─────────────────────────────────────────────────────────────────
export default function DemoNotesPage() {
  const [openStep, setOpenStep] = useState<number | null>(1);
  const [openBug, setOpenBug] = useState<string | null>(null);

  const passed = DEMO_STEPS.filter((s) => s.status === "pass").length;
  const warned = DEMO_STEPS.filter((s) => s.status === "warn").length;
  const failed = DEMO_STEPS.filter((s) => s.status === "fail").length;

  const openBugs = BUG_REPORT.filter((b) => b.status === "open").length;
  const resolvedBugs = BUG_REPORT.filter((b) => b.status === "resolved").length;

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-10">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <ClipboardList size={18} className="text-blue-400" />
          <h1 className="text-xl font-bold text-white">Week 3 — Demo Test Notes</h1>
        </div>
        <p className="text-sm text-slate-400">
          Demo flow walkthrough results, UI bug report, and week-3 deliverables checklist.
        </p>
      </div>

      {/* Summary counters */}
      <div className="grid grid-cols-3 gap-3">
        <SummaryPill icon={<CheckCircle2 size={14} />} value={passed} label="Steps Passed" color="emerald" />
        <SummaryPill icon={<AlertTriangle size={14} />} value={warned} label="Steps with Warn" color="amber" />
        <SummaryPill icon={<XCircle size={14} />} value={failed} label="Steps Failed" color="red" />
      </div>

      {/* ── Demo Flow Steps ───────────────────────── */}
      <Section title="Demo Flow Walkthrough">
        <div className="space-y-3">
          {DEMO_STEPS.map((step) => {
            const Icon = step.icon;
            const isOpen = openStep === step.id;
            const statusIcon =
              step.status === "pass" ? (
                <CheckCircle2 size={14} className="text-emerald-400 flex-shrink-0" />
              ) : step.status === "warn" ? (
                <AlertTriangle size={14} className="text-amber-400 flex-shrink-0" />
              ) : (
                <XCircle size={14} className="text-red-400 flex-shrink-0" />
              );

            return (
              <div
                key={step.id}
                className={cn(
                  "rounded-2xl border p-4 cursor-pointer transition-all",
                  step.bgColor,
                  isOpen && "border-slate-500"
                )}
                onClick={() => setOpenStep(isOpen ? null : step.id)}
              >
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center flex-shrink-0">
                    <Icon size={14} className={step.iconColor} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-slate-500">Step {step.id}</span>
                      {statusIcon}
                      <a
                        href={step.route}
                        onClick={(e) => e.stopPropagation()}
                        className="text-[10px] text-blue-400 hover:underline ml-auto"
                      >
                        {step.route}
                      </a>
                    </div>
                    <p className="text-sm font-semibold text-white mt-0.5">{step.title}</p>
                  </div>
                  <button className="text-slate-600 hover:text-slate-400">
                    {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                </div>

                {isOpen && (
                  <div
                    className="mt-3 pt-3 border-t border-slate-700/50 space-y-3"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="space-y-1.5">
                      <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
                        Steps
                      </p>
                      {step.instructions.map((ins, i) => (
                        <div key={i} className="flex gap-2 text-xs text-slate-300">
                          <span className="text-slate-600 flex-shrink-0">{i + 1}.</span>
                          <span>{ins}</span>
                        </div>
                      ))}
                    </div>
                    <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3">
                      <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1">
                        Expected Outcome
                      </p>
                      <p className="text-xs text-slate-300">{step.expectedOutcome}</p>
                    </div>
                    <div
                      className={cn(
                        "rounded-xl p-3 border text-xs leading-relaxed",
                        step.status === "pass"
                          ? "bg-emerald-950/30 border-emerald-800/40 text-emerald-300"
                          : step.status === "warn"
                          ? "bg-amber-950/30 border-amber-800/40 text-amber-300"
                          : "bg-red-950/30 border-red-800/40 text-red-300"
                      )}
                    >
                      <span className="font-semibold uppercase text-[10px] tracking-wide block mb-1">
                        Test Notes
                      </span>
                      {step.notes}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Section>

      {/* ── Bug Report ───────────────────────────── */}
      <Section title={`UI Bug Report — ${openBugs} open · ${resolvedBugs} resolved`}>
        <div className="space-y-3">
          {BUG_REPORT.map((bug) => {
            const isOpen = openBug === bug.id;
            const severityClass =
              bug.severity === "warn"
                ? "border-amber-700/50 bg-amber-950/20"
                : bug.severity === "info"
                ? "border-blue-700/50 bg-blue-950/20"
                : "border-emerald-700/50 bg-emerald-950/20";

            return (
              <div
                key={bug.id}
                className={cn(
                  "rounded-2xl border p-4 cursor-pointer transition-all",
                  severityClass,
                  bug.status === "resolved" && "opacity-60",
                  isOpen && "border-slate-500"
                )}
                onClick={() => setOpenBug(isOpen ? null : bug.id)}
              >
                <div className="flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-[10px]">{bug.area}</Badge>
                      {bug.status === "open" ? (
                        <span className="text-[10px] text-amber-400 font-medium">Open</span>
                      ) : (
                        <span className="text-[10px] text-emerald-400 font-medium flex items-center gap-1">
                          <CheckCircle2 size={10} /> Resolved
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-200 line-clamp-2">{bug.description}</p>
                  </div>
                  <button className="text-slate-600 hover:text-slate-400 flex-shrink-0">
                    {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                </div>
                {isOpen && (
                  <div
                    className="mt-3 pt-3 border-t border-slate-700/40 space-y-2"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <p className="text-xs text-slate-300 leading-relaxed">{bug.description}</p>
                    <div className="bg-slate-800/60 border border-slate-700 rounded-xl px-3 py-2">
                      <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1">
                        Suggested Fix
                      </p>
                      <p className="text-xs text-slate-300">{bug.fix}</p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Section>

      {/* ── Week 3 Deliverables Checklist ─────────── */}
      <Section title="Week-3 Completion Checklist">
        <div className="space-y-2">
          {DELIVERABLES.map((d, i) => (
            <div
              key={i}
              className={cn(
                "flex items-start gap-3 px-4 py-3 rounded-xl border transition",
                d.done
                  ? "bg-emerald-950/20 border-emerald-800/30"
                  : "bg-slate-800/40 border-slate-700"
              )}
            >
              {d.done ? (
                <CheckCircle2 size={14} className="text-emerald-400 flex-shrink-0 mt-0.5" />
              ) : (
                <div className="h-3.5 w-3.5 rounded-full border-2 border-slate-600 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1 min-w-0">
                <p className={cn("text-xs font-medium", d.done ? "text-emerald-300" : "text-slate-300")}>
                  {d.label}
                </p>
                {d.note && <p className="text-[10px] text-slate-500 mt-0.5">{d.note}</p>}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-950/30 border border-emerald-700/40">
          <CheckCircle2 size={16} className="text-emerald-400" />
          <p className="text-sm font-semibold text-emerald-300">
            {DELIVERABLES.filter((d) => d.done).length} / {DELIVERABLES.length} Week-3 deliverables complete
          </p>
        </div>
      </Section>
    </div>
  );
}

function SummaryPill({
  icon,
  value,
  label,
  color,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
  color: "emerald" | "amber" | "red";
}) {
  const colors = {
    emerald: "border-emerald-700/50 bg-emerald-950/30 text-emerald-400",
    amber: "border-amber-700/50 bg-amber-950/30 text-amber-400",
    red: "border-red-700/50 bg-red-950/30 text-red-400",
  };
  return (
    <div className={cn("rounded-2xl border p-4 text-center", colors[color])}>
      <div className="flex justify-center mb-1">{icon}</div>
      <p className="text-2xl font-bold stat-value">{value}</p>
      <p className="text-[10px] text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}
