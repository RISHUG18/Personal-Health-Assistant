/**
 * HealthCompanion — API Client
 * Thin fetch wrapper over FastAPI backend.
 * Falls back to DEMO data when backend is unreachable.
 */

const API = {
  base: '/api/v1',
  fallback: true, // toggle to false when backend is live

  _token() {
    return localStorage.getItem('hc_access_token');
  },

  _userId() {
    return localStorage.getItem('hc_user_id');
  },

  _headers(extra = {}) {
    const token = this._token();
    return {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...extra,
    };
  },

  async _get(path) {
    try {
      const r = await fetch(this.base + path, {
        headers: this._headers(),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      if (this.fallback) { console.warn('[API] GET', path, '→ demo fallback'); return null; }
      throw e;
    }
  },

  async _post(path, body) {
    try {
      const r = await fetch(this.base + path, {
        method: 'POST',
        headers: this._headers({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      if (this.fallback) { console.warn('[API] POST', path, '→ demo fallback'); return null; }
      throw e;
    }
  },

  async _patch(path, body) {
    try {
      const r = await fetch(this.base + path, {
        method: 'PATCH',
        headers: this._headers({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      if (this.fallback) { console.warn('[API] PATCH', path, '→ demo fallback'); return null; }
      throw e;
    }
  },

  async _delete(path) {
    try {
      const r = await fetch(this.base + path, {
        method: 'DELETE',
        headers: this._headers(),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      if (this.fallback) { console.warn('[API] DELETE', path, '→ demo fallback'); return null; }
      throw e;
    }
  },

  // GET /alerts/{user_id}
  async alerts(userId) {
    const effectiveUserId = userId || this._userId();
    const data = effectiveUserId ? await this._get(`/alerts/${effectiveUserId}`) : null;
    return data || ALERTS[effectiveUserId] || [];
  },

  // GET /api/v1/dashboard?user_id=...
  async dashboard(userId) {
    const data = await this._get(`/dashboard?user_id=${userId}`);
    return data || { patient: PATIENTS.find(p => p.id === userId), metrics: METRICS[userId] };
  },

  // GET /reports
  async reports(userId) {
    const effectiveUserId = userId || this._userId();
    const data = await this._get('/reports');
    return data || REPORTS[effectiveUserId] || [];
  },

  // GET /reports/status/{report_id}
  async reportStatus(reportId) {
    return this._get(`/reports/status/${reportId}`);
  },

  // GET /reports/{report_id}/lab-results
  async reportLabResults(reportId) {
    return this._get(`/reports/${reportId}/lab-results`);
  },

  // GET /reports/{report_id}/download_url
  async reportDownloadUrl(reportId) {
    return this._get(`/reports/${reportId}/download_url`);
  },

  // GET /api/v1/environment?city=...
  async environment(city) {
    const data = await this._get(`/environment?city=${encodeURIComponent(city)}`);
    return data || ENVIRONMENT[city] || null;
  },

  // POST /api/v1/rag_query
  async ragQuery(userId, query, role = 'user') {
    const data = await this._post('/rag_query', {
      user_id: userId,
      query,
      role,
      retrieval_strategy: 'pgvector',
      top_k: 10,
    });
    if (data) return data;
    // Demo fallback: return first AI example or generic response
    const examples = CHAT_EXAMPLES[userId];
    const aiMsg = examples ? examples.find(m => m.role === 'assistant') : null;
    return {
      answer: aiMsg ? aiMsg.content : "I'm currently using demo mode. Connect the backend to get real AI responses.",
      citations: aiMsg ? aiMsg.citations : [],
    };
  },

  // GET /users/me
  async myProfile() {
    return this._get('/users/me');
  },

  // PATCH /users/me
  async updateMyProfile(fields) {
    return this._patch('/users/me', fields);
  },

  // GET /users/me/export
  async exportMyData() {
    const resp = await fetch(this.base + '/users/me/export', {
      headers: this._headers(),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.blob();
  },

  // DELETE /users/me
  async deleteMyAccount() {
    return this._delete('/users/me');
  },
};
