/**
 * EnvironmentPanel — reusable environment info component.
 *
 * Usage (user view):   <EnvironmentPanel env={env} />
 * Usage (doctor view): <EnvironmentPanel env={env} compact />
 *
 * Shows AQI (with colour-coded visual indicator), temperature, humidity,
 * an AQI scale legend, and optional advisory banners.
 */
"use client";

import { useState } from "react";
import {
  Wind, Thermometer, Droplets, AlertTriangle,
  CheckCircle2, Info, ChevronDown, ChevronUp,
} from "lucide-react";
import { Card, Badge } from "@/components/ui/shared";
import { EnvironmentContext } from "@/lib/demo-data";
import { cn } from "@/lib/utils";

// ─────────────────────────────────────────────────────────────────
// AQI helpers (self-contained so the component is portable)
// ─────────────────────────────────────────────────────────────────

export type AqiLevel = "good" | "moderate" | "sensitive" | "unhealthy" | "very-bad";

export function getAqiLevel(aqi: number): AqiLevel {
  if (aqi <= 50)  return "good";
  if (aqi <= 100) return "moderate";
  if (aqi <= 150) return "sensitive";
  if (aqi <= 200) return "unhealthy";
  return "very-bad";
}

export const AQI_META: Record<AqiLevel, {
  label: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
  barColor: string;
  icon: JSX.Element;
  advice: string;
}> = {
  "good": {
    label: "Good",
    textColor: "text-emerald-400",
    bgColor: "bg-emerald-500/15",
    borderColor: "border-emerald-500/40",
    barColor: "bg-emerald-500",
    icon: <CheckCircle2 size={18} className="text-emerald-400" />,
    advice: "Air quality is satisfactory. Outdoor activities are safe.",
  },
  "moderate": {
    label: "Moderate",
    textColor: "text-yellow-400",
    bgColor: "bg-yellow-500/15",
    borderColor: "border-yellow-500/40",
    barColor: "bg-yellow-500",
    icon: <Info size={18} className="text-yellow-400" />,
    advice: "Acceptable quality. Sensitive individuals should limit prolonged outdoor exertion.",
  },
  "sensitive": {
    label: "Unhealthy (Sensitive)",
    textColor: "text-orange-400",
    bgColor: "bg-orange-500/15",
    borderColor: "border-orange-500/40",
    barColor: "bg-orange-500",
    icon: <AlertTriangle size={18} className="text-orange-400" />,
    advice: "People with respiratory or heart conditions should reduce outdoor activity.",
  },
  "unhealthy": {
    label: "Unhealthy",
    textColor: "text-red-400",
    bgColor: "bg-red-500/15",
    borderColor: "border-red-500/40",
    barColor: "bg-red-500",
    icon: <AlertTriangle size={18} className="text-red-400" />,
    advice: "Everyone may begin to experience health effects. Limit outdoor activity. Use N95 if going out.",
  },
  "very-bad": {
    label: "Very Unhealthy",
    textColor: "text-purple-400",
    bgColor: "bg-purple-600/15",
    borderColor: "border-purple-600/40",
    barColor: "bg-purple-600",
    icon: <AlertTriangle size={18} className="text-purple-400" />,
    advice: "Health warnings for everyone. Avoid outdoor activity. Keep windows closed.",
  },
};

const AQI_BANDS = [
  { max: 50,  level: "good"      as AqiLevel },
  { max: 100, level: "moderate"  as AqiLevel },
  { max: 150, level: "sensitive" as AqiLevel },
  { max: 200, level: "unhealthy" as AqiLevel },
  { max: 300, level: "very-bad"  as AqiLevel },
];

// ─────────────────────────────────────────────────────────────────
// Temperature helpers
// ─────────────────────────────────────────────────────────────────
function tempColor(avg: number) {
  if (avg >= 40) return "text-red-400";
  if (avg >= 35) return "text-orange-400";
  if (avg >= 28) return "text-yellow-400";
  return "text-blue-300";
}
function tempLabel(avg: number, max: number) {
  if (max >= 42) return { text: "Extreme Heat", variant: "danger" as const };
  if (avg >= 35) return { text: "Heatwave", variant: "danger" as const };
  if (avg >= 28) return { text: "Warm", variant: "warning" as const };
  return null;
}

