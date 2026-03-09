/* Environment Page — AQI + weather panel with tooltips (Person 5 Week 4) */
"use client";

import { useState } from "react";
import { Info, Wind, Minus } from "lucide-react";
import { Card, Section } from "@/components/ui/shared";
import { EnvironmentPanel } from "@/components/ui/EnvironmentPanel";
import { DEMO_ENVIRONMENT, DEMO_PATIENTS } from "@/lib/demo-data";
import { cn } from "@/lib/utils";

interface Tooltip { label: string; text: string }
const TOOLTIPS: Tooltip[] = [
  {
    label: "What is AQI?",
    text: "Air Quality Index (AQI) measures how clean or polluted the air is. Values 0\u201350 are Good, 51\u2013100 Moderate, 101\u2013150 Unhealthy for Sensitive Groups, 151\u2013200 Unhealthy, and above\u00a0200 Very\u00a0Unhealthy.",
  },
  {
    label: "Why does temperature affect sleep?",
    text: "Your body drops its core temperature to initiate sleep. Ambient heat (especially above 26\u00a0\u00b0C) makes this harder, reducing sleep quality and duration.",
  },
  {
    label: "How does environment affect alerts?",
    text: "The rules engine can raise alert severity when air quality is poor or temperatures are extreme \u2014 for example, a normal fatigue flag may escalate to High during a heatwave.",
  },
];

export default function EnvironmentPage() {
  const [patientId, setPatientId] = useState("pat-1");
  const env = DEMO_ENVIRONMENT.find((e) => e.patientId === patientId);

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Environment</h1>
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

      {env ? (
        <EnvironmentPanel env={env} showScenario />
      ) : (
        <Card className="flex flex-col items-center gap-3 py-10">
          <Wind size={32} className="text-slate-600" />
          <p className="text-sm text-slate-400 font-medium">Environmental data currently unavailable</p>
          <p className="text-xs text-slate-500">Using last known environmental conditions</p>
        </Card>
      )}

      {/* Tooltips/explainer cards */}
      <Section title="What does this mean?" subtitle="Plain-language explanations">
        <div className="space-y-3">
          {TOOLTIPS.map((t) => (
            <ExplainerCard key={t.label} label={t.label} text={t.text} />
          ))}
        </div>
      </Section>
    </div>
  );
}

function ExplainerCard({ label, text }: { label: string; text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <Card onClick={() => setOpen(!open)} className="cursor-pointer space-y-1">
      <div className="flex items-center gap-2">
        <Info size={13} className="text-blue-400 flex-shrink-0" />
        <p className="text-sm font-medium text-white">{label}</p>
        <Minus size={12} className={cn("ml-auto text-slate-500 transition-transform", open && "rotate-90")} />
      </div>
      {open && <p className="text-xs text-slate-400 leading-relaxed pl-5">{text}</p>}
    </Card>
  );
}

