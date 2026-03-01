/**
 * AnimatedModal — Scale from 0.95 to 1 with fade.
 * Use around any modal/drawer content for enter/exit animations.
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';

interface AnimatedModalProps {
  isOpen: boolean;
  children: React.ReactNode;
  onClose?: () => void;
  /** Extra class for the modal wrapper */
  className?: string;
}

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

const modalVariants = {
  hidden: {
    opacity: 0,
    scale: 0.95,
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.25,
      ease: [0.42, 0, 0.58, 1] as const,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: {
      duration: 0.2,
      ease: [0.42, 0, 0.58, 1] as const,
    },
  },
} as const;

export default function AnimatedModal({ isOpen, children, onClose, className = '' }: AnimatedModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            className="fixed inset-0 z-[998] bg-black/60 backdrop-blur-sm"
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            onClick={onClose}
          />

          {/* Modal content */}
          <motion.div
            key="modal"
            className={`fixed inset-0 z-[999] flex items-center justify-center p-4 pointer-events-none ${className}`}
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            <div className="pointer-events-auto max-h-[90vh] overflow-y-auto">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
