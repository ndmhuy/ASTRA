import { useEffect, useRef, useState } from 'react';
import { RotateCcw, X } from 'lucide-react';
import type { ExamHistory, ExamPackage, ExamVersionSummary } from '../types/exam';
import { ExamPaperView } from './Workspace/LiveCanvas/ExamPaperView';

interface Props {
  history: ExamHistory;
  jobId: string;
  workspaceId?: string;
  revision: number;
  onClose: () => void;
  onRestore: (version: number, currentRevision: number, jobId: string, targetJobId: string) => Promise<void>;
}

type HistoryResult = Awaited<ReturnType<ExamHistory['list']>>;

const timestamp = new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'short' });

function changeLabel(version: ExamVersionSummary) {
  switch (version.change) {
    case 'generated': return 'Đề vừa tạo';
    case 'baseline': return 'Bản lưu đầu tiên';
    case 'edited': return `Sửa câu ${version.questionId}`;
    case 'regenerated': return `Tạo lại câu ${version.questionId}`;
    case 'restored': return `Khôi phục phiên bản ${version.restoredFrom}`;
    case 'undone': return `Hoàn tác câu ${version.questionId}`;
    case 'branched': return 'Tạo nhánh đề thi';
  }
}

export function ExamVersionHistory({ history, jobId, workspaceId, revision, onClose, onRestore }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [listResult, setListResult] = useState<{ revision: number; data?: HistoryResult; error?: string }>();
  const [choice, setChoice] = useState<string>();
  const [previewResult, setPreviewResult] = useState<{ key: string; data?: ExamPackage; error?: string }>();
  const [restoreError, setRestoreError] = useState('');
  const [restoring, setRestoring] = useState(false);
  const list = listResult?.revision === revision ? listResult : undefined;
  const entries = list?.data;
  const currentJobId = entries?.currentJobId ?? jobId;
  const keyFor = (item: ExamVersionSummary) => `${item.jobId ?? jobId}:${item.revision}`;
  const currentKey = `${currentJobId}:${entries?.currentRevision}`;
  const version = entries?.versions.find(item => keyFor(item) === choice) ??
    entries?.versions.find(item => keyFor(item) !== currentKey) ?? entries?.versions[0];
  const selected = version?.revision;
  const selectedJob = version?.jobId ?? jobId;
  const selectedKey = `${selectedJob}:${selected}`;
  const viewed = previewResult?.key === selectedKey ? previewResult : undefined;
  const preview = viewed?.data;
  const canRestore = version?.restorable && selectedKey !== currentKey && preview?.revision === selected;

  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);

  useEffect(() => {
    let current = true;
    void history.list(jobId, workspaceId).then(result => {
      if (current) setListResult({ revision, data: result });
    }).catch(error => {
      if (current) setListResult({ revision, error: error.message });
    });
    return () => { current = false; };
  }, [history, jobId, workspaceId, revision]);

  useEffect(() => {
    if (selected === undefined) return;
    let current = true;
    void history.read(selectedJob, selected)
      .then(pkg => { if (current) setPreviewResult({ key: selectedKey, data: pkg }); })
      .catch(error => { if (current) setPreviewResult({ key: selectedKey, error: error.message }); });
    return () => { current = false; };
  }, [history, selectedJob, selected, selectedKey]);

  const restore = async () => {
    if (!canRestore || !entries || selected === undefined || restoring) return;
    setRestoring(true);
    setRestoreError('');
    try { await onRestore(selected, entries.currentRevision, currentJobId, selectedJob); }
    catch (error) { setRestoreError(error instanceof Error ? error.message : 'Chưa khôi phục được bản đề.'); }
    finally { setRestoring(false); }
  };

  return <dialog ref={dialog} className="integration-editor version-history-dialog" aria-labelledby="version-history-title"
    onCancel={event => { event.preventDefault(); if (!restoring) onClose(); }}>
    <header className="editor-modal-header">
      <div className="editor-modal-heading"><h2 id="version-history-title">Lịch sử phiên bản</h2></div>
      <button type="button" className="modal-icon-close" aria-label="Đóng lịch sử phiên bản" disabled={restoring} onClick={onClose}>
        <X size={17} aria-hidden="true" />
      </button>
    </header>
    <div className="version-history-body">
      {list?.error && <p className="editor-error-box" role="alert">{list.error}</p>}
      {!list && <p role="status">Đang tải lịch sử…</p>}
      {entries && <>
        <ol className="version-history-list" aria-label="Các phiên bản đề thi">
          {entries.versions.map(item => <li key={keyFor(item)}>
            <button type="button" className="button-secondary" disabled={restoring}
              aria-pressed={selectedKey === keyFor(item)} onClick={() => { setChoice(keyFor(item)); setRestoreError(''); }}>
              <strong>Phiên bản {item.revision}</strong>
              <span>{changeLabel(item)}{keyFor(item) === currentKey ? ' · Đang dùng' : item.jobId && item.jobId !== currentJobId ? ' · Lần tạo trước' : ''}</span>
              <time dateTime={item.createdAt}>{timestamp.format(new Date(item.createdAt))}</time>
            </button>
          </li>)}
        </ol>
        <section className="version-history-preview" aria-label="Xem phiên bản đã lưu">
          {viewed?.error && <p className="editor-error-box" role="alert">{viewed.error}</p>}
          {!viewed && <p role="status">Đang tải nội dung đề…</p>}
          {preview && <ExamPaperView key={selectedKey} showPdf={false}
            questions={preview.questions} passages={preview.passages} isGenerating={false}
            examMeta={{ title: preview.title, subject: preview.subject, duration: preview.durationMinutes,
              completedCount: preview.questions.length, totalCount: preview.questions.length }} />}
        </section>
      </>}
    </div>
    {restoreError && <p className="editor-error-box" role="alert">{restoreError}</p>}
    <footer className="editor-modal-footer">
      {version && !version.restorable && <span>Phiên bản này thiếu tệp nguồn để khôi phục.</span>}
      {canRestore && <span>Bản khôi phục cần được phê duyệt lại.</span>}
      <button type="button" className="button-primary" disabled={!canRestore || restoring} onClick={() => void restore()}>
        <RotateCcw size={14} aria-hidden="true" />
        {restoring ? 'Đang khôi phục…' : 'Khôi phục phiên bản'}
      </button>
    </footer>
  </dialog>;
}
