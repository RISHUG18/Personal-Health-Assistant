/* Dashboard page — main user view */
import { PatientSummaryCard, HealthMetricCards, AlertBanner } from "@/components/dashboard/DummyCards";
import { Section, StatCard } from "@/components/ui/shared";
import { DEMO_HEALTH_METRICS, DEMO_WEEK_SUMMARY } from "@/lib/demo-data";
import { TrendingDown, TrendingUp, Minus, Activity, Zap } from "lucide-react";

export default function DashboardPage() {
  const todayMetric = DEMO_HEALTH_METRICS.find((m) => m.patientId === "pat-1" && m.date === "2026-03-05")!;
  const ws = DEMO_WEEK_SUMMARY;

  const trendIcon =
    ws.trend === "improving" ? (
      <TrendingUp size={16} className="text-emerald-400" />
    ) : ws.trend === "declining" ? (
      <TrendingDown size={16} className="text-red-400" />
    ) : (
      <Minus size={16} className="text-slate-400" />
    );

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Good morning, Riya</h1>
          <p className="text-xs text-slate-400 mt-0.5">Thursday, 5 March 2026</p>
        </div>
        <div className="flex items-center gap-1.5 text-xs bg-slate-800 border border-slate-700 rounded-xl px-3 py-1.5">
          {trendIcon}
          <span className="text-slate-300 capitalize">{ws.trend}</span>
        </div>
      </div>

      {/* Alert banner */}
      <AlertBanner patientId="pat-1" />

      {/* Patient summary card */}
      <Section title="Your Profile">
        <PatientSummaryCard patientId="pat-1" />
      </Section>

      {/* Today's metrics */}
      <Section title="Today" subtitle="Synced from Health Connect">
        <HealthMetricCards metric={todayMetric} />
      </Section>

      {/* Week summary */}
      <Section title="This Week" subtitle={ws.weekLabel}>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <StatCard
            label="Avg Steps"
            value={ws.avgSteps.toLocaleString()}
            icon={<Activity size={16} />}
            trend={ws.avgSteps >= 7000 ? "up" : "down"}
            trendBad={ws.avgSteps < 7000}
          />
          <StatCard
            label="Avg Sleep"
            value={`${ws.avgSleepHours}h`}
            trend={ws.avgSleepHours >= 7 ? "up" : "down"}
            trendBad={ws.avgSleepHours < 7}
          />
          <StatCard
            label="Avg HR"
            value={`${ws.avgHeartRate} bpm`}
          />
          <StatCard
            label="Active Alerts"
            value={ws.totalActiveAlerts}
            icon={<Zap size={16} />}
            trend={ws.totalActiveAlerts === 0 ? "up" : "down"}
            trendBad={ws.totalActiveAlerts > 0}
          />
          <StatCard
            label="Lab Flags"
            value={ws.labFlags}
            trend={ws.labFlags === 0 ? "up" : "down"}
            trendBad={ws.labFlags > 0}
          />
        </div>

        {/* Trend notes */}
        <div className="mt-3 space-y-2">
          {ws.notes.map((note, i) => (
            <div
              key={i}
              className="flex items-start gap-2 bg-slate-800/60 border border-slate-700/60 rounded-xl px-3 py-2"
            >
              <span className="text-blue-400 text-xs mt-0.5">→</span>
              <p className="text-xs text-slate-300">{note}</p>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}
