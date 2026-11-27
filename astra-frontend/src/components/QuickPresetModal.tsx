import { getActiveUploads, subscribeUploads } from '../services/inputDocuments';
import React, { useSyncExternalStore, useEffect, useRef, useState } from 'react';
import { ChevronDown, ChevronUp, X } from 'lucide-react';
import type { ExamFormat, ExamRequestParams } from '../types/exam';
import { presetParams } from '../agent/intake';
import { getBackendHealth, getExamFormats, type BackendHealth } from '../services/examService';

import { DocumentAttachments } from './DocumentAttachments';
import type { InputDocument, InputDocumentsUpdate } from '../services/inputDocuments';

interface Props {
  documents: InputDocument[];
  onDocumentsChange: (documents: InputDocumentsUpdate) => void;
  onDialogMount?: (node: HTMLDivElement | null) => void;
  title?: string;
  onStart: (params: ExamRequestParams) => void;
  onClose: () => void;
  agentSelection?: { formats: ExamFormat[]; id: string; expanded: boolean; summary?: string };
  onManualSelect?: () => void;
}

const THPT_SECTION_TITLES: Record<string, string> = {
  P1: 'Phần I · Trắc nghiệm nhiều lựa chọn',
  P2: 'Phần II · Trắc nghiệm đúng/sai',
  P3: 'Phần III · Trả lời ngắn',
};

function sectionTitle(section: ExamFormat['sections'][number]): string {
  return section.title || THPT_SECTION_TITLES[section.id] || section.id;
}

function sectionTypeLabel(type: string): string {
  if (type === 'mcq') return 'nhiều lựa chọn';
  if (type === 'true_false') return 'đúng/sai';
  if (type === 'short_answer') return 'trả lời ngắn';
  if (type === 'written') return 'tự luận';
  return type;
}

function formatSummary(format: ExamFormat): string {
  if (format.examType === 'DGNL_DHQG') {
    return 'Tổng hợp 5 lĩnh vực · Cấu trúc chuẩn ĐHQG-HCM';
  }
  return `Môn ${format.subjects[0]} · Lớp ${format.grades[0]}`;
}

