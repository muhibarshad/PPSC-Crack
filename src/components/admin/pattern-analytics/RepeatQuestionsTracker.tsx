/**
 * Repeat Questions Tracker — sortable table of repeated questions.
 */

'use client';

import { useState } from 'react';
import type { RepeatQuestion, RepeatQuestionsResponse } from './types';

interface Props {
  data: RepeatQuestionsResponse | null;
  loading?: boolean;
  onPageChange?: (page: number) => void;
}

export default function RepeatQuestionsTracker({ data, loading, onPageChange }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="glass rounded-2xl p-6">
        <div className="h-6 w-56 bg-white/5 rounded-lg animate-pulse mb-6" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-14 bg-white/[0.02] rounded-xl mb-2 animate-pulse" />
        ))}
      </div>
    );
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const page = data?.page ?? 1;
  const perPage = data?.per_page ?? 30;
  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-display font-bold text-white">Repeat Questions Tracker</h3>
        <span className="text-xs text-[var(--clr-text-muted)] bg-white/5 px-3 py-1 rounded-full">
          {total} repeated questions
        </span>
      </div>

      {items.length === 0 ? (
        <div className="h-[200px] flex items-center justify-center text-[var(--clr-text-muted)] text-sm">
          No repeated questions detected yet.
        </div>
      ) : (
        <>
          {/* Table header */}
          <div className="grid grid-cols-[1fr_140px_80px_80px_80px] gap-3 px-4 py-2 text-[10px] uppercase tracking-[0.12em] font-semibold text-[var(--clr-text-muted)] border-b border-white/[0.06]">
            <span>Question</span>
            <span>Topic</span>
            <span className="text-center">Repeats</span>
            <span className="text-center">Year</span>
            <span className="text-center">Difficulty</span>
          </div>

          {/* Rows */}
          <div className="divide-y divide-white/[0.04]">
            {items.map((q) => (
              <div key={q.id}>
                <button
                  onClick={() => setExpandedId(expandedId === q.id ? null : q.id)}
                  className="w-full grid grid-cols-[1fr_140px_80px_80px_80px] gap-3 px-4 py-3 text-left hover:bg-white/[0.02] transition-colors rounded-lg"
                >
                  <span className="text-sm text-[var(--clr-text-secondary)] truncate">
                    {q.question_text}
                  </span>
                  <span className="inline-flex items-center">
                    <span className="badge-info text-[10px] truncate max-w-[130px]">
                      {q.topic_display_name}
                    </span>
                  </span>
                  <span className="text-center">
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-lg text-xs font-bold ${
                      q.repeat_count >= 5
                        ? 'bg-red-500/15 text-red-400 border border-red-500/20'
                        : q.repeat_count >= 3
                        ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20'
                        : 'bg-white/5 text-[var(--clr-text-secondary)] border border-white/10'
                    }`}>
                      {q.repeat_count}
                    </span>
                  </span>
                  <span className="text-center text-xs text-[var(--clr-text-muted)] tabular-nums">
                    {q.year_appeared ?? '—'}
                  </span>
                  <span className="text-center">
                    <DifficultyDot score={q.difficulty_score} />
                  </span>
                </button>

                {/* Expanded detail */}
                {expandedId === q.id && (
                  <div className="px-4 pb-4 pl-8">
                    <div className="glass-sm rounded-xl p-4 text-sm space-y-2">
                      <p className="text-[var(--clr-text-secondary)] leading-relaxed">
                        {q.question_text}
                      </p>
                      {q.fact_extracted && (
                        <p className="text-xs text-[var(--clr-text-muted)]">
                          <span className="font-semibold text-[var(--clr-primary)]">Fact: </span>
                          {q.fact_extracted}
                        </p>
                      )}
                      {q.similarity_group_id && (
                        <p className="text-[10px] text-[var(--clr-text-muted)] font-mono">
                          Group: {q.similarity_group_id.slice(0, 8)}…
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/[0.06]">
              <span className="text-xs text-[var(--clr-text-muted)]">
                Page {page} of {totalPages}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => onPageChange?.(page - 1)}
                  disabled={page <= 1}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 hover:bg-white/10 text-[var(--clr-text-secondary)] disabled:opacity-30 disabled:pointer-events-none transition-colors"
                >
                  ← Prev
                </button>
                <button
                  onClick={() => onPageChange?.(page + 1)}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 hover:bg-white/10 text-[var(--clr-text-secondary)] disabled:opacity-30 disabled:pointer-events-none transition-colors"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ── Difficulty dot ──────────────────────────── */

function DifficultyDot({ score }: { score: number }) {
  const label = score >= 0.7 ? 'Hard' : score >= 0.4 ? 'Med' : 'Easy';
  const cls =
    score >= 0.7
      ? 'bg-red-500/15 text-red-400 border-red-500/20'
      : score >= 0.4
      ? 'bg-amber-500/15 text-amber-400 border-amber-500/20'
      : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20';

  return (
    <span className={`inline-flex items-center justify-center px-2 py-0.5 rounded-md text-[10px] font-semibold border ${cls}`}>
      {label}
    </span>
  );
}
