/**
 * AuthProvider — Initialises the Zustand auth store listener.
 * Wrap the app tree with this component inside layout.tsx.
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
