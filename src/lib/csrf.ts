/**
 * CSRF Token Utility
 * ====================
 * Reads the CSRF token from the cookie set by the backend
 * and provides it for state-changing requests.
 */

/**
 * Read a cookie by name.
 */
function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Get the current CSRF token from the cookie.
 */
export function getCSRFToken(): string | null {
  return getCookie('csrf_token');
}

/**
 * Enhanced fetch that automatically includes CSRF token
 * on state-changing requests (POST, PUT, PATCH, DELETE).
 */
export async function csrfFetch(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const method = (options.method || 'GET').toUpperCase();
  const stateChanging = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);

  const headers = new Headers(options.headers || {});

  if (stateChanging) {
    const token = getCSRFToken();
    if (token) {
      headers.set('X-CSRF-Token', token);
    }
  }

  return fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Always send cookies
  });
}
