/* Reports — static timeline + report type + OCR preview (Person 5 Week 2) */
"use client";

import { useState } from "react";
import {
  FileText, Clock, CheckCircle2, Loader2, AlertCircle, ChevronDown,
  Eye, Upload, Microscope, Heart, Pill, ScanLine, Beaker,
} from "lucide-react";
import { Card, Badge, Section, EmptyState } from "@/components/ui/shared";
import { cn } from "@/lib/utils";
import {
  DEMO_REPORTS,
  DEMO_PATIENTS,
  MedicalReport,
  LabResult,
  ReportType,
  labStatus,
} from "@/lib/demo-data";

// ── Report-type metadata ──────────────────────
const REPORT_TYPE_META: Record<ReportType, { label: string; icon: React.ReactNode; color: string }> = {
  blood_test:   { label: "Blood Test",    icon: <Beaker size={11} />,     color: "bg-blue-900/40 text-blue-300 border-blue-700/50" },
  lipid_panel:  { label: "Lipid Panel",   icon: <Heart size={11} />,      color: "bg-rose-900/40 text-rose-300 border-rose-700/50" },
  thyroid:      { label: "Thyroid",       icon: <Microscope size={11} />, color: "bg-purple-900/40 text-purple-300 border-purple-700/50" },
  diabetes:     { label: "Diabetes",      icon: <ScanLine size={11} />,   color: "bg-amber-900/40 text-amber-300 border-amber-700/50" },
  imaging:      { label: "Imaging",       icon: <ScanLine size={11} />,   color: "bg-cyan-900/40 text-cyan-300 border-cyan-700/50" },
  prescription: { label: "Prescription",  icon: <Pill size={11} />,       color: "bg-emerald-900/40 text-emerald-300 border-emerald-700/50" },
  other:        { label: "Other",         icon: <FileText size={11} />,   color: "bg-slate-700/40 text-slate-300 border-slate-600/50" },
};

const STATUS_META = {
  ready:      { icon: CheckCircle2, color: "text-emerald-400", label: "Ready" },
  processing: { icon: Loader2,      color: "text-amber-400",   label: "Processing" },
  error:      { icon: AlertCircle,  color: "text-red-400",     label: "Error" },
};

type DrawerTab = "extracted" | "ocr";

const LAB_STATUS_COLORS = {
  normal:   "text-emerald-400",
  low:      "text-amber-400",
  high:     "text-orange-400",
  critical: "text-red-400",
};

