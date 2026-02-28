/**
 * Learning Path — /dashboard/learning-path/[jobTypeId]
 * =====================================================
 * Vertical roadmap of all topics for the selected job type,
 * ordered by predicted exam weight (highest first).
 * GSAP ScrollTrigger animates nodes in as the user scrolls.
 */

'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/store/auth-store';
import TopicNode from '@/components/dashboard/TopicNode';
import type { TopicNodeData } from '@/components/dashboard/TopicNode';
import Icon from '@/components/Icon';

gsap.registerPlugin(ScrollTrigger);

/* ── Types matching backend LearningPathResponse ── */

interface LearningPathData {
  job_type_id: string;
  job_type_name: string;
  total_topics: number;
  completed_count: number;
  in_progress_count: number;
  overall_percent: number;
  topics: TopicNodeData[];
}

/* ── API helper ── */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function fetchLearningPath(
  jobTypeId: string,
  token: string,
): Promise<LearningPathData> {
  const res = await fetch(`${API}/dashboard/learning-path/${jobTypeId}`, {
    headers: { Authorization: `Bearer ${token}` },
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to load learning path' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Content ── */

function LearningPathContent() {
  const params = useParams();
  const router = useRouter();
  const { session } = useAuthStore();
  const jobTypeId = params.jobTypeId as string;

  const [data, setData] = useState<LearningPathData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const nodesContainerRef = useRef<HTMLDivElement>(null);

  /* ── Fetch data ── */
  const load = useCallback(async () => {
    const token = session?.access_token;
    if (!token || !jobTypeId) return;
    try {
      setLoading(true);
      setError(null);
      const result = await fetchLearningPath(jobTypeId, token);
      setData(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, jobTypeId]);

  useEffect(() => {
    load();
  }, [load]);

  /* ── GSAP scroll animations ── */
  useEffect(() => {
    if (!data || !nodesContainerRef.current) return;

    const nodes = nodesContainerRef.current.querySelectorAll('.roadmap-node');
    if (nodes.length === 0) return;

    const ctx = gsap.context(() => {
      nodes.forEach((node, i) => {
        gsap.fromTo(
          node,
          { opacity: 0, y: 50, scale: 0.97 },
          {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.6,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: node,
              start: 'top 88%',
              toggleActions: 'play none none none',
            },
            delay: i < 4 ? i * 0.08 : 0, // stagger first 4 for initial view
          },
        );
      });
    }, nodesContainerRef);

    return () => ctx.revert();
  }, [data]);

  /* ── Navigate to story reader ── */
  const handleTopicClick = (topicId: string) => {
    router.push(`/dashboard/stories/${topicId}`);
  };

  /* ── Loading ── */
  if (loading) {
    return (
      <div className="min-h-screen z-10 relative pt-24 px-6">
        <div className="max-w-3xl mx-auto flex flex-col items-center justify-center gap-6 py-32">
          <div className="w-16 h-16 rounded-full border-4 border-[var(--clr-primary-dim)] border-t-[var(--clr-primary)] animate-spin" />
          <p className="text-[var(--clr-text-secondary)] text-sm">Loading learning path\u2026</p>
        </div>
      </div>
    );
  }

  /* ── Error ── */
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

  const notStarted = data.total_topics - data.completed_count - data.in_progress_count;

  return (
    <div className="min-h-screen z-10 relative pt-24 pb-20 px-6">
      <div className="max-w-3xl mx-auto flex flex-col gap-8">
        {/* ═══ Header ═══ */}
        <div className="animate-fade-in-up">
          {/* Back button */}
          <button
            onClick={() => router.push('/dashboard')}
            className="btn btn-ghost btn-sm mb-4"
          >
            <Icon name="arrow-right" size={14} className="rotate-180" />
            Dashboard
          </button>

          <h1 className="font-display text-3xl md:text-4xl font-bold text-white">
            <span className="gradient-text">{data.job_type_name}</span>
          </h1>
          <p className="text-[var(--clr-text-secondary)] mt-1">
            {data.total_topics} topics &middot; ordered by predicted exam weight
          </p>
        </div>

        {/* ═══ Summary bar ═══ */}
        <div className="glass p-6 animate-fade-in-up delay-100">
          <div className="flex flex-wrap items-center gap-6">
            {/* Overall progress ring (mini) */}
            <div className="relative w-16 h-16 shrink-0">
              <svg width={64} height={64} className="transform -rotate-90">
                <circle
                  cx={32}
                  cy={32}
                  r={26}
                  fill="none"
                  stroke="rgba(139, 92, 246, 0.08)"
                  strokeWidth={6}
                />
                <circle
                  cx={32}
                  cy={32}
                  r={26}
                  fill="none"
                  stroke="url(#lpGrad)"
                  strokeWidth={6}
                  strokeLinecap="round"
                  strokeDasharray={2 * Math.PI * 26}
                  strokeDashoffset={
                    2 * Math.PI * 26 -
                    (2 * Math.PI * 26 * data.overall_percent) / 100
                  }
                  style={{ transition: 'stroke-dashoffset 1.5s cubic-bezier(0.22,1,0.36,1)' }}
                />
                <defs>
                  <linearGradient id="lpGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#a78bfa" />
                    <stop offset="100%" stopColor="#e879f9" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="absolute inset-0 flex items-center justify-center font-display text-sm font-bold text-white">
                {Math.round(data.overall_percent)}%
              </span>
            </div>

            {/* Stat pills */}
            <div className="flex flex-wrap gap-3 flex-1">
              <div className="glass-sm px-4 py-2 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--clr-success)]" />
                <span className="text-sm text-white font-semibold">{data.completed_count}</span>
                <span className="text-xs text-[var(--clr-text-muted)]">Completed</span>
              </div>
              <div className="glass-sm px-4 py-2 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--clr-primary)]" />
                <span className="text-sm text-white font-semibold">{data.in_progress_count}</span>
                <span className="text-xs text-[var(--clr-text-muted)]">In Progress</span>
              </div>
              <div className="glass-sm px-4 py-2 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--clr-text-muted)]" />
                <span className="text-sm text-white font-semibold">{notStarted}</span>
                <span className="text-xs text-[var(--clr-text-muted)]">Not Started</span>
              </div>
            </div>
          </div>
        </div>

        {/* ═══ Roadmap ═══ */}
        <div ref={nodesContainerRef} className="flex flex-col">
          {data.topics.map((topic, idx) => (
            <div key={topic.topic_id} className="roadmap-node" style={{ opacity: 0 }}>
              <TopicNode
                topic={topic}
                isLast={idx === data.topics.length - 1}
                onClick={handleTopicClick}
              />
            </div>
          ))}

          {data.topics.length === 0 && (
            <div className="glass p-12 text-center">
              <Icon name="route" size={40} color="var(--clr-text-muted)" className="mx-auto mb-4" />
              <p className="text-[var(--clr-text-secondary)]">
                No topics found for this job type yet.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Page wrapper ── */

export default function LearningPathPage() {
  return (
    <ProtectedRoute>
      <LearningPathContent />
    </ProtectedRoute>
  );
}
