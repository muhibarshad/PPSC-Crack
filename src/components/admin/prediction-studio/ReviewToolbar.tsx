/**
 * Prediction Studio — Review Toolbar
 * =====================================
 * Bottom toolbar with bulk actions and publish button.
 */

'use client';

import type { ReviewableQuestion, StudioPhase } from './types';

interface ReviewToolbarProps {
  phase: StudioPhase;
  questions: ReviewableQuestion[];
  predictionId: string | null;
  onAcceptAll: () => void;
  onPublish: () => void;
  onNewGeneration: () => void;
}

export default function ReviewToolbar({
  phase,
  questions,
  predictionId,
  onAcceptAll,
  onPublish,
  onNewGeneration,
}: ReviewToolbarProps) {
  if (phase !== 'review' && phase !== 'published') return null;

  const acceptedCount = questions.filter((q) => q.status === 'accepted').length;
  const rejectedCount = questions.filter((q) => q.status === 'rejected').length;
  const pendingCount = questions.length - acceptedCount - rejectedCount;
  const allReviewed = pendingCount === 0;

  return (
    <div className="glass-sm px-6 py-3 flex items-center justify-between gap-4 shrink-0">
      <div className="flex items-center gap-4">
        {/* Stats */}
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#34d399]" />
            <span className="text-[#34d399] font-bold">{acceptedCount}</span>
            <span className="text-[var(--clr-text-muted)]">accepted</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#f87171]" />
            <span className="text-[#f87171] font-bold">{rejectedCount}</span>
            <span className="text-[var(--clr-text-muted)]">rejected</span>
          </span>
          {pendingCount > 0 && (
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[var(--clr-text-muted)]" />
              <span className="text-[var(--clr-text-muted)] font-bold">{pendingCount}</span>
              <span className="text-[var(--clr-text-muted)]">pending</span>
            </span>
          )}
        </div>

        {/* Bulk actions */}
        {phase === 'review' && (
          <>
            <div className="w-px h-5 bg-white/[0.06]" />
            <button
              onClick={onAcceptAll}
              className="px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider bg-[rgba(52,211,153,0.08)] text-[#34d399] hover:bg-[rgba(52,211,153,0.15)] transition-all"
            >
              ✓ Accept All Pending
            </button>
          </>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* New Generation */}
        <button
          onClick={onNewGeneration}
          className="px-4 py-2 rounded-xl text-xs font-bold text-[var(--clr-text-secondary)] hover:text-white bg-white/[0.03] hover:bg-white/[0.06] transition-all"
        >
          ↻ New Generation
        </button>

        {/* Publish */}
        {phase === 'review' && predictionId && (
          <button
            onClick={onPublish}
            disabled={!allReviewed}
            className="px-5 py-2 rounded-xl text-xs font-bold text-white transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed"
            style={{
              background: allReviewed
                ? 'linear-gradient(135deg, #f87171 0%, #ef4444 100%)'
                : 'rgba(248, 113, 113, 0.15)',
              boxShadow: allReviewed ? '0 0 25px rgba(248, 113, 113, 0.3)' : 'none',
            }}
          >
            🚀 Publish to Students
          </button>
        )}

        {phase === 'published' && (
          <span className="px-4 py-2 rounded-xl text-xs font-bold text-[#34d399] bg-[rgba(52,211,153,0.1)] border border-[rgba(52,211,153,0.2)]">
            ✓ Published
          </span>
        )}
      </div>
    </div>
  );
}
