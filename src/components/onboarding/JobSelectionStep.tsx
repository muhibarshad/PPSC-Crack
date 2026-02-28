'use client';

/**
 * Step 1: Job Selection — Full-screen grid of job type cards with multi-select + search.
 */

import { useState, useMemo } from 'react';
import Icon from '@/components/Icon';

/* ── Icons per department / job keyword ── */
const JOB_ICONS: Record<string, string> = {
  clerk: 'file-text',
  asi: 'shield',
  inspector: 'shield',
  tehsildar: 'settings',
  teacher: 'book-open',
  lecturer: 'book-open',
  accountant: 'credit-card',
  stenographer: 'file-text',
  default: 'target',
};

function getJobIcon(name: string): string {
  const lower = name.toLowerCase();
  for (const [key, icon] of Object.entries(JOB_ICONS)) {
    if (lower.includes(key)) return icon;
  }
  return JOB_ICONS.default;
}

export interface JobType {
  id: string;
  name: string;
  slug: string;
  department: string | null;
  total_papers: number;
  is_active: boolean;
}

interface Props {
  jobTypes: JobType[];
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
  onNext: () => void;
  loading?: boolean;
}

export default function JobSelectionStep({
  jobTypes,
  selectedIds,
  onSelectionChange,
  onNext,
  loading = false,
}: Props) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!search.trim()) return jobTypes;
    const q = search.toLowerCase();
    return jobTypes.filter(
      (j) =>
        j.name.toLowerCase().includes(q) ||
        (j.department && j.department.toLowerCase().includes(q)),
    );
  }, [jobTypes, search]);

  const toggle = (id: string) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((x) => x !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  return (
    <div className="animate-fade-in-up">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6"
          style={{ background: 'var(--clr-primary-dim)', border: '1px solid rgba(139,92,246,0.2)' }}>
          <Icon name="target" size={14} color="var(--clr-primary)" />
          <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--clr-primary)' }}>
            Step 1 of 3
          </span>
        </div>
        <h1 className="font-display text-4xl md:text-5xl font-bold mb-4" style={{ color: 'var(--clr-text-primary)' }}>
          Choose Your <span className="gradient-text">Target Jobs</span>
        </h1>
        <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--clr-text-secondary)' }}>
          Select the PPSC positions you&apos;re preparing for. Our AI will customize your entire experience.
        </p>
      </div>

      {/* Search */}
      <div className="max-w-md mx-auto mb-8">
        <div className="relative">
          <Icon name="sparkles" size={18} color="var(--clr-text-muted)"
            className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search job types..."
            className="w-full pl-12 pr-4 py-3 rounded-2xl text-sm outline-none transition-all"
            style={{
              background: 'var(--clr-glass-bg)',
              border: '1px solid var(--clr-glass-border)',
              color: 'var(--clr-text-primary)',
              backdropFilter: 'blur(16px)',
            }}
            onFocus={(e) => (e.target.style.borderColor = 'rgba(139,92,246,0.4)')}
            onBlur={(e) => (e.target.style.borderColor = 'var(--clr-glass-border)')}
          />
        </div>
      </div>

      {/* Selection count */}
      {selectedIds.length > 0 && (
        <div className="text-center mb-6 animate-fade-in">
          <span className="badge badge-primary">
            {selectedIds.length} job{selectedIds.length !== 1 ? 's' : ''} selected
          </span>
        </div>
      )}

      {/* Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 mb-10">
        {filtered.map((job, i) => {
          const selected = selectedIds.includes(job.id);
          return (
            <button
              key={job.id}
              onClick={() => toggle(job.id)}
              className="group relative text-left p-5 rounded-2xl transition-all"
              style={{
                animationDelay: `${i * 50}ms`,
                background: selected
                  ? 'linear-gradient(135deg, rgba(139,92,246,0.2) 0%, rgba(99,102,241,0.1) 100%)'
                  : 'var(--clr-glass-bg)',
                border: selected
                  ? '2px solid rgba(139,92,246,0.5)'
                  : '1px solid var(--clr-glass-border)',
                backdropFilter: 'blur(16px)',
                boxShadow: selected ? 'var(--shadow-glow)' : 'var(--shadow-sm)',
                transform: selected ? 'translateY(-4px)' : 'translateY(0)',
              }}
            >
              {/* Check indicator */}
              {selected && (
                <div className="absolute top-3 right-3 w-6 h-6 rounded-full flex items-center justify-center"
                  style={{ background: 'var(--grad-primary)' }}>
                  <Icon name="check" size={12} color="white" />
                </div>
              )}

              {/* Icon */}
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-3"
                style={{
                  background: selected ? 'var(--clr-primary-dim)' : 'rgba(139,92,246,0.06)',
                  border: '1px solid rgba(139,92,246,0.15)',
                }}
              >
                <Icon
                  name={getJobIcon(job.name)}
                  size={22}
                  color={selected ? 'var(--clr-primary)' : 'var(--clr-text-muted)'}
                />
              </div>

              {/* Info */}
              <h3
                className="font-display text-sm font-semibold mb-1 line-clamp-2"
                style={{ color: selected ? 'var(--clr-text-primary)' : 'var(--clr-text-secondary)' }}
              >
                {job.name}
              </h3>
              {job.department && (
                <p className="text-xs truncate" style={{ color: 'var(--clr-text-muted)' }}>
                  {job.department}
                </p>
              )}
              <p className="text-xs mt-2" style={{ color: 'var(--clr-text-muted)' }}>
                {job.total_papers} papers
              </p>
            </button>
          );
        })}
      </div>

      {/* Empty state */}
      {filtered.length === 0 && (
        <div className="text-center py-16">
          <Icon name="sparkles" size={48} color="var(--clr-text-muted)" className="mx-auto mb-4" />
          <p style={{ color: 'var(--clr-text-secondary)' }}>No job types match &ldquo;{search}&rdquo;</p>
        </div>
      )}

      {/* CTA */}
      <div className="text-center">
        <button
          onClick={onNext}
          disabled={selectedIds.length === 0 || loading}
          className="btn btn-primary btn-lg"
          style={{
            opacity: selectedIds.length === 0 ? 0.4 : 1,
            cursor: selectedIds.length === 0 ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? (
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <>
              Analyze My Jobs
              <Icon name="arrow-right" size={18} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
