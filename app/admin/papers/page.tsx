/**
 * Admin Papers Library — /admin/papers
 * =======================================
 * Searchable, filterable grid of all uploaded papers.
 * Clicking a paper opens a detail drawer with questions table.
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/admin/AdminLayout';
import { useAuthStore } from '@/store/auth-store';

/* ── Types ─────────────────────────────────────── */

interface TopicPill {
  id: string;
  name: string;
  display_name: string;
  color_hex: string | null;
}

interface PaperCard {
  id: string;
  title: string;
  paper_year: number;
  paper_month: number | null;
  paper_date: string | null;
  total_questions: number;
  ingestion_status: string;
  repeat_questions_count: number;
  job_type_id: string;
  job_type_name: string;
  job_type_slug: string;
  topics: TopicPill[];
  topics_total: number;
  source: string | null;
  created_at: string;
  updated_at: string | null;
}

interface PapersListResponse {
  papers: PaperCard[];
  total: number;
  page: number;
  per_page: number;
}

interface QuestionInPaper {
  id: string;
  question_number: number;
  question_text: string;
  option_a: string | null;
  option_b: string | null;
  option_c: string | null;
  option_d: string | null;
  correct_answer: string | null;
  topic_id: string | null;
  topic_name: string | null;
  subtopic: string | null;
  difficulty_score: number;
  fact_extracted: string | null;
  is_repeated: boolean;
  repeat_count: number;
  needs_review: boolean;
  admin_notes: string | null;
  created_at: string;
}

interface PaperDetail {
  id: string;
  title: string;
  paper_year: number;
  paper_month: number | null;
  paper_date: string | null;
  total_questions: number;
  ingestion_status: string;
  source: string | null;
  job_type_id: string;
  job_type_name: string;
  job_type_slug: string;
  topics: TopicPill[];
  questions: QuestionInPaper[];
  questions_total: number;
  questions_page: number;
  questions_per_page: number;
  repeat_questions_count: number;
  created_at: string;
  updated_at: string | null;
}

interface JobType {
  id: string;
  name: string;
  slug: string;
}

/* ── API Helper ────────────────────────────────── */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function apiFetch<T = unknown>(path: string, token?: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { headers, credentials: 'include', ...options });
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Status Badge ──────────────────────────────── */

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  pending: { label: 'Pending', color: '#fb923c', bg: 'rgba(251,146,60,0.12)', border: 'rgba(251,146,60,0.25)' },
  processing: { label: 'Processing', color: '#38bdf8', bg: 'rgba(56,189,248,0.12)', border: 'rgba(56,189,248,0.25)' },
  completed: { label: 'Complete', color: '#34d399', bg: 'rgba(52,211,153,0.12)', border: 'rgba(52,211,153,0.25)' },
  failed: { label: 'Error', color: '#f87171', bg: 'rgba(248,113,113,0.12)', border: 'rgba(248,113,113,0.25)' },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
      style={{ color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: cfg.color }} />
      {cfg.label}
    </span>
  );
}

/* ── Job Type Color Map ────────────────────────── */

const JOB_TYPE_COLORS = [
  { bg: 'rgba(139,92,246,0.15)', color: '#a78bfa', border: 'rgba(139,92,246,0.3)' },
  { bg: 'rgba(56,189,248,0.15)', color: '#38bdf8', border: 'rgba(56,189,248,0.3)' },
  { bg: 'rgba(232,121,249,0.15)', color: '#e879f9', border: 'rgba(232,121,249,0.3)' },
  { bg: 'rgba(251,191,36,0.15)', color: '#fbbf24', border: 'rgba(251,191,36,0.3)' },
  { bg: 'rgba(52,211,153,0.15)', color: '#34d399', border: 'rgba(52,211,153,0.3)' },
  { bg: 'rgba(251,146,60,0.15)', color: '#fb923c', border: 'rgba(251,146,60,0.3)' },
  { bg: 'rgba(129,140,248,0.15)', color: '#818cf8', border: 'rgba(129,140,248,0.3)' },
  { bg: 'rgba(244,114,182,0.15)', color: '#f472b6', border: 'rgba(244,114,182,0.3)' },
];

function getJobTypeColor(slug: string) {
  let hash = 0;
  for (let i = 0; i < slug.length; i++) hash = slug.charCodeAt(i) + ((hash << 5) - hash);
  return JOB_TYPE_COLORS[Math.abs(hash) % JOB_TYPE_COLORS.length];
}

