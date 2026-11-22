import React, { useEffect, useRef, useState } from 'react';
import type { ExamFormat, ExamRequestParams } from '../types/exam';
import { getBackendHealth, getExamFormats, type BackendHealth } from '../services/examService';

interface Props { title?: string; onStart: (params: ExamRequestParams) => void; onClose: () => void; }

export const QuickPresetModal: React.FC<Props> = ({ onStart, onClose, title = 'Tạo đề từ mẫu' }) => {
  const [formats, setFormats] = useState<ExamFormat[]>([]);
  const [selectedId, setSelectedId] = useState('thpt-math');
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [error, setError] = useState('');
  const modalRef = useRef<HTMLDivElement>(null);
  const selected = formats.find(format => format.id === selectedId);
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
    onStart({ formatId: selected.id, formatVersion: selected.version, subject: selected.subjects[0],
      grade: selected.grades[0], examType: selected.examType, durationMinutes: selected.durationMinutes,
      itemCount: selected.totalQuestions, prompt: `Tạo đề ${selected.displayName}`, uploadedFiles: [] });
  };
  return <>
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 999 }} />
    <div ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="preset-title" style={{ position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', zIndex: 1000, background: 'white', border: '1px solid #e2e8f0', borderRadius: 8, width: 'calc(100% - 32px)', maxWidth: 600, padding: 28, maxHeight: '90dvh', overflowY: 'auto' }}>
      <h2 id="preset-title">{title}</h2>
      {error && (
        <div role="alert">
          <p>{error}</p>
        </div>
      )}
      {!error && !formats.length && <p role="status">Đang tải danh sách mẫu đề…</p>}
      {health && !error && (
        <p className="preset-mode-notice" role="status">
          {health.demoMode
            ? 'Đang ở chế độ chạy thử (Demo): dùng dữ liệu mẫu, không gọi AI và không tốn chi phí.'
            : health.providerConfigured
              ? 'Đang dùng AI thật (sẽ tính phí theo nhà cung cấp AI). Nếu chỉ muốn chạy thử không tốn phí, hãy mở bằng start-astra-demo.bat.'
              : 'Chưa kết nối dịch vụ AI. Để dùng thử miễn phí ngay, thầy cô hãy mở bằng start-astra-demo.bat.'}
        </p>
      )}
      {formats.map(format => <label key={format.id} style={{ display: 'block', padding: 16, border: '1px solid #e2e8f0', margin: '16px 0' }}>
        <input type="radio" name="preset" checked={selectedId === format.id} disabled={!format.available} onChange={() => setSelectedId(format.id)} />
        {' '}{format.displayName} · {format.totalQuestions} câu · {format.durationMinutes} phút
        <p>{format.sections.map(section => `${section.title || section.id}: ${section.count} ${section.type === 'mcq' ? 'câu nhiều lựa chọn' : section.type === 'true_false' ? 'câu đúng/sai' : 'câu trả lời ngắn'}`).join(' · ')}</p>
      </label>)}
      {selected && <p>Môn {selected.subjects[0]} · Lớp {selected.grades[0]}. Số câu và thời gian theo định dạng đã chọn.</p>}
      <p>Các định dạng khả dụng được tải từ máy chủ (hiện hỗ trợ Toán THPT và V-ACT). Tệp đính kèm chưa được hỗ trợ.</p>
      <button className="button-primary" disabled={!selected?.available || !!error} onClick={start}>Tạo đề thi</button>
      <button className="button-secondary" onClick={onClose}>Huỷ</button>
    </div>
  </>;
};
