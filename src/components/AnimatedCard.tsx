/**
 * AnimatedCard — Framer Motion wrapper for cards that slide in from right
 * with spring physics. Used for current affairs card feed.
 */

'use client';

import { motion } from 'framer-motion';

interface AnimatedCardProps {
  children: React.ReactNode;
  index?: number;
  className?: string;
  /** 'right' | 'bottom' | 'left' */
  direction?: 'right' | 'bottom' | 'left';
}

const getVariants = (direction: string) => ({
  hidden: {
    opacity: 0,
    x: direction === 'right' ? 40 : direction === 'left' ? -40 : 0,
    y: direction === 'bottom' ? 30 : 0,
  },
  visible: {
    opacity: 1,
    x: 0,
    y: 0,
    transition: {
      type: 'spring' as const,
      damping: 25,
      stiffness: 250,
    },
  },
});

export default function AnimatedCard({
  children,
  index = 0,
  className = '',
  direction = 'right',
}: AnimatedCardProps) {
  return (
    <motion.div
      className={className}
      variants={getVariants(direction)}
      initial="hidden"
      animate="visible"
      transition={{ delay: index * 0.06 }}
    >
      {children}
    </motion.div>
  );
}
