/**
 * ToastNotification — Slide-in from top-right notification component.
 * Auto-dismisses after a configurable duration.
 */

'use client';

import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Icon from '@/components/Icon';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
}

interface ToastNotificationProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}

const iconMap: Record<string, string> = {
  success: 'check',
  error: 'x',
  info: 'info',
  warning: 'alert-triangle',
};

const colorMap: Record<string, string> = {
  success: 'var(--clr-success)',
  error: 'var(--clr-danger)',
  info: 'var(--clr-info)',
  warning: 'var(--clr-warning)',
};

const bgMap: Record<string, string> = {
  success: 'var(--clr-success-dim)',
  error: 'var(--clr-danger-dim)',
  info: 'var(--clr-info-dim)',
  warning: 'var(--clr-warning-dim)',
};

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(toast.id), toast.duration || 4000);
    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onDismiss]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 100, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.95 }}
      transition={{ type: 'spring', damping: 25, stiffness: 300 }}
      className="glass-sm flex items-center gap-3 px-4 py-3 min-w-[280px] max-w-[400px] cursor-pointer"
      style={{ borderLeft: `3px solid ${colorMap[toast.type]}` }}
      onClick={() => onDismiss(toast.id)}
    >
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
        style={{ background: bgMap[toast.type] }}
      >
        <Icon name={iconMap[toast.type]} size={16} color={colorMap[toast.type]} />
      </div>
      <p className="text-sm text-[var(--clr-text-primary)] leading-snug flex-1">
        {toast.message}
      </p>
    </motion.div>
  );
}

export default function ToastNotification({ toasts, onDismiss }: ToastNotificationProps) {
  return (
    <div className="fixed top-4 right-4 z-[1000] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <ToastItem toast={toast} onDismiss={onDismiss} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
}
