"use client";

import { useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  PatientSummaryCard,
  HealthMetricCards,
  AlertBanner,
} from "@/components/dashboard/DummyCards";
import { Section } from "@/components/ui/shared";
import { DEMO_PATIENTS, DEMO_HEALTH_METRICS, DEMO_WEEK_SUMMARY } from "@/lib/demo-data";

export default function DashboardPage() {
  const [patientId, setPatientId] = useState("pat-1");
  const metric = DEMO_HEALTH_METRICS.find((m) => m.patientId === patientId)!;

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6 animate-fade-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Dashboard</h1>
          <p className="text-xs text-slate-500 mt-0.5">Personal health overview</p>
        </div>
        <select
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
          className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-1.5"
        >
          {DEMO_PATIENTS.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {/* Alert banner */}
      <AlertBanner patientId={patientId} />

      {/* Patient summary card */}
      <Section title="Patient Overview">
        <PatientSummaryCard patientId={patientId} />
      </Section>

      {/* Health metrics */}
      {metric && (
        <Section title="Today's Health Metrics" subtitle={metric.date}>
          <HealthMetricCards metric={metric} />
        </Section>
      )}

      {/* Week 5: week-at-a-glance */}
      {patientId === "pat-1" && (
        <Section
          title="This Week at a Glance"
          subtitle={DEMO_WEEK_SUMMARY.weekLabel}
          action={
            <a href="/trends" className="text-xs text-blue-400 hover:text-blue-300">
              Full trends →
            </a>
          }
        >
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-3">
            <div className="flex items-center gap-2">
              {DEMO_WEEK_SUMMARY.trend === "improving" ? (
                <TrendingUp size={14} className="text-emerald-400" />
              ) : DEMO_WEEK_SUMMARY.trend === "declining" ? (
                <TrendingDown size={14} className="text-red-400" />
              ) : (
                <Minus size={14} className="text-slate-400" />
              )}
              <span
                className={`text-sm font-semibold ${
                  DEMO_WEEK_SUMMARY.trend === "improving"
                    ? "text-emerald-400"
                    : DEMO_WEEK_SUMMARY.trend === "declining"
                    ? "text-red-400"
                    : "text-slate-400"
                }`}
              >
                {DEMO_WEEK_SUMMARY.trend.charAt(0).toUpperCase() + DEMO_WEEK_SUMMARY.trend.slice(1)}
              </span>
              <span className="text-xs text-slate-500 ml-auto">
                avg {DEMO_WEEK_SUMMARY.avgSteps.toLocaleString()} steps/day
              </span>
            </div>
            <div className="space-y-1">
              {DEMO_WEEK_SUMMARY.notes.map((n, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-blue-400 text-xs mt-0.5">→</span>
                  <p className="text-xs text-slate-300">{n}</p>
                </div>
              ))}
            </div>
          </div>
        </Section>
      )}

      {/* Quick links */}
      <Section title="Quick Access">
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: "Upload Report", href: "/reports", emoji: "📄" },
            { label: "View Alerts", href: "/alerts", emoji: "⚠️" },
            { label: "Ask AI", href: "/chat", emoji: "💬" },
            { label: "Health Trends", href: "/trends", emoji: "📈" },
          ].map(({ label, href, emoji }) => (
            <a
              key={href}
              href={href}
              className="bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl p-4 flex flex-col gap-2 transition-colors"
            >
              <span className="text-2xl">{emoji}</span>
              <span className="text-sm font-medium text-slate-200">{label}</span>
            </a>
          ))}
        </div>
      </Section>
    </div>
  );
}
