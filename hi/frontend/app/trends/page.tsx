/* Week 5 – Health Trends: 7-day sparklines, week summary, trend notes */
"use client";

import { useState } from "react";
import { TrendingUp, TrendingDown, Minus, Moon, Heart, Footprints } from "lucide-react";
import { Card, Badge, Section } from "@/components/ui/shared";
import {
  DEMO_PATIENTS,
  DEMO_HEALTH_METRICS,
  DEMO_ALERTS,
  DEMO_REPORTS,
  DEMO_TRENDS,
  DEMO_WEEK_SUMMARY,
  labStatus,
} from "@/lib/demo-data";
import { cn } from "@/lib/utils";

// ── helper: avg ───────────────────────────────
function avg(nums: number[]) {
  if (!nums.length) return 0;
  return Math.round((nums.reduce((a, b) => a + b, 0) / nums.length) * 10) / 10;
}

// ── Inline sparkline (pure SVG, no lib needed) ─
function Sparkline({
  values,
  color = "#60a5fa",
  height = 36,
  width = 120,
}: {
  values: number[];
  color?: string;
  height?: number;
  width?: number;
}) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / (values.length - 1);
  const pts = values
    .map((v, i) => `${i * step},${height - ((v - min) / range) * (height - 6) - 3}`)
    .join(" ");
  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {/* last dot */}
      {(() => {
        const last = values[values.length - 1];
        const x = (values.length - 1) * step;
        const y = height - ((last - min) / range) * (height - 6) - 3;
        return <circle cx={x} cy={y} r="3" fill={color} />;
      })()}
    </svg>
  );
}

