/**
 * Prediction Studio — /admin/prediction-studio
 * ================================================
 * AI-powered predicted paper generator with live SSE streaming,
 * typewriter effect, review mode, and publish workflow.
 */

'use client';

import { useState, useCallback, useRef } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/admin/AdminLayout';
import { useAuthStore } from '@/store/auth-store';
import {
  ConfigPanel,
  StreamingOutput,
  ReviewToolbar,
  PublishModal,
} from '@/components/admin/prediction-studio';
import type {
  GenerationConfig,
  ReviewableQuestion,
  QuestionStatus,
  StudioPhase,
  SSEQuestionEvent,
  SSEConfidenceEvent,
  SSECompleteEvent,
} from '@/components/admin/prediction-studio';

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

/* ── Main Component ────────────────────────────── */

function PredictionStudioContent() {
  const session = useAuthStore((s) => s.session);
  const token = session?.access_token;

  // ── Core state ─────────────────────────────────
  const [phase, setPhase] = useState<StudioPhase>('configure');
  const [questions, setQuestions] = useState<ReviewableQuestion[]>([]);
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [currentSection, setCurrentSection] = useState('');
  const [predictionId, setPredictionId] = useState<string | null>(null);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [animatedUpTo, setAnimatedUpTo] = useState(0);
  const [configUsed, setConfigUsed] = useState<GenerationConfig | null>(null);

  // ── Confidence ─────────────────────────────────
  const [confidenceScore, setConfidenceScore] = useState<number | null>(null);
  const [confidenceExplanation, setConfidenceExplanation] = useState('');

  // ── Review / Publish ───────────────────────────
  const [regeneratingQ, setRegeneratingQ] = useState<number | null>(null);
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);

  // ── Error state ────────────────────────────────
  const [error, setError] = useState<string | null>(null);

  // SSE abort
  const abortRef = useRef<AbortController | null>(null);

  // ─────────────────────────────────────────────────
  // SSE Generation Handler
  // ─────────────────────────────────────────────────
  const handleGenerate = useCallback(async (config: GenerationConfig) => {
    if (!token) return;

    // Reset state
    setPhase('generating');
    setQuestions([]);
    setStatusMessages([]);
    setCurrentSection('');
    setPredictionId(null);
    setGenerationProgress(0);
    setAnimatedUpTo(0);
    setConfidenceScore(null);
    setConfidenceExplanation('');
    setError(null);
    setConfigUsed(config);

    // Abort previous if any
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const res = await fetch(`${API}/admin/predictions/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify(config),
        signal: ctrl.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error('No readable stream');

      const decoder = new TextDecoder();
      let buffer = '';
      let questionCount = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let eventType = 'message';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
            continue;
          }
          if (line.startsWith('data: ')) {
            const raw = line.slice(6);
            try {
              const data = JSON.parse(raw);
              handleSSEEvent(eventType, data, questionCount, config.total_questions);
              if (eventType === 'question' || eventType === 'current_affair') {
                questionCount++;
              }
            } catch { /* parse error, skip */ }
            eventType = 'message';
          }
        }
      }

      // If we exit cleanly and phase is still 'generating', switch to review
      setPhase((prev) => (prev === 'generating' ? 'review' : prev));
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      setError(err instanceof Error ? err.message : 'Generation failed');
      setPhase('configure');
    }
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  // ─────────────────────────────────────────────────
  // Process individual SSE events
  // ─────────────────────────────────────────────────
  const handleSSEEvent = (type: string, data: Record<string, unknown>, currentCount: number, totalTarget: number) => {
    switch (type) {
      case 'status': {
        const msg = (data as { message: string }).message;
        setStatusMessages((prev) => [...prev, msg]);
        if (data.progress) setGenerationProgress(data.progress as number);
        if (data.step) setCurrentSection(data.step as string);
        break;
      }
      case 'question':
      case 'current_affair': {
        const q = data as unknown as SSEQuestionEvent;
        const reviewable: ReviewableQuestion = {
          ...q,
          is_current_affairs: type === 'current_affair' || q.is_current_affairs,
          status: 'pending',
          admin_note: '',
        };
        setQuestions((prev) => [...prev, reviewable]);
        // Bump animated marker after a short delay for stagger
        const newCount = currentCount + 1;
        setTimeout(() => setAnimatedUpTo(newCount), 200);
        // Estimate progress
        const pct = Math.min(95, Math.round((newCount / totalTarget) * 100));
        setGenerationProgress(pct);
        break;
      }
      case 'confidence': {
        const c = data as unknown as SSEConfidenceEvent;
        setConfidenceScore(c.confidence_score);
        setConfidenceExplanation(
          c.explanation ||
          `Based on ${c.paper_count_basis} papers, pattern consistency ${(c.pattern_consistency * 100).toFixed(0)}%`
        );
        break;
      }
      case 'complete': {
        const complete = data as unknown as SSECompleteEvent;
        setPredictionId(complete.prediction_id);
        setGenerationProgress(100);
        setCurrentSection('done');
        setStatusMessages((prev) => [...prev, complete.message]);
        if (complete.confidence_score && confidenceScore === null) {
          setConfidenceScore(complete.confidence_score);
        }
        // Small delay then switch to review
        setTimeout(() => setPhase('review'), 800);
        break;
      }
      case 'error': {
        const errMsg = (data as { message: string }).message || 'Generation failed';
        setError(errMsg);
        setPhase('configure');
        break;
      }
    }
  };

  // ─────────────────────────────────────────────────
  // Review actions
  // ─────────────────────────────────────────────────
  const handleStatusChange = useCallback((qNum: number, status: QuestionStatus) => {
    setQuestions((prev) =>
      prev.map((q) =>
        q.question_number === qNum
          ? { ...q, status: q.status === status ? 'pending' : status }
          : q
      )
    );
  }, []);

  const handleNoteChange = useCallback((qNum: number, note: string) => {
    setQuestions((prev) =>
      prev.map((q) =>
        q.question_number === qNum ? { ...q, admin_note: note } : q
      )
    );
  }, []);

  const handleAcceptAll = useCallback(() => {
    setQuestions((prev) =>
      prev.map((q) => (q.status === 'pending' ? { ...q, status: 'accepted' } : q))
    );
  }, []);

  const handleRegenerate = useCallback(async (qNum: number) => {
    // For simplicity, we mark the question as pending and show a regenerating state.
    // In production, this would call a single-question regeneration endpoint.
    setRegeneratingQ(qNum);
    // Simulate a short delay, then just reset to pending
    setTimeout(() => {
      setQuestions((prev) =>
        prev.map((q) =>
          q.question_number === qNum ? { ...q, status: 'pending' } : q
        )
      );
      setRegeneratingQ(null);
    }, 1500);
  }, []);

  const handleNewGeneration = useCallback(() => {
    abortRef.current?.abort();
    setPhase('configure');
    setQuestions([]);
    setStatusMessages([]);
    setCurrentSection('');
    setPredictionId(null);
    setGenerationProgress(0);
    setAnimatedUpTo(0);
    setConfidenceScore(null);
    setConfidenceExplanation('');
    setError(null);
  }, []);

  // ─────────────────────────────────────────────────
  // Publish
  // ─────────────────────────────────────────────────
  const handlePublishConfirm = useCallback(async () => {
    if (!predictionId || !token) return;
    setIsPublishing(true);
    try {
      // First, save the reviewed questions back to the prediction
      const reviewedQuestions = questions.filter((q) => q.status === 'accepted');
      const mainQs = reviewedQuestions.filter((q) => !q.is_current_affairs);
      const caQs = reviewedQuestions.filter((q) => q.is_current_affairs);

      await apiFetch(
        `/admin/predictions/${predictionId}`,
        {
          method: 'PUT',
          body: JSON.stringify({
            questions_json: { questions: mainQs },
            current_affairs_json: { questions: caQs },
          }),
        },
        token,
      );

      // Then publish
      await apiFetch(
        `/admin/predictions/${predictionId}/publish?action=publish`,
        { method: 'POST' },
        token,
      );

      setPhase('published');
      setShowPublishModal(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Publish failed');
    } finally {
      setIsPublishing(false);
    }
  }, [predictionId, token, questions]);

  // ─────────────────────────────────────────────────
  // Resolve job type name from config
  // ─────────────────────────────────────────────────
  const jobTypeName = configUsed?.job_type_id
    ? questions.find((q) => !q.is_current_affairs)?.topic_name || 'Selected Job Type'
    : '';

  return (
    <AdminLayout>
      <div className="flex flex-col h-[calc(100vh-4rem)] max-w-[1600px]">
        {/* Header */}
        <div className="mb-5 shrink-0">
          <h1 className="font-display text-3xl font-bold text-white mb-1">
            Prediction Studio
          </h1>
          <p className="text-[var(--clr-text-secondary)] text-sm">
            AI-powered exam paper generator with live streaming output.
          </p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="glass-sm px-5 py-3 mb-4 border-l-4 border-[var(--clr-danger)] shrink-0">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--clr-danger)] font-semibold">{error}</p>
              </div>
              <button onClick={() => setError(null)} className="text-[var(--clr-text-muted)] hover:text-white text-sm">
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Main layout: Config (left) + Output (right) */}
        <div className="flex-1 grid grid-cols-1 xl:grid-cols-[340px_1fr] gap-5 min-h-0">
          {/* Left: Config Panel */}
          <div className="min-h-0 overflow-y-auto">
            <ConfigPanel
              phase={phase}
              token={token}
              onGenerate={handleGenerate}
              generationProgress={generationProgress}
              confidenceScore={confidenceScore}
              confidenceExplanation={confidenceExplanation}
            />
          </div>

          {/* Right: Streaming Output */}
          <div className="min-h-0 flex flex-col">
            <div className="flex-1 min-h-0">
              <StreamingOutput
                phase={phase}
                statusMessages={statusMessages}
                questions={questions}
                currentSection={currentSection}
                onStatusChange={handleStatusChange}
                onNoteChange={handleNoteChange}
                onRegenerate={handleRegenerate}
                regeneratingQ={regeneratingQ}
                animatedUpTo={animatedUpTo}
              />
            </div>

            {/* Review Toolbar */}
            <div className="mt-3">
              <ReviewToolbar
                phase={phase}
                questions={questions}
                predictionId={predictionId}
                onAcceptAll={handleAcceptAll}
                onPublish={() => setShowPublishModal(true)}
                onNewGeneration={handleNewGeneration}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Publish Modal */}
      <PublishModal
        isOpen={showPublishModal}
        onClose={() => setShowPublishModal(false)}
        onConfirm={handlePublishConfirm}
        isPublishing={isPublishing}
        questionCount={questions.filter((q) => q.status === 'accepted').length}
        jobTypeName={jobTypeName}
      />
    </AdminLayout>
  );
}

export default function PredictionStudioPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <PredictionStudioContent />
    </ProtectedRoute>
  );
}
