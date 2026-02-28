/**
 * ProtectedRoute — Client-side route guard.
 * Wraps pages that require authentication.
 * Redirects unauthenticated users to /auth/login.
 * Optionally enforces a specific role.
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** If set, the user must have this role (or be 'admin' who can access everything). */
  requiredRole?: 'student' | 'admin' | 'moderator';
}

export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const router = useRouter();
  const { user, loading, initialised } = useAuthStore();

  useEffect(() => {
    if (!initialised || loading) return;

    if (!user) {
      router.replace('/auth/login');
      return;
    }

    if (requiredRole && user.role !== requiredRole && user.role !== 'admin') {
      router.replace('/auth/login');
    }
  }, [user, loading, initialised, requiredRole, router]);

  // Show nothing while loading
  if (!initialised || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center z-10 relative">
        <svg className="animate-spin h-8 w-8 text-primary" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  // Don't render children if not authed
  if (!user) return null;

  // Role check
  if (requiredRole && user.role !== requiredRole && user.role !== 'admin') return null;

  return <>{children}</>;
}
