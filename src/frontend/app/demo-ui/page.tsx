/* Week 3 – Demo UI States: sample alerts, AI summaries, placeholder charts */
"use client";

import { useState } from "react";
import {
  Bell, Bot, FileText, TrendingUp, TrendingDown,
  Minus, Info, CheckCircle2, AlertTriangle, XCircle,
  Activity, Moon, Heart, Footprints, Wind, Thermometer,
  ChevronDown, ChevronUp, Zap,
} from "lucide-react";
import { Card, Badge, SeverityBadge, StatCard, Section } from "@/components/ui/shared";
import {
  PlaceholderBarChart,
  SummaryTile,
  PlaceholderDonut,
  SparkLine,
} from "@/components/dashboard/DummyCards";
import { cn } from "@/lib/utils";

// ─────────────────────────────────────────────────────────────────
// SAMPLE ALERT DATA (static — for screenshot states)
// ─────────────────────────────────────────────────────────────────
const SAMPLE_ALERTS = [
  {
    id: "sa-1",
    severity: "critical" as const,
    category: "Lab Result",
    icon: "🩸",
    title: "Haemoglobin critically low",
    patient: "Riya Sharma",
    detail:
      "Hb 9.8 g/dL — below safe threshold of 12 g/dL. Iron-deficiency anaemia likely. " +
      "Recommend iron supplementation and dietary review.",
    evidence: ["CBC Report Jan 2026 · Hb = 9.8 g/dL", "Serum Iron = 42 µg/dL (ref: 60–170)"],
    createdAt: "2026-01-10",
    state: "active",
  },
  {
    id: "sa-2",
    severity: "high" as const,
    category: "Lab Result",
    icon: "🫀",
    title: "LDL cholesterol elevated",
    patient: "Riya Sharma",
    detail:
      "LDL 138 mg/dL — above desirable range of <100 mg/dL. Continue statin therapy " +
      "and reduce saturated fat intake.",
    evidence: ["Lipid Panel Mar 2026 · LDL = 138 mg/dL", "Total Cholesterol = 215 mg/dL"],
    createdAt: "2026-03-04",
    state: "acknowledged",
  },
  {
    id: "sa-3",
    severity: "high" as const,
    category: "Diabetes",
    icon: "🩺",
    title: "HbA1c above diabetic threshold",
    patient: "Karan Patel",
    detail:
      "HbA1c 7.8% — in the diabetic range (≥6.5%). Blood glucose management needs " +
      "re-evaluation. Consider adjusting medication.",
    evidence: ["HbA1c Report Feb 2026 · 7.8%", "Fasting glucose 148 mg/dL"],
    createdAt: "2026-02-20",
    state: "active",
  },
  {
    id: "sa-4",
    severity: "medium" as const,
    category: "Environment",
    icon: "💨",
    title: "Poor air quality — outdoor activity caution",
    patient: "Riya Sharma",
    detail:
      "AQI 168 (Unhealthy). Riya has active anaemia. Outdoor exercise recommended only " +
      "in early morning with N95 mask.",
    evidence: ["Real-time AQI · Chennai North · 168 PM2.5", "Heatwave advisory active"],
    createdAt: "2026-03-09",
    state: "active",
  },
  {
    id: "sa-5",
    severity: "low" as const,
    category: "Wearable",
    icon: "😴",
    title: "Sleep duration below target",
    patient: "Riya Sharma",
    detail:
      "Average sleep 5.6h over last 7 days — below recommended 7–9h. Poor sleep " +
      "may worsen iron absorption and fatigue.",
    evidence: ["Wearable data · 7-day avg = 5.6h", "Min observed: 4.5h"],
    createdAt: "2026-03-07",
    state: "dismissed",
  },
];

