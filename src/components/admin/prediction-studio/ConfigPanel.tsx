/**
 * Prediction Studio — Config Panel (Left Side)
 * ===============================================
 * Job type selector, date picker, current affairs toggle,
 * total questions slider, and generate button.
 */

'use client';

import { useState, useEffect } from 'react';
import type { GenerationConfig, JobType, StudioPhase } from './types';

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

interface ConfigPanelProps {
  phase: StudioPhase;
  token: string | undefined;
  onGenerate: (config: GenerationConfig) => void;
  generationProgress: number;       // 0–100
  confidenceScore: number | null;
  confidenceExplanation: string;
}

export default function ConfigPanel({
  phase,
  token,
  onGenerate,
  generationProgress,
  confidenceScore,
  confidenceExplanation,
}: ConfigPanelProps) {
  const [jobTypes, setJobTypes] = useState<JobType[]>([]);
  const [loadingJT, setLoadingJT] = useState(true);

  // Form state
  const [jobTypeId, setJobTypeId] = useState('');
  const [predYear, setPredYear] = useState(new Date().getFullYear());
  const [predMonth, setPredMonth] = useState(new Date().getMonth() + 2 > 12 ? 1 : new Date().getMonth() + 2);
  const [includeCA, setIncludeCA] = useState(true);
  const [totalQuestions, setTotalQuestions] = useState(100);

  useEffect(() => {
    (async () => {
      if (!token) return;
      try {
        const res = await fetch(`${API}/job-types`, {
          headers: { Authorization: `Bearer ${token}` },
          credentials: 'include',
        });
        if (res.ok) {
          const data = await res.json();
          const items = data.job_types || data.items || data;
          setJobTypes(Array.isArray(items) ? items.filter((j: JobType) => j.is_active) : []);
          if (Array.isArray(items) && items.length > 0 && !jobTypeId) setJobTypeId(items[0].id);
        }
      } catch { /* ignore */ }
      finally { setLoadingJT(false); }
    })();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleGenerate = () => {
    if (!jobTypeId) return;
    const dateStr = `${predYear}-${String(predMonth).padStart(2, '0')}-01`;
    onGenerate({
      job_type_id: jobTypeId,
      prediction_date: dateStr,
      include_current_affairs: includeCA,
      total_questions: totalQuestions,
    });
  };

  const isGenerating = phase === 'generating';
  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
  ];

  return (
    <div className="glass p-6 h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-sm font-bold text-white uppercase tracking-[0.1em] flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          Configuration
        </h2>
        <p className="text-xs text-[var(--clr-text-muted)] mt-1">
          Set up your prediction parameters
        </p>
      </div>

      {/* Form fields */}
      <div className="space-y-5 flex-1">
        {/* Job Type */}
        <div>
          <label className="block text-xs font-semibold text-[var(--clr-text-secondary)] uppercase tracking-wider mb-2">
            Job Type
          </label>
          {loadingJT ? (
            <div className="h-10 rounded-xl bg-white/[0.04] animate-pulse" />
          ) : jobTypes.length === 0 ? (
            <div className="text-xs text-[var(--clr-text-muted)] bg-[var(--clr-bg-elevated)] rounded-xl px-3 py-3 border border-[var(--clr-glass-border)]">
              No job types found. Please run the seed script or add job types in the admin panel.
            </div>
          ) : (
            <select
              value={jobTypeId}
              onChange={(e) => setJobTypeId(e.target.value)}
              disabled={isGenerating}
              className="w-full h-10 rounded-xl bg-[var(--clr-bg-elevated)] border border-[var(--clr-glass-border)] px-3 text-sm text-white focus:outline-none focus:border-[var(--clr-primary-vivid)] transition-colors disabled:opacity-40"
            >
              {jobTypes.map((jt) => (
                <option key={jt.id} value={jt.id}>{jt.name}</option>
              ))}
            </select>
          )}
        </div>

        {/* Prediction Date */}
        <div>
          <label className="block text-xs font-semibold text-[var(--clr-text-secondary)] uppercase tracking-wider mb-2">
            Prediction Date
          </label>
          <div className="grid grid-cols-2 gap-2">
            <select
              value={predMonth}
              onChange={(e) => setPredMonth(Number(e.target.value))}
              disabled={isGenerating}
              className="h-10 rounded-xl bg-[var(--clr-bg-elevated)] border border-[var(--clr-glass-border)] px-3 text-sm text-white focus:outline-none focus:border-[var(--clr-primary-vivid)] transition-colors disabled:opacity-40"
            >
              {months.map((m, i) => (
                <option key={i} value={i + 1}>{m}</option>
              ))}
            </select>
            <select
              value={predYear}
              onChange={(e) => setPredYear(Number(e.target.value))}
              disabled={isGenerating}
              className="h-10 rounded-xl bg-[var(--clr-bg-elevated)] border border-[var(--clr-glass-border)] px-3 text-sm text-white focus:outline-none focus:border-[var(--clr-primary-vivid)] transition-colors disabled:opacity-40"
            >
              {[2026, 2027, 2028].map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Include Current Affairs */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-[var(--clr-text-secondary)] uppercase tracking-wider">
              Current Affairs
            </p>
            <p className="text-[10px] text-[var(--clr-text-muted)] mt-0.5">
              Include 15-20 current affairs MCQs
            </p>
          </div>
          <button
            onClick={() => setIncludeCA(!includeCA)}
            disabled={isGenerating}
            className={`relative w-11 h-6 rounded-full transition-colors duration-200 disabled:opacity-40 ${
              includeCA ? 'bg-[#f87171]' : 'bg-white/[0.1]'
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${
                includeCA ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Total Questions */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold text-[var(--clr-text-secondary)] uppercase tracking-wider">
              Total Questions
            </label>
            <span className="text-sm font-bold text-white tabular-nums">{totalQuestions}</span>
          </div>
          <input
            type="range"
            min={10}
            max={300}
            step={5}
            value={totalQuestions}
            onChange={(e) => setTotalQuestions(Number(e.target.value))}
            disabled={isGenerating}
            className="w-full h-1.5 rounded-full appearance-none bg-white/[0.08] accent-[#f87171] disabled:opacity-40 cursor-pointer"
          />
          <div className="flex justify-between mt-1">
            <span className="text-[10px] text-[var(--clr-text-muted)]">10</span>
            <span className="text-[10px] text-[var(--clr-text-muted)]">300</span>
          </div>
        </div>
      </div>

      {/* Confidence Score (visible in review / generating phase) */}
      {confidenceScore !== null && (
        <div className="glass-sm p-4 mb-4 mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-[var(--clr-text-secondary)] uppercase tracking-wider">
              Confidence Score
            </span>
            <span
              className="text-lg font-black tabular-nums"
              style={{
                color: confidenceScore >= 0.7 ? '#34d399' : confidenceScore >= 0.4 ? '#fbbf24' : '#f87171',
              }}
            >
              {(confidenceScore * 100).toFixed(1)}%
            </span>
          </div>
          <div className="w-full h-2 rounded-full bg-white/[0.06] overflow-hidden mb-2">
            <div
              className="h-full rounded-full transition-all duration-1000 ease-out"
              style={{
                width: `${confidenceScore * 100}%`,
                background: confidenceScore >= 0.7
                  ? 'linear-gradient(90deg, #34d399, #10b981)'
                  : confidenceScore >= 0.4
                    ? 'linear-gradient(90deg, #fbbf24, #f59e0b)'
                    : 'linear-gradient(90deg, #f87171, #ef4444)',
              }}
            />
          </div>
          {confidenceExplanation && (
            <p className="text-[10px] text-[var(--clr-text-muted)] leading-relaxed">
              {confidenceExplanation}
            </p>
          )}
        </div>
      )}

      {/* Generation Progress */}
      {isGenerating && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-[var(--clr-text-muted)] uppercase tracking-wider">
              Generating…
            </span>
            <span className="text-xs font-bold text-white tabular-nums">
              {generationProgress}%
            </span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[#f87171] to-[#e879f9] transition-all duration-300"
              style={{ width: `${generationProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={isGenerating || !jobTypeId || phase === 'review' || phase === 'published'}
        className="w-full py-3 rounded-xl font-bold text-sm text-white transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed"
        style={{
          background: isGenerating
            ? 'rgba(248, 113, 113, 0.2)'
            : 'linear-gradient(135deg, #f87171 0%, #ef4444 100%)',
          boxShadow: isGenerating ? 'none' : '0 0 30px rgba(248, 113, 113, 0.25)',
        }}
      >
        {isGenerating ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
            </svg>
            Generating Prediction…
          </span>
        ) : phase === 'review' ? (
          '✓ Generation Complete — Review Below'
        ) : phase === 'published' ? (
          '✓ Published'
        ) : (
          '⚡ Generate Prediction'
        )}
      </button>
    </div>
  );
}
