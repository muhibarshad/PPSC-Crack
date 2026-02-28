/**
 * SectionQuizBlock — Mini MCQ quiz at the end of each story section.
 * Students must answer all questions correctly to unlock the next section.
 */

'use client';

import { useState, useCallback } from 'react';
import Icon from '@/components/Icon';

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

interface SectionQuizBlockProps {
  quiz: SectionQuiz;
  sectionIndex: number;
  isCompleted: boolean;
  onComplete: () => void;
}

export default function SectionQuizBlock({
  quiz,
  sectionIndex,
  isCompleted,
  onComplete,
}: SectionQuizBlockProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(isCompleted);
  const [showExplanations, setShowExplanations] = useState(false);

  const allAnswered = quiz.questions.every((q) => answers[q.id]);
  const allCorrect = quiz.questions.every((q) => answers[q.id] === q.correct_answer);

  const handleSelect = useCallback((questionId: string, label: string) => {
    if (submitted) return;
    setAnswers((prev) => ({ ...prev, [questionId]: label }));
  }, [submitted]);

  const handleSubmit = useCallback(() => {
    setSubmitted(true);
    setShowExplanations(true);
    if (allCorrect) {
      onComplete();
    }
  }, [allCorrect, onComplete]);

  const handleRetry = useCallback(() => {
    setAnswers({});
    setSubmitted(false);
    setShowExplanations(false);
  }, []);

  if (isCompleted && !showExplanations) {
    return (
      <div
        className="glass-sm"
        style={{
          padding: 'var(--space-4) var(--space-5)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-3)',
          borderLeft: '3px solid var(--clr-success)',
        }}
      >
        <Icon name="check" size={18} color="var(--clr-success)" />
        <span className="text-sm font-medium" style={{ color: 'var(--clr-success)' }}>
          Section quiz completed — next section unlocked ✓
        </span>
      </div>
    );
  }

  return (
    <div
      className="glass"
      style={{
        padding: 'var(--space-6)',
        borderLeft: '3px solid var(--clr-accent)',
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Icon name="sparkles" size={18} color="var(--clr-accent)" />
        <h3 className="font-display text-base font-bold" style={{ color: 'var(--clr-accent)' }}>
          Section Quiz
        </h3>
        <span className="text-xs" style={{ color: 'var(--clr-text-muted)', marginLeft: 'auto' }}>
          {quiz.questions.length} questions
        </span>
      </div>

      {/* Questions */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        {quiz.questions.map((q, qIdx) => {
          const selected = answers[q.id];
          const isCorrectAnswer = submitted && selected === q.correct_answer;
          const isWrongAnswer = submitted && selected && selected !== q.correct_answer;

          return (
            <div key={q.id}>
              <p
                className="font-medium mb-3"
                style={{ fontSize: 'var(--text-sm)', color: 'var(--clr-text-primary)' }}
              >
                <span style={{ color: 'var(--clr-text-muted)' }}>Q{qIdx + 1}.</span> {q.question}
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {q.options.map((opt) => {
                  const isSelected = selected === opt.label;
                  const isCorrect = submitted && opt.label === q.correct_answer;
                  const isWrong = submitted && isSelected && opt.label !== q.correct_answer;

                  let borderColor = 'var(--clr-glass-border)';
                  let bgColor = 'transparent';
                  if (isSelected && !submitted) {
                    borderColor = 'var(--clr-accent)';
                    bgColor = 'var(--clr-accent-dim)';
                  }
                  if (isCorrect) {
                    borderColor = 'var(--clr-success)';
                    bgColor = 'var(--clr-success-dim)';
                  }
                  if (isWrong) {
                    borderColor = 'var(--clr-danger)';
                    bgColor = 'var(--clr-danger-dim)';
                  }

                  return (
                    <button
                      key={opt.label}
                      onClick={() => handleSelect(q.id, opt.label)}
                      disabled={submitted}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-3)',
                        padding: 'var(--space-3) var(--space-4)',
                        borderRadius: 'var(--radius-md)',
                        border: `1px solid ${borderColor}`,
                        background: bgColor,
                        textAlign: 'left',
                        transition: 'all var(--duration-fast) var(--ease-out)',
                        cursor: submitted ? 'default' : 'pointer',
                        width: '100%',
                      }}
                    >
                      <span
                        className="text-xs font-bold"
                        style={{
                          width: '24px',
                          height: '24px',
                          borderRadius: 'var(--radius-full)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                          background: isSelected ? 'var(--clr-accent-dim)' : 'rgba(82, 77, 115, 0.1)',
                          color: isCorrect ? 'var(--clr-success)' : isWrong ? 'var(--clr-danger)' : 'var(--clr-text-secondary)',
                        }}
                      >
                        {isCorrect ? '✓' : isWrong ? '✗' : opt.label}
                      </span>
                      <span className="text-sm" style={{ color: 'var(--clr-text-primary)' }}>
                        {opt.text}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Explanation */}
              {showExplanations && q.explanation && (
                <div
                  style={{
                    marginTop: 'var(--space-3)',
                    padding: 'var(--space-3) var(--space-4)',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(56, 189, 248, 0.06)',
                    borderLeft: '2px solid var(--clr-info)',
                  }}
                >
                  <p className="text-xs" style={{ color: 'var(--clr-info)' }}>
                    <strong>Explanation:</strong> {q.explanation}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3" style={{ marginTop: 'var(--space-6)' }}>
        {!submitted ? (
          <button
            className="btn btn-primary btn-sm"
            disabled={!allAnswered}
            onClick={handleSubmit}
            style={{ opacity: allAnswered ? 1 : 0.5 }}
          >
            <Icon name="check" size={14} />
            Submit Answers
          </button>
        ) : allCorrect ? (
          <div className="flex items-center gap-2">
            <Icon name="check" size={18} color="var(--clr-success)" />
            <span className="text-sm font-semibold" style={{ color: 'var(--clr-success)' }}>
              All correct! Next section unlocked 🎉
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <span className="text-sm" style={{ color: 'var(--clr-danger)' }}>
              Some answers are incorrect. Review and try again.
            </span>
            <button className="btn btn-ghost btn-sm" onClick={handleRetry}>
              <Icon name="arrow-right" size={14} className="rotate-180" />
              Retry
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
