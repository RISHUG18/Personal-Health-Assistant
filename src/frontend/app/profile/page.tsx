/* Week 2 – Profile / Consent UI (static, Person 5) */
"use client";

import { useState } from "react";
import { Trash2, ChevronRight } from "lucide-react";
import { Card, Badge, Section } from "@/components/ui/shared";
import { DEMO_PATIENTS, DEMO_DOCTORS } from "@/lib/demo-data";

const CONSENT_ITEMS = [
  {
    id: "store_reports",
    label: "Store medical reports",
    description: "Allow HealthCompanion to securely store uploaded PDFs in Supabase Storage.",
    default: true,
  },
  {
    id: "extract_labs",
    label: "Extract lab values",
    description: "Allow the OCR pipeline to extract and structure lab results from your reports.",
    default: true,
  },
  {
    id: "ai_analysis",
    label: "AI-powered analysis",
    description: "Allow Gemini to generate health summaries using your data as context.",
    default: true,
  },
  {
    id: "share_doctor",
    label: "Share data with assigned doctor",
    description: "Allow your assigned doctor to view your reports, alerts, and health metrics.",
    default: true,
  },
  {
    id: "env_context",
    label: "Use location for environmental context",
    description: "Allow the system to fetch weather and AQI data for your city to enrich AI context.",
    default: true,
  },
  {
    id: "notifications",
    label: "Push notifications",
    description: "Receive push notifications for high-priority alerts.",
    default: false,
  },
];

export default function ProfilePage() {
  const patient = DEMO_PATIENTS[0];
  const doctor = DEMO_DOCTORS.find((d) => d.id === patient.assignedDoctorId)!;
  const [consents, setConsents] = useState<Record<string, boolean>>(
    Object.fromEntries(CONSENT_ITEMS.map((c) => [c.id, c.default]))
  );

  const toggle = (id: string) => {
    if (id === "store_reports") return; // cannot revoke core consent
    setConsents((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
      <h1 className="text-xl font-bold text-white">Profile & Settings</h1>

      {/* Patient info */}
      <Section title="Your Details">
        <Card className="space-y-3">
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-full bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center text-white text-xl font-bold">
              {patient.name[0]}
            </div>
            <div>
              <p className="font-semibold text-white">{patient.name}</p>
              <p className="text-xs text-slate-400">{patient.age} years · {patient.gender} · {patient.bloodGroup}</p>
              <p className="text-xs text-slate-500">{patient.city}, {patient.pincode}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-700">
            {[
              { label: "City", value: patient.city },
              { label: "Pincode", value: patient.pincode },
              { label: "Blood Group", value: patient.bloodGroup },
              { label: "Patient ID", value: patient.id },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-[10px] text-slate-500">{label}</p>
                <p className="text-xs text-slate-200">{value}</p>
              </div>
            ))}
          </div>
        </Card>
      </Section>

      {/* Assigned doctor */}
      <Section title="Assigned Doctor">
        <Card className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-teal-600/20 border border-teal-600/40 flex items-center justify-center">
            <span className="text-teal-400 text-sm font-bold">{doctor.name[3]}</span>
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-white">{doctor.name}</p>
            <p className="text-xs text-slate-400">{doctor.specialization}</p>
            <p className="text-xs text-slate-500">{doctor.hospital}</p>
          </div>
          <ChevronRight size={14} className="text-slate-600" />
        </Card>
      </Section>

      {/* Data & Privacy / Consent */}
      <Section
        title="Data & Privacy"
        subtitle="You control what data is used and how."
      >
        <div className="space-y-2">
          {CONSENT_ITEMS.map((item) => {
            const enabled = consents[item.id];
            const locked = item.id === "store_reports";
            return (
              <Card key={item.id} className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-white">{item.label}</p>
                    {locked && <Badge variant="outline" className="text-[10px]">Required</Badge>}
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{item.description}</p>
                </div>
                <button
                  onClick={() => toggle(item.id)}
                  disabled={locked}
                  className={`relative inline-flex h-5 w-9 flex-shrink-0 rounded-full transition-colors duration-200 mt-0.5
                    ${enabled ? "bg-blue-600" : "bg-slate-700"}
                    ${locked ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200 mt-0.5
                      ${enabled ? "translate-x-4" : "translate-x-0.5"}`}
                  />
                </button>
              </Card>
            );
          })}
        </div>
      </Section>

      {/* Danger zone */}
      <Section title="Danger Zone">
        <Card className="border-red-800/40 bg-red-900/10 space-y-3">
          <div className="flex items-start gap-3">
            <Trash2 size={14} className="text-red-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-300">Delete all my data</p>
              <p className="text-xs text-slate-400">Permanently removes all reports, lab results, health metrics, and AI conversation history. This cannot be undone.</p>
            </div>
            <button className="text-xs bg-red-900/40 border border-red-700/50 text-red-400 hover:bg-red-800/40 px-3 py-1.5 rounded-lg transition-colors flex-shrink-0">
              Delete
            </button>
          </div>
        </Card>
      </Section>

      {/* System info */}
      <Section title="System">
        <div className="space-y-1 text-xs text-slate-500">
          {[
            ["Storage", "Supabase Storage (encrypted at rest)"],
            ["Vector DB", "Supabase pgvector"],
            ["AI Model", "Gemini 2.5 Flash"],
            ["Embeddings", "BAAI/bge-base-en-v1.5"],
            ["Version", "1.0.0-mvp (Release 1)"],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between border-b border-slate-800 py-1.5">
              <span>{k}</span>
              <span className="text-slate-400">{v}</span>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}
