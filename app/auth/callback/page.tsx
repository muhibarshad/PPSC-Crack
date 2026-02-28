/**
 * Auth Callback Page — /auth/callback
 * Handles the redirect after Google OAuth or magic-link.
 * Supabase JS automatically picks up the tokens from the URL hash.
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { useAuthStore, getRedirectPath } from '@/store/auth-store';

export default function AuthCallbackPage() {
  const router = useRouter();
  const { setError } = useAuthStore();
  const [status, setStatus] = useState<'loading' | 'error'>('loading');

  useEffect(() => {
    const handle = async () => {
      try {
        // Supabase JS auto-detects the hash params and creates the session
        const { data, error } = await supabase.auth.getSession();
        if (error) throw error;

        const session = data.session;
        if (!session) {
          throw new Error('No session returned after callback.');
        }

        // Notify our backend so it can create/link the local user
        const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';
        const res = await fetch(`${API}/auth/oauth/callback`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session.access_token}`,
          },
          credentials: 'include',
          body: JSON.stringify({
            access_token: session.access_token,
            refresh_token: session.refresh_token,
          }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: 'Backend callback failed' }));
          throw new Error(err.detail || `HTTP ${res.status}`);
        }

        const payload = await res.json();

        // Wait for the Zustand store to pick up the session, then redirect
        const role = payload.user?.role || 'student';
        router.replace(getRedirectPath(role));
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Authentication failed';
        setError(msg);
        setStatus('error');
        // Redirect to login with a short delay so the user sees the error
        setTimeout(() => router.replace('/auth/login'), 3000);
      }
    };

    handle();
  }, [router, setError]);

  return (
    <div className="min-h-screen flex items-center justify-center z-10 relative">
      {status === 'loading' ? (
        <div className="flex flex-col items-center gap-4">
          <svg className="animate-spin h-8 w-8 text-primary" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm text-[var(--clr-text-secondary)]">
            Completing sign-in…
          </p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 text-center px-6">
          <div className="w-12 h-12 rounded-full bg-[var(--clr-danger-dim)] flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--clr-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          </div>
          <p className="text-sm text-[var(--clr-danger)]">
            Something went wrong. Redirecting to login…
          </p>
        </div>
      )}
    </div>
  );
}
