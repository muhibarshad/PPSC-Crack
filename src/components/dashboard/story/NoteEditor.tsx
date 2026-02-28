/**
 * NoteEditor — Inline note editor for a story section.
 * Saves personal notes attached to a specific section index.
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import Icon from '@/components/Icon';

interface NoteEditorProps {
  sectionIndex: number;
  initialText: string;
  onSave: (sectionIndex: number, noteText: string) => void;
  onCancel: () => void;
}

export default function NoteEditor({ sectionIndex, initialText, onSave, onCancel }: NoteEditorProps) {
  const [text, setText] = useState(initialText);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  return (
    <div
      className="glass-sm animate-fade-in"
      style={{
        padding: 'var(--space-4)',
        margin: 'var(--space-4) 0',
        borderLeft: '3px solid var(--clr-neon)',
      }}
    >
      <div className="flex items-center gap-2 mb-3">
        <Icon name="file-text" size={14} color="var(--clr-neon)" />
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--clr-neon)' }}>
          Personal Note — Section {sectionIndex + 1}
        </span>
      </div>

      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Write your note here…"
        rows={3}
        style={{
          width: '100%',
          background: 'rgba(22, 18, 52, 0.4)',
          border: '1px solid var(--clr-glass-border)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-3)',
          color: 'var(--clr-text-primary)',
          fontSize: 'var(--text-sm)',
          lineHeight: '1.6',
          resize: 'vertical',
          outline: 'none',
          fontFamily: 'var(--font-body)',
        }}
        onFocus={(e) => { (e.target as HTMLElement).style.borderColor = 'var(--clr-neon)'; }}
        onBlur={(e) => { (e.target as HTMLElement).style.borderColor = 'var(--clr-glass-border)'; }}
      />

      <div className="flex items-center gap-2" style={{ marginTop: 'var(--space-3)' }}>
        <button
          className="btn btn-sm"
          style={{
            background: 'var(--clr-neon-dim)',
            color: 'var(--clr-neon)',
            border: '1px solid rgba(232, 121, 249, 0.2)',
          }}
          onClick={() => onSave(sectionIndex, text)}
        >
          <Icon name="check" size={12} />
          Save Note
        </button>
        <button
          className="btn btn-ghost btn-sm"
          onClick={onCancel}
        >
          Cancel
        </button>
        {initialText && (
          <button
            className="btn btn-sm ml-auto"
            style={{
              background: 'var(--clr-danger-dim)',
              color: 'var(--clr-danger)',
              border: '1px solid rgba(248, 113, 113, 0.2)',
            }}
            onClick={() => onSave(sectionIndex, '')}
          >
            <Icon name="x" size={12} />
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
