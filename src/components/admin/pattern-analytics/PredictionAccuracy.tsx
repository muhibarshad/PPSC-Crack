/**
 * Prediction Accuracy Retrospective — side-by-side comparison of
 * predicted vs actual paper topic distributions.
 */

'use client';

import { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { PredictionAccuracyResponse, PredictionSummary, PaperSummary } from './types';

interface Props {
  data: PredictionAccuracyResponse | null;
  predictions: PredictionSummary[];
  papers: PaperSummary[];
  loading?: boolean;
  onCompare?: (predictionId: string, paperId: string) => void;
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-sm px-4 py-3 rounded-xl border border-white/10 text-sm min-w-[180px]">
      <p className="font-semibold text-white mb-2">{label}</p>
      {payload.map((entry: any, idx: number) => (
        <div key={idx} className="flex items-center justify-between gap-4 text-[var(--clr-text-secondary)]">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: entry.color }} />
            {entry.name}
          </span>
          <span className="font-mono text-white">{entry.value?.toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}

export default function PredictionAccuracy({ data, predictions, papers, loading, onCompare }: Props) {
  const [selectedPred, setSelectedPred] = useState('');
  const [selectedPaper, setSelectedPaper] = useState('');

  const handleCompare = () => {
    if (selectedPred && selectedPaper && onCompare) {
      onCompare(selectedPred, selectedPaper);
    }
  };

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-display font-bold text-white">Prediction Accuracy</h3>
        {data?.accuracy_score != null && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--clr-text-muted)]">Accuracy</span>
            <span className={`text-lg font-bold font-mono ${
              data.accuracy_score >= 80 ? 'text-emerald-400' :
              data.accuracy_score >= 60 ? 'text-amber-400' : 'text-red-400'
            }`}>
              {data.accuracy_score.toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Selector row */}
      <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3 mb-6">
        <div>
          <label className="block text-[10px] uppercase tracking-[0.12em] font-semibold text-[var(--clr-text-muted)] mb-1.5">
            Prediction
          </label>
          <select
            value={selectedPred}
            onChange={(e) => setSelectedPred(e.target.value)}
            className="w-full bg-[var(--clr-bg-base)] border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--clr-primary)] transition-colors appearance-none"
          >
            <option value="">Select a prediction…</option>
            {predictions.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title} ({p.prediction_date})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-[10px] uppercase tracking-[0.12em] font-semibold text-[var(--clr-text-muted)] mb-1.5">
            Actual Paper
          </label>
          <select
            value={selectedPaper}
            onChange={(e) => setSelectedPaper(e.target.value)}
            className="w-full bg-[var(--clr-bg-base)] border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--clr-primary)] transition-colors appearance-none"
          >
            <option value="">Select an actual paper…</option>
            {papers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title} ({p.year})
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-end">
          <button
            onClick={handleCompare}
            disabled={!selectedPred || !selectedPaper || loading}
            className="btn bg-gradient-to-r from-[var(--clr-primary)] to-[var(--clr-neon)] text-white px-5 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40 disabled:pointer-events-none hover:shadow-[0_0_20px_rgba(139,92,246,0.3)] transition-all"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                Comparing…
              </span>
            ) : (
              'Compare →'
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      {data ? (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <MiniCard
              label="Confidence"
              value={`${(data.confidence_score * 100).toFixed(0)}%`}
              sub={`${data.paper_count_basis} papers basis`}
            />
            <MiniCard
              label="Predicted Topics"
              value={String(data.total_predicted_topics)}
              sub="unique topics"
            />
            <MiniCard
              label="Actual Topics"
              value={String(data.total_actual_topics)}
              sub="unique topics"
            />
            <MiniCard
              label="Overlap"
              value={`${data.comparison.filter((c) => c.predicted_pct > 0 && c.actual_pct > 0).length}`}
              sub="matching topics"
            />
          </div>

          {/* Side-by-side bar chart */}
          <ResponsiveContainer width="100%" height={Math.max(300, data.comparison.length * 36)}>
            <BarChart
              data={data.comparison}
              layout="vertical"
              margin={{ top: 0, right: 30, left: 10, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
              <XAxis
                type="number"
                tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
                tickLine={false}
                tickFormatter={(v: number) => `${v}%`}
              />
              <YAxis
                type="category"
                dataKey="topic"
                width={130}
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Legend
                wrapperStyle={{ paddingTop: '12px' }}
                formatter={(value: string) => (
                  <span className="text-xs text-[var(--clr-text-secondary)]">{value}</span>
                )}
              />
              <Bar dataKey="predicted_pct" name="Predicted" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={14} />
              <Bar dataKey="actual_pct" name="Actual" fill="#06b6d4" radius={[0, 4, 4, 0]} barSize={14} />
            </BarChart>
          </ResponsiveContainer>

          {/* Difference table */}
          <div className="mt-4 pt-4 border-t border-white/[0.06]">
            <p className="text-[10px] uppercase tracking-[0.12em] font-semibold text-[var(--clr-text-muted)] mb-3">
              Largest deviations
            </p>
            <div className="flex flex-wrap gap-2">
              {data.comparison
                .filter((c) => c.difference > 2)
                .sort((a, b) => b.difference - a.difference)
                .slice(0, 6)
                .map((c) => (
                  <span
                    key={c.topic}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20"
                  >
                    {c.topic}
                    <span className="font-mono">±{c.difference.toFixed(1)}%</span>
                  </span>
                ))}
            </div>
          </div>
        </>
      ) : (
        <div className="h-[200px] flex items-center justify-center text-[var(--clr-text-muted)] text-sm">
          Select a prediction and an actual paper above, then click Compare.
        </div>
      )}
    </div>
  );
}

/* ── Mini stat card ──────────────────────────── */

function MiniCard({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="glass-sm rounded-xl p-3">
      <p className="text-[10px] uppercase tracking-[0.12em] font-semibold text-[var(--clr-text-muted)] mb-1">
        {label}
      </p>
      <p className="text-xl font-bold font-mono text-white">{value}</p>
      <p className="text-[10px] text-[var(--clr-text-muted)]">{sub}</p>
    </div>
  );
}
