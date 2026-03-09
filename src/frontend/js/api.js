/**
 * HealthCompanion — API Client
 * Thin fetch wrapper over FastAPI backend.
 * Falls back to DEMO data when backend is unreachable.
 */

const API = {
  base: '/api/v1',
  fallback: true, // toggle to false when backend is live

  async _get(path) {
    try {
      const r = await fetch(this.base + path);
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      if (this.fallback) { console.warn('[API] POST', path, '→ demo fallback'); return null; }
      throw e;
    }
  },

  // GET /api/v1/alerts?user_id=...
  async alerts(userId) {
    const data = await this._get(`/alerts?user_id=${userId}`);
    return data || ALERTS[userId] || [];
  },

  // GET /api/v1/dashboard?user_id=...
  async dashboard(userId) {
    const data = await this._get(`/dashboard?user_id=${userId}`);
    return data || { patient: PATIENTS.find(p => p.id === userId), metrics: METRICS[userId] };
  },

  // GET /api/v1/reports?user_id=...
  async reports(userId) {
    const data = await this._get(`/reports?user_id=${userId}`);
    return data || REPORTS[userId] || [];
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
};
