/**
 * Admin — Notes (/admin/notes)
 * ===============================
 * Upload raw note content for AI processing into story documents.
 * Lists all submitted notes with topic assignments and processing status.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/admin/AdminLayout';
import { useAuthStore } from '@/store/auth-store';

/* ── Types ─────────────────────────────────────── */

interface AdminNote {
  id: string;
  raw_content: string;
  source_description: string | null;
  processed: boolean;
  assigned_topic_id: string | null;
  processed_content: string | null;
  position_in_story: number | null;
  created_at: string;
  topic_name: string | null;
  topic_display_name: string | null;
}

interface NoteListResponse {
  notes: AdminNote[];
  total: number;
  page: number;
  per_page: number;
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

/* ── Story section labels ──────────────────────── */

const STORY_SECTIONS = [
  'Introduction',
  'Core Foundations',
  'Historical Development',
  'Key Facts and Figures',
  'Relationships and Connections',
  'Recent Developments',
  'Exam Hotspots',
];

/* ── Component ─────────────────────────────────── */

function AdminNotesContent() {
  const session = useAuthStore((s) => s.session);
  const token = session?.access_token;

  // Notes list state
  const [notes, setNotes] = useState<AdminNote[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Filter state
  const [filterProcessed, setFilterProcessed] = useState<string>('all');

  // Upload form state
  const [rawContent, setRawContent] = useState('');
  const [sourceDesc, setSourceDesc] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Expanded note detail
  const [expandedId, setExpandedId] = useState<string | null>(null);

  /* ── Fetch notes ─────────────────────────────── */
  const fetchNotes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let path = `/admin/notes?page=${page}&per_page=${perPage}`;
      if (filterProcessed === 'true') path += '&processed=true';
      else if (filterProcessed === 'false') path += '&processed=false';

      const data = await apiFetch<NoteListResponse>(path, {}, token);
      setNotes(data.notes);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load notes');
    } finally {
      setLoading(false);
    }
  }, [page, perPage, filterProcessed, token]);

  useEffect(() => {
    if (token) fetchNotes();
  }, [fetchNotes, token]);

  /* ── Upload note ─────────────────────────────── */
  const handleUpload = async () => {
    if (!rawContent.trim() || rawContent.trim().length < 10) {
      setError('Note content must be at least 10 characters');
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const body: Record<string, string> = { raw_content: rawContent.trim() };
      if (sourceDesc.trim()) body.source_description = sourceDesc.trim();

      await apiFetch('/admin/notes', { method: 'POST', body: JSON.stringify(body) }, token);
      setSuccess('Note uploaded and queued for AI processing');
      setRawContent('');
      setSourceDesc('');
      // Refresh list
      fetchNotes();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to upload note');
    } finally {
      setSubmitting(false);
    }
  };

  /* ── Delete note ─────────────────────────────── */
  const handleDelete = async (noteId: string) => {
    if (!confirm('Delete this note? This action cannot be undone.')) return;
    setError(null);
    try {
      await apiFetch(`/admin/notes/${noteId}`, { method: 'DELETE' }, token);
      setSuccess('Note deleted');
      fetchNotes();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete note');
    }
  };

  /* ── Batch process ───────────────────────────── */
  const handleBatchProcess = async () => {
    setError(null);
    setSuccess(null);
    try {
      const result = await apiFetch<{ status: string; pending: number; message: string }>(
        '/admin/notes/batch-process',
        { method: 'POST' },
        token,
      );
      setSuccess(result.message);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to trigger batch processing');
    }
  };

  const totalPages = Math.ceil(total / perPage);

  return (
    <AdminLayout>
      <div className="max-w-5xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-3xl font-bold text-white mb-1">Admin Notes</h1>
            <p className="text-[var(--clr-text-secondary)]">
              Upload raw notes for AI processing into topic story documents.
            </p>
          </div>
          <button
            onClick={handleBatchProcess}
            className="px-4 py-2 text-sm font-medium rounded-xl bg-[var(--clr-primary-dim)] text-[var(--clr-primary)] border border-[var(--clr-glass-border)] hover:bg-[var(--clr-primary)] hover:text-white transition-all duration-200"
          >
            Process All Pending
          </button>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mb-6 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-6 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
            {success}
          </div>
        )}

        {/* ── Upload Form ──────────────────────── */}
        <div className="glass p-6 mb-8">
          <h2 className="text-lg font-bold text-white mb-4">Upload New Note</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[var(--clr-text-secondary)] mb-2">
                Raw Content
              </label>
              <textarea
                value={rawContent}
                onChange={(e) => setRawContent(e.target.value)}
                rows={8}
                placeholder="Paste raw note content here... (e.g. textbook excerpts, article summaries, manual facts)"
                className="w-full px-4 py-3 rounded-xl bg-[var(--clr-bg-surface)] border border-[var(--clr-glass-border)] text-white placeholder-[var(--clr-text-muted)] focus:outline-none focus:border-[var(--clr-primary)] focus:ring-1 focus:ring-[var(--clr-primary)] transition-all duration-200 resize-y text-sm leading-relaxed"
              />
              <p className="mt-1 text-xs text-[var(--clr-text-muted)]">
                {rawContent.length} characters · Min 10 required
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--clr-text-secondary)] mb-2">
                Source Description <span className="text-[var(--clr-text-muted)]">(optional)</span>
              </label>
              <input
                type="text"
                value={sourceDesc}
                onChange={(e) => setSourceDesc(e.target.value)}
                placeholder="e.g. Pakistan Studies textbook Ch. 3, Dawn News article, manual entry"
                maxLength={500}
                className="w-full px-4 py-2.5 rounded-xl bg-[var(--clr-bg-surface)] border border-[var(--clr-glass-border)] text-white placeholder-[var(--clr-text-muted)] focus:outline-none focus:border-[var(--clr-primary)] focus:ring-1 focus:ring-[var(--clr-primary)] transition-all duration-200 text-sm"
              />
            </div>

            <button
              onClick={handleUpload}
              disabled={submitting || rawContent.trim().length < 10}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-[var(--clr-primary)] to-[var(--clr-neon)] text-white font-semibold text-sm hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Uploading…
                </span>
              ) : (
                'Upload & Process'
              )}
            </button>
          </div>
        </div>

        {/* ── Filter bar ───────────────────────── */}
        <div className="flex items-center gap-4 mb-6">
          <span className="text-sm text-[var(--clr-text-secondary)]">Filter:</span>
          <div className="flex gap-2">
            {[
              { label: 'All', value: 'all' },
              { label: 'Processed', value: 'true' },
              { label: 'Pending', value: 'false' },
            ].map((f) => (
              <button
                key={f.value}
                onClick={() => { setFilterProcessed(f.value); setPage(1); }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 ${
                  filterProcessed === f.value
                    ? 'bg-[var(--clr-primary-dim)] text-[var(--clr-primary)] border border-[var(--clr-glass-border-hover)]'
                    : 'text-[var(--clr-text-muted)] hover:text-white hover:bg-white/[0.04] border border-transparent'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
          <span className="ml-auto text-sm text-[var(--clr-text-muted)]">
            {total} note{total !== 1 ? 's' : ''}
          </span>
        </div>

        {/* ── Notes List ───────────────────────── */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <svg className="animate-spin h-8 w-8 text-[var(--clr-primary)]" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : notes.length === 0 ? (
          <div className="glass p-12 text-center">
            <p className="text-[var(--clr-text-muted)] text-sm">
              No notes found. Upload your first note above.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {notes.map((note) => {
              const isExpanded = expandedId === note.id;
              return (
                <div key={note.id} className="glass overflow-hidden">
                  {/* Row header */}
                  <div
                    className="flex items-center gap-4 px-5 py-4 cursor-pointer hover:bg-white/[0.02] transition-colors"
                    onClick={() => setExpandedId(isExpanded ? null : note.id)}
                  >
                    {/* Status badge */}
                    <span
                      className={`shrink-0 w-2.5 h-2.5 rounded-full ${
                        note.processed
                          ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]'
                          : 'bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.5)] animate-pulse'
                      }`}
                      title={note.processed ? 'Processed' : 'Pending'}
                    />

                    {/* Content preview */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white truncate">
                        {note.raw_content.slice(0, 120)}
                        {note.raw_content.length > 120 ? '…' : ''}
                      </p>
                      <div className="flex items-center gap-3 mt-1">
                        {note.source_description && (
                          <span className="text-xs text-[var(--clr-text-muted)]">
                            📎 {note.source_description}
                          </span>
                        )}
                        <span className="text-xs text-[var(--clr-text-muted)]">
                          {new Date(note.created_at).toLocaleDateString('en-PK', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                    </div>

                    {/* Topic badge */}
                    {note.topic_display_name ? (
                      <span className="shrink-0 px-3 py-1 text-xs font-medium rounded-lg bg-[var(--clr-primary-dim)] text-[var(--clr-primary)] border border-[var(--clr-glass-border)]">
                        {note.topic_display_name}
                      </span>
                    ) : note.processed ? (
                      <span className="shrink-0 px-3 py-1 text-xs font-medium rounded-lg bg-orange-500/10 text-orange-400 border border-orange-500/20">
                        No topic match
                      </span>
                    ) : null}

                    {/* Story section */}
                    {note.position_in_story !== null && note.position_in_story !== undefined && (
                      <span className="shrink-0 px-2.5 py-1 text-xs rounded-lg bg-white/[0.04] text-[var(--clr-text-muted)] border border-[var(--clr-glass-border)]">
                        § {STORY_SECTIONS[note.position_in_story] || `Section ${note.position_in_story}`}
                      </span>
                    )}

                    {/* Expand icon */}
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className={`shrink-0 text-[var(--clr-text-muted)] transition-transform duration-200 ${
                        isExpanded ? 'rotate-180' : ''
                      }`}
                    >
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </div>

                  {/* Expanded detail */}
                  {isExpanded && (
                    <div className="border-t border-white/[0.06] px-5 py-4 bg-white/[0.01]">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Raw content */}
                        <div>
                          <h4 className="text-xs font-semibold text-[var(--clr-text-muted)] uppercase tracking-wider mb-2">
                            Raw Content
                          </h4>
                          <div className="text-sm text-[var(--clr-text-secondary)] whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto pr-2">
                            {note.raw_content}
                          </div>
                        </div>

                        {/* Processed content / extracted facts */}
                        <div>
                          <h4 className="text-xs font-semibold text-[var(--clr-text-muted)] uppercase tracking-wider mb-2">
                            {note.processed ? 'Extracted Facts' : 'Processing…'}
                          </h4>
                          {note.processed_content ? (
                            <div className="text-sm text-[var(--clr-text-secondary)] whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto pr-2">
                              {note.processed_content}
                            </div>
                          ) : (
                            <p className="text-sm text-[var(--clr-text-muted)] italic">
                              {note.processed
                                ? 'No processed content available'
                                : 'Note is queued for AI processing…'}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-3 mt-4 pt-4 border-t border-white/[0.04]">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDelete(note.id); }}
                          className="px-3 py-1.5 text-xs font-medium rounded-lg text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all"
                        >
                          Delete
                        </button>
                        <span className="ml-auto text-[10px] text-[var(--clr-text-muted)] font-mono">
                          {note.id}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ── Pagination ───────────────────────── */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs font-medium rounded-lg text-[var(--clr-text-muted)] hover:text-white hover:bg-white/[0.04] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              ← Prev
            </button>
            <span className="text-xs text-[var(--clr-text-muted)]">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-xs font-medium rounded-lg text-[var(--clr-text-muted)] hover:text-white hover:bg-white/[0.04] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}

export default function AdminNotesPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <AdminNotesContent />
    </ProtectedRoute>
  );
}
