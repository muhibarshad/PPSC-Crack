/**
 * Predicted Paper Page — /dashboard/predicted-paper
 * ===================================================
 * Premium feature that displays AI-predicted exam papers in realistic format.
 *
 * Two modes:
 *  • Exam Mode  — timed, answers hidden until submission, scored at end
 *  • Study Mode — click to reveal correct answer per question
 *
 * Post-exam: score, topic breakdown, probability badges.
 */

'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/store/auth-store';
import Icon from '@/components/Icon';

/* ═══════════════════════════════════════════
   Types
   ═══════════════════════════════════════════ */

interface PredictedQuestion {
  question_number: number;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: string; // a | b | c | d
  topic_name: string;
  subtopic: string | null;
  difficulty_score: number;
  confidence: number;
  is_current_affairs: boolean;
  probability: number; // percentage from topic frequency
}

interface TopicDistribution {
  topic_name: string;
  question_count: number;
  probability: number;
}

interface PredictionData {
  id: string;
  title: string;
  job_type_id: string;
  job_type_name: string | null;
  prediction_date: string;
  total_questions: number;
  confidence_score: number;
  paper_count_basis: number;
  pattern_consistency: number;
  published_at: string | null;
  questions: PredictedQuestion[];
  topic_distribution: TopicDistribution[];
  time_limit_minutes: number;
}

type Phase = 'loading' | 'upgrade' | 'mode-select' | 'exam' | 'study' | 'results';

/* ═══════════════════════════════════════════
   API
   ═══════════════════════════════════════════ */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function fetchLatestPrediction(token: string): Promise<PredictionData> {
  const res = await fetch(`${API}/student/predictions/latest`, {
    headers: { Authorization: `Bearer ${token}` },
    credentials: 'include',
  });
  if (res.status === 403) {
    const body = await res.json().catch(() => ({}));
    if (body?.detail?.upgrade_required) {
      throw { upgradeRequired: true };
    }
    throw new Error(body?.detail?.message || 'Access denied');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || 'Failed to load prediction');
  }
  return res.json();
}

/* ═══════════════════════════════════════════
   Helpers
   ═══════════════════════════════════════════ */

const OPTION_LABELS = ['A', 'B', 'C', 'D'] as const;
const OPTION_KEYS = ['a', 'b', 'c', 'd'] as const;

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function probabilityBadgeColor(p: number): string {
  if (p >= 15) return 'var(--clr-danger)';
  if (p >= 10) return 'var(--clr-gold)';
  if (p >= 5) return 'var(--clr-success)';
  return 'var(--clr-text-muted)';
}

function probabilityLabel(p: number): string {
  if (p >= 15) return 'Very Likely';
  if (p >= 10) return 'Likely';
  if (p >= 5) return 'Moderate';
  return 'Low';
}

/* ═══════════════════════════════════════════
   Sub-Components
   ═══════════════════════════════════════════ */

