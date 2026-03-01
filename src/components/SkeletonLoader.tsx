/**
 * SkeletonLoader — Loading placeholder with shimmer animation.
 * Uses CSS @keyframes for the shimmer effect.
 */

'use client';

interface SkeletonProps {
  /** 'text' | 'circle' | 'card' | 'rect' */
  variant?: 'text' | 'circle' | 'card' | 'rect';
  /** Width (CSS value). Default: '100%' */
  width?: string;
  /** Height (CSS value). Default: varies by variant */
  height?: string;
  /** Number of text lines to render */
  lines?: number;
  /** Additional CSS class */
  className?: string;
}

export default function SkeletonLoader({
  variant = 'rect',
  width = '100%',
  height,
  lines = 3,
  className = '',
}: SkeletonProps) {
  const baseClass = 'skeleton-shimmer';

  if (variant === 'text') {
    return (
      <div className={`flex flex-col gap-2 ${className}`} style={{ width }}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={baseClass}
            style={{
              height: '14px',
              borderRadius: '6px',
              width: i === lines - 1 ? '65%' : '100%',
            }}
          />
        ))}
      </div>
    );
  }

  if (variant === 'circle') {
    const size = height || '48px';
    return (
      <div
        className={`${baseClass} ${className}`}
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
        }}
      />
    );
  }

  if (variant === 'card') {
    return (
      <div
        className={`${baseClass} ${className}`}
        style={{
          width,
          height: height || '160px',
          borderRadius: 'var(--radius-xl)',
        }}
      />
    );
  }

  // rect (default)
  return (
    <div
      className={`${baseClass} ${className}`}
      style={{
        width,
        height: height || '20px',
        borderRadius: 'var(--radius-sm)',
      }}
    />
  );
}

/**
 * Stat card skeleton — mimics the QuickStatsBar loading state.
 */
export function StatCardSkeleton() {
  return (
    <div className="glass-sm p-4 flex items-center gap-4 flex-1 min-w-[180px]">
      <SkeletonLoader variant="circle" height="40px" />
      <div className="flex-1 flex flex-col gap-2">
        <SkeletonLoader variant="rect" width="60px" height="24px" />
        <SkeletonLoader variant="rect" width="80px" height="10px" />
      </div>
    </div>
  );
}

/**
 * Dashboard page skeleton — full loading state.
 */
export function DashboardSkeleton() {
  return (
    <div className="min-h-screen z-10 relative pt-24 pb-16 px-6">
      <div className="max-w-5xl mx-auto flex flex-col gap-8">
        {/* Header */}
        <div className="flex flex-col gap-2">
          <SkeletonLoader variant="rect" width="300px" height="36px" />
          <SkeletonLoader variant="rect" width="200px" height="16px" />
        </div>

        {/* Hero Section */}
        <SkeletonLoader variant="card" height="200px" />

        {/* Action Cards */}
        <div className="flex flex-wrap gap-6">
          <SkeletonLoader variant="card" width="280px" height="180px" />
          <SkeletonLoader variant="card" width="280px" height="180px" />
          <SkeletonLoader variant="card" width="280px" height="180px" />
        </div>

        {/* Stats */}
        <div className="flex flex-wrap gap-4">
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </div>
      </div>
    </div>
  );
}
