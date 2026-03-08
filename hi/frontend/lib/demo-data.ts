// ─────────────────────────────────────────────
//  Demo personas & synthetic data (Person 5)
// ─────────────────────────────────────────────

export type Severity = "low" | "medium" | "high" | "critical";
export type AlertCategory =
  | "lab"
  | "sleep"
  | "activity"
  | "environment"
  | "trend";
export type Season = "summer" | "monsoon" | "winter" | "spring";

// ── User / Patient ────────────────────────────
export interface Patient {
  id: string;
  name: string;
  age: number;
  gender: "male" | "female" | "other";
  city: string;
  pincode: string;
  bloodGroup: string;
  assignedDoctorId: string;
}

// ── Doctor ────────────────────────────────────
export interface Doctor {
  id: string;
  name: string;
  specialization: string;
  hospital: string;
}

// ── Lab Result ────────────────────────────────
export interface LabResult {
  id: string;
  patientId: string;
  testName: string;
  value: number;
  unit: string;
  referenceMin: number;
  referenceMax: number;
  date: string; // ISO
  reportId: string;
}

export type LabStatus = "normal" | "low" | "high" | "critical";

export function labStatus(r: LabResult): LabStatus {
  if (r.value < r.referenceMin * 0.8 || r.value > r.referenceMax * 1.2)
    return "critical";
  if (r.value < r.referenceMin) return "low";
  if (r.value > r.referenceMax) return "high";
  return "normal";
}

// ── Medical Report ────────────────────────────
export interface MedicalReport {
  id: string;
  patientId: string;
  fileName: string;
  uploadedAt: string;
  status: "processing" | "ready" | "error";
  pageCount: number;
  extractedResults: LabResult[];
}

// ── Alert ─────────────────────────────────────
export interface Alert {
  id: string;
  patientId: string;
  severity: Severity;
  category: AlertCategory;
  title: string;
  reason: string;
  evidence: string[];
  createdAt: string;
  acknowledged: boolean;
}

// ── Environmental Context ─────────────────────
export interface EnvironmentContext {
  patientId: string;
  date: string;
  city: string;
  temperature: { min: number; max: number; avg: number };
  humidity: number; // %
  aqi: number;
  pm25: number;
  pm10: number;
  season: Season;
  heatwave: boolean;
  poorAir: boolean;
}

// ── Health Metric (Google Fit / HealthConnect) ─
export interface HealthMetric {
  patientId: string;
  date: string;
  steps: number;
  sleepHours: number;
  heartRateAvg: number;
}

// ── Chat Message ──────────────────────────────
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: string[];
  timestamp: string;
}

// ── Week Summary ──────────────────────────────
export interface WeekSummary {
  patientId: string;
  weekLabel: string; // e.g. "Feb 24 – Mar 2"
  avgSteps: number;
  avgSleepHours: number;
  avgHeartRate: number;
  totalActiveAlerts: number;
  labFlags: number; // count of abnormal lab values
  trend: "improving" | "stable" | "declining";
  notes: string[];
}

// ── Trend Note ────────────────────────────────
export interface TrendNote {
  date: string;
  note: string;
  category: "lab" | "sleep" | "activity" | "environment";
}

// ─────────────────────────────────────────────
//  SYNTHETIC DEMO DATA
// ─────────────────────────────────────────────

export const DEMO_DOCTORS: Doctor[] = [
  {
    id: "doc-1",
    name: "Dr. Priya Nair",
    specialization: "General Physician",
    hospital: "Apollo Hospitals, Chennai",
  },
  {
    id: "doc-2",
    name: "Dr. Arjun Mehta",
    specialization: "Cardiologist",
    hospital: "Fortis, Bangalore",
  },
];

export const DEMO_PATIENTS: Patient[] = [
  {
    id: "pat-1",
    name: "Riya Sharma",
    age: 28,
    gender: "female",
    city: "Chennai",
    pincode: "600001",
    bloodGroup: "B+",
    assignedDoctorId: "doc-1",
  },
  {
    id: "pat-2",
    name: "Karan Patel",
    age: 45,
    gender: "male",
    city: "Bangalore",
    pincode: "560001",
    bloodGroup: "O+",
    assignedDoctorId: "doc-1",
  },
  {
    id: "pat-3",
    name: "Meera Iyer",
    age: 35,
    gender: "female",
    city: "Mumbai",
    pincode: "400001",
    bloodGroup: "A-",
    assignedDoctorId: "doc-2",
  },
];

