/**
 * Student Analytics — /dashboard/analytics
 * ==========================================
 * Comprehensive analytics screen with six chart sections:
 *   1. Study Streak Calendar (GitHub-style contribution grid)
 *   2. Topic Completion Bars (horizontal bar chart)
 *   3. Quiz Score Trend (area/line chart)
 *   4. Exam Readiness Score (animated CountUp + formula)
 *   5. Time Studied Per Day (bar chart — last 30 days)
 *   6. Comparison (user vs average peer readiness)
 *
 * Data: GET /api/v1/student/analytics
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/store/auth-store';
import Icon from '@/components/Icon';

import StudyStreakCalendar from '@/components/dashboard/analytics/StudyStreakCalendar';
import TopicCompletionBars from '@/components/dashboard/analytics/TopicCompletionBars';
import QuizScoreTrend from '@/components/dashboard/analytics/QuizScoreTrend';
import ExamReadinessScore from '@/components/dashboard/analytics/ExamReadinessScore';
import TimeStudiedChart from '@/components/dashboard/analytics/TimeStudiedChart';
import ReadinessComparison from '@/components/dashboard/analytics/ReadinessComparison';

/* ── Types matching backend StudentAnalyticsResponse ── */

interface StudyDay {
  date: string;
  minutes_studied: number;
}

interface TopicCompletion {
  topic_id: string;
  topic_name: string;
  display_name: string;
  completed: boolean;
  weight: number;
  completion_percent: number;
}

interface QuizScorePoint {
  date: string;
  score_percent: number;
  total_questions: number;
}

interface ExamReadiness {
  readiness_percent: number;
  completed_weight: number;
  total_weight: number;
  topics_completed: number;
  topics_total: number;
}

interface DailyStudyMinutes {
  date: string;
  minutes: number;
}

interface ReadinessComparisonData {
  user_readiness: number;
  average_readiness: number;
  total_peers: number;
}

interface AnalyticsData {
  study_calendar: StudyDay[];
  topic_completions: TopicCompletion[];
  quiz_scores: QuizScorePoint[];
  readiness: ExamReadiness;
  daily_study_minutes: DailyStudyMinutes[];
  comparison: ReadinessComparisonData;
}

/* ── API helper ── */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function fetchAnalytics(token: string): Promise<AnalyticsData> {
  const res = await fetch(`${API}/student/analytics`, {
    headers: { Authorization: `Bearer ${token}` },
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to load analytics' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Section Card wrapper ── */

function SectionCard({
  title,
  icon,
  badge,
  children,
  className = '',
}: {
  title: string;
  icon: string;
  badge?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`glass p-6 animate-fade-in-up ${className}`}>
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--clr-primary-dim)' }}
          >
            <Icon name={icon} size={18} color="var(--clr-primary)" />
          </div>
          <h2 className="font-display text-lg font-bold text-white">{title}</h2>
        </div>
        {badge && (
          <span className="badge badge-primary text-[10px]">{badge}</span>
        )}
      </div>
      {children}
    </section>
  );
}

/* ── Analytics Content ── */

function AnalyticsContent() {
  const router = useRouter();
  const { session } = useAuthStore();

  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = session?.access_token;
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const result = await fetchAnalytics(token);
      setData(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    load();
  }, [load]);

  /* ── Loading state ── */
  if (loading) {
    return (
      <div className="min-h-screen z-10 relative pt-24 px-6">
        <div className="max-w-6xl mx-auto flex flex-col items-center justify-center gap-6 py-32">
          <div className="w-16 h-16 rounded-full border-4 border-[var(--clr-primary-dim)] border-t-[var(--clr-primary)] animate-spin" />
          <p className="text-[var(--clr-text-secondary)] text-sm">Loading analytics…</p>
        </div>
      </div>
    );
  }

  /* ── Error state ── */
  if (error) {
    return (
      <div className="min-h-screen z-10 relative pt-24 px-6">
        <div className="max-w-lg mx-auto py-32">
          <div className="glass p-8 text-center">
            <div className="w-14 h-14 rounded-full bg-[var(--clr-danger-dim)] flex items-center justify-center mx-auto mb-4">
              <Icon name="x" size={24} color="var(--clr-danger)" />
            </div>
            <h2 className="font-display text-xl font-bold text-white mb-2">Oops!</h2>
            <p className="text-[var(--clr-text-secondary)] mb-6">{error}</p>
            <button onClick={load} className="btn btn-primary">
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="min-h-screen z-10 relative pt-24 pb-16 px-6">
      <div className="max-w-6xl mx-auto flex flex-col gap-8">
        {/* ═══ Header ═══ */}
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 animate-fade-in-up">
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold text-white">
              Your <span className="gradient-text">Analytics</span> 📊
            </h1>
            <p className="text-[var(--clr-text-secondary)] mt-1">
              Track your progress, identify weak areas, and monitor your exam readiness.
            </p>
          </div>

          <button
            onClick={() => router.push('/dashboard')}
            className="btn btn-ghost btn-sm"
          >
            <Icon name="arrow-right" size={14} />
            Back to Dashboard
          </button>
        </div>

        {/* ═══ Row 1: Readiness Score + Comparison ═══ */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SectionCard
            title="Exam Readiness"
            icon="target"
            badge="Weighted Score"
            className="delay-100"
          >
            <ExamReadinessScore
              readinessPercent={data.readiness.readiness_percent}
              completedWeight={data.readiness.completed_weight}
              totalWeight={data.readiness.total_weight}
              topicsCompleted={data.readiness.topics_completed}
              topicsTotal={data.readiness.topics_total}
            />
          </SectionCard>

          <SectionCard
            title="You vs Peers"
            icon="users"
            badge="Same Job Type"
            className="delay-200"
          >
            <ReadinessComparison
              userReadiness={data.comparison.user_readiness}
              averageReadiness={data.comparison.average_readiness}
              totalPeers={data.comparison.total_peers}
            />
          </SectionCard>
        </div>

        {/* ═══ Row 2: Study Streak Calendar ═══ */}
        <SectionCard
          title="Study Streak"
          icon="zap"
          badge="Last 90 Days"
          className="delay-200 overflow-x-auto"
        >
          <StudyStreakCalendar data={data.study_calendar} />
        </SectionCard>

        {/* ═══ Row 3: Quiz Score Trend + Time Studied ═══ */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SectionCard
            title="Quiz Score Trend"
            icon="trending-up"
            className="delay-300"
          >
            <QuizScoreTrend data={data.quiz_scores} />
          </SectionCard>

          <SectionCard
            title="Study Time"
            icon="chart-line"
            badge="Last 30 Days"
            className="delay-300"
          >
            <TimeStudiedChart data={data.daily_study_minutes} />
          </SectionCard>
        </div>

        {/* ═══ Row 4: Topic Completion Bars ═══ */}
        <SectionCard
          title="Topic Completion"
          icon="book-open"
          badge={`${data.topic_completions.filter((t) => t.completed).length} / ${data.topic_completions.length} done`}
          className="delay-400"
        >
          <TopicCompletionBars data={data.topic_completions} />
        </SectionCard>
      </div>
    </div>
  );
}

/* ── Page Wrapper ── */

export default function AnalyticsPage() {
  return (
    <ProtectedRoute>
      <AnalyticsContent />
    </ProtectedRoute>
  );
}