// ─────────────────────────────────────────────────────────────────
// Humidity helpers
// ─────────────────────────────────────────────────────────────────
function humidityColor(h: number) {
  if (h >= 80) return "text-cyan-300";
  if (h >= 60) return "text-blue-300";
  return "text-slate-200";
}
function humidityLabel(h: number) {
  if (h >= 80) return "Very humid";
  if (h >= 60) return "Comfortable";
  return "Dry";
}

// ─────────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────────
interface EnvironmentPanelProps {
  env: EnvironmentContext;
  /** Compact mode for doctor view — hides scale legend and tooltips */
  compact?: boolean;
  /** Show the Gemini demo scenario section */
  showScenario?: boolean;
}

export function EnvironmentPanel({
  env,
  compact = false,
  showScenario = false,
}: EnvironmentPanelProps) {
  const level = getAqiLevel(env.aqi);
  const meta  = AQI_META[level];
  const tLabel = tempLabel(env.temperature.avg, env.temperature.max);

  return (
    <div className="space-y-4">
      {/* ── Summary banner ─────────────────────── */}
      <div
        className={cn(
          "rounded-2xl border p-4 flex items-start gap-4",
          meta.bgColor, meta.borderColor
        )}
      >
        <span className="mt-0.5 flex-shrink-0">{meta.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <p className="font-semibold text-white">{env.city}</p>
            <span className="text-[10px] text-slate-400">{env.date}</span>
            <Badge variant="outline" className="text-[10px] capitalize">{env.season}</Badge>
          </div>
          <p className={cn("text-sm font-medium", meta.textColor)}>
            Air Quality: {meta.label}
          </p>
          <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{meta.advice}</p>
          {/* Advisory badges */}
          <div className="flex gap-2 mt-2 flex-wrap">
            {env.heatwave && <Badge variant="danger">Heatwave Active</Badge>}
            {env.poorAir  && <Badge variant="warning">Poor Air Quality</Badge>}
            {!env.heatwave && !env.poorAir && (
              <Badge variant="success">Conditions Normal</Badge>
            )}
          </div>
        </div>
      </div>

      {/* ── Metric grid ────────────────────────── */}
      <div className="grid grid-cols-3 gap-3">
        {/* AQI tile */}
        <AqiTile aqi={env.aqi} pm25={env.pm25} pm10={env.pm10} level={level} meta={meta} />

        {/* Temperature tile */}
        <Card className="space-y-1.5">
          <div className="flex items-center gap-1.5">
            <Thermometer size={13} className="text-slate-400 flex-shrink-0" />
            <span className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">Temp</span>
          </div>
          <p className={cn("text-2xl font-bold stat-value", tempColor(env.temperature.avg))}>
            {env.temperature.avg}°C
          </p>
          <p className="text-[10px] text-slate-500">
            {env.temperature.min}° – {env.temperature.max}°
          </p>
          {tLabel && <Badge variant={tLabel.variant} className="text-[10px]">{tLabel.text}</Badge>}
        </Card>

        {/* Humidity tile */}
        <Card className="space-y-1.5">
          <div className="flex items-center gap-1.5">
            <Droplets size={13} className="text-slate-400 flex-shrink-0" />
            <span className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">Humidity</span>
          </div>
          <p className={cn("text-2xl font-bold stat-value", humidityColor(env.humidity))}>
            {env.humidity}%
          </p>
          <p className="text-[10px] text-slate-500">{humidityLabel(env.humidity)}</p>
          <HumidityBar value={env.humidity} />
        </Card>
      </div>

      {/* ── AQI visual scale ──────────────────── */}
      {!compact && <AqiScale current={env.aqi} level={level} />}

      {/* ── Demo scenario ────────────────────── */}
      {showScenario && (
        <DemoScenarioPanel env={env} level={level} />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// AQI tile — prominent colour-coded block
// ─────────────────────────────────────────────────────────────────
function AqiTile({
  aqi, pm25, pm10, level, meta,
}: {
  aqi: number;
  pm25: number;
  pm10: number;
  level: AqiLevel;
  meta: typeof AQI_META[AqiLevel];
}) {
  // Gauge: arc-like segmented bar
  const pct = Math.min(aqi / 300, 1);

  return (
    <Card className={cn("space-y-1.5 border", meta.borderColor)}>
      <div className="flex items-center gap-1.5">
        <Wind size={13} className="text-slate-400 flex-shrink-0" />
        <span className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">AQI</span>
      </div>
      <p className={cn("text-2xl font-bold stat-value", meta.textColor)}>{aqi}</p>
      {/* Filled progress bar */}
      <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", meta.barColor)}
          style={{ width: `${pct * 100}%` }}
        />
      </div>
      <span
        className={cn(
          "inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border",
          meta.bgColor, meta.borderColor, meta.textColor
        )}
      >
        {meta.label}
      </span>
      <p className="text-[10px] text-slate-500">
        PM2.5: {pm25} · PM10: {pm10}
      </p>
    </Card>
  );
}

// ─────────────────────────────────────────────────────────────────
// Humidity mini bar
// ─────────────────────────────────────────────────────────────────
function HumidityBar({ value }: { value: number }) {
  const color =
    value >= 80 ? "bg-cyan-400" : value >= 60 ? "bg-blue-400" : "bg-slate-400";
  return (
    <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
      <div
        className={cn("h-full rounded-full transition-all", color)}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// AQI Scale legend
// ─────────────────────────────────────────────────────────────────
function AqiScale({ current, level }: { current: number; level: AqiLevel }) {
  return (
    <Card>
      <p className="text-xs font-medium text-slate-400 mb-3">AQI Visual Scale</p>
      {/* Segmented colour bar */}
      <div className="flex gap-0.5 h-3 rounded-full overflow-hidden">
        {AQI_BANDS.map((b) => (
          <div
            key={b.level}
            className={cn(
              "flex-1 transition-opacity",
              AQI_META[b.level].barColor,
              b.level === level ? "opacity-100" : "opacity-30"
            )}
          />
        ))}
      </div>
      {/* Labels */}
      <div className="flex mt-1.5 gap-0.5">
        {AQI_BANDS.map((b) => (
          <div key={b.level} className="flex-1 text-center">
            <p
              className={cn(
                "text-[9px] font-medium",
                b.level === level ? AQI_META[b.level].textColor : "text-slate-600"
              )}
            >
              {AQI_META[b.level].label.split(" ")[0]}
            </p>
          </div>
        ))}
      </div>
      {/* Current marker line */}
      <div className="mt-2 flex items-center gap-2">
        <div
          className={cn("h-2 w-2 rounded-full flex-shrink-0", AQI_META[level].barColor)}
        />
        <p className="text-xs text-slate-400">
          Current:{" "}
          <span className={cn("font-bold", AQI_META[level].textColor)}>{current}</span>
          {" — "}{AQI_META[level].label}
        </p>
      </div>
    </Card>
  );
}

// ─────────────────────────────────────────────────────────────────
// Demo Scenario Panel
// ─────────────────────────────────────────────────────────────────

const DEMO_SCENARIOS = [
  {
    id: "sc-1",
    title: "High AQI + Anaemia",
    condition: (env: EnvironmentContext) => env.aqi > 100 && env.poorAir,
    severity: "critical" as const,
    alertTriggered: "Outdoor activity risk — critical",
    geminiExplanation:
      "Riya\u2019s haemoglobin is already low at 9.8\u00a0g/dL (iron-deficiency anaemia). " +
      "When AQI exceeds 100, airborne PM2.5 particles enter the bloodstream and compete with " +
      "oxygen transport, which is already impaired. This combination can trigger dizziness, " +
      "shortness of breath, and fainting even during light activity. " +
      "Alert severity has been escalated from Medium to Critical.",
    citations: [
      "Environment \u00b7 Chennai AQI\u00a0168 \u00b7 PM2.5\u00a078\u00a0\u00b5g/m\u00b3",
      "CBC_Report_Jan2026.pdf \u00b7 Hb\u00a0=\u00a09.8\u00a0g/dL",
    ],
  },
  {
    id: "sc-2",
    title: "Heatwave + Poor Sleep",
    condition: (env: EnvironmentContext) => env.heatwave,
    severity: "high" as const,
    alertTriggered: "Sleep disruption risk \u2014 high",
    geminiExplanation:
      "Ambient temperatures above 35\u00a0\u00b0C prevent the body from lowering its core temperature, " +
      "which is required to initiate deep sleep. Riya\u2019s current average sleep is 5.6\u00a0h \u2014 " +
      "already below the 7\u20139\u00a0h target. The active heatwave (max " +
      "41\u00a0\u00b0C) will likely reduce this further and worsen fatigue associated with her anaemia. " +
      "Recommend: fan/AC at night, hydration, and avoiding heavy meals after 8\u00a0PM.",
    citations: [
      "Environment \u00b7 Chennai max\u00a041\u00a0\u00b0C \u00b7 Heatwave advisory",
      "Wearable data \u00b7 7-day avg sleep\u00a0=\u00a05.6\u00a0h",
    ],
  },
  {
    id: "sc-3",
    title: "Good AQI — No Advisory",
    condition: (env: EnvironmentContext) => !env.poorAir && !env.heatwave,
    severity: "low" as const,
    alertTriggered: "No environment-triggered alerts",
    geminiExplanation:
      "Current air quality is within safe limits (AQI\u00a0\u2264\u00a050). " +
      "Temperature and humidity are comfortable. " +
      "No environment-related advisory is needed today. " +
      "Outdoor moderate exercise is safe; this is a good opportunity to improve step count and sleep quality.",
    citations: [
      "Environment \u00b7 AQI good range",
    ],
  },
];

const SEVERITY_STYLE = {
  critical: "bg-red-950/30 border-red-700/50 text-red-300",
  high:     "bg-amber-950/30 border-amber-700/50 text-amber-300",
  medium:   "bg-orange-950/30 border-orange-700/50 text-orange-300",
  low:      "bg-emerald-950/30 border-emerald-700/50 text-emerald-300",
};

function DemoScenarioPanel({
  env,
  level,
}: {
  env: EnvironmentContext;
  level: AqiLevel;
}) {
  const [openId, setOpenId] = useState<string | null>(null);
  const activeScenario = DEMO_SCENARIOS.find((s) => s.condition(env));

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-sm font-semibold text-white">Demo Scenarios</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          How current environmental conditions influence alerts and AI explanations.
        </p>
      </div>

      {/* Active scenario highlight */}
      {activeScenario && (
        <div
          className={cn(
            "rounded-2xl border p-4 space-y-2",
            SEVERITY_STYLE[activeScenario.severity]
          )}
        >
          <div className="flex items-center gap-2">
            <AlertTriangle size={14} className="flex-shrink-0" />
            <p className="text-xs font-bold uppercase tracking-wide">
              Active Scenario
            </p>
            <span className="ml-auto text-[10px] opacity-70">{activeScenario.title}</span>
          </div>
          <p className="text-xs font-semibold">{activeScenario.alertTriggered}</p>
        </div>
      )}

      {/* All scenarios */}
      {DEMO_SCENARIOS.map((sc) => {
        const isActive = sc.condition(env);
        const isOpen = openId === sc.id;
        return (
          <div
            key={sc.id}
            className={cn(
              "rounded-2xl border p-4 cursor-pointer transition-all",
              isActive
                ? cn(SEVERITY_STYLE[sc.severity])
                : "bg-slate-800/50 border-slate-700 opacity-60 hover:opacity-80"
            )}
            onClick={() => setOpenId(isOpen ? null : sc.id)}
          >
            <div className="flex items-center gap-2">
              {isActive ? (
                <AlertTriangle size={13} className="flex-shrink-0" />
              ) : (
                <CheckCircle2 size={13} className="text-slate-500 flex-shrink-0" />
              )}
              <p className="text-xs font-semibold text-white flex-1">{sc.title}</p>
              <Badge
                variant={
                  sc.severity === "critical" ? "danger"
                  : sc.severity === "high" ? "warning"
                  : sc.severity === "low" ? "success"
                  : "default"
                }
                className="text-[10px]"
              >
                {sc.severity}
              </Badge>
              {isOpen ? <ChevronUp size={12} className="text-slate-500" /> : <ChevronDown size={12} className="text-slate-500" />}
            </div>

            {isOpen && (
              <div
                className="mt-3 pt-3 border-t border-slate-700/40 space-y-3"
                onClick={(e) => e.stopPropagation()}
              >
                {/* Simulated Gemini explanation */}
                <div className="space-y-1.5">
                  <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-blue-400 inline-block" />
                    Gemini Explanation
                  </p>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {sc.geminiExplanation}
                  </p>
                </div>
                {/* Citations */}
                <div className="space-y-1">
                  <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
                    Sources
                  </p>
                  {sc.citations.map((c, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-1.5 text-[10px] text-blue-400 bg-blue-950/30 border border-blue-800/30 rounded-lg px-2.5 py-1.5"
                    >
                      <Info size={9} />
                      {c}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
