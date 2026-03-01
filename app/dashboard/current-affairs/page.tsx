/**
 * Current Affairs Feed — /dashboard/current-affairs
 * ===================================================
 * Card-based feed with:
 *  • Category filter tabs (All / Government / Sports / Science / Economy / International)
 *  • Inline MCQ per card — tap to answer, reveal correct answer
 *  • "Mark as Learned" — moves card to Done section
 *  • Star badge for items included in predictions
 *  • Smooth slide-in-from-right spring animations
 *  • Pagination (Load More) for older items
 */

'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import gsap from 'gsap';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/store/auth-store';
import Icon from '@/components/Icon';

/* ═══════════════════════════════════════════
   Types
   ═══════════════════════════════════════════ */

interface CAItem {
  id: string;
  headline: string;
  summary: string | null;
  content: string;
  category: string;
  source_name: string | null;
  source_url: string | null;
  published_date: string | null;
  relevance_score: number;
  mcq_generated: boolean;
  mcq_text: string | null;
  mcq_options: Record<string, string> | null;
  mcq_correct_answer: string | null;
  mcq_explanation: string | null;
  is_included_in_prediction: boolean;
  is_learned: boolean;
}

interface CAListResponse {
  items: CAItem[];
  total: number;
  page: number;
  per_page: number;
  categories: string[];
}

/* ═══════════════════════════════════════════
   Constants
   ═══════════════════════════════════════════ */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

const CATEGORY_TABS = [
  { key: 'all', label: 'All', icon: 'globe' },
  { key: 'government', label: 'Government', icon: 'shield' },
  { key: 'sports', label: 'Sports', icon: 'target' },
  { key: 'science', label: 'Science', icon: 'cpu' },
  { key: 'economy', label: 'Economy', icon: 'chart-line' },
  { key: 'international', label: 'International', icon: 'globe' },
] as const;

const CATEGORY_DISPLAY: Record<string, string> = {
  govt_appointment: 'Government',
  sports: 'Sports',
  science: 'Science',
  economy: 'Economy',
  international: 'International',
  records: 'Records',
};

const OPTION_LABELS = ['A', 'B', 'C', 'D'] as const;
const OPTION_KEYS = ['a', 'b', 'c', 'd'] as const;

/* ═══════════════════════════════════════════
   API Helpers
   ═══════════════════════════════════════════ */

