/**
 * HealthCompanion — UI Component Renderers
 * Pure functions that return HTML strings.
 * No framework required.
 */

// ── Navigation ────────────────────────────────
function renderNav(activePage) {
  const items = [
    { href: "index.html",              label: "Dashboard" },
    { href: "alerts.html",             label: "Alerts" },
    { href: "reports.html",            label: "Reports" },
    { href: "chat.html",               label: "Ask AI" },
    { href: "environment.html",        label: "Environment" },
    { href: "profile.html",            label: "Profile" },
    { href: "doctor-dashboard.html",   label: "Doctor View" },
  ];
  return `<nav class="nav">
    <div class="nav-logo">Health<span>Companion</span><small>Personal Health AI</small></div>
    ${items.map(it => `<a href="${it.href}" class="nav-item${it.href === activePage ? ' active' : ''}">
      ${it.label}</a>`).join('')}
    <div class="nav-footer">v0.1-demo · Person 5</div>
  </nav>`;
}

// Auto-inject nav when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('nav');
  if (el && typeof PAGE !== 'undefined') el.outerHTML = renderNav(PAGE);
});

// ── Badges ─────────────────────────────────────
function badge(severity) {
  const map = { high:'badge-red', medium:'badge-amber', low:'badge-blue',
                normal:'badge-green', elevated:'badge-amber', borderline:'badge-amber',
                critical:'badge-red', ready:'badge-green', processing:'badge-amber' };
  return `<span class="badge ${map[severity]||'badge-gray'}">${severity}</span>`;
}

// ── Summary Tile ───────────────────────────────
function renderSummaryTile({ label, value, unit='', trend='stable', trendLabel='', accent='blue', sparkline=[] }) {
  const colors = { blue:'#3b82f6', green:'#10b981', red:'#ef4444', amber:'#f59e0b', purple:'#8b5cf6' };
  const trendClass = { up:'trend-up', down:'trend-down', stable:'trend-stable' };
  const trendSym = { up:'↑', down:'↓', stable:'→' };
  const col = colors[accent] || '#3b82f6';
  return `<div class="stat-tile">
    <div class="stat-tile-accent" style="background:${col}"></div>
    <div class="stat-label">${label}</div>
    <div class="stat-value">${value}</div>
    <div class="stat-unit">${unit}</div>
    ${sparkline.length > 1 ? `<div class="stat-sparkline">${sparklineSVG(sparkline, col)}</div>` : ''}
    ${trend ? `<div class="stat-trend ${trendClass[trend]||''}">${trendSym[trend]||''} ${trendLabel||trend}</div>` : ''}
  </div>`;
}

// ── SVG Sparkline ──────────────────────────────
function sparklineSVG(values, color='#3b82f6', w=110, h=28) {
  if (values.length < 2) return '';
  const mn = Math.min(...values), mx = Math.max(...values), rng = mx-mn || 1;
  const step = w / (values.length - 1);
  const pts = values.map((v,i) => `${i*step},${h-((v-mn)/rng)*(h-6)-3}`).join(' ');
  const [lx, ly] = [((values.length-1)*step), h-((values[values.length-1]-mn)/rng)*(h-6)-3];
  return `<svg width="${w}" height="${h}" style="overflow:visible;display:block">
    <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" opacity="0.75"/>
    <circle cx="${lx}" cy="${ly}" r="2.5" fill="${color}"/>
  </svg>`;
}

// ── Bar Chart ──────────────────────────────────
function renderBarChart(data, labels, title, color='#3b82f6') {
  const mx = Math.max(...data) || 1;
  const bw = 100 / data.length;
  const bars = data.map((v,i) => {
    const h = Math.max(2, Math.round((v/mx)*78));
    return `<rect x="${i*bw+bw*.12}%" y="${95-h}%" width="${bw*.76}%" height="${h}%" rx="2" fill="${color}" opacity="0.8"/>
    <text x="${i*bw+bw/2}%" y="99.5%" text-anchor="middle" font-size="5.5" fill="#475569">${labels[i]}</text>`;
  }).join('');
  return `<div class="chart-wrap">
    <div class="chart-title">${title}</div>
    <svg class="chart-area" width="100%" height="100" viewBox="0 0 100 100" preserveAspectRatio="none">${bars}</svg>
  </div>`;
}

