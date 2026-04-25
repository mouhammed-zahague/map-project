/* ============================================================
   Auth Module – Green Campus Alert Map
   Authentication powered by Supabase Auth.
   Requires: supabase-client.js (loaded before this file)
   ============================================================ */

const API_BASE = 'http://localhost:5000/api';

// ── Session helpers (light wrapper around Supabase session) ───
const SESSION_KEY = 'gca_session';
const Auth = {
  getUser:    () => JSON.parse(localStorage.getItem(SESSION_KEY) || 'null'),
  setUser:    (u) => localStorage.setItem(SESSION_KEY, JSON.stringify(u)),
  clear:      () => localStorage.removeItem(SESSION_KEY),
  isLoggedIn: () => !!Auth.getUser(),
  isManager:  () => {
    const u = Auth.getUser();
    return u && ['admin', 'manager', 'staff'].includes(u.role);
  },
  isAdmin: () => {
    const u = Auth.getUser();
    return u && u.role === 'admin';
  },
};

// ── Build a local user object from a Supabase user ────────────
function buildUser(supaUser) {
  const meta = supaUser.user_metadata || {};
  return {
    id:        supaUser.id,
    email:     supaUser.email,
    full_name: meta.full_name || supaUser.email.split('@')[0],
    username:  meta.username  || supaUser.email.split('@')[0],
    role:      meta.role      || 'student',
  };
}

// ── API request helper (attaches Supabase token when available)
async function apiFetch(endpoint, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  // Attach the live Supabase JWT so the backend can verify the user
  try {
    const { data: { session } } = await supabaseClient.auth.getSession();
    if (session) headers['Authorization'] = `Bearer ${session.access_token}`;
  } catch (_) { /* offline / no session */ }

  if (options.body instanceof FormData) delete headers['Content-Type'];

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (response.status === 401) { Auth.clear(); location.reload(); }
  return response;
}

// ── Map Supabase error messages to friendly text ──────────────
function friendlyAuthError(error, mode) {
  const msg = (error?.message || '').toLowerCase();
  if (
    msg.includes('invalid login credentials') ||
    msg.includes('invalid email or password') ||
    msg.includes('email not confirmed')        ||
    error?.status === 400
  ) {
    return mode === 'login'
      ? 'Email or password is incorrect'
      : 'Invalid email or password';
  }
  if (
    msg.includes('already registered') ||
    msg.includes('user already exists') ||
    error?.code === 'user_already_exists'
  ) {
    return 'User already exists. Please sign in';
  }
  if (msg.includes('password should be at least')) {
    return 'Password must be at least 6 characters';
  }
  if (msg.includes('unable to validate email')) {
    return 'Please enter a valid email address';
  }
  return error?.message || 'An unexpected error occurred. Please try again.';
}

