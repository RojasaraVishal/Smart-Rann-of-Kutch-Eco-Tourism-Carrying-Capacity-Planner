/**
 * Smart Rann of Kutch Eco-Tourism Platform — API Client
 * Central API layer for all frontend ↔ backend communication.
 *
 * Usage: API.method() — all methods return Promises.
 * Configure production URL via: <script>window.API_BASE = 'https://your-backend.com';</script>
 */
const API = (() => {
  const BASE = window.API_BASE || 'http://localhost:8000';

  // ── Token / Session ─────────────────────────────────────────────────────
  function setToken(t) {
    if (t) localStorage.setItem('kutch_token', t);
    else localStorage.removeItem('kutch_token');
  }
  function getToken() { return localStorage.getItem('kutch_token'); }
  function getUser() {
    try { return JSON.parse(localStorage.getItem('kutch_user') || 'null'); } catch { return null; }
  }
  function setUser(u) {
    if (u) localStorage.setItem('kutch_user', JSON.stringify(u));
    else localStorage.removeItem('kutch_user');
  }
  function logout() {
    setToken(null); setUser(null);
    window.location.href = 'login.html';
  }
  function isLoggedIn() { return !!getToken() && !!getUser(); }
  function hasRole(...roles) {
    const u = getUser();
    return u && roles.includes(u.role);
  }

  // ── Core Request ─────────────────────────────────────────────────────────
  async function req(method, path, body = null, auth = false, timeout = 15000) {
    const headers = { 'Content-Type': 'application/json' };
    if (auth && getToken()) headers['Authorization'] = `Bearer ${getToken()}`;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);

    try {
      const opts = { method, headers, signal: controller.signal };
      if (body) opts.body = JSON.stringify(body);
      const resp = await fetch(`${BASE}${path}`, opts);
      clearTimeout(timer);
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        // Auto-logout on 401
        if (resp.status === 401) { setToken(null); setUser(null); }
        throw new Error(data.detail || `Server error (${resp.status})`);
      }
      return data;
    } catch (e) {
      clearTimeout(timer);
      if (e.name === 'AbortError') throw new Error('Request timed out. Please try again.');
      if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError')) {
        throw new Error('BACKEND_OFFLINE');
      }
      throw e;
    }
  }

  // Form-encoded login (required for OAuth2PasswordRequestForm)
  async function loginForm(email, password) {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 15000);
    const resp = await fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
      signal: controller.signal,
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.detail || 'Login failed');
    return data;
  }

  // ── Auth ─────────────────────────────────────────────────────────────────
  const register = (d) => req('POST', '/auth/register', d);
  const login = (email, pass) => loginForm(email, pass);
  const getMe = () => req('GET', '/auth/me', null, true);

  // ── Destinations ─────────────────────────────────────────────────────────
  const getDestinations = (params = '') => req('GET', `/destinations/${params}`);
  const getDestination = (id) => req('GET', `/destinations/${id}`);

  // ── Tourist Load ─────────────────────────────────────────────────────────
  const getForecastAll = () => req('GET', '/tourist-load/forecast');
  const getForecast = (id, days = 1) => req('GET', `/tourist-load/forecast/${id}?days=${days}`);
  const getHistory = (id, days = 30) => req('GET', `/tourist-load/history/${id}?days=${days}`);
  const trainModel = () => req('POST', '/tourist-load/train', null, true);

  // ── Carrying Capacity ─────────────────────────────────────────────────────
  const getAllCC = () => req('GET', '/carrying-capacity/');
  const getCC = (id) => req('GET', `/carrying-capacity/${id}`);
  const getAlternatives = (id, max = 3) => req('GET', `/carrying-capacity/${id}/alternatives?max_results=${max}`);

  // ── Itinerary ─────────────────────────────────────────────────────────────
  const generateItinerary = (d) => req('POST', '/itinerary/generate/guest', d);
  const generateItineraryAuth = (d) => req('POST', '/itinerary/generate', d, true);

  // ── Artisans ─────────────────────────────────────────────────────────────
  const getArtisans = (category = '') => req('GET', `/artisans/${category ? `?category=${encodeURIComponent(category)}` : ''}`);
  const getArtisan = (id) => req('GET', `/artisans/${id}`);
  const getExperiences = (params = '') => req('GET', `/artisans/experiences${params}`);
  const matchCommunity = (d) => req('POST', '/artisans/match', d);

  // ── AI ────────────────────────────────────────────────────────────────────
  const chat = (query, language = 'en', session_id = null) =>
    req('POST', '/ai/chat', { query, language, session_id }, false, 60000);
  const chatAuth = (query, language = 'en', session_id = null) =>
    req('POST', '/ai/chat/auth', { query, language, session_id }, true, 60000);

  // ── Dashboard ─────────────────────────────────────────────────────────────
  const getDashboard = () => req('GET', '/dashboard/tourism-impact', null, true);
  const getDashboardPublic = () => req('GET', '/dashboard/tourism-impact/public');
  const getDashboardSummary = () => req('GET', '/dashboard/tourism-impact/ai-summary', null, true);

  // ── Alerts ────────────────────────────────────────────────────────────────
  const getAlerts = (activeOnly = true) => req('GET', `/alerts/?active_only=${activeOnly}`);
  const createAlert = (d) => req('POST', '/alerts/', d, true);
  const deactivateAlert = (id) => req('PATCH', `/alerts/${id}/deactivate`, null, true);

  // ── Health ────────────────────────────────────────────────────────────────
  const health = () => req('GET', '/health');

  return {
    BASE,
    // Session
    setToken, getToken, getUser, setUser, logout, isLoggedIn, hasRole,
    // Auth
    register, login, getMe,
    // Destinations
    getDestinations, getDestination,
    // Tourist Load
    getForecastAll, getForecast, getHistory, trainModel,
    // Carrying Capacity
    getAllCC, getCC, getAlternatives,
    // Itinerary
    generateItinerary, generateItineraryAuth,
    // Artisans
    getArtisans, getArtisan, getExperiences, matchCommunity,
    // AI
    chat, chatAuth,
    // Dashboard
    getDashboard, getDashboardPublic, getDashboardSummary,
    // Alerts
    getAlerts, createAlert, deactivateAlert,
    // Health
    health,
  };
})();

