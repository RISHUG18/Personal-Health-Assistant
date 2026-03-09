/* Demo Personas — 2 user personas + 1 doctor persona with expected demo questions (Person 5 Week 1) */
import { User, Stethoscope, MessageCircle, AlertTriangle, FileText } from "lucide-react";
import { Card, Badge, Section } from "@/components/ui/shared";
import { DEMO_DOCTORS } from "@/lib/demo-data";

// ── Persona definitions ──────────────────────
const USER_PERSONAS = [
  {
    id: "pat-1",
    name: "Riya Sharma",
    age: 28,
    gender: "Female",
    city: "Chennai",
    bloodGroup: "B+",
    occupation: "Software Engineer",
    healthProfile: [
      "Iron deficiency anaemia (Hb 9.8 g/dL)",
      "Elevated LDL cholesterol (138 mg/dL)",
      "Chronic sleep deprivation (avg 5.8h/night)",
      "Low physical activity during heatwave periods",
    ],
    environmentalContext: [
      "Chennai heatwave — max 38°C",
      "AQI 145 (Unhealthy for Sensitive Groups)",
      "High humidity (82%)",
    ],
    demoQuestions: [
      "Why am I feeling so tired lately?",
      "My haemoglobin is 9.8 — is that serious?",
      "What can I eat to improve my iron levels?",
      "Is the heat in Chennai affecting my sleep?",
      "Should I be concerned about my cholesterol?",
      "What lifestyle changes can help me sleep better?",
    ],
    alertsExpected: ["Iron Deficiency Anaemia", "Fatigue Risk — Heat + Low Iron", "Poor Air Quality"],
    accent: "from-blue-500 to-purple-600",
  },
  {
    id: "pat-2",
    name: "Karan Patel",
    age: 45,
    gender: "Male",
    city: "Bangalore",
    bloodGroup: "O+",
    occupation: "Operations Manager",
    healthProfile: [
      "HbA1c 7.8% — diabetic range",
      "Fasting glucose 142 mg/dL (elevated)",
      "Good activity levels (avg 7,800 steps/day)",
      "Consistent sleep (avg 6.8h/night)",
    ],
    environmentalContext: [
      "Bangalore — moderate conditions",
      "AQI 85 (Moderate)",
      "Temperature avg 23°C",
    ],
    demoQuestions: [
      "My HbA1c is 7.8% — what does that mean?",
      "How can I lower my blood sugar through diet?",
      "I walk 8,000 steps a day — is that enough?",
      "What are the risks if I don't manage my glucose levels?",
      "How often should I retest my HbA1c?",
      "Are there any patterns in my data I should know about?",
    ],
    alertsExpected: ["Elevated HbA1c — Diabetic Range"],
    accent: "from-emerald-500 to-teal-600",
  },
];

const DOCTOR_PERSONA = {
  name: DEMO_DOCTORS[0].name,
  specialization: DEMO_DOCTORS[0].specialization,
  hospital: DEMO_DOCTORS[0].hospital,
  responsibilities: [
    "Review flagged patient alerts in priority order",
    "Access uploaded medical reports and extracted values",
    "Add clinical annotations to specific lab results",
    "Track patient health trends across multiple reports",
    "Use AI-generated summaries as a starting point for review",
  ],
  demoQuestions: [
    "Which of my patients needs urgent review today?",
    "Show me Riya Sharma's CBC report findings.",
    "What trends do you see in Karan Patel's glucose over time?",
    "Has the heatwave in Chennai affected any patients?",
    "Summarise the key health issues for my patient list.",
  ],
  workflowSteps: [
    "Log in → see patient list sorted by alert severity",
    "Click Riya Sharma → see 3 active alerts (iron, heat-fatigue, AQI)",
    "Expand CBC report → view extracted Hb and iron values side-by-side",
    "Check environmental context → Chennai heatwave badge visible",
    "Click Karan Patel → see HbA1c alert (acknowledged)",
  ],
};

