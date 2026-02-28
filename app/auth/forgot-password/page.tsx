/**
 * Forgot Password Page — /auth/forgot-password
 * Sends a password-reset email via Supabase.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import AuthLayout from '@/components/auth/AuthLayout';
import FormInput from '@/components/auth/FormInput';
import { useAuthStore } from '@/store/auth-store';
import { forgotPasswordSchema, type ForgotPasswordFormData } from '@/lib/validations/auth';

export default function ForgotPasswordPage() {
  const { forgotPassword, error: storeError, setError } = useAuthStore();
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setError(null);
    setSubmitting(true);
    try {
      await forgotPassword(data.email);
      setSent(true);
    } catch {
      // Error set in store
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Reset Password"
      subtitle="Enter your email and we'll send a reset link"
    >
      {/* Global error */}
      {storeError && (
        <div className="mb-6 flex items-start gap-3 px-4 py-3 rounded-xl bg-[var(--clr-danger-dim)] border border-[rgba(248,113,113,0.2)]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--clr-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
          <p className="text-sm text-[var(--clr-danger)]">{storeError}</p>
        </div>
      )}

      {sent ? (
        /* Success state */
        <div className="text-center py-4">
          {/* Animated check icon */}
          <div className="mx-auto mb-6 w-16 h-16 rounded-full bg-[var(--clr-success-dim)] border border-[rgba(52,211,153,0.2)] flex items-center justify-center">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--clr-success)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>

          <h2 className="font-display text-lg font-bold text-white mb-2">
            Check Your Email
          </h2>
          <p className="text-sm text-[var(--clr-text-secondary)] mb-8 max-w-xs mx-auto">
            We&apos;ve sent a password reset link. Click the link in your email to create a new password.
          </p>

          <Link
            href="/auth/login"
            className="btn btn-ghost"
          >
            Back to Sign In
          </Link>
        </div>
      ) : (
        /* Email form */
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <FormInput
            label="Email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            {...register('email')}
            error={errors.email?.message}
          />

          <button
            type="submit"
            disabled={submitting}
            className="btn btn-primary btn-lg w-full animate-pulse-glow disabled:opacity-60 disabled:cursor-not-allowed disabled:animate-none mt-1"
          >
            {submitting ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Sending…
              </span>
            ) : (
              'Send Reset Link'
            )}
          </button>

          <p className="text-center text-sm text-[var(--clr-text-secondary)] mt-8">
            Remembered your password?{' '}
            <Link
              href="/auth/login"
              className="font-semibold text-primary hover:text-primary-light transition-colors"
            >
              Sign in
            </Link>
          </p>
        </form>
      )}
    </AuthLayout>
  );
}
