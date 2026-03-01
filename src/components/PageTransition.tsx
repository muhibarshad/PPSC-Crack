/**
 * PageTransition — Framer Motion wrapper for route-level fade + slide.
 *
 * Pattern:
 *  - Old page fades out + translates up 10px
 *  - New page fades in + translates up from 10px below
 *  - Duration: 250ms, easing: ease-in-out
 *
 * Wrap each page's content with <PageTransition> to enable smooth route changes.
 */

'use client';

import { motion } from 'framer-motion';

interface PageTransitionProps {
  children: React.ReactNode;
  className?: string;
}

const variants = {
  initial: {
    opacity: 0,
    y: 10,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.25,
      ease: [0.42, 0, 0.58, 1], // ease-in-out
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: {
      duration: 0.25,
      ease: [0.42, 0, 0.58, 1],
    },
  },
};

export default function PageTransition({ children, className }: PageTransitionProps) {
  return (
    <motion.div
      initial="initial"
      animate="animate"
      exit="exit"
      variants={variants}
      className={className}
    >
      {children}
    </motion.div>
  );
}
