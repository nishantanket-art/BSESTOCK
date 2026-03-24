/**
 * app.js — Promoter Stake Selling Dashboard v2
 * Handles commands, polling, rendering, expandable details, modal, and charts.
 */

let pollInterval = null;
let allResults = [];
let allInsights = [];
let sentimentFilter = 'all';
let riskChart = null;
let verdictChart = null;
let holdingChart = null;

/* ═══════════════════ COMMAND HANDLER ═══════════════════ */

function handleCommand() {
  const input = document.getElementById('commandInput');
  const raw = input.value.trim().toLowerCase();

  if (!raw) { shakeInput(); return; }

  // "update" / "refresh" / "scan"
  if (['update', 'refresh', 'scan', 'run', 'start'].some(c => raw.includes(c))) {
    input.value = '';
    startScan();
    return;
  }

  // "analyze [ticker]"
  const analyzeMatch = raw.match(/^analyze\s+(.+)/i);
  if (analyzeMatch) {
    input.value = '';
    openAnalyzeModal(analyzeMatch[1].trim().toUpperCase());
    return;
  }

  // "trend"
  if (raw.includes('trend')) {
    input.value = '';
    scrollToTrend();
    return;
  }

  shakeInput();
  showHint('💡 Commands: update · analyze [ticker] · trend');
}

/* ═══════════════════ INIT ═══════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('commandInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') handleCommand();
  });
  showLandingHint();
});

function showLandingHint() {
  const grid = document.getElementById('resultsGrid');
  grid.innerHTML = `
    <div class="landing-hint" style="grid-column:1/-1">
      <p style="color:var(--muted);font-size:0.92rem">👋 Welcome to the Promoter Stake Dashboard. Start scanning now.</p>
      <div class="landing-steps">
        <div class="landing-step">
          <div class="step-num">1</div>
          <div class="step-text">Type <strong>"update"</strong> to scan 87 stocks</div>
        </div>
        <div class="landing-step">
          <div class="step-num">2</div>
          <div class="step-text">AI analyzes promoter selling >&nbsp;40%</div>
        </div>
        <div class="landing-step">
          <div class="step-num">3</div>
          <div class="step-text">Get verdicts, risk scores & insights</div>
        </div>
      </div>
    </div>`;
}

/* ═══════════════════ SCAN / POLL ═══════════════════ */

async function startScan() {
  try {
    setRunning(true);
    const resp = await fetch('/api/update', { method: 'POST' });
    const data = await resp.json();
    console.log('[update]', data.message);
    showProgress(true);
    hideAllSections();
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(pollStatus, 1800);
  } catch (err) {
    console.error(err);
    showError('Failed to start scan. Is the server running?');
    setRunning(false);
  }
}

async function pollStatus() {
  try {
    const resp = await fetch('/api/status');
    const s = await resp.json();
    if (s.total > 0) {
      const pct = Math.round((s.progress / s.total) * 100);
      updateProgress(s.progress, s.total, pct, s.current_ticker);
    }
    if (s.status === 'done') {
      clearInterval(pollInterval); pollInterval = null;
      await loadResults(s.last_updated);
      showProgress(false);
      setRunning(false);
    } else if (s.status === 'error') {
      clearInterval(pollInterval); pollInterval = null;
      showProgress(false); setRunning(false);
      showError(s.error || 'Unknown error during scan.');
    }
  } catch (err) { console.error('[poll]', err); }
}

async function loadResults(lastUpdated) {
  const resp = await fetch('/api/results');
  const data = await resp.json();
  allResults = data.results || [];
  allInsights = data.insights || [];

  if (lastUpdated) {
    const badge = document.getElementById('lastUpdatedBadge');
    badge.textContent = '🕐 ' + lastUpdated;
    badge.style.display = 'inline-flex';
  }

  renderDashboard();
  loadTrendCharts();
}

/* ═══════════════════ RENDER DASHBOARD ═══════════════════ */

