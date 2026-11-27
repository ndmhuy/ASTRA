import { getActiveUploads, subscribeUploads } from '../../../services/inputDocuments';
import React, { useSyncExternalStore, useState, useRef, useCallback, useEffect } from 'react';
import { Globe, ArrowUp } from 'lucide-react';

import { DocumentAttachments } from '../../DocumentAttachments';
import type { InputDocument, InputDocumentsUpdate } from '../../../services/inputDocuments';

interface ModernChatBarProps {
  documents?: InputDocument[];
  onDocumentsChange?: (documents: InputDocumentsUpdate) => void;
  onSend: (message: string, options: { searchWeb: boolean; attachedFiles: InputDocument[] }) => void;
  disabled?: boolean;
  draft?: string;
  onDraftChange?: (value: string) => void;
}

export const ModernChatBar: React.FC<ModernChatBarProps> = ({ onSend, disabled = false, draft, onDraftChange, documents, onDocumentsChange }) => {
  const [localText, setLocalText] = useState('');
  const text = draft ?? localText;
  const setText = (value: string) => { setLocalText(value); onDraftChange?.(value); };
  const [searchWeb, setSearchWeb] = useState(false);
  const [localDocuments, setLocalDocuments] = useState<InputDocument[]>([]);
  const attachedFiles = documents ?? localDocuments;
  const setAttachedFiles = (value: InputDocumentsUpdate) => { setLocalDocuments(value); onDocumentsChange?.(value); };
  const [localUploading, setUploading] = useState(false);
  const activeUploads = useSyncExternalStore(subscribeUploads, getActiveUploads);
  const uploading = localUploading || activeUploads > 0;
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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
    const trimmed = text.trim() || (attachedFiles.length ? 'Soạn đề dựa trên tài liệu đính kèm.' : '');
    if (!trimmed || disabled || uploading) return;
    onSend(trimmed, { searchWeb, attachedFiles });
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const canSend = (Boolean(text.trim()) || attachedFiles.length > 0) && !disabled && !uploading;

  return (
    <div className="studio-composer">
      <DocumentAttachments documents={attachedFiles} onChange={setAttachedFiles} disabled={disabled} onBusyChange={setUploading} />

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
            className={`composer-tool-btn ${searchWeb ? 'is-active' : ''}`}
            onClick={() => setSearchWeb((v) => !v)}
            title="Tìm trên mạng cho chủ đề lân cận (SAT, IELTS, TOEIC, TOEFL, ACT)"
            aria-pressed={searchWeb}
          >
            <Globe size={15} aria-hidden="true" />
            <span>Tìm mạng</span>
          </button>

          <div className="composer-toolbar-spacer" />

          <span className="composer-hint" role={disabled ? 'status' : undefined} aria-live="polite">
            {disabled ? 'Đang đọc yêu cầu…' : 'Enter gửi · Shift+Enter xuống dòng'}
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
