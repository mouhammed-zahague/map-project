/* ============================================================
   Dashboard Module
   ============================================================ */

let charts = {};

// ── Demo data shown when the backend is offline ───────────────
const DEMO_STATS = {
  overview: {
    total: 12, reported: 5, validated: 2,
    in_progress: 3, resolved: 2, rejected: 0,
    critical: 1, resolution_rate: 17,
  },
  by_category: [
    { name: 'Water Issue',     count: 4, color: '#1565c0' },
    { name: 'Waste',           count: 3, color: '#2e7d32' },
    { name: 'Air Quality',     count: 2, color: '#e65100' },
    { name: 'Energy Waste',    count: 2, color: '#f9a825' },
    { name: 'Noise',           count: 1, color: '#6a1b9a' },
  ],
  by_zone: [
    { zone: 'Library',    count: 4 },
    { zone: 'Labs',       count: 3 },
    { zone: 'Cafeteria',  count: 2 },
    { zone: 'Garden',     count: 2 },
    { zone: 'Parking',    count: 1 },
  ],
  daily_trend: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((d, i) => ({
    date: d, count: [1, 2, 1, 3, 2, 1, 2][i],
  })),
  recent_alerts: [],
};

const DEMO_ML = { models_loaded: false };

async function loadDashboard() {
  showSpinner(true);
  try {
    const [statsRes, mlRes] = await Promise.all([
      apiFetch('/dashboard/stats'),
      apiFetch('/ml/info'),
    ]);

    if (!statsRes.ok) throw new Error(`Stats API error: ${statsRes.status}`);

    const stats = await statsRes.json();
    const ml    = await mlRes.json();

    renderStatCards(stats.overview);
    renderCharts(stats);
    renderRecentAlerts(stats.recent_alerts);
    renderMlInfo(ml);
  } catch (err) {
    // Backend offline – render demo data so charts are always visible
    console.warn('Dashboard: backend unavailable, switching to demo data.', err.message);
    renderStatCards(DEMO_STATS.overview);
    renderCharts(DEMO_STATS);
    renderRecentAlerts([]);
    renderMlInfo(DEMO_ML);
    showToast('Demo mode – connect the backend for live data', 'info', 5000);
  } finally {
    showSpinner(false);
  }
}

function renderStatCards(ov) {
  document.getElementById('statTotal').textContent      = ov.total;
  document.getElementById('statReported').textContent   = ov.reported;
  document.getElementById('statInProgress').textContent = ov.in_progress;
  document.getElementById('statResolved').textContent   = ov.resolved;
  document.getElementById('statCritical').textContent   = ov.critical;
  document.getElementById('statRate').textContent       = `${ov.resolution_rate}%`;
}

function renderCharts(stats) {
  // Category chart
  const catCtx = document.getElementById('categoryChart').getContext('2d');
  if (charts.category) charts.category.destroy();
  charts.category = new Chart(catCtx, {
    type: 'doughnut',
    data: {
      labels:   stats.by_category.map(c => c.name),
      datasets: [{
        data:            stats.by_category.map(c => c.count),
        backgroundColor: stats.by_category.map(c => c.color || '#4CAF50'),
        borderWidth: 2, borderColor: '#fff',
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'right', labels: { font: { size: 11 } } },
      },
    },
  });

  // Status chart
  const stCtx = document.getElementById('statusChart').getContext('2d');
  if (charts.status) charts.status.destroy();
  const ov = stats.overview;
  charts.status = new Chart(stCtx, {
    type: 'bar',
    data: {
      labels:   ['Reported', 'Validated', 'In Progress', 'Resolved', 'Rejected'],
      datasets: [{
        label:           'Count',
        data:            [ov.reported, ov.validated, ov.in_progress, ov.resolved, ov.rejected],
        backgroundColor: ['#1565c0','#6a1b9a','#e65100','#2e7d32','#b71c1c'],
        borderRadius:    8,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales:  { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
    },
  });

  // Trend chart
  const trCtx = document.getElementById('trendChart').getContext('2d');
  if (charts.trend) charts.trend.destroy();
  charts.trend = new Chart(trCtx, {
    type: 'line',
    data: {
      labels:   stats.daily_trend.map(d => d.date),
      datasets: [{
        label:           'Daily Alerts',
        data:            stats.daily_trend.map(d => d.count),
        borderColor:     '#2e7d32',
        backgroundColor: 'rgba(46,125,50,.15)',
        borderWidth:     3,
        tension:         0.4,
        fill:            true,
        pointRadius:     5,
        pointBackgroundColor: '#2e7d32',
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales:  { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
    },
  });

  // Zone chart
  const zCtx = document.getElementById('zoneChart').getContext('2d');
  if (charts.zone) charts.zone.destroy();
  charts.zone = new Chart(zCtx, {
    type: 'bar',
    data: {
      labels:   stats.by_zone.slice(0, 6).map(z => z.zone),
      datasets: [{
        label:           'Alerts',
        data:            stats.by_zone.slice(0, 6).map(z => z.count),
        backgroundColor: 'rgba(76,175,80,.7)',
        borderColor:     '#2e7d32',
        borderWidth:     2,
        borderRadius:    6,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: { legend: { display: false } },
      scales:  { x: { beginAtZero: true } },
    },
  });
}

function renderRecentAlerts(alerts) {
  const tbody = document.getElementById('recentAlertsBody');
  tbody.innerHTML = alerts.map(a => `
    <tr style="cursor:pointer;" onclick="openAlertDetail(${a.id})">
      <td>#${a.id}</td>
      <td>${escapeHtml(a.title)}</td>
      <td>
        <span class="cat-chip" style="background:${a.category?.color||'#888'};font-size:.75rem">
          ${a.category?.name||'Unknown'}
        </span>
      </td>
      <td><span class="priority-badge p-${a.priority}">${a.priority}</span></td>
      <td><span class="status-badge s-${a.status}">${formatStatus(a.status)}</span></td>
      <td>${new Date(a.created_at).toLocaleDateString()}</td>
    </tr>`).join('');
}

function renderMlInfo(ml) {
  const el = document.getElementById('mlInfoContent');
  if (!ml.models_loaded) {
    el.innerHTML = `<div class="ml-detail-item">
      <span>Models not loaded. Run train_model.py first.</span>
    </div>`;
    return;
  }
  el.innerHTML = `
    <div class="ml-detail-item">
      <strong>${(ml.category_accuracy*100).toFixed(1)}%</strong>
      Category Accuracy
    </div>
    <div class="ml-detail-item">
      <strong>${(ml.priority_accuracy*100).toFixed(1)}%</strong>
      Priority Accuracy
    </div>
    <div class="ml-detail-item">
      <strong>${(ml.cv_mean*100).toFixed(1)}%</strong>
      Cross-Validation Mean
    </div>
    <div class="ml-detail-item">
      <strong>${ml.training_samples}</strong>
      Training Samples
    </div>
    <div class="ml-detail-item">
      <strong>${ml.categories?.length||0}</strong>
      Categories Supported
    </div>`;
}