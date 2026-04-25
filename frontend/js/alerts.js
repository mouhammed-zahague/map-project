/* ============================================================
   Map Module – Leaflet Integration
   ENREDD Batna: 35.5641 N, 6.1845 E
   ============================================================ */

const CAMPUS = { lat: 35.5641, lng: 6.1845, zoom: 17 };
let mainMap, reportMap, heatLayer, markersLayer;
let heatmapActive = false;

const PRIORITY_COLORS = {
  critical: '#b71c1c',
  high:     '#e65100',
  medium:   '#f9a825',
  low:      '#2e7d32',
};

function initMainMap() {
  mainMap = L.map('map', { zoomControl: true }).setView(
    [CAMPUS.lat, CAMPUS.lng], CAMPUS.zoom
  );

  // OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 21,
    attribution: '© OpenStreetMap contributors | ENREDD Batna',
  }).addTo(mainMap);

  // Satellite option (ESRI)
  const satellite = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Tiles © Esri' }
  );

  // Layer control
  L.control.layers({
    'Street Map': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 21, attribution: '© OpenStreetMap',
    }).addTo(mainMap),
    'Satellite': satellite,
  }).addTo(mainMap);

  markersLayer = L.layerGroup().addTo(mainMap);

  // Scale
  L.control.scale({ metric: true, imperial: false }).addTo(mainMap);

  // Campus boundary marker
  L.marker([CAMPUS.lat, CAMPUS.lng], {
    icon: L.divIcon({
      className: '',
      html: `<div style="
        background:#1b5e20;color:#fff;padding:4px 10px;
        border-radius:6px;font-size:11px;font-weight:700;
        white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,.3);">
        ENREDD Batna</div>`,
      iconAnchor: [40, 14],
    }),
  }).addTo(mainMap);

  // Map controls
  document.getElementById('centerMap').addEventListener('click', () => {
    mainMap.setView([CAMPUS.lat, CAMPUS.lng], CAMPUS.zoom);
  });

  document.getElementById('toggleHeatmap').addEventListener('click', toggleHeatmap);
  document.getElementById('applyFilters').addEventListener('click', loadMapAlerts);
  document.getElementById('clearFilters').addEventListener('click', () => {
    document.getElementById('filterStatus').value   = '';
    document.getElementById('filterCategory').value = '';
    document.getElementById('filterPriority').value = '';
    loadMapAlerts();
  });

  loadMapAlerts();
}

function createMarkerIcon(alert) {
  const color = PRIORITY_COLORS[alert.priority] || '#607d8b';
  const icon  = alert.category?.icon || 'fa-exclamation';
  return L.divIcon({
    className: '',
    iconSize:  [36, 36],
    iconAnchor:[18, 36],
    popupAnchor:[0, -36],
    html: `
      <div style="
        width:36px;height:36px;border-radius:50% 50% 50% 0;
        background:${color};transform:rotate(-45deg);
        box-shadow:0 3px 10px rgba(0,0,0,.3);
        border:2px solid #fff;
        display:flex;align-items:center;justify-content:center;">
        <i class="fas ${icon}" style="
          transform:rotate(45deg);color:#fff;font-size:13px;"></i>
      </div>`,
  });
}

