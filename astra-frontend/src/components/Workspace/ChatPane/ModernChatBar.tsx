import React, { useState, useRef, useCallback } from 'react';
import { Paperclip, Globe, ArrowUp } from 'lucide-react';

interface ModernChatBarProps {
  onSend: (message: string, options: { searchWeb: boolean; attachedFiles: File[] }) => void;
  disabled?: boolean;
  draft?: string;
  onDraftChange?: (value: string) => void;
}

export const ModernChatBar: React.FC<ModernChatBarProps> = ({ onSend, disabled = false, draft, onDraftChange }) => {
  const [localText, setLocalText] = useState('');
  const text = draft ?? localText;
  const setText = (value: string) => { setLocalText(value); onDraftChange?.(value); };
  const [searchWeb, setSearchWeb] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    // Max ~5 lines at 22px line-height + padding
    el.style.height = Math.min(el.scrollHeight, 130) + 'px';
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    adjustHeight();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed, { searchWeb, attachedFiles });
    setText('');
    setAttachedFiles([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachedFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
    e.target.value = '';
  };

  return (
    <div className="studio-composer"
      style={{
        padding: '10px 12px',
        borderTop: '1px solid #e2e8f0',
        background: '#ffffff',
        flexShrink: 0,
      }}
    >
      {/* Attached files indicator */}
      {attachedFiles.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
          {attachedFiles.map((f, i) => (
            <span
              key={i}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                fontSize: 12,
                color: '#334155',
                background: '#f1f5f9',
                border: '1px solid #e2e8f0',
                borderRadius: 4,
                padding: '2px 8px',
              }}
            >
              {f.name}
              <button
                onClick={() => setAttachedFiles((prev) => prev.filter((_, j) => j !== i))}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 0, lineHeight: 1 }}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Main input container */}
      <div className="composer-box"
        style={{
          border: '1.5px solid #cbd5e1',
          borderRadius: 6,
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
          background: '#ffffff',
          transition: 'border-color 150ms ease',
        }}
        onFocusCapture={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = '#24634b';
        }}
        onBlurCapture={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = '#cbd5e1';
        }}
      >
        <textarea
          ref={textareaRef}
          aria-label="Yêu cầu soạn đề"
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ví dụ: Tạo 20 câu Toán lớp 12 về đạo hàm"
          rows={1}
          style={{
            width: '100%',
            resize: 'none',
            border: 'none',
            outline: 'none',
            padding: '10px 12px 6px',
            fontSize: 16,
            color: '#0f172a',
            background: 'transparent',
            lineHeight: '22px',
            fontFamily: 'inherit',
            boxSizing: 'border-box',
            overflowY: 'auto',
          }}
        />

        {/* Toolbar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '4px 8px 6px',
            gap: 4,
          }}
        >
          {/* Attach */}
          <button
            onClick={() => fileInputRef.current?.click()}
            title="Đính kèm tài liệu"
            aria-label="Đính kèm tài liệu"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: 15,
              color: '#64748b',
              padding: '4px 6px',
              borderRadius: 4,
              lineHeight: 1,
            }}
          >
            <Paperclip size={18} />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />

          {/* Search web toggle */}
          <button
            onClick={() => setSearchWeb((v) => !v)}
            title="Tìm trên mạng"
            aria-pressed={searchWeb}
            style={{
              background: searchWeb ? '#edf4ef' : 'none',
              border: searchWeb ? '1px solid #059669' : '1px solid transparent',
              cursor: 'pointer',
              fontSize: 13,
              color: searchWeb ? '#24634b' : '#64748b',
              padding: '3px 8px',
              borderRadius: 4,
              lineHeight: 1.5,
              fontWeight: searchWeb ? 600 : 400,
              transition: 'all 150ms ease',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <Globe size={16} />
            <span style={{ fontSize: 12 }}>Tìm mạng</span>
          </button>

          {/* Spacer */}
          <div style={{ flex: 1 }} />

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={!text.trim() || disabled}
            style={{
              background: !text.trim() || disabled ? '#e2e8f0' : '#24634b',
              color: !text.trim() || disabled ? '#94a3b8' : '#ffffff',
              border: 'none',
              borderRadius: 5,
              width: 44,
              height: 44,
              cursor: !text.trim() || disabled ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
              transition: 'background 150ms ease',
              flexShrink: 0,
            }}
            title="Gửi"
            aria-label="Gửi yêu cầu"
          >
            <ArrowUp size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};
