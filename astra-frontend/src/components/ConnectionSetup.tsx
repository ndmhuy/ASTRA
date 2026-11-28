import { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { AlertCircle, ArrowRight, Check, Eye, EyeOff, KeyRound, LoaderCircle, LockKeyhole, X } from 'lucide-react';
import { readConnection, saveConnection, type ConnectionStatus } from '../services/connection';
import './ConnectionSetup.css';

export function ConnectionSetup({ busy = false }: { busy?: boolean }) {
  const [status, setStatus] = useState<ConnectionStatus | null>(null);
  const [open, setOpen] = useState(false);
  const [key, setKey] = useState('');
  const [visible, setVisible] = useState(false);
  const [model, setModel] = useState('');
  const [url, setUrl] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [connectionError, setConnectionError] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const initialized = useRef(false);
  const saveRevision = useRef(0);
  const required = status?.configured === false;
  const available = status !== null;
  const isOpen = open || required;

  useEffect(() => {
    let live = true;
    const refresh = async () => {
      const revision = saveRevision.current;
      if (revision % 2) return;
      try {
        const value = await readConnection();
        if (live && revision === saveRevision.current) {
          if (!initialized.current && value) {
            setModel(value.model); setUrl(value.baseUrl); initialized.current = true;
          }
          setStatus(value); setConnectionError(false);
        }
      } catch { if (live) setConnectionError(true); }
    };
    void refresh();
    const interval = setInterval(() => { void refresh(); }, 5000);
    return () => { live = false; clearInterval(interval); };
  }, []);

  const edit = useCallback(() => {
    if (!status) return;
    setKey(''); setVisible(false); setError('');
    setModel(status.model); setUrl(status.baseUrl); setOpen(true);
  }, [status]);

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (isOpen && !element.open) element.showModal();
    else if (!isOpen && element.open) element.close();
  }, [isOpen, available]);

  const close = () => { if (!required && !saving) { setOpen(false); setKey(''); setVisible(false); setError(''); } };
  if (!status) return connectionError ? <span className="connection-offline" role="status">Chưa kết nối Backend</span> : null;
  const locked = busy || status.busy;

  return <>
    <button type="button" className={`connection-trigger ${status.lastFailure ? 'has-error' : ''}`} onClick={edit}
      title={`${status.model} · ${status.verified ? 'Đã nhận phản hồi API' : 'Chưa gọi API để kiểm tra'}`}>
      {status.lastFailure ? <AlertCircle size={16} /> : <KeyRound size={16} />}
      <span>{status.lastFailure ? 'Kiểm tra kết nối AI' : status.configured ? 'API key đã lưu' : 'Kết nối AI'}</span>
      {status.configured && !status.lastFailure && <Check size={14} className="connection-check" />}
    </button>
    {createPortal(<>
      {status.lastFailure && !isOpen && <aside className="connection-failure" role="alert">
        <AlertCircle size={19} /><div><strong>Kết nối AI cần kiểm tra</strong><p>{status.lastFailure.message}</p>
          <button type="button" onClick={edit}>Mở kết nối AI</button></div>
      </aside>}
      <dialog ref={dialog} className="connection-dialog" aria-labelledby="connection-title" aria-describedby="connection-description"
        onCancel={event => { event.preventDefault(); close(); }}>
        <form onSubmit={async event => {
          event.preventDefault();
          if (saving || locked) return;
          saveRevision.current += 1;
          setSaving(true); setError('');
          try {
            const saved = await saveConnection(status, key.trim(), model.trim(), url.trim());
            if (!saved) throw new Error('Backend chưa hỗ trợ lưu kết nối. Hãy khởi động bằng start.cmd.');
            setStatus(saved); setKey(''); setVisible(false); setOpen(false);
          } catch (failure) {
            setError(failure instanceof Error && failure.name === 'Error' ? failure.message : 'Kết nối tới ứng dụng bị gián đoạn. Hãy thử lưu lại.');
          } finally { saveRevision.current += 1; setSaving(false); }
        }}>
          {!required && <button type="button" className="connection-close" aria-label="Đóng kết nối AI" disabled={saving} onClick={close}><X size={20} /></button>}
          <div className="connection-emblem"><KeyRound size={27} strokeWidth={1.6} /></div>
          <span className="connection-eyebrow">ASTRA · KẾT NỐI AI</span>
          <h1 id="connection-title">Một key, sẵn sàng<br />cùng bạn soạn đề.</h1>
          <p id="connection-description" className="connection-description">Nhập API key của bạn để dùng chung cho trò chuyện và sinh đề.</p>
          <label className="connection-label" htmlFor="connection-key">API key {status.configured && <span>Để trống để giữ key hiện tại</span>}</label>
          <div className="connection-key-field">
            <LockKeyhole size={18} aria-hidden="true" />
            <input id="connection-key" name="astra-local-key" type={visible ? 'text' : 'password'} value={key}
              onChange={event => setKey(event.target.value)} placeholder={status.configured ? '••••••••••••••••••••••••' : 'Dán API key của bạn'}
              required={!status.configured} maxLength={4096} autoComplete="off" autoCapitalize="none" spellCheck={false} autoFocus disabled={saving} />
            <button type="button" aria-label={visible ? 'Ẩn API key' : 'Hiện API key'} onClick={() => setVisible(value => !value)} disabled={saving}>
              {visible ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          <div className="connection-destination"><span>MODEL DÙNG CHUNG</span><strong>{model || status.model}</strong></div>
          <details className="connection-advanced"><summary>URL &amp; model</summary>
            <label htmlFor="connection-url">API Base URL</label>
            <input id="connection-url" type="url" value={url} onChange={event => setUrl(event.target.value)} required disabled={saving} maxLength={2048} autoComplete="off" />
            <label htmlFor="connection-model">Model ID</label>
            <input id="connection-model" value={model} onChange={event => setModel(event.target.value)} required disabled={saving} maxLength={200} autoComplete="off" />
            <p>Dùng API Claude / Anthropic Messages. Cấu hình này áp dụng cho cả chat và sinh đề.</p>
          </details>
          {(error || status.configurationError || status.lastFailure) && <div className="connection-form-error" role="alert">
            <AlertCircle size={18} /><div>{error || status.configurationError || status.lastFailure?.message}
              {status.lastFailure && !error && <small>{status.lastFailure.status ? `HTTP ${status.lastFailure.status}` : status.lastFailure.code}{status.lastFailure.field ? ` · ${status.lastFailure.field}` : ''} · Không tự gọi lại API.</small>}
            </div>
          </div>}
          {locked && <p className="connection-busy" role="status">Chat hoặc sinh đề đang chạy. Hãy chờ hoàn tất hoặc dừng tác vụ trước khi đổi kết nối.</p>}
          {connectionError && <p role="status">Kết nối tới Backend bị gián đoạn. Cấu hình đang nhập vẫn được giữ.</p>}
          <button type="submit" className="connection-save" disabled={saving || locked}>
            {saving ? <><LoaderCircle size={18} className="connection-spinner" />Đang lưu…</> : <>{required ? 'Lưu và vào ASTRA' : 'Lưu kết nối'}<ArrowRight size={18} /></>}
          </button>
          <p className="connection-footnote"><LockKeyhole size={14} />Lưu trên máy này trong <code>.env</code>, được Git bỏ qua.</p>
          <p className="connection-no-probe">Lưu key không gọi thử API. API chỉ được gọi khi bạn thao tác.</p>
        </form>
      </dialog>
    </>, document.body)}
  </>;
}