function renderDashboard() {
  renderStats();
  renderInsights();
  renderCards();

  document.getElementById('dashboardSections').style.display = 'block';
  document.getElementById('filterBar').style.display = 'flex';
}

function renderStats() {
  const strip = document.getElementById('statsStrip');
  strip.style.display = 'grid';

  const exitC = allResults.filter(r => r.analysis?.verdict === 'Exit').length;
  const cautionC = allResults.filter(r => r.analysis?.verdict === 'Caution').length;
  const holdC = allResults.filter(r => r.analysis?.verdict === 'Hold').length;
  const buyC = allResults.filter(r => r.analysis?.verdict === 'Buy').length;

  document.getElementById('statTotal').textContent = allResults.length;
  document.getElementById('statExit').textContent = exitC;
  document.getElementById('statCaution').textContent = cautionC;
  document.getElementById('statHold').textContent = holdC;
  document.getElementById('statBuy').textContent = buyC;
}

function renderInsights() {
  const container = document.getElementById('insightsGrid');
  if (!allInsights.length) { container.innerHTML = ''; return; }

  container.innerHTML = allInsights.map(ins => `
    <div class="insight-card severity-${ins.severity}">
      <div class="insight-icon">${ins.icon}</div>
      <div class="insight-content">
        <div class="insight-title">${esc(ins.title)}</div>
        <div class="insight-desc">${esc(ins.description)}</div>
      </div>
    </div>`).join('');
}

function renderCards() {
  const grid = document.getElementById('resultsGrid');
  const empty = document.getElementById('emptyState');
  const search = document.getElementById('searchInput').value.toLowerCase();

  let filtered = allResults.filter(r => {
    const ms = !search || r.company_name?.toLowerCase().includes(search) || r.ticker?.toLowerCase().includes(search);
    const mf = sentimentFilter === 'all' || r.analysis?.verdict === sentimentFilter;
    return ms && mf;
  });

  if (!filtered.length && allResults.length) {
    grid.innerHTML = '';
    empty.style.display = 'block';
    return;
  }

  empty.style.display = 'none';
  grid.innerHTML = filtered.map((r, i) => buildCard(r, i)).join('');

  // Also render high-risk section
  const hrGrid = document.getElementById('highRiskGrid');
  const highRisk = allResults.filter(r => r.analysis?.risk_level === 'High');
  if (highRisk.length) {
    document.getElementById('highRiskSection').style.display = 'block';
    document.getElementById('highRiskCount').textContent = highRisk.length;
    hrGrid.innerHTML = highRisk.map((r, i) => buildCard(r, i)).join('');
  }
}

/* ═══════════════════ CARD BUILDER ═══════════════════ */

