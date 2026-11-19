import React, { useEffect, useRef, useState } from 'react';
import type { ExamFormat, ExamRequestParams } from '../types/exam';
import { getExamFormats } from '../services/examService';

interface Props {
  title?: string;
  onStart: (params: ExamRequestParams) => void;
  onClose: () => void;
  selectedId?: string;
  prompt?: string;
  onPromptChange?: (value: string) => void;
  onStateChange?: (state: { status: 'loading' | 'ready' | 'error'; formats: ExamFormat[]; selectedId: string; error?: string }) => void;
}

export const QuickPresetModal: React.FC<Props> = ({ onStart, onClose, selectedId: requestedId, prompt, onPromptChange, onStateChange, title = 'Tạo đề từ mẫu' }) => {
  const [formats, setFormats] = useState<ExamFormat[]>([]);
  const [localSelectedId, setSelectedId] = useState('thpt-math');
  const selectedId = requestedId || localSelectedId;
  const [error, setError] = useState('');
  const modalRef = useRef<HTMLDivElement>(null);
  const selected = formats.find(format => format.id === selectedId);
  useEffect(() => {
    let active = true;
    onStateChange?.({ status: 'loading', formats: [], selectedId: '' });
    getExamFormats().then(items => {
      if (!active) return;
      const nextId = items.find(item => item.available)?.id || '';
      setFormats(items); setSelectedId(nextId);
      onStateChange?.({ status: 'ready', formats: items, selectedId: nextId });
    }).catch(reason => {
      if (!active) return;
      const message = reason instanceof Error ? reason.message : 'Không tải được danh mục định dạng';
      setError(message);
      onStateChange?.({ status: 'error', formats: [], selectedId: '', error: message });
    });
    return () => { active = false; };
  }, [onStateChange]);
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
    onStart({ formatId: selected.id, formatVersion: selected.version, subject: selected.subjects[0],
      grade: selected.grades[0], examType: selected.examType, durationMinutes: selected.durationMinutes,
      itemCount: selected.totalQuestions, prompt: prompt?.trim() || `Tạo đề ${selected.displayName}`, uploadedFiles: [] });
  };
  return <>
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 999 }} />
    <div ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="preset-title" style={{ position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', zIndex: 1000, background: 'white', border: '1px solid #e2e8f0', borderRadius: 8, width: 'calc(100% - 32px)', maxWidth: 600, padding: 28, maxHeight: '90dvh', overflowY: 'auto' }}>
      <h2 id="preset-title">{title}</h2>
      <label>Yêu cầu bổ sung<textarea aria-label="Yêu cầu bổ sung" value={prompt || ''} maxLength={1000} onChange={event => onPromptChange?.(event.target.value)} /></label>
      {error && <p role="alert">{error}</p>}
      {!error && !formats.length && <p role="status">Đang tải định dạng từ máy chủ…</p>}
      {formats.map(format => <label key={format.id} style={{ display: 'block', padding: 16, border: '1px solid #e2e8f0', margin: '16px 0' }}>
        <input type="radio" name="preset" checked={selectedId === format.id} disabled={!format.available} onChange={() => { setSelectedId(format.id); onStateChange?.({ status: 'ready', formats, selectedId: format.id }); }} />
        {' '}{format.displayName} · {format.totalQuestions} câu · {format.durationMinutes} phút
        <p>{format.sections.map(section => `${section.id}: ${section.count} ${section.type === 'mcq' ? 'câu nhiều lựa chọn' : section.type === 'true_false' ? 'câu đúng/sai' : 'câu trả lời ngắn'}`).join(' · ')}</p>
      </label>)}
      {selected && <p>Môn {selected.subjects[0]} · Lớp {selected.grades[0]}. Số câu và thời gian theo định dạng đã chọn.</p>}
      <p>Các môn và định dạng khác chưa khả dụng trong luồng này. Tệp đính kèm chưa được hỗ trợ.</p>
      <button className="button-primary" disabled={!selected?.available || !!error} onClick={start}>Tạo đề thi</button>
      <button className="button-secondary" onClick={onClose}>Huỷ</button>
    </div>
  </>;
};
