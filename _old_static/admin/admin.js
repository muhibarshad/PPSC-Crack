/**
 * PPSC CRACK — Admin Dashboard
 * ============================================================
 * Renders all admin UI from centralized mock data.
 * Replace imports with API calls when backend is ready.
 * ============================================================
 */

import {
  ADMIN_STATS, ADMIN_NAV, RECENT_USERS, ACTIVITY_LOG,
  REVENUE_CHART, PLAN_DISTRIBUTION, SUBJECT_FREQUENCY,
} from '../assets/js/data/mock-data.js';

import { icon } from '../assets/js/components/icons.js';
import { formatNumber, formatDate, sanitize } from '../assets/js/utils/helpers.js';
import { normalizeChartData } from '../assets/js/utils/helpers.js';

// ──────────────────────────────────────────────
// SIDEBAR NAV
// ──────────────────────────────────────────────
function renderSidebarNav() {
  const nav = document.getElementById('sidebarNav');
  if (!nav) return;

  const mainItems = ADMIN_NAV.filter(n => n.id !== 'settings');
  const settingsItem = ADMIN_NAV.find(n => n.id === 'settings');

  nav.innerHTML = `
    <div class="sidebar-section-label">Main Menu</div>
    ${mainItems.map(item => `
      <div class="nav-item ${item.active ? 'active' : ''}" data-nav="${item.id}">
        <span class="nav-item-icon">
          ${icon(item.icon, { size: 16, color: item.active ? 'var(--clr-primary)' : 'currentColor' })}
        </span>
        <span>${item.label}</span>
      </div>
    `).join('')}

    <div class="sidebar-section-label" style="margin-top:var(--space-4)">System</div>
    ${settingsItem ? `
      <div class="nav-item" data-nav="settings">
        <span class="nav-item-icon">
          ${icon('settings', { size: 16 })}
        </span>
        <span>Settings</span>
      </div>
    ` : ''}
    <a href="../landing/" class="nav-item">
      <span class="nav-item-icon">${icon('arrow-right', { size: 16 })}</span>
      <span>View Landing Page</span>
    </a>
  `;

  // Nav item click — active state
  nav.querySelectorAll('.nav-item[data-nav]').forEach(item => {
    item.addEventListener('click', () => {
      nav.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      document.getElementById('topbarTitle').textContent =
        ADMIN_NAV.find(n => n.id === item.dataset.nav)?.label ?? 'Dashboard';
    });
  });
}

function renderSidebarUser() {
  const el = document.getElementById('sidebarUser');
  if (!el) return;
  el.innerHTML = `
    <div class="avatar avatar-md" style="background:var(--clr-primary-dim);color:var(--clr-primary)">SA</div>
    <div class="sidebar-user-info">
      <div class="sidebar-user-name">Super Admin</div>
      <div class="sidebar-user-role">admin@ppsccrack.pk</div>
    </div>
    ${icon('log-out', { size: 14, color: 'var(--clr-text-muted)' })}
  `;
}

// ──────────────────────────────────────────────
// TOPBAR ICONS
// ──────────────────────────────────────────────
function renderTopbarIcons() {
  const ids = { searchIcon: 'search', bellIcon: 'bell', settingsIcon: 'settings', menuIcon: 'menu' };
  Object.entries(ids).forEach(([id, name]) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = icon(name, { size: 16 });
  });

  // Show mobile toggle on small screens
  const mobileToggle = document.getElementById('mobileSidebarToggle');
  if (window.innerWidth <= 768 && mobileToggle) {
    mobileToggle.style.display = 'flex';
  }

  mobileToggle?.addEventListener('click', toggleMobileSidebar);
  document.getElementById('sidebarOverlay')?.addEventListener('click', closeMobileSidebar);
}

// ──────────────────────────────────────────────
// MOBILE SIDEBAR
// ──────────────────────────────────────────────
function toggleMobileSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}
function closeMobileSidebar() {
  document.getElementById('sidebar').classList.remove('open');
}

// ──────────────────────────────────────────────
// STATS CARDS
// ──────────────────────────────────────────────
function renderStats() {
  const grid = document.getElementById('statsGrid');
  if (!grid) return;

  const colorMap = {
    primary: { wrap: 'primary', color: 'var(--clr-primary)' },
    gold:    { wrap: 'gold',    color: 'var(--clr-gold)' },
    success: { wrap: 'success', color: 'var(--clr-success)' },
    warning: { wrap: 'warning', color: 'var(--clr-warning)' },
  };

  grid.innerHTML = ADMIN_STATS.map((stat, i) => {
    const cm = colorMap[stat.color] || colorMap.primary;
    const rawValue = typeof stat.value === 'number' ? formatNumber(stat.value) : stat.value;
    return `
      <div class="glass stat-card animate-fade-in-up" style="animation-delay:${i * 80}ms">
        <div class="stat-card-header">
          <div class="stat-icon-wrap ${cm.wrap}">
            ${icon(stat.icon, { size: 18, color: cm.color })}
          </div>
          <div class="stat-trend ${stat.trend}">
            ${icon(stat.trend === 'up' ? 'arrow-up' : 'arrow-down', { size: 12 })}
            ${sanitize(stat.change)}
          </div>
        </div>
        <div>
          <div class="stat-value">${rawValue}</div>
          <div class="stat-label">${sanitize(stat.label)}</div>
          <div class="stat-period">${sanitize(stat.period)}</div>
        </div>
      </div>
    `;
  }).join('');
}