async function fetchFeed(
  token: string,
  page: number,
  category: string | null,
): Promise<CAListResponse> {
  const params = new URLSearchParams();
  params.set('page', String(page));
  params.set('per_page', '20');
  if (category && category !== 'all') params.set('category', category);

  const res = await fetch(`${API}/student/current-affairs?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || 'Failed to load current affairs');
  }
  return res.json();
}

async function postMarkLearned(
  token: string,
  articleId: string,
): Promise<{ is_learned: boolean }> {
  const res = await fetch(`${API}/student/current-affairs/${articleId}/learned`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed' }));
    throw new Error(err.detail || 'Failed to mark as learned');
  }
  return res.json();
}

/* ═══════════════════════════════════════════
   Sub-Components
   ═══════════════════════════════════════════ */

/* ── Category Tabs ── */
function CategoryTabs({
  active,
  onChange,
}: {
  active: string;
  onChange: (key: string) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none">
      {CATEGORY_TABS.map((tab) => {
        const isActive = active === tab.key;
        return (
          <button
            key={tab.key}
            onClick={() => onChange(tab.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-medium whitespace-nowrap transition-all ${
              isActive
                ? 'ca-tab-active'
                : 'border-[var(--clr-glass-border)] text-[var(--clr-text-muted)] hover:border-[var(--clr-glass-border-hover)] hover:text-[var(--clr-text-secondary)]'
            }`}
          >
            <Icon name={tab.icon} size={14} />
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

/* ── MCQ Section inside a card ── */
function InlineMCQ({
  mcqText,
  mcqOptions,
  correctAnswer,
  explanation,
}: {
  mcqText: string;
  mcqOptions: Record<string, string>;
  correctAnswer: string;
  explanation: string | null;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);
  const optionRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  const handleSelect = (key: string) => {
    if (revealed) return;
    setSelected(key);
    setRevealed(true);

    // GSAP feedback on correct answer element
    const correctEl = optionRefs.current.get(correctAnswer);
    if (correctEl) {
      gsap.fromTo(correctEl,
        { boxShadow: 'none' },
        {
          boxShadow: '0 0 0 3px rgba(52, 211, 153, 0.4), 0 0 20px rgba(52, 211, 153, 0.2)',
          duration: 0.4,
          ease: 'power2.out',
          yoyo: true,
          repeat: 1,
        },
      );
    }

    // GSAP shake on wrong selection
    if (key !== correctAnswer) {
      const wrongEl = optionRefs.current.get(key);
      if (wrongEl) {
        gsap.timeline()
          .to(wrongEl, { x: -6, duration: 0.08 })
          .to(wrongEl, { x: 6, duration: 0.08 })
          .to(wrongEl, { x: -4, duration: 0.08 })
          .to(wrongEl, { x: 0, duration: 0.2, ease: 'power2.out' });
      }
    }
  };

  return (
    <div className="mt-4 pt-4 border-t border-[var(--clr-glass-border)]">
      <p className="text-xs uppercase tracking-widest text-[var(--clr-text-muted)] mb-2">
        📝 Quick MCQ
      </p>
      <p className="text-sm text-white font-medium mb-3 leading-relaxed">{mcqText}</p>

      <div className="grid gap-2">
        {OPTION_KEYS.map((key, i) => {
          const label = OPTION_LABELS[i];
          const optionText = mcqOptions[key];
          if (!optionText) return null;

          const isSelected = selected === key;
          const isCorrect = correctAnswer === key;

          let stateClass = '';
          if (revealed) {
            if (isCorrect) stateClass = 'ca-mcq-correct';
            else if (isSelected && !isCorrect) stateClass = 'ca-mcq-wrong';
          }

          return (
            <button
              key={key}
              ref={(el) => { if (el) optionRefs.current.set(key, el); }}
              onClick={() => handleSelect(key)}
              disabled={revealed}
              className={`flex items-center gap-3 p-2.5 rounded-lg border text-left text-xs transition-all ${stateClass} ${
                !revealed
                  ? 'border-[var(--clr-glass-border)] hover:border-[var(--clr-glass-border-hover)] hover:bg-[var(--clr-glass-bg-hover)] text-[var(--clr-text-secondary)]'
                  : isCorrect
                    ? 'border-[var(--clr-success)] bg-[var(--clr-success-dim)] text-[var(--clr-success)]'
                    : isSelected
                      ? 'border-[var(--clr-danger)] bg-[var(--clr-danger-dim)] text-[var(--clr-danger)]'
                      : 'border-[var(--clr-glass-border)] text-[var(--clr-text-muted)] opacity-60'
              }`}
            >
              <span
                className="flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold"
                style={{
                  background:
                    revealed && isCorrect
                      ? 'var(--clr-success-dim)'
                      : revealed && isSelected
                        ? 'var(--clr-danger-dim)'
                        : 'var(--clr-glass-bg)',
                  color:
                    revealed && isCorrect
                      ? 'var(--clr-success)'
                      : revealed && isSelected
                        ? 'var(--clr-danger)'
                        : 'var(--clr-text-muted)',
                }}
              >
                {label}
              </span>
              <span className="flex-1">{optionText}</span>
              {revealed && isCorrect && (
                <Icon name="check" size={14} color="var(--clr-success)" />
              )}
              {revealed && isSelected && !isCorrect && (
                <Icon name="x" size={14} color="var(--clr-danger)" />
              )}
            </button>
          );
        })}
      </div>

      {/* Explanation after answering */}
      {revealed && explanation && (
        <div className="mt-3 p-3 rounded-lg bg-[var(--clr-glass-bg)] border border-[var(--clr-glass-border)]">
          <p className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)] mb-1">
            Explanation
          </p>
          <p className="text-xs text-[var(--clr-text-secondary)] leading-relaxed">
            {explanation}
          </p>
        </div>
      )}
    </div>
  );
}

