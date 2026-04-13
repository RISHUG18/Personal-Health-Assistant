/* Trends page — health metric charts (static sparklines, no deps) */
"use client";

import { useState } from "react";
import { Section, Card, StatCard, Badge } from "@/components/ui/shared";
import { DEMO_HEALTH_METRICS, DEMO_TRENDS, DEMO_PATIENTS } from "@/lib/demo-data";
import {
  Footprints,
  Moon,
  Heart,
  Activity,
  Wind,
  FlaskConical,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

type Metric = "steps" | "sleepHours" | "heartRateAvg";

export default function TrendsPage() {
  const [patientId, setPatientId] = useState("pat-1");
  const metrics = DEMO_HEALTH_METRICS.filter((m) => m.patientId === patientId).sort(
    (a, b) => a.date.localeCompare(b.date)
  );

  const avg = (key: Metric) =>
    Math.round(metrics.reduce((s, m) => s + m[key], 0) / metrics.length);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Trends</h1>
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

      {/* Averages summary */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Avg Steps (7d)" value={avg("steps").toLocaleString()} icon={<Footprints size={16} />} />
        <StatCard label="Avg Sleep (7d)" value={`${avg("sleepHours")}h`} icon={<Moon size={16} />} />
        <StatCard label="Avg HR (7d)" value={`${avg("heartRateAvg")} bpm`} icon={<Heart size={16} />} />
      </div>

      {/* Charts */}
      <Section title="Steps (7 days)">
        <SparkChart
          data={metrics.map((m) => ({ date: m.date, value: m.steps }))}
          target={10000}
          formatVal={(v) => v.toLocaleString()}
          color="text-blue-400"
          barColor="bg-blue-500"
        />
      </Section>

      <Section title="Sleep (7 days)">
        <SparkChart
          data={metrics.map((m) => ({ date: m.date, value: m.sleepHours }))}
          target={7}
          formatVal={(v) => `${v}h`}
          color="text-purple-400"
          barColor="bg-purple-500"
          warnBelow
        />
      </Section>

      <Section title="Heart Rate (7 days)">
        <SparkChart
          data={metrics.map((m) => ({ date: m.date, value: m.heartRateAvg }))}
          formatVal={(v) => `${v}`}
          color="text-rose-400"
          barColor="bg-rose-500"
        />
      </Section>

      {/* Trend notes */}
      <Section title="Observations">
        <div className="space-y-2">
          {DEMO_TRENDS.map((t, i) => (
            <Card key={i} className="flex items-start gap-3">
              <span className="text-slate-400 mt-0.5">{catIcon(t.category)}</span>
              <div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px]">{t.date}</Badge>
                  <Badge variant="default" className="text-[10px] capitalize">{t.category}</Badge>
                </div>
                <p className="text-xs text-slate-300 mt-1">{t.note}</p>
              </div>
            </Card>
          ))}
        </div>
      </Section>
    </div>
  );
}

function catIcon(cat: string) {
  if (cat === "lab") return <FlaskConical size={16} />;
  if (cat === "sleep") return <Moon size={16} />;
  if (cat === "activity") return <Activity size={16} />;
  if (cat === "environment") return <Wind size={16} />;
  return <TrendingUp size={16} />;
}

function SparkChart({
  data,
  target,
  formatVal,
  color,
  barColor,
  warnBelow = false,
}: {
  data: { date: string; value: number }[];
  target?: number;
  formatVal: (v: number) => string;
  color: string;
  barColor: string;
  warnBelow?: boolean;
}) {
  const max = Math.max(...data.map((d) => d.value));
  const min = Math.min(...data.map((d) => d.value));
  const range = max - min || 1;

  return (
    <Card className="space-y-4">
      {/* Bar chart */}
      <div className="flex items-end gap-1.5 h-24">
        {data.map((d, i) => {
          const pct = ((d.value - min) / range) * 100;
          const belowTarget = target !== undefined && d.value < target;
          const day = new Date(d.date).toLocaleDateString("en-IN", { weekday: "short" });
          return (
            <div key={i} className="flex-1 flex flex-col items-center gap-1">
              <span className={cn("text-[10px] font-bold", color)}>{formatVal(d.value)}</span>
              <div className="w-full flex flex-col justify-end" style={{ height: "64px" }}>
                <div
                  className={cn(
                    "w-full rounded-t-sm transition-all",
                    warnBelow && belowTarget ? "bg-amber-500/70" : `${barColor}/70`
                  )}
                  style={{ height: `${Math.max(pct, 8)}%` }}
                />
              </div>
              <span className="text-[9px] text-slate-500">{day}</span>
            </div>
          );
        })}
      </div>

      {/* Target line note */}
      {target !== undefined && (
        <p className="text-xs text-slate-500">
          Target: <span className={color}>{formatVal(target)}</span>
          {" · "}
          {data.filter((d) => d.value >= target).length}/{data.length} days met
        </p>
      )}
    </Card>
  );
}
