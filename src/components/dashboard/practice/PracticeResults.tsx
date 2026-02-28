'use client';

/**
 * PracticeResults — Score display, topic breakdown, wrong answers review.
 * ========================================================================
 * Shown after the practice test is submitted and scored.
 */

import { useState } from 'react';
import Icon from '@/components/Icon';

/* ── Types matching PracticeSubmitResponse ── */

interface TopicPerformance {
  topic_id: string | null;
  topic_name: string;
  correct: number;
  total: number;
  percentage: number;
}

interface WrongAnswer {
  question_id: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  selected_answer: string;
  correct_answer: string;
  topic_name: string | null;
  explanation: string | null;
}

export interface PracticeResultsData {
  test_id: string;
  score: number;
  total: number;
  percentage: number;
  time_taken_seconds: number;
  topic_breakdown: TopicPerformance[];
  wrong_answers: WrongAnswer[];
}

interface PracticeResultsProps {
  results: PracticeResultsData;
  onRetry: () => void;
  onNewTest: () => void;
}

const OPTION_MAP: Record<string, string> = { a: 'A', b: 'B', c: 'C', d: 'D' };

export default function PracticeResults({ results, onRetry, onNewTest }: PracticeResultsProps) {
  const [showWrong, setShowWrong] = useState(false);

  const { score, total, percentage, time_taken_seconds, topic_breakdown, wrong_answers } = results;

  /* ── Grade label ── */
  const grade =
    percentage >= 90 ? { label: 'Excellent!', emoji: '🏆', color: 'var(--clr-gold)' }
    : percentage >= 75 ? { label: 'Great Job!', emoji: '🎯', color: 'var(--clr-success)' }
    : percentage >= 50 ? { label: 'Good Effort', emoji: '💪', color: 'var(--clr-warning)' }
    : { label: 'Keep Practicing', emoji: '📚', color: 'var(--clr-danger)' };

  /* ── Format time ── */
  const formatTime = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    if (mins > 0) return `${mins}m ${secs}s`;
    return `${secs}s`;
  };

  /* ── Get option text ── */
  const getOptionText = (q: WrongAnswer, key: string) => {
    if (key === 'a') return q.option_a;
    if (key === 'b') return q.option_b;
    if (key === 'c') return q.option_c;
    return q.option_d;
  };

  return (
    <div className="flex flex-col gap-8 animate-fade-in-up">
      {/* ═══ Score Hero ═══ */}
      <div className="glass p-8 text-center">
        <div className="text-5xl mb-3">{grade.emoji}</div>

        {/* Animated score ring */}
        <div className="relative inline-flex items-center justify-center w-40 h-40 mb-4">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
            <circle
              cx="60" cy="60" r="52"
              fill="none"
              stroke={grade.color}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${(percentage / 100) * 327} 327`}
              className="practice-score-ring"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-display text-4xl font-black text-white">{Math.round(percentage)}%</span>
            <span className="text-xs text-[var(--clr-text-secondary)]">{score}/{total}</span>
          </div>
        </div>

        <h2 className="font-display text-2xl font-bold" style={{ color: grade.color }}>
          {grade.label}
        </h2>
        <p className="text-sm text-[var(--clr-text-secondary)] mt-1">
          Completed in {formatTime(time_taken_seconds)}
        </p>
      </div>

      {/* ═══ Quick Stats ═══ */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass-sm p-4 text-center">
          <p className="font-display text-2xl font-bold text-[var(--clr-success)]">{score}</p>
          <p className="text-xs text-[var(--clr-text-muted)] mt-1">Correct</p>
        </div>
        <div className="glass-sm p-4 text-center">
          <p className="font-display text-2xl font-bold text-[var(--clr-danger)]">{wrong_answers.length}</p>
          <p className="text-xs text-[var(--clr-text-muted)] mt-1">Wrong</p>
        </div>
        <div className="glass-sm p-4 text-center">
          <p className="font-display text-2xl font-bold text-[var(--clr-primary)]">
            {total > 0 ? Math.round(time_taken_seconds / total) : 0}s
          </p>
          <p className="text-xs text-[var(--clr-text-muted)] mt-1">Avg / Question</p>
        </div>
      </div>

      {/* ═══ Topic Breakdown ═══ */}
      {topic_breakdown.length > 0 && (
        <div className="glass p-6">
          <h3 className="font-display text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Icon name="chart-line" size={18} color="var(--clr-accent)" />
            Topic Breakdown
          </h3>
          <div className="flex flex-col gap-3">
            {topic_breakdown.map((tp) => (
              <div key={tp.topic_name} className="flex items-center gap-3">
                <span className="text-sm text-white flex-1 min-w-0 truncate">{tp.topic_name}</span>
                <span className="text-xs text-[var(--clr-text-muted)] whitespace-nowrap">
                  {tp.correct}/{tp.total}
                </span>
                <div className="w-28 h-2 rounded-full bg-[rgba(255,255,255,0.06)] overflow-hidden shrink-0">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${tp.percentage}%`,
                      background:
                        tp.percentage >= 75 ? 'var(--clr-success)'
                        : tp.percentage >= 50 ? 'var(--clr-warning)'
                        : 'var(--clr-danger)',
                    }}
                  />
                </div>
                <span
                  className="text-sm font-bold w-12 text-right"
                  style={{
                    color:
                      tp.percentage >= 75 ? 'var(--clr-success)'
                      : tp.percentage >= 50 ? 'var(--clr-warning)'
                      : 'var(--clr-danger)',
                  }}
                >
                  {Math.round(tp.percentage)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ Wrong Answers Toggle ═══ */}
      {wrong_answers.length > 0 && (
        <div className="glass p-6">
          <button
            onClick={() => setShowWrong(!showWrong)}
            className="w-full flex items-center justify-between"
          >
            <h3 className="font-display text-lg font-semibold text-white flex items-center gap-2">
              <Icon name="x" size={18} color="var(--clr-danger)" />
              Wrong Answers ({wrong_answers.length})
            </h3>
            <Icon
              name="chevron-right"
              size={18}
              color="var(--clr-text-muted)"
              className={`transition-transform duration-200 ${showWrong ? 'rotate-90' : ''}`}
            />
          </button>

          {showWrong && (
            <div className="mt-4 flex flex-col gap-4">
              {wrong_answers.map((wa, i) => (
                <div key={wa.question_id} className="glass-sm p-5">
                  {/* Question */}
                  <div className="flex items-start gap-3 mb-3">
                    <span className="badge badge-danger text-[10px] shrink-0">Q{i + 1}</span>
                    <p className="text-sm text-white leading-relaxed">{wa.question_text}</p>
                  </div>

                  {/* Topic */}
                  {wa.topic_name && (
                    <span className="badge badge-primary text-[10px] mb-3 inline-flex">
                      {wa.topic_name}
                    </span>
                  )}

                  {/* Answers comparison */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                    {(['a', 'b', 'c', 'd'] as const).map((key) => {
                      const isCorrect = wa.correct_answer.toLowerCase() === key;
                      const isWrong = wa.selected_answer.toLowerCase() === key && !isCorrect;

                      return (
                        <div
                          key={key}
                          className={`px-3 py-2 rounded-lg text-sm flex items-start gap-2
                            ${isCorrect
                              ? 'bg-[var(--clr-success-dim)] border border-[rgba(52,211,153,0.3)]'
                              : isWrong
                                ? 'bg-[var(--clr-danger-dim)] border border-[rgba(248,113,113,0.3)]'
                                : 'bg-[rgba(255,255,255,0.02)] border border-transparent'
                            }`}
                        >
                          <span className={`font-bold shrink-0 ${
                            isCorrect ? 'text-[var(--clr-success)]'
                            : isWrong ? 'text-[var(--clr-danger)]'
                            : 'text-[var(--clr-text-muted)]'
                          }`}>
                            {OPTION_MAP[key]}
                          </span>
                          <span className={
                            isCorrect ? 'text-[var(--clr-success)]'
                            : isWrong ? 'text-[var(--clr-danger)]'
                            : 'text-[var(--clr-text-secondary)]'
                          }>
                            {getOptionText(wa, key)}
                          </span>
                          {isCorrect && <Icon name="check" size={14} color="var(--clr-success)" className="shrink-0 mt-0.5" />}
                          {isWrong && <Icon name="x" size={14} color="var(--clr-danger)" className="shrink-0 mt-0.5" />}
                        </div>
                      );
                    })}
                  </div>

                  {/* Explanation */}
                  {wa.explanation && (
                    <div className="mt-3 p-3 rounded-lg bg-[var(--clr-info-dim)] border border-[rgba(56,189,248,0.15)]">
                      <p className="text-xs text-[var(--clr-info)] flex items-start gap-1.5">
                        <Icon name="sparkles" size={12} className="shrink-0 mt-0.5" />
                        {wa.explanation}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ═══ Action Buttons ═══ */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button onClick={onRetry} className="btn btn-ghost btn-lg flex-1">
          <Icon name="arrow-right" size={18} />
          Retry Same Test
        </button>
        <button onClick={onNewTest} className="btn btn-primary btn-lg flex-1">
          <Icon name="play" size={18} />
          New Practice Test
        </button>
      </div>
    </div>
  );
}
