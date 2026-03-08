/* Week 1 – Dummy UI cards (static, no API) */
import { Activity, Droplets, Moon, Heart, Footprints } from "lucide-react";
import { Card, StatCard, SeverityBadge, Badge, Section } from "@/components/ui/shared";
import {
  DEMO_PATIENTS,
  DEMO_HEALTH_METRICS,
  DEMO_ALERTS,
  DEMO_ENVIRONMENT,
  HealthMetric,
} from "@/lib/demo-data";

export function PatientSummaryCard({ patientId = "pat-1" }: { patientId?: string }) {
  const patient = DEMO_PATIENTS.find((p) => p.id === patientId)!;
  const metric = DEMO_HEALTH_METRICS.find((m) => m.patientId === patientId);
  const env = DEMO_ENVIRONMENT.find((e) => e.patientId === patientId);
  const activeAlerts = DEMO_ALERTS.filter(
    (a) => a.patientId === patientId && !a.acknowledged
  );

  return (
    <Card className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
          {patient.name[0]}
        </div>
        <div>
          <p className="font-semibold text-white">{patient.name}</p>
          <p className="text-xs text-slate-400">
            {patient.age}y · {patient.gender} · {patient.bloodGroup}
          </p>
        </div>
        {activeAlerts.length > 0 && (
          <Badge variant="danger" className="ml-auto">
            {activeAlerts.length} alert{activeAlerts.length > 1 ? "s" : ""}
          </Badge>
        )}
      </div>

      {metric && (
        <div className="grid grid-cols-3 gap-2 mt-2">
          <MiniStat icon={<Footprints size={12} />} label="Steps" value={metric.steps.toLocaleString()} />
          <MiniStat icon={<Moon size={12} />} label="Sleep" value={`${metric.sleepHours}h`} warn={metric.sleepHours < 6} />
          <MiniStat icon={<Heart size={12} />} label="HR Avg" value={`${metric.heartRateAvg} bpm`} />
        </div>
      )}

      {env && (
        <div className="flex flex-wrap gap-2 pt-1">
          {env.heatwave && <Badge variant="danger">🌡 Heatwave</Badge>}
          {env.poorAir && <Badge variant="warning">💨 Poor Air</Badge>}
          <Badge variant="outline">{env.city}</Badge>
          <Badge variant="outline">AQI {env.aqi}</Badge>
        </div>
      )}
    </Card>
  );
}

function MiniStat({
  icon,
  label,
  value,
  warn,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  warn?: boolean;
}) {
  return (
    <div className="bg-slate-700/50 rounded-lg p-2 text-center">
      <div className="flex justify-center text-slate-400 mb-0.5">{icon}</div>
      <p className={`text-sm font-semibold ${warn ? "text-amber-400" : "text-white"}`}>{value}</p>
      <p className="text-[10px] text-slate-500">{label}</p>
    </div>
  );
}

// ── Health Metrics Row ────────────────────────
export function HealthMetricCards({ metric }: { metric: HealthMetric }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <StatCard
        label="Steps Today"
        value={metric.steps.toLocaleString()}
        icon={<Footprints size={16} />}
        trend={metric.steps >= 6000 ? "up" : "down"}
      />
      <StatCard
        label="Sleep"
        value={`${metric.sleepHours}h`}
        icon={<Moon size={16} />}
        trend={metric.sleepHours >= 7 ? "up" : "down"}
        trendBad={metric.sleepHours < 7}
      />
      <StatCard
        label="Heart Rate"
        value={`${metric.heartRateAvg} bpm`}
        icon={<Heart size={16} />}
      />
      <StatCard
        label="Activity"
        value={metric.steps >= 6000 ? "Active" : "Low"}
        icon={<Activity size={16} />}
        sub={metric.steps >= 10000 ? "Goal met!" : `${10000 - metric.steps} to goal`}
      />
    </div>
  );
}

// ── Quick Alert Banner ────────────────────────
export function AlertBanner({ patientId = "pat-1" }: { patientId?: string }) {
  const alerts = DEMO_ALERTS.filter(
    (a) => a.patientId === patientId && !a.acknowledged
  ).slice(0, 1);

  if (alerts.length === 0) return null;
  const alert = alerts[0];

  return (
    <div className="bg-red-900/30 border border-red-700/50 rounded-xl p-3 flex items-start gap-3">
      <span className="text-red-400 mt-0.5">⚠</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold text-red-300">{alert.title}</p>
          <SeverityBadge severity={alert.severity} />
        </div>
        <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{alert.reason}</p>
      </div>
    </div>
  );
}
