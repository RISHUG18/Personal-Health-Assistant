/**
 * HealthCompanion — Demo Data
 * All synthetic data used across the static UI.
 * Matches backend schemas (lab_results, alerts, reports, health_metrics, environment).
 */

const PATIENTS = [
  {
    id: "pat-1",
    name: "Meera Iyer",
    initials: "MI",
    age: 28,
    gender: "Female",
    city: "Chennai",
    bloodGroup: "B+",
    occupation: "Software Engineer",
    phone: "+91 98400 12345",
    conditions: ["Iron Deficiency Anaemia", "Vitamin D Insufficiency"],
    medications: ["Ferrous Sulphate 200 mg OD", "Vitamin D3 60,000 IU weekly"],
  },
  {
    id: "pat-2",
    name: "Rajan Subramaniam",
    initials: "RS",
    age: 55,
    gender: "Male",
    city: "Bengaluru",
    bloodGroup: "O+",
    occupation: "Retired Bank Manager",
    phone: "+91 98800 67890",
    conditions: ["Type 2 Diabetes", "Hypertension", "Dyslipidaemia", "Early CKD"],
    medications: ["Metformin 1000 mg BD", "Amlodipine 5 mg OD", "Atorvastatin 20 mg OD", "Losartan 50 mg OD"],
  },
];

const DOCTOR = {
  id: "doc-1",
  name: "Dr. Arjun Mehta",
  initials: "AM",
  specialization: "Cardiology",
  hospital: "Fortis Hospital, Bengaluru",
  yearsExp: 18,
  patients: ["pat-1", "pat-2"],
};

// ── Alerts (keyed by patient_id) ──────────────
const ALERTS = {
  "pat-1": [
    {
      alert_id: "alr-001",
      patient_id: "pat-1",
      severity: "high",
      category: "lab",
      reason: "Haemoglobin critically low at 9.8 g/dL",
      detail: "Your haemoglobin (9.8 g/dL) is well below the normal range for women (12.0–16.0 g/dL). This indicates moderate iron-deficiency anaemia. Low haemoglobin reduces oxygen delivery to tissues, which explains fatigue and breathlessness.",
      evidence_refs: ["CBC_Iron_Panel_Jan2026.pdf"],
      key_values: { "Haemoglobin": "9.8 g/dL", "Normal range": "12.0–16.0 g/dL", "Status": "LOW — clinical action required" },
      timestamp: "2026-01-15T10:35:00Z",
      acknowledged: false,
    },
    {
      alert_id: "alr-002",
      patient_id: "pat-1",
      severity: "high",
      category: "lab",
      reason: "Serum Iron deficient at 42 µg/dL (ref: 60–170)",
      detail: "Serum iron of 42 µg/dL is significantly below the normal range. Combined with elevated TIBC, this confirms iron deficiency as the cause of anaemia rather than anaemia of chronic disease.",
      evidence_refs: ["CBC_Iron_Panel_Jan2026.pdf"],
      key_values: { "Serum Iron": "42 µg/dL", "Normal range": "60–170 µg/dL", "TIBC": "480 µg/dL (HIGH)" },
      timestamp: "2026-01-15T10:35:00Z",
      acknowledged: false,
    },
    {
      alert_id: "alr-003",
      patient_id: "pat-1",
      severity: "medium",
      category: "lab",
      reason: "Ferritin low at 7 ng/mL — iron stores depleted",
      detail: "Ferritin at 7 ng/mL means your iron stores are nearly exhausted. This typically precedes low haemoglobin and, if untreated, iron deficiency progresses further. Current iron supplementation should replenish stores within 2–4 months.",
      evidence_refs: ["CBC_Iron_Panel_Jan2026.pdf"],
      key_values: { "Ferritin": "7 ng/mL", "Normal range": "12–150 ng/mL", "Trend": "Declining vs Aug 2025 (14 ng/mL)" },
      timestamp: "2026-01-15T10:35:00Z",
      acknowledged: false,
    },
    {
      alert_id: "alr-004",
      patient_id: "pat-1",
      severity: "medium",
      category: "environment",
      reason: "Chennai AQI 112 — elevated outdoor risk for anaemic patients",
      detail: "Today's AQI of 112 (Moderate) with PM2.5 at 42 µg/m³ poses additional strain for patients with anaemia. Low haemoglobin already reduces oxygen-carrying capacity; breathing polluted air compresses that further. Light indoor exercise is preferred today.",
      evidence_refs: [],
      key_values: { "AQI": "112 (Moderate)", "PM2.5": "42 µg/m³", "Temperature": "32°C", "City": "Chennai" },
      timestamp: "2026-03-09T08:00:00Z",
      acknowledged: false,
    },
  ],
  "pat-2": [
    {
      alert_id: "alr-005",
      patient_id: "pat-2",
      severity: "high",
      category: "lab",
      reason: "HbA1c 8.4% — poorly controlled diabetes",
      detail: "An HbA1c of 8.4% indicates your average blood sugar over the past 3 months has been too high. For most adults with Type 2 diabetes the target is <7.0%. At this level, risk of kidney damage, nerve damage, and cardiovascular disease is significantly elevated.",
      evidence_refs: ["HbA1c_KFT_Feb2026.pdf"],
      key_values: { "HbA1c": "8.4%", "Target": "<7.0%", "Fasting BG": "162 mg/dL", "Post-prandial BG": "248 mg/dL" },
      timestamp: "2026-02-10T09:15:00Z",
      acknowledged: false,
    },
    {
      alert_id: "alr-006",
      patient_id: "pat-2",
      severity: "high",
      category: "lab",
      reason: "LDL 178 mg/dL — high cardiovascular risk in diabetic patient",
      detail: "LDL of 178 mg/dL is elevated for any adult, but especially concerning with concurrent Type 2 diabetes which already doubles cardiovascular risk. The target for a diabetic patient with CKD is LDL <70 mg/dL. Statin dose review is advisable.",
      evidence_refs: ["Lipid_Profile_Feb2026.pdf"],
      key_values: { "LDL": "178 mg/dL", "Target (DM+CKD)": "<70 mg/dL", "Total Cholesterol": "264 mg/dL", "Triglycerides": "220 mg/dL" },
      timestamp: "2026-02-10T09:15:00Z",
      acknowledged: false,
    },
    {
      alert_id: "alr-007",
      patient_id: "pat-2",
      severity: "medium",
      category: "lab",
      reason: "eGFR declined to 58 mL/min — kidney function worsening",
      detail: "eGFR has dropped from 64 to 58 mL/min over 3 months, which is a clinically significant decline. This is Stage 3a chronic kidney disease. Dose adjustments for metformin and monitoring of potassium are needed.",
      evidence_refs: ["HbA1c_KFT_Feb2026.pdf"],
      key_values: { "eGFR": "58 mL/min", "3 months ago": "64 mL/min", "Creatinine": "1.6 mg/dL", "Microalbuminuria": "82 mg/g (HIGH)" },
      timestamp: "2026-02-10T09:15:00Z",
      acknowledged: false,
    },
  ],
};