// ──────────────────────────────────────────────
// REVENUE CHART (CSS bar chart)
// ──────────────────────────────────────────────
function renderRevenueChart() {
  const chart = document.getElementById('revenueChart');
  if (!chart) return;

  const data = normalizeChartData(REVENUE_CHART, 'revenue');
  const maxRevenue = Math.max(...REVENUE_CHART.map(d => d.revenue));

  chart.innerHTML = data.map(d => {
    const label = `₨${(d.revenue / 1000).toFixed(0)}K`;
    return `
      <div class="chart-bar-wrap">
        <div class="chart-bar" style="height:${d.pct}%">
          <div class="chart-bar-tooltip">${label} · ${d.users} users</div>
        </div>
        <div class="chart-bar-label">${d.day}</div>
      </div>
    `;
  }).join('');

  // Animate bars on load
  requestAnimationFrame(() => {
    chart.querySelectorAll('.chart-bar').forEach(bar => {
      const h = bar.style.height;
      bar.style.height = '0';
      setTimeout(() => { bar.style.height = h; }, 100);
    });
  });

  // Legend
  const legend = document.getElementById('chartLegend');
  if (legend) {
    legend.innerHTML = `
      <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--clr-text-muted)">
        <div style="width:12px;height:4px;border-radius:2px;background:var(--clr-primary)"></div>
        Revenue (₨)
      </div>
      <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--clr-text-muted)">
        Total this week: <strong style="color:var(--clr-text-primary)">₨${(REVENUE_CHART.reduce((s,d)=>s+d.revenue,0)/1000000).toFixed(1)}M</strong>
      </div>
    `;
  }
}

// ──────────────────────────────────────────────
// PLAN DISTRIBUTION
// ──────────────────────────────────────────────
function renderPlanDistribution() {
  const container = document.getElementById('planDist');
  if (!container) return;

  container.innerHTML = PLAN_DISTRIBUTION.map(p => `
    <div class="plan-dist-item">
      <div class="plan-dist-header">
        <div class="plan-dist-name">
          <div class="plan-dist-dot" style="background:${p.color}"></div>
          ${sanitize(p.plan)}
        </div>
        <div style="display:flex;align-items:center;gap:var(--space-4)">
          <div class="plan-dist-count">${formatNumber(p.users)} users</div>
          <div style="font-size:var(--text-xs);font-weight:600;color:var(--clr-text-secondary)">${p.pct}%</div>
        </div>
      </div>
      <div class="progress-bar">
        <div class="progress-bar-fill" style="width:0%;background:${p.color}" data-target="${p.pct}"></div>
      </div>
    </div>
  `).join('');

  // Animate progress bars
  requestAnimationFrame(() => {
    container.querySelectorAll('.progress-bar-fill').forEach(bar => {
      setTimeout(() => { bar.style.width = bar.dataset.target + '%'; }, 200);
    });
  });
}

// ──────────────────────────────────────────────
// QUICK ACTIONS
// ──────────────────────────────────────────────
const QUICK_ACTIONS = [
  { icon: 'upload',    label: 'Upload Paper',   color: 'var(--clr-primary)' },
  { icon: 'user-plus', label: 'Add User',        color: 'var(--clr-success)' },
  { icon: 'cpu',       label: 'Run Prediction',  color: 'var(--clr-gold)' },
  { icon: 'newspaper', label: 'Update Affairs',  color: 'var(--clr-warning)' },
  { icon: 'file-text', label: 'New Story Doc',   color: 'var(--clr-primary)' },
  { icon: 'settings',  label: 'Settings',        color: 'var(--clr-text-muted)' },
];

function renderQuickActions() {
  const container = document.getElementById('quickActions');
  if (!container) return;

  container.innerHTML = QUICK_ACTIONS.map(a => `
    <button class="quick-action-btn" title="${a.label}">
      ${icon(a.icon, { size: 18, color: a.color })}
      <span>${a.label}</span>
    </button>
  `).join('');
}

