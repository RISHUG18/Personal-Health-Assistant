# HealthAI — AI-Powered Health Companion (Frontend)

A Next.js 16 frontend for the HealthAI system — an AI-powered personal health companion that analyses medical reports, wearable data, and environmental context to surface insights and alerts.

> **Week 1–4 milestone (Person 5):** All UI screens are complete with full synthetic demo data.  
> No real backend is required to run the demo.

---

## Project Overview

HealthAI helps users understand their health by combining:

- **Medical reports** (uploaded PDFs → OCR → structured extraction)
- **Wearable data** (steps, sleep, heart rate via Health Connect / HealthKit)
- **Environmental context** (AQI, temperature, humidity from OpenWeather / OpenAQ)
- **Deterministic rules engine** (generates alerts without any LLM)
- **Gemini 2.5 Flash RAG pipeline** (grounds AI answers in actual report data)

---

## Pipeline Summary

```
Upload PDF → OCR
              ↙              ↘
   Structured DB          Vector DB (pgvector)
        ↓                       ↓
Environmental DB             RAG Retrieval
        ↓                       ↓
    Rules Engine (context-aware, no LLM)
                   ↓
            Context Builder
                   ↓
         Gemini 2.5 Flash
                   ↓
     User App  /  Doctor Dashboard
```

---

## Frontend Screens

| Route | Description |
|---|---|
| `/dashboard` | Daily summary, health metrics, active alert banner |
| `/alerts` | Rules-engine alerts with severity, evidence drawer, acknowledge/dismiss |
| `/reports` | Chronological report timeline with extracted lab values + OCR preview |
| `/trends` | 7-day bar charts for steps, sleep, heart rate |
| `/chat` | AI companion chat (stub → Gemini in Week 3) |
| `/environment` | AQI panel, temperature, humidity, tooltip explainers |
| `/doctor` | Doctor dashboard: patient list by priority, alert + report drill-down |
| `/profile` | Data-sharing and doctor-access consent toggles |
| `/personas` | Demo personas with expected questions and demo flow |
| `/demo-validation` | Automated data integrity checks — reports to backend team |

---

## Component Structure

```
components/
  AppShell.tsx              — Root shell: sidebar + toast provider
  nav/
    Navigation.tsx          — Sidebar (desktop) + BottomNav (mobile)
  ui/
    shared.tsx              — Design system: Card, Badge, SeverityBadge,
                              StatCard, Section, EmptyState, Spinner,
                              labStatusColor, aqiColor, aqiLabel
    toast.tsx               — Global toast notification system
  dashboard/
    DummyCards.tsx          — Reusable static UI components:
                              · PatientSummaryCard
                              · HealthMetricCards
                              · AlertBanner
                              · PlaceholderBarChart  ← Week 1
                              · SummaryTile          ← Week 1
                              · PlaceholderDonut     ← Week 1 (AQI gauge)
                              · SparkLine            ← Week 1
```

---

## Synthetic Demo Data

All demo data lives in `lib/demo-data.ts` — no backend or database needed.

### Fake Medical PDFs (labelled by report type)

| File | Patient | Report Type | Key Finding |
|---|---|---|---|
| `CBC_Report_Jan2026.pdf` | Riya Sharma | `blood_test` | Hb 9.8 g/dL (LOW), Serum Iron 42 (LOW) |
| `Lipid_Panel_Mar2026.pdf` | Riya Sharma | `lipid_panel` | LDL 138 mg/dL (HIGH) |
| `Lipid_Panel_Jan2026.pdf` | Karan Patel | `lipid_panel` | LDL 118 (HIGH), HDL 48 (LOW) |
| `HbA1c_Feb2026.pdf` | Karan Patel | `diabetes` | HbA1c 7.8% (HIGH — diabetic range) |
| `Thyroid_Feb2026.pdf` | Meera Iyer | `thyroid` | Processing (OCR quality poor) |

Each report includes an `ocrSnippet` field simulating real OCR text output — visible in the Reports timeline and validated in Demo QA.
| `/environment` | AQI panel, temperature, humidity, tooltip explainers |
| `/doctor` | Doctor view: patient list, alert priority, report access |
| `/profile` | Data-sharing toggles, doctor access consent switches |

---

## Demo Personas

### 👩 Riya Sharma (pat-1) — User Persona
- 28-year-old female, Chennai
- Blood reports: **Iron deficiency anaemia** (Hb 9.8, Serum Iron 42)
- Elevated cholesterol (LDL 138)
- Sleep average: 5.8 hrs/day
- Chennai heatwave + AQI 145 → environment-aware alerts

### 👨 Karan Patel (pat-2) — User Persona  
- 45-year-old male, Bangalore  
- **HbA1c 7.8%** (diabetic range), Fasting Glucose 142  
- Otherwise good activity levels  
- Bangalore conditions: normal (AQI 85)

### 👩 Meera Iyer (pat-3) — User Persona
- 35-year-old female, Mumbai  
- Report in processing state  
- Mumbai AQI 162, poor air quality alert

### 👨‍⚕️ Dr. Priya Nair (doc-1) — Doctor Persona
- General Physician, Apollo Hospitals Chennai  
- Assigned to Riya Sharma and Karan Patel  
- Demo question: *"Which patients need urgent review?"* → Riya (3 active alerts)

---

## Demo Flow

1. Open `/dashboard` — see Riya's health summary with heatwave + low-iron alert banner
2. Open `/alerts` — explore the 3 active alerts; click any to see evidence; acknowledge one
3. Open `/reports` — view the report timeline; expand CBC report to see extracted lab values
4. Open `/environment` — see Chennai AQI 145 + heatwave badge; read tooltip explanations
5. Open `/chat` — ask "Why am I feeling tired?" — AI response cites iron + sleep + heat
6. Open `/doctor` — switch to doctor view; see Riya ranked first by alert count; drill in
7. Open `/profile` — toggle doctor access and data-sharing permissions

---

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Tech Stack

- **Next.js 16** (App Router, TypeScript)
- **Tailwind CSS v4**
- **Radix UI** (Dialog, Tabs)
- **Lucide React** icons
- All demo data in `lib/demo-data.ts` — no backend needed for Week 1–4

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
