/**
 * StorySectionBlock — A single story section with beautiful typography.
 *
 * Features:
 *  - Auto-highlight: dates (orange), named entities (blue), organizations (purple)
 *  - High-frequency fact badges on matching paragraphs
 *  - Click paragraph to bookmark
 *  - Margin click to add a note
 */

'use client';

import { useRef, useEffect, useCallback, useMemo } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Icon from '@/components/Icon';

gsap.registerPlugin(ScrollTrigger);

interface BookmarkData {
  paragraph_index: number;
  text_preview: string;
  created_at: string;
}

interface StorySectionBlockProps {
  sectionIndex: number;
  title: string;
  paragraphs: string[];
  globalParaOffset: number;
  bookmarks: BookmarkData[];
  highFreqFactTexts: Set<string>;
  onToggleBookmark: (paragraphIndex: number, textPreview: string) => void;
  onOpenNote: () => void;
  existingNote?: string;
}

/* ── Regex patterns for auto-highlighting ── */

// Dates: "1947", "March 1947", "23 March 1947", "1947-03-23", "23/03/1947", etc.
const DATE_REGEX = /\b(\d{1,2}[\s/-](?:January|February|March|April|May|June|July|August|September|October|November|December)[\s/-]\d{4}|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\b\d{1,2}\/\d{1,2}\/\d{4}|\b\d{4}-\d{2}-\d{2}|\b(?:19|20)\d{2}\b)\b/gi;