// ── Reports (keyed by patient_id) ─────────────
const REPORTS = {
  "pat-1": [
    {
      id: "rep-001",
      filename: "CBC_Iron_Panel_Jan2026.pdf",
      type: "Iron Studies / CBC",
      upload_date: "2026-01-15",
      status: "ready",
      page_count: 3,
      dot_color: "#ef4444",
      findings: ["Hb 9.8 g/dL — LOW", "Ferritin 7 ng/mL — LOW", "Serum Iron 42 µg/dL — LOW", "TIBC 480 µg/dL — HIGH", "WBC 7,200 — Normal", "Platelets 285k — Normal"],
    },
    {
      id: "rep-002",
      filename: "VitD_B12_Dec2025.pdf",
      type: "Vitamin Panel",
      upload_date: "2025-12-20",
      status: "ready",
      page_count: 2,
      dot_color: "#f59e0b",
      findings: ["Vitamin D 18 ng/mL — INSUFFICIENT", "Vitamin B12 280 pg/mL — Low-Normal", "Folate 9.2 ng/mL — Normal"],
    },
  ],
  "pat-2": [
    {
      id: "rep-003",
      filename: "HbA1c_KFT_Feb2026.pdf",
      type: "Diabetes + Kidney Panel",
      upload_date: "2026-02-10",
      status: "ready",
      page_count: 4,
      dot_color: "#ef4444",
      findings: ["HbA1c 8.4% — HIGH", "FBG 162 mg/dL — HIGH", "eGFR 58 mL/min — LOW", "Creatinine 1.6 mg/dL — HIGH", "Microalbuminuria 82 mg/g — HIGH"],
    },
    {
      id: "rep-004",
      filename: "Lipid_Profile_Feb2026.pdf",
      type: "Lipid Profile",
      upload_date: "2026-02-10",
      status: "ready",
      page_count: 2,
      dot_color: "#ef4444",
      findings: ["LDL 178 mg/dL — HIGH", "Total Cholesterol 264 mg/dL — HIGH", "Triglycerides 220 mg/dL — HIGH", "HDL 38 mg/dL — LOW"],
    },
    {
      id: "rep-005",
      filename: "BP_Diary_Jan2026.pdf",
      type: "Blood Pressure Log",
      upload_date: "2026-01-05",
      status: "ready",
      page_count: 1,
      dot_color: "#f59e0b",
      findings: ["Average BP 148/96 mmHg — ELEVATED", "Peak 162/104 mmHg"],
    },
  ],
};

