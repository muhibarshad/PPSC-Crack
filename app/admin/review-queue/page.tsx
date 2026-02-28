/**
 * Admin — Review Queue (/admin/review-queue)
 * ============================================
 * Split-panel view: original scan data (left) | editable fields (right).
 * Lists questions with needs_review=true. Admin can correct, approve, or reject.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/admin/AdminLayout';
import { useAuthStore } from '@/store/auth-store';

/* ── Types ─────────────────────────────────────── */

interface ReviewItem {
  id: string;
  paper_id: string;
  question_number: number;
  question_text: string;
  option_a: string | null;
  option_b: string | null;
  option_c: string | null;
  option_d: string | null;
  correct_answer: string | null;
  topic_id: string | null;
  subtopic: string | null;
  difficulty_score: number;
  fact_extracted: string | null;
  year_appeared: number | null;
  is_repeated: boolean;
  repeat_count: number;
  needs_review: boolean;
  admin_notes: string | null;
  created_at: string;
  paper_title: string;
  paper_year: number;
  paper_month: number | null;
  job_type_name: string | null;
  raw_scan_data: Record<string, unknown> | null;
  topic_name: string | null;
  topic_display_name: string | null;
}

interface Stats {
  total_pending: number;
  total_reviewed: number;
  by_paper: { paper_id: string; title: string; paper_year: number; pending_count: number }[];
}

interface CorrectionForm {
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: string;
  subtopic: string;
  admin_notes: string;
}

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

/* ── Component ─────────────────────────────────── */