// ─────────────────────────────────────────────────────────────────
// SAMPLE AI SUMMARY DATA
// ─────────────────────────────────────────────────────────────────
const AI_SUMMARIES = [
  {
    id: "ai-1",
    question: "Why am I feeling so tired lately?",
    label: "Fatigue Explanation",
    accentColor: "border-blue-700/50 bg-blue-950/20",
    headerColor: "text-blue-400",
    confidence: 91,
    response: [
      "Your fatigue most likely has three overlapping causes:",
      "1. **Iron-deficiency anaemia** (Hb 9.8 g/dL) — low haemoglobin means your blood carries less oxygen to muscles and organs, causing persistent tiredness.",
      "2. **Poor sleep quality** — your wearable shows an average of only 5.6 h/night over the past week, well below the recommended 7–9 h.",
      "3. **High AQI exposure** — breathing polluted air (AQI 168 in Chennai) increases oxidative stress and can worsen fatigue in anaemic patients.",
    ],
    citations: [
      "CBC_Report_Jan2026.pdf · Hb = 9.8 g/dL",
      "Wearable data · 7-day avg sleep = 5.6 h",
      "Environment · Chennai AQI = 168",
    ],
    disclaimer: true,
  },
  {
    id: "ai-2",
    question: "What does my HbA1c of 7.8% mean?",
    label: "Lab Result Explanation",
    accentColor: "border-amber-700/50 bg-amber-950/20",
    headerColor: "text-amber-400",
    confidence: 96,
    response: [
      "HbA1c measures your **average blood glucose over the past 3 months** by looking at how much sugar is stuck to your red blood cells.",
      "A result of **7.8%** places you in the **diabetic range** (≥6.5% = diabetes). A healthy target for most managed diabetics is below 7.0%.",
      "Your current level suggests blood glucose has been consistently elevated. This raises risk for kidney, nerve, and eye complications if sustained long-term.",
    ],
    citations: [
      "HbA1c_Feb2026.pdf · HbA1c = 7.8%",
      "Lipid_Panel_Jan2026.pdf · Fasting glucose = 148 mg/dL",
    ],
    disclaimer: true,
  },
  {
    id: "ai-3",
    question: "Is it safe to exercise outdoors today?",
    label: "Personalised Safety Advice",
    accentColor: "border-emerald-700/50 bg-emerald-950/20",
    headerColor: "text-emerald-400",
    confidence: 83,
    response: [
      "**Today: Caution advised.** Chennai AQI is 168 (Unhealthy for all groups) and a heatwave advisory is active.",
      "Given your low haemoglobin (9.8 g/dL), strenuous outdoor exercise could cause dizziness, shortness of breath, or fainting.",
      "**Safer alternatives:** Indoor walking or light yoga, or outdoor activity before 7 AM when AQI tends to dip below 120.",
    ],
    citations: [
      "Environment · Chennai AQI = 168 · PM2.5 dominant",
      "CBC_Report_Jan2026.pdf · Hb = 9.8 g/dL",
    ],
    disclaimer: true,
  },
];

// ─────────────────────────────────────────────────────────────────
// PLACEHOLDER CHART DATA
// ─────────────────────────────────────────────────────────────────
const STEPS_DATA = [
  { label: "Mon", value: 4200 },
  { label: "Tue", value: 7800 },
  { label: "Wed", value: 6100 },
  { label: "Thu", value: 9400 },
  { label: "Fri", value: 5300 },
  { label: "Sat", value: 11200 },
  { label: "Sun", value: 8700 },
];
const SLEEP_DATA = [
  { label: "Mon", value: 5.5 },
  { label: "Tue", value: 6.2 },
  { label: "Wed", value: 4.8 },
  { label: "Thu", value: 7.1 },
  { label: "Fri", value: 5.9 },
  { label: "Sat", value: 8.0 },
  { label: "Sun", value: 6.5 },
];
const HR_DATA = [
  { label: "Mon", value: 78 },
  { label: "Tue", value: 82 },
  { label: "Wed", value: 75 },
  { label: "Thu", value: 88 },
  { label: "Fri", value: 80 },
  { label: "Sat", value: 72 },
  { label: "Sun", value: 76 },
];
const SPARK_STEPS = [4200, 7800, 6100, 9400, 5300, 11200, 8700];
const SPARK_HBA1C = [8.2, 8.0, 7.9, 7.8, 7.8, 7.8, 7.8];
const SPARK_SLEEP = [5.5, 6.2, 4.8, 7.1, 5.9, 8.0, 6.5];

// ─────────────────────────────────────────────────────────────────
// PAGE COMPONENT
// ─────────────────────────────────────────────────────────────────
type AlertState = "all" | "active" | "acknowledged" | "dismissed";