// ── Line/Area Chart ────────────────────────────
function renderLineChart(data, labels, title, color='#3b82f6') {
  if (data.length < 2) return '';
  const W=100, H=70, mn=Math.min(...data), mx=Math.max(...data), rng=mx-mn||1;
  const step = W/(data.length-1);
  const pts = data.map((v,i) => [i*step, H-((v-mn)/rng)*(H-10)-5]);
  const line = pts.map(([x,y]) => `${x},${y}`).join(' ');
  const area = `0,${H} ${line} ${W},${H}`;
  const id = 'g'+Math.random().toString(36).slice(2,6);
  return `<div class="chart-wrap">
    <div class="chart-title">${title}</div>
    <svg class="chart-area" width="100%" height="90" viewBox="0 0 100 ${H+12}" preserveAspectRatio="none" style="overflow:visible">
      <defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${color}" stop-opacity="0.25"/>
        <stop offset="100%" stop-color="${color}" stop-opacity="0.01"/>
      </linearGradient></defs>
      <polygon points="${area}" fill="url(#${id})"/>
      <polyline points="${line}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>
      ${pts.map(([x,y],i) => i===pts.length-1 ? `<circle cx="${x}" cy="${y}" r="2.5" fill="${color}"/>` : '').join('')}
      ${labels.length ? pts.map(([x],i) => i%Math.ceil(labels.length/6)===0 ? `<text x="${x}" y="${H+10}" text-anchor="middle" font-size="5" fill="#475569">${labels[i]}</text>` : '').join('') : ''}
    </svg>
  </div>`;
}

// ── Donut Chart ────────────────────────────────
function renderDonutChart(value, max, label, color='#3b82f6') {
  const pct = Math.min(value/max, 1);
  const r=28, c=2*Math.PI*r, dash=pct*c;
  return `<div class="chart-wrap" style="text-align:center;padding:1rem">
    <div class="chart-title">${label}</div>
    <svg width="80" height="80" viewBox="0 0 80 80" style="display:block;margin:auto">
      <circle cx="40" cy="40" r="${r}" fill="none" stroke="#1e293b" stroke-width="8"/>
      <circle cx="40" cy="40" r="${r}" fill="none" stroke="${color}" stroke-width="8"
        stroke-dasharray="${dash} ${c-dash}" stroke-linecap="round"
        transform="rotate(-90 40 40)"/>
      <text x="40" y="44" text-anchor="middle" font-size="11" fill="white" font-weight="700">${Math.round(pct*100)}%</text>
    </svg>
    <div style="font-size:0.68rem;color:#94a3b8;margin-top:0.25rem">${value} / ${max}</div>
  </div>`;
}

// ── Alert Card ─────────────────────────────────
function renderAlertCard(alert) {
  const sevClass = alert.severity==='high' ? 'sev-high' : alert.severity==='medium' ? 'sev-medium' : 'sev-low';
  const ts = new Date(alert.timestamp).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'});
  const evidenceRows = Object.entries(alert.key_values).map(([k,v]) =>
    `<div class="evidence-item"><span class="evidence-key">${k}</span><span>${v}</span></div>`).join('');
  return `<div class="alert-card" id="${alert.alert_id}">
    <div class="alert-card-header" onclick="toggleAlertBody('${alert.alert_id}')">
      <div class="alert-sev-bar ${sevClass}"></div>
      <div class="alert-info">
        <div class="alert-title">${alert.reason}</div>
        <div class="alert-meta">${ts} &nbsp;·&nbsp; ${alert.category} &nbsp;·&nbsp; ${badge(alert.severity)}</div>
      </div>
      <div class="alert-actions">
        <button class="btn btn-ghost" onclick="event.stopPropagation();ackAlert('${alert.alert_id}')">Acknowledge</button>
      </div>
    </div>
    <div class="alert-body" id="body_${alert.alert_id}">
      <p class="alert-body-text">${alert.detail}</p>
      ${evidenceRows.length ? `<div class="evidence-box"><div class="evidence-box-title">Evidence data</div>${evidenceRows}</div>` : ''}
      ${alert.evidence_refs.length ? `<p style="font-size:0.68rem;color:#475569;margin-top:0.5rem">Source: ${alert.evidence_refs.join(', ')}</p>` : ''}
      <div class="alert-body-actions">
        <button class="btn btn-primary" onclick="goToChat('${encodeURIComponent(alert.reason)}')">Ask AI about this</button>
        <button class="btn btn-danger"  onclick="dismissAlert('${alert.alert_id}')">Dismiss</button>
      </div>
    </div>
  </div>`;
}

