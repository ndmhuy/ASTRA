import React, { useEffect, useRef, useState } from 'react';
import { LoaderCircle, X } from 'lucide-react';
import type { QuestionItem } from '../types/exam';
import { MathRenderer } from './MathRenderer';

interface Props {
  question: QuestionItem;
  onSave: (question: QuestionItem) => Promise<void>;
  onRegenerate: (instruction: string) => Promise<void>;
  onClose: () => void;
}

export const QuestionEditor: React.FC<Props> = ({ question, onSave, onRegenerate, onClose }) => {
  const [draft, setDraft] = useState(() => structuredClone(question));
  const [instruction, setInstruction] = useState('');
  const [busyAction, setBusyAction] = useState<'save' | 'regen' | null>(null);
  const [error, setError] = useState('');
  const dialogRef = useRef<HTMLElement>(null);
  const draftRef = useRef(draft);
  const busy = busyAction !== null;

  useEffect(() => {
    draftRef.current = draft;
  }, [draft]);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const stemInput = dialogRef.current?.querySelector<HTMLTextAreaElement>('textarea[aria-label="Đề bài"]');
    stemInput?.focus();
    return () => {
      previous?.focus();
    };
  }, []);

  useEffect(() => {
    const dialog = dialogRef.current;
    const controls = () => Array.from(
      dialog?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled)') || []
    );
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !busy) {
        onClose();
        return;
      }
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter' && !busy) {
        event.preventDefault();
        setBusyAction('save');
        setError('');
        void onSave(draftRef.current)
          .catch(err => setError(err instanceof Error ? err.message : 'Không lưu được câu hỏi'))
          .finally(() => setBusyAction(null));
        return;
      }
      if (event.key === 'Tab' && dialog) {
        const items = controls();
        const first = items[0];
        const last = items[items.length - 1];
        if (!first || !last) return;
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => {
      window.removeEventListener('keydown', handleKey);
    };
  }, [busy, onClose, onSave]);

  const action = async (kind: 'save' | 'regen', operation: () => Promise<void>) => {
    setBusyAction(kind);
    setError('');
    try {
      await operation();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không lưu được câu hỏi');
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <div
      className="integration-editor-backdrop"
      onClick={() => { if (!busy) onClose(); }}
    >
      <section
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-title"
        className="integration-editor"
        onClick={event => event.stopPropagation()}
      >
        <header className="editor-modal-header">
          <div className="editor-modal-heading">
            <h2 id="edit-title">Sửa câu {question.stableId || question.id}</h2>
            <p className="editor-modal-subtitle">Lưu hoặc tạo lại sẽ hủy phê duyệt cũ.</p>
          </div>
          <button
            type="button"
            className="modal-icon-close"
            aria-label="Đóng cửa sổ sửa câu hỏi"
            disabled={busy}
            onClick={onClose}
          >
            <X size={17} aria-hidden="true" />
          </button>
        </header>

        <div className="editor-modal-body">
          {error && <div className="editor-error-box" role="alert">{error}</div>}

          <div className="editor-section">
            <label className="editor-field">
              <span className="editor-field-label">Đề bài</span>
              <textarea
                aria-label="Đề bài"
                rows={3}
                value={draft.stem}
                onChange={e => setDraft({ ...draft, stem: e.target.value })}
              />
            </label>

            {draft.stem.includes('$') && (
              <div className="editor-math-preview" aria-label="Xem trước công thức toán">
                <span className="editor-preview-label">Xem trước hiển thị</span>
                <div className="editor-preview-content">
                  <MathRenderer content={draft.stem} />
                </div>
              </div>
            )}

            {(!draft.questionType || draft.questionType === 'mcq') && (
              <>
                <div className="editor-choices-grid">
                  {(['A', 'B', 'C', 'D'] as const).map(key => (
                    <label key={key} className="editor-field">
                      <span className="editor-field-label">Phương án {key}</span>
                      <textarea
                        rows={2}
                        value={draft.choices[key]}
                        onChange={e => setDraft({ ...draft, choices: { ...draft.choices, [key]: e.target.value } })}
                      />
                    </label>
                  ))}
                </div>
                <label className="editor-field editor-field-compact">
                  <span className="editor-field-label">Đáp án</span>
                  <select value={draft.key} onChange={e => setDraft({ ...draft, key: e.target.value })}>
                    {['A', 'B', 'C', 'D'].map(key => <option key={key}>{key}</option>)}
                  </select>
                </label>
              </>
            )}

            {draft.questionType === 'true_false' && (
              <div className="editor-tf-grid">
                {draft.statements?.map((statement, index) => (
                  <fieldset key={index} className="editor-tf-card">
                    <legend>Ý {'abcd'[index]}</legend>
                    <textarea
                      aria-label={`Nội dung ý ${'abcd'[index]}`}
                      rows={2}
                      value={statement.text}
                      onChange={e => setDraft({
                        ...draft,
                        statements: draft.statements!.map((s, i) => i === index ? { ...s, text: e.target.value } : s),
                      })}
                    />
                    <label className="editor-tf-toggle">
                      <input
                        type="checkbox"
                        checked={statement.answer}
                        onChange={e => setDraft({
                          ...draft,
                          statements: draft.statements!.map((s, i) => i === index ? { ...s, answer: e.target.checked } : s),
                        })}
                      />
                      <span>Đúng</span>
                    </label>
                  </fieldset>
                ))}
              </div>
            )}

            {draft.questionType === 'short_answer' && (
              <label className="editor-field editor-field-compact">
                <span className="editor-field-label">Đáp án số</span>
                <input value={draft.key} onChange={e => setDraft({ ...draft, key: e.target.value })} />
              </label>
            )}

            <label className="editor-field">
              <span className="editor-field-label">Lời giải</span>
              <textarea
                rows={3}
                value={draft.explanation}
                onChange={e => setDraft({ ...draft, explanation: e.target.value })}
              />
            </label>
          </div>

          <div className="editor-ai-box">
            <label className="editor-field">
              <span className="editor-field-label">Yêu cầu tạo lại</span>
              <textarea
                rows={2}
                placeholder="Ví dụ: Đổi số liệu mới, giữ nguyên dạng toán..."
                value={instruction}
                onChange={e => setInstruction(e.target.value)}
              />
            </label>
          </div>
        </div>

        <footer className="editor-modal-footer">
          <button type="button" className="button-secondary" disabled={busy} onClick={onClose}>Đóng</button>
          <button
            type="button"
            className="button-secondary"
            disabled={busy}
            onClick={() => { void action('regen', () => onRegenerate(instruction)); }}
          >
            {busyAction === 'regen' && <LoaderCircle className="exam-status-spinner" size={14} aria-hidden="true" />}
            Tạo lại và giải kiểm tra
          </button>
          <button
            type="button"
            className="button-primary"
            disabled={busy}
            title="Lưu thay đổi (Ctrl+Enter)"
            onClick={() => { void action('save', () => onSave(draft)); }}
          >
            {busyAction === 'save' && <LoaderCircle className="exam-status-spinner" size={14} aria-hidden="true" />}
            Lưu thay đổi
          </button>
        </footer>
      </section>
    </div>
  );
};
