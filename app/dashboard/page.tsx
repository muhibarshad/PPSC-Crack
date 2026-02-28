/**
 * Student Dashboard — /dashboard
 * ================================
 * Home page showing readiness ring, streak counter, action cards, and quick stats.
 * Data is fetched from GET /api/v1/dashboard/home.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuthStore, needsOnboarding } from '@/store/auth-store';
import ProgressRing from '@/components/dashboard/ProgressRing';
import StreakCounter from '@/components/dashboard/StreakCounter';
import TodaysFocusCard from '@/components/dashboard/TodaysFocusCard';
import LatestPredictionCard from '@/components/dashboard/LatestPredictionCard';
import NextStoryCard from '@/components/dashboard/NextStoryCard';
import QuickStatsBar from '@/components/dashboard/QuickStatsBar';
import Icon from '@/components/Icon';

/* ── Types matching backend DashboardHomeResponse ── */

interface ProgressData {
  topics_completed: number;
  topics_total: number;
  readiness_percent: number;
}

interface StreakData {
  current_streak: number;
  longest_streak: number;
  studied_today: boolean;
}

interface QuickStats {
  topics_completed: number;
  questions_practiced: number;
  days_active: number;
}

interface TodaysFocus {
  topic_id: string;
  topic_name: string;
  display_name: string;
  percentage: number;
  trend_direction: string | null;
  icon: string | null;
}

interface LatestPrediction {
  prediction_id: string;
  title: string;
  prediction_date: string;
  confidence_score: number;
  total_questions: number;
  job_type_name: string;
}

interface NextStory {
  topic_id: string;
  topic_name: string;
  display_name: string;
  story_word_count: number;
  estimated_read_minutes: number;
  frequency_score: number;
}

interface DashboardData {
  greeting_name: string;
  subscription_tier: string;
  is_premium: boolean;
  progress: ProgressData;
  streak: StreakData;
  quick_stats: QuickStats;
  todays_focus: TodaysFocus | null;
  latest_prediction: LatestPrediction | null;
  next_story: NextStory | null;
  selected_job_names: string[];
}

