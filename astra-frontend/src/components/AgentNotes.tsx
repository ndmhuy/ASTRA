import { Check, MessageSquareText, Pencil, Play, X } from 'lucide-react';
import type { DeferredAgentNote } from '../agent/contracts';

interface AgentNotesProps {
  notes: DeferredAgentNote[];
  onCancel: (noteId: string) => void;
  onPrepareEdit: (note: DeferredAgentNote) => void;
  onApprove?: (noteId: string) => void;
  onApply?: (noteId: string) => void;
}

export function AgentNotes({ notes, onCancel, onPrepareEdit, onApprove, onApply }: AgentNotesProps) {
  const visible = notes.filter(note => note.status !== 'cancelled');
  if (!visible.length) return null;
  return <section className="agent-notes" aria-label="Ghi chú chỉnh sửa đang chờ">
    <div className="agent-notes-heading"><MessageSquareText size={16} /><strong>Ghi chú chỉnh sửa ({visible.length})</strong></div>
    <p>Ghi chú chưa sửa đề và sẽ không tự động áp dụng.</p>
    <ul>{visible.map(note => <li key={note.id}>
      <span>{note.targetQuestion ? `Câu ${note.targetQuestion}: ` : ''}{note.requestedChange} <em>({note.status})</em></span>
      <div>
        {['pending', 'approved', 'failed'].includes(note.status) && <button type="button" onClick={() => onPrepareEdit(note)}><Pencil size={13} /> Sửa</button>}
        {note.status === 'pending' && onApprove && <button type="button" onClick={() => onApprove(note.id)}><Check size={13} /> Duyệt</button>}
        {note.status === 'approved' && onApply && <button type="button" onClick={() => onApply(note.id)}><Play size={13} /> Áp dụng</button>}
        {['pending', 'approved', 'failed'].includes(note.status) && <button type="button" onClick={() => onCancel(note.id)}><X size={13} /> Hủy</button>}
      </div>
    </li>)}</ul>
  </section>;
}
