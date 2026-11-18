import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Paperclip, Globe, ArrowUp } from 'lucide-react';

interface ModernChatBarProps {
  onSend: (message: string, options: { searchWeb: boolean; attachedFiles: File[] }) => void;
  disabled?: boolean;
  draft?: string;
  onDraftChange?: (value: string) => void;
  busy?: boolean;
}

export const ModernChatBar: React.FC<ModernChatBarProps> = ({ onSend, disabled = false, draft, onDraftChange, busy = false }) => {
  const [localText, setLocalText] = useState('');
  const text = draft ?? localText;
  const setText = (value: string) => { setLocalText(value); onDraftChange?.(value); };
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    // Max ~5 lines at 22px line-height + padding
    el.style.height = Math.min(el.scrollHeight, 130) + 'px';
  }, []);

  useEffect(adjustHeight, [text, adjustHeight]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    adjustHeight();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled || busy) return;
    onSend(trimmed, { searchWeb: false, attachedFiles: [] });
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
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
      {/* Main input container */}
      <div className="composer-box">
        <textarea
          ref={textareaRef}
          aria-label="Yêu cầu soạn đề"
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
            disabled={disabled || busy}
          placeholder="Mô tả yêu cầu cho đề Toán THPT 22 câu"
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
            disabled
            title="Đính kèm chưa được hỗ trợ trong phiên bản này"
            aria-label="Đính kèm chưa được hỗ trợ"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'not-allowed',
              fontSize: 15,
              color: '#64748b',
              padding: '4px 6px',
              borderRadius: 4,
              lineHeight: 1,
            }}
          >
            <Paperclip size={18} />
          </button>
          {/* Search web toggle */}
          <button
            disabled
            title="Tìm mạng chưa được hỗ trợ trong phiên bản này"
            aria-pressed={false}
            style={{
              background: 'none',
              border: '1px solid transparent',
              cursor: 'not-allowed',
              fontSize: 13,
              color: '#94a3b8',
              padding: '3px 8px',
              borderRadius: 4,
              lineHeight: 1.5,
              fontWeight: 400,
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
            disabled={!text.trim() || disabled || busy}
            style={{
              background: !text.trim() || disabled || busy ? '#e2e8f0' : '#24634b',
              color: !text.trim() || disabled || busy ? '#94a3b8' : '#ffffff',
              border: 'none',
              borderRadius: 5,
              width: 44,
              height: 44,
              cursor: !text.trim() || disabled || busy ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
              transition: 'background 150ms ease',
              flexShrink: 0,
            }}
            title={busy ? 'ASTRA đang xử lý' : 'Gửi'}
            aria-label="Gửi yêu cầu"
          >
            <ArrowUp size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};
