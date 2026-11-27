import { useEffect, useRef, useState } from 'react';
import { Check, FileText, Flag, LoaderCircle, Plus, Search, Trash2, Upload, X } from 'lucide-react';
import type { ExamSession } from '../state/examSessions';

function ExamStatus({ session }: { session: ExamSession }) {
  const previous = useRef(session.status);
  const [justCompleted, setJustCompleted] = useState(false);
  useEffect(() => {
    const completed = previous.current === 'generating' && session.status === 'complete';
    previous.current = session.status;
    if (!completed) return;
    setJustCompleted(true);
    const timer = window.setTimeout(() => setJustCompleted(false), 1600);
    return () => window.clearTimeout(timer);
  }, [session.status]);
  const flagged = session.questions.some(question => question.status === 'FLAGGED');
  if (session.status === 'generating') return <LoaderCircle className="exam-status-spinner" size={14} aria-label="Đang soạn" />;
  if (session.status === 'error') return <X className="exam-status-error" size={14} aria-label="Lỗi tạo đề" />;
  if (flagged) return <Flag size={14} aria-label="Có câu cần xem lại" />;
  if (justCompleted) return <Check className="exam-status-done" size={14} aria-label="Vừa hoàn thành" />;
  return null;
}

interface Props {
  sessions: ExamSession[];
  activeId: string | null;
  collapsed: boolean;
  searchSaved?: (query: string, signal: AbortSignal) => Promise<{ workspaceIds: string[] }>;
  error: string;
  onRetry: () => void;
  browserImport: { pending: boolean; message: string };
  onImport: () => void;
  onNew: () => void;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
}

function searchText(value: string) {
  return value.toLocaleLowerCase('vi').normalize('NFC').replace(/\s+/g, ' ').trim();
}

function foldSearchAccents(value: string) {
  return value.replace(/đ/g, 'd').normalize('NFD').replace(/\p{M}/gu, '');
}

function matchesSession(session: ExamSession, term: string, searchContent: boolean) {
  const ignoreAccents = term === foldSearchAccents(term);
  const matches = (value: string) => {
    const normalized = searchText(value);
    return (ignoreAccents ? foldSearchAccents(normalized) : normalized).includes(term);
  };
  if ([session.title, session.meta?.title, session.meta?.subject].some(text => text && matches(text))) return true;
  if (!searchContent) return false;
  return session.messages.some(message => message.role !== 'system' && matches(message.content)) ||
    session.questions.some(question => matches(question.stem) ||
      Object.values(question.choices ?? {}).some(matches) ||
      question.statements?.some(statement => matches(statement.text)));
}

