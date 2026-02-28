/**
 * Reset Password Page — /auth/reset-password
 * =============================================
 * Users arrive here after clicking the reset link in their email.
 * Supabase JS picks up the recovery tokens from the URL hash and
 * establishes a session, then the user enters a new password.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import AuthLayout from '@/components/auth/AuthLayout';
import FormInput from '@/components/auth/FormInput';
import { supabase } from '@/lib/supabase';

/* ── Validation Schema ───────────────────────── */

const resetPasswordSchema = z
  .object({
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .max(128, 'Password is too long')
      .regex(/[A-Z]/, 'Include at least one uppercase letter')
      .regex(/[0-9]/, 'Include at least one number'),
    confirmPassword: z.string().min(1, 'Confirm your password'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

/* ── Password strength helper ────────────────── */

function getPasswordStrength(pw: string): { score: number; label: string; color: string } {
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;

  if (score <= 1) return { score, label: 'Weak', color: 'var(--clr-danger)' };
  if (score <= 3) return { score, label: 'Medium', color: 'var(--clr-warning)' };
  return { score, label: 'Strong', color: 'var(--clr-success)' };
}

/* ── Component ───────────────────────────────── */

export default function ResetPasswordPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [sessionReady, setSessionReady] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { password: '', confirmPassword: '' },
  });

  const passwordValue = watch('password', '');
  const strength = getPasswordStrength(passwordValue);

  /* Wait for Supabase to pick up the recovery session from the URL hash */
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event) => {
        if (event === 'PASSWORD_RECOVERY') {
          setSessionReady(true);
        }
      },
    );

    // Also check if there's already a session (user refreshed the page)
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) setSessionReady(true);
    });

    return () => subscription.unsubscribe();
  }, []);

  const onSubmit = async (data: ResetPasswordFormData) => {
    setLoading(true);
    setError(null);

    try {
      const { error: updateError } = await supabase.auth.updateUser({
        password: data.password,
      });

      if (updateError) throw new Error(updateError.message);

      setSuccess(true);

      // Redirect to login after a short delay
      setTimeout(() => router.replace('/auth/login'), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reset password';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  /* ── Success State ─────────────────────────── */
  if (success) {
    return (
      <AuthLayout title="Password Reset" subtitle="Your password has been updated">
        <div className="text-center py-4">
          <div className="mx-auto mb-6 w-16 h-16 rounded-full bg-[var(--clr-success-dim)] border border-[rgba(52,211,153,0.2)] flex items-center justify-center">
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--clr-success)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>

          <h2 className="font-display text-lg font-bold text-white mb-2">
            Password Updated!
          </h2>
          <p className="text-sm text-[var(--clr-text-secondary)] mb-8 max-w-xs mx-auto">
            Your password has been successfully changed. Redirecting to sign in…
          </p>

          <Link href="/auth/login" className="btn btn-ghost">
            Back to Sign In
          </Link>
        </div>
      </AuthLayout>
    );
  }

  /* ── Waiting for recovery session ──────────── */
  if (!sessionReady) {
    return (
      <AuthLayout title="Reset Password" subtitle="Verifying your reset link…">
        <div className="flex flex-col items-center gap-4 py-8">
          <svg className="animate-spin h-8 w-8 text-primary" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm text-[var(--clr-text-secondary)]">
            Verifying your reset link…
          </p>
        </div>
      </AuthLayout>
    );
  }

  /* ── Reset Form ────────────────────────────── */
  return (
    <AuthLayout title="Create New Password" subtitle="Enter your new password below">
      {/* Error */}
      {error && (
        <div className="mb-6 flex items-start gap-3 px-4 py-3 rounded-xl bg-[var(--clr-danger-dim)] border border-[rgba(248,113,113,0.2)]">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--clr-danger)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="mt-0.5 shrink-0"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
          <p className="text-sm text-[var(--clr-danger)]">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        {/* New Password + strength meter */}
        <div className="relative">
          <FormInput
            label="New Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Min. 8 characters"
            autoComplete="new-password"
            {...register('password')}
            error={errors.password?.message}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-[38px] text-[var(--clr-text-muted)] hover:text-white transition-colors"
            tabIndex={-1}
          >
            {showPassword ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                <line x1="1" y1="1" x2="23" y2="23" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            )}
          </button>
        </div>

        {/* Strength indicator */}
        {passwordValue.length > 0 && (
          <div className="-mt-3 mb-5">
            <div className="flex gap-1 mb-1">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="h-1 flex-1 rounded-full transition-colors duration-300"
                  style={{
                    backgroundColor: i <= strength.score ? strength.color : 'rgba(255,255,255,0.06)',
                  }}
                />
              ))}
            </div>
            <p className="text-xs" style={{ color: strength.color }}>
              {strength.label}
            </p>
          </div>
        )}

        <FormInput
          label="Confirm New Password"
          type={showPassword ? 'text' : 'password'}
          placeholder="••••••••"
          autoComplete="new-password"
          {...register('confirmPassword')}
          error={errors.confirmPassword?.message}
        />

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary btn-lg w-full animate-pulse-glow disabled:opacity-60 disabled:cursor-not-allowed disabled:animate-none mt-2"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Updating password…
            </span>
          ) : (
            'Reset Password'
          )}
        </button>
      </form>

      {/* Footer link */}
      <p className="text-center text-sm text-[var(--clr-text-secondary)] mt-8">
        Remember your password?{' '}
        <Link
          href="/auth/login"
          className="font-semibold text-primary hover:text-primary-light transition-colors"
        >
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