export const DEMO_REPORTS: MedicalReport[] = [
  {
    id: "rep-1",
    patientId: "pat-1",
    fileName: "CBC_Report_Jan2026.pdf",
    uploadedAt: "2026-01-15T10:30:00Z",
    status: "ready",
    pageCount: 3,
    extractedResults: [
      { id: "lr-1", patientId: "pat-1", reportId: "rep-1", testName: "Haemoglobin", value: 9.8, unit: "g/dL", referenceMin: 12.0, referenceMax: 16.0, date: "2026-01-15" },
      { id: "lr-2", patientId: "pat-1", reportId: "rep-1", testName: "Serum Iron", value: 42, unit: "µg/dL", referenceMin: 60, referenceMax: 170, date: "2026-01-15" },
      { id: "lr-3", patientId: "pat-1", reportId: "rep-1", testName: "Ferritin", value: 7, unit: "ng/mL", referenceMin: 12, referenceMax: 150, date: "2026-01-15" },
      { id: "lr-4", patientId: "pat-1", reportId: "rep-1", testName: "WBC", value: 7200, unit: "cells/µL", referenceMin: 4500, referenceMax: 11000, date: "2026-01-15" },
    ],
  },
  {
    id: "rep-2",
    patientId: "pat-1",
    fileName: "Lipid_Panel_Mar2026.pdf",
    uploadedAt: "2026-03-01T09:00:00Z",
    status: "ready",
    pageCount: 2,
    extractedResults: [
      { id: "lr-5", patientId: "pat-1", reportId: "rep-2", testName: "Total Cholesterol", value: 215, unit: "mg/dL", referenceMin: 0, referenceMax: 200, date: "2026-03-01" },
      { id: "lr-6", patientId: "pat-1", reportId: "rep-2", testName: "LDL", value: 138, unit: "mg/dL", referenceMin: 0, referenceMax: 100, date: "2026-03-01" },
      { id: "lr-7", patientId: "pat-1", reportId: "rep-2", testName: "HDL", value: 55, unit: "mg/dL", referenceMin: 50, referenceMax: 80, date: "2026-03-01" },
    ],
  },
  {
    id: "rep-3",
    patientId: "pat-2",
    fileName: "HbA1c_Feb2026.pdf",
    uploadedAt: "2026-02-20T14:00:00Z",
    status: "ready",
    pageCount: 2,
    extractedResults: [
      { id: "lr-8", patientId: "pat-2", reportId: "rep-3", testName: "HbA1c", value: 7.8, unit: "%", referenceMin: 4.0, referenceMax: 5.7, date: "2026-02-20" },
      { id: "lr-9", patientId: "pat-2", reportId: "rep-3", testName: "Fasting Glucose", value: 142, unit: "mg/dL", referenceMin: 70, referenceMax: 100, date: "2026-02-20" },
    ],
  },
  {
    id: "rep-4",
    patientId: "pat-3",
    fileName: "Thyroid_Feb2026.pdf",
    uploadedAt: "2026-02-10T11:00:00Z",
    status: "processing",
    pageCount: 1,
    extractedResults: [],
  },
];