// ── Daily Health Metrics ───────────────────────
const METRICS = {
  "pat-1": {
    today: { steps: 3200, sleep_hours: 5.8, heart_rate: 74, date: "2026-03-09" },
    week: [
      { day: "Mon", steps: 2800, sleep: 5.5, hr: 72 },
      { day: "Tue", steps: 3100, sleep: 6.0, hr: 75 },
      { day: "Wed", steps: 2600, sleep: 5.2, hr: 76 },
      { day: "Thu", steps: 3400, sleep: 6.1, hr: 73 },
      { day: "Fri", steps: 3800, sleep: 5.8, hr: 74 },
      { day: "Sat", steps: 2900, sleep: 5.5, hr: 75 },
      { day: "Sun", steps: 3200, sleep: 5.8, hr: 74 },
    ],
    week_summary: {
      avg_steps: 3114, avg_sleep: 5.7, avg_hr: 74,
      trend: "stable", active_alerts: 4, lab_flags: 3,
      notes: ["Iron levels have not improved since Jan — supplement adherence?", "Step count below 4,000/day all week", "Sleep consistently under 6 hours"],
    },
  },
  "pat-2": {
    today: { steps: 4200, sleep_hours: 6.5, heart_rate: 82, date: "2026-03-09" },
    week: [
      { day: "Mon", steps: 5200, sleep: 6.8, hr: 80 },
      { day: "Tue", steps: 4800, sleep: 6.5, hr: 83 },
      { day: "Wed", steps: 3900, sleep: 6.2, hr: 84 },
      { day: "Thu", steps: 4100, sleep: 6.0, hr: 82 },
      { day: "Fri", steps: 4600, sleep: 6.8, hr: 81 },
      { day: "Sat", steps: 3800, sleep: 6.3, hr: 83 },
      { day: "Sun", steps: 4200, sleep: 6.5, hr: 82 },
    ],
    week_summary: {
      avg_steps: 4371, avg_sleep: 6.4, avg_hr: 82,
      trend: "declining", active_alerts: 3, lab_flags: 5,
      notes: ["Step count declining over the week — concerns about activity", "Heart rate elevated vs baseline", "HbA1c still high — diet review needed"],
    },
  },
};

// ── Environment (keyed by city) ────────────────
const ENVIRONMENT = {
  "Chennai": {
    city: "Chennai",
    date: "2026-03-09",
    aqi: 112,
    aqi_label: "Moderate",
    aqi_class: "aqi-moderate",
    pm25: 42,
    pm10: 68,
    temperature: 32,
    humidity: 78,
    weather: "Partly Cloudy",
    season: "Summer",
    heatwave: false,
    advisory: "AQI 112: Sensitive groups (anaemia, asthma) should limit outdoor exertion. Indoor exercise preferred. Stay hydrated — 32°C heat increases fluid needs significantly.",
    alert_influence: ["Alert alr-004 severity elevated because AQI > 100 with anaemia diagnosis"],
  },
  "Bengaluru": {
    city: "Bengaluru",
    date: "2026-03-09",
    aqi: 68,
    aqi_label: "Moderate",
    aqi_class: "aqi-moderate",
    pm25: 28,
    pm10: 44,
    temperature: 28,
    humidity: 62,
    weather: "Mostly Clear",
    season: "Pre-monsoon",
    heatwave: false,
    advisory: "Air quality acceptable. 28°C is comfortable for moderate walking. Diabetic patients should stay hydrated and carry glucose tablets on walks.",
    alert_influence: [],
  },
};

