/**
 * Admin — Pattern Analytics Dashboard (/admin/pattern-analytics)
 * ================================================================
 * Five-section analytics dashboard using Recharts:
 * 1. Topic Frequency — horizontal bar chart
 * 2. Year-by-Year Shift — multi-line chart
 * 3. Job Type Comparison — radar chart
 * 4. Repeat Questions Tracker — expandable table
 * 5. Prediction Accuracy Retrospective — side-by-side comparison
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/admin/AdminLayout';
import { useAuthStore } from '@/store/auth-store';
import {
  TopicFrequencyChart,
  YearByYearChart,
  JobTypeComparisonChart,
  RepeatQuestionsTracker,
  PredictionAccuracy,
} from '@/components/admin/pattern-analytics';
import type {
  PatternOverviewResponse,
  YearByYearResponse,
  CompareJobTypesResponse,
  RepeatQuestionsResponse,
  PredictionAccuracyResponse,
  JobType,
  PredictionSummary,
  PaperSummary,
} from '@/components/admin/pattern-analytics/types';

/* ── API helper ────────────────────────────────── */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function apiFetch<T = unknown>(
  path: string,
  opts: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((opts.headers as Record<string, string>) || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...opts, headers, credentials: 'include' });
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Component ─────────────────────────────────── */