export const DEMO_HEALTH_METRICS: HealthMetric[] = [
  // pat-1 – 7 days
  { patientId: "pat-1", date: "2026-03-05", steps: 3200, sleepHours: 4.5, heartRateAvg: 78 },
  { patientId: "pat-1", date: "2026-03-04", steps: 5100, sleepHours: 6.2, heartRateAvg: 75 },
  { patientId: "pat-1", date: "2026-03-03", steps: 4800, sleepHours: 5.8, heartRateAvg: 76 },
  { patientId: "pat-1", date: "2026-03-02", steps: 6200, sleepHours: 7.1, heartRateAvg: 73 },
  { patientId: "pat-1", date: "2026-03-01", steps: 4100, sleepHours: 5.5, heartRateAvg: 79 },
  { patientId: "pat-1", date: "2026-02-28", steps: 3800, sleepHours: 5.0, heartRateAvg: 80 },
  { patientId: "pat-1", date: "2026-02-27", steps: 5500, sleepHours: 6.8, heartRateAvg: 74 },
  // pat-2 – 7 days
  { patientId: "pat-2", date: "2026-03-05", steps: 7500, sleepHours: 7.0, heartRateAvg: 72 },
  { patientId: "pat-2", date: "2026-03-04", steps: 8200, sleepHours: 6.5, heartRateAvg: 70 },
  { patientId: "pat-2", date: "2026-03-03", steps: 6900, sleepHours: 7.2, heartRateAvg: 71 },
  { patientId: "pat-2", date: "2026-03-02", steps: 9100, sleepHours: 7.5, heartRateAvg: 69 },
  { patientId: "pat-2", date: "2026-03-01", steps: 7800, sleepHours: 6.8, heartRateAvg: 73 },
  { patientId: "pat-2", date: "2026-02-28", steps: 8500, sleepHours: 7.0, heartRateAvg: 70 },
  { patientId: "pat-2", date: "2026-02-27", steps: 6600, sleepHours: 6.2, heartRateAvg: 74 },
  // pat-3 – 7 days
  { patientId: "pat-3", date: "2026-03-05", steps: 2100, sleepHours: 5.0, heartRateAvg: 82 },
  { patientId: "pat-3", date: "2026-03-04", steps: 3300, sleepHours: 5.5, heartRateAvg: 81 },
  { patientId: "pat-3", date: "2026-03-03", steps: 2800, sleepHours: 4.8, heartRateAvg: 84 },
  { patientId: "pat-3", date: "2026-03-02", steps: 4100, sleepHours: 6.2, heartRateAvg: 79 },
  { patientId: "pat-3", date: "2026-03-01", steps: 3600, sleepHours: 5.9, heartRateAvg: 80 },
  { patientId: "pat-3", date: "2026-02-28", steps: 2500, sleepHours: 5.2, heartRateAvg: 83 },
  { patientId: "pat-3", date: "2026-02-27", steps: 3900, sleepHours: 6.0, heartRateAvg: 81 },
];

export const DEMO_ENVIRONMENT: EnvironmentContext[] = [
  {
    patientId: "pat-1",
    date: "2026-03-05",
    city: "Chennai",
    temperature: { min: 26, max: 38, avg: 33 },
    humidity: 82,
    aqi: 145,
    pm25: 72,
    pm10: 110,
    season: "summer",
    heatwave: true,
    poorAir: true,
  },
  {
    patientId: "pat-2",
    date: "2026-03-05",
    city: "Bangalore",
    temperature: { min: 18, max: 28, avg: 23 },
    humidity: 55,
    aqi: 85,
    pm25: 38,
    pm10: 62,
    season: "spring",
    heatwave: false,
    poorAir: false,
  },
  {
    patientId: "pat-3",
    date: "2026-03-05",
    city: "Mumbai",
    temperature: { min: 24, max: 34, avg: 29 },
    humidity: 74,
    aqi: 162,
    pm25: 88,
    pm10: 130,
    season: "summer",
    heatwave: false,
    poorAir: true,
  },
];