/* ── Single CA Card ── */
function CACard({
  item,
  index,
  onMarkLearned,
  markingId,
}: {
  item: CAItem;
  index: number;
  onMarkLearned: (id: string) => void;
  markingId: string | null;
}) {
  const displayCategory = CATEGORY_DISPLAY[item.category] || item.category;
  const isMarking = markingId === item.id;

  // Two-sentence summary: first 2 sentences of content if summary missing
  const brief = useMemo(() => {
    if (item.summary) return item.summary;
    const sentences = item.content.split(/(?<=[.!?])\s+/).slice(0, 2);
    return sentences.join(' ');
  }, [item.summary, item.content]);

  return (
    <motion.div
      className={`${item.is_learned ? 'ca-card-learned' : ''}`}
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{
        type: 'spring',
        damping: 25,
        stiffness: 250,
        delay: index * 0.06,
      }}
    >
      <div className="glass p-5 sm:p-6 hover:border-[var(--clr-glass-border-hover)] transition-all">
        {/* Top badges */}
        <div className="flex items-center gap-2 mb-3">
          {/* Category badge */}
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--clr-glass-bg)] text-[var(--clr-text-muted)] uppercase tracking-wider font-medium">
            {displayCategory}
          </span>

          {/* Prediction star badge */}
          {item.is_included_in_prediction && (
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-bold flex items-center gap-1"
              style={{
                background: 'var(--clr-gold-dim)',
                color: 'var(--clr-gold)',
              }}
            >
              <Icon name="star" size={10} color="var(--clr-gold)" />
              In Prediction
            </span>
          )}

          {/* Learned badge */}
          {item.is_learned && (
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-bold flex items-center gap-1"
              style={{
                background: 'var(--clr-success-dim)',
                color: 'var(--clr-success)',
              }}
            >
              <Icon name="check" size={10} color="var(--clr-success)" />
              Done
            </span>
          )}

          {/* Source + Date — right aligned */}
          <div className="ml-auto text-[10px] text-[var(--clr-text-muted)] flex items-center gap-2">
            {item.source_name && <span>{item.source_name}</span>}
            {item.published_date && (
              <span>
                {new Date(item.published_date).toLocaleDateString('en-PK', {
                  month: 'short',
                  day: 'numeric',
                })}
              </span>
            )}
          </div>
        </div>

        {/* Headline */}
        <h3 className="font-display text-lg font-bold text-white leading-snug mb-2">
          {item.headline}
        </h3>

        {/* Brief context — 2 sentences */}
        <p className="text-sm text-[var(--clr-text-secondary)] leading-relaxed mb-3">
          {brief}
        </p>

        {/* Inline MCQ */}
        {item.mcq_generated && item.mcq_text && item.mcq_options && item.mcq_correct_answer && (
          <InlineMCQ
            mcqText={item.mcq_text}
            mcqOptions={item.mcq_options}
            correctAnswer={item.mcq_correct_answer}
            explanation={item.mcq_explanation}
          />
        )}

        {/* Footer: Mark as Learned */}
        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={() => onMarkLearned(item.id)}
            disabled={isMarking}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              item.is_learned
                ? 'bg-[var(--clr-success-dim)] text-[var(--clr-success)] border border-[var(--clr-success)] border-opacity-30'
                : 'bg-[var(--clr-glass-bg)] text-[var(--clr-text-muted)] hover:bg-[var(--clr-glass-bg-hover)] hover:text-[var(--clr-text-secondary)] border border-[var(--clr-glass-border)]'
            }`}
          >
            {isMarking ? (
              <div className="w-3 h-3 rounded-full border-2 border-current border-t-transparent animate-spin" />
            ) : (
              <Icon name="check" size={12} />
            )}
            {item.is_learned ? 'Learned ✓' : 'Mark as Learned'}
          </button>

          {/* Relevance score */}
          <div className="flex items-center gap-1 text-[10px] text-[var(--clr-text-muted)]">
            <Icon name="trending-up" size={10} />
            Relevance: {(item.relevance_score * 100).toFixed(0)}%
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════
   Main Page Content
   ═══════════════════════════════════════════ */

function CurrentAffairsContent() {
  const router = useRouter();
  const { session } = useAuthStore();
  const token = session?.access_token;

  const [items, setItems] = useState<CAItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState('all');
  const [markingId, setMarkingId] = useState<string | null>(null);

  const perPage = 20;

  /* ── Load feed ── */
  const loadFeed = useCallback(
    async (pageNum: number, append: boolean = false) => {
      if (!token) return;

      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }
      setError(null);

      try {
        const data = await fetchFeed(token, pageNum, activeCategory);
        if (append) {
          setItems((prev) => [...prev, ...data.items]);
        } else {
          setItems(data.items);
        }
        setTotal(data.total);
        setPage(pageNum);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Something went wrong');
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [token, activeCategory],
  );

  // Initial load + reload on category change
  useEffect(() => {
    setPage(1);
    setItems([]);
    loadFeed(1);
  }, [loadFeed]);

  /* ── Load more ── */
  const handleLoadMore = useCallback(() => {
    loadFeed(page + 1, true);
  }, [loadFeed, page]);

  const hasMore = items.length < total;

  /* ── Infinite scroll observer ── */
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!sentinelRef.current || !hasMore || loadingMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) {
          handleLoadMore();
        }
      },
      { rootMargin: '200px' },
    );

    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [hasMore, loadingMore, handleLoadMore]);

  /* ── Mark as learned ── */
  const handleMarkLearned = useCallback(
    async (articleId: string) => {
      if (!token) return;
      setMarkingId(articleId);

      try {
        const result = await postMarkLearned(token, articleId);
        setItems((prev) =>
          prev.map((item) =>
            item.id === articleId ? { ...item, is_learned: result.is_learned } : item,
          ),
        );
      } catch (err) {
        console.error('Failed to mark learned', err);
      } finally {
        setMarkingId(null);
      }
    },
    [token],
  );

  /* ── Category change ── */
  const handleCategoryChange = useCallback((key: string) => {
    setActiveCategory(key);
  }, []);

  /* ── Partition items into active / done ── */
  const { activeItems, doneItems } = useMemo(() => {
    const active: CAItem[] = [];
    const done: CAItem[] = [];
    for (const item of items) {
      if (item.is_learned) {
        done.push(item);
      } else {
        active.push(item);
      }
    }
    return { activeItems: active, doneItems: done };
  }, [items]);

  /* ── Loading state ── */
  if (loading) {
    return (
      <div className="min-h-screen z-10 relative pt-24 px-6">
        <div className="max-w-3xl mx-auto flex flex-col items-center justify-center gap-6 py-32">
          <div className="w-16 h-16 rounded-full border-4 border-[var(--clr-primary-dim)] border-t-[var(--clr-primary)] animate-spin" />
          <p className="text-[var(--clr-text-secondary)] text-sm">Loading current affairs…</p>
        </div>
      </div>
    );
  }

  /* ── Error state ── */
  if (error) {
    return (
      <div className="min-h-screen z-10 relative pt-24 px-6">
        <div className="max-w-lg mx-auto py-32">
          <div className="glass p-8 text-center">
            <div className="w-14 h-14 rounded-full bg-[var(--clr-danger-dim)] flex items-center justify-center mx-auto mb-4">
              <Icon name="x" size={24} color="var(--clr-danger)" />
            </div>
            <h2 className="font-display text-xl font-bold text-white mb-2">Oops!</h2>
            <p className="text-[var(--clr-text-secondary)] mb-6">{error}</p>
            <div className="flex gap-3 justify-center">
              <button onClick={() => loadFeed(1)} className="btn btn-primary">
                Try Again
              </button>
              <button onClick={() => router.push('/dashboard')} className="btn btn-ghost">
                Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen z-10 relative pt-24 pb-16 px-4 sm:px-6">
      <div className="max-w-3xl mx-auto flex flex-col gap-6">
        {/* ═══ Header ═══ */}
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 animate-fade-in-up">
          <div>
            <button
              onClick={() => router.push('/dashboard')}
              className="btn btn-ghost btn-sm w-fit mb-2"
            >
              ← Dashboard
            </button>
            <h1 className="font-display text-3xl md:text-4xl font-bold text-white">
              <span className="gradient-text">Current Affairs</span> 📰
            </h1>
            <p className="text-[var(--clr-text-secondary)] mt-1 text-sm">
              Today's exam-relevant news with instant MCQ practice
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-[var(--clr-text-muted)]">
              {total} article{total !== 1 ? 's' : ''}
            </span>
            {doneItems.length > 0 && (
              <span
                className="text-[10px] px-2 py-1 rounded-full font-bold"
                style={{ background: 'var(--clr-success-dim)', color: 'var(--clr-success)' }}
              >
                {doneItems.length} learned
              </span>
            )}
          </div>
        </div>

        {/* ═══ Category Filter Tabs ═══ */}
        <div className="animate-fade-in-up delay-100">
          <CategoryTabs active={activeCategory} onChange={handleCategoryChange} />
        </div>

        {/* ═══ Active Items Feed ═══ */}
        {activeItems.length === 0 && doneItems.length === 0 ? (
          <div className="glass p-12 text-center animate-fade-in-up delay-200">
            <div className="w-16 h-16 rounded-2xl bg-[var(--clr-info-dim)] flex items-center justify-center mx-auto mb-4">
              <Icon name="newspaper" size={32} color="var(--clr-info)" />
            </div>
            <h2 className="font-display text-xl font-bold text-white mb-2">
              No articles yet
            </h2>
            <p className="text-sm text-[var(--clr-text-secondary)]">
              Check back later for today's exam-relevant current affairs.
            </p>
          </div>
        ) : (
          <>
            {/* Active cards */}
            {activeItems.length > 0 && (
              <div className="flex flex-col gap-4">
                {activeItems.map((item, i) => (
                  <CACard
                    key={item.id}
                    item={item}
                    index={i}
                    onMarkLearned={handleMarkLearned}
                    markingId={markingId}
                  />
                ))}
              </div>
            )}

            {/* Done section */}
            {doneItems.length > 0 && (
              <div className="flex flex-col gap-4 mt-4">
                <div className="flex items-center gap-3">
                  <div className="h-px flex-1 bg-[var(--clr-glass-border)]" />
                  <span className="text-xs text-[var(--clr-success)] font-medium flex items-center gap-1">
                    <Icon name="check" size={12} color="var(--clr-success)" />
                    Learned ({doneItems.length})
                  </span>
                  <div className="h-px flex-1 bg-[var(--clr-glass-border)]" />
                </div>

                {doneItems.map((item, i) => (
                  <CACard
                    key={item.id}
                    item={item}
                    index={i}
                    onMarkLearned={handleMarkLearned}
                    markingId={markingId}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {/* ═══ Load More / Infinite Scroll Sentinel ═══ */}
        {hasMore && (
          <div ref={sentinelRef} className="flex justify-center py-6">
            {loadingMore ? (
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-full border-2 border-[var(--clr-primary-dim)] border-t-[var(--clr-primary)] animate-spin" />
                <span className="text-sm text-[var(--clr-text-muted)]">Loading more…</span>
              </div>
            ) : (
              <button onClick={handleLoadMore} className="btn btn-ghost btn-sm">
                Load More
              </button>
            )}
          </div>
        )}

        {/* End of feed */}
        {!hasMore && items.length > 0 && (
          <p className="text-center text-xs text-[var(--clr-text-muted)] py-4">
            You've seen all {total} articles ✨
          </p>
        )}
      </div>
    </div>
  );
}

/* ── Page Export ── */

export default function CurrentAffairsPage() {
  return (
    <ProtectedRoute>
      <CurrentAffairsContent />
    </ProtectedRoute>
  );
}