export default function ReportsPage() {
  const [patientId, setPatientId] = useState("pat-1");
  const [openId, setOpenId] = useState<string | null>(null);
  const [tabMap, setTabMap] = useState<Record<string, DrawerTab>>({});

  const reports = DEMO_REPORTS.filter((r) => r.patientId === patientId).sort(
    (a, b) => b.uploadedAt.localeCompare(a.uploadedAt)
  );

  function toggleReport(id: string) {
    setOpenId((prev) => (prev === id ? null : id));
    setTabMap((prev) => ({ ...prev, [id]: prev[id] ?? "extracted" }));
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Medical Reports</h1>
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

      {/* Upload stub */}
      <div className="border-2 border-dashed border-slate-700 rounded-2xl p-6 text-center">
        <Upload size={26} className="mx-auto text-slate-600 mb-2" />
        <p className="text-sm text-slate-400 font-medium">Upload a Medical Report</p>
        <p className="text-xs text-slate-500 mt-1">PDF or image · OCR extraction · Instant alerts</p>
        <div className="flex justify-center gap-2 mt-3 flex-wrap">
          {(["blood_test", "lipid_panel", "diabetes", "thyroid"] as ReportType[]).map((t) => {
            const m = REPORT_TYPE_META[t];
            return (
              <span key={t} className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border", m.color)}>
                {m.icon}{m.label}
              </span>
            );
          })}
        </div>
        <button
          className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 transition text-white text-sm rounded-xl font-medium"
          onClick={() => alert("File picker — backend integration in Week 2")}
        >
          Choose File
        </button>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { label: "Total",      count: reports.length,                                          color: "text-slate-200" },
          { label: "Ready",      count: reports.filter((r) => r.status === "ready").length,      color: "text-emerald-400" },
          { label: "Processing", count: reports.filter((r) => r.status === "processing").length, color: "text-amber-400" },
        ].map(({ label, count, color }) => (
          <div key={label} className="bg-slate-800 border border-slate-700 rounded-xl py-3">
            <p className={`text-2xl font-bold stat-value ${color}`}>{count}</p>
            <p className="text-xs text-slate-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Timeline */}
      <Section title="Report Timeline" subtitle="Chronological history · click any report to inspect">
        {reports.length === 0 ? (
          <EmptyState message="No reports found for this patient." icon={<FileText />} />
        ) : (
          <div className="relative">
            <div className="absolute left-5 top-2 bottom-2 w-0.5 bg-slate-700/60 rounded-full" />
            <div className="space-y-4 pl-12">
              {reports.map((report, idx) => (
                <ReportCard
                  key={report.id}
                  report={report}
                  isFirst={idx === 0}
                  open={openId === report.id}
                  tab={tabMap[report.id] ?? "extracted"}
                  onToggle={() => toggleReport(report.id)}
                  onTabChange={(t) => setTabMap((prev) => ({ ...prev, [report.id]: t }))}
                />
              ))}
            </div>
          </div>
        )}
      </Section>
    </div>
  );
}

// ── Report Card ───────────────────────────────
function ReportCard({
  report,
  isFirst,
  open,
  tab,
  onToggle,
  onTabChange,
}: {
  report: MedicalReport;
  isFirst: boolean;
  open: boolean;
  tab: DrawerTab;
  onToggle: () => void;
  onTabChange: (t: DrawerTab) => void;
}) {
  const statusMeta = STATUS_META[report.status];
  const StatusIcon = statusMeta.icon;
  const typeMeta = REPORT_TYPE_META[report.reportType];

  const date = new Date(report.uploadedAt);
  const dateStr = date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  const timeStr = date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

  return (
    <div className="relative">
      {/* Timeline dot */}
      <div className={cn(
        "absolute -left-[27px] h-3.5 w-3.5 rounded-full border-2 border-slate-900 top-4",
        isFirst ? "bg-blue-500" : "bg-slate-600"
      )} />

      <Card className="space-y-2" onClick={onToggle}>
        {/* Summary row */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 min-w-0">
            <FileText size={16} className="text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-white truncate">{report.fileName}</p>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                {/* Report type pill */}
                <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border", typeMeta.color)}>
                  {typeMeta.icon}{typeMeta.label}
                </span>
                <span className="flex items-center gap-1 text-xs text-slate-400">
                  <Clock size={10} />{dateStr} · {timeStr}
                </span>
                <Badge variant="outline" className="text-[10px]">{report.pageCount}p</Badge>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className={cn("flex items-center gap-1 text-xs font-medium", statusMeta.color)}>
              <StatusIcon size={12} className={report.status === "processing" ? "animate-spin" : ""} />
              {statusMeta.label}
            </span>
            <ChevronDown size={14} className={cn("text-slate-500 transition-transform", open && "rotate-180")} />
          </div>
        </div>

        {/* Drawer */}
        {open && (
          <div className="pt-2 border-t border-slate-700/60" onClick={(e) => e.stopPropagation()}>
            {/* Tab bar */}
            <div className="flex gap-1 mb-3">
              {(["extracted", "ocr"] as DrawerTab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => onTabChange(t)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition",
                    tab === t ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200 hover:bg-slate-700"
                  )}
                >
                  {t === "extracted" ? <Beaker size={11} /> : <Eye size={11} />}
                  {t === "extracted" ? "Extracted Values" : "OCR Output"}
                </button>
              ))}
            </div>

            {tab === "extracted" ? (
              <ExtractedTab results={report.extractedResults} status={report.status} />
            ) : (
              <OcrTab snippet={report.ocrSnippet} />
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

// ── Extracted values tab ──────────────────────
function ExtractedTab({ results, status }: { results: LabResult[]; status: MedicalReport["status"] }) {
  if (results.length === 0) {
    return (
      <p className="text-xs text-slate-500 italic py-2">
        {status === "processing" ? "Extraction in progress…" : "No structured values extracted from this report."}
      </p>
    );
  }
  return (
    <div className="space-y-1.5">
      {results.map((lr) => {
        const s = labStatus(lr);
        return (
          <div key={lr.id} className="flex items-center justify-between gap-2 bg-slate-700/30 rounded-lg px-3 py-1.5">
            <span className="text-xs text-slate-300 font-medium">{lr.testName}</span>
            <div className="flex items-center gap-2">
              <span className={cn("text-xs font-bold tabular-nums", LAB_STATUS_COLORS[s])}>
                {lr.value} {lr.unit}
              </span>
              <span className="text-[10px] text-slate-500">({lr.referenceMin}–{lr.referenceMax})</span>
              <Badge variant={s === "normal" ? "success" : s === "critical" ? "danger" : "warning"} className="text-[10px]">
                {s}
              </Badge>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── OCR output tab ────────────────────────────
function OcrTab({ snippet }: { snippet?: string }) {
  if (!snippet) return <p className="text-xs text-slate-500 italic py-2">No OCR output available.</p>;
  const isPartial = snippet.includes("in progress");
  return (
    <div className="bg-slate-900/70 border border-slate-700/50 rounded-xl p-3">
      <div className="flex items-center gap-2 mb-2">
        <ScanLine size={11} className="text-slate-500" />
        <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wide">OCR Extracted Text</span>
        <Badge variant={isPartial ? "warning" : "success"} className="text-[10px] ml-auto">
          {isPartial ? "Partial" : "Readable"}
        </Badge>
      </div>
      <pre className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap font-mono">{snippet}</pre>
    </div>
  );
}
