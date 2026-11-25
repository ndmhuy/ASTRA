import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowUp, Eye, FileText, ListChecks, LoaderCircle } from 'lucide-react';
import type { ExamPassage, ExamPreviewState, QuestionItem, VisualWarning } from '../../../types/exam';
import { formatVisualWarning } from '../../../utils/userMessages.ts';
import { StationeryArt } from '../../StationeryArt';
import { SchoolArt } from '../../SchoolArt';
import { MathRenderer } from '../../MathRenderer';
import { QuestionCard } from './QuestionCard';

export type ExamCanvasViewMode = 'paper' | 'review' | 'pdf';

const SECTION_HEADINGS: Record<string, string> = {
  P1: 'Phần I. Trắc nghiệm nhiều lựa chọn',
  P2: 'Phần II. Trắc nghiệm đúng/sai',
  P3: 'Phần III. Trả lời ngắn',
  TV: 'Phần 1. Sử dụng ngôn ngữ · 1.1. Tiếng Việt',
  TA: 'Phần 1. Sử dụng ngôn ngữ · 1.2. Tiếng Anh',
  TO: 'Phần 2. Toán học',
  LOGIC: 'Phần 3. Tư duy khoa học · 3.1. Logic, phân tích số liệu',
  SCIENCE: 'Phần 3. Tư duy khoa học · 3.2. Suy luận khoa học',
};

const SECTION_SHORT_LABELS: Record<string, string> = {
  P1: 'Phần I · Trắc nghiệm',
  P2: 'Phần II · Đúng/Sai',
  P3: 'Phần III · Trả lời ngắn',
  TV: 'Tiếng Việt',
  TA: 'Tiếng Anh',
  TO: 'Toán học',
  LOGIC: 'Logic & Số liệu',
  SCIENCE: 'Suy luận KH',
};

function sectionHeading(part: string): string {
  return SECTION_HEADINGS[part] || part;
}

interface ExamPaperViewProps {
  header?: React.ReactNode;
  questions: QuestionItem[];
  passages?: ExamPassage[];
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
}