export default function DemoUIPage() {
  const [alertFilter, setAlertFilter] = useState<AlertState>("all");
  const [openAlertId, setOpenAlertId] = useState<string | null>(null);
  const [openSummaryId, setOpenSummaryId] = useState<string | null>("ai-1");

  const filteredAlerts =
    alertFilter === "all"
      ? SAMPLE_ALERTS
      : SAMPLE_ALERTS.filter((a) => a.state === alertFilter);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-10">
      {/* Page header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Zap size={18} className="text-yellow-400" />
          <h1 className="text-xl font-bold text-white">Week 3 — Demo UI States</h1>
        </div>
        <p className="text-sm text-slate-400">
          Static showcase of all UI states for screenshots, demo walkthroughs, and documentation.
        </p>
        <div className="flex flex-wrap gap-2 mt-3">
          {(["alerts", "ai-summaries", "charts", "kpi-tiles"] as const).map((s) => (
            <a
              key={s}
              href={`#${s}`}
              className="text-xs px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 transition"
            >
              #{s}
            </a>
          ))}
        </div>
      </div>

      {/* ── 1. SAMPLE ALERTS ─────────────────────────── */}
      <section id="alerts" className="space-y-4">
        <SectionHeading
          icon={<Bell size={16} className="text-red-400" />}
          label="Sample Alerts"
          tag="UI State 1"
          description="All alert severity levels and interaction states (active · acknowledged · dismissed)."
        />

        {/* Filter bar */}
        <div className="flex gap-2 flex-wrap">
          {(["all", "active", "acknowledged", "dismissed"] as AlertState[]).map((f) => {
            const count =
              f === "all"
                ? SAMPLE_ALERTS.length
                : SAMPLE_ALERTS.filter((a) => a.state === f).length;
            return (
              <button
                key={f}
                onClick={() => setAlertFilter(f)}
                className={cn(
                  "text-xs px-3 py-1.5 rounded-lg border transition",
                  alertFilter === f
                    ? "bg-blue-600 border-blue-500 text-white"
                    : "bg-slate-800 border-slate-700 text-slate-400 hover:text-white"
                )}
              >
                {f[0].toUpperCase() + f.slice(1)}{" "}
                <span className="opacity-60">({count})</span>
              </button>
            );
          })}
        </div>

        <div className="space-y-3">
          {filteredAlerts.map((alert) => (
            <SampleAlertCard
              key={alert.id}
              alert={alert}
              open={openAlertId === alert.id}
              onToggle={() =>
                setOpenAlertId((prev) => (prev === alert.id ? null : alert.id))
              }
            />
          ))}
        </div>

        {/* State legend */}
        <div className="grid grid-cols-3 gap-2 mt-2">
          {[
            { label: "Active", color: "bg-red-500", desc: "Unreviewed, needs action" },
            { label: "Acknowledged", color: "bg-emerald-500", desc: "Reviewed by user" },
            { label: "Dismissed", color: "bg-slate-500", desc: "Ignored / resolved" },
          ].map((s) => (
            <div key={s.label} className="bg-slate-800/50 border border-slate-700 rounded-xl p-3 text-center">
              <div className={cn("h-2 w-2 rounded-full mx-auto mb-1.5", s.color)} />
              <p className="text-xs font-semibold text-white">{s.label}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── 2. AI SUMMARIES ──────────────────────────── */}
      <section id="ai-summaries" className="space-y-4">
        <SectionHeading
          icon={<Bot size={16} className="text-blue-400" />}
          label="Example AI Summaries"
          tag="UI State 2"
          description="RAG-grounded responses with citations, confidence scores, and medical disclaimers."
        />

        <div className="space-y-4">
          {AI_SUMMARIES.map((summary) => (
            <AISummaryCard
              key={summary.id}
              summary={summary}
              open={openSummaryId === summary.id}
              onToggle={() =>
                setOpenSummaryId((prev) => (prev === summary.id ? null : summary.id))
              }
            />
          ))}
        </div>

        {/* Confidence legend */}
        <div className="flex gap-3 flex-wrap mt-1">
          {[
            { range: "≥90%", color: "emerald", label: "High confidence" },
            { range: "75–89%", color: "amber", label: "Moderate" },
            { range: "<75%", color: "red", label: "Low — verify with doctor" },
          ].map((c) => (
            <div key={c.range} className="flex items-center gap-1.5 text-xs text-slate-400">
              <div
                className={cn(
                  "h-2 w-2 rounded-full",
                  c.color === "emerald"
                    ? "bg-emerald-400"
                    : c.color === "amber"
                    ? "bg-amber-400"
                    : "bg-red-400"
                )}
              />
              {c.range} — {c.label}
            </div>
          ))}
        </div>
      </section>

      {/* ── 3. PLACEHOLDER CHARTS ────────────────────── */}
      <section id="charts" className="space-y-4">
        <SectionHeading
          icon={<TrendingUp size={16} className="text-emerald-400" />}
          label="Placeholder Charts"
          tag="UI State 3"
          description="Pure CSS/SVG charts — no external library. Bar charts, sparklines, and donut gauges."
        />

        <div className="grid md:grid-cols-3 gap-4">
          <PlaceholderBarChart
            title="Daily Steps (7d)"
            data={STEPS_DATA}
            target={8000}
            unit=""
            color="bg-blue-500"
            warnColor="bg-amber-500"
          />
          <PlaceholderBarChart
            title="Sleep Hours (7d)"
            data={SLEEP_DATA}
            target={7}
            unit="h"
            color="bg-purple-500"
            warnColor="bg-rose-500"
          />
          <PlaceholderBarChart
            title="Heart Rate Avg (7d)"
            data={HR_DATA}
            unit=" bpm"
            color="bg-rose-500"
          />
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <SparkLine label="Steps Trend (7d)" data={SPARK_STEPS} color="#3b82f6" />
          <SparkLine label="HbA1c Trend (7 readings)" data={SPARK_HBA1C} color="#f59e0b" />
          <SparkLine label="Sleep Trend (7d)" data={SPARK_SLEEP} color="#a855f7" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <PlaceholderDonut label="Sleep goal" value={6.5} max={9} color="#a855f7" unit="h" />
          <PlaceholderDonut label="Step goal" value={8700} max={10000} color="#3b82f6" unit=" steps" />
          <PlaceholderDonut label="AQI (0–300)" value={168} max={300} color="#f97316" unit="" />
          <PlaceholderDonut label="HbA1c target" value={7.8} max={10} color="#f59e0b" unit="%" />
        </div>
      </section>

      {/* ── 4. KPI TILES ─────────────────────────────── */}
      <section id="kpi-tiles" className="space-y-4">
        <SectionHeading
          icon={<Activity size={16} className="text-purple-400" />}
          label="KPI Summary Tiles"
          tag="UI State 4"
          description="Summary tiles with trend arrows covering health, lab, and environment metrics."
        />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <SummaryTile label="Avg Steps / Day" value="7,386" sub="Last 7 days" trend="up" accent="blue" />
          <SummaryTile label="Avg Sleep" value="6.3h" sub="Target 7h" trend="down" trendGoodUp accent="purple" />
          <SummaryTile label="HbA1c" value="7.8%" sub="Diabetic range" trend="down" trendGoodUp={false} accent="amber" />
          <SummaryTile label="Haemoglobin" value="9.8 g/dL" sub="↓ Low" trend="down" trendGoodUp={false} accent="rose" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <SummaryTile label="Active Alerts" value="3" sub="For Riya Sharma" accent="rose" />
          <SummaryTile label="Reports Processed" value="5" sub="Jan–Mar 2026" trend="up" accent="emerald" />
          <SummaryTile label="AQI Today" value="168" sub="Unhealthy · Chennai" trend="down" trendGoodUp={false} accent="amber" />
          <SummaryTile label="LDL Cholesterol" value="138" sub="High (>100 mg/dL)" trend="up" trendGoodUp={false} accent="rose" />
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Steps Today" value="8,700" icon={<Footprints size={16} />} trend="up" />
          <StatCard label="Sleep" value="6.5h" icon={<Moon size={16} />} trend="down" trendBad />
          <StatCard label="Heart Rate" value="76 bpm" icon={<Heart size={16} />} />
          <StatCard label="Activity" value="Active" icon={<Activity size={16} />} sub="1,300 to goal" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="AQI" value="168" icon={<Wind size={16} />} trend="down" trendBad sub="Unhealthy" />
          <StatCard label="Temperature" value="37 °C" icon={<Thermometer size={16} />} trend="up" trendBad sub="Heatwave advisory" />
          <StatCard label="LDL" value="138 mg/dL" icon={<Activity size={16} />} trend="up" trendBad />
          <StatCard label="HbA1c" value="7.8%" icon={<Activity size={16} />} trend="neutral" sub="Stable" />
        </div>
      </section>

      {/* Screenshot guide */}
      <section className="space-y-3">
        <SectionHeading
          icon={<Info size={16} className="text-slate-400" />}
          label="Screenshot Guide"
          tag="Docs"
          description="Recommended screenshot regions for the project report."
        />
        <div className="grid md:grid-cols-2 gap-3">
          {[
            {
              screen: "/alerts",
              view: "Alerts Dashboard",
              tip: "Select Riya Sharma, show 3 active alerts. Expand first alert to show evidence drawer. Screenshot at 1280×800.",
            },
            {
              screen: "/chat",
              view: "AI Response View",
              tip: 'Send "Why am I feeling so tired?" message. Wait for stub response + citations to appear. Screenshot at 1280×900.',
            },
            {
              screen: "/reports",
              view: "Report Timeline",
              tip: "Expand CBC Report card to show OCR snippet and extracted lab values with colour-coded status badges.",
            },
            {
              screen: "/demo-ui#charts",
              view: "Placeholder Charts",
              tip: "Screenshot the bar chart grid (steps, sleep, HR) and the KPI tile section side by side.",
            },
          ].map((g) => (
            <div
              key={g.screen}
              className="bg-slate-800/60 border border-slate-700 rounded-2xl p-4 space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-white">{g.view}</p>
                <a
                  href={g.screen}
                  className="text-[10px] px-2 py-0.5 rounded bg-blue-900/50 border border-blue-700/40 text-blue-400 hover:bg-blue-800/60 transition"
                >
                  Open →
                </a>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">{g.tip}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// SUB-COMPONENTS
// ─────────────────────────────────────────────────────────────────

function SectionHeading({
  icon,
  label,
  tag,
  description,
}: {
  icon: React.ReactNode;
  label: string;
  tag: string;
  description: string;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        {icon}
        <h2 className="text-base font-bold text-white">{label}</h2>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700 text-slate-400 border border-slate-600">
          {tag}
        </span>
      </div>
      <p className="text-xs text-slate-500">{description}</p>
    </div>
  );
}

const STATE_META = {
  active: {
    label: "Active",
    dot: "bg-red-500",
    pill: "bg-red-950/40 border-red-800/40 text-red-400",
  },
  acknowledged: {
    label: "Acknowledged",
    dot: "bg-emerald-500",
    pill: "bg-emerald-950/40 border-emerald-800/40 text-emerald-400",
  },
  dismissed: {
    label: "Dismissed",
    dot: "bg-slate-600",
    pill: "bg-slate-800/40 border-slate-700 text-slate-500",
  },
};

function SampleAlertCard({
  alert,
  open,
  onToggle,
}: {
  alert: (typeof SAMPLE_ALERTS)[0];
  open: boolean;
  onToggle: () => void;
}) {
  const meta = STATE_META[alert.state as keyof typeof STATE_META];
  return (
    <Card
      className={cn(
        "cursor-pointer transition-all",
        alert.state === "dismissed" && "opacity-60",
        open && "border-slate-600"
      )}
      onClick={onToggle}
    >
      <div className="flex items-start gap-3">
        <span className="text-xl mt-0.5 flex-shrink-0">{alert.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <SeverityBadge severity={alert.severity} />
            <Badge variant="outline" className="text-[10px]">{alert.category}</Badge>
            <span
              className={cn(
                "text-[10px] px-2 py-0.5 rounded-full border font-medium",
                meta.pill
              )}
            >
              <span className={cn("inline-block h-1 w-1 rounded-full mr-1 align-middle", meta.dot)} />
              {meta.label}
            </span>
            <span className="text-[10px] text-slate-500 ml-auto">{alert.createdAt}</span>
          </div>
          <p className="text-sm font-semibold text-white">{alert.title}</p>
          <p className="text-xs text-slate-400 mt-0.5">{alert.patient}</p>
        </div>
        <button className="text-slate-600 hover:text-slate-400 ml-1 flex-shrink-0">
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {/* Evidence drawer */}
      {open && (
        <div
          className="mt-3 pt-3 border-t border-slate-700/60 space-y-3"
          onClick={(e) => e.stopPropagation()}
        >
          <p className="text-xs text-slate-300 leading-relaxed">{alert.detail}</p>
          <div className="space-y-1.5">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
              Evidence
            </p>
            {alert.evidence.map((e, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 text-[11px] text-blue-400 bg-blue-950/30 border border-blue-800/30 rounded-lg px-2.5 py-1.5"
              >
                <FileText size={10} />
                {e}
              </div>
            ))}
          </div>
          {alert.state === "active" && (
            <div className="flex gap-2">
              <button className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-emerald-900/40 border border-emerald-700/50 text-emerald-400 rounded-lg hover:bg-emerald-800/50 transition">
                <CheckCircle2 size={12} /> Acknowledge
              </button>
              <button className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-slate-800 border border-slate-700 text-slate-400 rounded-lg hover:bg-slate-700 transition">
                <XCircle size={12} /> Dismiss
              </button>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function AISummaryCard({
  summary,
  open,
  onToggle,
}: {
  summary: (typeof AI_SUMMARIES)[0];
  open: boolean;
  onToggle: () => void;
}) {
  const confColor =
    summary.confidence >= 90
      ? "text-emerald-400"
      : summary.confidence >= 75
      ? "text-amber-400"
      : "text-red-400";

  return (
    <div
      className={cn(
        "rounded-2xl border p-4 cursor-pointer transition-all",
        summary.accentColor,
        open && "border-slate-600"
      )}
      onClick={onToggle}
    >
      {/* Header row */}
      <div className="flex items-start gap-3">
        <div className="h-8 w-8 rounded-full bg-slate-700/80 border border-slate-600 flex items-center justify-center flex-shrink-0">
          <Bot size={14} className={summary.headerColor} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className="text-[10px]">{summary.label}</Badge>
            <span className={cn("text-[10px] font-semibold", confColor)}>
              {summary.confidence}% confidence
            </span>
          </div>
          <p className="text-xs text-slate-400 italic">&ldquo;{summary.question}&rdquo;</p>
        </div>
        <button className="text-slate-600 hover:text-slate-400 flex-shrink-0">
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {/* Expanded response */}
      {open && (
        <div
          className="mt-3 pt-3 border-t border-slate-700/40 space-y-3"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Response paragraphs with simple bold rendering */}
          <div className="space-y-2">
            {summary.response.map((line, i) => (
              <ResponseLine key={i} text={line} />
            ))}
          </div>

          {/* Citations */}
          <div className="space-y-1.5">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
              Sources
            </p>
            {summary.citations.map((c, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 text-[11px] text-blue-400 bg-blue-950/30 border border-blue-800/30 rounded-lg px-2.5 py-1.5"
              >
                <FileText size={10} />
                {c}
              </div>
            ))}
          </div>

          {/* Disclaimer */}
          {summary.disclaimer && (
            <div className="flex items-start gap-2 bg-amber-950/30 border border-amber-800/30 rounded-xl px-3 py-2">
              <AlertTriangle size={12} className="text-amber-400 mt-0.5 flex-shrink-0" />
              <p className="text-[10px] text-amber-300/80 leading-relaxed">
                This is not medical advice. Responses are AI-generated and grounded in your uploaded
                reports. Always consult a qualified doctor before acting on health information.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/** Renders **bold** markdown tokens inline */
function ResponseLine({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <p className="text-sm text-slate-200 leading-relaxed">
      {parts.map((part, i) =>
        part.startsWith("**") && part.endsWith("**") ? (
          <strong key={i} className="text-white font-semibold">
            {part.slice(2, -2)}
          </strong>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </p>
  );
}