/* ── API helper ── */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function fetchDashboard(token: string): Promise<DashboardData> {
  const res = await fetch(`${API}/dashboard/home`, {
    headers: { Authorization: `Bearer ${token}` },
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to load dashboard' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Dashboard Content ── */

function DashboardContent() {
  const router = useRouter();
  const { user, session, logout } = useAuthStore();

  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Redirect to onboarding if student hasn't selected job types
  useEffect(() => {
    if (user && needsOnboarding(user)) {
      router.replace('/onboarding');
    }
  }, [user, router]);

  // Fetch dashboard data
  const load = useCallback(async () => {
    const token = session?.access_token;
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const result = await fetchDashboard(token);
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

  /* ── Time-based greeting ── */
  const hour = new Date().getHours();
  const timeGreeting =
    hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  /* ── Loading state ── */
  if (loading) {
    return (
      <div className="min-h-screen z-10 relative pt-24 px-6">
        <div className="max-w-5xl mx-auto flex flex-col items-center justify-center gap-6 py-32">
          <div className="w-16 h-16 rounded-full border-4 border-[var(--clr-primary-dim)] border-t-[var(--clr-primary)] animate-spin" />
          <p className="text-[var(--clr-text-secondary)] text-sm">Loading your dashboard…</p>
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
      <div className="max-w-5xl mx-auto flex flex-col gap-8">
        {/* ═══ Header ═══ */}
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 animate-fade-in-up">
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold text-white">
              {timeGreeting}, <span className="gradient-text">{data.greeting_name}</span>! 👋
            </h1>
            <p className="text-[var(--clr-text-secondary)] mt-1">
              {data.selected_job_names.length > 0
                ? `Preparing for ${data.selected_job_names.join(', ')}`
                : 'Your PPSC exam preparation hub'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {data.is_premium && (
              <span className="badge badge-gold">
                <Icon name="star" size={12} /> Premium
              </span>
            )}
            <button onClick={logout} className="btn btn-ghost btn-sm">
              <Icon name="x" size={14} />
              Sign Out
            </button>
          </div>
        </div>

        {/* ═══ Hero Section: Progress Ring + Streak ═══ */}
        <section className="glass p-8 animate-fade-in-up delay-100">
          <div className="flex flex-col md:flex-row items-center gap-8 md:gap-12">
            {/* Progress Ring */}
            <ProgressRing
              percent={data.progress.readiness_percent}
              completed={data.progress.topics_completed}
              total={data.progress.topics_total}
              size={180}
              strokeWidth={10}
            />

            {/* Divider */}
            <div className="hidden md:block w-px h-32 bg-[var(--clr-glass-border)]" />
            <div className="block md:hidden w-32 h-px bg-[var(--clr-glass-border)]" />

            {/* Streak Counter */}
            <StreakCounter
              currentStreak={data.streak.current_streak}
              longestStreak={data.streak.longest_streak}
              studiedToday={data.streak.studied_today}
            />

            {/* Right side: motivational note */}
            <div className="flex-1 text-center md:text-left">
              <h2 className="font-display text-xl font-bold text-white mb-2">
                {data.progress.readiness_percent >= 75
                  ? '🎯 Almost there!'
                  : data.progress.readiness_percent >= 40
                    ? '💪 Keep going!'
                    : '🚀 Let\u2019s get started!'}
              </h2>
              <p className="text-sm text-[var(--clr-text-secondary)] leading-relaxed">
                {data.progress.readiness_percent >= 75
                  ? 'You\'re well-prepared. Review the predicted papers and polish your weak areas.'
                  : data.progress.readiness_percent >= 40
                    ? 'Great progress so far! Focus on today\'s hot topic to keep climbing.'
                    : 'Start with the stories below to build a solid foundation for your exam.'}
              </p>
            </div>
          </div>
        </section>

        {/* ═══ Action Cards ═══ */}
        <section className="flex flex-wrap gap-6 animate-fade-in-up delay-200">
          {/* Today's Focus */}
          {data.todays_focus && (
            <TodaysFocusCard
              topicName={data.todays_focus.topic_name}
              displayName={data.todays_focus.display_name}
              percentage={data.todays_focus.percentage}
              trendDirection={data.todays_focus.trend_direction}
              icon={data.todays_focus.icon}
            />
          )}

          {/* Latest Predicted Paper — premium only */}
          {data.latest_prediction && data.is_premium && (
            <LatestPredictionCard
              title={data.latest_prediction.title}
              predictionDate={data.latest_prediction.prediction_date}
              confidenceScore={data.latest_prediction.confidence_score}
              totalQuestions={data.latest_prediction.total_questions}
              jobTypeName={data.latest_prediction.job_type_name}
            />
          )}

          {/* Locked prediction card for free users */}
          {!data.is_premium && (
            <div className="glow-card p-6 flex flex-col gap-4 flex-1 min-w-[260px] opacity-70">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center"
                    style={{ background: 'var(--clr-gold-dim)' }}
                  >
                    <Icon name="lock" size={20} color="var(--clr-gold)" />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-widest text-[var(--clr-text-muted)]">
                      Predicted Paper
                    </p>
                    <h3 className="font-display text-lg font-bold text-white leading-snug">
                      Unlock AI Predictions
                    </h3>
                  </div>
                </div>
                <span className="badge badge-gold text-[10px]">⭐ Premium</span>
              </div>
              <p className="text-sm text-[var(--clr-text-secondary)] mt-auto">
                Get AI-predicted papers based on past PPSC patterns.
              </p>
              <button className="btn btn-gold btn-sm w-full mt-1">
                <Icon name="star" size={14} />
                Upgrade to Premium
              </button>
            </div>
          )}

          {/* Current Affairs Feed */}
          <div
            className="glow-card p-6 flex flex-col gap-4 flex-1 min-w-[260px] group cursor-pointer hover:border-[rgba(56,189,248,0.35)] transition-colors"
            onClick={() => (window.location.href = '/dashboard/current-affairs')}
            role="link"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter') window.location.href = '/dashboard/current-affairs'; }}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'rgba(56, 189, 248, 0.1)' }}
                >
                  <Icon name="globe" size={20} color="#38bdf8" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-widest text-[var(--clr-text-muted)]">
                    Daily Feed
                  </p>
                  <h3 className="font-display text-lg font-bold text-white leading-snug">
                    Current Affairs
                  </h3>
                </div>
              </div>
              <span
                className="badge text-[10px] font-bold"
                style={{
                  background: 'rgba(56, 189, 248, 0.12)',
                  color: '#38bdf8',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                }}
              >
                📰 Today
              </span>
            </div>
            <p className="text-sm text-[var(--clr-text-secondary)] mt-auto">
              Stay updated with today&apos;s headlines, test yourself with quick MCQs, and track what you&apos;ve learned.
            </p>
            <button className="btn btn-ghost btn-sm w-full mt-1 group-hover:border-[rgba(56,189,248,0.35)]">
              <Icon name="arrow-right" size={14} />
              Open Feed
            </button>
          </div>

          {/* Next Story */}
          {data.next_story && (
            <NextStoryCard
              displayName={data.next_story.display_name}
              storyWordCount={data.next_story.story_word_count}
              estimatedReadMinutes={data.next_story.estimated_read_minutes}
              frequencyScore={data.next_story.frequency_score}
            />
          )}
        </section>

        {/* ═══ Quick Stats Bar ═══ */}
        <section className="animate-fade-in-up delay-300">
          <QuickStatsBar
            topicsCompleted={data.quick_stats.topics_completed}
            questionsPracticed={data.quick_stats.questions_practiced}
            daysActive={data.quick_stats.days_active}
          />
        </section>
      </div>
    </div>
  );
}

/* ── Page Wrapper ── */

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
