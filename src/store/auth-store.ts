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
  subscription_expires_at: string | null;
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
    subscription_expires_at: (data.subscription_expires_at as string) || null,
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
    set({ error: null });
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

      set({ session: data.session, user: mapUser(res.user) });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Login failed';
      set({ error: message });
      throw err;
    }
  },

  /* ── Register ────────────────────────────────── */
  register: async (name, email, password, phone) => {
    set({ error: null });
    try {
      await api('/auth/register', { name, email, password, phone: phone || undefined });

      // Auto-login after registration
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        // Email confirmation may be required
        return;
      }

      const token = data.session?.access_token;
      const res = await api<{ access_token: string; user: Record<string, unknown> }>(
        '/auth/login',
        { email, password },
        token,
      );

      set({ session: data.session, user: mapUser(res.user) });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      set({ error: message });
      throw err;
    }
  },

  /* ── Google OAuth ────────────────────────────── */
  loginWithGoogle: async () => {
    set({ error: null });
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: `${window.location.origin}/auth/callback` },
      });
      if (error) throw new Error(error.message);
      // Redirect happens — no state update needed here
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Google login failed';
      set({ error: message });
      throw err;
    }
  },

  /* ── Magic Link ──────────────────────────────── */
  sendMagicLink: async (email) => {
    set({ error: null });
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: { shouldCreateUser: true },
      });
      if (error) throw new Error(error.message);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to send magic link';
      set({ error: message });
      throw err;
    }
  },

  /* ── Forgot Password ─────────────────────────── */
  forgotPassword: async (email) => {
    set({ error: null });
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      });
      if (error) throw new Error(error.message);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to send reset email';
      set({ error: message });
      throw err;
    }
  },

  /* ── Logout ──────────────────────────────────── */
  logout: async () => {
    try {
      await supabase.auth.signOut();
      // Also hit backend to clear httpOnly cookie
      await api('/auth/logout').catch(() => {});
      set({ user: null, session: null });
    } catch {
      set({ user: null, session: null });
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
    set({ loading: true });

    // Cancellation flag — prevents stale async work after React cleanup
    let cancelled = false;

    /**
     * Core session handler — called for INITIAL_SESSION, SIGNED_IN,
     * and TOKEN_REFRESHED.  Fetches the user profile from our backend
     * and falls back to an explicit token refresh when the access token
     * that Supabase gave us is expired.
     */
    async function handleSession(session: Session | null): Promise<void> {
      if (cancelled) return;

      if (!session) {
        set({ user: null, session: null, loading: false, initialised: true });
        return;
      }

      set({ session });

      try {
        const data = await api<Record<string, unknown>>(
          '/auth/me',
          undefined,
          session.access_token,
        );
        if (cancelled) return;
        set({ user: mapUser(data), loading: false, initialised: true });
      } catch {
        // Access token is likely expired — try refreshing via Supabase
        if (cancelled) return;
        try {
          const { data: refreshData } = await supabase.auth.refreshSession();
          if (cancelled) return;
          if (refreshData.session) {
            set({ session: refreshData.session });
            const userData = await api<Record<string, unknown>>(
              '/auth/me',
              undefined,
              refreshData.session.access_token,
            );
            if (cancelled) return;
            set({ user: mapUser(userData), loading: false, initialised: true });
          } else {
            set({ user: null, session: null, loading: false, initialised: true });
          }
        } catch {
          if (cancelled) return;
          set({ user: null, session: null, loading: false, initialised: true });
        }
      }
    }

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (cancelled) return;

      if (event === 'SIGNED_OUT') {
        set({ user: null, session: null, loading: false, initialised: true });
        return;
      }

      // INITIAL_SESSION is the reliable source of the persisted session
      // on page load — process it instead of a separate getSession() call.
      if (
        event === 'INITIAL_SESSION' ||
        event === 'SIGNED_IN' ||
        event === 'TOKEN_REFRESHED'
      ) {
        await handleSession(session);
      }
    });

    return () => {
      cancelled = true;
      subscription.unsubscribe();
    };
  },
}));