// ── Init auth UI ──────────────────────────────────────────────
function initAuth() {
  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`${btn.dataset.tab}Tab`).classList.add('active');
    });
  });

  // Password toggle
  document.querySelectorAll('.toggle-pass').forEach(icon => {
    icon.addEventListener('click', () => {
      const input = icon.previousElementSibling;
      input.type  = input.type === 'password' ? 'text' : 'password';
      icon.classList.toggle('fa-eye');
      icon.classList.toggle('fa-eye-slash');
    });
  });

  // Forgot Password
  const forgotLink = document.getElementById('forgotPasswordLink');
  if (forgotLink) {
    forgotLink.addEventListener('click', async (e) => {
      e.preventDefault();
      const email     = document.getElementById('loginIdentifier').value.trim();
      const errEl     = document.getElementById('loginError');
      const successEl = document.getElementById('forgotSuccess');
      errEl.classList.add('hidden');
      if (successEl) successEl.classList.add('hidden');

      if (!email) {
        errEl.textContent = 'Please enter your email address first';
        errEl.classList.remove('hidden');
        return;
      }

      showSpinner(true);
      try {
        const { error } = await supabaseClient.auth.resetPasswordForEmail(email);
        if (error) throw error;
        if (successEl) {
          successEl.textContent = `Password reset email sent to ${email}. Check your inbox.`;
          successEl.classList.remove('hidden');
        }
      } catch (err) {
        errEl.textContent = err.message || 'Could not send reset email. Try again.';
        errEl.classList.remove('hidden');
      } finally {
        showSpinner(false);
      }
    });
  }

  // ── Sign In ───────────────────────────────────────────────
  document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl     = document.getElementById('loginError');
    const successEl = document.getElementById('forgotSuccess');
    errEl.classList.add('hidden');
    if (successEl) successEl.classList.add('hidden');
    showSpinner(true);

    try {
      const email    = document.getElementById('loginIdentifier').value.trim();
      const password = document.getElementById('loginPassword').value;

      const { data, error } = await supabaseClient.auth.signInWithPassword({ email, password });

      if (error) {
        errEl.textContent = friendlyAuthError(error, 'login');
        errEl.classList.remove('hidden');
        return;
      }

      // Success → build user object, save session, go to home/dashboard
      const user = buildUser(data.user);
      Auth.setUser(user);
      onLoginSuccess(user);           // "redirect" to the dashboard view
    } catch (err) {
      errEl.textContent = 'Something went wrong. Please try again.';
      errEl.classList.remove('hidden');
    } finally {
      showSpinner(false);
    }
  });

  // ── Google Sign-In via Supabase OAuth ────────────────────────
  const googleBtn = document.getElementById('googleSignInBtn');
  if (googleBtn) {
    googleBtn.addEventListener('click', async () => {
      const errEl = document.getElementById('loginError');
      errEl.classList.add('hidden');
      showSpinner(true);
      try {
        // redirectTo must match one of the Allowed Redirect URLs in
        // Supabase Dashboard → Authentication → URL Configuration.
        const { error } = await supabaseClient.auth.signInWithOAuth({
          provider: 'google',
          options: {
            redirectTo: window.location.href,   // land back on this exact page
            queryParams: {
              access_type: 'offline',
              prompt: 'select_account',          // always show the account picker
            },
          },
        });
        if (error) throw error;
        // Supabase redirects the browser to Google – the rest is handled
        // by onAuthStateChange (SIGNED_IN) when the user is redirected back.
      } catch (err) {
        errEl.textContent = err.message || 'Google sign-in failed. Please try again.';
        errEl.classList.remove('hidden');
        showSpinner(false);
      }
      // Note: don't call showSpinner(false) in finally – the page is
      // navigating away, so leaving the spinner up is intentional.
    });
  }

  // ── Sign Up ───────────────────────────────────────────────
  document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('registerError');
    errEl.classList.add('hidden');
    showSpinner(true);

    try {
      const email    = document.getElementById('regEmail').value.trim();
      const password = document.getElementById('regPassword').value;
      const fullName = document.getElementById('regFullName').value.trim();
      const username = (document.getElementById('regUsername')?.value || '').trim()
                       || email.split('@')[0];

      if (password.length < 6) {
        errEl.textContent = 'Password must be at least 6 characters';
        errEl.classList.remove('hidden');
        return;
      }

      const { data, error } = await supabaseClient.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName, username }, // stored in user_metadata
        },
      });

      if (error) {
        errEl.textContent = friendlyAuthError(error, 'signup');
        errEl.classList.remove('hidden');
        return;
      }

      // Never auto-login after sign-up.
      // If Supabase auto-created a session (email confirmation disabled),
      // sign it out so the user must go through the login step manually.
      if (data.session) {
        await supabaseClient.auth.signOut();
      }

      // Always land on the Sign In tab with the email pre-filled
      // and a clear success message — works whether confirmation is
      // required or not.
      document.getElementById('registerForm').reset();
      redirectToLoginWithSuccess(email);
    } catch (err) {
      errEl.textContent = 'Something went wrong. Please try again.';
      errEl.classList.remove('hidden');
    } finally {
      showSpinner(false);
    }
  });

  // ── Logout ────────────────────────────────────────────────
  document.getElementById('logoutBtn').addEventListener('click', async () => {
    showSpinner(true);
    try {
      await supabaseClient.auth.signOut();
      Auth.clear();
      document.getElementById('loginForm').reset();
      document.getElementById('registerForm').reset();
      document.getElementById('app').classList.add('hidden');
      document.getElementById('authModal').classList.add('active');
      showToast('Logged out successfully', 'success');
    } catch (err) {
      showToast('Logout failed: ' + err.message, 'error');
    } finally {
      showSpinner(false);
    }
  });

  // ── Verification screen – back to login ───────────────────
  const verLoginBtn = document.getElementById('verificationLoginBtn');
  if (verLoginBtn) {
    verLoginBtn.addEventListener('click', () => {
      const vs = document.getElementById('verificationScreen');
      if (vs) vs.classList.remove('active');
      document.getElementById('authModal').classList.add('active');
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      document.querySelector('.tab-btn[data-tab="login"]').classList.add('active');
      document.getElementById('loginTab').classList.add('active');
    });
  }

  // ── Restore existing Supabase session on page load ────────
  supabaseClient.auth.getSession().then(({ data: { session } }) => {
    if (session) {
      const user = buildUser(session.user);
      Auth.setUser(user);
      onLoginSuccess(user);
    } else {
      Auth.clear(); // clear any stale local cache
    }
  });

  // ── React to auth state changes (tab focus, token refresh, OAuth redirect) ─
  supabaseClient.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_IN' && session) {
      // Handles the OAuth redirect callback (e.g. Google sign-in)
      // as well as any other sign-in event.
      const user = buildUser(session.user);
      Auth.setUser(user);
      // Only transition to the app if we're still on the auth screen
      if (document.getElementById('authModal')?.classList.contains('active')) {
        onLoginSuccess(user);
      }
    } else if (event === 'SIGNED_OUT' || !session) {
      Auth.clear();
      document.getElementById('app')?.classList.add('hidden');
      document.getElementById('authModal')?.classList.add('active');
    }
  });
}