// ═══════════════════════════════════════════════════════════════════════════
// UI UTILITIES — shared across all pages
// ═══════════════════════════════════════════════════════════════════════════

/** Pressure level → dark theme colors */
const PRESSURE_COLORS = {
  low:      { dot: '#42D392', label: 'Low',      cssClass: 'badge-low' },
  moderate: { dot: '#F5B942', label: 'Moderate', cssClass: 'badge-moderate' },
  high:     { dot: '#F5B942', label: 'High',     cssClass: 'badge-high' },
  critical: { dot: '#FF5C5C', label: 'Critical', cssClass: 'badge-critical' },
};

/** Render a pressure badge using CSS class-based dark-theme badges */
function pressureBadge(level) {
  const p = PRESSURE_COLORS[level] || PRESSURE_COLORS.low;
  const icons = { low: '▲', moderate: '◆', high: '◆', critical: '▼' };
  const icon = icons[level] || '●';
  return `<span class="badge ${p.cssClass}">${icon} ${p.label}</span>`;
}

/** Render a data-type badge */
function dataLabelBadge(label) {
  const map = {
    DEMO:      { cls: 'badge-demo',      icon: '○' },
    PREDICTED: { cls: 'badge-predicted', icon: '◈' },
    AI:        { cls: 'badge-ai',        icon: '◈' },
    VERIFIED:  { cls: 'badge-verified',  icon: '●' },
  };
  const s = map[label] || map.DEMO;
  return `<span class="badge ${s.cls}">${s.icon} ${label}</span>`;
}

/** Render a capacity utilization bar */
function scoreMeter(score) {
  const pct = Math.min(100, Math.max(0, score || 0));
  let fill;
  if (pct <= 50)       fill = '#42D392';
  else if (pct <= 70)  fill = '#F5B942';
  else if (pct <= 85)  fill = '#F5B942';
  else                 fill = '#FF5C5C';
  return `<div class="score-meter"><div class="score-meter-fill" style="width:${pct}%;background:${fill}"></div></div>`;
}

