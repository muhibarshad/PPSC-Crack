/**
 * Story Document Reader — /dashboard/topics/[id]/story
 * ======================================================
 * Full-screen immersive reading experience with:
 *  - Beautiful typography, readable line length
 *  - GSAP ScrollTrigger reading progress bar
 *  - Auto-highlighted dates, entities, organizations
 *  - High-frequency facts badges
 *  - Mini-quiz at section end (GPT-4o generated)
 *  - Bookmark system (click paragraph)
 *  - Personal inline notes (click margin)
 *  - Reading progress saved to backend
 */

'use client';

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/store/auth-store';
import Icon from '@/components/Icon';
import StoryProgressBar from '@/components/dashboard/story/StoryProgressBar';
import StorySectionBlock from '@/components/dashboard/story/StorySectionBlock';
import SectionQuizBlock from '@/components/dashboard/story/SectionQuizBlock';
import BookmarkPanel from '@/components/dashboard/story/BookmarkPanel';
import NoteEditor from '@/components/dashboard/story/NoteEditor';
import { useConfetti } from '@/lib/animations';

gsap.registerPlugin(ScrollTrigger);

/* ── Types matching backend StoryReaderResponse ── */

interface QuizOption {
  label: string;
  text: string;
}

interface QuizQuestion {
  id: string;
  question: string;
  options: QuizOption[];
  correct_answer: string;
  explanation: string;
}

interface SectionQuiz {
  section_index: number;
  questions: QuizQuestion[];
}

interface HighFreqFact {
  fact_text: string;
  repeat_count: number;
  question_text: string | null;
}

interface BookmarkData {
  paragraph_index: number;
  text_preview: string;
  created_at: string;
}

interface InlineNote {
  section_index: number;
  note_text: string;
  created_at: string;
}

interface StoryReaderData {
  topic_id: string;
  topic_name: string;
  display_name: string;
  story_document: string | null;
  story_word_count: number;
  story_last_updated: string | null;
  total_questions: number;
  frequency_score: number;
  color_hex: string | null;
  icon: string | null;
  high_freq_facts: HighFreqFact[];
  reading_progress: number;
  sections_unlocked: number;
  bookmarks: BookmarkData[];
  notes: InlineNote[];
  quizzes: SectionQuiz[];
}

/* ── API helpers ── */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function fetchStoryReader(topicId: string, token: string): Promise<StoryReaderData> {
  const res = await fetch(`${API}/student/topics/${topicId}/story`, {
    headers: { Authorization: `Bearer ${token}` },
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to load story' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function saveProgress(
  topicId: string,
  token: string,
  data: {
    reading_progress: number;
    sections_unlocked: number;
    bookmarks: BookmarkData[];
    notes: InlineNote[];
    completed?: boolean;
  },
) {
  await fetch(`${API}/student/topics/${topicId}/progress`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(data),
  });
}

async function generateQuiz(
  topicId: string,
  token: string,
  sectionIndex: number,
  sectionText: string,
): Promise<SectionQuiz> {
  const res = await fetch(`${API}/student/topics/${topicId}/quiz`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ section_index: sectionIndex, section_text: sectionText }),
  });
  if (!res.ok) {
    throw new Error('Failed to generate quiz');
  }
  const data = await res.json();
  return data.quiz;
}

/* ── Parse story into sections ── */

interface StorySection {
  title: string;
  paragraphs: string[];
  rawText: string;
}

function parseStorySections(doc: string): StorySection[] {
  // Split by markdown-style headings (## or ### or bold lines)
  const lines = doc.split('\n');
  const sections: StorySection[] = [];
  let currentTitle = 'Introduction';
  let currentParagraphs: string[] = [];
  let currentRaw: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();

    // Detect heading patterns
    const headingMatch = trimmed.match(/^#{1,4}\s+(.+)/);
    const boldHeading = trimmed.match(/^\*\*(.+)\*\*$/);

    if (headingMatch || boldHeading) {
      // Save previous section
      if (currentParagraphs.length > 0) {
        sections.push({
          title: currentTitle,
          paragraphs: currentParagraphs,
          rawText: currentRaw.join('\n'),
        });
      }
      currentTitle = headingMatch ? headingMatch[1] : boldHeading![1];
      currentParagraphs = [];
      currentRaw = [];
    } else if (trimmed.length > 0) {
      currentParagraphs.push(trimmed);
      currentRaw.push(trimmed);
    }
  }

  // Push final section
  if (currentParagraphs.length > 0) {
    sections.push({
      title: currentTitle,
      paragraphs: currentParagraphs,
      rawText: currentRaw.join('\n'),
    });
  }

  // If no sections were created, make one from the whole document
  if (sections.length === 0 && doc.trim().length > 0) {
    sections.push({
      title: 'Story',
      paragraphs: doc.split('\n').filter((l) => l.trim()),
      rawText: doc,
    });
  }

  return sections;
}