// ── Trend arrow ───────────────────────────────
function TrendArrow({ values, higherIsBetter = true }: { values: number[]; higherIsBetter?: boolean }) {
  if (values.length < 2) return null;
  const first = values[0];
  const last = values[values.length - 1];
  const delta = last - first;
  const pct = Math.round(Math.abs((delta / (first || 1)) * 100));
  const up = delta > 0;
  const good = (up && higherIsBetter) || (!up && !higherIsBetter);

  if (Math.abs(delta) < 0.5) {
    return <span className="text-xs text-slate-400 flex items-center gap-0.5"><Minus size={12} /> Stable</span>;
  }
  return (
    <span className={cn("text-xs flex items-center gap-0.5 font-medium", good ? "text-emerald-400" : "text-red-400")}>
      {up ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
      {pct}%
    </span>
  );
}

export default function TrendsPage() {
  const [patientId, setPatientId] = useState("pat-1");

  // Last 7 days sorted oldest→newest
  const metrics = DEMO_HEALTH_METRICS
    .filter((m) => m.patientId === patientId)
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-7);

  const steps   = metrics.map((m) => m.steps);
  const sleep   = metrics.map((m) => m.sleepHours);
  const hr      = metrics.map((m) => m.heartRateAvg);
  const dates   = metrics.map((m) =>
    new Date(m.date).toLocaleDateString("en-IN", { weekday: "short", day: "numeric" })
  );

  const activeAlerts = DEMO_ALERTS.filter((a) => a.patientId === patientId && !a.acknowledged);
  const abnormalLabs = DEMO_REPORTS
    .filter((r) => r.patientId === patientId)
    .flatMap((r) => r.extractedResults)
    .filter((r) => labStatus(r) !== "normal");

  // Summary uses pat-1 data; for other patients build on-the-fly
  const summary =
    patientId === "pat-1"
      ? DEMO_WEEK_SUMMARY
      : {
          patientId,
          weekLabel: "Feb 27 – Mar 5, 2026",
          avgSteps: avg(steps),
          avgSleepHours: avg(sleep),
          avgHeartRate: avg(hr),
          totalActiveAlerts: activeAlerts.length,
          labFlags: abnormalLabs.length,
          trend: (avg(steps) >= 6000 && avg(sleep) >= 7 ? "improving" : avg(steps) >= 4000 ? "stable" : "declining") as
            | "improving"
            | "stable"
            | "declining",
          notes: [],
        };

  const trendIcon = {
    improving: <TrendingUp size={14} className="text-emerald-400" />,
    stable: <Minus size={14} className="text-slate-400" />,
    declining: <TrendingDown size={14} className="text-red-400" />,
  }[summary.trend];

  const trendColor = {
    improving: "text-emerald-400",
    stable: "text-slate-400",
    declining: "text-red-400",
  }[summary.trend];

  const trends = patientId === "pat-1" ? DEMO_TRENDS : [];

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Health Trends</h1>
        <select
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
          className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-1.5"
        >
          {DEMO_PATIENTS.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>

      {/* Week summary card */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Weekly Summary</p>
            <p className="text-sm text-slate-300 mt-0.5">{summary.weekLabel}</p>
          </div>
          <div className={cn("flex items-center gap-1.5 font-semibold text-sm", trendColor)}>
            {trendIcon}
            {summary.trend.charAt(0).toUpperCase() + summary.trend.slice(1)}
          </div>
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: "Avg Steps", value: summary.avgSteps.toLocaleString(), ok: summary.avgSteps >= 6000 },
            { label: "Avg Sleep", value: `${summary.avgSleepHours}h`, ok: summary.avgSleepHours >= 7 },
            { label: "Avg HR", value: `${summary.avgHeartRate} bpm`, ok: true },
            { label: "Alerts", value: summary.totalActiveAlerts.toString(), ok: summary.totalActiveAlerts === 0 },
            { label: "Lab Flags", value: summary.labFlags.toString(), ok: summary.labFlags === 0 },
          ].map(({ label, value, ok }) => (
            <div key={label} className="bg-slate-900 rounded-xl p-3 text-center">
              <p className={cn("text-xl font-bold", ok ? "text-white" : "text-amber-400")}>{value}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* AI notes */}
        {summary.notes.length > 0 && (
          <div className="border-t border-slate-700 pt-3 space-y-1">
            <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-1.5">Observations</p>
            {summary.notes.map((n, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-blue-400 text-xs mt-0.5">→</span>
                <p className="text-xs text-slate-300">{n}</p>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Sparkline charts section */}
      <Section title="7-Day Sparklines" subtitle={`${dates[0] ?? ""} → ${dates[dates.length - 1] ?? ""}`}>
        <div className="space-y-3">
          <SparkCard
            label="Steps"
            icon={<Footprints size={14} />}
            values={steps}
            dates={dates}
            color="#60a5fa"
            unit="steps"
            goal={6000}
            higherIsBetter
          />
          <SparkCard
            label="Sleep"
            icon={<Moon size={14} />}
            values={sleep}
            dates={dates}
            color="#a78bfa"
            unit="h"
            goal={7}
            higherIsBetter
          />
          <SparkCard
            label="Heart Rate"
            icon={<Heart size={14} />}
            values={hr}
            dates={dates}
            color="#f87171"
            unit="bpm"
            higherIsBetter={false}
          />
        </div>
      </Section>

      {/* Day-by-day table */}
      <Section title="Daily Breakdown">
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400">
                <th className="text-left px-4 py-2.5 font-medium">Date</th>
                <th className="text-right px-3 py-2.5 font-medium">Steps</th>
                <th className="text-right px-3 py-2.5 font-medium">Sleep</th>
                <th className="text-right px-4 py-2.5 font-medium">HR Avg</th>
              </tr>
            </thead>
            <tbody>
              {[...metrics].reverse().map((m) => (
                <tr key={m.date} className="border-b border-slate-800 last:border-0">
                  <td className="px-4 py-2.5 text-slate-300">
                    {new Date(m.date).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })}
                  </td>
                  <td className={cn("text-right px-3 py-2.5 font-medium", m.steps >= 6000 ? "text-emerald-400" : "text-amber-400")}>
                    {m.steps.toLocaleString()}
                  </td>
                  <td className={cn("text-right px-3 py-2.5 font-medium", m.sleepHours >= 7 ? "text-emerald-400" : m.sleepHours < 6 ? "text-red-400" : "text-amber-400")}>
                    {m.sleepHours}h
                  </td>
                  <td className="text-right px-4 py-2.5 text-slate-300">{m.heartRateAvg} bpm</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </Section>

      {/* Trend notes */}
      {trends.length > 0 && (
        <Section title="Insights" subtitle="Auto-generated from pattern analysis">
          <div className="space-y-2">
            {trends.map((t, i) => {
              const catColor: Record<string, string> = {
                environment: "text-orange-400 bg-orange-900/20 border-orange-700/40",
                activity: "text-blue-400 bg-blue-900/20 border-blue-700/40",
                sleep: "text-purple-400 bg-purple-900/20 border-purple-700/40",
                lab: "text-red-400 bg-red-900/20 border-red-700/40",
              };
              const catEmoji: Record<string, string> = {
                environment: "🌍", activity: "🏃", sleep: "🌙", lab: "🧪",
              };
              return (
                <div key={i} className={cn("flex items-start gap-3 p-3 rounded-xl border", catColor[t.category])}>
                  <span className="text-base leading-none mt-0.5">{catEmoji[t.category]}</span>
                  <div className="flex-1">
                    <p className="text-xs text-slate-200">{t.note}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      {new Date(t.date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-[10px] flex-shrink-0">{t.category}</Badge>
                </div>
              );
            })}
          </div>
        </Section>
      )}
    </div>
  );
}

// ── SparkCard ─────────────────────────────────
function SparkCard({
  label,
  icon,
  values,
  dates,
  color,
  unit,
  goal,
  higherIsBetter,
}: {
  label: string;
  icon: React.ReactNode;
  values: number[];
  dates: string[];
  color: string;
  unit: string;
  goal?: number;
  higherIsBetter: boolean;
}) {
  const latest = values[values.length - 1];
  const average = avg(values);
  const atGoal = goal ? (higherIsBetter ? latest >= goal : latest <= goal) : true;

  return (
    <Card className="flex items-center gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-slate-400">{icon}</span>
          <span className="text-sm font-medium text-white">{label}</span>
          <TrendArrow values={values} higherIsBetter={higherIsBetter} />
          {goal && (
            <span className={cn("text-[10px] ml-auto", atGoal ? "text-emerald-400" : "text-amber-400")}>
              {atGoal ? "✓ Goal met" : `Goal: ${goal}${unit}`}
            </span>
          )}
        </div>
        <div className="flex items-end justify-between gap-2">
          <div>
            <p className={cn("text-2xl font-bold", atGoal ? "text-white" : "text-amber-400")}>
              {latest}{unit}
            </p>
            <p className="text-[10px] text-slate-500">Today · avg {average}{unit}</p>
          </div>
          <div className="flex-shrink-0">
            <Sparkline values={values} color={color} width={140} height={40} />
            <div className="flex justify-between text-[9px] text-slate-600 mt-0.5 w-[140px]">
              <span>{dates[0]}</span>
              <span>{dates[dates.length - 1]}</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