function PatternAnalyticsContent() {
  const session = useAuthStore((s) => s.session);
  const token = session?.access_token;

  /* ── Global state ── */
  const [jobTypes, setJobTypes] = useState<JobType[]>([]);
  const [selectedJobType, setSelectedJobType] = useState('');
  const [error, setError] = useState<string | null>(null);

  /* ── Section loading states ── */
  const [loadingOverview, setLoadingOverview] = useState(false);
  const [loadingYearByYear, setLoadingYearByYear] = useState(false);
  const [loadingRadar, setLoadingRadar] = useState(false);
  const [loadingRepeat, setLoadingRepeat] = useState(false);
  const [loadingAccuracy, setLoadingAccuracy] = useState(false);

  /* ── Section data ── */
  const [overview, setOverview] = useState<PatternOverviewResponse | null>(null);
  const [yearByYear, setYearByYear] = useState<YearByYearResponse | null>(null);
  const [radarData, setRadarData] = useState<CompareJobTypesResponse | null>(null);
  const [repeatData, setRepeatData] = useState<RepeatQuestionsResponse | null>(null);
  const [accuracyData, setAccuracyData] = useState<PredictionAccuracyResponse | null>(null);

  /* ── Radar comparison selector ── */
  const [compareIds, setCompareIds] = useState<string[]>([]);

  /* ── Prediction accuracy selectors ── */
  const [predictions, setPredictions] = useState<PredictionSummary[]>([]);
  const [papers, setPapers] = useState<PaperSummary[]>([]);

  /* ── Fetch job types on mount ── */
  useEffect(() => {
    if (!token) return;
    apiFetch<{ items: JobType[] }>('/job-types', {}, token)
      .then((res) => {
        const active = (res.items || []).filter((jt) => jt.is_active);
        setJobTypes(active);
        if (active.length > 0) setSelectedJobType(active[0].id);
      })
      .catch((e) => setError(e.message));
  }, [token]);

  /* ── Fetch overview + year-by-year + repeat questions when job type changes ── */
  const fetchJobTypeData = useCallback(
    async (jtId: string) => {
      if (!token || !jtId) return;
      setError(null);

      // 1) Pattern overview
      setLoadingOverview(true);
      try {
        const ov = await apiFetch<PatternOverviewResponse>(
          `/patterns/overview/${jtId}`, {}, token,
        );
        setOverview(ov);
      } catch (e: any) {
        setOverview(null);
        console.error('Overview fetch error:', e);
      } finally {
        setLoadingOverview(false);
      }

      // 2) Year-by-year
      setLoadingYearByYear(true);
      try {
        const yby = await apiFetch<YearByYearResponse>(
          `/admin/pattern-analytics/year-by-year/${jtId}?top_n=8`, {}, token,
        );
        setYearByYear(yby);
      } catch (e: any) {
        setYearByYear(null);
        console.error('Year-by-year fetch error:', e);
      } finally {
        setLoadingYearByYear(false);
      }

      // 3) Repeat questions
      setLoadingRepeat(true);
      try {
        const rq = await apiFetch<RepeatQuestionsResponse>(
          `/admin/pattern-analytics/repeat-questions/${jtId}?per_page=30`, {}, token,
        );
        setRepeatData(rq);
      } catch (e: any) {
        setRepeatData(null);
        console.error('Repeat questions fetch error:', e);
      } finally {
        setLoadingRepeat(false);
      }
    },
    [token],
  );

  useEffect(() => {
    if (selectedJobType) fetchJobTypeData(selectedJobType);
  }, [selectedJobType, fetchJobTypeData]);

  /* ── Fetch predictions + papers list for accuracy section ── */
  useEffect(() => {
    if (!token) return;

    apiFetch<{ items: PredictionSummary[] }>('/admin/predictions?per_page=50', {}, token)
      .then((res) => setPredictions(res.items || []))
      .catch(() => setPredictions([]));

    apiFetch<{ items: PaperSummary[] }>('/papers?per_page=100', {}, token)
      .then((res) => setPapers(res.items || []))
      .catch(() => setPapers([]));
  }, [token]);

  /* ── Radar comparison handler ── */
  const toggleCompareId = (id: string) => {
    setCompareIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const fetchRadarData = useCallback(async () => {
    if (!token || compareIds.length < 2) return;
    setLoadingRadar(true);
    try {
      const rd = await apiFetch<CompareJobTypesResponse>(
        `/admin/pattern-analytics/compare-job-types?job_type_ids=${compareIds.join(',')}`, {}, token,
      );
      setRadarData(rd);
    } catch (e: any) {
      setRadarData(null);
      console.error('Radar fetch error:', e);
    } finally {
      setLoadingRadar(false);
    }
  }, [token, compareIds]);

  useEffect(() => {
    if (compareIds.length >= 2) fetchRadarData();
    else setRadarData(null);
  }, [compareIds, fetchRadarData]);

  /* ── Prediction accuracy comparison handler ── */
  const handleCompareAccuracy = async (predId: string, paperId: string) => {
    if (!token) return;
    setLoadingAccuracy(true);
    try {
      const ad = await apiFetch<PredictionAccuracyResponse>(
        `/admin/pattern-analytics/prediction-accuracy/${predId}?actual_paper_id=${paperId}`, {}, token,
      );
      setAccuracyData(ad);
    } catch (e: any) {
      setAccuracyData(null);
      console.error('Accuracy fetch error:', e);
    } finally {
      setLoadingAccuracy(false);
    }
  };

  /* ── Repeat questions pagination ── */
  const handleRepeatPage = async (page: number) => {
    if (!token || !selectedJobType) return;
    setLoadingRepeat(true);
    try {
      const rq = await apiFetch<RepeatQuestionsResponse>(
        `/admin/pattern-analytics/repeat-questions/${selectedJobType}?page=${page}&per_page=30`, {}, token,
      );
      setRepeatData(rq);
    } catch (e: any) {
      console.error('Repeat page error:', e);
    } finally {
      setLoadingRepeat(false);
    }
  };

  return (
    <AdminLayout>
      <div className="max-w-[1400px] mx-auto space-y-8">
        {/* ── Header ── */}
        <div>
          <h1 className="text-2xl font-display font-black text-white tracking-tight">
            Pattern Analytics
          </h1>
          <p className="text-sm text-[var(--clr-text-muted)] mt-1">
            Deep-dive into topic trends, repeat patterns, and prediction accuracy.
          </p>
        </div>

        {/* ── Error banner ── */}
        {error && (
          <div className="glass-sm rounded-xl p-4 border border-red-500/20 bg-red-500/5">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* ── Job Type Selector ── */}
        <div className="glass rounded-2xl p-5">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex-1">
              <label className="block text-[10px] uppercase tracking-[0.12em] font-semibold text-[var(--clr-text-muted)] mb-1.5">
                Job Type
              </label>
              <select
                value={selectedJobType}
                onChange={(e) => setSelectedJobType(e.target.value)}
                className="w-full sm:max-w-xs bg-[var(--clr-bg-base)] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--clr-primary)] transition-colors appearance-none"
              >
                {jobTypes.map((jt) => (
                  <option key={jt.id} value={jt.id}>
                    {jt.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Quick stats from overview */}
            {overview && (
              <div className="flex gap-4">
                <QuickStat label="Papers" value={String(overview.paper_count)} />
                <QuickStat
                  label="Confidence"
                  value={`${(overview.confidence_score * 100).toFixed(0)}%`}
                />
                <QuickStat label="Topics" value={String(overview.topic_trends.length)} />
                <QuickStat
                  label="Repeats"
                  value={String(overview.repeat_summary.total_repeated_questions)}
                />
              </div>
            )}
          </div>
        </div>

        {/* ── Section 1: Topic Frequency ── */}
        <TopicFrequencyChart
          data={overview?.topic_trends ?? []}
          loading={loadingOverview}
        />

        {/* ── Section 2: Year-by-Year Shift ── */}
        <YearByYearChart data={yearByYear} loading={loadingYearByYear} />

        {/* ── Section 3: Job Type Comparison (Radar) ── */}
        <div className="space-y-4">
          <div className="glass rounded-2xl p-5">
            <h3 className="text-lg font-display font-bold text-white mb-4">
              Compare Job Types
            </h3>
            <p className="text-xs text-[var(--clr-text-muted)] mb-4">
              Select 2 or more job types to overlay their topic distributions.
            </p>
            <div className="flex flex-wrap gap-2">
              {jobTypes.map((jt) => {
                const isSelected = compareIds.includes(jt.id);
                return (
                  <button
                    key={jt.id}
                    onClick={() => toggleCompareId(jt.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all duration-200 border ${
                      isSelected
                        ? 'bg-[var(--clr-primary-dim)] text-[var(--clr-primary)] border-[var(--clr-primary)]/30 shadow-[0_0_12px_rgba(139,92,246,0.2)]'
                        : 'bg-white/[0.03] text-[var(--clr-text-secondary)] border-white/10 hover:bg-white/[0.06]'
                    }`}
                  >
                    {isSelected && '✓ '}{jt.name}
                  </button>
                );
              })}
            </div>
            {compareIds.length === 1 && (
              <p className="text-[10px] text-amber-400 mt-2">Pick at least one more job type.</p>
            )}
          </div>

          <JobTypeComparisonChart data={radarData} loading={loadingRadar} />
        </div>

        {/* ── Section 4: Repeat Questions Tracker ── */}
        <RepeatQuestionsTracker
          data={repeatData}
          loading={loadingRepeat}
          onPageChange={handleRepeatPage}
        />

        {/* ── Section 5: Prediction Accuracy Retrospective ── */}
        <PredictionAccuracy
          data={accuracyData}
          predictions={predictions}
          papers={papers}
          loading={loadingAccuracy}
          onCompare={handleCompareAccuracy}
        />
      </div>
    </AdminLayout>
  );
}

/* ── Quick stat pill ─────────────────────────── */

function QuickStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <p className="text-[10px] uppercase tracking-[0.12em] font-semibold text-[var(--clr-text-muted)]">
        {label}
      </p>
      <p className="text-lg font-bold font-mono text-white">{value}</p>
    </div>
  );
}

/* ── Page export with auth guard ── */

export default function PatternAnalyticsPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <PatternAnalyticsContent />
    </ProtectedRoute>
  );
}
