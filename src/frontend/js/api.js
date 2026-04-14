/**
 * HealthCompanion — API Client
 * Thin fetch wrapper over FastAPI backend.
 * Falls back to DEMO data when backend is unreachable.
 */

const API = {
  base: '/api/v1',
  reportsBase: '/reports',
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

  async _postFormRaw(path, formData) {
    const r = await fetch(path, {
      method: 'POST',
      headers: this._headers(),
      body: formData,
    });
    if (!r.ok) {
      let detail = '';
      try {
        const payload = await r.json();
        detail = payload?.detail ? `: ${payload.detail}` : '';
      } catch (_) {
        detail = '';
      }
      throw new Error(`HTTP ${r.status}${detail}`);
    }
    return r.json();
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
    try {
      const r = await fetch(this.reportsBase, {
        headers: this._headers(),
      });
      if (r.ok) {
        const data = await r.json();
        if (Array.isArray(data)) return data;
        if (Array.isArray(data?.items)) return data.items;
      }
    } catch (_) {
      // Fall back to demo data below.
    }
    return REPORTS[effectiveUserId] || [];
  },

  // GET /reports/status/{report_id}
  async reportStatus(reportId) {
    try {
      const r = await fetch(`${this.reportsBase}/status/${reportId}`, {
        headers: this._headers(),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      if (this.fallback) { console.warn('[API] GET report status → demo fallback'); return null; }
      throw e;
    }
  },

  // GET /reports/{report_id}/lab-results
  async reportLabResults(reportId) {
    try {
      const r = await fetch(`${this.reportsBase}/${reportId}/lab-results`, {
        headers: this._headers(),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      if (this.fallback) { console.warn('[API] GET report lab results → demo fallback'); return null; }
      throw e;
    }
  },

  // GET /reports/{report_id}/download_url
  async reportDownloadUrl(reportId) {
    try {
      const r = await fetch(`${this.reportsBase}/${reportId}/download_url`, {
        headers: this._headers(),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      if (this.fallback) { console.warn('[API] GET report download URL → demo fallback'); return null; }
      throw e;
    }
  },

  // POST /reports/ingest (multipart form upload)
  async ingestReport(file, userId, userName = null) {
    if (!file) throw new Error('No file selected');
    if (!userId) throw new Error('Missing user_id for report upload');

    const formData = new FormData();
    formData.append('user_id', userId);
    if (userName) formData.append('user_name', userName);
    formData.append('file', file);

    return this._postFormRaw(`${this.reportsBase}/ingest`, formData);
  },

  _buildWsUrl(pathname) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}${pathname}`;
  },

  // WebSocket status stream: /ws/report-status/{report_id}
  subscribeReportStatus(reportId, handlers = {}, options = {}) {
    let ws = null;
    let retries = 0;
    let closedByClient = false;
    const maxRetries = options.maxRetries ?? 5;
    const retryDelayMs = options.retryDelayMs ?? 1200;

    const connect = () => {
      if (closedByClient) return;
      const wsUrl = this._buildWsUrl(`/ws/report-status/${reportId}`);
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        retries = 0;
        if (handlers.onOpen) handlers.onOpen();
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (handlers.onMessage) handlers.onMessage(payload);
        } catch (err) {
          if (handlers.onError) handlers.onError(err);
        }
      };

      ws.onerror = (event) => {
        if (handlers.onError) handlers.onError(event);
      };

      ws.onclose = () => {
        if (handlers.onClose) handlers.onClose();
        if (closedByClient) return;
        if (retries >= maxRetries) return;
        retries += 1;
        window.setTimeout(connect, retryDelayMs * retries);
      };
    };

    connect();

    return () => {
      closedByClient = true;
      if (ws && ws.readyState < 2) {
        ws.close();
      }
    };
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
    if (data) {
      const chunks = data?.context?.rag_knowledge_base?.retrieved_chunks || [];
      const citations = chunks
        .map((chunk) => chunk?.report_id || chunk?.chunk_id || chunk?.section || '')
        .filter(Boolean);
      return { ...data, citations };
    }
    // Demo fallback: return first AI example or generic response
    const examples = CHAT_EXAMPLES[userId];
    const aiMsg = examples ? examples.find(m => m.role === 'assistant') : null;
    const demoCitations = aiMsg ? aiMsg.citations || [] : [];
    const retrievedChunks = demoCitations.map((label, idx) => ({
      chunk_id: `demo_chunk_${idx + 1}`,
      report_id: label,
      content: label,
      section: 'Demo',
      rank: idx + 1,
      score: null,
    }));

    return {
      answer: aiMsg ? aiMsg.content : "I'm currently using demo mode. Connect the backend to get real AI responses.",
      context: {
        rag_knowledge_base: {
          query_used: query,
          retrieved_chunks: retrievedChunks,
        },
      },
      chunks_retrieved: retrievedChunks.length,
      grounding_available: retrievedChunks.length > 0,
      model: 'demo-fallback',
      llm_error: null,
      citations: demoCitations,
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
