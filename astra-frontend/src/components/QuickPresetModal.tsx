import React, { useEffect, useRef, useState } from 'react';
import { Clock, FileText, Layers, Sparkles, X } from 'lucide-react';
import type { ExamFormat, ExamRequestParams } from '../types/exam';
import { getExamFormats } from '../services/examService';
import { formatUserError } from '../utils/userMessages';

interface Props {
  title?: string;
  onStart: (params: ExamRequestParams) => void;
  onClose: () => void;
  selectedId?: string;
  prompt?: string;
  onPromptChange?: (value: string) => void;
  onStateChange?: (state: { status: 'loading' | 'ready' | 'error'; formats: ExamFormat[]; selectedId: string; error?: string }) => void;
}

const VACT_FORMAT_OPTION: ExamFormat = {
  id: 'vact-dgnl',
  version: '1',
  displayName: 'Tạo đề ĐGNL (V-ACT)',
  examType: 'DGNL_DHQG',
  subjects: ['Tổng hợp'],
  grades: [12],
  durationMinutes: 150,
  totalQuestions: 120,
  totalScore: 1200,
  available: false,
  exportFormats: ['tex', 'json', 'pdf'],
  sections: [
    { id: 'P1', type: 'mcq', count: 60, instructions: 'Sử dụng ngôn ngữ (Tiếng Việt & Tiếng Anh)' },
    { id: 'P2', type: 'mcq', count: 30, instructions: 'Toán học' },
    { id: 'P3', type: 'mcq', count: 30, instructions: 'Tư duy khoa học (Logic, Phân tích số liệu & Suy luận)' },
  ],
};

let cachedFormats: ExamFormat[] | null = null;

function mergeWithVactOption(items: ExamFormat[]): ExamFormat[] {
  const hasVact = items.some(item => item.examType === 'DGNL_DHQG' || item.id.toLowerCase().includes('vact'));
  return hasVact ? items : [...items, VACT_FORMAT_OPTION];
}

function formatSectionLabel(section: ExamFormat['sections'][number], format: ExamFormat): string {
  if (format.examType === 'DGNL_DHQG' && section.instructions) {
    return `${section.id}: ${section.count} câu · ${section.instructions}`;
  }
  const typeLabel = section.type === 'mcq'
    ? 'câu nhiều lựa chọn'
    : section.type === 'true_false'
      ? 'câu đúng/sai'
      : 'câu trả lời ngắn';
  return `${section.id}: ${section.count} ${typeLabel}`;
}

