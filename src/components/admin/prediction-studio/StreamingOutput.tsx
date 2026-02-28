/**
 * Prediction Studio — Streaming Output Panel (Right Side)
 * =========================================================
 * Live streaming area that renders status messages, section headers,
 * and question cards as they arrive from the SSE stream.
 * After generation: switches to review mode.
 */

'use client';

import { useRef, useEffect } from 'react';
import QuestionCard from './QuestionCard';
import type { ReviewableQuestion, QuestionStatus, StudioPhase } from './types';

interface StreamingOutputProps {
  phase: StudioPhase;
  statusMessages: string[];
  questions: ReviewableQuestion[];
  currentSection: string;
  onStatusChange: (qNum: number, status: QuestionStatus) => void;
  onNoteChange: (qNum: number, note: string) => void;
  onRegenerate: (qNum: number) => void;
  regeneratingQ: number | null;
  /** Index up to which typewriter has been applied (for animation sequencing) */
  animatedUpTo: number;
}

export default function StreamingOutput({
  phase,
  statusMessages,
  questions,
  currentSection,
  onStatusChange,
  onNoteChange,
  onRegenerate,
  regeneratingQ,
  animatedUpTo,
}: StreamingOutputProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const isReview = phase === 'review' || phase === 'published';

  // Auto-scroll to bottom during generation
  useEffect(() => {
    if (phase === 'generating' && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [questions.length, statusMessages.length, phase]);

  // Partition questions
  const mainQuestions = questions.filter((q) => !q.is_current_affairs);
  const caQuestions = questions.filter((q) => q.is_current_affairs);

  const acceptedCount = questions.filter((q) => q.status === 'accepted').length;
  const rejectedCount = questions.filter((q) => q.status === 'rejected').length;

  return (
    <div className="glass flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/[0.06] shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-[#f87171] animate-pulse" style={{ animationDuration: phase === 'generating' ? '1s' : '0s', opacity: phase === 'generating' ? 1 : 0.3 }} />
            <h2 className="text-sm font-bold text-white uppercase tracking-[0.1em]">
              {phase === 'configure' && 'Output Preview'}
              {phase === 'generating' && 'Live Generation'}
              {phase === 'review' && 'Review Mode'}
              {phase === 'published' && 'Published ✓'}
            </h2>
          </div>

          {isReview && (
            <div className="flex items-center gap-3 text-[10px] font-bold uppercase tracking-wider">
              <span className="text-[#34d399]">✓ {acceptedCount}</span>
              <span className="text-[#f87171]">✕ {rejectedCount}</span>
              <span className="text-[var(--clr-text-muted)]">
                {questions.length - acceptedCount - rejectedCount} pending
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Scrollable content */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {/* Idle state */}
        {phase === 'configure' && questions.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-20">
            <div className="w-20 h-20 rounded-2xl bg-white/[0.03] flex items-center justify-center mb-5">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--clr-text-muted)" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                <path d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Ready to Generate</h3>
            <p className="text-sm text-[var(--clr-text-muted)] max-w-sm">
              Configure your prediction parameters on the left and click
              <span className="text-[#f87171] font-semibold"> ⚡ Generate</span> to start.
              Questions will appear here in real-time.
            </p>
          </div>
        )}

        {/* Status messages (during generation) */}
        {statusMessages.length > 0 && phase === 'generating' && (
          <div className="space-y-1 mb-3">
            {statusMessages.map((msg, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-xs animate-fade-slide-in"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <span className="w-1 h-1 rounded-full bg-[#f87171] shrink-0" />
                <span className="text-[var(--clr-text-muted)]">{msg}</span>
              </div>
            ))}
          </div>
        )}

        {/* Main Questions Section */}
        {mainQuestions.length > 0 && (
          <>
            <div className="flex items-center gap-3 pt-2 animate-slide-in-left">
              <div className="h-px flex-1 bg-gradient-to-r from-[#a78bfa]/30 to-transparent" />
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#a78bfa]">
                📚 Core Questions ({mainQuestions.length})
              </span>
              <div className="h-px flex-1 bg-gradient-to-l from-[#a78bfa]/30 to-transparent" />
            </div>
            <div className="space-y-3">
              {mainQuestions.map((q, i) => (
                <QuestionCard
                  key={q.question_number}
                  question={q}
                  index={i}
                  isReviewMode={isReview}
                  onStatusChange={onStatusChange}
                  onNoteChange={onNoteChange}
                  onRegenerate={onRegenerate}
                  isRegenerating={regeneratingQ === q.question_number}
                  animateIn={i >= animatedUpTo && phase === 'generating'}
                />
              ))}
            </div>
          </>
        )}

        {/* Current Affairs Section */}
        {caQuestions.length > 0 && (
          <>
            <div className="flex items-center gap-3 pt-4 animate-slide-in-left">
              <div className="h-px flex-1 bg-gradient-to-r from-[#38bdf8]/30 to-transparent" />
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#38bdf8]">
                🌍 Current Affairs ({caQuestions.length})
              </span>
              <div className="h-px flex-1 bg-gradient-to-l from-[#38bdf8]/30 to-transparent" />
            </div>
            <div className="space-y-3">
              {caQuestions.map((q, i) => (
                <QuestionCard
                  key={q.question_number}
                  question={q}
                  index={mainQuestions.length + i}
                  isReviewMode={isReview}
                  onStatusChange={onStatusChange}
                  onNoteChange={onNoteChange}
                  onRegenerate={onRegenerate}
                  isRegenerating={regeneratingQ === q.question_number}
                  animateIn={mainQuestions.length + i >= animatedUpTo && phase === 'generating'}
                />
              ))}
            </div>
          </>
        )}

        {/* Generation complete indicator */}
        {phase === 'generating' && currentSection === 'done' && (
          <div className="flex items-center gap-3 pt-4">
            <div className="h-px flex-1 bg-gradient-to-r from-[#34d399]/30 to-transparent" />
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#34d399]">
              ✓ Generation Complete
            </span>
            <div className="h-px flex-1 bg-gradient-to-l from-[#34d399]/30 to-transparent" />
          </div>
        )}
      </div>
    </div>
  );
}
