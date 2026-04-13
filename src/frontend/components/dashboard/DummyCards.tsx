/* Week 1 – Dummy UI cards (static, no API) + placeholder charts */
import {
  Activity,
  Moon,
  Heart,
  Footprints,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
} from "lucide-react";
import { Card, StatCard, SeverityBadge, Badge, Section } from "@/components/ui/shared";
import { cn } from "@/lib/utils";
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
          {env.heatwave && <Badge variant="danger">Heatwave</Badge>}
          {env.poorAir && <Badge variant="warning">Poor Air</Badge>}
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

// ── Placeholder Bar Chart ────────────────────
/**
 * Generic static bar chart — no charting library needed.
 * Pass an array of { label, value } and an optional target line.
 */
export function PlaceholderBarChart({
  title,
  data,
  target,
  unit = "",
  color = "bg-blue-500",
  warnColor = "bg-amber-500",
  height = 80,
}: {
  title: string;
  data: { label: string; value: number }[];
  target?: number;
  unit?: string;
  color?: string;
  warnColor?: string;
  height?: number;
}) {
  const max = Math.max(...data.map((d) => d.value), target ?? 0) || 1;
  return (
    <Card className="space-y-3">
      <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide">{title}</p>
      <div className="flex items-end gap-1" style={{ height }}>
        {data.map((d, i) => {
          const pct = (d.value / max) * 100;
          const isWarn = target !== undefined && d.value < target;
          return (
            <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
              <span className="text-[9px] text-slate-400 font-medium">
                {d.value}{unit}
              </span>
              <div className="w-full flex flex-col justify-end" style={{ height: height - 18 }}>
                <div
                  className={cn("w-full rounded-t-sm", isWarn ? warnColor : color, "opacity-80")}
                  style={{ height: `${Math.max(pct, 6)}%` }}
                />
              </div>
              <span className="text-[9px] text-slate-500 truncate w-full text-center">{d.label}</span>
            </div>
          );
        })}
      </div>
      {target !== undefined && (
        <p className="text-[10px] text-slate-500">
          Target: <span className="text-white">{target}{unit}</span>
          {" · "}{data.filter((d) => d.value >= target).length}/{data.length} days met
        </p>
      )}
    </Card>
  );
}

// ── Summary Tile (labelled KPI card) ─────────
export function SummaryTile({
  label,
  value,
  sub,
  trend,
  trendGoodUp = true,
  accent = "blue",
}: {
  label: string;
  value: string | number;
  sub?: string;
  trend?: "up" | "down" | "flat";
  trendGoodUp?: boolean;
  accent?: "blue" | "emerald" | "rose" | "amber" | "purple";
}) {
  const accentMap: Record<string, string> = {
    blue:    "border-blue-700/40 bg-blue-950/30",
    emerald: "border-emerald-700/40 bg-emerald-950/30",
    rose:    "border-rose-700/40 bg-rose-950/30",
    amber:   "border-amber-700/40 bg-amber-950/30",
    purple:  "border-purple-700/40 bg-purple-950/30",
  };
  const trendGood = trend === "up" ? trendGoodUp : !trendGoodUp;
  const trendIcon = trend === "up" ? (
    <TrendingUp size={13} className={trendGood ? "text-emerald-400" : "text-red-400"} />
  ) : trend === "down" ? (
    <TrendingDown size={13} className={trendGood ? "text-emerald-400" : "text-red-400"} />
  ) : null;

  return (
    <div className={cn("rounded-2xl border p-4 space-y-1", accentMap[accent])}>
      <p className="text-[10px] text-slate-400 uppercase tracking-wider font-medium">{label}</p>
      <div className="flex items-center gap-2">
        <p className="text-2xl font-bold text-white stat-value">{value}</p>
        {trendIcon}
      </div>
      {sub && <p className="text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

// ── Placeholder Donut (AQI / % gauge) ────────
export function PlaceholderDonut({
  label,
  value,
  max,
  color,
  unit = "%",
}: {
  label: string;
  value: number;
  max: number;
  color: string;
  unit?: string;
}) {
  const r = 28;
  const circ = 2 * Math.PI * r;
  const filled = Math.min(value / max, 1) * circ;

  return (
    <Card className="flex flex-col items-center gap-2 py-3">
      <svg width={72} height={72} viewBox="0 0 72 72">
        <circle cx={36} cy={36} r={r} fill="none" stroke="#1e293b" strokeWidth={8} />
        <circle
          cx={36} cy={36} r={r}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeDasharray={`${filled} ${circ}`}
          strokeLinecap="round"
          transform="rotate(-90 36 36)"
        />
        <text x={36} y={40} textAnchor="middle" fontSize={13} fontWeight="bold" fill="white">
          {value}
        </text>
      </svg>
      <p className="text-xs text-slate-400 font-medium">{label}</p>
      <p className="text-[10px] text-slate-500">max {max}{unit}</p>
    </Card>
  );
}

// ── Placeholder Line Sparkline ────────────────
export function SparkLine({
  label,
  data,
  color = "#3b82f6",
}: {
  label: string;
  data: number[];
  color?: string;
}) {
  const w = 120, h = 40;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pts = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * (h - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <Card className="space-y-1">
      <p className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">{label}</p>
      <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ height: 40 }}>
        <polyline points={pts} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </Card>
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
      <AlertTriangle size={16} className="text-red-400 mt-0.5 flex-shrink-0" />
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
