import { useEffect, useRef, useState } from 'react';
import { Check, FileText, Flag, FolderOpen, LoaderCircle, Plus, Trash2, X } from 'lucide-react';
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

function shortTimestamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

interface Props {
  sessions: ExamSession[];
  activeId: string | null;
  storageActive?: boolean;
  onNew: () => void;
  onOpen: (id: string) => void;
  onOpenStorage?: () => void;
  onDelete: (id: string) => void;
}

const MAX_RECENT_SIDEBAR = 5;

export function SidebarExamLibrary({ sessions, activeId, storageActive = false, onNew, onOpen, onOpenStorage, onDelete }: Props) {
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const recentSessions = sessions.slice(0, MAX_RECENT_SIDEBAR);

  return <nav className="sidebar-library" aria-label="Điều hướng và đề thi gần đây">
    <button className="sidebar-new-exam" onClick={onNew} title="Tạo đề mới">
      <Plus size={16} aria-hidden="true" />
      <span className="sidebar-label">Tạo đề mới</span>
    </button>
    {onOpenStorage && (
      <button
        type="button"
        className="sidebar-storage-link"
        onClick={onOpenStorage}
        aria-current={storageActive ? 'page' : undefined}
        title="Mở Kho đề của tôi"
      >
        <FolderOpen size={16} aria-hidden="true" />
        <span className="sidebar-label">Kho đề</span>
        {sessions.length > 0 && <span className="sidebar-count-badge sidebar-label">{sessions.length}</span>}
      </button>
    )}
    <h2 className="sidebar-library-heading sidebar-label">Gần đây</h2>
    {recentSessions.length === 0 && <p className="sidebar-library-empty sidebar-label">Đề gần đây sẽ hiện tại đây.</p>}
    <ul className="sidebar-exams">{recentSessions.map(session => <li key={session.id}>
      <div className="sidebar-exam-row">
        <button className="sidebar-exam" onClick={() => onOpen(session.id)} aria-current={session.id === activeId ? 'page' : undefined} title={`${session.title} (#${session.id.slice(0, 6)})`}>
          <FileText className="sidebar-exam-document" size={14} aria-hidden="true" />
          <span className="sidebar-exam-text sidebar-label">
            <span className="sidebar-exam-title">{session.title}</span>
            <span className="sidebar-exam-meta">{shortTimestamp(session.createdAt)} · #{session.id.slice(0, 4)}</span>
          </span>
          <span className="sidebar-exam-status" role="status"><ExamStatus session={session} /></span>
        </button>
        <button className="sidebar-exam-delete" onClick={() => setDeleteId(deleteId === session.id ? null : session.id)} title={`Xóa ${session.title}`} aria-label={`Xóa ${session.title}`}><Trash2 size={12} /></button>
      </div>
      {deleteId === session.id && (
        <div className="sidebar-delete-confirm">
          <span>{session.status === 'generating' ? 'Chỉ ẩn khỏi danh sách (không hủy job máy chủ)?' : 'Xóa đề này?'}</span>
          <button onClick={() => { onDelete(session.id); setDeleteId(null); }}>Xóa</button>
          <button onClick={() => setDeleteId(null)}>Hủy</button>
        </div>
      )}
    </li>)}</ul>
    {onOpenStorage && sessions.length > MAX_RECENT_SIDEBAR && (
      <button type="button" className="sidebar-more-link sidebar-label" onClick={onOpenStorage}>
        Xem tất cả ({sessions.length}) →
      </button>
    )}
  </nav>;
}
