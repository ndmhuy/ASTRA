import { useEffect, useRef, useState } from 'react';
import { Check, FileText, Flag, LoaderCircle, Plus, Trash2, X } from 'lucide-react';
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
  onNew: () => void;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
}
export function SidebarExamLibrary({ sessions, activeId, onNew, onOpen, onDelete }: Props) {
  const [deleteId, setDeleteId] = useState<string | null>(null);
  return <nav className="sidebar-library" aria-label="Đề thi của thầy cô">
    <button className="sidebar-new-exam" onClick={onNew} title="Tạo đề mới"><Plus size={16} aria-hidden="true" /><span className="sidebar-label">Tạo đề mới</span></button>
    <h2 className="sidebar-library-heading sidebar-label">Tủ đề</h2>
    {sessions.length === 0 && <p className="sidebar-library-empty sidebar-label">Đề thi sẽ xuất hiện ở đây.</p>}
    <ul className="sidebar-exams">{sessions.map(session => <li key={session.id}>
      <div className="sidebar-exam-row">
        <button className="sidebar-exam" onClick={() => onOpen(session.id)} aria-current={session.id === activeId ? 'page' : undefined} title={session.title}>
          <FileText className="sidebar-exam-document" size={14} aria-hidden="true" />
          <span className="sidebar-exam-title sidebar-label">{session.title}</span>
          <span className="sidebar-exam-status" role="status"><ExamStatus session={session} /></span>
        </button>
        <button className="sidebar-exam-delete" onClick={() => setDeleteId(deleteId === session.id ? null : session.id)} title={`Xóa ${session.title}`} aria-label={`Xóa ${session.title}`}><Trash2 size={12} /></button>
      </div>
      {deleteId === session.id && <div className="sidebar-delete-confirm"><span>Xóa đề này?</span><button onClick={() => { onDelete(session.id); setDeleteId(null); }}>Xóa</button><button onClick={() => setDeleteId(null)}>Hủy</button></div>}
    </li>)}</ul>
  </nav>;
}