function buildCard(r, idx) {
  const a = r.analysis || {};
  const delay = Math.min(idx * 50, 350);
  const cardId = `card-${r.ticker}-${idx}`;

  const verdictStyle = `background:${a.verdict_color}18;color:${a.verdict_color};border:1px solid ${a.verdict_color}35`;
  const riskStyle = `background:${a.risk_color}12;color:${a.risk_color};border:1px solid ${a.risk_color}25`;
  const sentimentStyle = `background:${a.sentiment_color}12;color:${a.sentiment_color};border:1px solid ${a.sentiment_color}25`;

  const prevH = r.promoter_prev != null
    ? `<div class="hold-cell"><div class="hold-val prev">${r.promoter_prev}%</div><div class="hold-lbl">Previous</div></div>
       <div class="hold-arrow">→</div>` : '';

  const reasons = (a.reasons || []).map(reason =>
    `<div class="detail-item">• ${esc(reason)}</div>`
  ).join('');

  return `
  <div class="company-card" style="animation-delay:${delay}ms">
    <div class="card-body">
      <div class="card-header">
        <div class="card-company">
          <div class="card-name">${esc(r.company_name || r.ticker)}</div>
          <span class="card-ticker">${esc(r.ticker)}</span>
        </div>
        <span class="verdict-badge" style="${verdictStyle}">${a.verdict_icon || ''} ${esc(a.verdict || '')}</span>
      </div>

      <div class="badges-row">
        <span class="mini-badge" style="${riskStyle}">${a.risk_icon || ''} ${esc(a.risk_level || '')} Risk</span>
        <span class="mini-badge" style="${sentimentStyle}">${esc(a.sentiment || '')}</span>
        <span class="mini-badge" style="background:var(--surface2);color:var(--muted);border:1px solid var(--border)">${esc(a.mode_of_selling || '')}</span>
      </div>

      <div class="holding-strip">
        ${prevH}
        <div class="hold-cell">
          <div class="hold-val current">${r.promoter_current}%</div>
          <div class="hold-lbl">Current</div>
        </div>
        <div class="hold-cell">
          <div class="hold-val change">▼ ${Math.abs(r.promoter_change || 0).toFixed(2)}%</div>
          <div class="hold-lbl">Sold</div>
        </div>
      </div>
    </div>

    <button class="card-expand-toggle" onclick="toggleExpand('${cardId}', this)">
      View Details <span class="chevron">▾</span>
    </button>

    <div id="${cardId}" class="card-details">
      <div class="card-details-inner">
        <div class="detail-section">
          <div class="detail-title">🧠 Reasons for Selling</div>
          ${reasons}
        </div>

        <div class="detail-section">
          <div class="detail-title">🎯 Promoter Intent</div>
          <div class="detail-text">
            <span class="detail-label">Confidence:</span> ${esc(a.intent_confidence || 'N/A')}<br>
            <span class="detail-label">Pattern:</span> ${esc(a.intent_pattern || 'N/A')}<br>
            <span class="detail-label">Trend:</span> ${esc(a.intent_trend_label || 'N/A')}
          </div>
        </div>

        <div class="detail-section">
          <div class="detail-title">📊 Impact Analysis</div>
          <div class="detail-text">
            <span class="detail-label">Governance:</span> ${esc(a.impact_governance || 'N/A')}<br>
            <span class="detail-label">Market Perception:</span> ${esc(a.impact_perception || 'N/A')}<br>
            <span class="detail-label">Short Term:</span> ${esc(a.impact_short_term || 'N/A')}<br>
            <span class="detail-label">Long Term:</span> ${esc(a.impact_long_term || 'N/A')}
          </div>
        </div>

        <div class="detail-section">
          <div class="detail-title">💡 Investor Recommendation</div>
          <div class="recommendation-box">${esc(a.recommendation || 'N/A')}</div>
        </div>
      </div>
    </div>

    <div class="card-footer">
      <span>Mkt Cap: <strong>${esc(r.market_cap || 'N/A')}</strong> · ${esc(a.analyzed_at || '')}</span>
      <a class="card-link" href="${esc(r.url || '#')}" target="_blank" rel="noopener">Screener →</a>
    </div>
  </div>`;
}

/* ═══════════════════ EXPANDABLE CARDS ═══════════════════ */

function toggleExpand(id, btn) {
  const el = document.getElementById(id);
  const isOpen = el.classList.contains('open');
  el.classList.toggle('open');
  btn.classList.toggle('open');
  btn.querySelector('.chevron').style.transform = isOpen ? '' : 'rotate(180deg)';
}

/* ═══════════════════ CHARTS (Chart.js) ═══════════════════ */

async function loadTrendCharts() {
  try {
    const resp = await fetch('/api/trend');
    const data = await resp.json();
    renderCharts(data);
    document.getElementById('chartsSection').style.display = 'block';
  } catch (err) { console.error('[trend]', err); }
}

