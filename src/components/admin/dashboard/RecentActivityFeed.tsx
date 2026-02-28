/**
 * Recent Activity Feed
 * =====================
 * Last 5 ingestion events with status badges and timestamps.
 */

'use client';

import type { RecentActivityItem } from './types';

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: string }> = {
  completed: {
    label: 'Complete',
    color: '#34d399',
    bg: 'rgba(52, 211, 153, 0.10)',
    icon: '✓',
  },
  processing: {
    label: 'Processing',
    color: '#fbbf24',
    bg: 'rgba(251, 191, 36, 0.10)',
    icon: '⟳',
  },
  pending: {
    label: 'Pending',
    color: '#818cf8',
    bg: 'rgba(129, 140, 248, 0.10)',
    icon: '◷',
  },
  failed: {
    label: 'Error',
    color: '#f87171',
    bg: 'rgba(248, 113, 113, 0.10)',
    icon: '✕',
  },
};

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function RecentActivityFeed({ items }: { items: RecentActivityItem[] }) {
  if (items.length === 0) {
    return (
      <div className="glass p-6 flex items-center justify-center">
        <p className="text-sm text-[var(--clr-text-muted)]">No recent activity.</p>
      </div>
    );
  }

  return (
    <div className="glass p-5">
      <h2 className="text-sm font-bold text-white uppercase tracking-[0.1em] mb-4">
        Recent Activity
      </h2>

      <div className="space-y-2">
        {items.map((item, i) => {
          const cfg = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending;
          return (
            <div
              key={item.paper_id}
              className="flex items-center gap-4 px-4 py-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors duration-200"
            >
              {/* Status icon */}
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
                style={{ color: cfg.color, background: cfg.bg }}
              >
                {cfg.icon}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{item.title}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[11px] text-[var(--clr-text-muted)]">{item.job_type_name}</span>
                  <span className="text-[var(--clr-text-muted)]">·</span>
                  <span className="text-[11px] text-[var(--clr-text-muted)]">{item.total_questions} Qs</span>
                </div>
              </div>

              {/* Status + Time */}
              <div className="text-right shrink-0">
                <span
                  className="inline-block px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider"
                  style={{ color: cfg.color, background: cfg.bg }}
                >
                  {cfg.label}
                </span>
                <p className="text-[10px] text-[var(--clr-text-muted)] mt-1">
                  {formatRelativeTime(item.created_at)}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