export const DEMO_ALERTS: Alert[] = [
  {
    id: "alert-1",
    patientId: "pat-1",
    severity: "high",
    category: "lab",
    title: "Iron Deficiency Anaemia Detected",
    reason: "Haemoglobin and Serum Iron are critically below reference range.",
    evidence: ["Haemoglobin: 9.8 g/dL (ref 12–16)", "Serum Iron: 42 µg/dL (ref 60–170)", "Ferritin: 7 ng/mL (ref 12–150)"],
    createdAt: "2026-01-16T07:00:00Z",
    acknowledged: false,
  },
  {
    id: "alert-2",
    patientId: "pat-1",
    severity: "medium",
    category: "environment",
    title: "Fatigue Risk — Heat + Low Iron",
    reason: "Poor sleep combined with extreme heat and existing low iron increases fatigue risk significantly.",
    evidence: ["Sleep: 4.5 hrs (2026-03-05)", "Temperature: 38°C max in Chennai", "Heatwave flag active", "Haemoglobin: 9.8 g/dL"],
    createdAt: "2026-03-05T06:00:00Z",
    acknowledged: false,
  },
  {
    id: "alert-3",
    patientId: "pat-1",
    severity: "medium",
    category: "environment",
    title: "Poor Air Quality — Breathing Risk",
    reason: "AQI 145 with PM2.5 at 72 µg/m³. Outdoor activity should be limited.",
    evidence: ["AQI: 145 (Unhealthy)", "PM2.5: 72 µg/m³", "PM10: 110 µg/m³"],
    createdAt: "2026-03-05T06:00:00Z",
    acknowledged: false,
  },
  {
    id: "alert-4",
    patientId: "pat-2",
    severity: "high",
    category: "lab",
    title: "Elevated HbA1c — Diabetic Range",
    reason: "HbA1c of 7.8% indicates poor long-term glucose control.",
    evidence: ["HbA1c: 7.8% (ref 4–5.7%)", "Fasting Glucose: 142 mg/dL (ref 70–100)"],
    createdAt: "2026-02-21T08:00:00Z",
    acknowledged: true,
  },
  {
    id: "alert-5",
    patientId: "pat-3",
    severity: "medium",
    category: "environment",
    title: "Air Quality Alert — Mumbai",
    reason: "AQI 162 with high PM2.5 levels; caution advised for outdoor activity.",
    evidence: ["AQI: 162 (Unhealthy)", "PM2.5: 88 µg/m³"],
    createdAt: "2026-03-05T07:00:00Z",
    acknowledged: false,
  },
];

// ── Trend Notes ────────────────────────────────
export const DEMO_TRENDS: TrendNote[] = [
  { date: "2026-03-05", note: "Lowest sleep duration (4.5h) this week coincided with heatwave peak", category: "environment" },
  { date: "2026-03-03", note: "Steps dropped by 22% compared to previous week avg", category: "activity" },
  { date: "2026-02-28", note: "Heart rate elevated (+5 bpm) after poor sleep night", category: "sleep" },
];

export const DEMO_WEEK_SUMMARY: WeekSummary = {
  patientId: "pat-1",
  weekLabel: "Feb 27 – Mar 5, 2026",
  avgSteps: 4671,
  avgSleepHours: 5.8,
  avgHeartRate: 76,
  totalActiveAlerts: 3,
  labFlags: 2,
  trend: "declining",
  notes: [
    "Activity levels have dropped 15% from last week.",
    "Sleep consistency is poor (variance > 1.5h).",
    "Heatwave appears to correlate with low activity days.",
  ],
};

export const DEMO_CHAT_HISTORY: ChatMessage[] = [
  {
    id: "msg-1",
    role: "user",
    content: "Why am I feeling so tired lately?",
    timestamp: "2026-03-05T10:00:00Z",
  },
  {
    id: "msg-2",
    role: "assistant",
    content:
      "I noticed a few things in your data that could be contributing to your fatigue. Your last blood test showed your haemoglobin at 9.8 g/dL and serum iron at 42 µg/dL — both below normal range. On top of that, you only slept 4.5 hours last night, and Chennai is experiencing a heatwave with temperatures reaching 38°C today.\n\nAll three — low iron, poor sleep, and extreme heat — are well-known contributors to low energy. I'd suggest mentioning this to your doctor, especially the iron levels, to discuss whether supplementation might help.",
    citations: ["CBC_Report_Jan2026.pdf, Page 1", "Health Metrics: 2026-03-05", "Environmental Context: Chennai, 2026-03-05"],
    timestamp: "2026-03-05T10:00:10Z",
  },
  {
    id: "msg-3",
    role: "user",
    content: "Is my cholesterol dangerous?",
    timestamp: "2026-03-05T10:02:00Z",
  },
  {
    id: "msg-4",
    role: "assistant",
    content:
      "Your recent lipid panel shows total cholesterol at 215 mg/dL and LDL at 138 mg/dL — both above the optimal range. However, your HDL (the 'good' cholesterol) at 55 mg/dL is within a healthy range, which is a positive sign.\n\nI'm not a doctor and can't tell you whether this requires medication, but elevated LDL is a trend worth discussing with Dr. Priya Nair at your next visit. Eating habits, exercise, and family history all factor into what action is appropriate.",
    citations: ["Lipid_Panel_Mar2026.pdf, Page 1"],
    timestamp: "2026-03-05T10:02:12Z",
  },
];