export const QuickPresetModal: React.FC<Props> = ({ documents, onDocumentsChange, onStart, onClose, onDialogMount, agentSelection, onManualSelect, title = 'Tạo đề từ mẫu' }) => {
  const [formats, setFormats] = useState<ExamFormat[]>([]);
  const [manualGroup, setMasterGroup] = useState<'thpt' | 'dgnl'>('thpt');
  const [pickerOpen, setThptPickerOpen] = useState(false);
  const [selectedThptId, setSelectedThptId] = useState('thpt-math');
  const [expandedOverrides, setExpandedGroup] = useState<{ thpt?: boolean; dgnl?: boolean }>({
    thpt: undefined,
    dgnl: undefined,
  });
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [error, setError] = useState('');
  const [localUploading, setUploading] = useState(false);
  const activeUploads = useSyncExternalStore(subscribeUploads, getActiveUploads);
  const uploading = localUploading || activeUploads > 0;
  const [catalogAttempt, setCatalogAttempt] = useState(0);
  const modalRef = useRef<HTMLDivElement>(null);

  const catalog = agentSelection?.formats ?? formats;
  const agentFormat = agentSelection && catalog.find(format => format.id === agentSelection.id);
  const masterGroup = agentFormat ? (agentFormat.examType === 'DGNL_DHQG' ? 'dgnl' : 'thpt') : manualGroup;
  const thptPickerOpen = agentFormat ? masterGroup === 'thpt' : pickerOpen;
  const expandedGroup = {
    thpt: expandedOverrides.thpt ?? (masterGroup === 'thpt' && !!agentSelection?.expanded),
    dgnl: expandedOverrides.dgnl ?? (masterGroup === 'dgnl' && !!agentSelection?.expanded),
  };
  const thptFormats = catalog.filter(format => format.examType === 'THPT_STANDARD');
  const dgnlFormat = catalog.find(format => format.examType === 'DGNL_DHQG');
  const selectedThpt =
    thptFormats.find(format => format.id === (agentSelection?.id ?? selectedThptId)) ||
    thptFormats.find(format => format.available) ||
    thptFormats[0];
  const selected = masterGroup === 'thpt' ? selectedThpt : dgnlFormat;

  const toggleGroupExpand = (group: 'thpt' | 'dgnl') => {
    setExpandedGroup(prev => ({ ...prev, [group]: !expandedGroup[group] }));
  };
  const selectThptMaster = () => {
    setFormats(catalog);
    onManualSelect?.();
    setMasterGroup('thpt');
    setThptPickerOpen(true);
  };
  const selectDgnlMaster = () => {
    setFormats(catalog);
    onManualSelect?.();
    setMasterGroup('dgnl');
    setThptPickerOpen(false);
  };

  useEffect(() => {
    let active = true;
    void getBackendHealth().then(info => { if (active && info) setHealth(info); });
    if (agentSelection) return () => { active = false; };
    getExamFormats()
      .then(items => {
        if (!active) return;
        setFormats(items);
        const firstThpt = items.find(item => item.examType === 'THPT_STANDARD' && item.available);
        const firstDgnl = items.find(item => item.examType === 'DGNL_DHQG' && item.available);
        if (firstThpt) {
          setSelectedThptId(firstThpt.id);
          setMasterGroup('thpt');
        } else if (firstDgnl) {
          setMasterGroup('dgnl');
        }
      })
      .catch(err => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Không tải được danh sách mẫu đề từ máy chủ.');
        }
      });
    return () => { active = false; };
  }, [agentSelection, catalogAttempt]);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const modal = modalRef.current;
    const controls = () => Array.from(modal?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not([type="file"]):not(:disabled), select:not(:disabled)') || []);
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

  const retryCatalog = () => {
    setError('');
    setCatalogAttempt(attempt => attempt + 1);
  };

  const start = () => {
    if (!selected?.available || uploading) return;
    onStart({ ...presetParams(selected), uploadedFiles: documents.map(document => document.id) });
  };

  const handleOptionKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && selected?.available && !error) {
      event.preventDefault();
      start();
    }
  };

  return (
    <div className="preset-modal-backdrop" onClick={onClose}>
      <div
        ref={node => {
          modalRef.current = node;
          onDialogMount?.(node);
        }}
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
          <div className="preset-error-box">
            <p role="alert">{error}</p>
            <button type="button" className="button-secondary" onClick={retryCatalog}>
              Tải lại danh sách mẫu đề
            </button>
          </div>
        )}
        {!error && !catalog.length && (
          <div className="preset-loading-wrap">
            <p role="status" className="preset-loading-text">Đang tải danh sách mẫu đề…</p>
            <div className="preset-skeleton-card" aria-hidden="true" />
            <div className="preset-skeleton-card" aria-hidden="true" />
          </div>
        )}

        <div className="preset-options-list">
          {thptFormats.length > 0 && selectedThpt && (
            <div className={`preset-option-card ${masterGroup === 'thpt' ? 'is-selected' : ''}`}>
              <div className="preset-option-top">
                <label className="preset-option-label">
                  <input
                    type="radio"
                    name="preset-master"
                    checked={masterGroup === 'thpt'}
                    onChange={selectThptMaster}
                    onClick={selectThptMaster}
                    onKeyDown={handleOptionKeyDown}
                  />
                  <span className="preset-option-copy">
                    <strong>Đề thi THPT Quốc gia</strong>
                    <small>
                      {thptPickerOpen
                        ? `${selectedThpt.subjects[0]} · ${selectedThpt.totalQuestions} câu · ${selectedThpt.durationMinutes} phút`
                        : `${thptFormats.length} môn chuẩn Bộ GD&ĐT · Đang chọn: ${selectedThpt.subjects[0]}`}
                    </small>
                  </span>
                </label>
                <button
                  type="button"
                  className="preset-expand-btn"
                  aria-expanded={thptPickerOpen}
                  onClick={() => {
                    if (masterGroup !== 'thpt') selectThptMaster();
                    else setThptPickerOpen(prev => !prev);
                  }}
                >
                  {thptPickerOpen ? 'Ẩn môn' : `Chọn môn (${thptFormats.length})`}
                </button>
              </div>

              {masterGroup === 'thpt' && thptPickerOpen && (
                <div className="preset-subject-panel">
                  <div className="preset-subject-picker" role="group" aria-label="Chọn môn thi THPT Quốc gia">
                    {thptFormats.map(format => {
                      const active = selectedThpt.id === format.id;
                      return (
                        <button
                          key={format.id}
                          type="button"
                          aria-pressed={active}
                          disabled={!format.available}
                          className={`preset-subject-pill ${active ? 'is-active' : ''}`}
                          onClick={() => { setFormats(catalog); setMasterGroup('thpt'); setThptPickerOpen(true); setSelectedThptId(format.id); onManualSelect?.(); }}
                        >
                          {format.subjects[0]}
                        </button>
                      );
                    })}
                  </div>
                  <div className="preset-subject-meta">
                    <span>
                      {selectedThpt.displayName} · {selectedThpt.totalQuestions} câu · {selectedThpt.durationMinutes} phút
                    </span>
                    <button
                      type="button"
                      className="preset-expand-btn"
                      aria-expanded={expandedGroup.thpt}
                      onClick={() => toggleGroupExpand('thpt')}
                    >
                      <span>{expandedGroup.thpt ? 'Thu gọn' : 'Xem thêm'}</span>
                      {expandedGroup.thpt ? <ChevronUp size={14} aria-hidden="true" /> : <ChevronDown size={14} aria-hidden="true" />}
                    </button>
                  </div>
                  {expandedGroup.thpt && (
                    <div className="preset-details">
                      <p className="preset-details-summary">{formatSummary(selectedThpt)}</p>
                      <ul className="preset-section-list">
                        {selectedThpt.sections.map(section => (
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
              )}
            </div>
          )}

          {dgnlFormat && (
            <div className={`preset-option-card ${masterGroup === 'dgnl' ? 'is-selected' : ''}`}>
              <div className="preset-option-top">
                <label className="preset-option-label">
                  <input
                    type="radio"
                    name="preset-master"
                    checked={masterGroup === 'dgnl'}
                    disabled={!dgnlFormat.available}
                    onChange={selectDgnlMaster}
                    onClick={selectDgnlMaster}
                    onKeyDown={handleOptionKeyDown}
                  />
                  <span className="preset-option-copy">
                    <strong>{dgnlFormat.displayName}</strong>
                    <small>{dgnlFormat.totalQuestions} câu · {dgnlFormat.durationMinutes} phút</small>
                  </span>
                </label>
                <button
                  type="button"
                  className="preset-expand-btn"
                  aria-expanded={expandedGroup.dgnl}
                  onClick={() => toggleGroupExpand('dgnl')}
                >
                  <span>{expandedGroup.dgnl ? 'Thu gọn' : 'Xem thêm'}</span>
                  {expandedGroup.dgnl ? <ChevronUp size={14} aria-hidden="true" /> : <ChevronDown size={14} aria-hidden="true" />}
                </button>
              </div>
              {expandedGroup.dgnl && (
                <div className="preset-details">
                  <p className="preset-details-summary">{formatSummary(dgnlFormat)}</p>
                  <ul className="preset-section-list">
                    {dgnlFormat.sections.map(section => (
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
          )}
        </div>

      <DocumentAttachments documents={documents} onChange={onDocumentsChange} onBusyChange={setUploading} />
      {agentSelection?.summary && <p className="preset-details-summary">{agentSelection.summary}</p>}
      <div className="preset-modal-actions">
        <button type="button" className="button-secondary" onClick={onClose}>Huỷ</button>
        <button type="button" className="button-primary" disabled={!selected?.available || !!error || uploading} onClick={start}>Tạo đề thi</button>
      </div>
      </div>
    </div>
  );
};
