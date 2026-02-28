/**
 * Admin Dashboard — /admin
 * =========================
 * Full dashboard home screen with stat cards, papers timeline,
 * prediction health panel, and recent activity feed.
 * Protected route: requires role='admin'.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/admin/AdminLayout';
import { useAuthStore } from '@/store/auth-store';
import {
  AdminStatCards,
  PapersTimeline,
  PredictionHealthPanel,
  RecentActivityFeed,
} from '@/components/admin/dashboard';
import type { AdminDashboardData } from '@/components/admin/dashboard';

/* ── API helper ────────────────────────────────── */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function apiFetch<T = unknown>(
  path: string,
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { headers, credentials: 'include' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Skeleton Loaders ──────────────────────────── */

function StatCardSkeleton() {
  return (
    <div className="glass p-5 animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="w-11 h-11 rounded-xl bg-white/[0.06]" />
        <div className="w-16 h-8 rounded-lg bg-white/[0.06]" />
      </div>
      <div className="w-24 h-3 rounded bg-white/[0.06]" />
    </div>
  );
}

function TimelineSkeleton() {
  return (
    <div className="glass p-5 animate-pulse">
      <div className="w-32 h-4 rounded bg-white/[0.06] mb-4" />
      <div className="w-full h-[220px] rounded-xl bg-white/[0.03]" />
    </div>
  );
}

function HealthSkeleton() {
  return (
    <div className="glass p-5 animate-pulse h-full">
      <div className="w-36 h-4 rounded bg-white/[0.06] mb-4" />
      {[1, 2, 3].map((i) => (
        <div key={i} className="glass-sm p-4 mb-3">
          <div className="flex items-center justify-between">
            <div className="w-28 h-4 rounded bg-white/[0.06]" />
            <div className="w-16 h-5 rounded-full bg-white/[0.06]" />
          </div>
          <div className="w-full h-1.5 rounded-full bg-white/[0.04] mt-3" />
        </div>
      ))}
    </div>
  );
}

function ActivitySkeleton() {
  return (
    <div className="glass p-5 animate-pulse">
      <div className="w-28 h-4 rounded bg-white/[0.06] mb-4" />
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3">
          <div className="w-8 h-8 rounded-lg bg-white/[0.06]" />
          <div className="flex-1 space-y-2">
            <div className="w-40 h-3 rounded bg-white/[0.06]" />
            <div className="w-24 h-2 rounded bg-white/[0.04]" />
          </div>
          <div className="w-16 h-5 rounded bg-white/[0.06]" />
        </div>
      ))}
    </div>
  );
}

/* ── Dashboard Content ─────────────────────────── */

function AdminDashboardContent() {
  const session = useAuthStore((s) => s.session);
  const initialised = useAuthStore((s) => s.initialised);
  const token = session?.access_token;

  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const result = await apiFetch<AdminDashboardData>('/admin/dashboard', token);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (initialised && token) {
      fetchDashboard();
    }
  }, [initialised, token, fetchDashboard]);

  return (
    <AdminLayout>
      <div className="max-w-[1400px]">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-display text-3xl font-bold text-white mb-1">Dashboard</h1>
            <p className="text-[var(--clr-text-secondary)] text-sm">
              Real-time overview of the PPSC Crack intelligence system.
            </p>
          </div>
          <button
            onClick={fetchDashboard}
            disabled={loading}
            className="glass-sm px-4 py-2 text-xs font-semibold text-[var(--clr-text-secondary)] hover:text-white hover:border-[var(--clr-glass-border-hover)] transition-all duration-200 disabled:opacity-50"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin w-3.5 h-3.5" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                </svg>
                Loading…
              </span>
            ) : (
              '↻ Refresh'
            )}
          </button>
        </div>

        {/* Error state */}
        {error && (
          <div className="glass-sm px-5 py-4 mb-6 border-l-4 border-[var(--clr-danger)]">
            <p className="text-sm text-[var(--clr-danger)] font-semibold">Failed to load dashboard</p>
            <p className="text-xs text-[var(--clr-text-muted)] mt-1">{error}</p>
            <button
              onClick={fetchDashboard}
              className="text-xs text-[var(--clr-primary)] hover:underline mt-2"
            >
              Try again
            </button>
          </div>
        )}

        {/* 1. Stat Cards */}
        {loading || !data ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => <StatCardSkeleton key={i} />)}
          </div>
        ) : (
          <div className="mb-6">
            <AdminStatCards stats={data.stats} />
          </div>
        )}

        {/* 2. Timeline + 3. Prediction Health — side by side */}
        <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-5 mb-6">
          {loading || !data ? (
            <>
              <TimelineSkeleton />
              <HealthSkeleton />
            </>
          ) : (
            <>
              <PapersTimeline papers={data.timeline} />
              <PredictionHealthPanel items={data.prediction_health} />
            </>
          )}
        </div>

        {/* 4. Recent Activity Feed */}
        {loading || !data ? (
          <ActivitySkeleton />
        ) : (
          <RecentActivityFeed items={data.recent_activity} />
        )}
      </div>
    </AdminLayout>
  );
}

export default function AdminPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <AdminDashboardContent />
    </ProtectedRoute>
  );
}