// Named entities: Capitalized multi-word names (2+ consecutive capitalized words)
const ENTITY_REGEX = /\b([A-Z][a-z]+(?:\s+(?:of|the|and|al-|bin|ibn|ul|ur)\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b/g;

// Organizations: Common org patterns — acronyms, "Commission", "Council", "Authority", etc.
const ORG_REGEX = /\b([A-Z]{2,6}(?:\s|$)|(?:United\s+Nations|European\s+Union|World\s+(?:Bank|Health|Trade)|International\s+\w+|(?:National|Provincial|Federal|Supreme|High|Punjab|Pakistan)\s+(?:Assembly|Commission|Council|Authority|Board|Committee|Court|Service|Government|Bureau))\w*)\b/g;

/** Highlight a text string with colored spans for dates, entities, and orgs */
function highlightText(text: string): string {
  // We apply highlights in a specific order to avoid overlapping
  // First mark all positions to highlight
  type Highlight = { start: number; end: number; type: 'date' | 'entity' | 'org' };
  const highlights: Highlight[] = [];

  // Find dates
  let match: RegExpExecArray | null;
  const dateRe = new RegExp(DATE_REGEX.source, DATE_REGEX.flags);
  while ((match = dateRe.exec(text)) !== null) {
    highlights.push({ start: match.index, end: match.index + match[0].length, type: 'date' });
  }

  // Find organizations (before entities so they take priority)
  const orgRe = new RegExp(ORG_REGEX.source, ORG_REGEX.flags);
  while ((match = orgRe.exec(text)) !== null) {
    // Skip very short matches
    if (match[0].length < 3) continue;
    highlights.push({ start: match.index, end: match.index + match[0].length, type: 'org' });
  }

  // Find named entities
  const entityRe = new RegExp(ENTITY_REGEX.source, ENTITY_REGEX.flags);
  while ((match = entityRe.exec(text)) !== null) {
    // Skip if it overlaps with an existing highlight
    const overlaps = highlights.some(
      (h) => match!.index < h.end && match!.index + match![0].length > h.start,
    );
    if (overlaps) continue;
    // Skip common sentence starters
    const skipWords = ['The', 'This', 'That', 'These', 'Those', 'However', 'Moreover', 'Furthermore', 'According', 'During', 'After', 'Before', 'While', 'Since', 'Until', 'Although'];
    if (skipWords.some((w) => match![0].startsWith(w + ' '))) continue;
    highlights.push({ start: match.index, end: match.index + match[0].length, type: 'entity' });
  }

  // Sort highlights by start position (descending) to apply from end
  highlights.sort((a, b) => b.start - a.start);

  // Remove overlapping highlights (keep first occurrence)
  const filtered: Highlight[] = [];
  let lastStart = text.length;
  for (const h of highlights) {
    if (h.end <= lastStart) {
      filtered.push(h);
      lastStart = h.start;
    }
  }

  // Apply highlights to text (from end to preserve indices)
  let result = text;
  for (const h of filtered) {
    const span = result.slice(h.start, h.end);
    const colorClass =
      h.type === 'date'
        ? 'story-hl-date'
        : h.type === 'org'
          ? 'story-hl-org'
          : 'story-hl-entity';
    result = result.slice(0, h.start) + `<span class="${colorClass}">${span}</span>` + result.slice(h.end);
  }

  return result;
}

export default function StorySectionBlock({
  sectionIndex,
  title,
  paragraphs,
  globalParaOffset,
  bookmarks,
  highFreqFactTexts,
  onToggleBookmark,
  onOpenNote,
  existingNote,
}: StorySectionBlockProps) {
  const sectionRef = useRef<HTMLDivElement>(null);

  /* ── Fade-in animation ── */
  useEffect(() => {
    if (!sectionRef.current) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(
        sectionRef.current,
        { opacity: 0, y: 30 },
        {
          opacity: 1,
          y: 0,
          duration: 0.7,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 85%',
            toggleActions: 'play none none none',
          },
        },
      );
    });
    return () => ctx.revert();
  }, []);

  /* ── Check if paragraph contains a high-freq fact ── */
  const isHighFreq = useCallback(
    (paraText: string) => {
      const lower = paraText.toLowerCase();
      for (const fact of highFreqFactTexts) {
        // Fuzzy match — check if significant portion of fact appears
        const words = fact.split(/\s+/).filter((w) => w.length > 3);
        const matchCount = words.filter((w) => lower.includes(w)).length;
        if (words.length > 0 && matchCount / words.length >= 0.6) return true;
      }
      return false;
    },
    [highFreqFactTexts],
  );

  return (
    <div ref={sectionRef} className="story-section-block" style={{ opacity: 0 }}>
      {/* Section heading */}
      <div className="flex items-center gap-3" style={{ marginBottom: 'var(--space-6)' }}>
        <div
          style={{
            width: '4px',
            height: '28px',
            borderRadius: '2px',
            background: 'var(--grad-vivid)',
            flexShrink: 0,
          }}
        />
        <h2
          className="font-display font-bold"
          style={{
            fontSize: 'var(--text-2xl)',
            color: 'var(--clr-text-primary)',
            lineHeight: 'var(--leading-tight)',
          }}
        >
          {title}
        </h2>

        {/* Note button in margin */}
        <button
          onClick={onOpenNote}
          className="ml-auto"
          title="Add a note to this section"
          style={{
            opacity: 0.4,
            transition: 'opacity var(--duration-fast) var(--ease-out)',
            flexShrink: 0,
          }}
          onMouseEnter={(e) => { (e.target as HTMLElement).style.opacity = '1'; }}
          onMouseLeave={(e) => { (e.target as HTMLElement).style.opacity = '0.4'; }}
        >
          <Icon
            name="file-text"
            size={18}
            color={existingNote ? 'var(--clr-neon)' : 'var(--clr-text-muted)'}
          />
        </button>
      </div>

      {/* Paragraphs */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
        {paragraphs.map((para, pIdx) => {
          const globalIdx = globalParaOffset + pIdx;
          const isBookmarked = bookmarks.some((b) => b.paragraph_index === globalIdx);
          const isHF = isHighFreq(para);
          const highlighted = highlightText(para);

          return (
            <div
              key={pIdx}
              id={`para-${globalIdx}`}
              className="story-paragraph-wrapper"
              style={{
                position: 'relative',
                cursor: 'pointer',
                paddingLeft: 'var(--space-4)',
                borderLeft: isBookmarked
                  ? '3px solid var(--clr-gold)'
                  : '3px solid transparent',
                transition: 'border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out)',
                borderRadius: '2px',
                background: isBookmarked ? 'rgba(251, 191, 36, 0.03)' : 'transparent',
              }}
              onClick={() => onToggleBookmark(globalIdx, para)}
            >
              {/* High-frequency badge */}
              {isHF && (
                <span
                  className="badge badge-warning"
                  style={{
                    fontSize: '9px',
                    padding: '1px 8px',
                    marginBottom: 'var(--space-1)',
                    display: 'inline-flex',
                  }}
                >
                  🔥 High Frequency
                </span>
              )}

              {/* Paragraph text with auto-highlighting */}
              <p
                className="story-paragraph"
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: 'var(--text-lg)',
                  lineHeight: '1.85',
                  color: 'var(--clr-text-primary)',
                  letterSpacing: '0.01em',
                  fontWeight: 'var(--weight-normal)',
                }}
                dangerouslySetInnerHTML={{ __html: highlighted }}
              />

              {/* Bookmark indicator */}
              {isBookmarked && (
                <div
                  style={{
                    position: 'absolute',
                    top: '2px',
                    right: '-28px',
                    opacity: 0.7,
                  }}
                >
                  <Icon name="star" size={14} color="var(--clr-gold)" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