// ── AI Chat Examples ───────────────────────────
const CHAT_EXAMPLES = {
  "pat-1": [
    {
      role: "user",
      content: "What does my latest haemoglobin reading mean?",
      timestamp: "2026-01-15T11:00:00Z",
    },
    {
      role: "assistant",
      content: "Your haemoglobin from the January CBC report is 9.8 g/dL — below the normal range for women (12.0–16.0 g/dL). This indicates moderate iron-deficiency anaemia.\n\nThis means your blood has fewer red blood cells to carry oxygen, which directly explains the fatigue and mid-day energy dips you've mentioned. Your ferritin (7 ng/mL) and serum iron (42 µg/dL) are also both low — this is a classic iron deficiency pattern.\n\nWith your current iron supplement (Ferrous Sulphate 200 mg), haemoglobin typically starts recovering in 4–6 weeks, and ferritin normalises in 3–6 months. A repeat test in 8 weeks would show if the supplement is working.",
      citations: ["CBC_Iron_Panel_Jan2026.pdf — Haemoglobin 9.8 g/dL", "CBC_Iron_Panel_Jan2026.pdf — Ferritin 7 ng/mL"],
      timestamp: "2026-01-15T11:00:08Z",
    },
    {
      role: "user",
      content: "Is today's AQI in Chennai safe for an evening run?",
      timestamp: "2026-03-09T17:30:00Z",
    },
    {
      role: "assistant",
      content: "Today's AQI in Chennai is 112 (Moderate) with PM2.5 at 42 µg/m³. For most healthy people this is borderline acceptable, but given your anaemia I'd recommend caution.\n\nYour haemoglobin is already low, so your blood is already less efficient at carrying oxygen. Adding PM2.5 - which irritates airways and reduces lung efficiency - compounds this.\n\nSuggestion: Instead of a run, a 20-minute brisk walk indoors (treadmill, mall, or at home) would achieve similar cardiovascular benefits without the pollution exposure. If you do go outside, keep it to a light 15-min walk and stop if you feel breathless.",
      citations: ["Chennai AQI data — 2026-03-09: 112", "CBC_Iron_Panel_Jan2026.pdf — Hb 9.8 g/dL"],
      timestamp: "2026-03-09T17:30:11Z",
    },
  ],
  "pat-2": [
    {
      role: "user",
      content: "Is my diabetes well controlled?",
      timestamp: "2026-02-10T10:00:00Z",
    },
    {
      role: "assistant",
      content: "Based on your February lab results, your diabetes is not well controlled at this time.\n\nYour HbA1c is 8.4%, which reflects your average blood sugar over the past 3 months. For most adults with Type 2 diabetes, the target is below 7.0% (or 7.5% for older patients). At 8.4%, you are significantly above target.\n\nYour fasting blood glucose (162 mg/dL) and post-prandial glucose (248 mg/dL) are both elevated, which is consistent with poor control.\n\nThe concerning part is that uncontrolled blood sugar is accelerating your kidney disease — your eGFR dropped from 64 to 58 in just 3 months, which is likely partly due to glycaemic stress on the kidneys.\n\nA review of your medication dose and diet with your doctor would be advisable.",
      citations: ["HbA1c_KFT_Feb2026.pdf — HbA1c 8.4%", "HbA1c_KFT_Feb2026.pdf — FBG 162 mg/dL", "HbA1c_KFT_Feb2026.pdf — eGFR 58 mL/min"],
      timestamp: "2026-02-10T10:00:14Z",
    },
  ],
};

// ── Suggested AI Questions per persona ─────────
const SUGGESTED_QUESTIONS = {
  "pat-1": [
    "What does my haemoglobin reading mean?",
    "Is my Vitamin D level dangerous?",
    "What foods will raise my ferritin?",
    "Is today's AQI safe for exercise?",
    "Summarise my January blood report.",
  ],
  "pat-2": [
    "Is my diabetes well controlled?",
    "My eGFR dropped from 64 to 58 — should I worry?",
    "Which medications are safe with early kidney disease?",
    "What diet changes will lower my triglycerides?",
    "What is my cardiovascular risk?",
  ],
};

// ── Profile consent settings (default) ─────────
const CONSENT_DEFAULTS = {
  "pat-1": {
    share_wearable: true,
    share_location: true,
    doctor_access: true,
    research_opt_in: false,
    push_notifications: true,
    weekly_summary: true,
  },
  "pat-2": {
    share_wearable: true,
    share_location: false,
    doctor_access: true,
    research_opt_in: false,
    push_notifications: false,
    weekly_summary: true,
  },
};
