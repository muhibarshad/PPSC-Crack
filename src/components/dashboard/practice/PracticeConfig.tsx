'use client';

/**
 * PracticeConfig — Topic selection, question count, timed mode toggle.
 * ===========================================================================
 * The "setup" screen before a practice session starts.
 */

import { useEffect, useState } from 'react';
import Icon from '@/components/Icon';
import { useAuthStore } from '@/store/auth-store';

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

interface TopicOption {
  id: string;
  name: string;
  display_name: string;
  total_questions: number;
  icon: string | null;
  color_hex: string | null;
}

interface PracticeConfigProps {
  onStart: (config: {
    topicId: string | null;
    numQuestions: number;
    timed: boolean;
    topicName: string;
  }) => void;
}

const QUESTION_COUNTS = [10, 25, 50, 100];

export default function PracticeConfig({ onStart }: PracticeConfigProps) {
  const { session } = useAuthStore();

  const [topics, setTopics] = useState<TopicOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [numQuestions, setNumQuestions] = useState(25);
  const [timed, setTimed] = useState(false);

  /* ── Fetch available topics ── */
  useEffect(() => {
    async function load() {
      const token = session?.access_token;
      if (!token) return;
      try {
        const res = await fetch(`${API}/stories/topics`, {
          headers: { Authorization: `Bearer ${token}` },
          credentials: 'include',
        });
        if (res.ok) {
          const data = await res.json();
          // API might return {topics: [...]} or a plain array
          const list = Array.isArray(data) ? data : data.topics ?? [];
          setTopics(list.filter((t: TopicOption) => t.total_questions > 0));
        }
      } catch {
        // silently ignore — user can still do Full Paper mode
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [session?.access_token]);

  const selectedName =
    selectedTopic === null
      ? 'Full Paper (All Topics)'
      : topics.find((t) => t.id === selectedTopic)?.display_name ?? 'Selected Topic';

  return (
    <div className="flex flex-col gap-8 animate-fade-in-up">
      {/* ═══ Header ═══ */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
             style={{ background: 'var(--clr-primary-dim)' }}>
          <Icon name="target" size={32} color="var(--clr-primary)" />
        </div>
        <h1 className="font-display text-3xl md:text-4xl font-bold text-white">
          Practice <span className="gradient-text">Test</span>
        </h1>
        <p className="text-[var(--clr-text-secondary)] mt-2 max-w-md mx-auto">
          Choose your topic, set the question count, and challenge yourself.
        </p>
      </div>

      {/* ═══ Topic Selection ═══ */}
      <div className="glass p-6">
        <h2 className="font-display text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Icon name="book-open" size={18} color="var(--clr-primary)" />
          Select Topic
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {/* Full Paper Mode card */}
          <button
            onClick={() => setSelectedTopic(null)}
            className={`practice-topic-card group ${selectedTopic === null ? 'practice-topic-active' : ''}`}
          >
            <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-2"
                 style={{ background: selectedTopic === null ? 'var(--clr-primary-dim)' : 'rgba(255,255,255,0.04)' }}>
              <Icon name="zap" size={18}
                    color={selectedTopic === null ? 'var(--clr-primary)' : 'var(--clr-text-muted)'} />
            </div>
            <span className="text-sm font-medium text-white leading-tight">Full Paper</span>
            <span className="text-[10px] text-[var(--clr-text-muted)] mt-0.5">All Topics</span>
          </button>

          {loading
            ? Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="practice-topic-card animate-pulse"
                     style={{ background: 'rgba(255,255,255,0.02)' }}>
                  <div className="w-9 h-9 rounded-xl bg-[rgba(255,255,255,0.04)] mb-2" />
                  <div className="w-16 h-3 bg-[rgba(255,255,255,0.04)] rounded" />
                </div>
              ))
            : topics.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTopic(t.id)}
                  className={`practice-topic-card group ${selectedTopic === t.id ? 'practice-topic-active' : ''}`}
                >
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-2"
                       style={{
                         background: selectedTopic === t.id
                           ? `${t.color_hex ?? 'var(--clr-primary)'}20`
                           : 'rgba(255,255,255,0.04)',
                       }}>
                    <Icon
                      name={t.icon ?? 'book-open'}
                      size={18}
                      color={selectedTopic === t.id ? (t.color_hex ?? 'var(--clr-primary)') : 'var(--clr-text-muted)'}
                    />
                  </div>
                  <span className="text-sm font-medium text-white leading-tight line-clamp-2">
                    {t.display_name}
                  </span>
                  <span className="text-[10px] text-[var(--clr-text-muted)] mt-0.5">
                    {t.total_questions} Qs
                  </span>
                </button>
              ))}
        </div>
      </div>

      {/* ═══ Question Count ═══ */}
      <div className="glass p-6">
        <h2 className="font-display text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Icon name="file-text" size={18} color="var(--clr-accent)" />
          Number of Questions
        </h2>
        <div className="flex flex-wrap gap-3">
          {QUESTION_COUNTS.map((n) => (
            <button
              key={n}
              onClick={() => setNumQuestions(n)}
              className={`px-6 py-3 rounded-xl font-display font-bold text-lg transition-all duration-200
                ${numQuestions === n
                  ? 'bg-[var(--clr-primary)] text-white shadow-[0_4px_25px_rgba(139,92,246,0.4)]'
                  : 'glass-sm text-[var(--clr-text-secondary)] hover:text-white hover:border-[var(--clr-glass-border-hover)]'
                }`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {/* ═══ Timed Toggle ═══ */}
      <div className="glass p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-display text-lg font-semibold text-white flex items-center gap-2">
              <Icon name="zap" size={18} color="var(--clr-gold)" />
              Timed Mode
            </h2>
            <p className="text-sm text-[var(--clr-text-secondary)] mt-1">
              {timed
                ? `${numQuestions} minutes countdown (1 min / question)`
                : 'Take your time — no time limit'}
            </p>
          </div>
          <button
            onClick={() => setTimed(!timed)}
            className={`relative w-14 h-8 rounded-full transition-colors duration-300
              ${timed ? 'bg-[var(--clr-primary)]' : 'bg-[rgba(255,255,255,0.1)]'}`}
            aria-label="Toggle timed mode"
          >
            <span
              className={`absolute top-1 left-1 w-6 h-6 rounded-full bg-white shadow-md transition-transform duration-300
                ${timed ? 'translate-x-6' : 'translate-x-0'}`}
            />
          </button>
        </div>
      </div>

      {/* ═══ Start Button ═══ */}
      <button
        onClick={() =>
          onStart({
            topicId: selectedTopic,
            numQuestions,
            timed,
            topicName: selectedName,
          })
        }
        className="btn btn-primary btn-lg w-full text-lg animate-pulse-glow"
      >
        <Icon name="play" size={20} />
        Start Practice — {numQuestions} Questions
      </button>
    </div>
  );
}
