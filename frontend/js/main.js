/* ============================================================
   Main Application Module
   ============================================================ */

// ── Utility functions ─────────────────────────────────────────
function showSpinner(show) {
  document.getElementById('spinner').classList.toggle('hidden', !show);
}

function showToast(message, type = 'success', duration = 3500) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className   = `toast ${type}`;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), duration);
}

function escapeHtml(str = '') {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

function formatStatus(s) {
  const map = {
    reported:    '🔵 Reported',
    validated:   '🟣 Validated',
    in_progress: '🟠 In Progress',
    resolved:    '🟢 Resolved',
    rejected:    '🔴 Rejected',
  };
  return map[s] || s;
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)    return 'just now';
  if (mins < 60)   return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)    return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

// ── View navigation ───────────────────────────────────────────
function switchView(viewName) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`${viewName}View`).classList.add('active');
  document.querySelector(`[data-view="${viewName}"]`)?.classList.add('active');

  if (viewName === 'map') {
    setTimeout(() => mainMap && mainMap.invalidateSize(), 100);
  } else if (viewName === 'alerts') {
    loadAlerts();
  } else if (viewName === 'dashboard') {
    loadDashboard();
  }
}

// ── App initialization ────────────────────────────────────────
function initApp() {
  // Navigation
  document.querySelectorAll('[data-view]').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });

  // Close modals
  document.getElementById('closeDetail').addEventListener('click', () => {
    document.getElementById('alertDetailModal').classList.remove('active');
  });
  document.getElementById('alertDetailModal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('alertDetailModal')) {
      document.getElementById('alertDetailModal').classList.remove('active');
    }
  });

  // Search debounce
  let searchDebounce;
  document.getElementById('alertSearch').addEventListener('input', () => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => loadAlerts(), 500);
  });

  document.getElementById('alertSortBy').addEventListener('change',       () => loadAlerts());
  document.getElementById('alertFilterStatus2').addEventListener('change', () => loadAlerts());

  // Empty state Report button — opens the report modal
  document.getElementById('emptyStateReportBtn')?.addEventListener('click', () => {
    document.getElementById('reportBtn').click();
  });

  // Initialize modules
  initMainMap();
  initReportModal();
  loadFormSelects();

  // Load categories into the map filter panel
  apiFetch('/categories')
    .then(res => res.json())
    .then(cats => {
      const sel = document.getElementById('filterCategory');
      cats.forEach(c => {
        sel.innerHTML += `<option value="${c.id}">${c.name}</option>`;
      });
    })
    .catch(() => { /* filter will just show all alerts */ });

  // Initial view
  switchView('map');
}

// ── Bootstrap ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initAuth();
});