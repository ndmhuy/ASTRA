import { MessageSquareText, Pencil, X } from 'lucide-react';
import type { DeferredAgentNote } from '../agent/contracts';

interface AgentNotesProps {
  notes: DeferredAgentNote[];
  onCancel: (noteId: string) => void;
  onPrepareEdit: (note: DeferredAgentNote) => void;
}

export function AgentNotes({ notes, onCancel, onPrepareEdit }: AgentNotesProps) {
  const pending = notes.filter(note => note.status === 'pending');
  if (!pending.length) return null;
  return <section className="agent-notes" aria-label="Ghi chú chỉnh sửa đang chờ">
    <div className="agent-notes-heading"><MessageSquareText size={16} /><strong>Ghi chú chờ xem lại ({pending.length})</strong></div>
    <p>Ghi chú chưa sửa đề và sẽ không tự động áp dụng.</p>
    <ul>{pending.map(note => <li key={note.id}>
      <span>{note.targetQuestion ? `Câu ${note.targetQuestion}: ` : ''}{note.requestedChange}</span>
      <div>
        <button type="button" onClick={() => onPrepareEdit(note)} aria-label={`Chuẩn bị sửa ghi chú ${note.id}`}><Pencil size={13} /> Sửa</button>
        <button type="button" onClick={() => onCancel(note.id)} aria-label={`Hủy ghi chú ${note.id}`}><X size={13} /> Hủy</button>
      </div>
    </li>)}</ul>
  </section>;
}
