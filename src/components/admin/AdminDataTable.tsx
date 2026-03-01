/**
 * AdminDataTable — Responsive table that becomes card-based on mobile.
 * Use this wrapper in all admin pages that display tabular data.
 */

'use client';

import { ReactNode } from 'react';

export interface Column<T> {
  key: string;
  label: string;
  render: (row: T) => ReactNode;
  /** Hide this column on mobile cards (still shows in desktop table) */
  hideOnMobile?: boolean;
  /** Priority label for mobile card view */
  mobileLabel?: string;
}

interface AdminDataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  emptyMessage?: string;
}

export default function AdminDataTable<T>({
  columns,
  data,
  keyExtractor,
  emptyMessage = 'No data found.',
}: AdminDataTableProps<T>) {
  if (data.length === 0) {
    return (
      <div className="glass p-8 text-center">
        <p className="text-sm text-[var(--clr-text-muted)]">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <>
      {/* Desktop table — hidden on small screens */}
      <div className="hidden md:block glass overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/[0.06]">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--clr-text-muted)]"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr
                key={keyExtractor(row)}
                className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-[var(--clr-text-secondary)]">
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile card view — visible only on small screens */}
      <div className="md:hidden space-y-3">
        {data.map((row) => (
          <div key={keyExtractor(row)} className="glass p-4 space-y-2">
            {columns
              .filter((col) => !col.hideOnMobile)
              .map((col) => (
                <div key={col.key} className="flex items-start justify-between gap-3">
                  <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--clr-text-muted)] shrink-0 pt-0.5">
                    {col.mobileLabel || col.label}
                  </span>
                  <span className="text-sm text-[var(--clr-text-secondary)] text-right">
                    {col.render(row)}
                  </span>
                </div>
              ))}
          </div>
        ))}
      </div>
    </>
  );
}
