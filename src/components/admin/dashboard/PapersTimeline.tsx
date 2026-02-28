/**
 * Papers Timeline — Horizontal scrollable timeline
 * ===================================================
 * Displays all ingested papers chronologically using Recharts.
 * Each point is colored by job type. Hover shows paper details.
 */

'use client';

import { useMemo, useState } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { TimelinePaperPoint } from './types';

/* ── Deterministic color palette per job type ──── */

const JOB_COLORS = [
  '#f87171', // red
  '#a78bfa', // violet
  '#34d399', // emerald
  '#fbbf24', // amber
  '#38bdf8', // sky
  '#e879f9', // fuchsia
  '#fb923c', // orange
  '#818cf8', // indigo
  '#2dd4bf', // teal
  '#f472b6', // pink
];

function getColorForJob(slug: string, slugMap: Map<string, number>): string {
  if (!slugMap.has(slug)) {
    slugMap.set(slug, slugMap.size);
  }
  return JOB_COLORS[slugMap.get(slug)! % JOB_COLORS.length];
}

/* ── Custom Tooltip ────────────────────────────── */

interface TipProps {
  active?: boolean;
  payload?: Array<{ payload: ChartDatum }>;
}

interface ChartDatum {
  x: number;
  y: number;
  paper: TimelinePaperPoint;
  color: string;
}

function CustomTooltip({ active, payload }: TipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const p = d.paper;
  const month = p.paper_month ? String(p.paper_month).padStart(2, '0') : '??';

  return (
    <div className="glass-sm px-4 py-3 max-w-xs shadow-xl pointer-events-none">
      <p className="text-sm font-bold text-white truncate">{p.title}</p>
      <div className="flex items-center gap-2 mt-1">
        <span
          className="inline-block w-2 h-2 rounded-full"
          style={{ background: d.color }}
        />
        <span className="text-xs text-[var(--clr-text-secondary)]">{p.job_type_name}</span>
      </div>
      <div className="flex gap-4 mt-2 text-xs text-[var(--clr-text-muted)]">
        <span>📅 {month}/{p.paper_year}</span>
        <span>📝 {p.total_questions} Qs</span>
        <span
          className={`capitalize font-semibold ${
            p.ingestion_status === 'completed'
              ? 'text-[var(--clr-success)]'
              : p.ingestion_status === 'failed'
                ? 'text-[var(--clr-danger)]'
                : 'text-[var(--clr-warning)]'
          }`}
        >
          {p.ingestion_status}
        </span>
      </div>
    </div>
  );
}

/* ── Main Component ────────────────────────────── */

export default function PapersTimeline({ papers }: { papers: TimelinePaperPoint[] }) {
  const slugMap = useMemo(() => new Map<string, number>(), []);

  // Transform papers → scatter data
  const { data, legend } = useMemo(() => {
    const pts: ChartDatum[] = papers.map((p, i) => ({
      x: p.paper_year + (p.paper_month ? (p.paper_month - 1) / 12 : 0),
      y: p.total_questions,
      paper: p,
      color: getColorForJob(p.job_type_slug, slugMap),
    }));

    // Build legend entries
    const seen = new Map<string, { name: string; color: string }>();
    papers.forEach((p) => {
      if (!seen.has(p.job_type_slug)) {
        seen.set(p.job_type_slug, {
          name: p.job_type_name,
          color: getColorForJob(p.job_type_slug, slugMap),
        });
      }
    });

    return { data: pts, legend: Array.from(seen.values()) };
  }, [papers, slugMap]);

  if (papers.length === 0) {
    return (
      <div className="glass p-6 flex items-center justify-center h-52">
        <p className="text-sm text-[var(--clr-text-muted)]">No papers ingested yet. Upload your first paper to see the timeline.</p>
      </div>
    );
  }

  return (
    <div className="glass p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold text-white uppercase tracking-[0.1em]">Papers Timeline</h2>
          <p className="text-xs text-[var(--clr-text-muted)] mt-0.5">{papers.length} papers across all job types</p>
        </div>
        {/* Legend */}
        <div className="flex flex-wrap gap-3">
          {legend.map((l) => (
            <div key={l.name} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: l.color }} />
              <span className="text-[10px] text-[var(--clr-text-secondary)] font-medium">{l.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="overflow-x-auto" style={{ minWidth: Math.max(600, papers.length * 12) }}>
        <ResponsiveContainer width="100%" height={220}>
          <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
            <XAxis
              type="number"
              dataKey="x"
              domain={['dataMin - 0.5', 'dataMax + 0.5']}
              tickFormatter={(v: number) => String(Math.round(v))}
              tick={{ fill: 'var(--clr-text-muted)', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
              tickLine={false}
              name="Year"
            />
            <YAxis
              type="number"
              dataKey="y"
              tick={{ fill: 'var(--clr-text-muted)', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
              tickLine={false}
              name="Questions"
              width={36}
            />
            <Tooltip content={<CustomTooltip />} cursor={false} />
            <Scatter data={data} isAnimationActive={true} animationDuration={800}>
              {data.map((d, i) => (
                <Cell
                  key={d.paper.id}
                  fill={d.color}
                  fillOpacity={0.85}
                  r={6}
                  stroke={d.color}
                  strokeWidth={1}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
