/**
 * StudyStreakCalendar — GitHub-style contribution grid.
 * Green shading intensity based on minutes studied per day.
 * Shows the past 90 days of study activity.
 */

'use client';

import { useMemo } from 'react';

interface StudyDay {
  date: string;
  minutes_studied: number;
}

interface Props {
  data: StudyDay[];
}

/** Map minutes → intensity level 0–4 */
function getLevel(mins: number): number {
  if (mins === 0) return 0;
  if (mins < 15) return 1;
  if (mins < 45) return 2;
  if (mins < 90) return 3;
  return 4;
}

const LEVEL_COLORS = [
  'rgba(139, 92, 246, 0.06)',    // 0 — none
  'rgba(52, 211, 153, 0.25)',    // 1 — light
  'rgba(52, 211, 153, 0.45)',    // 2 — medium
  'rgba(52, 211, 153, 0.7)',     // 3 — strong
  '#34d399',                      // 4 — max
];

const DAY_LABELS = ['', 'Mon', '', 'Wed', '', 'Fri', ''];

export default function StudyStreakCalendar({ data }: Props) {
  const { weeks, monthLabels, maxMinutes } = useMemo(() => {
    // Build map of date → minutes
    const map = new Map<string, number>();
    let max = 0;
    for (const d of data) {
      map.set(d.date, d.minutes_studied);
      if (d.minutes_studied > max) max = d.minutes_studied;
    }

    // Build weeks (columns). First find the start day
    const today = new Date();
    const start = new Date(today);
    start.setDate(start.getDate() - 89);

    // Align start to previous Sunday
    const startDay = start.getDay();
    start.setDate(start.getDate() - startDay);

    const weeks: { date: string; level: number; minutes: number; day: number }[][] = [];
    const months: { label: string; col: number }[] = [];
    let lastMonth = -1;
    let col = 0;

    const cursor = new Date(start);
    while (cursor <= today || weeks.length === 0 || weeks[weeks.length - 1].length < 7) {
      if (weeks.length === 0 || weeks[weeks.length - 1].length === 7) {
        weeks.push([]);
        col = weeks.length - 1;

        // Track month label at first week of each month
        const m = cursor.getMonth();
        if (m !== lastMonth) {
          months.push({
            label: cursor.toLocaleString('en', { month: 'short' }),
            col,
          });
          lastMonth = m;
        }
      }

      const dateStr = cursor.toISOString().split('T')[0];
      const mins = map.get(dateStr) || 0;
      const isPast = cursor <= today;

      weeks[weeks.length - 1].push({
        date: dateStr,
        level: isPast ? getLevel(mins) : -1,
        minutes: mins,
        day: cursor.getDay(),
      });

      cursor.setDate(cursor.getDate() + 1);

      // Safety: don't exceed ~14 weeks
      if (weeks.length > 14 && weeks[weeks.length - 1].length === 7) break;
    }

    return { weeks, monthLabels: months, maxMinutes: max };
  }, [data]);

  const cellSize = 14;
  const gap = 3;
  const labelWidth = 28;

  return (
    <div className="flex flex-col gap-3">
      {/* Month labels */}
      <div className="flex" style={{ paddingLeft: labelWidth }}>
        {monthLabels.map((m, i) => (
          <span
            key={i}
            className="text-[10px] text-[var(--clr-text-muted)]"
            style={{
              position: 'relative',
              left: m.col * (cellSize + gap),
              marginRight: gap,
            }}
          >
            {m.label}
          </span>
        ))}
      </div>

      {/* Grid */}
      <div className="flex gap-0.5">
        {/* Day labels */}
        <div
          className="flex flex-col justify-between"
          style={{ width: labelWidth, height: 7 * (cellSize + gap) - gap }}
        >
          {DAY_LABELS.map((lbl, i) => (
            <span key={i} className="text-[10px] text-[var(--clr-text-muted)] leading-none" style={{ height: cellSize }}>
              {lbl}
            </span>
          ))}
        </div>

        {/* Weeks */}
        <div className="flex" style={{ gap }}>
          {weeks.map((week, wi) => (
            <div key={wi} className="flex flex-col" style={{ gap }}>
              {week.map((cell, di) => (
                <div
                  key={di}
                  title={cell.level >= 0 ? `${cell.date}: ${cell.minutes} min` : ''}
                  style={{
                    width: cellSize,
                    height: cellSize,
                    borderRadius: 3,
                    background: cell.level >= 0 ? LEVEL_COLORS[cell.level] : 'transparent',
                    transition: 'background 200ms',
                  }}
                />
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-2 mt-1" style={{ paddingLeft: labelWidth }}>
        <span className="text-[10px] text-[var(--clr-text-muted)]">Less</span>
        {LEVEL_COLORS.map((c, i) => (
          <div
            key={i}
            style={{
              width: cellSize,
              height: cellSize,
              borderRadius: 3,
              background: c,
            }}
          />
        ))}
        <span className="text-[10px] text-[var(--clr-text-muted)]">More</span>
        {maxMinutes > 0 && (
          <span className="text-[10px] text-[var(--clr-text-muted)] ml-2">
            Peak: {maxMinutes} min
          </span>
        )}
      </div>
    </div>
  );
}
