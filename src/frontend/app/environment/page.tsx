/* Week 4 – Environment Info Panel (read-only, Person 5) */
"use client";

import { useState } from "react";
import { Wind, Thermometer, Droplets, AlertTriangle, Info } from "lucide-react";
import { Card, Badge, Section, EmptyState, aqiColor, aqiLabel } from "@/components/ui/shared";
import { DEMO_ENVIRONMENT, DEMO_PATIENTS, EnvironmentContext } from "@/lib/demo-data";

export default function EnvironmentPage() {
  const [patientId, setPatientId] = useState("pat-1");
  const env = DEMO_ENVIRONMENT.find((e) => e.patientId === patientId);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Environmental Context</h1>
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

      {/* Data source note */}
      <div className="flex items-start gap-2 bg-slate-800/60 border border-slate-700 rounded-xl p-3">
        <Info size={14} className="text-blue-400 mt-0.5 flex-shrink-0" />
        <p className="text-xs text-slate-400">
          Environmental data is fetched daily via <strong className="text-slate-300">Weather API</strong> and{" "}
          <strong className="text-slate-300">AQI API</strong> using the patient's coarse location (city/pincode).
          This data enriches the Rules Engine and AI context — it is <em>never</em> used to diagnose.
        </p>
      </div>

      {!env ? (
        <EmptyState message="No environmental data for this patient." icon={<Wind />} />
      ) : (
        <>
          {/* Active flags */}
          {(env.heatwave || env.poorAir) && (
            <Section title="Active Flags">
              <div className="flex flex-wrap gap-2">
                {env.heatwave && (
                  <FlagCard
                    emoji="🌡"
                    label="Heatwave Active"
                    desc={`Max temp ${env.temperature.max}°C in ${env.city}`}
                    color="red"
                  />
                )}
                {env.poorAir && (
                  <FlagCard
                    emoji="💨"
                    label="Poor Air Quality"
                    desc={`AQI ${env.aqi} — ${aqiLabel(env.aqi)}`}
                    color="amber"
                  />
                )}
              </div>
            </Section>
          )}

          {/* Weather */}
          <Section title="Weather" subtitle={`${env.city} · ${env.date} · ${env.season.charAt(0).toUpperCase() + env.season.slice(1)}`}>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <MetricTile
                icon={<Thermometer size={16} />}
                label="Avg Temperature"
                value={`${env.temperature.avg}°C`}
                sub={`${env.temperature.min}°–${env.temperature.max}°C`}
                warn={env.temperature.max > 37}
              />
              <MetricTile
                icon={<Droplets size={16} />}
                label="Humidity"
                value={`${env.humidity}%`}
                warn={env.humidity > 75}
              />
              <MetricTile
                icon={<Wind size={16} />}
                label="Season"
                value={env.season.charAt(0).toUpperCase() + env.season.slice(1)}
              />
            </div>
          </Section>

          {/* Air Quality */}
          <Section title="Air Quality Index">
            <Card>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className={`text-3xl font-bold ${aqiColor(env.aqi)}`}>{env.aqi}</p>
                  <p className="text-xs text-slate-400">{aqiLabel(env.aqi)}</p>
                </div>
                <AqiGauge aqi={env.aqi} />
              </div>
              <div className="grid grid-cols-2 gap-3 border-t border-slate-700 pt-3">
                <div>
                  <p className="text-xs text-slate-400">PM2.5</p>
                  <p className={`text-lg font-semibold ${env.pm25 > 60 ? "text-red-400" : env.pm25 > 35 ? "text-amber-400" : "text-emerald-400"}`}>
                    {env.pm25} <span className="text-xs">µg/m³</span>
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">PM10</p>
                  <p className={`text-lg font-semibold ${env.pm10 > 100 ? "text-red-400" : env.pm10 > 54 ? "text-amber-400" : "text-emerald-400"}`}>
                    {env.pm10} <span className="text-xs">µg/m³</span>
                  </p>
                </div>
              </div>
            </Card>
          </Section>

          {/* Context injection preview */}
          <Section title="AI Context Injection Preview" subtitle="What the Rules Engine sees">
            <Card className="font-mono text-xs text-emerald-300 space-y-1 bg-slate-900">
              <p className="text-slate-500">{"// environment_context object"}</p>
              <p>{`city: "${env.city}"`}</p>
              <p>{`temperature_avg: ${env.temperature.avg}°C`}</p>
              <p>{`humidity: ${env.humidity}%`}</p>
              <p>{`aqi: ${env.aqi} (${aqiLabel(env.aqi)})`}</p>
              <p>{`pm25: ${env.pm25} µg/m³`}</p>
              <p>{`season: "${env.season}"`}</p>
              <p>{`flags: [${[env.heatwave ? '"heatwave"' : null, env.poorAir ? '"poor_air"' : null].filter(Boolean).join(", ") || "none"}]`}</p>
            </Card>
          </Section>
        </>
      )}
    </div>
  );
}

function MetricTile({
  icon,
  label,
  value,
  sub,
  warn,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  warn?: boolean;
}) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-3 space-y-1">
      <div className="flex items-center gap-1.5 text-slate-400">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <p className={`text-xl font-bold ${warn ? "text-amber-400" : "text-white"}`}>{value}</p>
      {sub && <p className="text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

function FlagCard({ emoji, label, desc, color }: { emoji: string; label: string; desc: string; color: "red" | "amber" }) {
  return (
    <div className={`flex items-start gap-3 p-3 rounded-xl border flex-1 min-w-[200px]
      ${color === "red" ? "bg-red-900/20 border-red-700/40" : "bg-amber-900/20 border-amber-700/40"}`}>
      <span className="text-xl">{emoji}</span>
      <div>
        <p className={`text-sm font-semibold ${color === "red" ? "text-red-300" : "text-amber-300"}`}>{label}</p>
        <p className="text-xs text-slate-400">{desc}</p>
      </div>
    </div>
  );
}

function AqiGauge({ aqi }: { aqi: number }) {
  const pct = Math.min((aqi / 300) * 100, 100);
  const col = aqi <= 50 ? "#10b981" : aqi <= 100 ? "#f59e0b" : aqi <= 150 ? "#f97316" : "#ef4444";
  return (
    <div className="flex flex-col items-end gap-1">
      <div className="h-3 w-24 bg-slate-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: col }} />
      </div>
      <p className="text-[10px] text-slate-500">0 — 300</p>
    </div>
  );
}
