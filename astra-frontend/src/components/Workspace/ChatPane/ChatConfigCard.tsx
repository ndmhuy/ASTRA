import React from 'react';
import { AlertTriangle, CheckCircle2, HelpCircle, Play, Settings2, X } from 'lucide-react';
import type { ExamFormat } from '../../../types/exam';
import type { ChatConfigDraft } from '../../../agent/chatConfig';

interface PendingActionProps {
  label: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

interface ChatConfigCardProps {
  draft?: ChatConfigDraft | null;
  formats: ExamFormat[];
  pendingAction?: PendingActionProps | null;
  disabled?: boolean;
  onChange?: (patch: Partial<Pick<ChatConfigDraft, 'formatId' | 'topic' | 'difficulty' | 'extraNotes'>>) => void;
  onGenerate?: () => void;
  onOpenModal?: () => void;
  onDismiss?: () => void;
}

export const ChatConfigCard: React.FC<ChatConfigCardProps> = ({
  draft,
  formats,
  pendingAction,
  disabled = false,
  onChange,
  onGenerate,
  onOpenModal,
  onDismiss,
}) => {
  if (!draft && !pendingAction) return null;

  const availableFormats = formats.filter(f => f.available);
  const selectedFormat = draft?.formatId ? availableFormats.find(f => f.id === draft.formatId) : undefined;

  const cardTone = draft?.needsClarification.length
    ? 'is-missing'
    : draft?.hasMismatch
      ? 'is-limit'
      : 'is-ready';

  return (
    <section className={`chat-config-card ${cardTone}`} aria-label="Cấu hình đề thi từ yêu cầu">
      {pendingAction && (
        <div className="chat-config-pending">
          <div className="chat-config-pending-header">
            <span className="chat-config-badge is-ready">Chờ xác nhận</span>
            <strong>{pendingAction.label}</strong>
          </div>
          <div className="chat-config-actions">
            <button
              type="button"
              className="button-primary"
              disabled={disabled}
              onClick={pendingAction.onConfirm}
            >
              <Play size={14} aria-hidden="true" />
              <span>{pendingAction.confirmLabel || 'Xác nhận & thực hiện'}</span>
            </button>
            <button
              type="button"
              className="button-secondary"
              disabled={disabled}
              onClick={pendingAction.onCancel}
            >
              <X size={14} aria-hidden="true" />
              <span>Huỷ</span>
            </button>
          </div>
        </div>
      )}

      {draft && (
        <div className="chat-config-body">
          <div className="chat-config-head">
            <div>
              <span className={`chat-config-badge ${draft.needsClarification.length > 0 ? 'is-missing' : draft.hasMismatch ? 'is-limit' : 'is-ready'}`}>
                {draft.needsClarification.length > 0
                  ? 'Cần chọn mẫu'
                  : draft.hasMismatch
                    ? 'Mẫu có cấu trúc cố định'
                    : 'Sẵn sàng tạo đề'}
              </span>
              <h4>{selectedFormat ? selectedFormat.displayName : 'Cấu hình đề từ trao đổi'}</h4>
            </div>
            {onDismiss && (
              <button
                type="button"
                className="chat-config-close"
                aria-label="Ẩn bảng cấu hình"
                title="Ẩn bảng cấu hình"
                onClick={onDismiss}
              >
                <X size={14} aria-hidden="true" />
              </button>
            )}
          </div>

          {draft.limitations.length > 0 && (
            <div className="chat-config-notice is-warning" role="status">
              <AlertTriangle size={14} aria-hidden="true" />
              <div>
                {draft.limitations.map((text, idx) => (
                  <p key={idx}>{text}</p>
                ))}
              </div>
            </div>
          )}

          {draft.needsClarification.length > 0 && (
            <div className="chat-config-notice is-info">
              <HelpCircle size={14} aria-hidden="true" />
              <div>
                {draft.needsClarification.map((text, idx) => (
                  <p key={idx}>{text}</p>
                ))}
              </div>
            </div>
          )}

          {draft.applied.length > 0 && (
            <ul className="chat-config-applied" aria-label="Đã áp dụng">
              {draft.applied.map((item, idx) => (
                <li key={idx}>
                  <CheckCircle2 size={13} aria-hidden="true" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )}

          <div className="chat-config-fields">
            <label className="chat-config-field">
              <span>Mẫu đề / Môn học</span>
              <select
                aria-label="Chọn mẫu đề"
                value={draft.formatId || ''}
                disabled={disabled || !availableFormats.length}
                onChange={e => onChange?.({ formatId: e.target.value || undefined })}
              >
                <option value="">-- Chọn mẫu đề --</option>
                {availableFormats.map(format => (
                  <option key={format.id} value={format.id}>
                    {format.displayName} ({format.totalQuestions} câu · {format.durationMinutes} phút)
                  </option>
                ))}
              </select>
            </label>

            {(!selectedFormat || selectedFormat.examType !== 'DGNL_DHQG') && (
              <>
                <label className="chat-config-field">
                  <span>Chủ đề trọng tâm</span>
                  <input
                    type="text"
                    value={draft.topic}
                    disabled={disabled}
                    placeholder="Ví dụ: Hàm số, Mũ - Logarit, Tích phân..."
                    onChange={e => onChange?.({ topic: e.target.value })}
                  />
                </label>

                <label className="chat-config-field">
                  <span>Mức độ / phân bố câu hỏi</span>
                  <input
                    type="text"
                    value={draft.difficulty}
                    disabled={disabled}
                    placeholder="Ví dụ: Tăng câu vận dụng, giữ cấu trúc chuẩn..."
                    onChange={e => onChange?.({ difficulty: e.target.value })}
                  />
                </label>
              </>
            )}
          </div>

          <div className="chat-config-actions">
            {selectedFormat && onGenerate && (
              <button
                type="button"
                className="button-primary"
                disabled={disabled}
                onClick={onGenerate}
              >
                <Play size={14} aria-hidden="true" />
                <span>{draft.hasMismatch ? `Dùng mẫu này (${selectedFormat.totalQuestions} câu · ${selectedFormat.durationMinutes}p)` : 'Tạo đề ngay'}</span>
              </button>
            )}
            {onOpenModal && (
              <button
                type="button"
                className="button-secondary"
                disabled={disabled}
                onClick={onOpenModal}
              >
                <Settings2 size={14} aria-hidden="true" />
                <span>Mở cấu hình</span>
              </button>
            )}
          </div>
        </div>
      )}
    </section>
  );
};
