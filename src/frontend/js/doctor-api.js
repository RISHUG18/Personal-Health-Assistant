/**
 * HealthCompanion — Doctor API Client
 * Thin fetch wrapper over FastAPI /api/v1/doctor/* endpoints.
 * Handles JWT Bearer token injection on every request.
 */

const BACKEND  = 'http://localhost:8000';
const API_BASE = BACKEND + '/api/v1';

const DoctorAPI = {
  // ── Auth helpers ──────────────────────────────────────────────────────────

  _token() {
    return localStorage.getItem('hc_access_token');
  },

  _headers(extra = {}) {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this._token()}`,
      ...extra,
    };
  },

  async _request(method, path, body = null) {
    const opts = {
      method,
      headers: this._headers(),
    };
    if (body !== null) opts.body = JSON.stringify(body);

    const resp = await fetch(API_BASE + path, opts);
    let data;
    try { data = await resp.json(); } catch { data = {}; }

    if (!resp.ok) {
      throw new Error(data.detail || `HTTP ${resp.status}`);
    }
    return data;
  },

  _get(path)          { return this._request('GET', path); },
  _post(path, body)   { return this._request('POST', path, body); },
  _delete(path)       { return this._request('DELETE', path); },

  async _download(path) {
    const resp = await fetch(API_BASE + path, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this._token()}`,
      },
    });
    if (!resp.ok) {
      let data = {};
      try { data = await resp.json(); } catch {}
      throw new Error(data.detail || `HTTP ${resp.status}`);
    }
    return resp.blob();
  },

  // ── Profile ───────────────────────────────────────────────────────────────

  /**
   * Fetch the logged-in doctor's own profile.
   * Uses GET /api/v1/users/me.
   */
  async getProfile() {
    return this._get('/users/me');
  },

  // ── Patient roster ────────────────────────────────────────────────────────

  /**
   * List all patients assigned to this doctor.
   * GET /api/v1/doctor/patients
   * Returns { doctor_id, count, patients[] }
   */
  async getPatients() {
    return this._get('/doctor/patients');
  },

  /**
   * Add a patient by email address.
   * Looks up the patient UUID via GET /api/v1/doctor/patients/lookup?email=...,
   * then posts to POST /api/v1/doctor/patients with the patient_id.
   * @param {string} email - Patient's registered email
   */
  async addPatient(email) {
    // Step 1: resolve email → UUID
    const userResp = await this._get(`/doctor/patients/lookup?email=${encodeURIComponent(email)}`);
    const patientId = userResp.patient_id || userResp.id || userResp.user_id;
    if (!patientId) throw new Error('Could not resolve patient ID from email.');

    // Step 2: create the mapping
    return this._post('/doctor/patients', { patient_id: patientId });
  },

  /**
   * Remove a patient from the roster.
   * DELETE /api/v1/doctor/patients/{patient_id}
   * @param {string} patientId - Patient UUID
   */
  async removePatient(patientId) {
    return this._delete(`/doctor/patients/${patientId}`);
  },

  // ── Patient detail ────────────────────────────────────────────────────────

  /**
   * Comprehensive overview for a single patient.
   * GET /api/v1/doctor/patients/{patient_id}/summary
   * Returns { patient, reports: {total, recent}, alerts, latest_health_summary, wearable_vitals }
   */
  async getPatientSummary(patientId) {
    return this._get(`/doctor/patients/${patientId}/summary`);
  },

  /**
   * Chart-friendly health trends for a single patient.
   * GET /api/v1/doctor/patients/{patient_id}/trends?days=...
   */
  async getPatientTrends(patientId, days = 180) {
    const query = Number.isFinite(days) ? `?days=${encodeURIComponent(days)}` : '';
    return this._get(`/doctor/patients/${patientId}/trends${query}`);
  },

  /**
   * All medical reports for a patient.
   * GET /api/v1/doctor/patients/{patient_id}/reports
   * Returns { patient_id, count, reports[] }
   */
  async getPatientReports(patientId) {
    return this._get(`/doctor/patients/${patientId}/reports`);
  },

  /**
   * Full detail of a single report including extracted lab results.
   * GET /api/v1/doctor/patients/{patient_id}/reports/{report_id}
   */
  async getReportDetail(patientId, reportId) {
    return this._get(`/doctor/patients/${patientId}/reports/${reportId}`);
  },

  /**
   * All alerts for a patient with evidence.
   * GET /api/v1/doctor/patients/{patient_id}/alerts
   * Returns { patient_id, count, alerts[] }
   */
  async getPatientAlerts(patientId) {
    return this._get(`/doctor/patients/${patientId}/alerts`);
  },

  /**
   * All lab results across all reports, grouped by report.
   * GET /api/v1/doctor/patients/{patient_id}/lab-results
   * Returns { patient_id, total_lab_results, reports[] }
   */
  async getPatientLabResults(patientId) {
    return this._get(`/doctor/patients/${patientId}/lab-results`);
  },

  // ── Actions ───────────────────────────────────────────────────────────────

  /**
   * Trigger rules-engine alert evaluation for a patient.
   * POST /api/v1/doctor/patients/{patient_id}/evaluate-alerts
   * Returns { patient_id, alerts_triggered, deleted, inserted, evidence_inserted, errors }
   */
  async evaluateAlerts(patientId, location = null, date = null) {
    const body = {};
    if (location) body.location = location;
    if (date)     body.date     = date;
    return this._post(`/doctor/patients/${patientId}/evaluate-alerts`, body);
  },

  /**
   * Generate AI health summary for a patient.
   * POST /api/v1/doctor/patients/{patient_id}/generate-summary
   */
  async generateSummary(patientId) {
    return this._post(`/doctor/patients/${patientId}/generate-summary`, {});
  },
  /**
   * Update the logged-in doctor's own profile.
   * Uses PATCH /api/v1/users/me with partial fields.
   * @param {object} fields - Only include fields you want to change
   */
  async updateProfile(fields) {
    return this._request('PATCH', '/users/me', fields);
  },

  /**
   * Export the logged-in doctor's stored account data.
   * GET /api/v1/users/me/export
   */
  async exportMyData() {
    return this._download('/users/me/export');
  },

  /**
   * Delete the logged-in doctor's account.
   * DELETE /api/v1/users/me
   */
  async deleteMyAccount() {
    return this._delete('/users/me');
  },
};