/** Show a toast notification — dark themed */
function showToast(msg, type = 'info') {
  document.querySelectorAll('.kutch-toast').forEach(e => e.remove());
  const styles = {
    error:   'background:#1A0D0D;border:1px solid rgba(255,92,92,0.4);color:#FF5C5C',
    success: 'background:#0D1A12;border:1px solid rgba(66,211,146,0.4);color:#42D392',
    warning: 'background:#1A160D;border:1px solid rgba(245,185,66,0.4);color:#F5B942',
    info:    'background:#1A1F25;border:1px solid #30363D;color:#A7ADB5',
  };
  const el = document.createElement('div');
  el.className = 'kutch-toast';
  el.style.cssText = [
    'position:fixed', 'bottom:24px', 'right:24px',
    styles[type] || styles.info,
    'padding:12px 20px', 'border-radius:10px', 'z-index:99999',
    'font-size:0.84rem', 'max-width:360px', 'line-height:1.5',
    'box-shadow:0 4px 20px rgba(0,0,0,0.6)', 'font-family:var(--font)',
    'backdrop-filter:blur(8px)',
  ].join(';');
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0'; el.style.transition = 'opacity 0.3s';
    setTimeout(() => el.remove(), 300);
  }, 3500);
}

/** Show structured error state in a container */
function showError(containerId, message, showDemo = false) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const isOffline = message === 'BACKEND_OFFLINE';
  el.innerHTML = `
    <div style="text-align:center;padding:48px 24px;background:var(--card);border-radius:var(--radius-lg);border:1px solid var(--border)">
      <div style="font-size:2rem;margin-bottom:14px;opacity:0.6">${isOffline ? '⚡' : '○'}</div>
      <div style="font-weight:700;font-size:0.95rem;margin-bottom:8px;color:var(--text-primary)">${isOffline ? 'Backend Offline' : 'Data Unavailable'}</div>
      <div style="color:var(--text-muted);font-size:0.83rem;margin-bottom:${showDemo ? '16px' : '0'};line-height:1.6">
        ${isOffline
          ? 'Start the FastAPI server:<br><code>cd backend &amp;&amp; uvicorn main:app --reload --port 8000</code>'
          : ((message || 'An unexpected error occurred. Please try again.').replace(/</g,'&lt;').replace(/>/g,'&gt;'))}
      </div>
      ${showDemo ? '<span class="badge badge-demo" style="margin-top:12px">DEMO DATA</span>' : ''}
    </div>`;
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatNum(n) {
  if (n == null) return '—';
  return Number(n).toLocaleString('en-IN');
}

function pctColor(pct) {
  if (pct <= 50) return '#42D392';
  if (pct <= 70) return '#F5B942';
  if (pct <= 85) return '#F5B942';
  return '#FF5C5C';
}

function pctLabel(pct) {
  if (pct <= 50) return 'LOW';
  if (pct <= 70) return 'MODERATE';
  if (pct <= 85) return 'HIGH';
  if (pct <= 100) return 'VERY HIGH';
  return 'CRITICAL';
}

/** Redirect to login if not authenticated. Call on protected pages. */
function requireAuth(redirectBack = true) {
  if (!API.isLoggedIn()) {
    const dest = redirectBack ? `login.html?next=${encodeURIComponent(location.pathname + location.search)}` : 'login.html';
    window.location.href = dest;
    return false;
  }
  return true;
}

/** Redirect to login if not the required role. */
function requireRole(...roles) {
  if (!API.isLoggedIn()) { requireAuth(); return false; }
  if (!API.hasRole(...roles)) {
    showToast('You do not have permission to view this page.', 'error');
    setTimeout(() => window.location.href = 'dashboard.html', 1500);
    return false;
  }
  return true;
}

/** Update nav auth state on every page load. */
function updateNavAuth() {
  const user = API.getUser();
  const logoutBtns = document.querySelectorAll('#nav-logout, .nav-logout-btn');
  const loginBtns = document.querySelectorAll('#nav-login, .nav-login-btn');
  const userNames = document.querySelectorAll('#nav-user-name, .nav-user-name');
  const adminLinks = document.querySelectorAll('.nav-admin-link');

  if (user) {
    loginBtns.forEach(el => el.style.display = 'none');
    logoutBtns.forEach(el => { el.style.display = 'inline-flex'; el.addEventListener('click', API.logout); });
    userNames.forEach(el => el.textContent = user.name.split(' ')[0]);
    if (user.role === 'authority' || user.role === 'admin') {
      adminLinks.forEach(el => el.style.display = 'inline-flex');
    }
  } else {
    loginBtns.forEach(el => el.style.display = 'inline-flex');
    logoutBtns.forEach(el => el.style.display = 'none');
    adminLinks.forEach(el => el.style.display = 'none');
  }
}

document.addEventListener('DOMContentLoaded', updateNavAuth);
