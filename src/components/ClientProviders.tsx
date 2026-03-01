/**
 * ClientProviders — Client-side providers for the app.
 * Wraps children with AnimatePresence for page transitions.
 * Renders the global ParticlesBackground behind all content.
 */

'use client';

import { usePathname } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import dynamic from 'next/dynamic';

// Dynamically import ParticlesBackground to avoid SSR issues
const ParticlesBackground = dynamic(
  () => import('@/components/ParticlesBackground'),
  { ssr: false },
);

interface ClientProvidersProps {
  children: React.ReactNode;
}

export default function ClientProviders({ children }: ClientProvidersProps) {
  const pathname = usePathname();
  const isLanding = pathname === '/';

  return (
    <>
      {/* Global particle background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <ParticlesBackground density={isLanding ? 'dense' : 'normal'} />
      </div>

      {/* AnimatePresence wraps page transitions */}
      <AnimatePresence mode="wait">
        <motion.div
          key={pathname}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.25, ease: [0.42, 0, 0.58, 1] }}
        >
          {children}
        </motion.div>
      </AnimatePresence>
    </>
  );
}
