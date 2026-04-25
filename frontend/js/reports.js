/* ============================================================
   Reports Module – initReportModal + loadFormSelects
   ============================================================ */

const DEFAULT_CATEGORIES = [
  { id: 1, name: 'Water Issue' },
  { id: 2, name: 'Waste / Littering' },
  { id: 3, name: 'Air Quality' },
  { id: 4, name: 'Energy Waste' },
  { id: 5, name: 'Biodiversity' },
  { id: 6, name: 'Noise Pollution' },
];

const DEFAULT_ZONES = [
  'Main Building', 'Library', 'Labs', 'Cafeteria',
  'Sports Area', 'Parking', 'Garden', 'Dormitories', 'Administration',
];

// ── Load categories & zones into the report form ──────────────
function loadFormSelects() {
  // Categories for report form
  apiFetch('/categories')
    .then(r => r.json())
    .then(cats => {
      const sel = document.getElementById('rCategory');
      cats.forEach(c => {
        sel.innerHTML += `<option value="${c.id}">${c.name}</option>`;
      });
    })
    .catch(() => {
      // Fallback: use built-in category list when backend is offline
      const sel = document.getElementById('rCategory');
      DEFAULT_CATEGORIES.forEach(c => {
        sel.innerHTML += `<option value="${c.id}">${c.name}</option>`;
      });
    });

  // Zones for report form
  apiFetch('/zones')
    .then(r => r.json())
    .then(zones => {
      const sel = document.getElementById('rZone');
      zones.forEach(z => {
        sel.innerHTML += `<option value="${z.id}">${z.name}</option>`;
      });
    })
    .catch(() => {
      // Fallback: use built-in zone list when backend is offline
      const sel = document.getElementById('rZone');
      DEFAULT_ZONES.forEach(z => {
        sel.innerHTML += `<option value="${z}">${z}</option>`;
      });
    });
}

// ── Report modal wiring ───────────────────────────────────────
function initReportModal() {
  const modal     = document.getElementById('reportModal');
  const reportBtn = document.getElementById('reportBtn');
  const closeBtn  = document.getElementById('closeReport');
  const cancelBtn = document.getElementById('cancelReport');

  // ── Open ──────────────────────────────────────────────────
  function openModal() {
    modal.classList.add('active');
    // Re-initialise the mini map every time so it sizes correctly
    initReportMap();
  }

  // ── Close / reset ─────────────────────────────────────────
  function closeModal() {
    modal.classList.remove('active');
    document.getElementById('reportForm').reset();
    const preview = document.getElementById('imagePreview');
    preview.src = '';
    preview.classList.add('hidden');
    document.getElementById('reportError').classList.add('hidden');
    document.getElementById('rLat').textContent = '--';
    document.getElementById('rLng').textContent = '--';
    document.getElementById('rLatInput').value  = '';
    document.getElementById('rLngInput').value  = '';
  }

  reportBtn.addEventListener('click', openModal);
  closeBtn .addEventListener('click', closeModal);
  cancelBtn.addEventListener('click', closeModal);

  // Click outside modal-box to close
  modal.addEventListener('click', e => {
    if (e.target === modal) closeModal();
  });

  // ── Image preview ─────────────────────────────────────────
  const fileInput      = document.getElementById('rImage');
  const fileUploadArea = document.getElementById('fileUploadArea');
  const imagePreview   = document.getElementById('imagePreview');

  fileUploadArea.addEventListener('click', () => fileInput.click());

  // Drag-and-drop
  fileUploadArea.addEventListener('dragover', e => {
    e.preventDefault();
    fileUploadArea.style.borderColor = '#2e7d32';
  });
  fileUploadArea.addEventListener('dragleave', () => {
    fileUploadArea.style.borderColor = '';
  });
  fileUploadArea.addEventListener('drop', e => {
    e.preventDefault();
    fileUploadArea.style.borderColor = '';
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      fileInput.files = e.dataTransfer.files;
      showImagePreview(file);
    }
  });

  fileInput.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) showImagePreview(file);
  });

  function showImagePreview(file) {
    const reader = new FileReader();
    reader.onload = ev => {
      imagePreview.src = ev.target.result;
      imagePreview.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
  }

  // ── ML description auto-suggest (optional live feature) ───
  let mlDebounce;
  document.getElementById('rDescription').addEventListener('input', () => {
    clearTimeout(mlDebounce);
    const desc = document.getElementById('rDescription').value;
    if (desc.length < 20) {
      document.getElementById('mlPreview').classList.add('hidden');
      return;
    }
    mlDebounce = setTimeout(() => fetchMlSuggestion(desc), 700);
  });

  async function fetchMlSuggestion(text) {
    try {
      const res = await apiFetch('/ml/predict', {
        method: 'POST',
        body: JSON.stringify({ text }),
      });
      if (!res.ok) return;
      const ml = await res.json();
      document.getElementById('mlCatSug').textContent = ml.category  || '–';
      document.getElementById('mlPriSug').textContent = ml.priority  || '–';
      document.getElementById('mlConf'  ).textContent = ml.confidence
        ? `${(ml.confidence * 100).toFixed(0)}%`
        : '–';
      document.getElementById('mlPreview').classList.remove('hidden');
    } catch {
      // ML service offline – silently skip the preview
    }
  }

  // ── Form submit ───────────────────────────────────────────
  document.getElementById('reportForm').addEventListener('submit', async e => {
    e.preventDefault();
    const errEl = document.getElementById('reportError');
    errEl.classList.add('hidden');

    const lat = document.getElementById('rLatInput').value;
    const lng = document.getElementById('rLngInput').value;

    if (!lat || !lng) {
      errEl.textContent = 'Please click on the map to pin the exact location.';
      errEl.classList.remove('hidden');
      return;
    }

    if (!document.getElementById('rCategory').value) {
      errEl.textContent = 'Please select a category.';
      errEl.classList.remove('hidden');
      return;
    }

    showSpinner(true);
    try {
      const fd = new FormData();
      fd.append('title',         document.getElementById('rTitle').value);
      fd.append('description',   document.getElementById('rDescription').value);
      fd.append('category_id',   document.getElementById('rCategory').value);
      fd.append('zone',          document.getElementById('rZone').value);
      fd.append('latitude',      lat);
      fd.append('longitude',     lng);
      fd.append('location_name', document.getElementById('rLocationName').value);
      fd.append('anonymous',     document.getElementById('rAnonymous').checked);

      const imgFile = document.getElementById('rImage').files[0];
      if (imgFile) fd.append('image', imgFile);

      const res = await apiFetch('/alerts', { method: 'POST', body: fd });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.message || `Server error ${res.status}`);
      }

      closeModal();
      showToast('✅ Alert submitted successfully!', 'success');
      // Refresh map markers
      if (typeof loadMapAlerts === 'function') loadMapAlerts();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove('hidden');
    } finally {
      showSpinner(false);
    }
  });
}
