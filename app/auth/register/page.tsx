/**
 * Register Page — /auth/register
 * Full name, email, phone (optional), password with strength indicator.
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
import { registerSchema, type RegisterFormData } from '@/lib/validations/auth';

/* ── Password strength helper ────────────────────── */
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

export default function RegisterPage() {
  const router = useRouter();
  const { register: authRegister, loading, error: storeError, setError } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: '', email: '', phone: '', password: '', confirmPassword: '' },
  });

  const passwordValue = watch('password', '');
  const strength = getPasswordStrength(passwordValue);

  const onSubmit = async (data: RegisterFormData) => {
    setError(null);
    setSuccessMsg('');
    try {
      await authRegister(data.name, data.email, data.password, data.phone || undefined);
      // If login succeeded (no email confirmation required)
      const user = useAuthStore.getState().user;
      if (user) {
        router.push(getRedirectPath(user.role));
      } else {
        setSuccessMsg(
          'Account created! Check your email to confirm, then sign in.',
        );
      }
    } catch {
      // Error set in store
    }
  };

  return (
    <AuthLayout title="Create Account" subtitle="Start your PPSC preparation journey">
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

      {/* Success message */}
      {successMsg && (
        <div className="mb-6 flex items-start gap-3 px-4 py-3 rounded-xl bg-[var(--clr-success-dim)] border border-[rgba(52,211,153,0.2)]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--clr-success)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <p className="text-sm text-[var(--clr-success)]">{successMsg}</p>
        </div>
      )}

      {/* Social */}
      <SocialAuthButtons />

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <FormInput
          label="Full Name"
          type="text"
          placeholder="Muhammad Ali"
          autoComplete="name"
          {...register('name')}
          error={errors.name?.message}
        />

        <FormInput
          label="Email"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          {...register('email')}
          error={errors.email?.message}
        />

        <FormInput
          label="Phone (optional)"
          type="tel"
          placeholder="+92 300 1234567"
          autoComplete="tel"
          {...register('phone')}
          error={errors.phone?.message}
        />

        {/* Password + strength meter */}
        <div className="relative">
          <FormInput
            label="Password"
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
          label="Confirm Password"
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
              Creating account…
            </span>
          ) : (
            'Create Account'
          )}
        </button>
      </form>

      {/* Footer link */}
      <p className="text-center text-sm text-[var(--clr-text-secondary)] mt-8">
        Already have an account?{' '}
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