// ──────────────────────────────────────────────
// USERS TABLE
// ──────────────────────────────────────────────
function renderUsersTable() {
  const table = document.getElementById('usersTable');
  if (!table) return;

  const planBadge = (plan) => {
    const map = { free: 'default', pro: 'badge-primary', elite: 'badge-gold' };
    const cls = map[plan] ?? '';
    return `<span class="badge ${cls}" style="${!cls ? 'color:var(--clr-text-muted);background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08)' : ''}">${plan}</span>`;
  };

  const statusBadge = (status) => {
    const map = { active: 'badge-success', suspended: 'badge-danger', pending: 'badge-warning' };
    return `<span class="badge ${map[status] ?? ''}">${status}</span>`;
  };

  table.innerHTML = `
    <thead>
      <tr>
        <th>User</th>
        <th>Plan</th>
        <th>Status</th>
        <th>Joined</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      ${RECENT_USERS.map(user => `
        <tr>
          <td>
            <div class="user-cell">
              <div class="avatar avatar-sm" style="background:${user.color}22;color:${user.color};border:1px solid ${user.color}44">${user.initials}</div>
              <div>
                <div style="font-weight:var(--weight-medium)">${sanitize(user.name)}</div>
                <div class="user-email">${sanitize(user.email)}</div>
              </div>
            </div>
          </td>
          <td>${planBadge(user.plan)}</td>
          <td>${statusBadge(user.status)}</td>
          <td style="color:var(--clr-text-muted)">${formatDate(user.joined)}</td>
          <td>
            <div class="table-actions">
              <button class="btn btn-icon btn-ghost btn-sm" title="View">
                ${icon('eye', { size: 13 })}
              </button>
              <button class="btn btn-icon btn-ghost btn-sm" title="Edit">
                ${icon('edit', { size: 13 })}
              </button>
              <button class="btn btn-icon btn-ghost btn-sm" title="Delete" style="color:var(--clr-danger)">
                ${icon('trash-2', { size: 13, color: 'var(--clr-danger)' })}
              </button>
            </div>
          </td>
        </tr>
      `).join('')}
    </tbody>
  `;
}

// ──────────────────────────────────────────────
// ACTIVITY FEED
// ──────────────────────────────────────────────
function renderActivityFeed() {
  const feed = document.getElementById('activityFeed');
  if (!feed) return;

  const colorMap = {
    success: 'var(--clr-success)',
    primary: 'var(--clr-primary)',
    gold:    'var(--clr-gold)',
    warning: 'var(--clr-warning)',
    danger:  'var(--clr-danger)',
  };

  feed.innerHTML = ACTIVITY_LOG.map(a => `
    <div class="activity-item animate-fade-in">
      <div class="activity-icon ${a.color}">
        ${icon(a.icon, { size: 14, color: colorMap[a.color] ?? 'currentColor' })}
      </div>
      <div class="activity-content">
        <div class="activity-message">${sanitize(a.message)}</div>
        <div class="activity-time">${sanitize(a.time)}</div>
      </div>
    </div>
  `).join('');
}

// ──────────────────────────────────────────────
// SUBJECT FREQUENCY
// ──────────────────────────────────────────────
function renderSubjectFrequency() {
  const container = document.getElementById('subjectList');
  if (!container) return;

  const total = SUBJECT_FREQUENCY.reduce((s, x) => s + x.frequency, 0);

  container.innerHTML = SUBJECT_FREQUENCY.map(s => {
    const pct = Math.round((s.frequency / total) * 100);
    const changeClass = s.change.startsWith('+') ? 'up' : s.change.startsWith('-') ? 'down' : 'neutral';
    return `
      <div class="subject-item">
        <div class="subject-header">
          <div style="display:flex;align-items:center;gap:var(--space-3)">
            <div class="subject-name">${sanitize(s.subject)}</div>
            <div class="subject-change ${changeClass}">${sanitize(s.change)}</div>
          </div>
          <div class="subject-pct">${s.frequency}% · ${pct}% share</div>
        </div>
        <div class="progress-bar">
          <div class="progress-bar-fill" style="width:0%" data-target="${s.frequency}"></div>
        </div>
      </div>
    `;
  }).join('');

  requestAnimationFrame(() => {
    container.querySelectorAll('.progress-bar-fill').forEach(bar => {
      setTimeout(() => { bar.style.width = bar.dataset.target + '%'; }, 300);
    });
  });
}

// ──────────────────────────────────────────────
// UPDATE TOPBAR DATE
// ──────────────────────────────────────────────
function updateTopbarSubtitle() {
  const el = document.getElementById('topbarSubtitle');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toLocaleDateString('en-PK', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}

// ──────────────────────────────────────────────
// WINDOW RESIZE — toggle mobile button
// ──────────────────────────────────────────────
function handleResize() {
  const mobileToggle = document.getElementById('mobileSidebarToggle');
  if (!mobileToggle) return;
  mobileToggle.style.display = window.innerWidth <= 768 ? 'flex' : 'none';
  if (window.innerWidth > 768) closeMobileSidebar();
}

// ──────────────────────────────────────────────
// INIT
// ──────────────────────────────────────────────
function init() {
  renderSidebarNav();
  renderSidebarUser();
  renderTopbarIcons();
  updateTopbarSubtitle();
  renderStats();
  renderRevenueChart();
  renderPlanDistribution();
  renderQuickActions();
  renderUsersTable();
  renderActivityFeed();
  renderSubjectFrequency();

  window.addEventListener('resize', handleResize, { passive: true });
  handleResize();
}

document.addEventListener('DOMContentLoaded', init);
