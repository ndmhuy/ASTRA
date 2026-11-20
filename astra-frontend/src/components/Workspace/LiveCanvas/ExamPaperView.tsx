import React, { useEffect, useRef, useState } from 'react';
import { StationeryArt } from '../../StationeryArt';
import { SchoolArt } from '../../SchoolArt';
import { Eye, FileText, ListChecks } from 'lucide-react';
import type { ExamPreviewState, QuestionItem, VisualWarning } from '../../../types/exam';
import { QuestionCard } from './QuestionCard';

export type ExamCanvasViewMode = 'paper' | 'review' | 'pdf';

interface ExamPaperViewProps {
  header?: React.ReactNode;
  notices?: React.ReactNode;
  questions: QuestionItem[];
  examMeta: {
    title: string;
    subject: string;
    duration: number;
    completedCount: number;
    totalCount: number;
  } | null;
  isGenerating: boolean;
  latestQuestionCount?: number;
  onEditQuestion?: (questionId: number) => void;
  viewMode?: ExamCanvasViewMode;
  onViewModeChange?: (mode: ExamCanvasViewMode) => void;
  examId?: string;
  revision?: number;
  contentHash?: string;
  approved?: boolean;
  preview?: ExamPreviewState;
  visualWarnings?: VisualWarning[];
  previewLog?: string;
  previewError?: string;
  previewErrorCode?: string;
  artifactChanged?: boolean;
  onRetryPreview?: () => void;
  onPreviewOpened?: () => void;
  focusedQuestionId?: number | null;
  expandedDetails?: boolean;
}

