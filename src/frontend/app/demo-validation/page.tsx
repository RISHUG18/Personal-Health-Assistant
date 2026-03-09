/* Demo Data Validation — integrity checks on all synthetic demo data (Person 5 Week 2) */
"use client";

import { useMemo } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Users,
  FileText,
  Activity,
  Wind,
  Bell,
  ScanLine,
} from "lucide-react";
import { Card, Badge, Section } from "@/components/ui/shared";
import {
  DEMO_PATIENTS,
  DEMO_REPORTS,
  DEMO_HEALTH_METRICS,
  DEMO_ENVIRONMENT,
  DEMO_ALERTS,
  labStatus,
} from "@/lib/demo-data";
import { cn } from "@/lib/utils";

// ── Check result type ─────────────────────────
type CheckStatus = "pass" | "warn" | "fail";

interface Check {
  id: string;
  label: string;
  detail: string;
  status: CheckStatus;
}

interface CheckGroup {
  title: string;
  icon: React.ReactNode;
  checks: Check[];
}

// ── Run all checks ────────────────────────────
function runValidation(): CheckGroup[] {
  const groups: CheckGroup[] = [];

  // ── 1. Patients ──────────────────────────────
  const patientChecks: Check[] = DEMO_PATIENTS.map((p) => ({
    id: `pat-${p.id}`,
    label: `${p.name} profile`,
    detail: `age=${p.age}, city=${p.city}, bloodGroup=${p.bloodGroup}, assignedDoctor=${p.assignedDoctorId}`,
    status: p.name && p.city && p.bloodGroup && p.assignedDoctorId ? "pass" : "fail",
  }));
  groups.push({ title: "Patients", icon: <Users size={14} />, checks: patientChecks });

  // ── 2. Reports ───────────────────────────────
  const reportChecks: Check[] = DEMO_REPORTS.map((r) => {
    const hasResults = r.extractedResults.length > 0;
    const isProcessing = r.status === "processing";
    const hasOcr = !!r.ocrSnippet;
    let status: CheckStatus = "pass";
    let detail = `type=${r.reportType}, pages=${r.pageCount}, results=${r.extractedResults.length}, ocr=${hasOcr ? "yes" : "no"}`;

    if (!hasOcr) {
      status = "warn";
      detail += " — no OCR snippet";
    }
    if (!hasResults && !isProcessing) {
      status = "fail";
      detail += " — ready but 0 extracted values";
    }
    if (hasResults && !isProcessing) {
      // Check each lab result has a value within sane bounds
      for (const lr of r.extractedResults) {
        if (lr.value === undefined || lr.referenceMin === undefined) {
          status = "fail";
          detail += ` — ${lr.testName} missing value or ref`;
          break;
        }
      }
    }
    return {
      id: `rep-${r.id}`,
      label: r.fileName,
      detail,
      status,
    };
  });
  groups.push({ title: "Reports & OCR", icon: <FileText size={14} />, checks: reportChecks });

  // ── 3. Lab result integrity ─────────────────
  const labChecks: Check[] = [];
  for (const r of DEMO_REPORTS) {
    for (const lr of r.extractedResults) {
      const s = labStatus(lr);
      labChecks.push({
        id: `lr-${lr.id}`,
        label: `${lr.testName} (${r.fileName})`,
        detail: `value=${lr.value} ${lr.unit}, ref=${lr.referenceMin}–${lr.referenceMax}, status=${s}`,
        status: s === "critical" ? "warn" : "pass",
      });
    }
  }
  if (labChecks.length === 0) {
    labChecks.push({ id: "no-labs", label: "No lab results found", detail: "No extracted values across all reports", status: "fail" });
  }
  groups.push({ title: "Lab Result Values", icon: <ScanLine size={14} />, checks: labChecks });

  // ── 4. Health metrics ────────────────────────
  const metricChecks: Check[] = DEMO_PATIENTS.map((p) => {
    const rows = DEMO_HEALTH_METRICS.filter((m) => m.patientId === p.id);
    const status: CheckStatus = rows.length >= 7 ? "pass" : rows.length > 0 ? "warn" : "fail";
    return {
      id: `met-${p.id}`,
      label: `${p.name} — health metrics`,
      detail: `${rows.length} day(s) of data; latest=${rows.sort((a, b) => b.date.localeCompare(a.date))[0]?.date ?? "none"}`,
      status,
    };
  });
  groups.push({ title: "Health Metrics (Wearable)", icon: <Activity size={14} />, checks: metricChecks });

  // ── 5. Environment ───────────────────────────
  const envChecks: Check[] = DEMO_PATIENTS.map((p) => {
    const env = DEMO_ENVIRONMENT.find((e) => e.patientId === p.id);
    if (!env) {
      return { id: `env-${p.id}`, label: `${p.name} — environment`, detail: "No environment record found", status: "fail" };
    }
    const hasAqi = env.aqi > 0;
    const hasTemp = env.temperature.avg > 0;
    const status: CheckStatus = hasAqi && hasTemp ? "pass" : "warn";
    return {
      id: `env-${p.id}`,
      label: `${p.name} — ${env.city}`,
      detail: `AQI=${env.aqi}, temp=${env.temperature.avg}°C, humidity=${env.humidity}%, season=${env.season}, heatwave=${env.heatwave}, poorAir=${env.poorAir}`,
      status,
    };
  });
  groups.push({ title: "Environmental Context", icon: <Wind size={14} />, checks: envChecks });

  // ── 6. Alerts ────────────────────────────────
  const alertChecks: Check[] = DEMO_ALERTS.map((a) => {
    const hasEvidence = a.evidence.length > 0;
    const validSeverity = ["low", "medium", "high", "critical"].includes(a.severity);
    const status: CheckStatus = hasEvidence && validSeverity ? "pass" : "warn";
    return {
      id: `alert-${a.id}`,
      label: a.title,
      detail: `severity=${a.severity}, category=${a.category}, evidence=${a.evidence.length} item(s), ack=${a.acknowledged}`,
      status,
    };
  });
  groups.push({ title: "Alerts", icon: <Bell size={14} />, checks: alertChecks });

  return groups;
}

