/**
 * Practice Test Page — /dashboard/practice
 * ==========================================
 * Three-phase flow: Config → Test → Results.
 * Fetches questions from the backend, submits answers for scoring.
 */

'use client';

import { useCallback, useState } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/store/auth-store';
import PracticeConfig from '@/components/dashboard/practice/PracticeConfig';
import PracticeTest, { type PracticeQuestion } from '@/components/dashboard/practice/PracticeTest';
import PracticeResults, { type PracticeResultsData } from '@/components/dashboard/practice/PracticeResults';
import Icon from '@/components/Icon';

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

type Phase = 'config' | 'test' | 'results';

/* ── Types from API ── */

interface GenerateResponse {
  test_id: string;
  questions: PracticeQuestion[];
  total_questions: number;
  time_limit_seconds: number | null;
}

interface AnswerRecord {
  question_id: string;
  selected_answer: string;
}

/* ── Stored config for retry ── */
interface TestConfig {
  topicId: string | null;
  numQuestions: number;
  timed: boolean;
  topicName: string;
}

function PracticeContent() {
  const { session } = useAuthStore();

  const [phase, setPhase] = useState<Phase>('config');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Test state
  const [testId, setTestId] = useState('');
  const [questions, setQuestions] = useState<PracticeQuestion[]>([]);
  const [timeLimitSeconds, setTimeLimitSeconds] = useState<number | null>(null);
  const [results, setResults] = useState<PracticeResultsData | null>(null);
  const [lastConfig, setLastConfig] = useState<TestConfig | null>(null);

  const token = session?.access_token;

  /* ── Generate test ── */
  const handleStart = useCallback(
    async (config: TestConfig) => {
      if (!token) return;
      setLastConfig(config);
      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        if (config.topicId) params.set('topic_id', config.topicId);
        params.set('num_questions', String(config.numQuestions));
        params.set('timed', String(config.timed));

        const res = await fetch(`${API}/student/practice/generate?${params}`, {
          headers: { Authorization: `Bearer ${token}` },
          credentials: 'include',
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
          throw new Error(err.detail || 'Failed to generate test');
        }

        const data: GenerateResponse = await res.json();
        setTestId(data.test_id);
        setQuestions(data.questions);
        setTimeLimitSeconds(data.time_limit_seconds);
        setPhase('test');
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Something went wrong');
      } finally {
        setLoading(false);
      }
    },
    [token],
  );

  /* ── Submit test ── */
  const handleFinish = useCallback(
    async (answers: AnswerRecord[], timeTaken: number) => {
      if (!token) return;
      setLoading(true);
      setError(null);

      try {
        const res = await fetch(`${API}/student/practice/submit`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            test_id: testId,
            answers,
            time_taken_seconds: timeTaken,
          }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
          throw new Error(err.detail || 'Failed to submit test');
        }

        const data: PracticeResultsData = await res.json();
        setResults(data);
        setPhase('results');
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Submission failed');
      } finally {
        setLoading(false);
      }
    },
    [token, testId],
  );

  /* ── Retry same config ── */
  const handleRetry = useCallback(() => {
    if (lastConfig) handleStart(lastConfig);
  }, [lastConfig, handleStart]);

  /* ── New test (back to config) ── */
  const handleNewTest = useCallback(() => {
    setPhase('config');
    setResults(null);
    setError(null);
  }, []);

  /* ── Quit test ── */
  const handleQuit = useCallback(() => {
    if (window.confirm('Are you sure you want to quit? Your progress will be lost.')) {
      setPhase('config');
    }
  }, []);

  return (
    <div className="min-h-screen z-10 relative pt-24 pb-16 px-6">
      <div className="max-w-3xl mx-auto">
        {/* ── Back to Dashboard (config phase only) ── */}
        {phase === 'config' && (
          <a
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-sm text-[var(--clr-text-secondary)]
                       hover:text-white transition-colors mb-6"
          >
            <Icon name="arrow-right" size={14} className="rotate-180" />
            Back to Dashboard
          </a>
        )}

        {/* ── Loading Overlay ── */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-24 gap-4 animate-fade-in">
            <div className="w-14 h-14 rounded-full border-4 border-[var(--clr-primary-dim)]
                            border-t-[var(--clr-primary)] animate-spin" />
            <p className="text-[var(--clr-text-secondary)] text-sm">
              {phase === 'config' ? 'Generating your practice test…' : 'Scoring your answers…'}
            </p>
          </div>
        )}

        {/* ── Error ── */}
        {error && !loading && (
          <div className="glass p-6 text-center mb-6 animate-fade-in-up">
            <div className="w-12 h-12 rounded-full bg-[var(--clr-danger-dim)] flex items-center
                            justify-center mx-auto mb-3">
              <Icon name="x" size={20} color="var(--clr-danger)" />
            </div>
            <p className="text-[var(--clr-danger)] text-sm mb-4">{error}</p>
            <button onClick={() => setError(null)} className="btn btn-ghost btn-sm">
              Dismiss
            </button>
          </div>
        )}

        {/* ── Phase Rendering ── */}
        {!loading && (
          <>
            {phase === 'config' && <PracticeConfig onStart={handleStart} />}
            {phase === 'test' && (
              <PracticeTest
                questions={questions}
                testId={testId}
                timeLimitSeconds={timeLimitSeconds}
                onFinish={handleFinish}
                onQuit={handleQuit}
              />
            )}
            {phase === 'results' && results && (
              <PracticeResults
                results={results}
                onRetry={handleRetry}
                onNewTest={handleNewTest}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function PracticePage() {
  return (
    <ProtectedRoute>
      <PracticeContent />
    </ProtectedRoute>
  );
}
