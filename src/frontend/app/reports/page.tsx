/* Reports — Pipeline2 Layer 2 dual-path visualization */
"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import {
  FileText, CheckCircle, Clock, AlertCircle,
  ChevronDown, ChevronUp, Upload, Share2, Tag, Cpu,
} from "lucide-react";
import { Card, Badge, Section, EmptyState } from "@/components/ui/shared";
import { DEMO_REPORTS, DEMO_PATIENTS, labStatus, MedicalReport, LabResult, PipelineStage } from "@/lib/demo-data";
import { useToast } from "@/components/ui/toast";
import { cn } from "@/lib/utils";

// ── Simulated upload state ─────────────────────
interface UploadingFile {
  id: string;
  name: string;
  progress: number;
  status: "uploading" | "processing" | "ready";
}

// ── Lab history: group by test name across reports ─
function buildLabHistory(reports: MedicalReport[]) {
  const map = new Map<
    string,
    { date: string; value: number; unit: string; refMin: number; refMax: number }[]
  >();
  for (const r of reports) {
    for (const lr of r.extractedResults) {
      const existing = map.get(lr.testName) ?? [];
      existing.push({ date: lr.date, value: lr.value, unit: lr.unit, refMin: lr.referenceMin, refMax: lr.referenceMax });
      map.set(lr.testName, existing);
    }
  }
  return Array.from(map.entries()).map(([name, pts]) => ({
    name,
    points: pts.sort((a, b) => a.date.localeCompare(b.date)),
  }));
}