export const QuickPresetModal: React.FC<Props> = ({
  onStart,
  onClose,
  selectedId: requestedId,
  prompt,
  onPromptChange,
  onStateChange,
  title = 'Tạo đề từ mẫu',
}) => {
  const [formats, setFormats] = useState<ExamFormat[]>(() => cachedFormats || []);
  const [localSelectedId, setSelectedId] = useState(() => cachedFormats?.find(item => item.available)?.id || 'thpt-math');
  const selectedId = requestedId || localSelectedId;
  const [error, setError] = useState('');
  const modalRef = useRef<HTMLDivElement>(null);
  const selected = formats.find(format => format.id === selectedId);
  const promptValue = prompt || '';

  useEffect(() => {
    let active = true;
    if (!cachedFormats) {
      onStateChange?.({ status: 'loading', formats: [], selectedId: '' });
    }
    getExamFormats().then(items => {
      if (!active) return;
      const merged = mergeWithVactOption(items);
      cachedFormats = merged;
      const nextId = merged.find(item => item.available)?.id || merged[0]?.id || '';
      setFormats(merged);
      setSelectedId(current => merged.some(item => item.id === current) ? current : nextId);
      onStateChange?.({ status: 'ready', formats: merged, selectedId: nextId });
    }).catch(reason => {
      if (!active) return;
      const message = formatUserError(reason);
      setError(message);
      onStateChange?.({ status: 'error', formats: [], selectedId: '', error: message });
    });
    return () => { active = false; };
  }, [onStateChange]);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const modal = modalRef.current;
    const controls = () => Array.from(
      modal?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled)') || []
    );
    modal?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'Tab') {
        const items = controls();
        const first = items[0];
        const last = items[items.length - 1];
        if (!first) return;
        if (event.shiftKey && (document.activeElement === first || document.activeElement === modal)) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    modal?.addEventListener('keydown', handleKey);
    return () => { modal?.removeEventListener('keydown', handleKey); previous?.focus(); };
  }, [onClose]);

  const selectFormat = (formatId: string) => {
    setSelectedId(formatId);
    onStateChange?.({ status: 'ready', formats, selectedId: formatId });
  };

  const start = () => {
    if (!selected?.available) return;
    onStart({
      formatId: selected.id,
      formatVersion: selected.version,
      subject: selected.subjects[0],
      grade: selected.grades[0],
      examType: selected.examType,
      durationMinutes: selected.durationMinutes,
      itemCount: selected.totalQuestions,
      prompt: promptValue.trim() || `Tạo đề ${selected.displayName}`,
      uploadedFiles: [],
    });
  };

  return (
    <div
      className="setup-modal-backdrop"
      onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}
    >
      <div
        ref={modalRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="preset-title"
        className="setup-modal"
      >
        <header className="setup-modal-header">
          <div>
            <span className="setup-modal-eyebrow">CẤU HÌNH ĐỀ THI</span>
            <h2 id="preset-title">{title}</h2>
            <p className="setup-modal-subtitle">
              Chọn khung đề chuẩn và ghi chú trọng tâm kiến thức trước khi khởi tạo.
            </p>
          </div>
          <button
            type="button"
            className="setup-modal-close"
            onClick={onClose}
            aria-label="Đóng hộp thiết lập"
            title="Đóng"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <div className="setup-modal-body">
          <section className="setup-section" aria-label="Chọn định dạng đề thi">
            <div className="setup-section-head">
              <span className="setup-section-title">1. Định dạng đề thi</span>
              <span className="setup-section-hint">Số câu & thời lượng theo chuẩn kỳ thi</span>
            </div>

            {error && <p className="setup-alert is-error" role="alert">{error}</p>}
            {!error && !formats.length && (
              <p className="setup-status" role="status">Đang tải danh mục định dạng từ máy chủ…</p>
            )}

            <div className="setup-format-list">
              {formats.map(format => {
                const isSelected = selectedId === format.id;
                return (
                  <label
                    key={format.id}
                    className={`setup-format-card ${isSelected ? 'is-selected' : ''} ${!format.available ? 'is-upcoming' : ''}`}
                  >
                    <div className="setup-format-top">
                      <span className="setup-format-radio-wrap">
                        <input
                          type="radio"
                          name="preset"
                          checked={isSelected}
                          onChange={() => selectFormat(format.id)}
                        />
                        <span className="setup-format-name">{format.displayName}</span>
                      </span>
                      <span className={`setup-format-badge ${format.available ? 'is-ready' : 'is-pending'}`}>
                        {format.available ? 'Sẵn sàng' : 'Đang tích hợp'}
                      </span>
                    </div>

                    <div className="setup-format-meta">
                      <span><FileText size={13} aria-hidden="true" />{format.totalQuestions} câu</span>
                      <span><Clock size={13} aria-hidden="true" />{format.durationMinutes} phút</span>
                      <span><Layers size={13} aria-hidden="true" />Thang {format.totalScore} điểm</span>
                    </div>

                    <ul className="setup-format-sections">
                      {format.sections.map(section => (
                        <li key={section.id}>{formatSectionLabel(section, format)}</li>
                      ))}
                    </ul>
                  </label>
                );
              })}
            </div>

            {selected && (
              <div className={`setup-summary-bar ${!selected.available ? 'is-notice' : ''}`}>
                {selected.available ? (
                  <p>
                    <strong>Môn {selected.subjects[0]} · Lớp {selected.grades[0]}.</strong>{' '}
                    Số câu và thời gian khóa theo định dạng đã chọn; xuất hỗ trợ {selected.exportFormats.map(f => f.toUpperCase()).join(', ')}.
                  </p>
                ) : (
                  <p>
                    <strong>{selected.displayName}</strong> đã có khung cấu trúc 120 câu (150 phút) trên giao diện và đang chờ nối hợp đồng sinh đề ở máy chủ. Hiện tại hãy chọn <strong>Toán THPT</strong> để tạo đề trực tiếp.
                  </p>
                )}
              </div>
            )}
          </section>

          <section className="setup-section">
            <label className="setup-prompt-field">
              <span className="setup-section-head">
                <span className="setup-section-title">2. Yêu cầu bổ sung</span>
                <span className="setup-char-count">{promptValue.length} / 1000</span>
              </span>
              <textarea
                aria-label="Yêu cầu bổ sung"
                value={promptValue}
                maxLength={1000}
                rows={3}
                placeholder="Ví dụ: Tập trung chương Hàm số và Tích phân, tăng câu vận dụng thực tế, tránh lặp dạng đồ thị..."
                onChange={event => onPromptChange?.(event.target.value)}
              />
            </label>
          </section>
        </div>

        <footer className="setup-modal-footer">
          <p className="setup-footer-note">
            Tệp đính kèm và các môn khác chưa khả dụng trong luồng hiện tại.
          </p>
          <div className="setup-footer-actions">
            <button type="button" className="button-secondary" onClick={onClose}>Huỷ</button>
            <button
              type="button"
              className="button-primary"
              disabled={!selected?.available || !!error}
              onClick={start}
            >
              <Sparkles size={15} aria-hidden="true" />
              Tạo đề thi
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
};