/* ── Topic Pill Colors ─────────────────────────── */

const TOPIC_COLORS = ['#a78bfa', '#38bdf8', '#e879f9', '#34d399', '#fbbf24', '#fb923c', '#818cf8', '#f472b6'];

function getTopicColor(name: string) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return TOPIC_COLORS[Math.abs(hash) % TOPIC_COLORS.length];
}

/* ── Month helper ──────────────────────────────── */

const MONTHS = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/* ── SVG Icons (inline) ───────────────────────── */

function SearchIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
    </svg>
  );
}

function XIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  );
}

function ChevronIcon({ direction = 'down' }: { direction?: 'down' | 'up' | 'left' | 'right' }) {
  const d = { down: 'M6 9l6 6 6-6', up: 'M18 15l-6-6-6 6', left: 'M15 18l-6-6 6-6', right: 'M9 18l6-6-6-6' };
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d={d[direction]} />
    </svg>
  );
}

/* ═══════════════════════════════════════════════════════
   PAPER CARD COMPONENT
   ═══════════════════════════════════════════════════════ */

function PaperCardComponent({
  paper,
  onClick,
}: {
  paper: PaperCard;
  onClick: () => void;
}) {
  const jtColor = getJobTypeColor(paper.job_type_slug);

  return (
    <div
      onClick={onClick}
      className="glass p-5 cursor-pointer hover:border-[var(--clr-glass-border-hover)] transition-all duration-200 group"
    >
      {/* Top row: Job type badge + status */}
      <div className="flex items-center justify-between mb-3">
        <span
          className="inline-flex items-center px-2.5 py-1 rounded-lg text-[11px] font-bold uppercase tracking-wider"
          style={{ color: jtColor.color, background: jtColor.bg, border: `1px solid ${jtColor.border}` }}
        >
          {paper.job_type_name}
        </span>
        <StatusBadge status={paper.ingestion_status} />
      </div>

      {/* Title */}
      <h3 className="font-display text-base font-bold text-white leading-snug mb-1 group-hover:text-[var(--clr-primary-light)] transition-colors line-clamp-2">
        {paper.title}
      </h3>

      {/* Date + Questions */}
      <div className="flex items-center gap-3 text-xs text-[var(--clr-text-secondary)] mb-3">
        <span>{paper.paper_month ? `${MONTHS[paper.paper_month]} ${paper.paper_year}` : paper.paper_year}</span>
        <span className="w-1 h-1 rounded-full bg-[var(--clr-text-muted)]" />
        <span>{paper.total_questions} questions</span>
        {paper.repeat_questions_count > 0 && (
          <>
            <span className="w-1 h-1 rounded-full bg-[var(--clr-text-muted)]" />
            <span className="text-[var(--clr-warning)]">{paper.repeat_questions_count} repeats</span>
          </>
        )}
      </div>

      {/* Topic pills */}
      <div className="flex flex-wrap gap-1.5">
        {paper.topics.map((t) => {
          const c = t.color_hex || getTopicColor(t.name);
          return (
            <span
              key={t.id}
              className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold"
              style={{ color: c, background: `${c}18`, border: `1px solid ${c}30` }}
            >
              {t.display_name}
            </span>
          );
        })}
        {paper.topics_total > 5 && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold text-[var(--clr-text-muted)] bg-white/[0.04] border border-white/[0.06]">
            +{paper.topics_total - 5} more
          </span>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   PAPER DETAIL DRAWER
   ═══════════════════════════════════════════════════════ */

function PaperDetailDrawer({
  paperId,
  token,
  onClose,
  onDelete,
}: {
  paperId: string;
  token: string;
  onClose: () => void;
  onDelete: () => void;
}) {
  const [detail, setDetail] = useState<PaperDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [questionsPage, setQuestionsPage] = useState(1);
  const [editingQuestion, setEditingQuestion] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [reprocessing, setReprocessing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const fetchDetail = useCallback(async (page = 1) => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiFetch<PaperDetail>(
        `/admin/papers/${paperId}?questions_page=${page}&questions_per_page=20`,
        token,
      );
      setDetail(data);
      setQuestionsPage(page);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load paper');
    } finally {
      setLoading(false);
    }
  }, [paperId, token]);

  useEffect(() => { fetchDetail(); }, [fetchDetail]);

  const handleReprocess = async () => {
    setReprocessing(true);
    try {
      await apiFetch(`/admin/papers/${paperId}/reprocess`, token, { method: 'POST' });
      fetchDetail(questionsPage);
    } catch {
      // Silently handle
    } finally {
      setReprocessing(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await apiFetch(`/admin/papers/${paperId}`, token, { method: 'DELETE' });
      onDelete();
    } catch {
      setDeleting(false);
    }
  };

  const startEditing = (q: QuestionInPaper) => {
    setEditingQuestion(q.id);
    setEditValues({
      question_text: q.question_text,
      option_a: q.option_a || '',
      option_b: q.option_b || '',
      option_c: q.option_c || '',
      option_d: q.option_d || '',
      correct_answer: q.correct_answer || '',
    });
  };

  const saveQuestion = async (questionId: string) => {
    setSaving(true);
    try {
      await apiFetch(`/admin/papers/${paperId}/questions/${questionId}`, token, {
        method: 'PUT',
        body: JSON.stringify(editValues),
      });
      setEditingQuestion(null);
      fetchDetail(questionsPage);
    } catch {
      // Silently handle
    } finally {
      setSaving(false);
    }
  };

  const totalPages = detail ? Math.ceil(detail.questions_total / detail.questions_per_page) : 0;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Drawer */}
      <div className="absolute right-0 top-0 bottom-0 w-full max-w-3xl bg-[var(--clr-bg-surface)] border-l border-white/[0.06] overflow-y-auto animate-slide-in-right">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-[var(--clr-bg-surface)] border-b border-white/[0.06] px-6 py-4 flex items-center justify-between">
          <h2 className="font-display text-xl font-bold text-white truncate mr-4">
            {detail?.title || 'Loading…'}
          </h2>
          <button onClick={onClose} className="glass-sm p-2 hover:bg-white/[0.08] transition-colors rounded-lg">
            <XIcon size={18} />
          </button>
        </div>

        {loading && !detail ? (
          <div className="flex items-center justify-center py-32">
            <div className="w-12 h-12 rounded-full border-4 border-[var(--clr-primary-dim)] border-t-[var(--clr-primary)] animate-spin" />
          </div>
        ) : error ? (
          <div className="p-6">
            <div className="glass-sm p-6 text-center">
              <p className="text-[var(--clr-danger)] font-semibold mb-2">Error</p>
              <p className="text-sm text-[var(--clr-text-secondary)]">{error}</p>
              <button onClick={() => fetchDetail()} className="mt-4 text-xs text-[var(--clr-primary)] hover:underline">
                Try again
              </button>
            </div>
          </div>
        ) : detail ? (
          <div className="p-6 space-y-6">
            {/* Paper info */}
            <div className="glass-sm p-5 space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)] mb-1">Job Type</p>
                  <span
                    className="inline-flex items-center px-2.5 py-1 rounded-lg text-[11px] font-bold uppercase"
                    style={{
                      color: getJobTypeColor(detail.job_type_slug).color,
                      background: getJobTypeColor(detail.job_type_slug).bg,
                    }}
                  >
                    {detail.job_type_name}
                  </span>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)] mb-1">Year</p>
                  <p className="text-sm font-semibold text-white">
                    {detail.paper_month ? `${MONTHS[detail.paper_month]} ` : ''}{detail.paper_year}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)] mb-1">Questions</p>
                  <p className="text-sm font-semibold text-white">{detail.total_questions}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)] mb-1">Status</p>
                  <StatusBadge status={detail.ingestion_status} />
                </div>
              </div>

              {/* Topics */}
              {detail.topics.length > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)] mb-2">Topics Covered</p>
                  <div className="flex flex-wrap gap-1.5">
                    {detail.topics.map((t) => {
                      const c = t.color_hex || getTopicColor(t.name);
                      return (
                        <span
                          key={t.id}
                          className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold"
                          style={{ color: c, background: `${c}18`, border: `1px solid ${c}30` }}
                        >
                          {t.display_name}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  onClick={handleReprocess}
                  disabled={reprocessing}
                  className="glass-sm px-4 py-2 text-xs font-semibold text-[var(--clr-info)] hover:bg-[var(--clr-info-dim)] transition-colors disabled:opacity-50"
                >
                  {reprocessing ? '⏳ Reprocessing…' : '🔄 Re-trigger AI Processing'}
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="glass-sm px-4 py-2 text-xs font-semibold text-[var(--clr-danger)] hover:bg-[var(--clr-danger-dim)] transition-colors"
                >
                  🗑️ Delete Paper
                </button>
              </div>

              {/* Delete confirmation */}
              {showDeleteConfirm && (
                <div className="glass-sm p-4 border border-[var(--clr-danger)]/30 space-y-3">
                  <p className="text-sm text-[var(--clr-danger)] font-semibold">
                    ⚠️ Are you sure you want to delete this paper?
                  </p>
                  <p className="text-xs text-[var(--clr-text-secondary)]">
                    This will permanently delete the paper and all {detail.total_questions} questions. This cannot be undone.
                  </p>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleDelete}
                      disabled={deleting}
                      className="px-4 py-2 text-xs font-bold text-white bg-[var(--clr-danger)] rounded-lg hover:brightness-110 transition disabled:opacity-50"
                    >
                      {deleting ? 'Deleting…' : 'Yes, Delete'}
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="glass-sm px-4 py-2 text-xs font-semibold text-[var(--clr-text-secondary)]"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Questions table */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-display text-lg font-bold text-white">
                  Questions ({detail.questions_total})
                </h3>
                {detail.repeat_questions_count > 0 && (
                  <span className="text-xs text-[var(--clr-warning)] font-semibold">
                    🔄 {detail.repeat_questions_count} repeat questions
                  </span>
                )}
              </div>

              <div className="space-y-2">
                {detail.questions.map((q) => (
                  <div key={q.id} className="glass-sm p-4 space-y-2">
                    {editingQuestion === q.id ? (
                      /* ── Inline edit mode ── */
                      <div className="space-y-3">
                        <div>
                          <label className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)] block mb-1">
                            Question Text
                          </label>
                          <textarea
                            value={editValues.question_text || ''}
                            onChange={(e) => setEditValues({ ...editValues, question_text: e.target.value })}
                            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white placeholder:text-[var(--clr-text-muted)] focus:border-[var(--clr-primary)] outline-none resize-none"
                            rows={3}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          {(['a', 'b', 'c', 'd'] as const).map((opt) => (
                            <div key={opt}>
                              <label className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)] block mb-1">
                                Option {opt.toUpperCase()}
                              </label>
                              <input
                                value={editValues[`option_${opt}`] || ''}
                                onChange={(e) => setEditValues({ ...editValues, [`option_${opt}`]: e.target.value })}
                                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-1.5 text-sm text-white placeholder:text-[var(--clr-text-muted)] focus:border-[var(--clr-primary)] outline-none"
                              />
                            </div>
                          ))}
                        </div>
                        <div className="w-32">
                          <label className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)] block mb-1">
                            Correct Answer
                          </label>
                          <select
                            value={editValues.correct_answer || ''}
                            onChange={(e) => setEditValues({ ...editValues, correct_answer: e.target.value })}
                            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-1.5 text-sm text-white focus:border-[var(--clr-primary)] outline-none"
                          >
                            <option value="">—</option>
                            <option value="a">A</option>
                            <option value="b">B</option>
                            <option value="c">C</option>
                            <option value="d">D</option>
                          </select>
                        </div>
                        <div className="flex items-center gap-2 pt-1">
                          <button
                            onClick={() => saveQuestion(q.id)}
                            disabled={saving}
                            className="px-3 py-1.5 text-xs font-bold text-white bg-[var(--clr-primary-vivid)] rounded-lg hover:brightness-110 transition disabled:opacity-50"
                          >
                            {saving ? 'Saving…' : '✓ Save'}
                          </button>
                          <button
                            onClick={() => setEditingQuestion(null)}
                            className="glass-sm px-3 py-1.5 text-xs font-semibold text-[var(--clr-text-secondary)]"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* ── View mode ── */
                      <>
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-[10px] font-bold text-[var(--clr-primary)] bg-[var(--clr-primary-dim)] px-1.5 py-0.5 rounded">
                                Q{q.question_number}
                              </span>
                              {q.is_repeated && (
                                <span className="text-[10px] font-bold text-[var(--clr-warning)] bg-[var(--clr-warning-dim)] px-1.5 py-0.5 rounded">
                                  🔄 ×{q.repeat_count}
                                </span>
                              )}
                              {q.needs_review && (
                                <span className="text-[10px] font-bold text-[var(--clr-danger)] bg-[var(--clr-danger-dim)] px-1.5 py-0.5 rounded">
                                  Review
                                </span>
                              )}
                              {q.topic_name && (
                                <span className="text-[10px] text-[var(--clr-text-muted)]">
                                  {q.topic_name}
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-white leading-relaxed">{q.question_text}</p>
                          </div>
                          <button
                            onClick={() => startEditing(q)}
                            className="shrink-0 glass-sm px-2 py-1 text-[10px] font-semibold text-[var(--clr-text-secondary)] hover:text-white transition-colors"
                          >
                            ✏️ Edit
                          </button>
                        </div>

                        {/* Options */}
                        <div className="grid grid-cols-2 gap-1.5 pl-2">
                          {(['a', 'b', 'c', 'd'] as const).map((opt) => {
                            const text = q[`option_${opt}` as keyof QuestionInPaper] as string | null;
                            if (!text) return null;
                            const isCorrect = q.correct_answer === opt;
                            return (
                              <div
                                key={opt}
                                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs ${
                                  isCorrect
                                    ? 'bg-[var(--clr-success-dim)] text-[var(--clr-success)] font-semibold border border-[rgba(52,211,153,0.25)]'
                                    : 'bg-white/[0.02] text-[var(--clr-text-secondary)]'
                                }`}
                              >
                                <span className="font-bold text-[10px] uppercase">{opt}.</span>
                                <span className="truncate">{text}</span>
                                {isCorrect && <span className="ml-auto">✓</span>}
                              </div>
                            );
                          })}
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-4">
                  <button
                    onClick={() => fetchDetail(questionsPage - 1)}
                    disabled={questionsPage <= 1}
                    className="glass-sm px-3 py-1.5 text-xs font-semibold text-[var(--clr-text-secondary)] disabled:opacity-30"
                  >
                    <ChevronIcon direction="left" />
                  </button>
                  <span className="text-xs text-[var(--clr-text-secondary)]">
                    Page {questionsPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => fetchDetail(questionsPage + 1)}
                    disabled={questionsPage >= totalPages}
                    className="glass-sm px-3 py-1.5 text-xs font-semibold text-[var(--clr-text-secondary)] disabled:opacity-30"
                  >
                    <ChevronIcon direction="right" />
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   MAIN PAPERS PAGE CONTENT
   ═══════════════════════════════════════════════════════ */

function PapersPageContent() {
  const session = useAuthStore((s) => s.session);
  const initialised = useAuthStore((s) => s.initialised);
  const token = session?.access_token || '';

  // Data
  const [papers, setPapers] = useState<PaperCard[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedJobTypes, setSelectedJobTypes] = useState<string[]>([]);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [yearMin, setYearMin] = useState('');
  const [yearMax, setYearMax] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [page, setPage] = useState(1);
  const perPage = 20;

  // Job types for filter dropdown
  const [jobTypes, setJobTypes] = useState<JobType[]>([]);

  // Drawer
  const [selectedPaperId, setSelectedPaperId] = useState<string | null>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Reset page on filter change
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, selectedJobTypes, selectedStatuses, yearMin, yearMax, sortBy]);

  // Fetch job types
  useEffect(() => {
    if (!token) return;
    apiFetch<{ id: string; name: string; slug: string }[]>('/job-types', token)
      .then((data) => {
        // Backend might return { job_types: [] } or just []
        if (Array.isArray(data)) setJobTypes(data);
        else if (data && typeof data === 'object' && 'job_types' in data) setJobTypes((data as unknown as { job_types: JobType[] }).job_types);
      })
      .catch(() => {});
  }, [token]);

  // Fetch papers
  const fetchPapers = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('per_page', String(perPage));
      params.set('sort', sortBy);
      if (debouncedSearch) params.set('search', debouncedSearch);
      if (selectedJobTypes.length > 0) params.set('job_type_ids', selectedJobTypes.join(','));
      if (selectedStatuses.length > 0) params.set('status', selectedStatuses.join(','));
      if (yearMin) params.set('year_min', yearMin);
      if (yearMax) params.set('year_max', yearMax);

      const data = await apiFetch<PapersListResponse>(`/admin/papers?${params}`, token);
      setPapers(data.papers);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load papers');
    } finally {
      setLoading(false);
    }
  }, [token, page, perPage, sortBy, debouncedSearch, selectedJobTypes, selectedStatuses, yearMin, yearMax]);

  useEffect(() => {
    if (initialised && token) {
      fetchPapers();
    }
  }, [initialised, token, fetchPapers]);

  const totalPages = Math.ceil(total / perPage);

  const toggleJobType = (id: string) => {
    setSelectedJobTypes((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  const toggleStatus = (s: string) => {
    setSelectedStatuses((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]);
  };

  const clearFilters = () => {
    setSearch('');
    setSelectedJobTypes([]);
    setSelectedStatuses([]);
    setYearMin('');
    setYearMax('');
    setSortBy('newest');
  };

  const hasFilters = search || selectedJobTypes.length > 0 || selectedStatuses.length > 0 || yearMin || yearMax;

  return (
    <AdminLayout>
      <div className="max-w-[1400px]">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-display text-3xl font-bold text-white mb-1">Papers Library</h1>
            <p className="text-[var(--clr-text-secondary)] text-sm">
              {total} papers in the database{hasFilters ? ' (filtered)' : ''}
            </p>
          </div>
          <button
            onClick={fetchPapers}
            disabled={loading}
            className="glass-sm px-4 py-2 text-xs font-semibold text-[var(--clr-text-secondary)] hover:text-white transition-all disabled:opacity-50"
          >
            {loading ? '⏳ Loading…' : '↻ Refresh'}
          </button>
        </div>

        {/* Search + Filters */}
        <div className="glass p-4 mb-6 space-y-4">
          {/* Search bar */}
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--clr-text-muted)]">
              <SearchIcon />
            </span>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search papers by title…"
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder:text-[var(--clr-text-muted)] focus:border-[var(--clr-primary)] outline-none transition-colors"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--clr-text-muted)] hover:text-white"
              >
                <XIcon />
              </button>
            )}
          </div>

          {/* Filters row */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Job Type multi-select */}
            <div className="relative group">
              <button className="glass-sm px-3 py-1.5 text-xs font-semibold text-[var(--clr-text-secondary)] hover:text-white flex items-center gap-1.5 transition-colors">
                Job Types {selectedJobTypes.length > 0 && `(${selectedJobTypes.length})`}
                <ChevronIcon />
              </button>
              <div className="absolute top-full left-0 mt-1 w-56 bg-[var(--clr-bg-elevated)] border border-white/[0.08] rounded-xl shadow-2xl p-2 z-20 hidden group-hover:block">
                {jobTypes.map((jt) => (
                  <label
                    key={jt.id}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/[0.04] cursor-pointer text-xs text-[var(--clr-text-secondary)]"
                  >
                    <input
                      type="checkbox"
                      checked={selectedJobTypes.includes(jt.id)}
                      onChange={() => toggleJobType(jt.id)}
                      className="accent-[var(--clr-primary)]"
                    />
                    {jt.name}
                  </label>
                ))}
                {jobTypes.length === 0 && (
                  <p className="text-xs text-[var(--clr-text-muted)] px-3 py-2">Loading…</p>
                )}
              </div>
            </div>

            {/* Status filter */}
            <div className="relative group">
              <button className="glass-sm px-3 py-1.5 text-xs font-semibold text-[var(--clr-text-secondary)] hover:text-white flex items-center gap-1.5 transition-colors">
                Status {selectedStatuses.length > 0 && `(${selectedStatuses.length})`}
                <ChevronIcon />
              </button>
              <div className="absolute top-full left-0 mt-1 w-44 bg-[var(--clr-bg-elevated)] border border-white/[0.08] rounded-xl shadow-2xl p-2 z-20 hidden group-hover:block">
                {['pending', 'processing', 'completed', 'failed'].map((s) => (
                  <label
                    key={s}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/[0.04] cursor-pointer text-xs"
                  >
                    <input
                      type="checkbox"
                      checked={selectedStatuses.includes(s)}
                      onChange={() => toggleStatus(s)}
                      className="accent-[var(--clr-primary)]"
                    />
                    <StatusBadge status={s} />
                  </label>
                ))}
              </div>
            </div>

            {/* Year range */}
            <div className="flex items-center gap-1.5">
              <input
                type="number"
                value={yearMin}
                onChange={(e) => setYearMin(e.target.value)}
                placeholder="Year from"
                className="w-24 bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-1.5 text-xs text-white placeholder:text-[var(--clr-text-muted)] focus:border-[var(--clr-primary)] outline-none"
              />
              <span className="text-[var(--clr-text-muted)] text-xs">—</span>
              <input
                type="number"
                value={yearMax}
                onChange={(e) => setYearMax(e.target.value)}
                placeholder="Year to"
                className="w-24 bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-1.5 text-xs text-white placeholder:text-[var(--clr-text-muted)] focus:border-[var(--clr-primary)] outline-none"
              />
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-1.5 text-xs text-white focus:border-[var(--clr-primary)] outline-none"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="job_type">By Job Type</option>
              <option value="questions">By Question Count</option>
            </select>

            {/* Clear filters */}
            {hasFilters && (
              <button
                onClick={clearFilters}
                className="text-xs text-[var(--clr-danger)] hover:underline font-semibold"
              >
                ✕ Clear filters
              </button>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="glass-sm px-5 py-4 mb-6 border-l-4 border-[var(--clr-danger)]">
            <p className="text-sm text-[var(--clr-danger)] font-semibold">{error}</p>
            <button onClick={fetchPapers} className="text-xs text-[var(--clr-primary)] hover:underline mt-1">
              Try again
            </button>
          </div>
        )}

        {/* Loading state */}
        {loading && papers.length === 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="glass p-5 animate-pulse space-y-3">
                <div className="flex justify-between">
                  <div className="w-24 h-6 rounded-lg bg-white/[0.06]" />
                  <div className="w-20 h-5 rounded-full bg-white/[0.06]" />
                </div>
                <div className="w-3/4 h-5 rounded bg-white/[0.06]" />
                <div className="w-1/2 h-3 rounded bg-white/[0.04]" />
                <div className="flex gap-1.5">
                  <div className="w-16 h-5 rounded-full bg-white/[0.04]" />
                  <div className="w-20 h-5 rounded-full bg-white/[0.04]" />
                  <div className="w-14 h-5 rounded-full bg-white/[0.04]" />
                </div>
              </div>
            ))}
          </div>
        ) : papers.length === 0 ? (
          <div className="glass p-16 text-center">
            <div className="text-4xl mb-4">📄</div>
            <h3 className="font-display text-xl font-bold text-white mb-2">No papers found</h3>
            <p className="text-sm text-[var(--clr-text-secondary)]">
              {hasFilters ? 'Try adjusting your filters' : 'No papers have been ingested yet'}
            </p>
          </div>
        ) : (
          <>
            {/* Papers Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
              {papers.map((paper) => (
                <PaperCardComponent
                  key={paper.id}
                  paper={paper}
                  onClick={() => setSelectedPaperId(paper.id)}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-3 mb-8">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="glass-sm px-4 py-2 text-xs font-semibold text-[var(--clr-text-secondary)] disabled:opacity-30"
                >
                  ← Previous
                </button>
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const start = Math.max(1, Math.min(page - 2, totalPages - 4));
                    const p = start + i;
                    if (p > totalPages) return null;
                    return (
                      <button
                        key={p}
                        onClick={() => setPage(p)}
                        className={`w-8 h-8 rounded-lg text-xs font-bold transition-colors ${
                          p === page
                            ? 'bg-[var(--clr-primary-dim)] text-[var(--clr-primary)] border border-[var(--clr-glass-border-hover)]'
                            : 'text-[var(--clr-text-secondary)] hover:bg-white/[0.04]'
                        }`}
                      >
                        {p}
                      </button>
                    );
                  })}
                </div>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="glass-sm px-4 py-2 text-xs font-semibold text-[var(--clr-text-secondary)] disabled:opacity-30"
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Detail Drawer */}
      {selectedPaperId && (
        <PaperDetailDrawer
          paperId={selectedPaperId}
          token={token}
          onClose={() => setSelectedPaperId(null)}
          onDelete={() => {
            setSelectedPaperId(null);
            fetchPapers();
          }}
        />
      )}
    </AdminLayout>
  );
}

/* ── Page Wrapper ── */

export default function AdminPapersPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <PapersPageContent />
    </ProtectedRoute>
  );
}
