/**
 * PPSC CRACK — Utility Helpers
 * ============================================================
 * Pure functions. No side effects. No DOM access here.
 * ============================================================
 */

/**
 * Format a number with compact notation.
 * e.g. 52840 → "52.8K"
 */
export function formatNumber(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000)     return (n / 1_000).toFixed(1)     + 'K';
  return String(n);
}

/**
 * Format a currency value.
 * e.g. 499 → "Rs 499"
 */
export function formatCurrency(amount, currency = 'Rs') {
  if (typeof amount === 'string') return amount; // Already formatted
  return `${currency} ${amount.toLocaleString()}`;
}

/**
 * Clamp a number between min and max.
 */
export function clamp(val, min, max) {
  return Math.min(Math.max(val, min), max);
}

/**
 * Get initials from a full name.
 */
export function getInitials(name) {
  return name
    .split(' ')
    .slice(0, 2)
    .map(w => w[0].toUpperCase())
    .join('');
}

/**
 * Debounce a function.
 */
export function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Normalize chart data to 0–100 scale.
 */
export function normalizeChartData(data, key) {
  const max = Math.max(...data.map(d => d[key]));
  return data.map(d => ({ ...d, pct: Math.round((d[key] / max) * 100) }));
}

/**
 * Determine badge variant from plan string.
 */
export function planBadgeVariant(plan) {
  const map = { free: 'default', pro: 'primary', elite: 'gold' };
  return map[plan] ?? 'default';
}

/**
 * Determine badge variant from status string.
 */
export function statusBadgeVariant(status) {
  const map = { active: 'success', suspended: 'danger', pending: 'warning' };
  return map[status] ?? 'default';
}

/**
 * Sanitize a string for safe innerHTML (basic).
 */
export function sanitize(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Format ISO date to readable string.
 */
export function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-PK', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}
