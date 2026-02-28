/**
 * FormInput — Styled text input matching the ultraviolet design system.
 * Works with React Hook Form's `register()`.
 */

'use client';

import { forwardRef } from 'react';

interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

const FormInput = forwardRef<HTMLInputElement, FormInputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="mb-5">
        <label className="block text-sm font-medium text-[var(--clr-text-secondary)] mb-1.5">
          {label}
        </label>
        <input
          ref={ref}
          className={`
            w-full px-4 py-3 rounded-xl text-sm text-white placeholder-[var(--clr-text-muted)]
            bg-[rgba(22,18,52,0.6)] border transition-all duration-200 outline-none
            ${
              error
                ? 'border-[var(--clr-danger)] focus:border-[var(--clr-danger)] focus:shadow-[0_0_0_3px_rgba(248,113,113,0.15)]'
                : 'border-[var(--clr-glass-border)] focus:border-primary/40 focus:shadow-[0_0_0_3px_rgba(139,92,246,0.1)]'
            }
            ${className}
          `}
          {...props}
        />
        {error && (
          <p className="mt-1.5 text-xs text-[var(--clr-danger)]">{error}</p>
        )}
      </div>
    );
  },
);

FormInput.displayName = 'FormInput';
export default FormInput;
