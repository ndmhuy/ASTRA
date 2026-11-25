import React, { useState } from 'react';
import type { QuestionItem } from '../types/exam';

interface Props {
  question: QuestionItem;
  onSave: (question: QuestionItem) => Promise<void>;
  onRegenerate: (instruction: string) => Promise<void>;
  onClose: () => void;
}

export const QuestionEditor: React.FC<Props> = ({ question, onSave, onRegenerate, onClose }) => {
  const [draft, setDraft] = useState(() => structuredClone(question));
  const [instruction, setInstruction] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const action = async (operation: () => Promise<void>) => {
    setBusy(true); setError('');
    try { await operation(); } catch (error) { setError(error instanceof Error ? error.message : 'Không lưu được câu hỏi'); }
    finally { setBusy(false); }
  };
  return <div className="integration-editor-backdrop">
    <section role="dialog" aria-modal="true" aria-labelledby="edit-title" className="integration-editor">
      <h2 id="edit-title">Sửa câu {question.stableId || question.id}</h2>
      <p>Lưu hoặc tạo lại sẽ hủy phê duyệt cũ.</p>
      {error && <p role="alert">{error}</p>}
      <label>Đề bài<textarea aria-label="Đề bài" value={draft.stem} onChange={e => setDraft({ ...draft, stem: e.target.value })} /></label>
      {(!draft.questionType || draft.questionType === 'mcq') && <>
        {(['A', 'B', 'C', 'D'] as const).map(key => <label key={key}>Phương án {key}<textarea value={draft.choices[key]} onChange={e => setDraft({ ...draft, choices: { ...draft.choices, [key]: e.target.value } })} /></label>)}
        <label>Đáp án<select value={draft.key} onChange={e => setDraft({ ...draft, key: e.target.value })}>{['A', 'B', 'C', 'D'].map(key => <option key={key}>{key}</option>)}</select></label>
      </>}
      {draft.questionType === 'true_false' && draft.statements?.map((statement, index) => <fieldset key={index}>
        <legend>Ý {'abcd'[index]}</legend>
        <textarea aria-label={`Nội dung ý ${'abcd'[index]}`} value={statement.text} onChange={e => setDraft({ ...draft, statements: draft.statements!.map((s, i) => i === index ? { ...s, text: e.target.value } : s) })} />
        <label><input type="checkbox" checked={statement.answer} onChange={e => setDraft({ ...draft, statements: draft.statements!.map((s, i) => i === index ? { ...s, answer: e.target.checked } : s) })} /> Đúng</label>
      </fieldset>)}
      {draft.questionType === 'short_answer' && <label>Đáp án số<input value={draft.key} onChange={e => setDraft({ ...draft, key: e.target.value })} /></label>}
      <label>Lời giải<textarea value={draft.explanation} onChange={e => setDraft({ ...draft, explanation: e.target.value })} /></label>
      <label>Yêu cầu tạo lại<textarea value={instruction} onChange={e => setInstruction(e.target.value)} /></label>
      <button className="button-primary" disabled={busy} onClick={() => { void action(() => onSave(draft)); }}>Lưu thay đổi</button>
      <button className="button-secondary" disabled={busy} onClick={() => { void action(() => onRegenerate(instruction)); }}>Tạo lại và giải kiểm tra</button>
      <button className="button-secondary" disabled={busy} onClick={onClose}>Đóng</button>
    </section>
  </div>;
};