async function loadMapAlerts() {
  try {
    const res  = await apiFetch('/alerts/map');
    const data = await res.json();
    markersLayer.clearLayers();

    // Sidebar mini-list
    const miniList = document.getElementById('miniAlertList');
    miniList.innerHTML = '';

    const status   = document.getElementById('filterStatus').value;
    const catId    = document.getElementById('filterCategory').value;
    const priority = document.getElementById('filterPriority').value;

    const filtered = data.filter(a => {
      if (status   && a.status   !== status)           return false;
      if (catId    && String(a.category?.id) !== catId) return false;
      if (priority && a.priority !== priority)          return false;
      return true;
    });

    document.getElementById('alertsBadge').textContent = filtered.length;

    filtered.forEach(alert => {
      const marker = L.marker([alert.latitude, alert.longitude], {
        icon: createMarkerIcon(alert),
      });

      const popupContent = `
        <div style="min-width:220px;font-family:sans-serif;">
          <strong style="color:${PRIORITY_COLORS[alert.priority]}">${alert.title}</strong>
          <br>
          <span style="background:${alert.category?.color||'#888'};color:#fff;
            padding:2px 8px;border-radius:10px;font-size:11px;margin:4px 0;display:inline-block;">
            ${alert.category?.name || 'Unknown'}
          </span>
          <br>
          <small>📍 ${alert.location_name || 'ENREDD Campus'}</small><br>
          <small>🕐 ${new Date(alert.created_at).toLocaleDateString()}</small><br>
          <span style="font-size:11px;font-weight:600;color:#555;">
            Status: ${alert.status.toUpperCase()}
          </span><br>
          <button onclick="openAlertDetail(${alert.id})"
            style="margin-top:8px;background:#2e7d32;color:#fff;border:none;
              padding:5px 12px;border-radius:6px;cursor:pointer;font-size:12px;width:100%;">
            View Details
          </button>
        </div>`;

      marker.bindPopup(popupContent, { maxWidth: 280 });
      marker.on('click', () => marker.openPopup());
      markersLayer.addLayer(marker);

      // Mini list item
      const item = document.createElement('div');
      item.className = 'mini-alert-item';
      item.innerHTML = `
        <div class="title">${alert.title}</div>
        <div class="meta">
          <span>${alert.category?.name || ''}</span> ·
          <span style="color:${PRIORITY_COLORS[alert.priority]}">${alert.priority}</span>
        </div>`;
      item.addEventListener('click', () => {
        mainMap.setView([alert.latitude, alert.longitude], 19);
        marker.openPopup();
      });
      miniList.appendChild(item);
    });

    // Update heatmap if active
    if (heatmapActive) loadHeatmap();
  } catch (err) {
    console.error('Map load error:', err);
  }
}

async function loadHeatmap() {
  try {
    const res  = await apiFetch('/dashboard/heatmap');
    const data = await res.json();
    if (heatLayer) mainMap.removeLayer(heatLayer);
    heatLayer = L.heatLayer(data.heatmap_data, {
      radius: 25, blur: 20, maxZoom: 18,
      gradient: { 0.2: '#4CAF50', 0.5: '#FF9800', 0.8: '#F44336', 1.0: '#B71C1C' },
    }).addTo(mainMap);
  } catch (err) {
    console.error('Heatmap error:', err);
  }
}

function toggleHeatmap() {
  heatmapActive = !heatmapActive;
  const btn = document.getElementById('toggleHeatmap');
  if (heatmapActive) {
    loadHeatmap();
    btn.classList.add('btn-primary');
  } else {
    if (heatLayer) mainMap.removeLayer(heatLayer);
    btn.classList.remove('btn-primary');
  }
}

// ── Report Map ────────────────────────────────────────────────
let reportMarker = null;

function initReportMap() {
  if (reportMap) { reportMap.remove(); reportMap = null; }
  reportMap = L.map('reportMap').setView([CAMPUS.lat, CAMPUS.lng], CAMPUS.zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 21,
  }).addTo(reportMap);

  reportMap.on('click', (e) => {
    const { lat, lng } = e.latlng;
    if (reportMarker) reportMap.removeLayer(reportMarker);
    reportMarker = L.marker([lat, lng], {
      icon: L.divIcon({
        className: '',
        html: '<div style="font-size:24px;">📍</div>',
        iconAnchor: [12, 24],
      }),
      draggable: true,
    }).addTo(reportMap);

    updateCoords(lat, lng);
    reportMarker.on('dragend', (ev) => {
      const pos = ev.target.getLatLng();
      updateCoords(pos.lat, pos.lng);
    });
  });

  setTimeout(() => reportMap.invalidateSize(), 300);
}

function updateCoords(lat, lng) {
  document.getElementById('rLat').textContent      = lat.toFixed(6);
  document.getElementById('rLng').textContent      = lng.toFixed(6);
  document.getElementById('rLatInput').value       = lat;
  document.getElementById('rLngInput').value       = lng;
}