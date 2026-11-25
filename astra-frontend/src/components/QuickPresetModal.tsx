import React, { useEffect, useRef, useState } from 'react';
import { ChevronDown, ChevronUp, X } from 'lucide-react';
import type { ExamFormat, ExamRequestParams } from '../types/exam';
import { getBackendHealth, getExamFormats, type BackendHealth } from '../services/examService';

interface Props { title?: string; onStart: (params: ExamRequestParams) => void; onClose: () => void; }

const THPT_SECTION_TITLES: Record<string, string> = {
  P1: 'Phần I · Trắc nghiệm nhiều lựa chọn',
  P2: 'Phần II · Trắc nghiệm đúng/sai',
  P3: 'Phần III · Trả lời ngắn',
};

function sectionTitle(section: ExamFormat['sections'][number]): string {
  return THPT_SECTION_TITLES[section.id] || section.title || section.id;
}

function sectionTypeLabel(type: string): string {
  if (type === 'mcq') return 'nhiều lựa chọn';
  if (type === 'true_false') return 'đúng/sai';
  if (type === 'short_answer') return 'trả lời ngắn';
  return type;
}

function formatSummary(format: ExamFormat): string {
  if (format.examType === 'DGNL_DHQG') {
    return 'Tổng hợp 5 lĩnh vực · Cấu trúc chuẩn ĐHQG-HCM';
  }
  return `Môn ${format.subjects[0]} · Lớp ${format.grades[0]}`;
}

export const QuickPresetModal: React.FC<Props> = ({ onStart, onClose, title = 'Tạo đề từ mẫu' }) => {
  const [formats, setFormats] = useState<ExamFormat[]>([]);
  const [selectedId, setSelectedId] = useState('thpt-math');
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({});
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [error, setError] = useState('');
  const modalRef = useRef<HTMLDivElement>(null);
  const selected = formats.find(format => format.id === selectedId);
  const toggleExpand = (id: string) => {
    setExpandedIds(prev => ({ ...prev, [id]: !prev[id] }));
  };

  useEffect(() => {
    let active = true;
    void getBackendHealth().then(info => { if (active && info) setHealth(info); });
    getExamFormats().then(items => { if (active) { setFormats(items); setSelectedId(items.find(item => item.available)?.id || ''); } })
      .catch(error => { if (active) setError(error instanceof Error ? error.message : 'Không tải được danh sách mẫu đề từ máy chủ.'); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const modal = modalRef.current;
    const controls = () => Array.from(modal?.querySelectorAll<HTMLElement>('button:not(:disabled), input, select') || []);
    controls()[0]?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'Tab') {
        const items = controls(); const first = items[0]; const last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    modal?.addEventListener('keydown', handleKey);
    return () => { modal?.removeEventListener('keydown', handleKey); previous?.focus(); };
  }, [onClose]);

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
      prompt: `Tạo đề ${selected.displayName}`,
      uploadedFiles: [],
    });
  };

  return (
    <div className="preset-modal-backdrop" onClick={onClose}>
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="preset-title"
        className="preset-modal-card"
        onClick={event => event.stopPropagation()}
      >
      <div className="preset-modal-header">
        <div className="preset-modal-title-group">
          <h2 id="preset-title">{title}</h2>
          {health && !error && (
            <span
              className={`preset-mode-pill ${health.demoMode ? 'is-demo' : 'is-ai'}`}
              title={health.demoMode ? 'Tạo đề nhanh từ bộ dữ liệu cài sẵn, không gọi AI' : undefined}
            >
              {health.demoMode ? 'Không tốn phí AI' : health.providerConfigured ? 'Dùng AI thật' : 'Chưa kết nối AI'}
            </span>
          )}
        </div>
        <button
          type="button"
          className="modal-icon-close"
          aria-label="Đóng hộp thoại mẫu đề"
          onClick={onClose}
        >
          <X size={17} aria-hidden="true" />
        </button>
      </div>

      {error && (
        <div role="alert" className="preset-error-box">
          <p>{error}</p>
        </div>
      )}
      {!error && !formats.length && (
        <div className="preset-loading-wrap">
          <p role="status" className="preset-loading-text">Đang tải danh sách mẫu đề…</p>
          <div className="preset-skeleton-card" aria-hidden="true" />
          <div className="preset-skeleton-card" aria-hidden="true" />
        </div>
      )}

      <div className="preset-options-list">
        {formats.map(format => {
          const isSelected = selectedId === format.id;
          const isExpanded = Boolean(expandedIds[format.id]);
          return (
            <div key={format.id} className={`preset-option-card ${isSelected ? 'is-selected' : ''}`}>
              <div className="preset-option-top">
                <label className="preset-option-label">
                  <input
                    type="radio"
                    name="preset"
                    checked={isSelected}
                    disabled={!format.available}
                    onChange={() => setSelectedId(format.id)}
                  />
                  <span className="preset-option-copy">
                    <strong>{format.displayName}</strong>
                    <small>{format.totalQuestions} câu · {format.durationMinutes} phút</small>
                  </span>
                </label>
                <button
                  type="button"
                  className="preset-expand-btn"
                  aria-expanded={isExpanded}
                  onClick={() => toggleExpand(format.id)}
                >
                  <span>{isExpanded ? 'Thu gọn' : 'Xem thêm'}</span>
                  {isExpanded ? <ChevronUp size={14} aria-hidden="true" /> : <ChevronDown size={14} aria-hidden="true" />}
                </button>
              </div>
              {isExpanded && (
                <div className="preset-details">
                  <p className="preset-details-summary">{formatSummary(format)}</p>
                  <ul className="preset-section-list">
                    {format.sections.map(section => (
                      <li key={section.id}>
                        <span>{sectionTitle(section)}</span>
                        <span className="preset-section-meta">
                          {section.count} câu ({sectionTypeLabel(section.type)})
                          {section.questionRange ? ` · Câu ${section.questionRange[0]}–${section.questionRange[1]}` : ''}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="preset-modal-actions">
        <button type="button" className="button-secondary" onClick={onClose}>Huỷ</button>
        <button type="button" className="button-primary" disabled={!selected?.available || !!error} onClick={start}>Tạo đề thi</button>
      </div>
      </div>
    </div>
  );
};
