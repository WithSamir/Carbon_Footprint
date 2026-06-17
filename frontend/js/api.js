/* ============================================================
   api.js — Fetch wrapper for CarbonTrace backend
   ============================================================ */

const API_BASE = '';

function getToken() {
  return localStorage.getItem('ct_token');
}

function setToken(token) {
  localStorage.setItem('ct_token', token);
}

function clearAuth() {
  localStorage.removeItem('ct_token');
  localStorage.removeItem('ct_user');
}

function getUser() {
  try {
    const raw = localStorage.getItem('ct_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function setUser(user) {
  localStorage.setItem('ct_user', JSON.stringify(user));
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }

  return data;
}

// ── Auth ──────────────────────────────────────────────────────
const api = {
  auth: {
    async register(email, password, displayName, country) {
      const data = await apiFetch('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password, display_name: displayName, country }),
      });
      setToken(data.access_token);
      setUser(data.user);
      return data;
    },

    async login(email, password) {
      const data = await apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      setToken(data.access_token);
      setUser(data.user);
      return data;
    },

    logout() {
      clearAuth();
      window.location.href = '/';
    },

    isLoggedIn() {
      return !!getToken();
    },

    getUser,
  },

  // ── Carbon ──────────────────────────────────────────────────
  carbon: {
    async calculate(inputs) {
      return apiFetch('/api/carbon/calculate', {
        method: 'POST',
        body: JSON.stringify(inputs),
      });
    },

    async submit(inputs) {
      return apiFetch('/api/carbon/submit', {
        method: 'POST',
        body: JSON.stringify(inputs),
      });
    },

    async history() {
      return apiFetch('/api/carbon/history');
    },

    async summary() {
      return apiFetch('/api/carbon/summary');
    },
  },

  // ── Insights ─────────────────────────────────────────────────
  insights: {
    async recommendations() {
      return apiFetch('/api/insights/recommendations');
    },

    async commitAction(actionId) {
      return apiFetch('/api/insights/actions/commit', {
        method: 'POST',
        body: JSON.stringify({ action_id: actionId }),
      });
    },

    async completeAction(actionId) {
      return apiFetch('/api/insights/actions/complete', {
        method: 'POST',
        body: JSON.stringify({ action_id: actionId }),
      });
    },

    async myActions() {
      return apiFetch('/api/insights/actions/my');
    },
  },
};

// ── Session persistence helpers ───────────────────────────────
function savePendingResult(result) {
  sessionStorage.setItem('ct_pending_result', JSON.stringify(result));
}

function getPendingResult() {
  try {
    const raw = sessionStorage.getItem('ct_pending_result');
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function clearPendingResult() {
  sessionStorage.removeItem('ct_pending_result');
}

function savePendingInputs(inputs) {
  sessionStorage.setItem('ct_pending_inputs', JSON.stringify(inputs));
}

function getPendingInputs() {
  try {
    const raw = sessionStorage.getItem('ct_pending_inputs');
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}
