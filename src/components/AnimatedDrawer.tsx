/**
 * AnimatedDrawer — Slide-in drawer from the right with spring physics.
 * Scale from 0.95 to 1 with fade.
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';

interface AnimatedDrawerProps {
  isOpen: boolean;
  children: React.ReactNode;
  onClose?: () => void;
  className?: string;
  /** 'right' (default) | 'left' | 'bottom' */
  direction?: 'right' | 'left' | 'bottom';
}

const getSlideVariants = (direction: string) => {
  const offset = direction === 'right' ? { x: '100%' } : direction === 'left' ? { x: '-100%' } : { y: '100%' };
  return {
    hidden: {
      ...offset,
      opacity: 0,
    },
    visible: {
      x: 0,
      y: 0,
      opacity: 1,
      transition: {
        type: 'spring' as const,
        damping: 30,
        stiffness: 300,
      },
    },
    exit: {
      ...offset,
      opacity: 0,
      transition: {
        duration: 0.2,
        ease: [0.42, 0, 0.58, 1] as const,
      },
    },
  };
};

export default function AnimatedDrawer({
  isOpen,
  children,
  onClose,
  className = '',
  direction = 'right',
}: AnimatedDrawerProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            key="drawer-backdrop"
            className="fixed inset-0 z-[998] bg-black/50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            key="drawer"
            className={`fixed z-[999] ${
              direction === 'right'
                ? 'top-0 right-0 h-full'
                : direction === 'left'
                  ? 'top-0 left-0 h-full'
                  : 'bottom-0 left-0 w-full'
            } ${className}`}
            variants={getSlideVariants(direction)}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
