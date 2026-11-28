import { getActiveUploads, subscribeUploads } from '../../../services/inputDocuments';
import React, { useSyncExternalStore, useState, useRef, useCallback, useEffect, useId } from 'react';
import { Globe, ArrowUp, Paperclip, SlidersHorizontal, X } from 'lucide-react';

import { DocumentAttachments } from '../../DocumentAttachments';
import type { InputDocument, InputDocumentsUpdate } from '../../../services/inputDocuments';

interface ModernChatBarProps {
  documents?: InputDocument[];
  onDocumentsChange?: (documents: InputDocumentsUpdate) => void;
  onSend: (message: string, options: { searchWeb: boolean; attachedFiles: InputDocument[] }) => void;
  disabled?: boolean;
  draft?: string;
  onDraftChange?: (value: string) => void;
  compact?: boolean;
}

export const ModernChatBar: React.FC<ModernChatBarProps> = ({
  onSend,
  disabled = false,
  draft,
  onDraftChange,
  documents,
  onDocumentsChange,
  compact = false,
}) => {
  const [localText, setLocalText] = useState('');
  const text = draft ?? localText;
  const setText = (value: string) => { setLocalText(value); onDraftChange?.(value); };
  const [searchWeb, setSearchWeb] = useState(false);
  const [optionsOpen, setOptionsOpen] = useState(false);
  const [attachmentsOpen, setAttachmentsOpen] = useState(false);
  const [localDocuments, setLocalDocuments] = useState<InputDocument[]>([]);
  const attachedFiles = documents ?? localDocuments;
  const setAttachedFiles = (value: InputDocumentsUpdate) => { setLocalDocuments(value); onDocumentsChange?.(value); };
  const [localUploading, setUploading] = useState(false);
  const activeUploads = useSyncExternalStore(subscribeUploads, getActiveUploads);
  const uploading = localUploading || activeUploads > 0;
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const optionsId = useId();
  const optionsTrigger = useRef<HTMLButtonElement>(null);
  const optionsPopover = useRef<HTMLDivElement>(null);

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 128) + 'px';
  }, []);

  useEffect(adjustHeight, [text, adjustHeight]);

  useEffect(() => {
    if (!optionsOpen) return;
    function handleOutside(event: PointerEvent) {
      const target = event.target as Node;
      if (!optionsTrigger.current?.contains(target) && !optionsPopover.current?.contains(target)) {
        setOptionsOpen(false);
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key !== 'Escape') return;
      setOptionsOpen(false);
      optionsTrigger.current?.focus();
    }
    document.addEventListener('pointerdown', handleOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('pointerdown', handleOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [optionsOpen]);

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
    setOptionsOpen(false);
    if (compact) setAttachmentsOpen(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const canSend = (Boolean(text.trim()) || attachedFiles.length > 0) && !disabled && !uploading;
  const showAttachStrip = !compact || attachmentsOpen || attachedFiles.length > 0;

  return (
    <div className={`studio-composer ${compact ? 'is-compact' : ''}`}>
      <div className="composer-box">
        {showAttachStrip && (
          <div className="composer-attach-header">
            <DocumentAttachments
              documents={attachedFiles}
              onChange={setAttachedFiles}
              disabled={disabled}
              onBusyChange={setUploading}
              compact={compact}
              toolsOpen={!compact || attachmentsOpen}
            />
          </div>
        )}

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
          {compact && (
            <button
              type="button"
              className={`composer-tool-btn ${attachmentsOpen || attachedFiles.length > 0 ? 'is-active' : ''}`}
              onClick={() => setAttachmentsOpen(value => !value)}
              aria-expanded={attachmentsOpen}
              title="Đính kèm tài liệu đầu vào"
            >
              <Paperclip size={14} aria-hidden="true" />
              <span>Đính kèm{attachedFiles.length > 0 ? ` (${attachedFiles.length})` : ''}</span>
            </button>
          )}

          <div className="composer-options-wrap">
            <button
              ref={optionsTrigger}
              type="button"
              className={`composer-tool-btn ${optionsOpen || searchWeb ? 'is-active' : ''}`}
              aria-expanded={optionsOpen}
              aria-controls={optionsOpen ? optionsId : undefined}
              onClick={() => setOptionsOpen(value => !value)}
              title="Tuỳ chọn mở rộng"
            >
              <SlidersHorizontal size={14} aria-hidden="true" />
              <span>Tuỳ chọn</span>
            </button>

            {optionsOpen && (
              <div ref={optionsPopover} id={optionsId} className="composer-options-popover" role="region" aria-label="Tuỳ chọn mở rộng">
                <label className="composer-option-toggle">
                  <input
                    type="checkbox"
                    checked={searchWeb}
                    onChange={e => setSearchWeb(e.target.checked)}
                  />
                  <span>
                    <strong>
                      <Globe size={13} aria-hidden="true" /> Tìm kiếm trên mạng
                    </strong>
                    <small>Tìm cấu trúc đề tham khảo cho các chủ đề lân cận: SAT, IELTS, TOEIC, TOEFL, ACT.</small>
                  </span>
                </label>
              </div>
            )}
          </div>

          {searchWeb && (
            <button
              type="button"
              className="composer-scope-chip"
              onClick={() => setSearchWeb(false)}
              title="Đang bật Tìm mạng cho SAT, IELTS, TOEIC, TOEFL, ACT — nhấn để tắt"
            >
              <Globe size={12} aria-hidden="true" />
              <span>Tìm mạng: SAT, IELTS, TOEIC, TOEFL, ACT</span>
              <X size={12} aria-hidden="true" />
            </button>
          )}

          <div className="composer-toolbar-spacer" />

          {disabled && (
            <span className="composer-hint" role="status" aria-live="polite">
              Đang đọc yêu cầu…
            </span>
          )}

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
