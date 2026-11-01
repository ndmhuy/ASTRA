import React, { useState, useEffect, useRef } from 'react';
import type { ExamRequestParams, ExamType } from '../types/exam';

interface QuickPresetModalProps {
  title?: string;
  onStart: (params: ExamRequestParams) => void;
  onClose: () => void;
}

type PresetOption = {
  id: ExamType;
  label: string;
  questions: number;
  duration: number;
  description: string;
};

const PRESETS: PresetOption[] = [
  {
    id: 'THPT_STANDARD',
    label: 'THPT Quốc Gia',
    questions: 40,
    duration: 50,
    description: '40 câu · 50 phút',
  },
  {
    id: 'DGNL_DHQG',
    label: 'Đánh Giá Năng Lực',
    questions: 30,
    duration: 40,
    description: '30 câu · 40 phút',
  },
];

// Display labels for subjects — mapped to the actual Subject type values used in exam.ts
const SUBJECT_OPTIONS: { label: string; value: string }[] = [
  { label: 'Vật Lý',      value: 'V\u1eadt L\u00fd' },
  { label: 'Toán Học',    value: 'To\u00e1n H\u1ecdc' },
  { label: 'Hóa Học',     value: 'H\u00f3a H\u1ecdc' },
  { label: 'Sinh Học',    value: 'Sinh H\u1ecdc' },
  { label: 'Tiếng Anh',   value: 'Ti\u1ebfng Anh' },
  { label: 'Lịch Sử',     value: 'L\u1ecbch S\u1eed' },
  { label: 'Địa Lý',      value: '\u0110\u1ecba L\u00fd' },
  { label: 'GDCD / KTPL', value: 'GDCD / KTPL' },
  { label: 'Tổng hợp',    value: 'T\u1ed5ng h\u1ee3p' },
];

export const QuickPresetModal: React.FC<QuickPresetModalProps> = ({ onStart, onClose, title = 'Tạo đề từ mẫu' }) => {
  const [selectedPreset, setSelectedPreset] = useState<ExamType>('THPT_STANDARD');
  const [selectedSubjectValue, setSelectedSubjectValue] = useState<string>(SUBJECT_OPTIONS[0].value);

  const modalRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const modal = modalRef.current;
    const controls = () => Array.from(modal?.querySelectorAll<HTMLElement>('button, input, select') || []);
    controls()[0]?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'Tab') {
        const items = controls();
        const first = items[0];
        const last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    modal?.addEventListener('keydown', handleKey);
    return () => { modal?.removeEventListener('keydown', handleKey); previous?.focus(); };
  }, [onClose]);

  const handleStart = () => {
    const preset = PRESETS.find((p) => p.id === selectedPreset)!;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const subject = selectedSubjectValue as any;
    onStart({
      subject,
      grade: 12,
      examType: selectedPreset,
      durationMinutes: preset.duration,
      itemCount: preset.questions,
      prompt: `Tạo đề thi ${preset.label} môn ${SUBJECT_OPTIONS.find((s) => s.value === selectedSubjectValue)?.label}`,
      uploadedFiles: [],
    });
  };

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(15,23,42,0.35)',
          zIndex: 100,
        }}
      />

      {/* Modal */}
      <div ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="preset-title"
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 101,
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: 8,
          width: 'calc(100% - 32px)',
          maxHeight: '90dvh',
          overflowY: 'auto',
          maxWidth: 540,
          padding: '28px 28px 24px',
          boxShadow: '0 4px 24px rgba(0,0,0,0.10)',
        }}
      >
        <h2 id="preset-title"
          style={{
            fontSize: 20,
            fontWeight: 700,
            color: '#0f172a',
            marginBottom: 20,
          }}
        >
          {title}
        </h2>

        {/* Preset Cards */}
        <div style={{ marginBottom: 20 }}>
          <p style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Loại đề thi
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {PRESETS.map((preset) => {
              const isSelected = selectedPreset === preset.id;
              return (
                <label
                  key={preset.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    padding: '16px 18px',
                    border: `2px solid ${isSelected ? '#24634b' : '#e2e8f0'}`,
                    borderRadius: 6,
                    background: isSelected ? '#edf4ef' : '#ffffff',
                    cursor: 'pointer',
                    transition: 'border-color 150ms ease, background 150ms ease',
                  }}
                >
                  <input
                    type="radio"
                    name="preset"
                    value={preset.id}
                    checked={isSelected}
                    onChange={() => setSelectedPreset(preset.id)}
                    style={{ accentColor: '#24634b', width: 18, height: 18, flexShrink: 0 }}
                  />
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#0f172a' }}>{preset.label}</div>
                    <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>{preset.description}</div>
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        {/* Subject Select */}
        <div style={{ marginBottom: 24 }}>
          <label
            htmlFor="subject-select"
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: '#64748b',
              display: 'block',
              marginBottom: 8,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Môn học
          </label>
          <select
            id="subject-select"
            value={selectedSubjectValue}
            onChange={(e) => setSelectedSubjectValue(e.target.value)}
            style={{
              width: '100%',
              padding: '12px 14px',
              border: '1.5px solid #e2e8f0',
              borderRadius: 6,
              fontSize: 15,
              color: '#0f172a',
              background: '#ffffff',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            {SUBJECT_OPTIONS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {/* Actions */}
        <button
          onClick={handleStart}
          style={{
            width: '100%',
            padding: '15px 0',
            background: '#24634b',
            color: '#ffffff',
            border: 'none',
            borderRadius: 6,
            fontSize: 16,
            fontWeight: 700,
            cursor: 'pointer',
            marginBottom: 10,
            letterSpacing: '-0.01em',
          }}
        >
          Bắt đầu tạo đề →
        </button>

        <button
          onClick={onClose}
          style={{
            width: '100%',
            padding: '10px 0',
            background: 'transparent',
            color: '#64748b',
            border: 'none',
            fontSize: 14,
            cursor: 'pointer',
          }}
        >
          Huỷ
        </button>
      </div>
    </>
  );
};
