/* ============================================================
   ui.js — Shared UI utilities: toasts, modals, nav, loaders
   ============================================================ */

// ── Toast System ─────────────────────────────────────────────
function showToast(title, message, type = 'success', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '✅', error: '❌', info: 'ℹ️', badge: '🏅' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || '🌿'}</span>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${message ? `<div class="toast-msg">${message}</div>` : ''}
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Badge Unlock Toast ────────────────────────────────────────
function showBadgeUnlock(badge) {
  showToast(`${badge.icon} Badge Unlocked!`, `<strong>${badge.name}</strong> — ${badge.description}`, 'badge', 5000);
}

// ── Auth Modal ────────────────────────────────────────────────
function openAuthModal(mode = 'login', onSuccess = null) {
  let overlay = document.getElementById('auth-modal-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'auth-modal-overlay';
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="auth-modal-title">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:28px;">
          <div style="width:40px;height:40px;background:linear-gradient(135deg,#22c55e,#14b8a6);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;">🌿</div>
          <div>
            <h3 id="auth-modal-title" style="margin:0;font-size:1.125rem;">Join CarbonTrace</h3>
            <p style="margin:0;font-size:0.8125rem;">Save your results & track progress</p>
          </div>
        </div>
        <div id="auth-tabs" style="display:flex;gap:0;background:var(--bg-base);border-radius:var(--radius-md);padding:4px;margin-bottom:24px;">
          <button id="tab-login" onclick="switchAuthTab('login')" class="btn w-full" style="border-radius:var(--radius-sm);flex:1;padding:9px;">Sign In</button>
          <button id="tab-register" onclick="switchAuthTab('register')" class="btn w-full" style="border-radius:var(--radius-sm);flex:1;padding:9px;">Create Account</button>
        </div>
        <form id="auth-form" onsubmit="handleAuthSubmit(event)">
          <div class="form-group mb-4" id="field-name" style="display:none;">
            <label class="form-label" for="auth-name">Your Name</label>
            <input id="auth-name" class="form-input" type="text" placeholder="Alex Johnson" autocomplete="name">
          </div>
          <div class="form-group mb-4">
            <label class="form-label" for="auth-email">Email Address</label>
            <input id="auth-email" class="form-input" type="email" placeholder="you@example.com" required autocomplete="email">
          </div>
          <div class="form-group mb-6">
            <label class="form-label" for="auth-password">Password</label>
            <input id="auth-password" class="form-input" type="password" placeholder="••••••••" required autocomplete="current-password" minlength="6">
          </div>
          <div id="auth-error" class="hidden" style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#f87171;padding:12px 16px;border-radius:var(--radius-md);font-size:0.875rem;margin-bottom:16px;"></div>
          <button id="auth-submit-btn" type="submit" class="btn btn-primary w-full btn-lg">Sign In</button>
        </form>
        <button onclick="closeAuthModal()" style="position:absolute;top:16px;right:16px;background:none;border:none;color:var(--text-muted);font-size:1.25rem;cursor:pointer;padding:4px;" aria-label="Close">✕</button>
      </div>
    `;
    document.body.appendChild(overlay);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeAuthModal(); });
  }

  window._authSuccessCallback = onSuccess;
  switchAuthTab(mode);
  requestAnimationFrame(() => overlay.classList.add('open'));
}

function closeAuthModal() {
  const overlay = document.getElementById('auth-modal-overlay');
  if (overlay) {
    overlay.classList.remove('open');
  }
}

function switchAuthTab(mode) {
  window._authMode = mode;
  const loginBtn = document.getElementById('tab-login');
  const registerBtn = document.getElementById('tab-register');
  const fieldName = document.getElementById('field-name');
  const submitBtn = document.getElementById('auth-submit-btn');
  const pwdInput = document.getElementById('auth-password');
  const errDiv = document.getElementById('auth-error');

  if (errDiv) errDiv.classList.add('hidden');

  if (mode === 'login') {
    loginBtn.style.background = 'var(--bg-card)';
    loginBtn.style.color = 'var(--text-primary)';
    registerBtn.style.background = 'transparent';
    registerBtn.style.color = 'var(--text-secondary)';
    if (fieldName) fieldName.style.display = 'none';
    if (submitBtn) submitBtn.textContent = 'Sign In';
    if (pwdInput) pwdInput.setAttribute('autocomplete', 'current-password');
  } else {
    registerBtn.style.background = 'var(--bg-card)';
    registerBtn.style.color = 'var(--text-primary)';
    loginBtn.style.background = 'transparent';
    loginBtn.style.color = 'var(--text-secondary)';
    if (fieldName) fieldName.style.display = 'flex';
    if (submitBtn) submitBtn.textContent = 'Create Account';
    if (pwdInput) pwdInput.setAttribute('autocomplete', 'new-password');
  }
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const mode = window._authMode || 'login';
  const email = document.getElementById('auth-email').value;
  const password = document.getElementById('auth-password').value;
  const name = document.getElementById('auth-name')?.value || '';
  const submitBtn = document.getElementById('auth-submit-btn');
  const errDiv = document.getElementById('auth-error');

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<div class="spinner" style="width:20px;height:20px;border-width:2px;"></div>';
  errDiv.classList.add('hidden');

  try {
    if (mode === 'login') {
      await api.auth.login(email, password);
    } else {
      await api.auth.register(email, password, name, 'GBR');
    }
    closeAuthModal();
    showToast('Welcome!', 'You\'re now signed in to CarbonTrace 🌿', 'success');
    if (window._authSuccessCallback) window._authSuccessCallback();
    else window.location.href = '/dashboard.html';
  } catch (err) {
    errDiv.textContent = err.message;
    errDiv.classList.remove('hidden');
    submitBtn.disabled = false;
    submitBtn.textContent = mode === 'login' ? 'Sign In' : 'Create Account';
  }
}

// ── Nav render ────────────────────────────────────────────────
function renderNav(activePage = '') {
  const isLoggedIn = api.auth.isLoggedIn();
  const user = api.auth.getUser();
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';

  const navLinks = isLoggedIn
    ? [
        { href: '/dashboard.html', label: 'Dashboard', id: 'dashboard' },
        { href: '/insights.html', label: 'My Actions', id: 'insights' },
        { href: '/calculator.html', label: 'Log Entry', id: 'calculator' },
      ]
    : [];

  const navEl = document.getElementById('main-nav');
  if (!navEl) return;

  navEl.innerHTML = `
    <div class="nav-inner">
      <a href="/" class="nav-logo" id="nav-logo">
        <div class="nav-logo-icon">🌿</div>
        CarbonTrace
      </a>
      ${navLinks.length ? `
        <ul class="nav-links">
          ${navLinks.map(l => `
            <li>
              <a href="${l.href}" class="nav-link ${currentPage.includes(l.id) ? 'active' : ''}" id="nav-${l.id}">
                ${l.label}
              </a>
            </li>
          `).join('')}
        </ul>
      ` : ''}
      <div style="display:flex;align-items:center;gap:10px;">
        ${isLoggedIn
          ? `<span style="font-size:0.875rem;color:var(--text-muted);">
               Hi, <strong style="color:var(--text-primary);">${(user?.display_name || 'there').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;')}</strong>
             </span>
             <button onclick="api.auth.logout()" class="btn btn-ghost btn-sm" id="nav-logout">Sign Out</button>`
          : `<button onclick="openAuthModal('login')" class="btn btn-ghost btn-sm" id="nav-signin">Sign In</button>
             <button onclick="openAuthModal('register')" class="btn btn-primary btn-sm" id="nav-signup">Get Started</button>`
        }
      </div>
    </div>
  `;
}

// ── Number animation ──────────────────────────────────────────
function animateNumber(el, from, to, duration = 1200, decimals = 1) {
  const start = performance.now();
  const update = (time) => {
    const elapsed = time - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current = from + (to - from) * eased;
    el.textContent = current.toFixed(decimals);
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

// ── Effort badge ─────────────────────────────────────────────
function effortBadge(score) {
  const map = {
    1: { label: 'Easy', cls: 'badge-green' },
    2: { label: 'Low', cls: 'badge-teal' },
    3: { label: 'Medium', cls: 'badge-orange' },
    4: { label: 'Hard', cls: 'badge-red' },
    5: { label: 'Very Hard', cls: 'badge-red' },
  };
  const m = map[score] || map[3];
  return `<span class="badge ${m.cls}">${m.label} effort</span>`;
}

// ── Category colors ───────────────────────────────────────────
const CATEGORY_COLORS = {
  transport: '#22c55e',
  diet: '#14b8a6',
  home_energy_kg: '#3b82f6',
  shopping: '#a855f7',
  energy: '#3b82f6',
};