export default function ReportsPage() {
  const [patientId, setPatientId] = useState("pat-1");
  const [uploading, setUploading] = useState<UploadingFile[]>([]);
  const [addedReports, setAddedReports] = useState<MedicalReport[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const baseReports = DEMO_REPORTS.filter((r) => r.patientId === patientId);
  const allReports = [
    ...baseReports,
    ...addedReports.filter((r) => r.patientId === patientId),
  ].sort((a, b) => b.uploadedAt.localeCompare(a.uploadedAt));

  const labHistory = buildLabHistory(allReports.filter((r) => r.status === "ready"));

  // ── Simulate an upload ──────────────────────
  function simulateUpload(file: File) {
    if (file.size > 20 * 1024 * 1024) {
      toast({ title: "File too large", description: "Maximum file size is 20 MB.", variant: "error" });
      return;
    }
    const id = `upload-${Date.now()}`;
    setUploading((prev) => [...prev, { id, name: file.name, progress: 0, status: "uploading" }]);

    let pct = 0;
    const interval = setInterval(() => {
      pct += Math.random() * 18 + 8;
      if (pct >= 100) {
        clearInterval(interval);
        setUploading((prev) => prev.map((u) => u.id === id ? { ...u, progress: 100, status: "processing" } : u));
        setTimeout(() => {
          setUploading((prev) => prev.filter((u) => u.id !== id));
          const newReport: MedicalReport = {
            id,
            patientId,
            fileName: file.name,
            uploadedAt: new Date().toISOString(),
            status: "ready",
            pipelineStage: "ready",
            reportType: "Blood Test",
            tags: ["General"],
            chunkCount: Math.ceil(Math.random() * 8) + 3,
            pageCount: Math.ceil(Math.random() * 4) + 1,
            extractedResults: [],
          };
          setAddedReports((prev) => [...prev, newReport]);
          toast({ title: "Report ready", description: `${file.name} processed successfully.`, variant: "success" });
        }, 2500);
      } else {
        setUploading((prev) => prev.map((u) => u.id === id ? { ...u, progress: Math.round(pct) } : u));
      }
    }, 200);
  }

  function handleFiles(files: FileList | null) {
    if (!files) return;
    Array.from(files).forEach((f) => {
      if (/\.(pdf|jpg|jpeg|png)$/i.test(f.name)) {
        simulateUpload(f);
      } else {
        toast({ title: "Unsupported format", description: `${f.name} — only PDF/JPG/PNG allowed.`, variant: "warning" });
      }
    });
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
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

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        className={cn(
          "border-2 border-dashed rounded-xl p-8 flex flex-col items-center gap-2 cursor-pointer transition-all",
          dragOver
            ? "border-blue-500 bg-blue-900/10 text-blue-400"
            : "border-slate-700 text-slate-500 hover:border-slate-500 hover:bg-slate-800/30"
        )}
      >
        <Upload size={28} />
        <p className="text-sm font-medium">Drop PDF / JPG / PNG here, or click to browse</p>
        <p className="text-xs opacity-70">Max 20 MB per file</p>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          multiple
          className="hidden"
          onChange={(e: ChangeEvent<HTMLInputElement>) => handleFiles(e.target.files)}
        />
      </div>

      {/* Upload progress items */}
      {uploading.length > 0 && (
        <div className="space-y-2">
          {uploading.map((u) => (
            <Card key={u.id} className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 min-w-0">
                  {u.status === "processing"
                    ? <Clock size={14} className="text-amber-400 flex-shrink-0 animate-spin" />
                    : <Upload size={14} className="text-blue-400 flex-shrink-0" />}
                  <span className="text-sm text-white truncate">{u.name}</span>
                </div>
                <Badge variant={u.status === "processing" ? "warning" : "info"}>
                  {u.status === "processing" ? "Processing OCR…" : `${u.progress}%`}
                </Badge>
              </div>
              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-200",
                    u.status === "processing" ? "bg-amber-500 w-full animate-pulse" : "bg-blue-500"
                  )}
                  style={u.status === "uploading" ? { width: `${u.progress}%` } : undefined}
                />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Report Timeline */}
      <Section
        title="Report Timeline"
        subtitle={`${allReports.length} report${allReports.length !== 1 ? "s" : ""}`}
      >
        {allReports.length === 0 ? (
          <EmptyState message="No reports uploaded yet." icon={<FileText />} />
        ) : (
          <div className="space-y-3">
            {allReports.map((report) => (
              <ReportCard
                key={report.id}
                report={report}
                onShare={() =>
                  toast({
                    title: "Shared with doctor",
                    description: `${report.fileName} sent to your assigned doctor.`,
                    variant: "success",
                  })
                }
              />
            ))}
          </div>
        )}
      </Section>

      {/* Lab History Timeline */}
      {labHistory.length > 0 && (
        <Section title="Lab History Timeline" subtitle="Values across all reports">
          <div className="space-y-3">
            {labHistory.map(({ name, points }) => (
              <LabHistoryRow key={name} name={name} points={points} />
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// ── Pipeline Stage Indicator (Layer 2 dual-path) ─
const PIPELINE_STEPS: { key: PipelineStage; label: string; path?: "A" | "B" }[] = [
  { key: "uploaded",   label: "Stored"    },
  { key: "ocr_running",label: "OCR"       },
  { key: "extracting", label: "Structured", path: "A" },
  { key: "embedding",  label: "Embedded",   path: "B" },
  { key: "ready",      label: "Ready"      },
];
const STAGE_ORDER: PipelineStage[] = ["uploaded","ocr_running","extracting","embedding","ready"];

function PipelineIndicator({ stage }: { stage: PipelineStage }) {
  const currentIdx = STAGE_ORDER.indexOf(stage);
  return (
    <div className="flex items-center gap-1 overflow-x-auto py-1">
      {PIPELINE_STEPS.map((step, i) => {
        const idx = STAGE_ORDER.indexOf(step.key);
        const done    = idx < currentIdx;
        const current = idx === currentIdx;
        return (
          <div key={step.key} className="flex items-center">
            <div className={cn(
              "flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium whitespace-nowrap transition-all",
              done    ? "bg-emerald-900/60 text-emerald-400 border border-emerald-700/40" :
              current ? "bg-blue-900/60 text-blue-300 border border-blue-600/50 animate-pulse" :
                        "bg-slate-800 text-slate-500 border border-slate-700"
            )}>
              {done ? <CheckCircle size={9}/> : current ? <Clock size={9}/> : <span className="w-2 h-2 rounded-full bg-slate-600 inline-block"/>}
              {step.label}
              {step.path && <span className="opacity-60 ml-0.5">({step.path})</span>}
            </div>
            {i < PIPELINE_STEPS.length - 1 && (
              <span className="text-slate-700 mx-0.5 text-[10px]">›</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Report Card ───────────────────────────────
function ReportCard({ report, onShare }: { report: MedicalReport; onShare: () => void }) {
  const [expanded, setExpanded] = useState(false);

  const statusIcon = {
    ready:      <CheckCircle size={14} className="text-emerald-400" />,
    processing: <Clock       size={14} className="text-amber-400" />,
    error:      <AlertCircle size={14} className="text-red-400" />,
  }[report.status];

  const statusBadge = {
    ready:      <Badge variant="success">Ready</Badge>,
    processing: <Badge variant="warning">Processing</Badge>,
    error:      <Badge variant="danger">Error</Badge>,
  }[report.status];

  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded((v) => !v)}>
        <div className="flex items-center gap-3 min-w-0">
          <div className="h-9 w-9 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
            {statusIcon}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-white truncate">{report.fileName}</p>
            <p className="text-xs text-slate-400">
              {new Date(report.uploadedAt).toLocaleDateString("en-IN", {
                day: "numeric", month: "short", year: "numeric",
              })}{" "}
              · {report.pageCount} page{report.pageCount !== 1 ? "s" : ""}
              {report.reportType && ` · ${report.reportType}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {statusBadge}
          {report.status === "ready" && (
            <button
              onClick={(e) => { e.stopPropagation(); onShare(); }}
              title="Share with doctor"
              className="text-slate-500 hover:text-blue-400 transition-colors"
            >
              <Share2 size={14} />
            </button>
          )}
          {expanded ? <ChevronUp size={14} className="text-slate-400" /> : <ChevronDown size={14} className="text-slate-400" />}
        </div>
      </div>

      {/* Pipeline Stage — always visible */}
      <PipelineIndicator stage={report.pipelineStage ?? (report.status === "ready" ? "ready" : "ocr_running")} />

      {/* Tags + chunk count */}
      {(report.tags?.length || report.chunkCount) && (
        <div className="flex items-center gap-2 flex-wrap">
          {report.tags?.map((t) => (
            <span key={t} className="flex items-center gap-1 text-[10px] bg-slate-700 text-slate-300 rounded px-2 py-0.5">
              <Tag size={8}/>{t}
            </span>
          ))}
          {report.chunkCount ? (
            <span className="flex items-center gap-1 text-[10px] bg-slate-700/60 text-slate-400 rounded px-2 py-0.5">
              <Cpu size={8}/>{report.chunkCount} chunks embedded (Path B)
            </span>
          ) : null}
        </div>
      )}

      {expanded && report.extractedResults.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                <th className="text-left py-1.5 pr-3 font-medium">Test</th>
                <th className="text-right py-1.5 pr-3 font-medium">Value</th>
                <th className="text-right py-1.5 pr-3 font-medium">Unit</th>
                <th className="text-right py-1.5 font-medium">Reference</th>
              </tr>
            </thead>
            <tbody>
              {report.extractedResults.map((r) => {
                const s = labStatus(r);
                const color = { normal: "text-emerald-400", low: "text-amber-400", high: "text-orange-400", critical: "text-red-400" }[s];
                return (
                  <tr key={r.id} className="border-b border-slate-800">
                    <td className="py-1.5 pr-3 text-slate-200">{r.testName}</td>
                    <td className={cn("text-right pr-3 font-semibold", color)}>{r.value}</td>
                    <td className="text-right pr-3 text-slate-400">{r.unit}</td>
                    <td className="text-right text-slate-500">{r.referenceMin}–{r.referenceMax}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {expanded && report.extractedResults.length === 0 && (
        <p className="text-xs text-slate-500 italic">
          {report.status === "processing" ? "Extracting lab values…" : "No structured data extracted."}
        </p>
      )}
    </Card>
  );
}

// ── Lab History Row ───────────────────────────
function LabHistoryRow({
  name,
  points,
}: {
  name: string;
  points: { date: string; value: number; unit: string; refMin: number; refMax: number }[];
}) {
  const latest = points[points.length - 1];
  const s = labStatus({
    value: latest.value,
    referenceMin: latest.refMin,
    referenceMax: latest.refMax,
  } as LabResult);
  const valueColor = {
    normal:   "text-emerald-400",
    low:      "text-amber-400",
    high:     "text-orange-400",
    critical: "text-red-400",
  }[s];

  return (
    <Card className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-white">{name}</p>
        <div className="flex items-center gap-2">
          <span className={cn("text-sm font-bold", valueColor)}>
            {latest.value}{" "}
            <span className="text-xs font-normal text-slate-400">{latest.unit}</span>
          </span>
          <Badge variant="outline" className="text-[10px]">Latest</Badge>
        </div>
      </div>

      {/* Timeline dots */}
      <div className="flex items-end gap-4 overflow-x-auto pb-1 pt-1">
        {points.map((pt, i) => {
          const ps = labStatus({ value: pt.value, referenceMin: pt.refMin, referenceMax: pt.refMax } as LabResult);
          const dotColor  = { normal: "bg-emerald-400", low: "bg-amber-400", high: "bg-orange-400", critical: "bg-red-400" }[ps];
          const textColor = { normal: "text-emerald-400", low: "text-amber-400", high: "text-orange-400", critical: "text-red-400" }[ps];
          const isLast = i === points.length - 1;
          return (
            <div key={i} className="flex flex-col items-center gap-1 flex-shrink-0">
              <span className={cn("text-xs font-semibold", textColor)}>{pt.value}</span>
              <div className={cn("h-2.5 w-2.5 rounded-full", dotColor, isLast && "ring-2 ring-white ring-offset-1 ring-offset-slate-800")} />
              <span className="text-[9px] text-slate-500">
                {new Date(pt.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
              </span>
            </div>
          );
        })}
      </div>

      <p className="text-[10px] text-slate-600">
        Ref: {latest.refMin}–{latest.refMax} {latest.unit}
      </p>
    </Card>
  );
}