/* ── Content ── */

function StoryReaderContent() {
  const params = useParams();
  const router = useRouter();
  const { session } = useAuthStore();
  const topicId = params.id as string;
  const fireConfetti = useConfetti();
  const confettiFiredRef = useRef(false);

  const [data, setData] = useState<StoryReaderData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Reader state
  const [bookmarks, setBookmarks] = useState<BookmarkData[]>([]);
  const [notes, setNotes] = useState<InlineNote[]>([]);
  const [sectionsUnlocked, setSectionsUnlocked] = useState(1);
  const [quizzes, setQuizzes] = useState<Map<number, SectionQuiz>>(new Map());
  const [quizLoadingIdx, setQuizLoadingIdx] = useState<number | null>(null);
  const [showBookmarkPanel, setShowBookmarkPanel] = useState(false);
  const [activeNoteSection, setActiveNoteSection] = useState<number | null>(null);
  const [readingProgress, setReadingProgress] = useState(0);

  const contentRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef(0);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const token = session?.access_token;

  /* ── Fetch story data ── */
  useEffect(() => {
    if (!topicId || !token) return;

    fetchStoryReader(topicId, token)
      .then((res) => {
        setData(res);
        setBookmarks(res.bookmarks || []);
        setNotes(res.notes || []);
        setSectionsUnlocked(Math.max(1, res.sections_unlocked));
        setReadingProgress(res.reading_progress);

        // Load cached quizzes
        const qMap = new Map<number, SectionQuiz>();
        for (const q of res.quizzes || []) {
          qMap.set(q.section_index, q);
        }
        setQuizzes(qMap);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [topicId, token]);

  /* ── Parse sections ── */
  const sections = useMemo(() => {
    if (!data?.story_document) return [];
    return parseStorySections(data.story_document);
  }, [data?.story_document]);

  /* ── Auto-save progress (debounced) ── */
  const debouncedSave = useCallback(() => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      if (!token || !topicId) return;
      const completed = progressRef.current >= 0.95 && sectionsUnlocked >= sections.length;
      saveProgress(topicId, token, {
        reading_progress: progressRef.current,
        sections_unlocked: sectionsUnlocked,
        bookmarks,
        notes,
        completed,
      });
    }, 2000);
  }, [token, topicId, sectionsUnlocked, bookmarks, notes, sections.length]);

  useEffect(() => {
    debouncedSave();
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, [bookmarks, notes, sectionsUnlocked, debouncedSave]);

  /* ── Progress update from scroll ── */
  const handleProgressUpdate = useCallback((progress: number) => {
    progressRef.current = progress;
    setReadingProgress(progress);
  }, []);

  /* ── Bookmark toggle ── */
  const toggleBookmark = useCallback(
    (paragraphIndex: number, textPreview: string) => {
      setBookmarks((prev) => {
        const exists = prev.find((b) => b.paragraph_index === paragraphIndex);
        if (exists) {
          return prev.filter((b) => b.paragraph_index !== paragraphIndex);
        }
        return [
          ...prev,
          {
            paragraph_index: paragraphIndex,
            text_preview: textPreview.slice(0, 100),
            created_at: new Date().toISOString(),
          },
        ];
      });
    },
    [],
  );

  /* ── Note save ── */
  const saveNote = useCallback(
    (sectionIndex: number, noteText: string) => {
      setNotes((prev) => {
        const filtered = prev.filter((n) => n.section_index !== sectionIndex);
        if (noteText.trim()) {
          filtered.push({
            section_index: sectionIndex,
            note_text: noteText,
            created_at: new Date().toISOString(),
          });
        }
        return filtered;
      });
      setActiveNoteSection(null);
    },
    [],
  );

  /* ── Quiz generation ── */
  const handleGenerateQuiz = useCallback(
    async (sectionIndex: number, sectionText: string) => {
      if (!token || !topicId || quizzes.has(sectionIndex)) return;
      setQuizLoadingIdx(sectionIndex);
      try {
        const quiz = await generateQuiz(topicId, token, sectionIndex, sectionText);
        setQuizzes((prev) => new Map(prev).set(sectionIndex, quiz));
      } catch {
        // silently fail — quiz is optional
      } finally {
        setQuizLoadingIdx(null);
      }
    },
    [token, topicId, quizzes],
  );

  /* ── Quiz complete → unlock next section ── */
  const handleQuizComplete = useCallback(
    (sectionIndex: number) => {
      setSectionsUnlocked((prev) => Math.max(prev, sectionIndex + 2));
    },
    [],
  );

  /* ── Build high-freq fact set for text matching ── */
  const highFreqFactTexts = useMemo(() => {
    if (!data) return new Set<string>();
    return new Set(data.high_freq_facts.map((f) => f.fact_text.toLowerCase().trim()));
  }, [data]);

  /* ── Loading / Error states ── */
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center z-10 relative">
        <div className="flex flex-col items-center gap-4">
          <svg className="animate-spin h-10 w-10" viewBox="0 0 24 24" style={{ color: 'var(--clr-primary)' }}>
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm" style={{ color: 'var(--clr-text-secondary)' }}>Loading story…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center z-10 relative">
        <div className="glass p-8 text-center max-w-md">
          <Icon name="x" size={32} color="var(--clr-danger)" />
          <h2 className="font-display text-xl font-bold mt-4">Failed to load story</h2>
          <p className="text-sm mt-2" style={{ color: 'var(--clr-text-secondary)' }}>
            {error || 'Story document not available.'}
          </p>
          <button className="btn btn-ghost mt-6" onClick={() => router.back()}>
            <Icon name="arrow-right" size={14} className="rotate-180" /> Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!data.story_document) {
    return (
      <div className="min-h-screen flex items-center justify-center z-10 relative">
        <div className="glass p-8 text-center max-w-md">
          <Icon name="book-open" size={40} color="var(--clr-primary)" />
          <h2 className="font-display text-xl font-bold mt-4">Story Not Yet Generated</h2>
          <p className="text-sm mt-2" style={{ color: 'var(--clr-text-secondary)' }}>
            The AI story document for <strong>{data.display_name}</strong> hasn&apos;t been generated yet.
            Check back soon!
          </p>
          <button className="btn btn-primary mt-6" onClick={() => router.back()}>
            Back to Learning Path
          </button>
        </div>
      </div>
    );
  }

  const readMinutes = Math.max(1, Math.round(data.story_word_count / 200));

  return (
    <div className="story-reader-root" style={{ minHeight: '100vh', position: 'relative', zIndex: 1 }}>
      {/* ── Progress bar (floating top) ── */}
      <StoryProgressBar
        contentRef={contentRef}
        onProgressUpdate={handleProgressUpdate}
      />

      {/* ── Top bar ── */}
      <div
        className="story-top-bar"
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 50,
          padding: 'var(--space-4) var(--space-6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(6, 6, 15, 0.85)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid var(--clr-glass-border)',
        }}
      >
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="btn btn-ghost btn-sm"
            style={{ padding: '6px 10px' }}
          >
            <Icon name="arrow-right" size={16} className="rotate-180" />
          </button>
          <div>
            <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--clr-text-muted)' }}>
              Story Document
            </p>
            <h1 className="font-display text-lg font-bold" style={{ color: 'var(--clr-text-primary)' }}>
              {data.display_name}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Reading stats */}
          <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--clr-text-secondary)' }}>
            <span className="flex items-center gap-1">
              <Icon name="file-text" size={12} />
              {data.story_word_count.toLocaleString()} words
            </span>
            <span className="flex items-center gap-1">
              <Icon name="book-open" size={12} />
              ~{readMinutes} min
            </span>
            <span className="flex items-center gap-1">
              <Icon name="zap" size={12} color="var(--clr-gold)" />
              {Math.round(readingProgress * 100)}%
            </span>
          </div>

          {/* Bookmark panel toggle */}
          <button
            onClick={() => setShowBookmarkPanel(!showBookmarkPanel)}
            className="btn btn-ghost btn-sm relative"
            style={{ padding: '6px 10px' }}
          >
            <Icon name="star" size={16} color={bookmarks.length > 0 ? 'var(--clr-gold)' : 'currentColor'} />
            {bookmarks.length > 0 && (
              <span
                className="badge-primary"
                style={{
                  position: 'absolute',
                  top: '-2px',
                  right: '-2px',
                  fontSize: '9px',
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-full)',
                }}
              >
                {bookmarks.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* ── Bookmark panel overlay ── */}
      {showBookmarkPanel && (
        <BookmarkPanel
          bookmarks={bookmarks}
          sections={sections}
          onClose={() => setShowBookmarkPanel(false)}
          onJumpTo={(paraIdx) => {
            setShowBookmarkPanel(false);
            document.getElementById(`para-${paraIdx}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }}
          onRemove={(paraIdx) => {
            setBookmarks((prev) => prev.filter((b) => b.paragraph_index !== paraIdx));
          }}
        />
      )}

      {/* ── Main reading content ── */}
      <div ref={contentRef} className="story-content-wrapper" style={{ maxWidth: '720px', margin: '0 auto', padding: 'var(--space-8) var(--space-6) var(--space-32)' }}>
        {/* ── High-frequency facts banner ── */}
        {data.high_freq_facts.length > 0 && (
          <div
            className="glass-sm"
            style={{
              padding: 'var(--space-4) var(--space-5)',
              marginBottom: 'var(--space-8)',
              borderLeft: '3px solid var(--clr-warning)',
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Icon name="zap" size={14} color="var(--clr-warning)" />
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--clr-warning)' }}>
                High Frequency Facts — Appeared in 3+ Papers
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {data.high_freq_facts.slice(0, 8).map((fact, i) => (
                <span key={i} className="badge badge-warning" style={{ fontSize: '10px', textTransform: 'none' }}>
                  🔥 {fact.fact_text.slice(0, 80)}{fact.fact_text.length > 80 ? '…' : ''} ({fact.repeat_count}×)
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── Sections ── */}
        {sections.map((section, sIdx) => {
          const isUnlocked = sIdx < sectionsUnlocked;
          const isLast = sIdx === sections.length - 1;
          const sectionNote = notes.find((n) => n.section_index === sIdx);
          const sectionQuiz = quizzes.get(sIdx);
          const globalParaOffset = sections.slice(0, sIdx).reduce((acc, s) => acc + s.paragraphs.length, 0);

          return (
            <div key={sIdx} className="story-section" style={{ marginBottom: 'var(--space-12)' }}>
              {isUnlocked ? (
                <>
                  <StorySectionBlock
                    sectionIndex={sIdx}
                    title={section.title}
                    paragraphs={section.paragraphs}
                    globalParaOffset={globalParaOffset}
                    bookmarks={bookmarks}
                    highFreqFactTexts={highFreqFactTexts}
                    onToggleBookmark={toggleBookmark}
                    onOpenNote={() => setActiveNoteSection(sIdx)}
                    existingNote={sectionNote?.note_text}
                  />

                  {/* Inline note display */}
                  {sectionNote && activeNoteSection !== sIdx && (
                    <div
                      className="glass-sm"
                      style={{
                        padding: 'var(--space-3) var(--space-4)',
                        margin: 'var(--space-4) 0',
                        borderLeft: '3px solid var(--clr-neon)',
                        cursor: 'pointer',
                      }}
                      onClick={() => setActiveNoteSection(sIdx)}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Icon name="file-text" size={12} color="var(--clr-neon)" />
                        <span className="text-xs font-medium" style={{ color: 'var(--clr-neon)' }}>Your Note</span>
                      </div>
                      <p className="text-sm" style={{ color: 'var(--clr-text-secondary)' }}>{sectionNote.note_text}</p>
                    </div>
                  )}

                  {/* Note editor */}
                  {activeNoteSection === sIdx && (
                    <NoteEditor
                      sectionIndex={sIdx}
                      initialText={sectionNote?.note_text || ''}
                      onSave={saveNote}
                      onCancel={() => setActiveNoteSection(null)}
                    />
                  )}

                  {/* Section quiz area */}
                  {!isLast && (
                    <div style={{ margin: 'var(--space-8) 0' }}>
                      {sectionQuiz ? (
                        <SectionQuizBlock
                          quiz={sectionQuiz}
                          sectionIndex={sIdx}
                          isCompleted={sIdx + 1 < sectionsUnlocked}
                          onComplete={() => handleQuizComplete(sIdx)}
                        />
                      ) : (
                        <div className="text-center" style={{ padding: 'var(--space-6) 0' }}>
                          <button
                            className="btn btn-ghost"
                            onClick={() => handleGenerateQuiz(sIdx, section.rawText)}
                            disabled={quizLoadingIdx === sIdx}
                          >
                            {quizLoadingIdx === sIdx ? (
                              <>
                                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                Generating Quiz…
                              </>
                            ) : (
                              <>
                                <Icon name="sparkles" size={14} />
                                Take Section Quiz to Continue
                              </>
                            )}
                          </button>
                          {sIdx + 1 >= sectionsUnlocked && sIdx + 1 < sections.length && (
                            <p className="text-xs mt-2" style={{ color: 'var(--clr-text-muted)' }}>
                              Complete the quiz to unlock the next section
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                /* ── Locked section ── */
                <div
                  className="glass-sm"
                  style={{
                    padding: 'var(--space-8)',
                    textAlign: 'center',
                    opacity: 0.5,
                    filter: 'blur(0px)',
                  }}
                >
                  <Icon name="lock" size={32} color="var(--clr-text-muted)" />
                  <h3 className="font-display text-lg font-bold mt-3" style={{ color: 'var(--clr-text-muted)' }}>
                    {section.title}
                  </h3>
                  <p className="text-sm mt-2" style={{ color: 'var(--clr-text-muted)' }}>
                    Complete the previous section quiz to unlock
                  </p>
                </div>
              )}
            </div>
          );
        })}

        {/* ── Completion badge with confetti burst ── */}
        {readingProgress >= 0.95 && sectionsUnlocked >= sections.length && (
          <CompletionBadge
            displayName={data.display_name}
            onBack={() => router.back()}
            fireConfetti={fireConfetti}
            confettiFiredRef={confettiFiredRef}
          />
        )}
      </div>
    </div>
  );
}

/* ── Completion badge — fires confetti on mount ── */
function CompletionBadge({
  displayName,
  onBack,
  fireConfetti,
  confettiFiredRef,
}: {
  displayName: string;
  onBack: () => void;
  fireConfetti: () => void;
  confettiFiredRef: React.MutableRefObject<boolean>;
}) {
  useEffect(() => {
    if (!confettiFiredRef.current) {
      confettiFiredRef.current = true;
      // Small delay to let the element render
      setTimeout(fireConfetti, 300);
    }
  }, [fireConfetti, confettiFiredRef]);

  return (
    <div
      className="glass text-center animate-fade-in-up"
      style={{ padding: 'var(--space-8)', marginTop: 'var(--space-12)' }}
    >
      <div style={{ fontSize: '48px' }}>🎉</div>
      <h2 className="font-display text-2xl font-bold gradient-text mt-4">Story Complete!</h2>
      <p className="text-sm mt-2" style={{ color: 'var(--clr-text-secondary)' }}>
        You&apos;ve finished reading <strong>{displayName}</strong>. Great work!
      </p>
      <button className="btn btn-primary mt-6" onClick={onBack}>
        <Icon name="arrow-right" size={14} className="rotate-180" />
        Back to Learning Path
      </button>
    </div>
  );
}

/* ── Wrapped with ProtectedRoute ── */

export default function StoryReaderPage() {
  return (
    <ProtectedRoute requiredRole="student">
      <StoryReaderContent />
    </ProtectedRoute>
  );
}