/* ── Upgrade Prompt ── */
function UpgradePrompt() {
  const router = useRouter();
  return (
    <div className="min-h-screen z-10 relative pt-24 px-6">
      <div className="max-w-lg mx-auto py-20">
        <div className="glass p-10 text-center">
          <div className="w-20 h-20 rounded-2xl bg-[var(--clr-gold-dim)] flex items-center justify-center mx-auto mb-6">
            <Icon name="lock" size={36} color="var(--clr-gold)" />
          </div>
          <h1 className="font-display text-3xl font-bold text-white mb-3">
            Premium Feature
          </h1>
          <p className="text-[var(--clr-text-secondary)] mb-2 leading-relaxed">
            AI-Predicted Papers are available exclusively for Premium members.
          </p>
          <p className="text-sm text-[var(--clr-text-muted)] mb-8">
            Get exam papers generated from 500+ past PPSC paper patterns, complete with
            probability scores for every question type.
          </p>

          <div className="flex flex-col gap-3">
            <button className="btn btn-gold w-full text-base py-3">
              <Icon name="star" size={18} />
              Upgrade to Premium
            </button>
            <button
              onClick={() => router.push('/dashboard')}
              className="btn btn-ghost w-full"
            >
              Back to Dashboard
            </button>
          </div>

          {/* Feature list */}
          <div className="mt-8 text-left space-y-3">
            {[
              'AI-predicted exam papers based on real patterns',
              'Exam & Study mode with instant scoring',
              'Topic probability badges for smart preparation',
              'Unlimited practice on predicted questions',
            ].map((feat, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-[var(--clr-gold-dim)] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Icon name="check" size={12} color="var(--clr-gold)" />
                </div>
                <span className="text-sm text-[var(--clr-text-secondary)]">{feat}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Paper Header (realistic PPSC branding) ── */
function PaperHeader({
  data,
  mode,
}: {
  data: PredictionData;
  mode: 'exam' | 'study';
}) {
  const formattedDate = new Date(data.prediction_date).toLocaleDateString('en-PK', {
    month: 'long',
    year: 'numeric',
  });

  return (
    <div className="glass p-6 sm:p-8 text-center border-b-2 border-[var(--clr-primary-dim)]">
      {/* Top bar */}
      <div className="flex items-center justify-between mb-4">
        <span className="badge badge-gold text-[10px]">⭐ AI Predicted</span>
        <span
          className="badge text-[10px]"
          style={{
            background: mode === 'exam' ? 'var(--clr-danger-dim)' : 'var(--clr-success-dim)',
            color: mode === 'exam' ? 'var(--clr-danger)' : 'var(--clr-success)',
          }}
        >
          {mode === 'exam' ? '⏱ Exam Mode' : '📖 Study Mode'}
        </span>
      </div>

      {/* PPSC-style header */}
      <div className="space-y-1">
        <p className="text-xs uppercase tracking-[0.3em] text-[var(--clr-text-muted)]">
          Punjab Public Service Commission
        </p>
        <h1 className="font-display text-2xl sm:text-3xl font-bold text-white">
          {data.title}
        </h1>
        {data.job_type_name && (
          <p className="text-[var(--clr-primary)] font-medium">{data.job_type_name}</p>
        )}
        <p className="text-sm text-[var(--clr-text-muted)]">
          Predicted for {formattedDate} • {data.total_questions} Questions
        </p>
      </div>

      {/* Confidence bar */}
      <div className="mt-4 flex items-center justify-center gap-4 text-xs">
        <span className="text-[var(--clr-text-muted)]">
          Confidence:{' '}
          <strong className="text-[var(--clr-gold)]">{data.confidence_score.toFixed(0)}%</strong>
        </span>
        <span className="text-[var(--clr-glass-border)]">|</span>
        <span className="text-[var(--clr-text-muted)]">
          Based on <strong className="text-white">{data.paper_count_basis}</strong> past papers
        </span>
      </div>
    </div>
  );
}

/* ── Single question component ── */
function QuestionCard({
  q,
  index,
  selectedAnswer,
  onSelect,
  showAnswer,
  showProbability,
}: {
  q: PredictedQuestion;
  index: number;
  selectedAnswer: string | null;
  onSelect: (key: string) => void;
  showAnswer: boolean;
  showProbability: boolean;
}) {
  const optionFields = [q.option_a, q.option_b, q.option_c, q.option_d];

  return (
    <div className="glass p-5 sm:p-6 hover:border-[var(--clr-glass-border-hover)] transition-all">
      {/* Question header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3 flex-1">
          <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-[var(--clr-primary-dim)] flex items-center justify-center text-sm font-bold text-[var(--clr-primary)]">
            {q.question_number}
          </span>
          <p className="text-white font-medium leading-relaxed pt-1">{q.question_text}</p>
        </div>

        {/* Probability badge */}
        {showProbability && q.probability > 0 && (
          <div
            className="flex-shrink-0 flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-bold"
            style={{
              background: `color-mix(in srgb, ${probabilityBadgeColor(q.probability)} 15%, transparent)`,
              color: probabilityBadgeColor(q.probability),
            }}
            title={`${probabilityLabel(q.probability)} — ${q.probability}% of paper typically covers this topic`}
          >
            <Icon name="target" size={10} />
            {q.probability}%
          </div>
        )}
      </div>

      {/* Topic tag */}
      <div className="flex items-center gap-2 mb-4 ml-11">
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--clr-glass-bg)] text-[var(--clr-text-muted)]">
          {q.topic_name}
        </span>
        {q.is_current_affairs && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--clr-info-dim)] text-[var(--clr-info)]">
            Current Affairs
          </span>
        )}
      </div>

      {/* Options */}
      <div className="grid gap-2 ml-11">
        {OPTION_LABELS.map((label, oi) => {
          const key = OPTION_KEYS[oi];
          const isSelected = selectedAnswer === key;
          const isCorrect = q.correct_answer === key;

          let optionStyle = '';
          if (showAnswer) {
            if (isCorrect) {
              optionStyle =
                'border-[var(--clr-success)] bg-[var(--clr-success-dim)] text-[var(--clr-success)]';
            } else if (isSelected && !isCorrect) {
              optionStyle =
                'border-[var(--clr-danger)] bg-[var(--clr-danger-dim)] text-[var(--clr-danger)]';
            }
          } else if (isSelected) {
            optionStyle =
              'border-[var(--clr-primary)] bg-[var(--clr-primary-dim)] text-[var(--clr-primary)]';
          }

          return (
            <button
              key={key}
              onClick={() => onSelect(key)}
              disabled={showAnswer}
              className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all text-sm ${
                optionStyle ||
                'border-[var(--clr-glass-border)] hover:border-[var(--clr-glass-border-hover)] hover:bg-[var(--clr-glass-bg-hover)] text-[var(--clr-text-secondary)]'
              }`}
            >
              <span
                className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold"
                style={{
                  background: isSelected
                    ? 'var(--clr-primary-dim)'
                    : 'var(--clr-glass-bg)',
                  color: isSelected
                    ? 'var(--clr-primary)'
                    : 'var(--clr-text-muted)',
                }}
              >
                {label}
              </span>
              <span className="flex-1">{optionFields[oi]}</span>
              {showAnswer && isCorrect && <Icon name="check" size={16} color="var(--clr-success)" />}
              {showAnswer && isSelected && !isCorrect && (
                <Icon name="x" size={16} color="var(--clr-danger)" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Mode Select Screen
   ═══════════════════════════════════════════ */

function ModeSelectScreen({
  data,
  onSelect,
  onBack,
}: {
  data: PredictionData;
  onSelect: (mode: 'exam' | 'study') => void;
  onBack: () => void;
}) {
  const formattedDate = new Date(data.prediction_date).toLocaleDateString('en-PK', {
    month: 'long',
    year: 'numeric',
  });

  return (
    <div className="min-h-screen z-10 relative pt-24 pb-16 px-6">
      <div className="max-w-2xl mx-auto flex flex-col gap-8 animate-fade-in-up">
        {/* Back */}
        <button onClick={onBack} className="btn btn-ghost btn-sm w-fit">
          ← Back to Dashboard
        </button>

        {/* Card */}
        <div className="glass p-8 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[var(--clr-gold-dim)] flex items-center justify-center mx-auto mb-4">
            <Icon name="sparkles" size={32} color="var(--clr-gold)" />
          </div>
          <h1 className="font-display text-3xl font-bold text-white mb-2">
            {data.title}
          </h1>
          <p className="text-[var(--clr-primary)] font-medium mb-1">
            {data.job_type_name}
          </p>
          <p className="text-sm text-[var(--clr-text-muted)] mb-6">
            {data.total_questions} Questions • Predicted for {formattedDate}
          </p>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            {[
              { label: 'Confidence', value: `${data.confidence_score.toFixed(0)}%`, icon: 'target' },
              { label: 'Past Papers', value: data.paper_count_basis, icon: 'file-text' },
              {
                label: 'Consistency',
                value: `${(data.pattern_consistency * 100).toFixed(0)}%`,
                icon: 'chart-line',
              },
            ].map((stat, i) => (
              <div key={i} className="glass p-3 text-center">
                <Icon name={stat.icon} size={16} className="mx-auto mb-1 text-[var(--clr-primary)]" />
                <p className="text-lg font-bold text-white">{stat.value}</p>
                <p className="text-[10px] text-[var(--clr-text-muted)] uppercase tracking-wider">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>

          {/* Mode buttons */}
          <div className="grid sm:grid-cols-2 gap-4">
            <button
              onClick={() => onSelect('exam')}
              className="glass p-6 text-left hover:border-[var(--clr-danger)] transition-all group"
            >
              <div className="w-12 h-12 rounded-xl bg-[var(--clr-danger-dim)] flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Icon name="zap" size={24} color="var(--clr-danger)" />
              </div>
              <h3 className="font-display text-lg font-bold text-white mb-1">
                Exam Mode
              </h3>
              <p className="text-xs text-[var(--clr-text-muted)] leading-relaxed">
                Timed test. Answers revealed only after you submit. Get your score
                with a full topic breakdown.
              </p>
              <p className="text-[10px] text-[var(--clr-danger)] mt-2 font-medium">
                ⏱ {data.time_limit_minutes} minutes
              </p>
            </button>

            <button
              onClick={() => onSelect('study')}
              className="glass p-6 text-left hover:border-[var(--clr-success)] transition-all group"
            >
              <div className="w-12 h-12 rounded-xl bg-[var(--clr-success-dim)] flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Icon name="book-open" size={24} color="var(--clr-success)" />
              </div>
              <h3 className="font-display text-lg font-bold text-white mb-1">
                Study Mode
              </h3>
              <p className="text-xs text-[var(--clr-text-muted)] leading-relaxed">
                No time pressure. Click any option to instantly reveal the correct
                answer. Learn at your own pace.
              </p>
              <p className="text-[10px] text-[var(--clr-success)] mt-2 font-medium">
                📖 Untimed — reveal on click
              </p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Exam / Study Mode Screen
   ═══════════════════════════════════════════ */

function ExamScreen({
  data,
  mode,
  onFinish,
  onQuit,
}: {
  data: PredictionData;
  mode: 'exam' | 'study';
  onFinish: (answers: Record<number, string>, timeTaken: number) => void;
  onQuit: () => void;
}) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [revealedQuestions, setRevealedQuestions] = useState<Set<number>>(new Set());
  const [timeLeft, setTimeLeft] = useState(data.time_limit_minutes * 60);
  const [showConfirmSubmit, setShowConfirmSubmit] = useState(false);
  const startTimeRef = useRef(Date.now());

  // Timer (exam mode only)
  useEffect(() => {
    if (mode !== 'exam') return;
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          // Auto-submit
          const timeTaken = Math.floor((Date.now() - startTimeRef.current) / 1000);
          onFinish(answers, timeTaken);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [mode]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSelect = useCallback(
    (qNum: number, key: string) => {
      if (mode === 'study') {
        // In study mode, selecting reveals the answer
        setAnswers((prev) => ({ ...prev, [qNum]: key }));
        setRevealedQuestions((prev) => new Set(prev).add(qNum));
      } else {
        // Exam mode: just record the answer
        setAnswers((prev) => ({ ...prev, [qNum]: key }));
      }
    },
    [mode],
  );

  const handleSubmit = () => {
    const timeTaken = Math.floor((Date.now() - startTimeRef.current) / 1000);
    onFinish(answers, timeTaken);
  };

  const answeredCount = Object.keys(answers).length;
  const progress = (answeredCount / data.total_questions) * 100;

  const timeWarning = mode === 'exam' && timeLeft < 300; // last 5 minutes

  return (
    <div className="min-h-screen z-10 relative pt-20 pb-32 px-4 sm:px-6">
      <div className="max-w-4xl mx-auto flex flex-col gap-6">
        {/* Paper header */}
        <PaperHeader data={data} mode={mode} />

        {/* Sticky toolbar */}
        <div className="sticky top-0 z-30 glass p-3 sm:p-4 flex items-center justify-between gap-4 backdrop-blur-xl">
          <div className="flex items-center gap-4">
            <button onClick={onQuit} className="btn btn-ghost btn-sm">
              ← Quit
            </button>
            <span className="text-xs text-[var(--clr-text-muted)]">
              {answeredCount}/{data.total_questions} answered
            </span>
          </div>

          {/* Progress bar */}
          <div className="hidden sm:block flex-1 max-w-xs">
            <div className="h-1.5 rounded-full bg-[var(--clr-glass-bg)] overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${progress}%`,
                  background: 'var(--clr-primary)',
                }}
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Timer (exam only) */}
            {mode === 'exam' && (
              <span
                className={`font-mono text-sm font-bold ${
                  timeWarning ? 'text-[var(--clr-danger)] animate-pulse' : 'text-white'
                }`}
              >
                ⏱ {formatTime(timeLeft)}
              </span>
            )}

            {/* Submit (exam) */}
            {mode === 'exam' && (
              <button
                onClick={() => setShowConfirmSubmit(true)}
                className="btn btn-primary btn-sm"
              >
                Submit Paper
              </button>
            )}
          </div>
        </div>

        {/* Questions */}
        <div className="flex flex-col gap-4">
          {data.questions.map((q, i) => (
            <QuestionCard
              key={q.question_number}
              q={q}
              index={i}
              selectedAnswer={answers[q.question_number] ?? null}
              onSelect={(key) => handleSelect(q.question_number, key)}
              showAnswer={mode === 'study' ? revealedQuestions.has(q.question_number) : false}
              showProbability={mode === 'study'}
            />
          ))}
        </div>

        {/* Bottom submit bar for exam */}
        {mode === 'exam' && (
          <div className="glass p-4 text-center">
            <button
              onClick={() => setShowConfirmSubmit(true)}
              className="btn btn-primary px-12 py-3"
            >
              <Icon name="check" size={18} />
              Submit Paper ({answeredCount}/{data.total_questions} answered)
            </button>
          </div>
        )}

        {/* Study mode: back button */}
        {mode === 'study' && (
          <div className="glass p-4 text-center">
            <button onClick={onQuit} className="btn btn-ghost">
              ← Back to Mode Selection
            </button>
          </div>
        )}
      </div>

      {/* Confirm submit modal */}
      {showConfirmSubmit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
          <div className="glass p-8 max-w-md w-full text-center">
            <div className="w-14 h-14 rounded-full bg-[var(--clr-primary-dim)] flex items-center justify-center mx-auto mb-4">
              <Icon name="file-text" size={24} color="var(--clr-primary)" />
            </div>
            <h2 className="font-display text-xl font-bold text-white mb-2">
              Submit Paper?
            </h2>
            <p className="text-sm text-[var(--clr-text-secondary)] mb-1">
              You've answered <strong className="text-white">{answeredCount}</strong> of{' '}
              <strong className="text-white">{data.total_questions}</strong> questions.
            </p>
            {answeredCount < data.total_questions && (
              <p className="text-xs text-[var(--clr-warning)] mb-4">
                ⚠ {data.total_questions - answeredCount} question(s) unanswered — they'll be marked wrong.
              </p>
            )}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowConfirmSubmit(false)}
                className="btn btn-ghost flex-1"
              >
                Keep Working
              </button>
              <button onClick={handleSubmit} className="btn btn-primary flex-1">
                Submit Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   Results Screen
   ═══════════════════════════════════════════ */

function ResultsScreen({
  data,
  answers,
  timeTaken,
  onRetry,
  onStudy,
  onBack,
}: {
  data: PredictionData;
  answers: Record<number, string>;
  timeTaken: number;
  onRetry: () => void;
  onStudy: () => void;
  onBack: () => void;
}) {
  // Calculate score
  const { score, correct, wrong, unanswered, topicBreakdown } = useMemo(() => {
    let correct = 0;
    let wrong = 0;
    let unanswered = 0;

    const tbMap: Record<
      string,
      { topic_name: string; correct: number; total: number; probability: number }
    > = {};

    for (const q of data.questions) {
      const userAnswer = answers[q.question_number];
      const isCorrect = userAnswer === q.correct_answer;
      const tn = q.topic_name || 'Uncategorized';

      if (!tbMap[tn]) {
        tbMap[tn] = { topic_name: tn, correct: 0, total: 0, probability: q.probability };
      }
      tbMap[tn].total += 1;

      if (!userAnswer) {
        unanswered++;
      } else if (isCorrect) {
        correct++;
        tbMap[tn].correct += 1;
      } else {
        wrong++;
      }
    }

    const score = data.total_questions > 0 ? (correct / data.total_questions) * 100 : 0;

    return {
      score,
      correct,
      wrong,
      unanswered,
      topicBreakdown: Object.values(tbMap).sort((a, b) => b.total - a.total),
    };
  }, [data, answers]);

  const scoreColor =
    score >= 70
      ? 'var(--clr-success)'
      : score >= 50
        ? 'var(--clr-gold)'
        : 'var(--clr-danger)';

  return (
    <div className="min-h-screen z-10 relative pt-24 pb-16 px-6">
      <div className="max-w-3xl mx-auto flex flex-col gap-8 animate-fade-in-up">
        {/* Score card */}
        <div className="glass p-8 text-center">
          <p className="text-xs uppercase tracking-[0.3em] text-[var(--clr-text-muted)] mb-4">
            Your Score
          </p>
          <div
            className="text-6xl font-display font-bold mb-2"
            style={{ color: scoreColor }}
          >
            {score.toFixed(0)}%
          </div>
          <p className="text-[var(--clr-text-secondary)] mb-6">
            {correct} correct out of {data.total_questions} questions
          </p>

          {/* Stats row */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Correct', value: correct, color: 'var(--clr-success)' },
              { label: 'Wrong', value: wrong, color: 'var(--clr-danger)' },
              { label: 'Skipped', value: unanswered, color: 'var(--clr-text-muted)' },
              { label: 'Time', value: formatTime(timeTaken), color: 'var(--clr-info)' },
            ].map((s, i) => (
              <div key={i} className="glass p-3 text-center">
                <p className="text-xl font-bold" style={{ color: s.color }}>
                  {s.value}
                </p>
                <p className="text-[10px] text-[var(--clr-text-muted)] uppercase tracking-wider">
                  {s.label}
                </p>
              </div>
            ))}
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-3 justify-center">
            <button onClick={onStudy} className="btn btn-primary">
              <Icon name="book-open" size={16} />
              Review in Study Mode
            </button>
            <button onClick={onRetry} className="btn btn-ghost">
              <Icon name="zap" size={16} />
              Retry Exam
            </button>
            <button onClick={onBack} className="btn btn-ghost">
              ← Dashboard
            </button>
          </div>
        </div>

        {/* Topic Breakdown */}
        <div className="glass p-6">
          <h2 className="font-display text-xl font-bold text-white mb-4">
            Topic Breakdown
          </h2>
          <div className="space-y-3">
            {topicBreakdown.map((t, i) => {
              const pct = t.total > 0 ? (t.correct / t.total) * 100 : 0;
              const barColor =
                pct >= 70 ? 'var(--clr-success)' : pct >= 50 ? 'var(--clr-gold)' : 'var(--clr-danger)';

              return (
                <div key={i} className="glass p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">{t.topic_name}</span>
                      {/* Probability badge */}
                      {t.probability > 0 && (
                        <span
                          className="text-[10px] px-1.5 py-0.5 rounded-full font-bold"
                          style={{
                            background: `color-mix(in srgb, ${probabilityBadgeColor(t.probability)} 15%, transparent)`,
                            color: probabilityBadgeColor(t.probability),
                          }}
                        >
                          {t.probability}% likely
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-[var(--clr-text-muted)]">
                      {t.correct}/{t.total} correct
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full bg-[var(--clr-glass-bg)] overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, background: barColor }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Detailed answer review */}
        <div className="glass p-6">
          <h2 className="font-display text-xl font-bold text-white mb-4">
            Answer Review
          </h2>
          <div className="space-y-3">
            {data.questions.map((q) => {
              const userAnswer = answers[q.question_number];
              const isCorrect = userAnswer === q.correct_answer;
              const statusColor = !userAnswer
                ? 'var(--clr-text-muted)'
                : isCorrect
                  ? 'var(--clr-success)'
                  : 'var(--clr-danger)';

              return (
                <div
                  key={q.question_number}
                  className="flex items-center gap-3 p-3 rounded-xl"
                  style={{ background: 'var(--clr-glass-bg)' }}
                >
                  <span
                    className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold"
                    style={{ background: `color-mix(in srgb, ${statusColor} 15%, transparent)`, color: statusColor }}
                  >
                    {q.question_number}
                  </span>
                  <p className="flex-1 text-sm text-[var(--clr-text-secondary)] line-clamp-1">
                    {q.question_text}
                  </p>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {/* Probability badge */}
                    {q.probability > 0 && (
                      <span
                        className="text-[9px] px-1.5 py-0.5 rounded-full font-bold"
                        style={{
                          background: `color-mix(in srgb, ${probabilityBadgeColor(q.probability)} 15%, transparent)`,
                          color: probabilityBadgeColor(q.probability),
                        }}
                      >
                        {q.probability}%
                      </span>
                    )}
                    {!userAnswer ? (
                      <span className="text-[10px] text-[var(--clr-text-muted)]">Skipped</span>
                    ) : isCorrect ? (
                      <Icon name="check" size={14} color="var(--clr-success)" />
                    ) : (
                      <div className="flex items-center gap-1">
                        <span className="text-[10px] text-[var(--clr-danger)] line-through">
                          {userAnswer.toUpperCase()}
                        </span>
                        <span className="text-[10px] text-[var(--clr-success)] font-bold">
                          {q.correct_answer.toUpperCase()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Main Page Component
   ═══════════════════════════════════════════ */

function PredictedPaperContent() {
  const router = useRouter();
  const { session } = useAuthStore();

  const [phase, setPhase] = useState<Phase>('loading');
  const [data, setData] = useState<PredictionData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [examAnswers, setExamAnswers] = useState<Record<number, string>>({});
  const [examTimeTaken, setExamTimeTaken] = useState(0);

  // Fetch prediction on mount
  const loadData = useCallback(async () => {
    const token = session?.access_token;
    if (!token) return;

    setPhase('loading');
    setError(null);

    try {
      const result = await fetchLatestPrediction(token);
      setData(result);
      setPhase('mode-select');
    } catch (err: any) {
      if (err?.upgradeRequired) {
        setPhase('upgrade');
        return;
      }
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setPhase('loading');
    }
  }, [session?.access_token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Phase handlers
  const handleModeSelect = (mode: 'exam' | 'study') => {
    setPhase(mode);
  };

  const handleFinishExam = (answers: Record<number, string>, timeTaken: number) => {
    setExamAnswers(answers);
    setExamTimeTaken(timeTaken);
    setPhase('results');
  };

  const handleRetryExam = () => {
    setExamAnswers({});
    setExamTimeTaken(0);
    setPhase('exam');
  };

  const handleStudyFromResults = () => {
    setPhase('study');
  };

  const handleQuit = () => {
    setPhase('mode-select');
  };

  const handleBack = () => {
    router.push('/dashboard');
  };

  /* ── Render ── */

  // Loading
  if (phase === 'loading' && !error) {
    return (
      <div className="min-h-screen z-10 relative pt-24 px-6">
        <div className="max-w-5xl mx-auto flex flex-col items-center justify-center gap-6 py-32">
          <div className="w-16 h-16 rounded-full border-4 border-[var(--clr-primary-dim)] border-t-[var(--clr-primary)] animate-spin" />
          <p className="text-[var(--clr-text-secondary)] text-sm">Loading predicted paper…</p>
        </div>
      </div>
    );
  }

  // Error
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
            <div className="flex gap-3 justify-center">
              <button onClick={loadData} className="btn btn-primary">Try Again</button>
              <button onClick={handleBack} className="btn btn-ghost">Dashboard</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Upgrade prompt for free users
  if (phase === 'upgrade') {
    return <UpgradePrompt />;
  }

  // Mode selection
  if (phase === 'mode-select' && data) {
    return <ModeSelectScreen data={data} onSelect={handleModeSelect} onBack={handleBack} />;
  }

  // Exam mode
  if (phase === 'exam' && data) {
    return (
      <ExamScreen
        data={data}
        mode="exam"
        onFinish={handleFinishExam}
        onQuit={handleQuit}
      />
    );
  }

  // Study mode
  if (phase === 'study' && data) {
    return (
      <ExamScreen
        data={data}
        mode="study"
        onFinish={() => {}}
        onQuit={handleQuit}
      />
    );
  }

  // Results
  if (phase === 'results' && data) {
    return (
      <ResultsScreen
        data={data}
        answers={examAnswers}
        timeTaken={examTimeTaken}
        onRetry={handleRetryExam}
        onStudy={handleStudyFromResults}
        onBack={handleBack}
      />
    );
  }

  return null;
}

/* ── Page Export ── */

export default function PredictedPaperPage() {
  return (
    <ProtectedRoute>
      <PredictedPaperContent />
    </ProtectedRoute>
  );
}