function renderCharts(data) {
  // Risk Distribution Donut
  const riskCtx = document.getElementById('riskChart').getContext('2d');
  if (riskChart) riskChart.destroy();
  riskChart = new Chart(riskCtx, {
    type: 'doughnut',
    data: {
      labels: ['High Risk', 'Medium Risk', 'Low Risk'],
      datasets: [{
        data: [data.risk_distribution.High, data.risk_distribution.Medium, data.risk_distribution.Low],
        backgroundColor: ['#ff4d4d', '#ffa500', '#00cc88'],
        borderColor: '#0d1117',
        borderWidth: 3,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#6b7a99', padding: 16, font: { size: 12 } } },
      },
    },
  });

  // Verdict Distribution Bar
  const verdictCtx = document.getElementById('verdictChart').getContext('2d');
  if (verdictChart) verdictChart.destroy();
  verdictChart = new Chart(verdictCtx, {
    type: 'bar',
    data: {
      labels: ['Exit', 'Caution', 'Hold', 'Buy'],
      datasets: [{
        label: 'Companies',
        data: [data.verdict_distribution.Exit, data.verdict_distribution.Caution, data.verdict_distribution.Hold, data.verdict_distribution.Buy],
        backgroundColor: ['#ff4d4d', '#ff8c00', '#ffc107', '#00cc88'],
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: '#1e2a4220' }, ticks: { color: '#6b7a99' } },
        y: { grid: { display: false }, ticks: { color: '#e2e8f0', font: { weight: '600' } } },
      },
    },
  });

  // Holding Comparison Bar (top 10 biggest drops)
  const holdingCtx = document.getElementById('holdingChart').getContext('2d');
  if (holdingChart) holdingChart.destroy();

  const sorted = [...data.holding_data].sort((a, b) => a.change - b.change).slice(0, 10);
  holdingChart = new Chart(holdingCtx, {
    type: 'bar',
    data: {
      labels: sorted.map(d => d.ticker),
      datasets: [
        {
          label: 'Previous %',
          data: sorted.map(d => d.previous),
          backgroundColor: '#6b7a9940',
          borderRadius: 4,
        },
        {
          label: 'Current %',
          data: sorted.map(d => d.current),
          backgroundColor: '#4f7cff80',
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { color: '#6b7a99', padding: 12, font: { size: 11 } } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#6b7a99', font: { size: 10 } } },
        y: { grid: { color: '#1e2a4220' }, ticks: { color: '#6b7a99' }, min: 0, max: 100 },
      },
    },
  });
}

function scrollToTrend() {
  const el = document.getElementById('chartsSection');
  if (el && el.style.display !== 'none') {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else {
    showHint('💡 Run "update" first to generate trend data');
  }
}

/* ═══════════════════ MODAL ═══════════════════ */

async function openAnalyzeModal(ticker) {
  const overlay = document.getElementById('modalOverlay');
  const body = document.getElementById('modalBody');
  const title = document.getElementById('modalTitle');

  title.textContent = `Analyzing ${ticker}…`;
  body.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--muted)">Loading…</div>';
  overlay.classList.add('visible');

  try {
    const resp = await fetch(`/api/analyze/${ticker}`);
    const data = await resp.json();

    if (!data.found) {
      body.innerHTML = `<div style="text-align:center;padding:3rem;color:var(--orange)">
        ⚠️ ${esc(data.message || 'Not found')}<br><br>
        <span style="color:var(--muted);font-size:0.85rem">Run "update" first to scan markets.</span>
      </div>`;
      return;
    }

    const r = data.data;
    const a = r.analysis || {};
    title.textContent = `${r.company_name || r.ticker} — Deep Analysis`;

    body.innerHTML = `
      <div style="margin-bottom:1.5rem">
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:1rem">
          <span class="verdict-badge" style="background:${a.verdict_color}18;color:${a.verdict_color};border:1px solid ${a.verdict_color}35;font-size:0.85rem">
            ${a.verdict_icon} ${a.verdict} — ${esc(a.verdict_desc || '')}
          </span>
        </div>

        <div class="holding-strip">
          ${r.promoter_prev != null ? `<div class="hold-cell"><div class="hold-val prev">${r.promoter_prev}%</div><div class="hold-lbl">Previous</div></div><div class="hold-arrow">→</div>` : ''}
          <div class="hold-cell"><div class="hold-val current">${r.promoter_current}%</div><div class="hold-lbl">Current</div></div>
          <div class="hold-cell"><div class="hold-val change">▼ ${Math.abs(r.promoter_change || 0).toFixed(2)}%</div><div class="hold-lbl">Reduction</div></div>
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-title">🧠 Probable Reasons for Selling</div>
        ${(a.reasons || []).map(r => `<div class="detail-item">• ${esc(r)}</div>`).join('')}
      </div>

      <div class="detail-section">
        <div class="detail-title">🎯 Promoter Intent Analysis</div>
        <div class="detail-text">
          <strong>Confidence Level:</strong> ${esc(a.intent_confidence)}<br>
          <strong>Selling Pattern:</strong> ${esc(a.intent_pattern)}<br>
          <strong>Trend Assessment:</strong> ${esc(a.intent_trend_label)}<br>
          <strong>Mode of Selling:</strong> ${esc(a.mode_of_selling)}
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-title">📊 Impact on Company</div>
        <div class="detail-text">
          <strong>Governance Signal:</strong> ${esc(a.impact_governance)}<br>
          <strong>Market Perception:</strong> ${esc(a.impact_perception)}<br>
          <strong>Short-Term Impact:</strong> ${esc(a.impact_short_term)}<br>
          <strong>Long-Term Impact:</strong> ${esc(a.impact_long_term)}
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-title">💡 Investor Decision</div>
        <div class="recommendation-box" style="font-size:0.9rem">${esc(a.recommendation)}</div>
      </div>

      <div style="margin-top:1.2rem;text-align:center">
        <a class="card-link" href="${esc(r.url || '#')}" target="_blank" rel="noopener" style="padding:8px 20px;font-size:0.85rem">View on Screener →</a>
      </div>
    `;
  } catch (err) {
    body.innerHTML = `<div style="text-align:center;padding:3rem;color:var(--red)">Error: ${esc(err.message)}</div>`;
  }
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('visible');
}

/* ═══════════════════ FILTERS ═══════════════════ */

function filterResults() { if (allResults.length) renderCards(); }
function setSentimentFilter(val, btn) {
  sentimentFilter = val;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filterResults();
}

/* ═══════════════════ UI HELPERS ═══════════════════ */

function hideAllSections() {
  document.getElementById('resultsGrid').innerHTML = '';
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('errorState').style.display = 'none';
  document.getElementById('statsStrip').style.display = 'none';
  document.getElementById('filterBar').style.display = 'none';
  document.getElementById('dashboardSections').style.display = 'none';
  document.getElementById('chartsSection').style.display = 'none';
  document.getElementById('highRiskSection').style.display = 'none';
}

function showProgress(visible) {
  document.getElementById('progressSection').style.display = visible ? 'block' : 'none';
  if (!visible) document.getElementById('progressBar').style.width = '100%';
}
function updateProgress(done, total, pct, ticker) {
  document.getElementById('progressBar').style.width = pct + '%';
  document.getElementById('progressText').textContent = `Scanned ${done} of ${total} companies`;
  document.getElementById('progressPct').textContent = pct + '%';
  document.getElementById('currentTicker').textContent = `🔍 Scanning: ${ticker}`;
}
function setRunning(isRunning) {
  const btn = document.getElementById('runBtn');
  btn.disabled = isRunning;
  btn.textContent = isRunning ? '⏳ Scanning…' : 'Run ▶';
}
function showError(msg) {
  document.getElementById('errorMsg').textContent = msg;
  document.getElementById('errorState').style.display = 'block';
}
function showHint(msg) {
  const hint = document.querySelector('.command-hint');
  const original = hint.innerHTML;
  hint.style.color = 'var(--orange)';
  hint.textContent = msg;
  setTimeout(() => { hint.style.color = ''; hint.innerHTML = original; }, 3000);
}
function shakeInput() {
  const box = document.querySelector('.command-box');
  box.style.borderColor = 'var(--red)';
  setTimeout(() => { box.style.borderColor = ''; }, 1000);
}
function esc(str) {
  if (typeof str !== 'string') return str ?? '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
