/**
 * LatestPredictionCard — Shows the most recently published predicted paper.
 * Only visible to premium users.
 */

'use client';

import { useRouter } from 'next/navigation';
import Icon from '@/components/Icon';

interface LatestPredictionCardProps {
  title: string;
  predictionDate: string;
  confidenceScore: number;
  totalQuestions: number;
  jobTypeName: string;
}

export default function LatestPredictionCard({
  title,
  predictionDate,
  confidenceScore,
  totalQuestions,
  jobTypeName,
}: LatestPredictionCardProps) {
  const router = useRouter();
  const formattedDate = new Date(predictionDate).toLocaleDateString('en-PK', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  const confidenceColor =
    confidenceScore >= 80
      ? 'var(--clr-success)'
      : confidenceScore >= 60
        ? 'var(--clr-gold)'
        : 'var(--clr-warning)';

  return (
    <div className="glow-card p-6 flex flex-col gap-4 flex-1 min-w-[260px] group">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--clr-gold-dim)' }}
          >
            <Icon name="sparkles" size={20} color="var(--clr-gold)" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-[var(--clr-text-muted)]">
              Predicted Paper
            </p>
            <h3 className="font-display text-lg font-bold text-white leading-snug line-clamp-1">
              {title}
            </h3>
          </div>
        </div>
        <span className="badge badge-gold text-[10px]">⭐ Premium</span>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-6 mt-auto">
        <div>
          <p className="text-2xl font-bold" style={{ color: confidenceColor }}>
            {confidenceScore}%
          </p>
          <p className="text-[11px] text-[var(--clr-text-muted)]">Confidence</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-white">{totalQuestions}</p>
          <p className="text-[11px] text-[var(--clr-text-muted)]">Questions</p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-sm text-[var(--clr-text-secondary)]">{jobTypeName}</p>
          <p className="text-[11px] text-[var(--clr-text-muted)]">{formattedDate}</p>
        </div>
      </div>

      {/* CTA */}
      <button onClick={() => router.push('/dashboard/predicted-paper')} className="btn btn-gold btn-sm w-full mt-1">
        <Icon name="file-text" size={14} />
        Practice Paper
        <Icon name="arrow-right" size={14} />
      </button>
    </div>
  );
}
