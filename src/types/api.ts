// ===========================================
// Health MVP API - Frontend Type Definitions
// ===========================================

// 1. DASHBOARD TYPES
export interface DashboardData {
  user_id: string;
  greeting: string;
  wellbeing_score: number;
  wellbeing_trend: 'improving' | 'stable' | 'declining';
  active_alerts_count: number;
  environment: {
    aqi: number;
    weather: string;
  } | null; // Nullable for Week 1 (Partial Data)
}

export interface DashboardResponse {
  status: 'success' | 'partial_success' | 'error';
  data?: DashboardData;
  error_message?: string;
}

// 2. ALERT TYPES
export interface AlertEvidence {
  source: string;     // e.g., "Apple Watch"
  metric: string;     // e.g., "sleep_duration"
  value: string;      // e.g., "4h 12m"
  threshold: string;  // e.g., "6h 00m"
}

export interface AlertItem {
  id: string;
  title: string;
  severity: 'low' | 'medium' | 'high';
  timestamp: string;
  message: string;
  evidence: AlertEvidence | null; // Null for simple reminders
}

export interface AlertsResponse {
  status: 'success' | 'error';
  data: {
    alerts: AlertItem[];
  };
}

// 3. RAG / CHAT TYPES
export interface Citation {
  source_file: string;
  page: number;
  snippet: string;
}

export interface RagResponse {
  status: 'success' | 'error';
  data: {
    answer: string;
    citations: Citation[];
  };
}

// 4. REPORT TYPES
export interface UploadResponse {
  status: 'processing' | 'error';
  report_id?: string;
  message: string;
}

// 5. DOCTOR TYPES
export interface PatientSummary {
  user_id: string;
  name: string;
  age: number;
  risk_level: 'low' | 'medium' | 'high'; // This drives the "Traffic Light" UI
  last_updated: string;
}

export interface DoctorPatientsResponse {
  patients: PatientSummary[];
}
