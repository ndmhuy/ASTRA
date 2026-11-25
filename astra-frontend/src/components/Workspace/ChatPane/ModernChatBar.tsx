import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Paperclip, Globe, ArrowUp, X } from 'lucide-react';

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
    el.style.height = Math.min(el.scrollHeight, 140) + 'px';
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

  const canSend = Boolean(text.trim()) && !disabled;

  return (
    <div className="studio-composer">
      {attachedFiles.length > 0 && (
        <div className="composer-attachments">
          {attachedFiles.map((f, i) => (
            <span key={`${f.name}-${i}`} className="composer-file-chip">
              <span>{f.name}</span>
              <button
                type="button"
                className="composer-file-remove"
                aria-label={`Bỏ đính kèm ${f.name}`}
                onClick={() => setAttachedFiles((prev) => prev.filter((_, j) => j !== i))}
              >
                <X size={13} aria-hidden="true" />
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="composer-box">
        <textarea
          ref={textareaRef}
          className="composer-textarea"
          aria-label="Yêu cầu soạn đề"
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Mô tả yêu cầu cho đề thi thầy cô muốn soạn..."
          rows={1}
        />

        <div className="composer-toolbar">
          <button
            type="button"
            className="composer-tool-btn"
            onClick={() => fileInputRef.current?.click()}
            title="Đính kèm tài liệu"
            aria-label="Đính kèm tài liệu"
          >
            <Paperclip size={16} aria-hidden="true" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="composer-file-input"
            onChange={handleFileChange}
          />

          <button
            type="button"
            className={`composer-tool-btn ${searchWeb ? 'is-active' : ''}`}
            onClick={() => setSearchWeb((v) => !v)}
            title="Tìm trên mạng"
            aria-pressed={searchWeb}
          >
            <Globe size={15} aria-hidden="true" />
            <span>Tìm mạng</span>
          </button>

          <div className="composer-toolbar-spacer" />

          <span className="composer-hint" aria-hidden="true">
            Enter gửi · Shift+Enter xuống dòng
          </span>

          <button
            type="button"
            className={`composer-send-btn ${canSend ? 'is-ready' : ''}`}
            onClick={handleSend}
            disabled={!canSend}
            title="Gửi"
            aria-label="Gửi yêu cầu"
          >
            <ArrowUp size={17} aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
};
