/* Doctor Dashboard — patient list + alert prioritisation + report view */
"use client";

import { useState } from "react";
import { useState as _unused } from "react";
import {
  Stethoscope,
  ChevronRight,
  FileText,
  AlertTriangle,
  CheckCircle2,
  User as UserIcon,
} from "lucide-react";
import {
  Card,
  Badge,
  SeverityBadge,
  Section,
  EmptyState,
} from "@/components/ui/shared";
import {
  DEMO_PATIENTS,
  DEMO_ALERTS,
  DEMO_REPORTS,
  DEMO_DOCTORS,
  DEMO_ENVIRONMENT,
  Patient,
} from "@/lib/demo-data";
import { cn } from "@/lib/utils";
import { EnvironmentPanel } from "@/components/ui/EnvironmentPanel";

export default function DoctorPage() {
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const doctor = DEMO_DOCTORS[0];

  const patientsWithAlerts = DEMO_PATIENTS.map((p) => ({
    ...p,
    activeAlerts: DEMO_ALERTS.filter((a) => a.patientId === p.id && !a.acknowledged),
  })).sort((a, b) => b.activeAlerts.length - a.activeAlerts.length);

  if (selectedPatientId) {
    const patient = DEMO_PATIENTS.find((p) => p.id === selectedPatientId)!;
    return (
      <PatientDetailView
        patient={patient}
        onBack={() => setSelectedPatientId(null)}
      />
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      {/* Doctor header */}
      <Card className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-emerald-900/60 border border-emerald-700/50 flex items-center justify-center flex-shrink-0">
          <Stethoscope size={16} className="text-emerald-400" />
        </div>
        <div>
          <p className="font-semibold text-white">{doctor.name}</p>
          <p className="text-xs text-slate-400">{doctor.specialization} · {doctor.hospital}</p>
        </div>
        <Badge variant="success" className="ml-auto">Active</Badge>
      </Card>

      {/* Summary bar */}
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { label: "Patients", count: DEMO_PATIENTS.length, color: "text-blue-400" },
          {
            label: "With Alerts",
            count: patientsWithAlerts.filter((p) => p.activeAlerts.length > 0).length,
            color: "text-amber-400",
          },
          {
            label: "Total Alerts",
            count: DEMO_ALERTS.filter((a) => !a.acknowledged).length,
            color: "text-red-400",
          },
        ].map(({ label, count, color }) => (
          <div key={label} className="bg-slate-800 border border-slate-700 rounded-xl py-3">
            <p className={`text-2xl font-bold ${color}`}>{count}</p>
            <p className="text-xs text-slate-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Patient list */}
      <Section title="Patient List" subtitle="Sorted by alert priority">
        <div className="space-y-2">
          {patientsWithAlerts.map((p) => (
            <Card
              key={p.id}
              className="flex items-center gap-3"
              onClick={() => setSelectedPatientId(p.id)}
            >
              <div className="h-9 w-9 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                {p.name[0]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white">{p.name}</p>
                <p className="text-xs text-slate-400">{p.age}y · {p.city}</p>
              </div>
              <div className="flex items-center gap-2">
                {p.activeAlerts.length > 0 ? (
                  <Badge variant="danger">{p.activeAlerts.length} alert{p.activeAlerts.length > 1 ? "s" : ""}</Badge>
                ) : (
                  <Badge variant="success">Clear</Badge>
                )}
                <ChevronRight size={14} className="text-slate-500" />
              </div>
            </Card>
          ))}
        </div>
      </Section>
    </div>
  );
}

function PatientDetailView({
  patient,
  onBack,
}: {
  patient: Patient;
  onBack: () => void;
}) {
  const alerts = DEMO_ALERTS.filter((a) => a.patientId === patient.id).sort(
    (a, b) => b.createdAt.localeCompare(a.createdAt)
  );
  const reports = DEMO_REPORTS.filter((r) => r.patientId === patient.id).sort(
    (a, b) => b.uploadedAt.localeCompare(a.uploadedAt)
  );
  const env = DEMO_ENVIRONMENT.find((e) => e.patientId === patient.id);
  const [openAlertId, setOpenAlertId] = useState<string | null>(null);
  const [openReportId, setOpenReportId] = useState<string | null>(null);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      {/* Back + header */}
      <button
        onClick={onBack}
        className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
      >
        ← Back to patient list
      </button>

      <Card className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
          {patient.name[0]}
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-white text-base">{patient.name}</p>
          <div className="flex flex-wrap gap-1.5">
            <Badge variant="outline">{patient.age}y</Badge>
            <Badge variant="outline">{patient.gender}</Badge>
            <Badge variant="outline">{patient.bloodGroup}</Badge>
            <Badge variant="outline">{patient.city}</Badge>
          </div>
        </div>
      </Card>

      {/* Environment summary — compact reusable panel */}
      {env && (
        <Section title="Environmental Context">
          <EnvironmentPanel env={env} compact />
        </Section>
      )}

      {/* Alerts */}
      <Section title="Alerts" subtitle="Generated by deterministic rules engine">
        {alerts.length === 0 ? (
          <EmptyState message="No alerts for this patient." icon={<CheckCircle2 />} />
        ) : (
          <div className="space-y-2">
            {alerts.map((a) => (
              <Card
                key={a.id}
                className={cn(
                  "space-y-1",
                  a.acknowledged && "opacity-60",
                  !a.acknowledged && a.severity === "high" && "border-red-700/60"
                )}
                onClick={() => setOpenAlertId(openAlertId === a.id ? null : a.id)}
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <SeverityBadge severity={a.severity} />
                  <p className="text-sm font-medium text-white">{a.title}</p>
                  {a.acknowledged && <Badge variant="success" className="ml-auto text-[10px]">Acknowledged</Badge>}
                </div>
                <p className="text-xs text-slate-400">{a.reason}</p>
                {openAlertId === a.id && (
                  <div className="pt-2 space-y-1 border-t border-slate-700/50">
                    <p className="text-xs font-medium text-slate-300">Evidence</p>
                    {a.evidence.map((ev, i) => (
                      <p key={i} className="text-xs text-slate-400 flex gap-2">
                        <span className="text-blue-400">→</span>{ev}
                      </p>
                    ))}
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </Section>

      {/* Reports */}
      <Section title="Medical Reports">
        {reports.length === 0 ? (
          <EmptyState message="No reports uploaded." icon={<FileText />} />
        ) : (
          <div className="space-y-2">
            {reports.map((r) => (
              <Card
                key={r.id}
                onClick={() => setOpenReportId(openReportId === r.id ? null : r.id)}
              >
                <div className="flex items-center gap-3">
                  <FileText size={15} className="text-blue-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{r.fileName}</p>
                    <p className="text-xs text-slate-500">
                      {new Date(r.uploadedAt).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                      {" · "}{r.pageCount} page{r.pageCount !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <Badge
                    variant={r.status === "ready" ? "success" : r.status === "error" ? "danger" : "warning"}
                    className="text-[10px]"
                  >
                    {r.status}
                  </Badge>
                </div>
                {openReportId === r.id && r.extractedResults.length > 0 && (
                  <div className="pt-3 border-t border-slate-700/50 space-y-1 mt-2">
                    <p className="text-xs font-medium text-slate-300 mb-2">Extracted values</p>
                    {r.extractedResults.map((lr) => (
                      <div key={lr.id} className="flex items-center justify-between text-xs bg-slate-700/30 rounded-lg px-3 py-1.5">
                        <span className="text-slate-300">{lr.testName}</span>
                        <span className="text-white font-bold">{lr.value} {lr.unit}</span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}
