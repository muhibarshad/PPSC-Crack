/**
 * PPSC Crack — Zustand Auth Store
 * =================================
 * Global auth state with Supabase integration.
 *
 * - Persists nothing to localStorage (Supabase handles session).
 * - Listens to onAuthStateChange to stay in sync.
 * - Role-aware: students → /dashboard, admins → /admin.
 */

import { create } from 'zustand';
import { supabase } from '@/lib/supabase';
import type { User as SupabaseUser, Session } from '@supabase/supabase-js';

/* ── Types ─────────────────────────────────────── */

export interface AppUser {
  id: string;
  email: string;
  name: string;
  role: 'student' | 'admin' | 'moderator';
  avatar_url: string | null;
  auth_provider: string;
  is_premium: boolean;
  subscription_tier: string;
  selected_job_types: string[] | null;
}

interface AuthState {
  /* state */
  user: AppUser | null;
  session: Session | null;
  loading: boolean;
  initialised: boolean;
  error: string | null;

  /* actions */
  setUser: (user: AppUser | null) => void;
  setSession: (session: Session | null) => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;

  /* auth flows */
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, phone?: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  sendMagicLink: (email: string) => Promise<void>;
  forgotPassword: (email: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;

  /* lifecycle */
  init: () => () => void; // returns unsubscribe fn
}

/* ── Helpers ───────────────────────────────────── */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

/** POST to our FastAPI backend, returns parsed JSON. */
async function api<T = unknown>(
  path: string,
  body?: Record<string, unknown>,
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, {
    method: body ? 'POST' : 'GET',
    headers,
    credentials: 'include', // send httpOnly cookies
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

/** Map backend /auth/me response to our AppUser shape. */
function mapUser(data: Record<string, unknown>): AppUser {
  return {
    id: data.id as string,
    email: data.email as string,
    name: data.name as string,
    role: (data.role as AppUser['role']) || 'student',
    avatar_url: (data.avatar_url as string) || null,
    auth_provider: (data.auth_provider as string) || 'email',
    is_premium: (data.is_premium as boolean) || false,
    subscription_tier: (data.subscription_tier as string) || 'free',
    selected_job_types: (data.selected_job_types as string[] | null) || null,
  };
}

/** Return the target redirect path based on role + onboarding state. */
export function getRedirectPath(user: AppUser): string {
  if (user.role === 'admin') return '/admin';
  // Students who haven't completed onboarding go to the onboarding flow
  if (!user.selected_job_types || user.selected_job_types.length === 0) {
    return '/onboarding';
  }
  return '/dashboard';
}

/** Check if a student still needs onboarding. */
export function needsOnboarding(user: AppUser): boolean {
  return user.role === 'student' && (!user.selected_job_types || user.selected_job_types.length === 0);
}

/* ── Store ─────────────────────────────────────── */

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  session: null,
  loading: true,
  initialised: false,
  error: null,

  setUser: (user) => set({ user }),
  setSession: (session) => set({ session }),
  setError: (error) => set({ error }),
  setLoading: (loading) => set({ loading }),

  /* ── Login ───────────────────────────────────── */
  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      // 1) Supabase sign-in
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw new Error(error.message);

      const token = data.session?.access_token;

      // 2) Hit our backend to ensure local user + get profile
      const res = await api<{ access_token: string; user: Record<string, unknown> }>(
        '/auth/login',
        { email, password },
        token,
      );

      set({ session: data.session, user: mapUser(res.user), loading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Login failed';
      set({ error: message, loading: false });
      throw err;
    }
  },

  /* ── Register ────────────────────────────────── */
  register: async (name, email, password, phone) => {
    set({ loading: true, error: null });
    try {
      await api('/auth/register', { name, email, password, phone: phone || undefined });

      // Auto-login after registration
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        // Email confirmation may be required
        set({ loading: false });
        return;
      }

      const token = data.session?.access_token;
      const res = await api<{ access_token: string; user: Record<string, unknown> }>(
        '/auth/login',
        { email, password },
        token,
      );

      set({ session: data.session, user: mapUser(res.user), loading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      set({ error: message, loading: false });
      throw err;
    }
  },

  /* ── Google OAuth ────────────────────────────── */
  loginWithGoogle: async () => {
    set({ loading: true, error: null });
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: `${window.location.origin}/auth/callback` },
      });
      if (error) throw new Error(error.message);
      // Redirect happens — no state update needed here
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Google login failed';
      set({ error: message, loading: false });
      throw err;
    }
  },

  /* ── Magic Link ──────────────────────────────── */
  sendMagicLink: async (email) => {
    set({ loading: true, error: null });
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: { shouldCreateUser: true },
      });
      if (error) throw new Error(error.message);
      set({ loading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to send magic link';
      set({ error: message, loading: false });
      throw err;
    }
  },

  /* ── Forgot Password ─────────────────────────── */
  forgotPassword: async (email) => {
    set({ loading: true, error: null });
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      });
      if (error) throw new Error(error.message);
      set({ loading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to send reset email';
      set({ error: message, loading: false });
      throw err;
    }
  },

  /* ── Logout ──────────────────────────────────── */
  logout: async () => {
    set({ loading: true, error: null });
    try {
      await supabase.auth.signOut();
      // Also hit backend to clear httpOnly cookie
      await api('/auth/logout').catch(() => {});
      set({ user: null, session: null, loading: false });
    } catch {
      set({ user: null, session: null, loading: false });
    }
  },

  /* ── Refresh user profile from backend ───────── */
  refreshUser: async () => {
    const session = get().session;
    if (!session?.access_token) return;
    try {
      const data = await api<Record<string, unknown>>('/auth/me', undefined, session.access_token);
      set({ user: mapUser(data) });
    } catch {
      // Token may be expired — don't crash
    }
  },

  /* ── Init (listen for Supabase auth events) ──── */
  init: () => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        set({ session, loading: false, initialised: true });

        if (session?.access_token) {
          // Sync with our backend to get the full user profile
          try {
            const data = await api<Record<string, unknown>>(
              '/auth/me',
              undefined,
              session.access_token,
            );
            set({ user: mapUser(data) });
          } catch {
            set({ user: null });
          }
        } else {
          set({ user: null });
        }

        if (event === 'SIGNED_OUT') {
          set({ user: null, session: null });
        }
      },
    );

    // Also check current session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        set({ session, loading: true });
        api<Record<string, unknown>>('/auth/me', undefined, session.access_token)
          .then((data) => set({ user: mapUser(data), loading: false, initialised: true }))
          .catch(() => set({ user: null, loading: false, initialised: true }));
      } else {
        set({ loading: false, initialised: true });
      }
    });

    return () => subscription.unsubscribe();
  },
}));