function ReviewQueueContent() {
  const session = useAuthStore((s) => s.session);
  const token = session?.access_token;

  // State
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [perPage] = useState(20);

  // Selected question for editing
  const [selected, setSelected] = useState<ReviewItem | null>(null);
  const [form, setForm] = useState<CorrectionForm>({
    question_text: '',
    option_a: '',
    option_b: '',
    option_c: '',
    option_d: '',
    correct_answer: '',
    subtopic: '',
    admin_notes: '',
  });
  const [saving, setSaving] = useState(false);

  /* ── Fetch queue ─────────────────────────────── */
  const fetchQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<{
        items: ReviewItem[];
        total: number;
        page: number;
        per_page: number;
      }>(`/admin/review-queue?page=${page}&per_page=${perPage}`, {}, token);
      setItems(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load review queue');
    } finally {
      setLoading(false);
    }
  }, [token, page, perPage]);

  const fetchStats = useCallback(async () => {
    try {
      const data = await apiFetch<Stats>('/admin/review-queue/stats', {}, token);
      setStats(data);
    } catch {
      // Non-critical, ignore
    }
  }, [token]);

  useEffect(() => {
    fetchQueue();
    fetchStats();
  }, [fetchQueue, fetchStats]);

  // Auto-clear success
  useEffect(() => {
    if (!success) return;
    const t = setTimeout(() => setSuccess(null), 4000);
    return () => clearTimeout(t);
  }, [success]);

  /* ── Select a question for editing ───────────── */
  const selectItem = (item: ReviewItem) => {
    setSelected(item);
    setForm({
      question_text: item.question_text,
      option_a: item.option_a || '',
      option_b: item.option_b || '',
      option_c: item.option_c || '',
      option_d: item.option_d || '',
      correct_answer: item.correct_answer || '',
      subtopic: item.subtopic || '',
      admin_notes: item.admin_notes || '',
    });
  };

  /* ── Save correction ─────────────────────────── */
  const handleSave = async () => {
    if (!selected) return;
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {};
      if (form.question_text !== selected.question_text) payload.question_text = form.question_text;
      if (form.option_a !== (selected.option_a || '')) payload.option_a = form.option_a || null;
      if (form.option_b !== (selected.option_b || '')) payload.option_b = form.option_b || null;
      if (form.option_c !== (selected.option_c || '')) payload.option_c = form.option_c || null;
      if (form.option_d !== (selected.option_d || '')) payload.option_d = form.option_d || null;
      if (form.correct_answer !== (selected.correct_answer || '')) payload.correct_answer = form.correct_answer || null;
      if (form.subtopic !== (selected.subtopic || '')) payload.subtopic = form.subtopic || null;
      if (form.admin_notes) payload.admin_notes = form.admin_notes;

      await apiFetch(
        `/admin/questions/${selected.id}`,
        { method: 'PUT', body: JSON.stringify(payload) },
        token,
      );
      setSuccess('Question corrected & re-embedded ✓');
      setSelected(null);
      fetchQueue();
      fetchStats();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save correction');
    } finally {
      setSaving(false);
    }
  };

  /* ── Quick approve ───────────────────────────── */
  const handleApprove = async (id: string) => {
    try {
      await apiFetch(`/admin/questions/${id}/approve`, { method: 'PUT' }, token);
      setSuccess('Question approved ✓');
      if (selected?.id === id) setSelected(null);
      fetchQueue();
      fetchStats();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to approve');
    }
  };

  /* ── Reject / delete ─────────────────────────── */
  const handleReject = async (id: string) => {
    if (!confirm('Delete this question permanently? This cannot be undone.')) return;
    try {
      await apiFetch(`/admin/questions/${id}`, { method: 'DELETE' }, token);
      setSuccess('Question rejected & deleted ✓');
      if (selected?.id === id) setSelected(null);
      fetchQueue();
      fetchStats();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / perPage));

  /* ── Render ──────────────────────────────────── */
  return (
    <AdminLayout>
      <div className="max-w-[1600px]">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-display text-3xl font-bold text-white mb-1">Review Queue</h1>
            <p className="text-[var(--clr-text-secondary)]">
              Questions flagged for manual correction after AI ingestion.
            </p>
          </div>
          {stats && (
            <div className="flex gap-4">
              <div className="glass px-4 py-2 text-center">
                <p className="text-2xl font-bold text-[var(--clr-warning)]">{stats.total_pending}</p>
                <p className="text-[10px] uppercase tracking-wider text-[var(--clr-text-muted)]">Pending</p>
              </div>
              <div className="glass px-4 py-2 text-center">
                <p className="text-2xl font-bold text-[var(--clr-success)]">{stats.total_reviewed}</p>
                <p className="text-[10px] uppercase tracking-wider text-[var(--clr-text-muted)]">Reviewed</p>
              </div>
            </div>
          )}
        </div>

        {/* Toast messages */}
        {error && (
          <div className="mb-4 p-3 rounded-xl border border-[var(--clr-danger)]/30 bg-[var(--clr-danger)]/10 text-[var(--clr-danger)] text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 rounded-xl border border-[var(--clr-success)]/30 bg-[var(--clr-success)]/10 text-[var(--clr-success)] text-sm">
            {success}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <svg className="animate-spin h-8 w-8 text-primary" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        )}

        {/* Empty state */}
        {!loading && items.length === 0 && (
          <div className="glass p-12 text-center">
            <svg className="mx-auto mb-4 w-16 h-16 text-[var(--clr-success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-xl font-bold text-white mb-2">All Clear!</h2>
            <p className="text-[var(--clr-text-muted)]">No questions need review. The AI pipeline is doing a great job 🎉</p>
          </div>
        )}

        {/* Main split view */}
        {!loading && items.length > 0 && (
          <div className="flex gap-6">
            {/* ── Left: Question list ─────────────── */}
            <div className={`${selected ? 'w-1/2' : 'w-full'} transition-all duration-300`}>
              <div className="space-y-3">
                {items.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => selectItem(item)}
                    className={`glass p-4 cursor-pointer transition-all duration-200 hover:border-[var(--clr-glass-border-hover)] ${
                      selected?.id === item.id
                        ? 'border-[var(--clr-primary)] bg-[var(--clr-primary-dim)]'
                        : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        {/* Paper badge */}
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider bg-white/[0.06] text-[var(--clr-text-muted)]">
                            {item.paper_title} • {item.paper_year}
                          </span>
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider bg-white/[0.06] text-[var(--clr-text-muted)]">
                            Q#{item.question_number}
                          </span>
                          {item.job_type_name && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider bg-[var(--clr-primary-dim)] text-[var(--clr-primary)]">
                              {item.job_type_name}
                            </span>
                          )}
                          {item.topic_display_name && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider bg-[var(--clr-neon)]/10 text-[var(--clr-neon)]">
                              {item.topic_display_name}
                            </span>
                          )}
                        </div>

                        {/* Question text (truncated) */}
                        <p className="text-sm text-white line-clamp-2 mb-2">{item.question_text}</p>

                        {/* Options preview */}
                        <div className="grid grid-cols-2 gap-1 text-xs text-[var(--clr-text-muted)]">
                          {item.option_a && <span className={item.correct_answer === 'a' ? 'text-[var(--clr-success)] font-semibold' : ''}>A) {item.option_a}</span>}
                          {item.option_b && <span className={item.correct_answer === 'b' ? 'text-[var(--clr-success)] font-semibold' : ''}>B) {item.option_b}</span>}
                          {item.option_c && <span className={item.correct_answer === 'c' ? 'text-[var(--clr-success)] font-semibold' : ''}>C) {item.option_c}</span>}
                          {item.option_d && <span className={item.correct_answer === 'd' ? 'text-[var(--clr-success)] font-semibold' : ''}>D) {item.option_d}</span>}
                        </div>
                      </div>

                      {/* Quick actions */}
                      <div className="flex flex-col gap-1.5 shrink-0">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleApprove(item.id); }}
                          title="Approve as-is"
                          className="w-8 h-8 rounded-lg bg-[var(--clr-success)]/10 text-[var(--clr-success)] hover:bg-[var(--clr-success)]/20 flex items-center justify-center transition-colors"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M5 13l4 4L19 7" />
                          </svg>
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleReject(item.id); }}
                          title="Reject & delete"
                          className="w-8 h-8 rounded-lg bg-[var(--clr-danger)]/10 text-[var(--clr-danger)] hover:bg-[var(--clr-danger)]/20 flex items-center justify-center transition-colors"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-6">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="px-3 py-1.5 rounded-lg text-sm font-medium glass disabled:opacity-40 hover:bg-white/[0.06] transition-colors"
                  >
                    ← Prev
                  </button>
                  <span className="text-sm text-[var(--clr-text-muted)]">
                    Page {page} of {totalPages} ({total} questions)
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="px-3 py-1.5 rounded-lg text-sm font-medium glass disabled:opacity-40 hover:bg-white/[0.06] transition-colors"
                  >
                    Next →
                  </button>
                </div>
              )}
            </div>

            {/* ── Right: Edit panel ───────────────── */}
            {selected && (
              <div className="w-1/2 sticky top-0 max-h-[calc(100vh-6rem)] overflow-y-auto">
                <div className="glass p-6">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-lg font-bold text-white">
                        Edit Question #{selected.question_number}
                      </h2>
                      <p className="text-xs text-[var(--clr-text-muted)]">
                        {selected.paper_title} • {selected.paper_year}
                        {selected.job_type_name ? ` • ${selected.job_type_name}` : ''}
                      </p>
                    </div>
                    <button
                      onClick={() => setSelected(null)}
                      className="w-8 h-8 rounded-lg hover:bg-white/[0.06] flex items-center justify-center text-[var(--clr-text-muted)] hover:text-white transition-colors"
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>

                  {/* Raw scan data (if available) */}
                  {selected.raw_scan_data && (
                    <div className="mb-6 p-4 rounded-xl bg-[var(--clr-bg-deep)] border border-white/[0.04]">
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--clr-text-muted)] mb-2">
                        Original Scan Data
                      </h3>
                      <pre className="text-xs text-[var(--clr-text-secondary)] whitespace-pre-wrap break-words max-h-40 overflow-y-auto font-mono">
                        {JSON.stringify(selected.raw_scan_data, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Editable fields */}
                  <div className="space-y-4">
                    {/* Question text */}
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--clr-text-muted)] mb-1.5">
                        Question Text
                      </label>
                      <textarea
                        value={form.question_text}
                        onChange={(e) => setForm((f) => ({ ...f, question_text: e.target.value }))}
                        rows={3}
                        className="w-full px-3 py-2 rounded-xl bg-[var(--clr-bg-deep)] border border-white/[0.08] text-white text-sm placeholder:text-[var(--clr-text-muted)] focus:outline-none focus:border-[var(--clr-primary)] transition-colors resize-none"
                      />
                    </div>

                    {/* Options grid */}
                    <div className="grid grid-cols-2 gap-3">
                      {(['a', 'b', 'c', 'd'] as const).map((opt) => {
                        const key = `option_${opt}` as keyof CorrectionForm;
                        return (
                          <div key={opt}>
                            <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--clr-text-muted)] mb-1.5">
                              Option {opt.toUpperCase()}
                              {form.correct_answer === opt && (
                                <span className="ml-1 text-[var(--clr-success)]">✓ correct</span>
                              )}
                            </label>
                            <input
                              type="text"
                              value={form[key]}
                              onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                              className="w-full px-3 py-2 rounded-xl bg-[var(--clr-bg-deep)] border border-white/[0.08] text-white text-sm placeholder:text-[var(--clr-text-muted)] focus:outline-none focus:border-[var(--clr-primary)] transition-colors"
                            />
                          </div>
                        );
                      })}
                    </div>

                    {/* Correct answer selector */}
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--clr-text-muted)] mb-1.5">
                        Correct Answer
                      </label>
                      <div className="flex gap-2">
                        {['a', 'b', 'c', 'd'].map((opt) => (
                          <button
                            key={opt}
                            onClick={() => setForm((f) => ({ ...f, correct_answer: opt }))}
                            className={`w-10 h-10 rounded-xl text-sm font-bold transition-all duration-200 ${
                              form.correct_answer === opt
                                ? 'bg-[var(--clr-success)] text-white shadow-[0_0_12px_rgba(34,197,94,0.4)]'
                                : 'bg-[var(--clr-bg-deep)] border border-white/[0.08] text-[var(--clr-text-muted)] hover:border-[var(--clr-success)]/50 hover:text-white'
                            }`}
                          >
                            {opt.toUpperCase()}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Subtopic */}
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--clr-text-muted)] mb-1.5">
                        Subtopic
                      </label>
                      <input
                        type="text"
                        value={form.subtopic}
                        onChange={(e) => setForm((f) => ({ ...f, subtopic: e.target.value }))}
                        placeholder="e.g., Constitutional Amendments"
                        className="w-full px-3 py-2 rounded-xl bg-[var(--clr-bg-deep)] border border-white/[0.08] text-white text-sm placeholder:text-[var(--clr-text-muted)] focus:outline-none focus:border-[var(--clr-primary)] transition-colors"
                      />
                    </div>

                    {/* Admin notes */}
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--clr-text-muted)] mb-1.5">
                        Admin Notes
                      </label>
                      <textarea
                        value={form.admin_notes}
                        onChange={(e) => setForm((f) => ({ ...f, admin_notes: e.target.value }))}
                        rows={2}
                        placeholder="Optional review notes..."
                        className="w-full px-3 py-2 rounded-xl bg-[var(--clr-bg-deep)] border border-white/[0.08] text-white text-sm placeholder:text-[var(--clr-text-muted)] focus:outline-none focus:border-[var(--clr-primary)] transition-colors resize-none"
                      />
                    </div>

                    {/* Metadata display */}
                    <div className="p-3 rounded-xl bg-[var(--clr-bg-deep)] border border-white/[0.04]">
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--clr-text-muted)] mb-2">
                        Metadata
                      </h3>
                      <div className="grid grid-cols-2 gap-2 text-xs text-[var(--clr-text-secondary)]">
                        <div>Topic: <span className="text-white">{selected.topic_display_name || 'Unclassified'}</span></div>
                        <div>Difficulty: <span className="text-white">{(selected.difficulty_score * 100).toFixed(0)}%</span></div>
                        <div>Year: <span className="text-white">{selected.year_appeared || '—'}</span></div>
                        <div>Repeated: <span className="text-white">{selected.is_repeated ? `Yes (${selected.repeat_count}×)` : 'No'}</span></div>
                        {selected.fact_extracted && (
                          <div className="col-span-2">Fact: <span className="text-white">{selected.fact_extracted}</span></div>
                        )}
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex gap-3 pt-2">
                      <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex-1 px-4 py-2.5 rounded-xl bg-gradient-to-r from-primary-vivid to-neon text-white font-semibold text-sm shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:shadow-[0_0_28px_rgba(139,92,246,0.5)] transition-all duration-200 disabled:opacity-50"
                      >
                        {saving ? 'Saving...' : 'Save & Approve'}
                      </button>
                      <button
                        onClick={() => handleApprove(selected.id)}
                        className="px-4 py-2.5 rounded-xl border border-[var(--clr-success)]/30 text-[var(--clr-success)] font-semibold text-sm hover:bg-[var(--clr-success)]/10 transition-all duration-200"
                      >
                        Approve As-Is
                      </button>
                      <button
                        onClick={() => handleReject(selected.id)}
                        className="px-4 py-2.5 rounded-xl border border-[var(--clr-danger)]/30 text-[var(--clr-danger)] font-semibold text-sm hover:bg-[var(--clr-danger)]/10 transition-all duration-200"
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AdminLayout>
  );
}

export default function ReviewQueuePage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <ReviewQueueContent />
    </ProtectedRoute>
  );
}