// ── Called after successful login or register ─────────────────
// This is the "redirect to home (/)" equivalent in a SPA.
function onLoginSuccess(user) {
  document.getElementById('authModal').classList.remove('active');
  const vs = document.getElementById('verificationScreen');
  if (vs) vs.classList.remove('active');
  document.getElementById('app').classList.remove('hidden');
  document.getElementById('userName').textContent = user.full_name || user.username;
  document.getElementById('userRole').textContent = user.role;
  showToast(`Welcome, ${user.full_name || user.username}!`, 'success');
  initApp();
}

// ── Show email-verification pending screen ────────────────────
function showVerificationScreen(email) {
  const emailEl = document.getElementById('verificationEmail');
  if (emailEl) emailEl.textContent = email;
  document.getElementById('authModal').classList.remove('active');
  const vs = document.getElementById('verificationScreen');
  if (vs) vs.classList.add('active');
}

// ── After sign-up: switch to Login tab, pre-fill email, ────────
// ── show success banner. Never auto-login.               ────────
function redirectToLoginWithSuccess(email) {
  // 1. Hide any lingering error/success messages on the login tab
  const loginErr  = document.getElementById('loginError');
  const forgotOk  = document.getElementById('forgotSuccess');
  if (loginErr) loginErr.classList.add('hidden');
  if (forgotOk)  forgotOk.classList.add('hidden');

  // 2. Pre-fill the email so the user doesn't have to retype it
  const emailInput = document.getElementById('loginIdentifier');
  if (emailInput) emailInput.value = email;

  // 3. Switch tabs: deactivate Register, activate Login
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  const loginTab = document.querySelector('.tab-btn[data-tab="login"]');
  if (loginTab) loginTab.classList.add('active');
  document.getElementById('loginTab').classList.add('active');

  // 4. Show the success banner
  const banner = document.getElementById('signupSuccess');
  if (banner) banner.classList.remove('hidden');
}

// ═════════════════════════════════════════════════════════════
// Alerts view – demo data used when the backend is offline
// ═════════════════════════════════════════════════════════════
const DEMO_ALERTS = [
  {
    id: 1, title: 'Water Leak in Library Basement',
    description: 'A broken pipe is leaking water near the archive section. Area is becoming slippery and damaging stored materials.',
    priority: 'critical', status: 'in_progress',
    category: { name: 'Water Issue', color: '#1565c0', icon: 'fa-tint' },
    location_name: 'Library – Basement', created_at: new Date(Date.now() - 86400000).toISOString(),
    upvotes: 12, reporter: 'Ahmed B.',
  },
  {
    id: 2, title: 'Overflowing Trash Bins Near Cafeteria',
    description: 'Multiple trash bins around the cafeteria have been overflowing since yesterday morning.',
    priority: 'high', status: 'reported',
    category: { name: 'Waste / Littering', color: '#2e7d32', icon: 'fa-trash' },
    location_name: 'Cafeteria – Entrance', created_at: new Date(Date.now() - 172800000).toISOString(),
    upvotes: 8, reporter: 'Sara M.',
  },
  {
    id: 3, title: 'Strong Chemical Smell from Lab 3',
    description: 'A persistent chemical odor is coming from Chemistry Lab 3, affecting nearby classrooms.',
    priority: 'high', status: 'validated',
    category: { name: 'Air Quality', color: '#e65100', icon: 'fa-wind' },
    location_name: 'Labs – Building B', created_at: new Date(Date.now() - 259200000).toISOString(),
    upvotes: 15, reporter: 'Mohamed K.',
  },
  {
    id: 4, title: 'Lights Left On in Empty Classrooms',
    description: 'Classrooms 201-205 have lights running all night even when empty, wasting energy.',
    priority: 'medium', status: 'reported',
    category: { name: 'Energy Waste', color: '#f9a825', icon: 'fa-bolt' },
    location_name: 'Main Building – 2nd Floor', created_at: new Date(Date.now() - 345600000).toISOString(),
    upvotes: 6, reporter: 'Fatima Z.',
  },
  {
    id: 5, title: 'Noise from Construction Near Dorms',
    description: 'Ongoing construction work creating excessive noise during study hours (8AM-6PM).',
    priority: 'medium', status: 'in_progress',
    category: { name: 'Noise Pollution', color: '#6a1b9a', icon: 'fa-volume-up' },
    location_name: 'Dormitories – East Wing', created_at: new Date(Date.now() - 432000000).toISOString(),
    upvotes: 4, reporter: 'Youcef A.',
  },
  {
    id: 6, title: 'Dead Trees in Campus Garden',
    description: 'Several ornamental trees in the main garden area appear to be dead and may pose falling hazards.',
    priority: 'low', status: 'resolved',
    category: { name: 'Biodiversity', color: '#388e3c', icon: 'fa-tree' },
    location_name: 'Garden – Central Area', created_at: new Date(Date.now() - 604800000).toISOString(),
    upvotes: 3, reporter: 'Amira L.',
  },
  {
    id: 7, title: 'Broken Water Fountain at Sports Area',
    description: 'The drinking water fountain near the football field has been broken for a week.',
    priority: 'medium', status: 'reported',
    category: { name: 'Water Issue', color: '#1565c0', icon: 'fa-tint' },
    location_name: 'Sports Area', created_at: new Date(Date.now() - 518400000).toISOString(),
    upvotes: 9, reporter: 'Karim D.',
  },
];

