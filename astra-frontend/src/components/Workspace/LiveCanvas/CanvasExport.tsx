import { useEffect, useId, useRef, useState } from 'react';
import { Download } from 'lucide-react';

export type CanvasExportFormat = 'docx' | 'pdf' | 'tex' | 'json' | 'md';

const OPTIONS: ReadonlyArray<{ format: CanvasExportFormat; label: string }> = [
  { format: 'docx', label: 'Word (.docx)' },
  { format: 'pdf', label: 'PDF (.pdf)' },
  { format: 'tex', label: 'LaTeX (.tex)' },
  { format: 'md', label: 'Markdown (.md)' },
  { format: 'json', label: 'Đáp án (.json)' },
];

export function CanvasExport({ approved, pdfReady, onExport }: {
  approved: boolean;
  pdfReady: boolean;
  onExport: (format: CanvasExportFormat) => Promise<boolean>;
}) {
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState<CanvasExportFormat>();
  const popup = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const popupId = useId();

  useEffect(() => {
    if (!open) return;
    function handleOutside(event: PointerEvent) {
      const target = event.target as Node;
      if (!trigger.current?.contains(target) && !popup.current?.contains(target)) setOpen(false);
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key !== 'Escape') return;
      setOpen(false);
      trigger.current?.focus();
    }
    document.addEventListener('pointerdown', handleOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('pointerdown', handleOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [open]);

  async function download(format: CanvasExportFormat) {
    setPending(format);
    try {
      if (await onExport(format)) {
        setOpen(false);
        if (popup.current?.contains(document.activeElement)) trigger.current?.focus();
      }
    } finally {
      setPending(undefined);
    }
  }

  return <>
    <button ref={trigger} className="canvas-export-trigger" type="button"
      aria-expanded={open} aria-controls={open ? popupId : undefined}
      onClick={() => setOpen(!open)}><Download size={14} aria-hidden="true" />Xuất</button>
    {open && <div ref={popup} id={popupId} className="canvas-export-popup" role="group" aria-label="Định dạng xuất đề">
      {!approved && <p>Cần phê duyệt đề trước khi xuất.</p>}
      {OPTIONS.map(({ format, label }) => <button key={format} type="button"
        disabled={!approved || Boolean(pending) || (format === 'pdf' && !pdfReady)}
        onClick={() => { void download(format); }}>
        {pending === format ? 'Đang tạo tệp…' : label}
      </button>)}
    </div>}
  </>;
}
