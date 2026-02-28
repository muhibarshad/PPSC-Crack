/**
 * Login Page — /auth/login
 * Email + password form with Google OAuth and magic link.
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import AuthLayout from '@/components/auth/AuthLayout';
import FormInput from '@/components/auth/FormInput';
import SocialAuthButtons from '@/components/auth/SocialAuthButtons';
import { useAuthStore, getRedirectPath } from '@/store/auth-store';
import { loginSchema, type LoginFormData } from '@/lib/validations/auth';

export default function LoginPage() {
  const router = useRouter();
  const { login, loading, error: storeError, setError } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    try {
      await login(data.email, data.password);
      // Redirect based on role + onboarding state
      const user = useAuthStore.getState().user;
      if (user) {
        router.push(getRedirectPath(user));
      } else {
        router.push('/dashboard');
      }
    } catch {
      // Error already set in store
    }
  };

  return (
    <AuthLayout title="Welcome Back" subtitle="Sign in to continue your preparation">
      {/* Global error */}
      {storeError && (
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
          <p className="text-sm text-[var(--clr-danger)]">{storeError}</p>
        </div>
      )}

      {/* Social / Magic Link */}
      <SocialAuthButtons showMagicLink />

      {/* Email + Password Form */}
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <FormInput
          label="Email"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          {...register('email')}
          error={errors.email?.message}
        />

        <div className="relative">
          <FormInput
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            autoComplete="current-password"
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

        {/* Forgot password link */}
        <div className="flex justify-end mb-6 -mt-2">
          <Link
            href="/auth/forgot-password"
            className="text-xs font-medium text-primary hover:text-primary-light transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary btn-lg w-full animate-pulse-glow disabled:opacity-60 disabled:cursor-not-allowed disabled:animate-none"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Signing in…
            </span>
          ) : (
            'Sign In'
          )}
        </button>
      </form>

      {/* Footer link */}
      <p className="text-center text-sm text-[var(--clr-text-secondary)] mt-8">
        Don&apos;t have an account?{' '}
        <Link
          href="/auth/register"
          className="font-semibold text-primary hover:text-primary-light transition-colors"
        >
          Create one
        </Link>
      </p>
    </AuthLayout>
  );
}
