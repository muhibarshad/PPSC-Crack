/**
 * Prediction Studio — Question Card
 * ====================================
 * Displays a single predicted MCQ with review controls.
 * Admin can accept/reject, add notes, view details.
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import type { ReviewableQuestion, QuestionStatus } from './types';

interface QuestionCardProps {
  question: ReviewableQuestion;
  index: number;
  isReviewMode: boolean;
  onStatusChange: (qNum: number, status: QuestionStatus) => void;
  onNoteChange: (qNum: number, note: string) => void;
  onRegenerate: (qNum: number) => void;
  isRegenerating: boolean;
  /** Controls typewriter animation */
  animateIn: boolean;
}

const OPTION_LABELS = ['A', 'B', 'C', 'D'] as const;

function DifficultyDots({ score }: { score: number }) {
  const dots = Math.max(1, Math.min(5, Math.round(score * 5)));
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((d) => (
        <span
          key={d}
          className="w-1.5 h-1.5 rounded-full"
          style={{
            background: d <= dots ? (dots <= 2 ? '#34d399' : dots <= 3 ? '#fbbf24' : '#f87171') : 'rgba(255,255,255,0.08)',
          }}
        />
      ))}
    </div>
  );
}

export default function QuestionCard({
  question,
  index,
  isReviewMode,
  onStatusChange,
  onNoteChange,
  onRegenerate,
  isRegenerating,
  animateIn,
}: QuestionCardProps) {
  const [showNote, setShowNote] = useState(false);
  const [displayedText, setDisplayedText] = useState('');
  const [typewriterDone, setTypewriterDone] = useState(!animateIn);
  const cardRef = useRef<HTMLDivElement>(null);

  // Typewriter effect for question_text
  useEffect(() => {
    if (!animateIn) {
      setDisplayedText(question.question_text);
      setTypewriterDone(true);
      return;
    }
    setDisplayedText('');
    setTypewriterDone(false);
    const text = question.question_text;
    let i = 0;
    const speed = Math.max(8, Math.min(25, 800 / text.length)); // adaptive speed
    const timer = setInterval(() => {
      i++;
      setDisplayedText(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(timer);
        setTypewriterDone(true);
      }
    }, speed);
    return () => clearInterval(timer);
  }, [question.question_text, animateIn]);

  // Fade-in animation after typewriter completes
  useEffect(() => {
    if (typewriterDone && cardRef.current && animateIn) {
      cardRef.current.style.opacity = '1';
      cardRef.current.style.transform = 'translateY(0)';
    }
  }, [typewriterDone, animateIn]);

  const options = [
    { key: 'a', label: 'A', text: question.option_a },
    { key: 'b', label: 'B', text: question.option_b },
    { key: 'c', label: 'C', text: question.option_c },
    { key: 'd', label: 'D', text: question.option_d },
  ];

  const statusBorder =
    question.status === 'accepted'
      ? 'border-l-[#34d399]'
      : question.status === 'rejected'
        ? 'border-l-[#f87171]'
        : 'border-l-transparent';

  return (
    <div
      ref={cardRef}
      className={`glass-sm p-5 border-l-4 ${statusBorder} transition-all duration-500`}
      style={animateIn ? { opacity: 0, transform: 'translateY(12px)' } : {}}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2.5">
          <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-white/[0.06] text-[11px] font-bold text-[var(--clr-text-muted)] tabular-nums">
            {question.question_number}
          </span>
          <span
            className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md"
            style={{
              color: question.is_current_affairs ? '#38bdf8' : '#a78bfa',
              background: question.is_current_affairs ? 'rgba(56,189,248,0.1)' : 'rgba(139,92,246,0.1)',
            }}
          >
            {question.is_current_affairs ? 'Current Affairs' : question.topic_name}
          </span>
          {question.subtopic && (
            <span className="text-[10px] text-[var(--clr-text-muted)]">
              · {question.subtopic}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <DifficultyDots score={question.difficulty_score} />
          <span className="text-[10px] text-[var(--clr-text-muted)] tabular-nums">
            {(question.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Question text with typewriter */}
      <p className="text-sm text-white leading-relaxed mb-3 min-h-[1.4em]">
        {displayedText}
        {!typewriterDone && <span className="inline-block w-0.5 h-4 bg-[#f87171] animate-pulse ml-0.5 align-text-bottom" />}
      </p>

      {/* Options */}
      {typewriterDone && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
          {options.map((opt) => (
            <div
              key={opt.key}
              className={`flex items-start gap-2 px-3 py-2 rounded-lg text-xs transition-colors ${
                opt.key === question.correct_answer
                  ? 'bg-[rgba(52,211,153,0.08)] border border-[rgba(52,211,153,0.2)]'
                  : 'bg-white/[0.02] border border-white/[0.04]'
              }`}
            >
              <span
                className={`font-bold shrink-0 ${
                  opt.key === question.correct_answer ? 'text-[#34d399]' : 'text-[var(--clr-text-muted)]'
                }`}
              >
                {opt.label}.
              </span>
              <span className={opt.key === question.correct_answer ? 'text-[#34d399]' : 'text-[var(--clr-text-secondary)]'}>
                {opt.text}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Fact basis */}
      {typewriterDone && question.fact_basis && (
        <p className="text-[10px] text-[var(--clr-text-muted)] italic mb-3 px-1">
          💡 {question.fact_basis}
        </p>
      )}

      {/* Review controls */}
      {isReviewMode && typewriterDone && (
        <div className="flex items-center gap-2 pt-2 border-t border-white/[0.04]">
          <button
            onClick={() => onStatusChange(question.question_number, 'accepted')}
            className={`px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all duration-200 ${
              question.status === 'accepted'
                ? 'bg-[rgba(52,211,153,0.15)] text-[#34d399] border border-[rgba(52,211,153,0.3)]'
                : 'bg-white/[0.03] text-[var(--clr-text-muted)] hover:bg-[rgba(52,211,153,0.08)] hover:text-[#34d399]'
            }`}
          >
            ✓ Accept
          </button>
          <button
            onClick={() => onStatusChange(question.question_number, 'rejected')}
            className={`px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all duration-200 ${
              question.status === 'rejected'
                ? 'bg-[rgba(248,113,113,0.15)] text-[#f87171] border border-[rgba(248,113,113,0.3)]'
                : 'bg-white/[0.03] text-[var(--clr-text-muted)] hover:bg-[rgba(248,113,113,0.08)] hover:text-[#f87171]'
            }`}
          >
            ✕ Reject
          </button>

          {question.status === 'rejected' && (
            <button
              onClick={() => onRegenerate(question.question_number)}
              disabled={isRegenerating}
              className="px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider bg-[rgba(251,191,36,0.1)] text-[#fbbf24] hover:bg-[rgba(251,191,36,0.15)] transition-all disabled:opacity-40"
            >
              {isRegenerating ? '⟳ Replacing…' : '↻ Replace'}
            </button>
          )}

          <button
            onClick={() => setShowNote(!showNote)}
            className="ml-auto px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider bg-white/[0.03] text-[var(--clr-text-muted)] hover:text-white transition-all"
          >
            📝 Note
          </button>
        </div>
      )}

      {/* Admin note input */}
      {showNote && (
        <div className="mt-3">
          <textarea
            value={question.admin_note}
            onChange={(e) => onNoteChange(question.question_number, e.target.value)}
            placeholder="Add a note about this question…"
            rows={2}
            className="w-full rounded-lg bg-[var(--clr-bg-elevated)] border border-[var(--clr-glass-border)] px-3 py-2 text-xs text-white placeholder:text-[var(--clr-text-muted)] focus:outline-none focus:border-[var(--clr-primary-vivid)] resize-none transition-colors"
          />
        </div>
      )}
    </div>
  );
}