export const ExamPaperView: React.FC<ExamPaperViewProps> = ({
  header,
  notices,
  questions,
  examMeta,
  isGenerating,
  latestQuestionCount = 0,
  onEditQuestion,
  viewMode,
  onViewModeChange,
  examId,
  revision,
  contentHash,
  approved,
  preview,
  visualWarnings,
  previewLog,
  previewError,
  previewErrorCode,
  artifactChanged = false,
  onRetryPreview,
  onPreviewOpened,
  focusedQuestionId,
  expandedDetails,
}) => {
  const [internalMode, setInternalMode] = useState<ExamCanvasViewMode>('paper');
  const activeMode = viewMode ?? internalMode;
  const setMode = (nextMode: ExamCanvasViewMode) => {
    setInternalMode(nextMode);
    onViewModeChange?.(nextMode);
  };
  const review = activeMode === 'review';
  const flaggedCount = questions.filter(q => q.status === 'FLAGGED').length;
  const lastAutoRequested = useRef<string>('');
  const bindingMatch = Boolean(
    preview &&
    revision !== undefined &&
    contentHash !== undefined &&
    preview.revision === revision &&
    preview.contentHash === contentHash
  );
  useEffect(() => {
    if (focusedQuestionId) document.getElementById(`question-${focusedQuestionId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [focusedQuestionId, activeMode]);

  useEffect(() => {
    if (activeMode !== 'pdf' || isGenerating || artifactChanged || !examId || revision === undefined || !contentHash) {
      return;
    }
    if (bindingMatch && preview?.status === 'ready') {
      onPreviewOpened?.();
      return;
    }
    const key = `${examId}:${revision}:${contentHash}`;
    if (preview?.status === 'not_requested' && bindingMatch && lastAutoRequested.current !== key) {
      lastAutoRequested.current = key;
      onRetryPreview?.();
    }
  }, [activeMode, isGenerating, artifactChanged, examId, revision, contentHash, bindingMatch, preview?.status, onPreviewOpened, onRetryPreview]);

  const renderPdfPanel = () => {
    if (!examMeta) {
      return (
        <div className="paper-empty">
          <StationeryArt kind="pencil" className="preview-pencil" />
          <StationeryArt kind="apple" className="preview-apple" />
          <span className="preview-label">02 / XEM TRƯỚC PDF</span>
          <SchoolArt kind="book" className="preview-art" />
          <h2>Chưa có đề để biên dịch PDF.</h2>
          <p>Tạo đề thi trước để xem bản PDF chuẩn mẫu LaTeX và hình vẽ TikZ.</p>
        </div>
      );
    }

    if (isGenerating) {
      return (
        <div className="pdf-preview-loading" role="status">
          <strong>Đang soạn đề thi...</strong>
          <p>Bản xem trước PDF LaTeX sẽ tự động biên dịch sau khi quá trình tạo câu hỏi hoàn tất.</p>
        </div>
      );
    }

    const isDraft = !approved || preview?.draft !== false;

    return (
      <section className="pdf-preview-panel" aria-label="Bản xem trước PDF chuẩn mẫu LaTeX">
        <div className={`pdf-preview-banner ${isDraft ? 'is-draft' : 'is-approved'}`} role="status">
          <div className="pdf-preview-banner-text">
            <strong>
              {isDraft
                ? 'Bản nháp (chờ giáo viên kiểm tra)'
                : 'Đã phê duyệt bản hiện tại'}
            </strong>
            <span>
              {revision ? ` · Phiên bản ${revision}` : ''}
              {preview?.pageCount ? ` · ${preview.pageCount} trang` : ''}
            </span>
          </div>
          {bindingMatch && preview?.status === 'ready' && !artifactChanged && (
            <a className="pdf-open-tab-link" href={preview.pdfUrl} target="_blank" rel="noreferrer">
              Mở tab mới
            </a>
          )}
        </div>

        {!!visualWarnings?.length && (
          <div className="pdf-preview-warning" role="alert">
            <strong>Cảnh báo hình vẽ / bảng biểu ({visualWarnings.length})</strong>
            <p>
              Các đề đã tạo trước đó không tự viết lại hoặc tự bịa hình vẽ trong PDF. Hãy sửa hoặc tạo lại từng câu bị ảnh hưởng kèm mô tả hình/bảng rõ ràng.
            </p>
            <ul>
              {visualWarnings.map((warning, index) => {
                const target = questions.find(q => q.stableId === warning.questionId);
                return (
                  <li key={`${warning.questionId}-${index}`}>
                    <span><code>{warning.questionId}</code>: {warning.code}</span>
                    {target && onEditQuestion && (
                      <button
                        type="button"
                        className="button-secondary"
                        onClick={() => onEditQuestion(target.id)}
                      >
                        Sửa / tạo lại câu {warning.questionId}
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {artifactChanged && (
          <div className="pdf-preview-error" role="alert">
            <strong>Nguồn LaTeX đã thay đổi ngoài phiên làm việc (`artifact_changed`)</strong>
            <p>Tệp nguồn đề thi đã bị sửa bên ngoài hệ thống, vì vậy không thể phê duyệt hoặc xuất bản hiện tại.</p>
          </div>
        )}

        {!artifactChanged && (previewErrorCode === 'latex_compiler_unavailable' || preview?.status === 'unavailable') && (
          <div className="pdf-preview-error" role="alert">
            <strong>Trình biên dịch LaTeX chưa sẵn sàng (`latex_compiler_unavailable`)</strong>
            <p>
              {previewError || 'Máy chủ chưa tìm thấy Tectonic/XeLaTeX/LuaLaTeX. Chạy scripts/install_latex_compiler.py hoặc cấu hình EXAM_LATEX_COMPILER trên backend; không cần tạo lại đề thi.'}
            </p>
            <div className="pdf-preview-meta">
              <button type="button" className="button-secondary" onClick={() => setMode('paper')}>
                Xem dạng văn bản (Đề thi)
              </button>
            </div>
          </div>
        )}

        {!artifactChanged && previewErrorCode !== 'latex_compiler_unavailable' && (!preview || !bindingMatch || preview.status === 'not_requested' || preview.status === 'queued' || preview.status === 'compiling') && (
          <div className="pdf-preview-loading" role="status">
            <strong>
              {preview?.status === 'compiling'
                ? 'Đang biên dịch PDF từ nguồn LaTeX...'
                : preview?.status === 'queued'
                  ? 'Đang xếp hàng biên dịch PDF...'
                  : 'Đang chuẩn bị bản xem trước PDF cho phiên bản hiện tại...'}
            </strong>
            <p>
              Lần biên dịch đầu tiên có thể mất thêm thời gian để tải gói TeX. Nếu quá thời gian, hệ thống sẽ cho phép thử biên dịch lại cùng nguồn đã lưu.
            </p>
            {previewError && <p role="alert">{previewError}</p>}
          </div>
        )}

        {!artifactChanged && bindingMatch && preview?.status === 'failed' && (
          <div className="pdf-preview-error" role="alert">
            <strong>Biên dịch PDF không thành công ({preview.error || previewErrorCode || 'latex_compile_failed'})</strong>
            <p>{previewError || 'Không thể biên dịch nguồn LaTeX hiện tại.'}</p>
            <div className="pdf-preview-meta">
              {onRetryPreview && (
                <button type="button" className="button-primary" onClick={onRetryPreview}>
                  Thử biên dịch lại PDF
                </button>
              )}
              {preview.logUrl && (
                <a className="button-secondary" href={preview.logUrl} target="_blank" rel="noreferrer">
                  Xem file nhật ký (`compile.log`)
                </a>
              )}
              <button type="button" className="button-secondary" onClick={() => setMode('paper')}>
                Xem dạng văn bản (Đề thi)
              </button>
            </div>
            {previewLog && <pre className="pdf-compile-log">{previewLog}</pre>}
          </div>
        )}

        {!artifactChanged && bindingMatch && preview?.status === 'ready' && (
          <div className="pdf-preview-frame-wrap">
            <iframe
              key={`${examId}:${revision}:${preview.pdfHash}`}
              title="Student exam PDF preview"
              src={preview.pdfUrl}
              className="pdf-preview-iframe"
            />
          </div>
        )}
      </section>
    );
  };

  return <>
    <div className="canvas-topbar">{header}
    <div className="paper-toolbar">
      <div className="view-switch" role="group" aria-label="Chế độ xem đề thi">
        <button aria-pressed={activeMode === 'paper'} onClick={() => setMode('paper')}><FileText size={14} aria-hidden="true" />Đề thi</button>
        <button aria-pressed={activeMode === 'review'} onClick={() => setMode('review')}><ListChecks size={14} aria-hidden="true" />Xem đáp án</button>
        <button aria-pressed={activeMode === 'pdf'} onClick={() => setMode('pdf')}><Eye size={14} aria-hidden="true" />Xem trước PDF</button>
      </div>
      {flaggedCount > 0 && <button className="review-count" onClick={() => setMode('review')}>{flaggedCount} câu cần xem xét</button>}
    </div>
    </div>
    <div className="paper-scroll">
      {notices}
      {activeMode === 'pdf' ? renderPdfPanel() : (
        <article className={`exam-paper ${!examMeta ? 'is-empty' : ''}`}>
          {examMeta ? <header className="exam-paper-heading">
            <div className="eyebrow">Đề kiểm tra · {examMeta.subject}</div>
            <h1>{examMeta.title || `Đề thi ${examMeta.subject}`}</h1>
            <p>Thời gian: {examMeta.duration} phút <span>·</span> {examMeta.totalCount} câu hỏi</p>
            {!review && <div className="student-line">Họ và tên: ................................................ <span>Lớp: ................</span></div>}
          </header> : <div className="paper-empty">
            <StationeryArt kind="pencil" className="preview-pencil" /><StationeryArt kind="apple" className="preview-apple" /><span className="preview-label">02 / TRANG ĐỀ</span><SchoolArt kind="book" className="preview-art" />
            <h2>Một trang mới,<br />chờ ý tưởng hay.</h2>
            <p>Trao đổi với ASTRA, chọn thiết lập đề, rồi xem từng câu hỏi xuất hiện tại đây.</p>
          </div>}
          {questions.map((q, i) => <div id={`question-${q.id}`} className={focusedQuestionId === q.id ? 'agent-question-focus' : ''} key={q.id}>
            {q.part && q.part !== questions[i - 1]?.part && <h2>{q.part === 'P1' ? 'Phần I. Trắc nghiệm nhiều lựa chọn' : q.part === 'P2' ? 'Phần II. Trắc nghiệm đúng/sai' : 'Phần III. Trả lời ngắn'}</h2>}
            <QuestionCard
              question={q}
              index={i}
              review={review}
              expandedDetails={expandedDetails}
              appearing={i >= latestQuestionCount}
              onOpenPdf={() => setMode('pdf')}
              onEdit={onEditQuestion ? () => onEditQuestion(q.id) : undefined}
            />
          </div>)}
          {isGenerating && <p className="paper-progress" role="status">Đang soạn câu hỏi tiếp theo…</p>}
          {questions.length > 0 && !isGenerating && <footer className="paper-end">— Hết —</footer>}
        </article>
      )}
    </div>
  </>;
};
