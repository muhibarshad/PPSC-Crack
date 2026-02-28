'use client';

/**
 * /onboarding — Student first-login onboarding flow.
 * ====================================================
 * Full-screen 3-step wizard:
 *   1. Job selection (multi-select grid + search)
 *   2. AI analysis (radar charts, confidence, prep time)
 *   3. Learning path preview (top 5 priority topics)
 *
 * On complete → saves selected_job_types → redirects to /dashboard.
 */

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import JobSelectionStep, { type JobType } from '@/components/onboarding/JobSelectionStep';
import AIAnalysisStep, { type JobAnalysis } from '@/components/onboarding/AIAnalysisStep';
import LearningPathStep, { type LearningPathPreview } from '@/components/onboarding/LearningPathStep';
import Icon from '@/components/Icon';

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function apiFetch<T>(path: string, token: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
  const res = await fetch(`${API}${path}`, {
    method: body ? 'POST' : 'GET',
    headers,
    credentials: 'include',
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Step indicator ── */
function StepIndicator({ current }: { current: number }) {
  const steps = [
    { n: 1, label: 'Choose Jobs' },
    { n: 2, label: 'AI Analysis' },
    { n: 3, label: 'Learning Path' },
  ];

  return (
    <div className="flex items-center justify-center gap-2 mb-12">
      {steps.map((s, i) => {
        const active = s.n === current;
        const done = s.n < current;
        return (
          <div key={s.n} className="flex items-center gap-2">
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded-full transition-all text-xs font-medium"
              style={{
                background: active
                  ? 'var(--grad-primary)'
                  : done
                  ? 'var(--clr-success-dim)'
                  : 'rgba(139,92,246,0.06)',
                color: active
                  ? 'white'
                  : done
                  ? 'var(--clr-success)'
                  : 'var(--clr-text-muted)',
                border: active
                  ? 'none'
                  : done
                  ? '1px solid rgba(52,211,153,0.2)'
                  : '1px solid var(--clr-glass-border)',
              }}
            >
              {done ? <Icon name="check" size={12} /> : <span>{s.n}</span>}
              <span className="hidden sm:inline">{s.label}</span>
            </div>
            {i < steps.length - 1 && (
              <div
                className="w-8 h-px"
                style={{
                  background: s.n < current ? 'var(--clr-success)' : 'var(--clr-glass-border)',
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function OnboardingContent() {
  const router = useRouter();
  const { user, session } = useAuthStore();

  const [step, setStep] = useState(1);
  const [jobTypes, setJobTypes] = useState<JobType[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [analyses, setAnalyses] = useState<JobAnalysis[]>([]);
  const [learningPath, setLearningPath] = useState<LearningPathPreview>({
    topics: [],
    total_topics_in_path: 0,
  });
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [loadingComplete, setLoadingComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ── Fetch job types on mount ── */
  useEffect(() => {
    async function fetchJobs() {
      try {
        const data = await apiFetch<{ job_types: JobType[] }>(
          '/job-types/?active_only=true',
          session?.access_token || '',
        );
        setJobTypes(data.job_types);
      } catch (err) {
        console.error('Failed to fetch job types:', err);
        setError('Failed to load job types. Please refresh.');
      } finally {
        setLoadingJobs(false);
      }
    }
    fetchJobs();
  }, [session]);

  /* ── Step 1 → 2: Analyze ── */
  const handleAnalyze = useCallback(async () => {
    setLoadingAnalysis(true);
    setError(null);
    try {
      const data = await apiFetch<{ analyses: JobAnalysis[] }>(
        '/onboarding/analyze',
        session?.access_token || '',
        { selected_job_type_ids: selectedIds },
      );
      setAnalyses(data.analyses);
      setStep(2);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Analysis failed';
      setError(msg);
    } finally {
      setLoadingAnalysis(false);
    }
  }, [selectedIds, session]);

  /* ── Step 3: Complete ── */
  const handleComplete = useCallback(async () => {
    setLoadingComplete(true);
    setError(null);
    try {
      const data = await apiFetch<{
        learning_path: LearningPathPreview;
        analyses: JobAnalysis[];
      }>(
        '/onboarding/complete',
        session?.access_token || '',
        { selected_job_type_ids: selectedIds },
      );
      // Update learning path from complete response
      if (data.learning_path) {
        setLearningPath(data.learning_path);
      }
      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to complete onboarding';
      setError(msg);
      setLoadingComplete(false);
    }
  }, [selectedIds, session, router]);

  /* ── Step 2 → 3: Build learning path preview ── */
  const handleViewPath = useCallback(async () => {
    // We already have analyses; the learning path comes from the /complete call,
    // but for preview we build it from the /analyze response data.
    // Use the analyze endpoint response and build local preview
    setLoadingAnalysis(true);
    try {
      const data = await apiFetch<{
        learning_path: LearningPathPreview;
        analyses: JobAnalysis[];
      }>(
        '/onboarding/complete',
        session?.access_token || '',
        { selected_job_type_ids: selectedIds },
      );
      setLearningPath(data.learning_path);
      setAnalyses(data.analyses);
      setStep(3);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load learning path';
      setError(msg);
    } finally {
      setLoadingAnalysis(false);
    }
  }, [selectedIds, session]);

  /* ── Loading state ── */
  if (loadingJobs) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center z-10 relative">
        <svg className="animate-spin h-10 w-10 mb-4" style={{ color: 'var(--clr-primary)' }} viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p style={{ color: 'var(--clr-text-secondary)' }}>Loading job types…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen z-10 relative py-12 px-4 sm:px-6">
      <div className="max-w-5xl mx-auto">
        {/* Step indicator */}
        <StepIndicator current={step} />

        {/* Error banner */}
        {error && (
          <div
            className="glass-sm flex items-center gap-3 p-4 mb-8 max-w-2xl mx-auto"
            style={{
              background: 'var(--clr-danger-dim)',
              border: '1px solid rgba(248,113,113,0.2)',
            }}
          >
            <Icon name="x" size={16} color="var(--clr-danger)" />
            <p className="text-sm" style={{ color: 'var(--clr-danger)' }}>{error}</p>
            <button onClick={() => setError(null)} className="ml-auto">
              <Icon name="x" size={14} color="var(--clr-danger)" />
            </button>
          </div>
        )}

        {/* Steps */}
        {step === 1 && (
          <JobSelectionStep
            jobTypes={jobTypes}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            onNext={handleAnalyze}
            loading={loadingAnalysis}
          />
        )}

        {step === 2 && (
          <AIAnalysisStep
            analyses={analyses}
            onNext={handleViewPath}
            onBack={() => setStep(1)}
          />
        )}

        {step === 3 && (
          <LearningPathStep
            learningPath={learningPath}
            onBack={() => setStep(2)}
            onComplete={handleComplete}
            loading={loadingComplete}
          />
        )}
      </div>
    </div>
  );
}

export default function OnboardingPage() {
  return (
    <ProtectedRoute>
      <OnboardingContent />
    </ProtectedRoute>
  );
}
