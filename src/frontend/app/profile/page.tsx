/* Profile & Consent — data sharing toggles (Person 5 Week 2) */
"use client";

import { useState } from "react";
import { User, Shield, Bell, Stethoscope, Eye, EyeOff } from "lucide-react";
import { Card, Badge, Section } from "@/components/ui/shared";
import { DEMO_PATIENTS, DEMO_DOCTORS } from "@/lib/demo-data";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";

const patient = DEMO_PATIENTS[0];
const doctor = DEMO_DOCTORS[0];

interface Toggle {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  category: "sharing" | "notifications" | "doctor";
}

const TOGGLES: Toggle[] = [
  {
    id: "share_health_metrics",
    label: "Share Health Metrics",
    description: "Allow the AI system to read your steps, sleep, and heart rate for insights.",
    icon: <Eye size={15} />,
    category: "sharing",
  },
  {
    id: "share_lab_results",
    label: "Share Lab Results",
    description: "Allow AI to reference extracted lab values when answering your questions.",
    icon: <Eye size={15} />,
    category: "sharing",
  },
  {
    id: "share_environment",
    label: "Share Location (Coarse)",
    description: "Use your city-level location to fetch air quality and weather context.",
    icon: <Eye size={15} />,
    category: "sharing",
  },
  {
    id: "alerts_push",
    label: "Push Notifications",
    description: "Receive real-time alerts on your device when new health flags are raised.",
    icon: <Bell size={15} />,
    category: "notifications",
  },
  {
    id: "alerts_weekly",
    label: "Weekly Summary Email",
    description: "Get a weekly health summary delivered to your email address.",
    icon: <Bell size={15} />,
    category: "notifications",
  },
  {
    id: "doctor_view_reports",
    label: "Doctor Can View Reports",
    description: `Allow ${doctor.name} to view your uploaded medical reports.`,
    icon: <Stethoscope size={15} />,
    category: "doctor",
  },
  {
    id: "doctor_add_comments",
    label: "Doctor Can Add Comments",
    description: `Allow ${doctor.name} to annotate your reports with clinical notes.`,
    icon: <Stethoscope size={15} />,
    category: "doctor",
  },
  {
    id: "doctor_view_metrics",
    label: "Doctor Can See Metrics",
    description: `Allow ${doctor.name} to view your daily activity and sleep metrics.`,
    icon: <Stethoscope size={15} />,
    category: "doctor",
  },
];

export default function ProfilePage() {
  const { toast } = useToast();
  const [enabled, setEnabled] = useState<Record<string, boolean>>({
    share_health_metrics: true,
    share_lab_results: true,
    share_environment: true,
    alerts_push: true,
    alerts_weekly: false,
    doctor_view_reports: true,
    doctor_add_comments: true,
    doctor_view_metrics: false,
  });

  function toggle(id: string) {
    setEnabled((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      const label = TOGGLES.find((t) => t.id === id)?.label ?? id;
      toast({
        title: next[id] ? "Permission enabled" : "Permission disabled",
        description: label,
        variant: next[id] ? "success" : "info",
      });
      return next;
    });
  }

  const categories: { key: Toggle["category"]; label: string; subtitle: string }[] = [
    { key: "sharing",       label: "Data Sharing",        subtitle: "Control what the AI system can access" },
    { key: "notifications", label: "Notifications",       subtitle: "Manage alerts and weekly summaries" },
    { key: "doctor",        label: "Doctor Access",       subtitle: `Permissions for ${doctor.name}` },
  ];

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
      <h1 className="text-xl font-bold text-white">Profile & Consent</h1>

      {/* Patient card */}
      <Card>
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
            {patient.name[0]}
          </div>
          <div className="space-y-1 min-w-0">
            <p className="font-semibold text-white text-base">{patient.name}</p>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline">{patient.age} yrs</Badge>
              <Badge variant="outline">{patient.gender}</Badge>
              <Badge variant="outline">{patient.bloodGroup}</Badge>
              <Badge variant="outline">{patient.city}</Badge>
            </div>
          </div>
        </div>

        <div className="divider my-4" />

        <div className="flex items-center gap-3">
          <Shield size={15} className="text-blue-400 flex-shrink-0" />
          <p className="text-xs text-slate-400">
            Your data is encrypted at rest and in transit. Only you and your authorised doctor
            can view identifiable information.
          </p>
        </div>
      </Card>

      {/* Assigned doctor */}
      <Section title="Your Doctor">
        <Card>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-emerald-900/60 border border-emerald-700/50 flex items-center justify-center">
              <Stethoscope size={16} className="text-emerald-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">{doctor.name}</p>
              <p className="text-xs text-slate-400">{doctor.specialization} · {doctor.hospital}</p>
            </div>
          </div>
        </Card>
      </Section>

      {/* Permission toggles */}
      {categories.map(({ key, label, subtitle }) => (
        <Section key={key} title={label} subtitle={subtitle}>
          <div className="space-y-2">
            {TOGGLES.filter((t) => t.category === key).map((toggle_item) => (
              <ToggleRow
                key={toggle_item.id}
                item={toggle_item}
                on={enabled[toggle_item.id] ?? false}
                onToggle={() => toggle(toggle_item.id)}
              />
            ))}
          </div>
        </Section>
      ))}

      {/* Footer note */}
      <p className="text-xs text-slate-600 text-center pb-4">
        Permissions apply only within this demo. No real data is transmitted.
      </p>
    </div>
  );
}

function ToggleRow({
  item,
  on,
  onToggle,
}: {
  item: Toggle;
  on: boolean;
  onToggle: () => void;
}) {
  return (
    <Card className="flex items-center justify-between gap-4">
      <div className="flex items-start gap-3 min-w-0">
        <span className={cn("mt-0.5 flex-shrink-0", on ? "text-blue-400" : "text-slate-600")}>
          {on ? item.icon : <EyeOff size={15} />}
        </span>
        <div className="min-w-0">
          <p className="text-sm font-medium text-white">{item.label}</p>
          <p className="text-xs text-slate-400 mt-0.5">{item.description}</p>
        </div>
      </div>
      <button
        role="switch"
        aria-checked={on}
        onClick={onToggle}
        className={cn(
          "relative flex-shrink-0 w-11 h-6 rounded-full transition-colors duration-200 focus-visible:ring-2 ring-blue-500",
          on ? "bg-blue-600" : "bg-slate-700"
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform duration-200",
            on && "translate-x-5"
          )}
        />
      </button>
    </Card>
  );
}
