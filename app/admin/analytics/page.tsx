/**
 * Admin Analytics — /admin/analytics
 * ====================================
 * Shows Daily Active Users (DAU) chart and conversion funnel.
 * Data comes from PostHog event aggregation via backend endpoint.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/admin/AdminLayout';
import { useAuthStore } from '@/store/auth-store';
import Icon from '@/components/Icon';

// Dynamic import for charts (code-split heavy Recharts)
const ResponsiveChart = dynamic(
  () => import('@/components/ResponsiveChart'),
  { ssr: false, loading: () => <div className="w-full h-[300px] animate-pulse rounded-xl bg-white/[0.03]" /> },
);

const AreaChartDynamic = dynamic(
  () => import('recharts').then(mod => mod.AreaChart),
  { ssr: false },
);

// We need to import recharts components individually
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';

/* ── Types ── */

interface DAUPoint {
  date: string;
  active_users: number;
}

interface FunnelStep {
  step: string;
  label: string;
  count: number;
  color: string;
}

interface AnalyticsResponse {
  dau: DAUPoint[];
  funnel: FunnelStep[];
  total_users: number;
  dau_average: number;
}

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

/* ── Skeleton ── */
function ChartSkeleton({ label }: { label: string }) {
  return (
    <div className="glass p-6 animate-pulse">
      <div className="w-40 h-5 rounded bg-white/[0.06] mb-6" />
      <div className="w-full h-[300px] rounded-xl bg-white/[0.03]" />
    </div>
  );
}

/* ── DAU Chart ── */
function DAUChart({ data, average }: { data: DAUPoint[]; average: number }) {
  const chartData = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en', { month: 'short', day: 'numeric' }),
    users: d.active_users,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData} margin={{ top: 8, right: 12, left: -8, bottom: 4 }}>
        <defs>
          <linearGradient id="dauGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#a78bfa" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#a78bfa" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(139,92,246,0.06)" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#9d95c7', fontSize: 11 }}
          axisLine={{ stroke: 'rgba(139,92,246,0.1)' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#9d95c7', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: 'rgba(12, 12, 29, 0.95)',
            border: '1px solid rgba(139,92,246,0.2)',
            borderRadius: 12,
            color: '#f1f0ff',
            fontSize: 12,
          }}
          formatter={(value: number) => [`${value} users`, 'DAU']}
        />
        <Area
          type="monotone"
          dataKey="users"
          stroke="#a78bfa"
          strokeWidth={2}
          fill="url(#dauGrad)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/* ── Conversion Funnel ── */