// ── Summary totals ────────────────────────────
function summarise(groups: CheckGroup[]) {
  let pass = 0, warn = 0, fail = 0;
  for (const g of groups) {
    for (const c of g.checks) {
      if (c.status === "pass") pass++;
      else if (c.status === "warn") warn++;
      else fail++;
    }
  }
  return { pass, warn, fail, total: pass + warn + fail };
}

// ── Page ──────────────────────────────────────
export default function DemoValidationPage() {
  const groups = useMemo(() => runValidation(), []);
  const { pass, warn, fail, total } = summarise(groups);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Demo Data Validation</h1>
        <p className="text-xs text-slate-400 mt-1">
          Automated integrity checks on all synthetic demo data — verifies OCR readability,
          extracted values, metrics, environment, and alerts.
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { label: "Pass",  count: pass,  color: "text-emerald-400", bg: "border-emerald-800/40" },
          { label: "Warn",  count: warn,  color: "text-amber-400",   bg: "border-amber-800/40" },
          { label: "Fail",  count: fail,  color: "text-red-400",     bg: "border-red-800/40" },
        ].map(({ label, count, color, bg }) => (
          <div key={label} className={cn("bg-slate-800 border rounded-xl py-3", bg)}>
            <p className={`text-2xl font-bold stat-value ${color}`}>{count}</p>
            <p className="text-xs text-slate-400 mt-0.5">{label} / {total}</p>
          </div>
        ))}
      </div>

      {/* Overall banner */}
      {fail > 0 ? (
        <div className="flex items-start gap-3 bg-red-900/20 border border-red-700/50 rounded-xl p-3">
          <XCircle size={16} className="text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-red-300">{fail} check{fail > 1 ? "s" : ""} failed</p>
            <p className="text-xs text-slate-400 mt-0.5">Review the sections below and report issues to the backend team.</p>
          </div>
        </div>
      ) : warn > 0 ? (
        <div className="flex items-start gap-3 bg-amber-900/20 border border-amber-700/50 rounded-xl p-3">
          <AlertTriangle size={16} className="text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-amber-300">{warn} warning{warn > 1 ? "s" : ""} — demo safe, but worth reviewing</p>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3 bg-emerald-900/20 border border-emerald-700/50 rounded-xl p-3">
          <CheckCircle2 size={16} className="text-emerald-400 flex-shrink-0" />
          <p className="text-sm font-semibold text-emerald-300">All {total} checks passed — demo data is valid</p>
        </div>
      )}

      {/* Check groups */}
      {groups.map((g) => (
        <Section key={g.title} title={g.title}>
          <div className="space-y-2">
            {g.checks.map((c) => (
              <CheckRow key={c.id} check={c} />
            ))}
          </div>
        </Section>
      ))}

      {/* Backend issues to report */}
      <Section title="Issues to Report to Backend Team">
        <div className="space-y-2">
          {groups.flatMap((g) => g.checks).filter((c) => c.status !== "pass").length === 0 ? (
            <Card>
              <p className="text-xs text-emerald-400">No issues — all demo data passed validation.</p>
            </Card>
          ) : (
            groups.flatMap((g) =>
              g.checks
                .filter((c) => c.status !== "pass")
                .map((c) => (
                  <Card key={c.id} className="border-amber-800/40">
                    <div className="flex items-start gap-2">
                      <StatusIcon status={c.status} />
                      <div>
                        <p className="text-sm font-medium text-white">{c.label}</p>
                        <p className="text-xs text-slate-400 mt-0.5">{c.detail}</p>
                      </div>
                    </div>
                  </Card>
                ))
            )
          )}
        </div>
      </Section>
    </div>
  );
}

// ── Row component ─────────────────────────────
function CheckRow({ check }: { check: Check }) {
  return (
    <Card className={cn(
      "flex items-start gap-3",
      check.status === "fail" && "border-red-800/50",
      check.status === "warn" && "border-amber-800/40",
    )}>
      <StatusIcon status={check.status} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-medium text-white">{check.label}</p>
          <StatusBadge status={check.status} />
        </div>
        <p className="text-xs text-slate-500 mt-0.5 truncate">{check.detail}</p>
      </div>
    </Card>
  );
}

function StatusIcon({ status }: { status: CheckStatus }) {
  if (status === "pass") return <CheckCircle2 size={15} className="text-emerald-400 flex-shrink-0 mt-0.5" />;
  if (status === "warn") return <AlertTriangle size={15} className="text-amber-400 flex-shrink-0 mt-0.5" />;
  return <XCircle size={15} className="text-red-400 flex-shrink-0 mt-0.5" />;
}

function StatusBadge({ status }: { status: CheckStatus }) {
  if (status === "pass") return <Badge variant="success" className="text-[10px]">pass</Badge>;
  if (status === "warn") return <Badge variant="warning" className="text-[10px]">warn</Badge>;
  return <Badge variant="danger" className="text-[10px]">fail</Badge>;
}