export default function PersonasPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-8">
      <div>
        <h1 className="text-xl font-bold text-white">Demo Personas</h1>
        <p className="text-xs text-slate-400 mt-1">
          2 user personas and 1 doctor persona — use these during demo walkthroughs and testing.
        </p>
      </div>

      {/* User personas */}
      <Section title="User Personas" subtitle="Patients using the mobile health companion app">
        <div className="space-y-6">
          {USER_PERSONAS.map((p) => (
            <PersonaCard key={p.id} persona={p} />
          ))}
        </div>
      </Section>

      {/* Doctor persona */}
      <Section title="Doctor Persona" subtitle="Medical professional using the web dashboard">
        <DoctorPersonaCard />
      </Section>

      {/* Demo flow summary */}
      <Section title="Recommended Demo Flow">
        <Card className="space-y-3">
          {[
            { step: "1", label: "Dashboard", desc: "Open Riya's dashboard → see heatwave banner, 3 active alerts, declining trend" },
            { step: "2", label: "Alerts",    desc: "Click alerts → expand Iron Deficiency alert → read evidence, acknowledge one" },
            { step: "3", label: "Reports",   desc: "Open reports → expand CBC → see Hb 9.8 flagged critical in red" },
            { step: "4", label: "Environment", desc: "Open environment → AQI 145 badge, heatwave, tooltip explains health impact" },
            { step: "5", label: "AI Chat",   desc: 'Ask "Why am I so tired?" → AI cites iron, sleep, and heat from reports' },
            { step: "6", label: "Doctor View", desc: "Switch to doctor → Riya ranked #1 by alert count → drill into her detail" },
            { step: "7", label: "Profile",   desc: "Toggle doctor access off → toast confirms change → UI only" },
            { step: "8", label: "Demo QA",   desc: "Open Demo QA → all checks pass → show to backend team" },
          ].map(({ step, label, desc }) => (
            <div key={step} className="flex items-start gap-3">
              <span className="flex-shrink-0 h-6 w-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">
                {step}
              </span>
              <div>
                <p className="text-sm font-medium text-white">{label}</p>
                <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
        </Card>
      </Section>
    </div>
  );
}

function PersonaCard({ persona }: { persona: typeof USER_PERSONAS[0] }) {
  return (
    <Card className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className={`h-12 w-12 rounded-full bg-gradient-to-br ${persona.accent} flex items-center justify-center text-white font-bold text-lg flex-shrink-0`}>
          {persona.name[0]}
        </div>
        <div>
          <p className="font-semibold text-white text-base">{persona.name}</p>
          <div className="flex flex-wrap gap-1.5 mt-1">
            <Badge variant="outline">{persona.age}y · {persona.gender}</Badge>
            <Badge variant="outline">{persona.city}</Badge>
            <Badge variant="outline">{persona.bloodGroup}</Badge>
            <Badge variant="outline">{persona.occupation}</Badge>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Health profile */}
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <FileText size={12} className="text-blue-400" />
            <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide">Health Profile</p>
          </div>
          <ul className="space-y-1">
            {persona.healthProfile.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                <span className="text-blue-400 mt-0.5 flex-shrink-0">→</span>{item}
              </li>
            ))}
          </ul>
        </div>

        {/* Environment */}
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <AlertTriangle size={12} className="text-amber-400" />
            <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide">Environment</p>
          </div>
          <ul className="space-y-1">
            {persona.environmentalContext.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                <span className="text-amber-400 mt-0.5 flex-shrink-0">→</span>{item}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Expected alerts */}
      <div>
        <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">Expected Alerts</p>
        <div className="flex flex-wrap gap-1.5">
          {persona.alertsExpected.map((a) => (
            <Badge key={a} variant="warning" className="text-[10px]">{a}</Badge>
          ))}
        </div>
      </div>

      {/* Demo questions */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <MessageCircle size={12} className="text-purple-400" />
          <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide">Expected Demo Questions</p>
        </div>
        <div className="space-y-1.5">
          {persona.demoQuestions.map((q, i) => (
            <div key={i} className="bg-slate-700/40 border border-slate-700/60 rounded-lg px-3 py-1.5">
              <p className="text-xs text-slate-300 italic">&ldquo;{q}&rdquo;</p>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

function DoctorPersonaCard() {
  const d = DOCTOR_PERSONA;
  return (
    <Card className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="h-12 w-12 rounded-full bg-emerald-900/60 border border-emerald-700/50 flex items-center justify-center flex-shrink-0">
          <Stethoscope size={18} className="text-emerald-400" />
        </div>
        <div>
          <p className="font-semibold text-white text-base">{d.name}</p>
          <div className="flex flex-wrap gap-1.5 mt-1">
            <Badge variant="success">{d.specialization}</Badge>
            <Badge variant="outline">{d.hospital}</Badge>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">Responsibilities</p>
          <ul className="space-y-1">
            {d.responsibilities.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                <span className="text-emerald-400 mt-0.5 flex-shrink-0">→</span>{r}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">Demo Workflow</p>
          <ol className="space-y-1">
            {d.workflowSteps.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                <span className="text-slate-500 flex-shrink-0 font-bold">{i + 1}.</span>{s}
              </li>
            ))}
          </ol>
        </div>
      </div>

      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <MessageCircle size={12} className="text-purple-400" />
          <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide">Expected Demo Questions</p>
        </div>
        <div className="space-y-1.5">
          {d.demoQuestions.map((q, i) => (
            <div key={i} className="bg-slate-700/40 border border-slate-700/60 rounded-lg px-3 py-1.5">
              <p className="text-xs text-slate-300 italic">&ldquo;{q}&rdquo;</p>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