export function SidebarExamLibrary({
  sessions, activeId, collapsed, searchSaved, error, onRetry, browserImport, onImport, onNew, onOpen, onDelete,
}: Props) {
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<{ term: string; ids?: Set<string> }>();
  const searchButton = useRef<HTMLButtonElement>(null);
  const term = searchOpen && !collapsed ? searchText(query) : '';

  useEffect(() => {
    if (!term || !searchSaved) return;
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      try {
        const { workspaceIds } = await searchSaved(term, controller.signal);
        if (!controller.signal.aborted) setResult({ term, ids: new Set(workspaceIds) });
      } catch {
        if (!controller.signal.aborted) setResult({ term });
      }
    }, 160);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [searchSaved, term]);

  const currentResult = result?.term === term ? result : undefined;
  const visible = term ? sessions.filter(session => currentResult?.ids?.has(session.id) ||
    matchesSession(session, term, session.browserOnly || !searchSaved || Boolean(currentResult && !currentResult.ids))) : sessions;

  function closeSearch() {
    setSearchOpen(false);
    setQuery('');
    setResult(undefined);
  }

  function dismissSearch() {
    closeSearch();
    window.requestAnimationFrame(() => searchButton.current?.focus());
  }
  useEffect(() => {
    if (!deleteId) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setDeleteId(null);
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [deleteId]);
  return <nav className="sidebar-library" aria-label="Đề thi của thầy cô">
    <button type="button" className="sidebar-new-exam" onClick={onNew} title="Tạo đề mới"><Plus size={16} aria-hidden="true" /><span className="sidebar-label">Tạo đề mới</span></button>
    <div className="sidebar-library-search">
      {searchOpen ? <div className="sidebar-library-search-field"
        onKeyDown={event => {
          if (event.key !== 'Escape') return;
          event.preventDefault();
          dismissSearch();
        }}>
        <input type="search" aria-label="Tìm đề thi và tin nhắn" placeholder="Tìm trong tủ đề…"
          maxLength={200} value={query} autoFocus onChange={event => setQuery(event.target.value)} />
        <button type="button" className="sidebar-library-search-close" aria-label="Đóng tìm kiếm"
          title="Đóng tìm kiếm" onClick={dismissSearch}><X size={14} aria-hidden="true" /></button>
      </div> : <>
        <h2 className="sidebar-library-heading sidebar-label">Tủ đề</h2>
        <button ref={searchButton} type="button" aria-label="Tìm trong tủ đề" title="Tìm trong tủ đề"
          onClick={() => setSearchOpen(true)}><Search size={14} aria-hidden="true" /></button>
      </>}
    </div>
    {sessions.some(session => session.browserOnly) && (
      <button type="button" className="sidebar-new-exam sidebar-import-action" aria-label="Nhập đề từ trình duyệt này"
        title="Nhập đề từ trình duyệt này" disabled={browserImport.pending} onClick={onImport}>
        <Upload size={16} aria-hidden="true" />
        <span className="sidebar-label">{browserImport.pending ? 'Đang nhập…' : 'Nhập đề cũ'}</span>
      </button>
    )}
    {browserImport.message && (
      <p className="sidebar-import-status sidebar-label" role="status">{browserImport.message}</p>
    )}
    {error && <div className="sidebar-library-error">
      <span role="alert">{error}</span>
      <button type="button" onClick={onRetry}>Thử lại</button>
    </div>}
    {sessions.length === 0 && !error && (
      <div className="sidebar-library-empty sidebar-label">
        <FileText size={15} aria-hidden="true" />
        <span>Đề thi đã soạn sẽ lưu tại đây.</span>
      </div>
    )}
    {term && sessions.length > 0 && visible.length === 0 && <div className="sidebar-library-empty" role="status">
      {searchSaved && !currentResult ? 'Đang tìm…' : currentResult && !currentResult.ids ? 'Không thể tìm nội dung đã lưu.' : 'Không tìm thấy kết quả.'}
    </div>}
    <ul className="sidebar-exams">{visible.map(session => <li key={session.id}>
      <div className="sidebar-exam-row">
        <button type="button" className="sidebar-exam" onClick={() => { closeSearch(); onOpen(session.id); }} aria-current={session.id === activeId ? 'page' : undefined} title={session.title}>
          <FileText className="sidebar-exam-document" size={14} aria-hidden="true" />
          <span className="sidebar-exam-copy sidebar-label">
            <span className="sidebar-exam-title">{session.mode === 'template' ? session.meta?.title ?? session.title : session.title}</span>
            {session.meta && (
              <span className="sidebar-exam-meta">
                {session.meta.totalCount} câu · {session.meta.duration} phút
              </span>
            )}
            {session.browserOnly && <span className="sidebar-exam-meta">Chỉ trên trình duyệt này</span>}
          </span>
          <span className="sidebar-exam-status" role="status"><ExamStatus session={session} /></span>
        </button>
        <button type="button" className="sidebar-exam-delete" onClick={() => setDeleteId(deleteId === session.id ? null : session.id)} title={`Xóa ${session.title}`} aria-label={`Xóa ${session.title}`}><Trash2 size={13} aria-hidden="true" /></button>
      </div>
      {deleteId === session.id && (
        <div className="sidebar-delete-confirm">
          <span>Xóa đề này?</span>
          <button type="button" className="is-danger" onClick={() => { onDelete(session.id); setDeleteId(null); }}>Xóa</button>
          <button type="button" className="is-cancel" onClick={() => setDeleteId(null)}>Hủy</button>
        </div>
      )}
    </li>)}</ul>
  </nav>;
}
