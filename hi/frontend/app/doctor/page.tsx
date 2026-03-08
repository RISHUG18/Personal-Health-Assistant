/* Week 4/6 – Doctor Dashboard: patient detail + doctor notes */
"use client";

import { useState } from "react";
import { Stethoscope, ChevronRight, FileText, TrendingUp, Save, NotebookPen } from "lucide-react";
import { Card, Badge, SeverityBadge, Section, EmptyState } from "@/components/ui/shared";
import { useToast } from "@/components/ui/toast";
import {
  DEMO_DOCTORS,
  DEMO_PATIENTS,
  DEMO_ALERTS,
  DEMO_REPORTS,
  DEMO_ENVIRONMENT,
  DEMO_HEALTH_METRICS,
  labStatus,
  Severity,
} from "@/lib/demo-data";

export default function DoctorPage() {
  const [doctorId, setDoctorId] = useState("doc-1");
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  // Week 6: per-patient notes stored in state
  const [notes, setNotes] = useState<Record<string, string>>({});

  const doctor = DEMO_DOCTORS.find((d) => d.id === doctorId)!;
  const patients = DEMO_PATIENTS.filter((p) => p.assignedDoctorId === doctorId);
  const selectedPatient = patients.find((p) => p.id === selectedPatientId) ?? null;

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
      {/* Doctor header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-teal-600/30 border border-teal-600/50 flex items-center justify-center">
            <Stethoscope size={18} className="text-teal-400" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white">{doctor.name}</h1>
            <p className="text-xs text-slate-400">{doctor.specialization} · {doctor.hospital}</p>
          </div>
        </div>
        <select
          value={doctorId}
          onChange={(e) => { setDoctorId(e.target.value); setSelectedPatientId(null); }}
          className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-1.5"
        >
          {DEMO_DOCTORS.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col md:flex-row gap-4">
        {/* Patient list column */}
        <div className="md:w-72 flex-shrink-0 space-y-2">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Patients ({patients.length})</p>
          {patients.map((p) => {
            const alerts = DEMO_ALERTS.filter((a) => a.patientId === p.id && !a.acknowledged);
            const maxSev = alerts.reduce<Severity | null>((acc, a) => {
              const rank: Record<Severity, number> = { critical: 4, high: 3, medium: 2, low: 1 };
              if (!acc || rank[a.severity] > rank[acc]) return a.severity;
              return acc;
            }, null);

            return (
              <button
                key={p.id}
                onClick={() => setSelectedPatientId(p.id)}
                className={`w-full text-left flex items-center gap-3 p-3 rounded-xl border transition-colors ${
                  selectedPatientId === p.id
                    ? "bg-blue-600/20 border-blue-600/50"
                    : "bg-slate-800 border-slate-700 hover:border-slate-600"
                }`}
              >
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                  {p.name[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{p.name}</p>
                  <p className="text-xs text-slate-400">{p.age}y · {p.city}</p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  {maxSev && <SeverityBadge severity={maxSev} />}
                  <ChevronRight size={12} className="text-slate-600" />
                </div>
              </button>
            );
          })}
        </div>

        {/* Patient detail */}
        <div className="flex-1 space-y-4">
          {!selectedPatient ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-600 py-20">
              <Stethoscope size={32} className="opacity-30 mb-2" />
              <p className="text-sm">Select a patient to view details</p>
            </div>
          ) : (
            <PatientDetail
              patientId={selectedPatient.id}
              note={notes[selectedPatient.id] ?? ""}
              onNoteChange={(v) => setNotes((prev) => ({ ...prev, [selectedPatient.id]: v }))}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function PatientDetail({ patientId, note, onNoteChange }: { patientId: string; note: string; onNoteChange: (v: string) => void }) {
  const { toast } = useToast();
  const patient = DEMO_PATIENTS.find((p) => p.id === patientId)!;
  const alerts = DEMO_ALERTS.filter((a) => a.patientId === patientId);
  const reports = DEMO_REPORTS.filter((r) => r.patientId === patientId);
  const metrics = DEMO_HEALTH_METRICS.filter((m) => m.patientId === patientId).slice(0, 3);
  const env = DEMO_ENVIRONMENT.find((e) => e.patientId === patientId);

  // Flatten all lab results
  const allLabs = reports.flatMap((r) => r.extractedResults).filter(
    (r) => labStatus(r) !== "normal"
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
          {patient.name[0]}
        </div>
        <div>
          <p className="font-semibold text-white">{patient.name}</p>
          <p className="text-xs text-slate-400">{patient.age}y · {patient.gender} · {patient.bloodGroup} · {patient.city}</p>
        </div>
        {env?.heatwave && <Badge variant="danger">🌡 Heatwave</Badge>}
        {env?.poorAir && <Badge variant="warning">💨 Poor Air</Badge>}
      </div>

      {/* Week 6 – Doctor Notes */}
      <Section title="Clinical Notes" subtitle="Private — visible only to you">
        <Card className="space-y-3">
          <div className="flex items-center gap-2">
            <NotebookPen size={13} className="text-teal-400" />
            <p className="text-xs font-semibold text-teal-300 uppercase tracking-wider">Doctor Notes</p>
          </div>
          <textarea
            value={note}
            onChange={(e) => onNoteChange(e.target.value)}
            placeholder="Add clinical observations, follow-up reminders, or notes for next visit…"
            rows={4}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 resize-none outline-none focus:border-blue-600 transition-colors"
          />
          <div className="flex items-center justify-between">
            <p className="text-[10px] text-slate-600">{note.length} characters</p>
            <button
              onClick={() => toast({ title: "Notes saved", description: "Clinical notes saved locally.", variant: "success" })}
              disabled={!note.trim()}
              className="flex items-center gap-1.5 text-xs bg-teal-900/40 border border-teal-700/50 text-teal-400 hover:bg-teal-800/40 disabled:opacity-40 disabled:cursor-not-allowed px-3 py-1.5 rounded-lg transition-colors"
            >
              <Save size={12} /> Save Note
            </button>
          </div>
        </Card>
      </Section>

      {/* Doctor Summary Card (Week 4) */}
      <DoctorSummaryCard patientId={patientId} />

      {/* Abnormal labs */}
      {allLabs.length > 0 && (
        <Section title="Abnormal Lab Values" subtitle="Extracted from uploaded reports">
          <div className="space-y-1">
            {allLabs.map((r) => {
              const s = labStatus(r);
              const color = { low: "text-amber-400", high: "text-orange-400", critical: "text-red-400", normal: "text-emerald-400" }[s];
              return (
                <div key={r.id} className="flex items-center justify-between py-1.5 border-b border-slate-800">
                  <div>
                    <span className="text-sm text-slate-200">{r.testName}</span>
                    <span className="text-xs text-slate-500 ml-2">({new Date(r.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })})</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-semibold ${color}`}>{r.value} {r.unit}</span>
                    <span className="text-xs text-slate-500">ref {r.referenceMin}–{r.referenceMax}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Section>
      )}

      {/* Active alerts */}
      <Section title="Active Alerts">
        {alerts.filter((a) => !a.acknowledged).length === 0 ? (
          <EmptyState message="No active alerts." />
        ) : (
          <div className="space-y-2">
            {alerts.filter((a) => !a.acknowledged).map((a) => (
              <div key={a.id} className="flex items-start gap-2 bg-slate-800 border border-slate-700 rounded-xl p-3">
                <SeverityBadge severity={a.severity} />
                <div>
                  <p className="text-sm font-medium text-white">{a.title}</p>
                  <p className="text-xs text-slate-400">{a.reason}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Reports */}
      <Section title="Reports">
        <div className="space-y-2">
          {reports.map((r) => (
            <div key={r.id} className="flex items-center gap-3 bg-slate-800 border border-slate-700 rounded-xl p-3">
              <FileText size={14} className="text-slate-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{r.fileName}</p>
                <p className="text-xs text-slate-500">{new Date(r.uploadedAt).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</p>
              </div>
              <Badge variant={r.status === "ready" ? "success" : r.status === "processing" ? "warning" : "danger"}>
                {r.status}
              </Badge>
            </div>
          ))}
        </div>
      </Section>

      {/* Health trends */}
      {metrics.length > 0 && (
        <Section title="Health Trends (Last 3 Days)">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="text-left py-1.5 pr-4 font-medium">Date</th>
                  <th className="text-right pr-4 font-medium">Steps</th>
                  <th className="text-right pr-4 font-medium">Sleep</th>
                  <th className="text-right font-medium">HR Avg</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((m) => (
                  <tr key={m.date} className="border-b border-slate-800">
                    <td className="py-1.5 pr-4 text-slate-300">{new Date(m.date).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })}</td>
                    <td className={`text-right pr-4 font-medium ${m.steps >= 6000 ? "text-emerald-400" : "text-amber-400"}`}>{m.steps.toLocaleString()}</td>
                    <td className={`text-right pr-4 font-medium ${m.sleepHours >= 7 ? "text-emerald-400" : "text-amber-400"}`}>{m.sleepHours}h</td>
                    <td className="text-right text-slate-300">{m.heartRateAvg} bpm</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}
    </div>
  );
}

/* Week 4 – Doctor Summary Card (Person 5 output) */
function DoctorSummaryCard({ patientId }: { patientId: string }) {
  const alerts = DEMO_ALERTS.filter((a) => a.patientId === patientId && !a.acknowledged);
  const env = DEMO_ENVIRONMENT.find((e) => e.patientId === patientId);
  const metric = DEMO_HEALTH_METRICS.find((m) => m.patientId === patientId);

  // Build a demo narrative for the doctor
  const lines: string[] = [];
  if (alerts.some((a) => a.category === "lab"))
    lines.push("⚠ Abnormal lab values detected — iron deficiency markers are significantly below reference range.");
  if (metric && metric.sleepHours < 6)
    lines.push(`🌙 Patient reported only ${metric.sleepHours}h of sleep on ${metric.date}.`);
  if (env?.heatwave)
    lines.push(`🌡 Heatwave conditions in ${env.city} (max ${env.temperature.max}°C) may be exacerbating fatigue.`);
  if (env?.poorAir)
    lines.push(`💨 AQI ${env.aqi} — recommend limiting outdoor exposure.`);
  if (lines.length === 0)
    lines.push("No significant concerns flagged today.");

  return (
    <Card className="bg-teal-900/10 border-teal-700/30 space-y-2">
      <div className="flex items-center gap-2">
        <TrendingUp size={14} className="text-teal-400" />
        <p className="text-xs font-semibold text-teal-300 uppercase tracking-wider">AI-Generated Doctor Summary</p>
        <Badge variant="outline" className="text-[10px] ml-auto">Demo · Gemini</Badge>
      </div>
      <ul className="space-y-1">
        {lines.map((l, i) => (
          <li key={i} className="text-xs text-slate-300 leading-relaxed">{l}</li>
        ))}
      </ul>
      <p className="text-[10px] text-slate-600 border-t border-teal-700/20 pt-2">
        This summary is AI-generated from structured data + environmental context. It does not replace clinical judgment.
      </p>
    </Card>
  );
}
