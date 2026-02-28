/**
 * AuthProvider — Initialises the Zustand auth store listener.
 * Wrap the app tree with this component inside layout.tsx.
 *
 * React Strict Mode (used by Next.js in dev) will mount → unmount → remount.
 * Each mount creates a fresh Supabase subscription; each unmount cleans it up
 * via the `cancelled` flag inside init().  This is intentional and correct.
 */

'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/store/auth-store';

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const init = useAuthStore((s) => s.init);

  useEffect(() => {
    const unsubscribe = init();
    return () => unsubscribe();
  }, [init]);

  return <>{children}</>;
}