async function loadAlerts() {
  const grid         = document.getElementById('alertsGrid');
  const emptyState   = document.getElementById('alertsEmptyState');
  const searchQuery  = document.getElementById('alertSearch').value.toLowerCase();
  const statusFilter = document.getElementById('alertFilterStatus2').value;
  const sortBy       = document.getElementById('alertSortBy').value;

  let alerts = [];
  try {
    const res = await apiFetch('/alerts');
    if (!res.ok) throw new Error('API error');
    alerts = await res.json();
    if (alerts.alerts) alerts = alerts.alerts;
  } catch {
    alerts = [...DEMO_ALERTS];
  }

  // Filter
  let filtered = alerts.filter(a => {
    if (statusFilter && a.status !== statusFilter) return false;
    if (searchQuery) {
      const match = (a.title || '').toLowerCase().includes(searchQuery)
        || (a.description || '').toLowerCase().includes(searchQuery)
        || (a.category?.name || '').toLowerCase().includes(searchQuery);
      if (!match) return false;
    }
    return true;
  });

  // Sort
  const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };
  if (sortBy === 'priority') {
    filtered.sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 4) - (PRIORITY_ORDER[b.priority] ?? 4));
  } else if (sortBy === 'upvotes') {
    filtered.sort((a, b) => (b.upvotes || 0) - (a.upvotes || 0));
  } else {
    filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }

  // Render
  Array.from(grid.children).forEach(child => {
    if (child.id !== 'alertsEmptyState') child.remove();
  });

  if (filtered.length === 0) {
    if (emptyState) emptyState.classList.remove('hidden');
    return;
  }
  if (emptyState) emptyState.classList.add('hidden');

  filtered.forEach(alert => {
    const card     = document.createElement('div');
    card.className = `alert-card priority-${alert.priority}`;
    card.addEventListener('click', () => {
      if (typeof openAlertDetail === 'function') openAlertDetail(alert.id);
    });

    const catColor = alert.category?.color || '#888';
    const catName  = alert.category?.name  || 'Unknown';
    const desc     = (alert.description || '').substring(0, 120);
    const dateStr  = new Date(alert.created_at).toLocaleDateString();

    card.innerHTML = `
      <div class="alert-card-body">
        <div class="alert-card-header">
          <span class="alert-card-title">${escapeHtml(alert.title)}</span>
          <span class="priority-badge p-${alert.priority}">${alert.priority}</span>
        </div>
        <p class="alert-card-desc">${escapeHtml(desc)}</p>
        <div class="alert-card-footer">
          <span class="status-badge s-${alert.status}">${formatStatus(alert.status)}</span>
          <span class="cat-chip" style="background:${catColor}">${catName}</span>
        </div>
        <div class="card-actions">
          <span class="card-meta"><i class="fas fa-map-pin"></i> ${escapeHtml(alert.location_name || 'Campus')}</span>
          <span class="card-meta"><i class="fas fa-clock"></i> ${dateStr}</span>
          <button class="vote-btn"><i class="fas fa-thumbs-up"></i> ${alert.upvotes || 0}</button>
        </div>
      </div>`;

    grid.appendChild(card);
  });
}