// ── Environment Panel ──────────────────────────
function renderEnvPanel(env) {
  const aqiPct = Math.min((env.aqi/300)*100, 100);
  const borderCol = env.aqi < 50 ? '#10b981' : env.aqi < 150 ? '#f59e0b' : '#ef4444';
  return `<div class="card">
    <div class="flex items-center justify-between mb-2">
      <div>
        <div class="font-semibold">${env.city}</div>
        <div class="text-xs text-muted">${env.weather} · ${env.season} · ${env.date}</div>
      </div>
      <div class="${env.aqi_class}" style="font-size:1.35rem;font-weight:800">AQI ${env.aqi}</div>
    </div>
    <div class="env-grid">
      <div class="env-tile"><div class="env-icon">AQI</div><div class="env-label">AQI</div><div class="env-value ${env.aqi_class}">${env.aqi}</div><div class="env-unit">${env.aqi_label}</div></div>
      <div class="env-tile"><div class="env-icon">PM</div><div class="env-label">PM 2.5</div><div class="env-value">${env.pm25}</div><div class="env-unit">µg/m³</div></div>
      <div class="env-tile"><div class="env-icon">TEMP</div><div class="env-label">Temp</div><div class="env-value">${env.temperature}°</div><div class="env-unit">Celsius</div></div>
      <div class="env-tile"><div class="env-icon">RH</div><div class="env-label">Humidity</div><div class="env-value">${env.humidity}%</div><div class="env-unit">Relative</div></div>
    </div>
    <div class="aqi-bar mt-3"><div class="aqi-pointer" style="left:${aqiPct}%"></div></div>
    <div class="aqi-scale"><span style="color:#10b981">Good</span><span>Moderate</span><span>Unhealthy</span><span style="color:#ef4444">Hazardous</span></div>
    <div class="env-advisory" style="border-left-color:${borderCol}">${env.advisory}</div>
    ${env.alert_influence.length ? `<div style="margin-top:0.5rem;font-size:0.7rem;color:#94a3b8">${env.alert_influence.join('<br>')}</div>` : ''}
  </div>`;
}

// ── Report Timeline ────────────────────────────
function renderTimeline(reports) {
  if (!reports || !reports.length)
    return `<div class="empty"><div class="empty-icon">Report</div><div class="empty-text">No reports uploaded yet.</div></div>`;
  return `<div class="timeline">${reports.map(r => `
    <div class="timeline-item">
      <div class="timeline-dot" style="background:${r.dot_color||'#10b981'}"></div>
      <div class="timeline-content">
        <div class="timeline-title">${r.filename}</div>
        <div class="timeline-date">${r.upload_date} · ${r.type} · ${r.page_count} pages · ${badge(r.status)}</div>
        <div class="timeline-tags">${r.findings.map(f => `<span class="badge ${f.includes('LOW')||f.includes('HIGH') ? 'badge-red' : 'badge-green'}" style="margin-top:0.2rem">${f}</span>`).join('')}</div>
      </div>
    </div>`).join('')}</div>`;
}

// ── Chat Message ───────────────────────────────
function renderChatMessage(msg) {
  const isUser = msg.role === 'user';
  const avatar = isUser ? 'ME' : 'AI';
  const nl2br = s => s.replace(/\n/g, '<br>');
  return `<div class="chat-msg ${isUser ? 'user-msg' : ''}">
    <div class="chat-avatar${isUser ? '' : ' ai'}">${avatar}</div>
    <div>
      <div class="chat-bubble">${nl2br(msg.content)}</div>
      ${msg.citations && msg.citations.length ? `<div class="chat-citations">${msg.citations.map(c=>`<span class="chat-citation">Source: ${c}</span>`).join('')}</div>` : ''}
    </div>
  </div>`;
}

// ── Doctor Patient Card ────────────────────────
function renderPatientCard(patient, alertCount, selected=false) {
  return `<div class="patient-card${selected?' selected':''}" onclick="selectPatient('${patient.id}')">
    <div class="patient-avatar">${patient.initials}</div>
    <div>
      <div class="patient-name">${patient.name}</div>
      <div class="patient-meta">${patient.age}y · ${patient.gender} · ${patient.city}</div>
      <div class="patient-meta" style="margin-top:0.1rem">${patient.conditions.slice(0,2).join(', ')}${patient.conditions.length>2?'…':''}</div>
    </div>
    ${alertCount > 0 ? `<div class="alert-count-badge">${alertCount}</div>` : ''}
  </div>`;
}

// ── Interactive Handlers ───────────────────────
function toggleAlertBody(id) {
  const body = document.getElementById('body_' + id);
  if (body) body.classList.toggle('open');
}

function ackAlert(id) {
  const card = document.getElementById(id);
  if (!card) return;
  card.style.opacity = '0.5';
  const btn = card.querySelector('.btn-ghost');
  if (btn) { btn.textContent = 'Done'; btn.disabled = true; }
}

function dismissAlert(id) {
  const card = document.getElementById(id);
  if (card) { card.style.transition='opacity 0.3s'; card.style.opacity='0'; setTimeout(()=>card.remove(), 300); }
}

function goToChat(q) {
  window.location.href = `chat.html?q=${q}`;
}

// ── Patient selector utility ───────────────────
function buildPatientSelector(currentId, onChangeCallback) {
  return `<select class="sel" onchange="${onChangeCallback}" id="patient-sel">
    ${PATIENTS.map(p=>`<option value="${p.id}"${p.id===currentId?' selected':''}>${p.name}</option>`).join('')}
  </select>`;
}