function ConversionFunnel({ data }: { data: FunnelStep[] }) {
  const maxCount = data.length > 0 ? data[0].count : 1;

  return (
    <div className="space-y-3">
      {data.map((step, idx) => {
        const widthPct = Math.max((step.count / maxCount) * 100, 8);
        const convRate = idx > 0 && data[idx - 1].count > 0
          ? ((step.count / data[idx - 1].count) * 100).toFixed(1)
          : '100.0';

        return (
          <div key={step.step} className="group">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-white">{step.label}</span>
              <div className="flex items-center gap-3">
                {idx > 0 && (
                  <span className="text-[10px] text-[var(--clr-text-muted)]">
                    {convRate}% from prev
                  </span>
                )}
                <span className="text-sm font-bold font-display text-white">
                  {step.count.toLocaleString()}
                </span>
              </div>
            </div>
            <div className="w-full h-8 rounded-lg bg-white/[0.04] overflow-hidden">
              <div
                className="h-full rounded-lg transition-all duration-700 flex items-center px-3"
                style={{
                  width: `${widthPct}%`,
                  background: step.color,
                }}
              >
                <span className="text-[10px] font-bold text-white/80 truncate">
                  {((step.count / maxCount) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ── Page Content ── */
function AdminAnalyticsContent() {
  const session = useAuthStore((s) => s.session);
  const token = session?.access_token;

  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

  const fetchData = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API}/admin/analytics?period=${period}`, {
        headers: { Authorization: `Bearer ${token}` },
        credentials: 'include',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
      // Fallback mock data for when API is not yet available
      setData({
        dau: Array.from({ length: period === '7d' ? 7 : period === '30d' ? 30 : 90 }, (_, i) => ({
          date: new Date(Date.now() - (period === '7d' ? 7 : period === '30d' ? 30 : 90 - i) * 86400000 + i * 86400000).toISOString().split('T')[0],
          active_users: Math.floor(Math.random() * 150) + 20,
        })),
        funnel: [
          { step: 'registered', label: 'Registered', count: 1240, color: 'rgba(167, 139, 250, 0.6)' },
          { step: 'onboarded', label: 'Completed Onboarding', count: 890, color: 'rgba(139, 92, 246, 0.6)' },
          { step: 'first_topic', label: 'Started First Topic', count: 620, color: 'rgba(232, 121, 249, 0.6)' },
          { step: 'practice_test', label: 'Took Practice Test', count: 380, color: 'rgba(56, 189, 248, 0.6)' },
          { step: 'subscribed', label: 'Subscribed (Premium)', count: 95, color: 'rgba(52, 211, 153, 0.6)' },
        ],
        total_users: 1240,
        dau_average: 87,
      });
    } finally {
      setLoading(false);
    }
  }, [token, period]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <AdminLayout>
      <div className="max-w-[1400px]">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="font-display text-3xl font-bold text-white mb-1">
              Product Analytics
            </h1>
            <p className="text-[var(--clr-text-secondary)] text-sm">
              Daily active users and conversion funnel from PostHog events.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {(['7d', '30d', '90d'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  period === p
                    ? 'bg-[var(--clr-primary-dim)] text-[var(--clr-primary)] border border-[var(--clr-glass-border-hover)]'
                    : 'text-[var(--clr-text-muted)] hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Stat cards */}
        {data && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="glass p-5">
              <p className="text-[10px] uppercase tracking-[0.15em] text-[var(--clr-text-muted)] mb-1">Total Users</p>
              <p className="font-display text-2xl font-bold text-white">{data.total_users.toLocaleString()}</p>
            </div>
            <div className="glass p-5">
              <p className="text-[10px] uppercase tracking-[0.15em] text-[var(--clr-text-muted)] mb-1">Avg DAU</p>
              <p className="font-display text-2xl font-bold text-white">{data.dau_average}</p>
            </div>
            <div className="glass p-5">
              <p className="text-[10px] uppercase tracking-[0.15em] text-[var(--clr-text-muted)] mb-1">Conversion Rate</p>
              <p className="font-display text-2xl font-bold text-[var(--clr-success)]">
                {data.funnel.length >= 2
                  ? ((data.funnel[data.funnel.length - 1].count / data.funnel[0].count) * 100).toFixed(1)
                  : '0'}%
              </p>
            </div>
            <div className="glass p-5">
              <p className="text-[10px] uppercase tracking-[0.15em] text-[var(--clr-text-muted)] mb-1">Premium Users</p>
              <p className="font-display text-2xl font-bold text-[var(--clr-gold)]">
                {data.funnel.find(f => f.step === 'subscribed')?.count.toLocaleString() ?? '0'}
              </p>
            </div>
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* DAU Chart */}
          <div className="glass p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-[var(--clr-primary-dim)]">
                <Icon name="trending-up" size={18} color="var(--clr-primary)" />
              </div>
              <h2 className="font-display text-lg font-bold text-white">Daily Active Users</h2>
            </div>
            {loading ? (
              <div className="w-full h-[300px] animate-pulse rounded-xl bg-white/[0.03]" />
            ) : data ? (
              <DAUChart data={data.dau} average={data.dau_average} />
            ) : null}
          </div>

          {/* Conversion Funnel */}
          <div className="glass p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-[rgba(232,121,249,0.1)]">
                <Icon name="target" size={18} color="#e879f9" />
              </div>
              <h2 className="font-display text-lg font-bold text-white">Conversion Funnel</h2>
            </div>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="w-32 h-3 rounded bg-white/[0.06] mb-2" />
                    <div className="w-full h-8 rounded-lg bg-white/[0.03]" />
                  </div>
                ))}
              </div>
            ) : data ? (
              <ConversionFunnel data={data.funnel} />
            ) : null}
          </div>
        </div>

        {/* Error notice */}
        {error && (
          <div className="glass-sm px-5 py-3 mt-4 border-l-4 border-[var(--clr-gold)]">
            <p className="text-xs text-[var(--clr-gold)]">
              ⚠ Using demo data — backend analytics endpoint returned: {error}
            </p>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}

export default function AdminAnalyticsPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <AdminAnalyticsContent />
    </ProtectedRoute>
  );
}
