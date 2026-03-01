/**
 * BookmarkPanel — Slide-out panel listing all bookmarked paragraphs.
 * Allows jumping to a bookmark or removing it.
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';
import Icon from '@/components/Icon';

interface BookmarkData {
  paragraph_index: number;
  text_preview: string;
  created_at: string;
}

interface StorySection {
  title: string;
  paragraphs: string[];
  rawText: string;
}

interface BookmarkPanelProps {
  bookmarks: BookmarkData[];
  sections: StorySection[];
  onClose: () => void;
  onJumpTo: (paragraphIndex: number) => void;
  onRemove: (paragraphIndex: number) => void;
}

export default function BookmarkPanel({
  bookmarks,
  sections,
  onClose,
  onJumpTo,
  onRemove,
}: BookmarkPanelProps) {
  /** Find which section a global paragraph index belongs to */
  function getSectionTitle(paraIndex: number): string {
    let offset = 0;
    for (const section of sections) {
      if (paraIndex < offset + section.paragraphs.length) {
        return section.title;
      }
      offset += section.paragraphs.length;
    }
    return 'Unknown Section';
  }

  return (
    <>
      {/* Overlay backdrop */}
      <motion.div
        onClick={onClose}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          zIndex: 60,
          backdropFilter: 'blur(4px)',
        }}
      />

      {/* Panel */}
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: '360px',
          maxWidth: '90vw',
          zIndex: 70,
          background: 'var(--clr-bg-surface)',
          borderLeft: '1px solid var(--clr-glass-border)',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '-8px 0 40px rgba(0, 0, 0, 0.5)',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: 'var(--space-5) var(--space-5)',
            borderBottom: '1px solid var(--clr-glass-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div className="flex items-center gap-2">
            <Icon name="star" size={18} color="var(--clr-gold)" />
            <h3 className="font-display font-bold text-base">Bookmarks</h3>
            <span className="badge badge-gold" style={{ fontSize: '10px' }}>
              {bookmarks.length}
            </span>
          </div>
          <button onClick={onClose} style={{ opacity: 0.6 }}>
            <Icon name="x" size={18} />
          </button>
        </div>

        {/* Bookmark list */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-4)' }}>
          {bookmarks.length === 0 ? (
            <div className="text-center" style={{ padding: 'var(--space-12) var(--space-4)', color: 'var(--clr-text-muted)' }}>
              <Icon name="star" size={32} color="var(--clr-text-muted)" className="mx-auto mb-3" />
              <p className="text-sm">No bookmarks yet</p>
              <p className="text-xs mt-1">Click any paragraph to bookmark it</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {bookmarks.map((bm) => (
                <div
                  key={bm.paragraph_index}
                  className="glass-sm"
                  style={{
                    padding: 'var(--space-3) var(--space-4)',
                    cursor: 'pointer',
                    transition: 'all var(--duration-fast) var(--ease-out)',
                    borderLeft: '2px solid var(--clr-gold)',
                  }}
                  onClick={() => onJumpTo(bm.paragraph_index)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium" style={{ color: 'var(--clr-gold)' }}>
                      {getSectionTitle(bm.paragraph_index)}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemove(bm.paragraph_index);
                      }}
                      style={{ opacity: 0.4, transition: 'opacity var(--duration-fast)' }}
                      onMouseEnter={(e) => { (e.target as HTMLElement).style.opacity = '1'; }}
                      onMouseLeave={(e) => { (e.target as HTMLElement).style.opacity = '0.4'; }}
                    >
                      <Icon name="x" size={12} />
                    </button>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--clr-text-secondary)', lineHeight: '1.5' }}>
                    {bm.text_preview || 'Bookmarked paragraph'}…
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </>
  );
}