export const ExamPaperView: React.FC<ExamPaperViewProps> = ({
  header,
  questions,
  passages,
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
  const paperScrollRef = useRef<HTMLDivElement>(null);
  const [showScrollTop, setShowScrollTop] = useState(false);

  const passageById = useMemo(
    () => new Map((passages || []).map(passage => [passage.id, passage])),
    [passages]
  );

  const sectionSummaries = useMemo(() => {
    const order: Array<{ part: string; label: string; count: number }> = [];
    const byPart = new Map<string, { part: string; label: string; count: number }>();
    for (const q of questions) {
      if (!q.part) continue;
      let entry = byPart.get(q.part);
      if (!entry) {
        entry = { part: q.part, label: SECTION_SHORT_LABELS[q.part] || q.part, count: 0 };
        byPart.set(q.part, entry);
        order.push(entry);
      }
      entry.count += 1;
    }
    return order;
  }, [questions]);

  const bindingMatch = Boolean(
    preview &&
    revision !== undefined &&
    contentHash !== undefined &&
    preview.revision === revision &&
    preview.contentHash === contentHash
  );

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

  const scrollBehavior = (): ScrollBehavior =>
    window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';

  const jumpToSection = (part: string) => {
    const target = document.getElementById(`exam-section-${part}`);
    target?.scrollIntoView({ behavior: scrollBehavior(), block: 'start' });
  };

  const scrollToTop = () => {
    paperScrollRef.current?.scrollTo({ top: 0, behavior: scrollBehavior() });
  };

  const renderEmptySteps = () => (
    <div className="paper-empty-steps" aria-label="Quy trình 3 bước">
      <span><strong>01</strong> Mô tả yêu cầu</span>
      <span><strong>02</strong> Chọn mẫu &amp; tạo đề</span>
      <span><strong>03</strong> Xem PDF &amp; phê duyệt</span>
    </div>
  );

  const renderPdfPanel = () => {
    if (!examMeta) {
      return (
        <div className="paper-empty">
          <StationeryArt kind="pencil" className="preview-pencil" />
          <StationeryArt kind="apple" className="preview-apple" />
          <span className="preview-label">02 / XEM TRƯỚC PDF</span>
          <SchoolArt kind="book" className="preview-art" />
          <h2>Chưa có đề để hiển thị bản in PDF.</h2>
          <p>Thầy cô hãy tạo đề thi trước để xem bản in chuẩn theo mẫu.</p>
          {renderEmptySteps()}
        </div>
      );
    }

    if (isGenerating) {
      return (
        <div className="pdf-preview-loading" role="status">
          <div className="pdf-preview-loading-row">
            <LoaderCircle className="exam-status-spinner" size={16} aria-hidden="true" />
            <strong>Đang soạn đề thi...</strong>
          </div>
          <p>Bản xem trước PDF sẽ được tạo tự động sau khi quá trình soạn câu hỏi hoàn tất.</p>
        </div>
      );
    }

    const isDraft = !approved || preview?.draft !== false;

    return (
      <section className="pdf-preview-panel" aria-label="Bản xem trước PDF theo mẫu chuẩn">
        <div className={`pdf-preview-banner ${isDraft ? 'is-draft' : 'is-approved'}`} role="status">
          <div>
            <strong>
              {isDraft
                ? 'Bản nháp — thầy cô vui lòng kiểm tra kỹ trước khi duyệt'
                : 'Đã phê duyệt bản xem trước hiện tại'}
            </strong>
            <span>
              {revision ? ` · Phiên bản ${revision}` : ''}
              {preview?.pageCount ? ` · ${preview.pageCount} trang` : ''}
            </span>
          </div>
          {bindingMatch && preview?.status === 'ready' && !artifactChanged && (
            <a className="button-secondary" href={preview.pdfUrl} target="_blank" rel="noreferrer">
              Mở PDF trong tab mới
            </a>
          )}
        </div>

        {!!visualWarnings?.length && (
          <div className="pdf-preview-warning" role="alert">
            <strong>Cảnh báo hình vẽ / bảng biểu ({visualWarnings.length})</strong>
            <p>
              Một số câu hỏi có nhắc đến hình vẽ hoặc bảng số liệu nhưng chưa có hình minh họa kèm theo. Thầy cô hãy chỉnh sửa câu hỏi để bổ sung rõ ràng.
            </p>
            <ul>
              {visualWarnings.map((warning, index) => {
                const target = questions.find(q => q.stableId === warning.questionId);
                const label = target ? `Câu ${target.id}` : warning.questionId;
                return (
                  <li key={`${warning.questionId}-${index}`}>
                    <span><strong>{label}:</strong> {formatVisualWarning(warning.code)}</span>
                    {target && onEditQuestion && (
                      <button
                        type="button"
                        className="button-secondary"
                        onClick={() => onEditQuestion(target.id)}
                      >
                        Sửa {label}
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
            <strong>Tệp đề thi đã thay đổi ngoài phiên làm việc</strong>
            <p>Nội dung đề thi đã bị chỉnh sửa bên ngoài hệ thống nên không thể phê duyệt hoặc xuất tệp từ phiên bản này.</p>
          </div>
        )}

        {!artifactChanged && (previewErrorCode === 'latex_compiler_unavailable' || preview?.status === 'unavailable') && (
          <div className="pdf-preview-error" role="alert">
            <strong>Máy chủ chưa cài đặt bộ tạo bản in PDF</strong>
            <p>
              {previewError || 'Thầy cô vẫn xem và chỉnh sửa câu hỏi bình thường ở mục Đề thi; liên hệ người phụ trách kỹ thuật nếu cần xuất file PDF.'}
            </p>
          </div>
        )}

        {!artifactChanged && previewErrorCode !== 'latex_compiler_unavailable' && (!preview || !bindingMatch || preview.status === 'not_requested' || preview.status === 'queued' || preview.status === 'compiling') && (
          <div className="pdf-preview-loading" role="status">
            <div className="pdf-preview-loading-row">
              <LoaderCircle className="exam-status-spinner" size={16} aria-hidden="true" />
              <strong>
                {preview?.status === 'compiling'
                  ? 'Đang tạo bản xem trước PDF...'
                  : preview?.status === 'queued'
                    ? 'Đang xếp hàng tạo bản xem trước PDF...'
                    : 'Đang chuẩn bị bản xem trước PDF cho phiên bản hiện tại...'}
              </strong>
            </div>
            <p>
              Lần tạo bản in đầu tiên có thể mất thêm vài chục giây. Nếu quá thời gian, thầy cô chỉ cần bấm thử lại.
            </p>
            {previewError && <p role="alert">{previewError}</p>}
          </div>
        )}

        {!artifactChanged && bindingMatch && preview?.status === 'failed' && (
          <div className="pdf-preview-error" role="alert">
            <strong>Chưa tạo được bản xem trước PDF</strong>
            <p>{previewError || 'Không thể tạo bản in PDF từ nội dung hiện tại.'}</p>
            <div className="pdf-preview-meta">
              {onRetryPreview && (
                <button type="button" className="button-primary" onClick={onRetryPreview}>
                  Thử tạo lại bản xem trước
                </button>
              )}
              {preview.logUrl && (
                <a className="button-secondary" href={preview.logUrl} target="_blank" rel="noreferrer">
                  Mở nhật ký chi tiết
                </a>
              )}
            </div>
            {previewLog && (
              <details>
                <summary>Chi tiết kỹ thuật (khi cần hỗ trợ)</summary>
                <pre className="pdf-compile-log">{previewLog}</pre>
              </details>
            )}
          </div>
        )}

        {!artifactChanged && bindingMatch && preview?.status === 'ready' && (
          <div className="pdf-preview-frame-wrap">
            <iframe
              key={`${examId}:${revision}:${preview.pdfHash}`}
              title="Student exam PDF preview"
              src={preview.pdfUrl}
              style={{ width: '100%', height: '80vh', border: 0 }}
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
        <button type="button" aria-pressed={activeMode === 'paper'} onClick={() => setMode('paper')}><FileText size={14} aria-hidden="true" />Đề thi</button>
        <button type="button" aria-pressed={activeMode === 'review'} onClick={() => setMode('review')}><ListChecks size={14} aria-hidden="true" />Xem đáp án</button>
        <button type="button" aria-pressed={activeMode === 'pdf'} onClick={() => setMode('pdf')}><Eye size={14} aria-hidden="true" />Xem trước PDF</button>
      </div>
      {flaggedCount > 0 && <button type="button" className="review-count" onClick={() => setMode('review')}>{flaggedCount} câu cần xem xét</button>}
    </div>
    </div>
    <div
      ref={paperScrollRef}
      className="paper-scroll"
      onScroll={e => setShowScrollTop(e.currentTarget.scrollTop > 360)}
    >
      {activeMode === 'pdf' ? renderPdfPanel() : (
        <article className={`exam-paper ${!examMeta ? 'is-empty' : ''}`}>
          {examMeta ? <>
            <header className="exam-paper-heading">
              <div className="eyebrow">Đề kiểm tra · {examMeta.subject}</div>
              <h1>{examMeta.title || `Đề thi ${examMeta.subject}`}</h1>
              <p>Thời gian: {examMeta.duration} phút <span>·</span> {examMeta.totalCount} câu hỏi</p>
              {!review && <div className="student-line">Họ và tên: ................................................ <span>Lớp: ................</span></div>}
            </header>
            {sectionSummaries.length >= 2 && (
              <nav className="exam-section-index" aria-label="Chuyển nhanh đến phần thi">
                {sectionSummaries.map(section => (
                  <button
                    key={section.part}
                    type="button"
                    className="exam-section-jump"
                    onClick={() => jumpToSection(section.part)}
                  >
                    <span>{section.label}</span>
                    <span className="exam-section-jump-count">{section.count}</span>
                  </button>
                ))}
              </nav>
            )}
          </> : <div className="paper-empty">
            <StationeryArt kind="pencil" className="preview-pencil" />
            <StationeryArt kind="apple" className="preview-apple" />
            <span className="preview-label">02 / TRANG ĐỀ</span>
            <SchoolArt kind="book" className="preview-art" />
            <h2>Một trang mới,<br />chờ ý tưởng hay.</h2>
            <p>Trao đổi với ASTRA, chọn thiết lập đề, rồi xem từng câu hỏi xuất hiện tại đây.</p>
            {renderEmptySteps()}
          </div>}
          {questions.map((q, i) => {
            const prev = questions[i - 1];
            const showPart = Boolean(q.part && q.part !== prev?.part);
            const showGroupInstruction = Boolean(
              q.groupInstruction && q.groupInstruction !== prev?.groupInstruction
            );
            const passage =
              q.passageId && q.passageId !== prev?.passageId
                ? passageById.get(q.passageId)
                : undefined;
            return (
              <React.Fragment key={q.id}>
                {showPart && <h2 id={`exam-section-${q.part}`} className="exam-section-heading">{sectionHeading(q.part!)}</h2>}
                {showGroupInstruction && (
                  <p className="vact-group-instruction"><strong>{q.groupInstruction}</strong></p>
                )}
                {passage && (
                  <aside className="vact-passage-card" aria-label={passage.instruction}>
                    <div className="vact-passage-instruction"><strong>{passage.instruction}</strong></div>
                    {passage.heading && (
                      <div className="vact-passage-heading">
                        <MathRenderer content={passage.heading} />
                      </div>
                    )}
                    <div className="vact-passage-body">
                      <MathRenderer content={passage.text} />
                    </div>
                    {passage.table && (
                      <div className="vact-passage-table-wrap">
                        <table className="vact-passage-table">
                          <thead>
                            <tr>
                              {passage.table.columns.map((column, columnIndex) => (
                                <th key={columnIndex}><MathRenderer content={column} /></th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {passage.table.rows.map((row, rowIndex) => (
                              <tr key={rowIndex}>
                                {row.map((cell, cellIndex) => (
                                  <td key={cellIndex}><MathRenderer content={cell} /></td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </aside>
                )}
                <QuestionCard
                  question={q}
                  index={i}
                  review={review}
                  appearing={i >= latestQuestionCount}
                  onEdit={onEditQuestion ? () => onEditQuestion(q.id) : undefined}
                />
              </React.Fragment>
            );
          })}
          {isGenerating && (
            <p className="paper-progress" role="status">
              <LoaderCircle className="exam-status-spinner" size={14} aria-hidden="true" />
              <span>Đang soạn câu hỏi tiếp theo…</span>
            </p>
          )}
          {questions.length > 0 && !isGenerating && <footer className="paper-end">— Hết —</footer>}
        </article>
      )}
    </div>
    {activeMode !== 'pdf' && showScrollTop && (
      <button
        type="button"
        className="paper-scroll-top"
        aria-label="Cuộn lên đầu đề thi"
        title="Cuộn lên đầu đề thi"
        onClick={scrollToTop}
      >
        <ArrowUp size={15} aria-hidden="true" />
        <span>Đầu trang</span>
      </button>
    )}
  </>;
};
