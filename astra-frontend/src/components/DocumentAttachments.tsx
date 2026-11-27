import { useEffect, useRef, useState } from 'react';
import { Paperclip, X } from 'lucide-react';
import { documentKinds, getDocumentPolicy, uploadDocument, validateDocument } from '../services/inputDocuments';
import type { DocumentKind, DocumentPolicy, InputDocument, InputDocumentsUpdate } from '../services/inputDocuments';
import './DocumentAttachments.css';

interface Props {
  documents: InputDocument[]; onChange: (documents: InputDocumentsUpdate) => void;
  disabled?: boolean; onBusyChange?: (busy: boolean) => void;
}
export function DocumentAttachments({ documents, onChange, disabled, onBusyChange }: Props) {
  const [policy, setPolicy] = useState<DocumentPolicy>();
  const [kind, setKind] = useState<DocumentKind>('supplementary');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const uploading = useRef(false);
  const mounted = useRef(true);
  const abortRef = useRef<AbortController | null>(null);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      abortRef.current?.abort();
      abortRef.current = null;
    };
  }, []);
  useEffect(() => {
    let active = true;
    void getDocumentPolicy().then(value => { if (active) { setPolicy(value); setError(''); } })
      .catch(() => { if (active) setError('Chưa lấy được giới hạn tải tài liệu.'); });
    return () => { active = false; };
  }, [attempt]);
  const upload = async (files: File[]) => {
    if (!policy || uploading.current || disabled) return;
    const controller = new AbortController();
    abortRef.current = controller;
    uploading.current = true; setBusy(true); onBusyChange?.(true); setError('');
    const uploaded = [...documents];
    const errors: string[] = [];
    try {
      for (const file of files) {
        if (!mounted.current || controller.signal.aborted) return;
        const invalid = validateDocument(file, uploaded.length, policy);
        if (invalid) { errors.push(`${file.name}: ${invalid}`); continue; }
        try {
          const saved = await uploadDocument(file, kind, controller.signal);
          if (!mounted.current || controller.signal.aborted) return;
          uploaded.push(saved);
          onChange(current => current.some(item => item.id === saved.id) || current.length >= policy.max_files
            ? current : [...current, saved]);
        } catch (failure) {
          if (!mounted.current || controller.signal.aborted) return;
          errors.push(`${file.name}: ${failure instanceof Error ? failure.message : 'Không tải được tệp.'}`);
        }
      }
      if (mounted.current && !controller.signal.aborted) setError(errors.join('\n'));
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      uploading.current = false;
      if (mounted.current) { setBusy(false); onBusyChange?.(false); }
    }
  };
  return <section className="input-documents" aria-label="Tài liệu đầu vào">
    <div className="input-document-tools">
      <label>Loại tài liệu <select aria-label="Loại tài liệu tải lên" value={kind} disabled={disabled || busy} onChange={e => setKind(e.target.value as DocumentKind)}>
        {Object.entries(documentKinds).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select></label>
      <button type="button" className="composer-tool-btn" disabled={disabled || busy || !policy || documents.length >= policy.max_files}
        onClick={() => input.current?.click()}><Paperclip size={15} aria-hidden="true" />Đính kèm tài liệu</button>
      <input ref={input} className="composer-file-input" type="file" multiple accept={policy?.extensions.join(',')}
        aria-label="Chọn tài liệu đầu vào" disabled={disabled || busy || !policy}
        onChange={event => { const selected = Array.from(event.target.files ?? []); event.target.value = ''; void upload(selected); }} />
    </div>
    <small>PDF có chữ, DOCX, TXT, MD, CSV, JSON{policy ? ` · ${policy.max_files} tệp · ${policy.max_bytes / 1048576} MiB/tệp · ${policy.max_characters.toLocaleString('vi-VN')} ký tự/tệp` : ''}</small>
    <small>Ma trận hướng dẫn chủ đề và mức độ trong cấu trúc đề đã chọn. PDF scan cần OCR trước.</small>
    {busy && <p role="status">Đang tải và đọc tài liệu…</p>}
    {error && <p role="alert" className="input-document-error">{error}{!policy && <button type="button" onClick={() => setAttempt(value => value + 1)}>Thử lại</button>}</p>}
    {documents.map(document => <div className="input-document" key={document.id}>
      <details><summary>{documentKinds[document.kind]} · {document.filename} · {document.characters.toLocaleString('vi-VN')} ký tự</summary>
        <pre>{document.preview}</pre></details>
      <button type="button" className="composer-file-remove" aria-label={`Bỏ đính kèm ${document.filename}`} disabled={disabled || busy}
        onClick={() => onChange(documents.filter(item => item.id !== document.id))}><X size={14} aria-hidden="true" /></button>
    </div>)}
  </section>;
}
