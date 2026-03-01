/**
 * Prediction Studio — Publish Confirmation Modal
 * =================================================
 * Glass modal with confirmation dialog before publishing.
 */

'use client';

import { useEffect } from 'react';
import AnimatedModal from '@/components/AnimatedModal';

interface PublishModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isPublishing: boolean;
  questionCount: number;
  jobTypeName: string;
}

export default function PublishModal({
  isOpen,
  onClose,
  onConfirm,
  isPublishing,
  questionCount,
  jobTypeName,
}: PublishModalProps) {
  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <AnimatedModal isOpen={isOpen} onClose={onClose}>
      <div className="glass relative w-full max-w-md mx-4 p-0 overflow-hidden">
        {/* Header */}
        <div className="px-6 pt-6 pb-4">
          <div className="flex items-center gap-3 mb-4">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center"
              style={{ background: 'rgba(248, 113, 113, 0.1)' }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Publish Prediction</h3>
              <p className="text-xs text-[var(--clr-text-muted)]">
                This action makes the paper visible to students
              </p>
            </div>
          </div>

          {/* Summary */}
          <div className="glass-sm p-4 mb-4">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--clr-text-muted)]">Job Type</span>
                <span className="text-white font-semibold">{jobTypeName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--clr-text-muted)]">Questions</span>
                <span className="text-white font-semibold">{questionCount}</span>
              </div>
            </div>
          </div>

          <p className="text-xs text-[var(--clr-text-secondary)] leading-relaxed">
            Once published, students subscribed to <strong className="text-white">{jobTypeName}</strong> will
            immediately see this predicted paper in their dashboard. This action can be undone later.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 px-6 py-4 border-t border-white/[0.06]">
          <button
            onClick={onClose}
            disabled={isPublishing}
            className="flex-1 py-2.5 rounded-xl text-xs font-bold text-[var(--clr-text-secondary)] bg-white/[0.04] hover:bg-white/[0.08] transition-all disabled:opacity-40"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isPublishing}
            className="flex-1 py-2.5 rounded-xl text-xs font-bold text-white transition-all duration-300 disabled:opacity-70"
            style={{
              background: 'linear-gradient(135deg, #f87171 0%, #ef4444 100%)',
              boxShadow: '0 0 25px rgba(248, 113, 113, 0.3)',
            }}
          >
            {isPublishing ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-3.5 h-3.5" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                </svg>
                Publishing…
              </span>
            ) : (
              '🚀 Confirm Publish'
            )}
          </button>
        </div>
      </div>
    </AnimatedModal>
  );
}
