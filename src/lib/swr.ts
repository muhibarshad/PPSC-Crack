/**
 * SWR Configuration & Custom Hooks
 * ==================================
 * Centralized data-fetching with SWR.
 * 5-minute stale time for static data.
 */

import useSWR, { SWRConfiguration } from 'swr';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

/** Global fetcher — includes credentials for cookie auth */
export async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url.startsWith('http') ? url : `${API_BASE}${url}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const error = new Error('API request failed');
    (error as any).status = res.status;
    (error as any).info = await res.json().catch(() => null);
    throw error;
  }
  return res.json();
}

/** Default SWR config — 5 min stale time for static data */
export const swrStaticConfig: SWRConfiguration = {
  dedupingInterval: 5 * 60 * 1000, // 5 minutes
  revalidateOnFocus: false,
  revalidateIfStale: false,
  shouldRetryOnError: true,
  errorRetryCount: 3,
};

/** SWR config for dynamic data — 30s refresh */
export const swrDynamicConfig: SWRConfiguration = {
  dedupingInterval: 30_000,
  revalidateOnFocus: true,
  shouldRetryOnError: true,
  errorRetryCount: 2,
};

// ── Typed hooks for common endpoints ──

export function useDashboardHome() {
  return useSWR('/dashboard/home', fetcher, swrDynamicConfig);
}

export function useStudentAnalytics() {
  return useSWR('/student/analytics', fetcher, swrStaticConfig);
}

export function useJobTypes() {
  return useSWR('/job-types/', fetcher, swrStaticConfig);
}

export function useLearningPath(jobTypeId: string | null) {
  return useSWR(
    jobTypeId ? `/dashboard/learning-path/${jobTypeId}` : null,
    fetcher,
    swrStaticConfig,
  );
}

export function useAdminDashboard() {
  return useSWR('/admin/dashboard', fetcher, swrDynamicConfig);
}

export function useCurrentAffairs(page: number, category?: string) {
  const params = new URLSearchParams({ page: String(page) });
  if (category) params.set('category', category);
  return useSWR(`/student/current-affairs?${params}`, fetcher, swrDynamicConfig);
}

export function usePredictions() {
  return useSWR('/student/predictions/latest', fetcher, swrStaticConfig);
}
