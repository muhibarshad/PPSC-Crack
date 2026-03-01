/**
 * Responsive Chart Wrapper
 * =========================
 * Wraps Recharts charts in ResponsiveContainer for proper mobile sizing.
 * Dynamically imported to reduce bundle size.
 */

'use client';

import { ResponsiveContainer } from 'recharts';
import { ReactNode } from 'react';

interface ResponsiveChartProps {
  children: ReactNode;
  height?: number;
  minHeight?: number;
  className?: string;
}

export default function ResponsiveChart({
  children,
  height = 300,
  minHeight = 200,
  className = '',
}: ResponsiveChartProps) {
  return (
    <div className={`w-full ${className}`} style={{ minHeight }}>
      <ResponsiveContainer width="100%" height={height}>
        {children as React.ReactElement}
      </ResponsiveContainer>
    </div>
  );
}
