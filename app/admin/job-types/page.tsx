/**
 * Admin — Job Types Manager (/admin/job-types)
 * ==============================================
 * Full CRUD for PPSC job types with inline topic_ratios editor.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/admin/AdminLayout';
import { useAuthStore } from '@/store/auth-store';

/* ── Types ─────────────────────────────────────── */

interface JobType {
  id: string;
  name: string;
  slug: string;
  department: string | null;
  total_papers: number;
  avg_questions_per_paper: number;
  topic_ratios: Record<string, number> | null;
  last_updated_ratios: string | null;
  is_active: boolean;
  created_at: string;
}

interface FormData {
  name: string;
  slug: string;
  department: string;
  is_active: boolean;
  topic_ratios: Record<string, number>;
}

const EMPTY_FORM: FormData = {
  name: '',
  slug: '',
  department: '',
  is_active: true,
  topic_ratios: {},
};

/* ── API helper ────────────────────────────────── */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function apiFetch<T = unknown>(
  path: string,
  opts: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...((opts.headers as Record<string, string>) || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...opts, headers, credentials: 'include' });
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Slug helper ───────────────────────────────── */

function toSlug(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/* ── Component ─────────────────────────────────── */

function JobTypesContent() {
  const session = useAuthStore((s) => s.session);
  const token = session?.access_token;

  const [jobTypes, setJobTypes] = useState<JobType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  // Topic ratio editor
  const [newTopicName, setNewTopicName] = useState('');
  const [newTopicValue, setNewTopicValue] = useState('');

  // Delete confirmation
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  /* ── Fetch all job types ─────────────────────── */
  const fetchJobTypes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<{ job_types: JobType[]; total: number }>(
        '/job-types/?active_only=false',
        {},
        token,
      );
      setJobTypes(data.job_types);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load job types');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchJobTypes();
  }, [fetchJobTypes]);

  // Auto-clear success message
  useEffect(() => {
    if (!success) return;
    const t = setTimeout(() => setSuccess(null), 4000);
    return () => clearTimeout(t);
  }, [success]);

  /* ── Open create / edit modal ────────────────── */
  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setNewTopicName('');
    setNewTopicValue('');
    setShowModal(true);
  };

  const openEdit = (jt: JobType) => {
    setEditingId(jt.id);
    setForm({
      name: jt.name,
      slug: jt.slug,
      department: jt.department || '',
      is_active: jt.is_active,
      topic_ratios: jt.topic_ratios ? { ...jt.topic_ratios } : {},
    });
    setNewTopicName('');
    setNewTopicValue('');
    setShowModal(true);
  };

  /* ── Form handlers ───────────────────────────── */
  const handleNameChange = (val: string) => {
    setForm((f) => ({
      ...f,
      name: val,
      slug: editingId ? f.slug : toSlug(val), // auto-slug only on create
    }));
  };

  const addTopic = () => {
    const name = newTopicName.trim();
    const val = parseFloat(newTopicValue);
    if (!name || isNaN(val) || val < 0 || val > 1) return;
    setForm((f) => ({ ...f, topic_ratios: { ...f.topic_ratios, [name]: val } }));
    setNewTopicName('');
    setNewTopicValue('');
  };

  const removeTopic = (key: string) => {
    setForm((f) => {
      const copy = { ...f.topic_ratios };
      delete copy[key];
      return { ...f, topic_ratios: copy };
    });
  };

  const updateTopicValue = (key: string, val: string) => {
    const num = parseFloat(val);
    if (isNaN(num)) return;
    setForm((f) => ({ ...f, topic_ratios: { ...f.topic_ratios, [key]: num } }));
  };

  /* ── Save (create or update) ─────────────────── */
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      if (editingId) {
        // Update basic fields
        await apiFetch(
          `/job-types/${editingId}`,
          {
            method: 'PUT',
            body: JSON.stringify({
              name: form.name,
              slug: form.slug,
              department: form.department || null,
              is_active: form.is_active,
              topic_ratios: Object.keys(form.topic_ratios).length > 0 ? form.topic_ratios : null,
            }),
          },
          token,
        );
        // Also update topic ratios via PATCH if present
        if (Object.keys(form.topic_ratios).length > 0) {
          await apiFetch(
            `/job-types/${editingId}/topic-ratios`,
            {
              method: 'PATCH',
              body: JSON.stringify({ topic_ratios: form.topic_ratios }),
            },
            token,
          );
        }
        setSuccess(`"${form.name}" updated successfully`);
      } else {
        // Create
        await apiFetch(
          '/job-types/',
          {
            method: 'POST',
            body: JSON.stringify({
              name: form.name,
              slug: form.slug,
              department: form.department || null,
            }),
          },
          token,
        );
        setSuccess(`"${form.name}" created successfully`);
      }
      setShowModal(false);
      await fetchJobTypes();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  /* ── Delete ──────────────────────────────────── */
  const handleDelete = async () => {
    if (!deletingId) return;
    setDeleting(true);
    setError(null);
    try {
      await apiFetch(`/job-types/${deletingId}`, { method: 'DELETE' }, token);
      setSuccess('Job type deleted');
      setDeletingId(null);
      await fetchJobTypes();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    } finally {
      setDeleting(false);
    }
  };

  /* ── Ratio sum helper ────────────────────────── */
  const ratioSum = Object.values(form.topic_ratios).reduce((a, b) => a + b, 0);

  return (
    <AdminLayout>
      <div className="max-w-6xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-3xl font-bold text-white mb-1">Job Types</h1>
            <p className="text-sm text-[var(--clr-text-secondary)]">
              Manage PPSC job categories and their topic weight distributions.
            </p>
          </div>
          <button onClick={openCreate} className="btn btn-primary flex items-center gap-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add Job Type
          </button>
        </div>

        {/* Toast messages */}
        {success && (
          <div className="mb-6 flex items-center gap-3 px-4 py-3 rounded-xl bg-[var(--clr-success-dim)] border border-[rgba(52,211,153,0.2)] animate-in fade-in slide-in-from-top-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--clr-success)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            <p className="text-sm text-[var(--clr-success)]">{success}</p>
          </div>
        )}
        {error && (
          <div className="mb-6 flex items-center gap-3 px-4 py-3 rounded-xl bg-[var(--clr-danger-dim)] border border-[rgba(248,113,113,0.2)]">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--clr-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            <p className="text-sm text-[var(--clr-danger)]">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto text-[var(--clr-danger)] hover:text-white text-xs">✕</button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-20">
            <svg className="animate-spin h-8 w-8 text-primary" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
          </div>
        )}

        {/* Table */}
        {!loading && (
          <div className="glass overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-[var(--clr-text-muted)] font-semibold">Name</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-[var(--clr-text-muted)] font-semibold">Department</th>
                    <th className="text-center px-6 py-4 text-xs uppercase tracking-wider text-[var(--clr-text-muted)] font-semibold">Papers</th>
                    <th className="text-center px-6 py-4 text-xs uppercase tracking-wider text-[var(--clr-text-muted)] font-semibold">Topics</th>
                    <th className="text-center px-6 py-4 text-xs uppercase tracking-wider text-[var(--clr-text-muted)] font-semibold">Status</th>
                    <th className="text-right px-6 py-4 text-xs uppercase tracking-wider text-[var(--clr-text-muted)] font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobTypes.map((jt) => (
                    <tr key={jt.id} className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors">
                      <td className="px-6 py-4">
                        <p className="font-semibold text-white">{jt.name}</p>
                        <p className="text-xs text-[var(--clr-text-muted)] font-mono">{jt.slug}</p>
                      </td>
                      <td className="px-6 py-4 text-[var(--clr-text-secondary)]">{jt.department || '—'}</td>
                      <td className="px-6 py-4 text-center text-white font-semibold">{jt.total_papers}</td>
                      <td className="px-6 py-4 text-center">
                        <span className="text-[var(--clr-primary)] font-semibold">
                          {jt.topic_ratios ? Object.keys(jt.topic_ratios).length : 0}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            jt.is_active
                              ? 'bg-[var(--clr-success-dim)] text-[var(--clr-success)] border border-[rgba(52,211,153,0.2)]'
                              : 'bg-[var(--clr-danger-dim)] text-[var(--clr-danger)] border border-[rgba(248,113,113,0.2)]'
                          }`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${jt.is_active ? 'bg-[var(--clr-success)]' : 'bg-[var(--clr-danger)]'}`} />
                          {jt.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => openEdit(jt)}
                            className="p-2 rounded-lg text-[var(--clr-text-muted)] hover:text-[var(--clr-primary)] hover:bg-[var(--clr-primary-dim)] transition-all"
                            title="Edit"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                          </button>
                          <button
                            onClick={() => setDeletingId(jt.id)}
                            className="p-2 rounded-lg text-[var(--clr-text-muted)] hover:text-[var(--clr-danger)] hover:bg-[var(--clr-danger-dim)] transition-all"
                            title="Delete"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <polyline points="3 6 5 6 21 6"/>
                              <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {jobTypes.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-16 text-center text-[var(--clr-text-muted)]">
                        No job types found. Click &quot;Add Job Type&quot; to create one.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* ════════════ Create / Edit Modal ════════════ */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowModal(false)} />

          {/* Dialog */}
          <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto glass p-8 animate-in fade-in zoom-in-95 duration-200">
            <h2 className="font-display text-xl font-bold text-white mb-1">
              {editingId ? 'Edit Job Type' : 'Create Job Type'}
            </h2>
            <p className="text-sm text-[var(--clr-text-secondary)] mb-6">
              {editingId ? 'Update details and topic weight distribution.' : 'Add a new PPSC job category.'}
            </p>

            {/* Basic fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-[var(--clr-text-secondary)] mb-1.5">Name *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="e.g. ASI Police"
                  className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-[var(--clr-text-muted)] bg-[rgba(22,18,52,0.6)] border border-[var(--clr-glass-border)] focus:border-primary/40 focus:shadow-[0_0_0_3px_rgba(139,92,246,0.1)] outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--clr-text-secondary)] mb-1.5">Slug *</label>
                <input
                  type="text"
                  value={form.slug}
                  onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))}
                  placeholder="asi-police"
                  className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-[var(--clr-text-muted)] bg-[rgba(22,18,52,0.6)] border border-[var(--clr-glass-border)] focus:border-primary/40 focus:shadow-[0_0_0_3px_rgba(139,92,246,0.1)] outline-none transition-all font-mono"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--clr-text-secondary)] mb-1.5">Department</label>
                <input
                  type="text"
                  value={form.department}
                  onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))}
                  placeholder="e.g. Punjab Police"
                  className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-[var(--clr-text-muted)] bg-[rgba(22,18,52,0.6)] border border-[var(--clr-glass-border)] focus:border-primary/40 focus:shadow-[0_0_0_3px_rgba(139,92,246,0.1)] outline-none transition-all"
                />
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-3 cursor-pointer">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={form.is_active}
                      onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 rounded-full bg-white/10 peer-checked:bg-[var(--clr-primary-vivid)] transition-colors" />
                    <div className="absolute left-0.5 top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform peer-checked:translate-x-5" />
                  </div>
                  <span className="text-sm font-medium text-[var(--clr-text-secondary)]">Active</span>
                </label>
              </div>
            </div>

            {/* Topic Ratios Editor */}
            <div className="border-t border-white/[0.06] pt-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold text-white">Topic Ratios</h3>
                  <p className="text-xs text-[var(--clr-text-muted)]">
                    Weight distribution across topics (should sum to 1.0)
                  </p>
                </div>
                <span
                  className={`text-xs font-mono font-bold px-2.5 py-1 rounded-lg ${
                    Math.abs(ratioSum - 1.0) < 0.01
                      ? 'bg-[var(--clr-success-dim)] text-[var(--clr-success)]'
                      : 'bg-[var(--clr-warning-dim)] text-[var(--clr-warning)]'
                  }`}
                >
                  Σ = {ratioSum.toFixed(2)}
                </span>
              </div>

              {/* Existing topics */}
              <div className="space-y-2 mb-4">
                {Object.entries(form.topic_ratios).map(([key, val]) => (
                  <div key={key} className="flex items-center gap-3">
                    <span className="flex-1 text-sm text-[var(--clr-text-secondary)] truncate">{key}</span>
                    <div className="w-24 relative">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={val}
                        onChange={(e) => updateTopicValue(key, e.target.value)}
                        className="w-full px-3 py-2 rounded-lg text-xs text-white text-center bg-[rgba(22,18,52,0.6)] border border-[var(--clr-glass-border)] focus:border-primary/40 outline-none transition-all font-mono"
                      />
                    </div>
                    {/* Visual bar */}
                    <div className="w-24 h-2 rounded-full bg-white/[0.06] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-primary to-neon transition-all duration-300"
                        style={{ width: `${Math.min(val * 100, 100)}%` }}
                      />
                    </div>
                    <button
                      onClick={() => removeTopic(key)}
                      className="p-1.5 rounded-lg text-[var(--clr-text-muted)] hover:text-[var(--clr-danger)] hover:bg-[var(--clr-danger-dim)] transition-all"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>
                ))}
              </div>

              {/* Add new topic */}
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={newTopicName}
                  onChange={(e) => setNewTopicName(e.target.value)}
                  placeholder="Topic name"
                  className="flex-1 px-3 py-2 rounded-lg text-xs text-white placeholder-[var(--clr-text-muted)] bg-[rgba(22,18,52,0.6)] border border-[var(--clr-glass-border)] focus:border-primary/40 outline-none transition-all"
                  onKeyDown={(e) => e.key === 'Enter' && addTopic()}
                />
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={newTopicValue}
                  onChange={(e) => setNewTopicValue(e.target.value)}
                  placeholder="0.15"
                  className="w-20 px-3 py-2 rounded-lg text-xs text-white text-center placeholder-[var(--clr-text-muted)] bg-[rgba(22,18,52,0.6)] border border-[var(--clr-glass-border)] focus:border-primary/40 outline-none transition-all font-mono"
                  onKeyDown={(e) => e.key === 'Enter' && addTopic()}
                />
                <button
                  type="button"
                  onClick={addTopic}
                  className="px-3 py-2 rounded-lg text-xs font-semibold bg-[var(--clr-primary-dim)] text-[var(--clr-primary)] hover:bg-[var(--clr-primary-vivid)] hover:text-white transition-all"
                >
                  + Add
                </button>
              </div>
            </div>

            {/* Modal actions */}
            <div className="flex items-center justify-end gap-3 mt-8 pt-6 border-t border-white/[0.06]">
              <button
                onClick={() => setShowModal(false)}
                className="btn btn-ghost"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !form.name || !form.slug}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    Saving…
                  </span>
                ) : editingId ? 'Update Job Type' : 'Create Job Type'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ════════════ Delete Confirmation Modal ════════════ */}
      {deletingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setDeletingId(null)} />
          <div className="relative w-full max-w-md glass p-8 animate-in fade-in zoom-in-95 duration-200 text-center">
            <div className="mx-auto mb-5 w-14 h-14 rounded-full bg-[var(--clr-danger-dim)] border border-[rgba(248,113,113,0.2)] flex items-center justify-center">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--clr-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
              </svg>
            </div>
            <h3 className="font-display text-lg font-bold text-white mb-2">Delete Job Type?</h3>
            <p className="text-sm text-[var(--clr-text-secondary)] mb-6">
              This action cannot be undone. All related data may also be affected.
            </p>
            <div className="flex items-center justify-center gap-3">
              <button onClick={() => setDeletingId(null)} className="btn btn-ghost">
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-5 py-2.5 rounded-xl text-sm font-bold bg-[var(--clr-danger)] text-white hover:bg-[var(--clr-danger)]/80 transition-all disabled:opacity-50"
              >
                {deleting ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}

export default function JobTypesPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <JobTypesContent />
    </ProtectedRoute>
  );
}
