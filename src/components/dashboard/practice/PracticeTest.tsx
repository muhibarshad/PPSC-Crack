'use client';

/**
 * PracticeTest — One question at a time with answer feedback animations.
 * ========================================================================
 * Shows large question text, 4 clickable option cards, countdown timer,
 * progress bar.  Green flash on correct, red shake on wrong.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import gsap from 'gsap';
import Icon from '@/components/Icon';

/* ── Types matching PracticeGenerateResponse ── */

export interface PracticeQuestion {
  id: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  topic_id: string | null;
  topic_name: string | null;
  difficulty_score: number;
}

interface AnswerRecord {
  question_id: string;
  selected_answer: string;
}

interface PracticeTestProps {
  questions: PracticeQuestion[];
  testId: string;
  timeLimitSeconds: number | null;
  onFinish: (answers: AnswerRecord[], timeTaken: number) => void;
  onQuit: () => void;
}

const OPTION_KEYS: ('a' | 'b' | 'c' | 'd')[] = ['a', 'b', 'c', 'd'];
const OPTION_LABELS = { a: 'A', b: 'B', c: 'C', d: 'D' };

export default function PracticeTest({
  questions,
  testId,
  timeLimitSeconds,
  onFinish,
  onQuit,
}: PracticeTestProps) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<AnswerRecord[]>([]);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [feedbackState, setFeedbackState] = useState<'idle' | 'correct' | 'wrong'>('idle');
  const [timeLeft, setTimeLeft] = useState(timeLimitSeconds ?? 0);
  const [elapsed, setElapsed] = useState(0);

  const startTime = useRef(Date.now());
  const feedbackTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const optionRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  const currentQuestion = questions[currentIdx];
  const progress = ((currentIdx) / questions.length) * 100;
  const isLast = currentIdx === questions.length - 1;

  /* ── Timer ── */
  useEffect(() => {
    const interval = setInterval(() => {
      const secs = Math.floor((Date.now() - startTime.current) / 1000);
      setElapsed(secs);
      if (timeLimitSeconds) {
        const remaining = timeLimitSeconds - secs;
        setTimeLeft(remaining);
        if (remaining <= 0) {
          clearInterval(interval);
          // Auto-submit on timeout
          onFinish(answers, timeLimitSeconds);
        }
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [timeLimitSeconds, answers, onFinish]);

  /* ── Keyboard shortcuts ── */
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (feedbackState !== 'idle') return;
      if (e.key === '1' || e.key === 'a') handleAnswer('a');
      else if (e.key === '2' || e.key === 'b') handleAnswer('b');
      else if (e.key === '3' || e.key === 'c') handleAnswer('c');
      else if (e.key === '4' || e.key === 'd') handleAnswer('d');
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentIdx, feedbackState]);

  /* ── Cleanup timeout on unmount ── */
  useEffect(() => {
    return () => {
      if (feedbackTimeout.current) clearTimeout(feedbackTimeout.current);
    };
  }, []);

  /* ── GSAP answer feedback animations ── */
  const gsapFlashCorrect = useCallback((el: HTMLElement) => {
    const tl = gsap.timeline();
    tl.to(el, {
      boxShadow: '0 0 0 4px rgba(52, 211, 153, 0.4), 0 0 30px rgba(52, 211, 153, 0.25)',
      borderColor: 'rgba(52, 211, 153, 0.6)',
      backgroundColor: 'rgba(52, 211, 153, 0.08)',
      duration: 0.3,
      ease: 'power2.out',
    })
      .to(el, {
        boxShadow: '0 0 0 2px rgba(52, 211, 153, 0.2), 0 0 15px rgba(52, 211, 153, 0.1)',
        duration: 0.4,
        ease: 'power2.inOut',
        yoyo: true,
        repeat: 1,
      })
      .to(el, {
        boxShadow: 'none',
        borderColor: '',
        backgroundColor: '',
        duration: 0.3,
        ease: 'power2.out',
      });
  }, []);

  const gsapShakeWrong = useCallback((el: HTMLElement) => {
    const tl = gsap.timeline();
    tl.to(el, {
      borderColor: 'rgba(248, 113, 113, 0.5)',
      backgroundColor: 'rgba(248, 113, 113, 0.08)',
      duration: 0.1,
    })
      .to(el, { x: -8, duration: 0.08 })
      .to(el, { x: 8, duration: 0.08 })
      .to(el, { x: -5, duration: 0.08 })
      .to(el, { x: 0, borderColor: '', backgroundColor: '', duration: 0.3, ease: 'power2.out' });
  }, []);

  /* ── Handle answer selection ── */
  const handleAnswer = useCallback(
    (option: string) => {
      if (feedbackState !== 'idle') return;

      setSelectedOption(option);

      // We don't know the correct answer on the client — we'll show
      // a neutral "selected" flash, then advance.  Real scoring happens on submit.
      // But to keep the fun UX, we'll show "answered" feedback briefly.
      setFeedbackState('correct'); // neutral positive feedback for answering

      // Trigger GSAP flash on the selected option button
      const optionEl = optionRefs.current.get(option);
      if (optionEl) gsapFlashCorrect(optionEl);

      const newAnswers = [...answers, { question_id: currentQuestion.id, selected_answer: option }];
      setAnswers(newAnswers);

      feedbackTimeout.current = setTimeout(() => {
        setFeedbackState('idle');
        setSelectedOption(null);

        if (isLast) {
          const totalTime = Math.floor((Date.now() - startTime.current) / 1000);
          onFinish(newAnswers, totalTime);
        } else {
          setCurrentIdx((prev) => prev + 1);
        }
      }, 600);
    },
    [feedbackState, answers, currentQuestion, isLast, onFinish, gsapFlashCorrect],
  );

  /* ── Option text getter ── */
  const getOptionText = (key: string) => {
    const q = currentQuestion;
    if (key === 'a') return q.option_a;
    if (key === 'b') return q.option_b;
    if (key === 'c') return q.option_c;
    return q.option_d;
  };

  /* ── Format time ── */
  const formatTime = (s: number) => {
    const mins = Math.floor(Math.abs(s) / 60);
    const secs = Math.abs(s) % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const timerDanger = timeLimitSeconds ? timeLeft < 60 : false;

  return (
    <div className="flex flex-col gap-6 animate-fade-in-up">
      {/* ═══ Top Bar: Progress + Timer + Quit ═══ */}
      <div className="glass p-4 flex items-center justify-between gap-4">
        {/* Progress */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <span className="text-sm font-semibold text-white whitespace-nowrap">
            {currentIdx + 1} / {questions.length}
          </span>
          <div className="flex-1 h-2 rounded-full bg-[rgba(255,255,255,0.06)] overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${progress}%`,
                background: 'var(--grad-primary)',
              }}
            />
          </div>
        </div>

        {/* Timer (if timed) */}
        {timeLimitSeconds && (
          <div
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-bold font-display
              ${timerDanger
                ? 'bg-[var(--clr-danger-dim)] text-[var(--clr-danger)] practice-timer-danger'
                : 'bg-[var(--clr-primary-dim)] text-[var(--clr-primary)]'
              }`}
          >
            <Icon name="zap" size={14} />
            {formatTime(timeLeft)}
          </div>
        )}

        {/* Elapsed (untimed) */}
        {!timeLimitSeconds && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
                          bg-[rgba(255,255,255,0.04)] text-[var(--clr-text-secondary)]">
            <Icon name="zap" size={14} />
            {formatTime(elapsed)}
          </div>
        )}

        {/* Quit */}
        <button
          onClick={onQuit}
          className="btn btn-ghost btn-sm text-[var(--clr-danger)] border-[var(--clr-danger-dim)]
                     hover:bg-[var(--clr-danger-dim)]"
        >
          <Icon name="x" size={14} />
          Quit
        </button>
      </div>

      {/* ═══ Topic Badge ═══ */}
      {currentQuestion.topic_name && (
        <div className="flex justify-center">
          <span className="badge badge-primary text-[10px]">
            <Icon name="book-open" size={10} />
            {currentQuestion.topic_name}
          </span>
        </div>
      )}

      {/* ═══ Question Text ═══ */}
      <div
        key={currentQuestion.id}
        className="glass p-8 text-center practice-question-enter"
      >
        <p className="font-display text-xl md:text-2xl font-semibold text-white leading-relaxed">
          {currentQuestion.question_text}
        </p>
      </div>

      {/* ═══ Option Cards ═══ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {OPTION_KEYS.map((key) => {
          const text = getOptionText(key);
          const isSelected = selectedOption === key;
          const isAnswered = feedbackState !== 'idle';

          let cardClass = 'practice-option-card';
          if (isSelected && feedbackState === 'correct') {
            cardClass += ' practice-option-selected';
          }
          if (isAnswered && !isSelected) {
            cardClass += ' opacity-50 pointer-events-none';
          }

          return (
            <button
              key={key}
              ref={(el) => { if (el) optionRefs.current.set(key, el); }}
              onClick={() => handleAnswer(key)}
              disabled={isAnswered}
              className={`${cardClass} glow-card p-5 flex items-start gap-4 text-left transition-all duration-200
                         hover:translate-y-[-4px] cursor-pointer disabled:cursor-default
                         ${isAnswered ? '' : 'active:scale-[0.97]'}`}
            >
              {/* Option label badge */}
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center font-display font-bold text-lg shrink-0
                  ${isSelected
                    ? 'bg-[var(--clr-primary)] text-white'
                    : 'bg-[rgba(255,255,255,0.06)] text-[var(--clr-text-secondary)]'
                  }`}
              >
                {OPTION_LABELS[key]}
              </div>

              {/* Option text */}
              <span className="text-base md:text-lg text-white leading-relaxed pt-1.5">
                {text}
              </span>
            </button>
          );
        })}
      </div>

      {/* ═══ Keyboard hint ═══ */}
      <p className="text-center text-xs text-[var(--clr-text-muted)]">
        Press <span className="font-mono font-bold text-[var(--clr-text-secondary)]">A</span>{' '}
        <span className="font-mono font-bold text-[var(--clr-text-secondary)]">B</span>{' '}
        <span className="font-mono font-bold text-[var(--clr-text-secondary)]">C</span>{' '}
        <span className="font-mono font-bold text-[var(--clr-text-secondary)]">D</span> or{' '}
        <span className="font-mono font-bold text-[var(--clr-text-secondary)]">1-4</span> to answer
      </p>
    </div>
  );
}
