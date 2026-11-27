import React, { useEffect, useId, useImperativeHandle, useMemo, useRef, useState } from 'react';
import { ArrowUp, CheckCircle2, Eye, FileText, ListChecks, LoaderCircle } from 'lucide-react';
import type { ExamPackage, ExamPassage, ExamPreviewState, QuestionItem, VisualWarning } from '../../../types/exam';
import {
  buildQuestionReviewSummary,
  formatQuestionLabel,
  getPrimaryReviewReason,
} from '../../../utils/questionReview.ts';
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

function questionNodeKey(question: Pick<QuestionItem, 'stableId' | 'id'>): string {
  return question.stableId?.trim() || `id:${question.id}`;
}

export type ExamPaperControls = {
  question(stableId: string): boolean;
  section(part: string): boolean;
  top(): boolean;
};

interface ExamPaperViewProps {
  controlsRef?: React.Ref<ExamPaperControls>;
  onManualPdfOpen?: () => void;
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
  onVerifyQuestion?: (questionId: number) => void;
  onApproveQuestion?: (questionId: number, reason?: string) => Promise<void> | void;
  verifyingQuestionId?: number | null;
  approvingQuestionId?: number | null;
  viewMode?: ExamCanvasViewMode;
  onViewModeChange?: (mode: ExamCanvasViewMode) => void;
  examId?: string;
  revision?: number;
  contentHash?: string;
  approved?: boolean;
  preview?: ExamPreviewState;
  warnings?: ExamPackage['warnings'];
  visualWarnings?: VisualWarning[];
  previewLog?: string;
  previewError?: string;
  previewErrorCode?: string;
  artifactChanged?: boolean;
  onRetryPreview?: () => void;
  onPreviewOpened?: () => void;
  showPdf?: boolean;
}

export const ExamPaperView: React.FC<ExamPaperViewProps> = ({
  header,
  controlsRef,
  onManualPdfOpen,
  questions,
  passages,
  examMeta,
  isGenerating,
  latestQuestionCount = 0,
  onEditQuestion,
  onVerifyQuestion,
  onApproveQuestion,
  verifyingQuestionId = null,
  approvingQuestionId = null,
  viewMode,
  onViewModeChange,
  examId,
  revision,
  contentHash,
  approved,
  preview,
  warnings,
  visualWarnings,
  previewLog,
  previewError,
  previewErrorCode,
  artifactChanged = false,
  onRetryPreview,
  onPreviewOpened,
  showPdf = true,
}) => {
  const sectionId = useId();
  const [internalMode, setInternalMode] = useState<ExamCanvasViewMode>('paper');
  const activeMode = viewMode ?? internalMode;
  const setMode = (nextMode: ExamCanvasViewMode) => {
    setInternalMode(nextMode);
    onViewModeChange?.(nextMode);
  };
  const review = activeMode === 'review';
  const [openReviewKey, setOpenReviewKey] = useState<string | null>(null);
  const reviewSummary = useMemo(
    () => buildQuestionReviewSummary(questions, warnings, visualWarnings),
    [questions, warnings, visualWarnings]
  );
  const issueCount = reviewSummary.answerIssueItems.length;
  const lastAutoRequested = useRef<string>('');
  const questionElements = useRef(new Map<string, HTMLElement>());
  const sectionElements = useRef(new Map<string, HTMLElement>());
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

  const jumpToQuestion = (key: string, openReview = false) => {
    if (openReview) setOpenReviewKey(key);
    const target = questionElements.current.get(key);
    target?.scrollIntoView({ behavior: scrollBehavior(), block: 'start' });
    return Boolean(target);
  };

  const jumpToSection = (part: string) => {
    const target = sectionElements.current.get(part);
    target?.scrollIntoView({ behavior: scrollBehavior(), block: 'start' });
    return Boolean(target);
  };

  const scrollToTop = () => {
    paperScrollRef.current?.scrollTo({ top: 0, behavior: scrollBehavior() });
    return Boolean(paperScrollRef.current);
  };
  useImperativeHandle(controlsRef, () => ({
    question: stableId => jumpToQuestion(stableId),
    section: jumpToSection,
    top: scrollToTop,
  }));

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
            <a className="button-secondary" href={preview.pdfUrl} target="_blank" rel="noreferrer" onClick={onManualPdfOpen}>
              Mở PDF trong tab mới
            </a>
          )}
        </div>

        {!!visualWarnings?.length && (
          <div className="pdf-preview-warning" role="alert">
            <strong>Cảnh báo hình vẽ / bảng biểu ({visualWarnings.length})</strong>
            <p>
              Một số câu hỏi có nhắc đến hình vẽ hoặc bảng số liệu nhưng chưa có hình minh họa kèm theo. Thầy cô xem trước kỹ trước khi duyệt xuất bản:
            </p>
            <ul>
              {visualWarnings.map((warning, index) => (
                <li key={`${warning.questionId}-${warning.code}-${index}`}>
                  Câu {warning.questionId}: {formatVisualWarning(warning.code)}
                </li>
              ))}
            </ul>
          </div>
        )}

        {artifactChanged && (
          <div className="pdf-preview-error" role="alert">
            <strong>Tệp nguồn đề thi đã thay đổi ngoài phiên làm việc</strong>
            <p>Không thể sử dụng bản xem trước hiện tại. Thầy cô vui lòng tạo lại đề mới hoặc liên hệ bộ phận kỹ thuật nếu cần kiểm tra.</p>
          </div>
        )}

        {!artifactChanged && preview?.status === 'unavailable' && previewErrorCode === 'latex_compiler_unavailable' && (
          <div className="pdf-preview-error" role="alert">
            <strong>Chưa có trình biên dịch PDF trên máy này</strong>
            <p>{previewError || 'Thầy cô vẫn có thể duyệt đề dựa trên nội dung hiển thị hoặc xuất file nguồn .tex.'}</p>
          </div>
        )}

        {!artifactChanged && preview?.status !== 'unavailable' && (!bindingMatch || preview?.status === 'queued' || preview?.status === 'compiling' || preview?.status === 'not_requested') && (
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
        {showPdf && <button type="button" aria-pressed={activeMode === 'pdf'} onClick={() => setMode('pdf')}><Eye size={14} aria-hidden="true" />Xem trước PDF</button>}
      </div>
      {issueCount > 0 && <button type="button" className="review-count" onClick={() => setMode('review')}>{issueCount} câu cần xử lý</button>}
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
            {review && questions.length > 0 && (
              <section className={`review-queue-panel ${issueCount === 0 ? 'is-clear' : ''}`} aria-label="Câu cần xử lý">
                <div className="review-queue-header">
                  <div>
                    <span className="review-queue-kicker">Rà soát từng câu</span>
                    <h3>
                      {issueCount > 0
                        ? `${issueCount} câu cần xử lý`
                        : 'Đã đối chiếu hết các câu bị gắn cờ'}
                    </h3>
                  </div>
                  <div className="review-queue-counts">
                    {reviewSummary.unapprovedMatchedItems.length > 0 && (
                      <span>{reviewSummary.unapprovedMatchedItems.length} câu khớp · chưa duyệt</span>
                    )}
                    {reviewSummary.approvedItems.length > 0 && (
                      <span>{reviewSummary.approvedItems.length} câu đã duyệt</span>
                    )}
                    {reviewSummary.sourceOrVisualQuestionCount > 0 && (
                      <span>{reviewSummary.sourceOrVisualQuestionCount} câu có lưu ý nguồn / hình</span>
                    )}
                  </div>
                </div>

                {reviewSummary.answerIssueItems.length > 0 && (
                  <ul className="review-queue-list">
                    {reviewSummary.answerIssueItems.map(item => {
                      const itemKey = questionNodeKey(item.question);
                      const writerKey = item.question.writerKey || item.question.key;
                      return (
                        <li key={itemKey} className="review-queue-item">
                          <button
                            type="button"
                            className="review-queue-row"
                            onClick={() => jumpToQuestion(itemKey, true)}
                          >
                            <div className="review-queue-row-top">
                              <strong>{item.label}</strong>
                              <span className={`question-status-badge is-${item.state.kind}`}>
                                {item.state.label}
                              </span>
                              {item.notes.length > 0 && (
                                <span className="review-queue-note-badge">
                                  Lưu ý nguồn/hình ({item.notes.length})
                                </span>
                              )}
                            </div>
                            <p className="review-queue-reason">{getPrimaryReviewReason(item.question)}</p>
                            <div className="review-queue-meta">
                              <span>Dự kiến: {writerKey}</span>
                              {item.question.solverKey && (
                                <span>Giải độc lập: {item.question.solverKey}</span>
                              )}
                              <span className="review-queue-action-hint">{item.state.primaryAction}</span>
                            </div>
                          </button>
                          {item.notes.length > 0 && (
                            <details className="review-queue-extra-notes">
                              <summary>Chi tiết lưu ý nguồn hoặc hình/bảng ({item.notes.length})</summary>
                              <ul>
                                {item.notes.map((note, idx) => (
                                  <li key={idx}>{note}</li>
                                ))}
                              </ul>
                            </details>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}

                {reviewSummary.unapprovedMatchedItems.length > 0 && (
                  <details className="review-queue-unapproved" open={issueCount === 0}>
                    <summary>
                      Danh sách câu khớp đáp án · chưa duyệt ({reviewSummary.unapprovedMatchedItems.length})
                    </summary>
                    <div className="review-queue-chips">
                      {reviewSummary.unapprovedMatchedItems.map(item => {
                        const itemKey = questionNodeKey(item.question);
                        return (
                          <button
                            key={itemKey}
                            type="button"
                            className="review-queue-chip"
                            onClick={() => jumpToQuestion(itemKey, true)}
                          >
                            <strong>{item.label}</strong>
                            <span>Chưa duyệt</span>
                          </button>
                        );
                      })}
                    </div>
                  </details>
                )}

                {issueCount === 0 && reviewSummary.unapprovedMatchedItems.length === 0 && reviewSummary.approvedItems.length > 0 && (
                  <p className="review-queue-all-approved">
                    <CheckCircle2 size={14} aria-hidden="true" />
                    <span>Tất cả câu hỏi trong đề đã được duyệt.</span>
                  </p>
                )}
              </section>
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
            const itemKey = questionNodeKey(q);
            const stableNotes = q.stableId
              ? (reviewSummary.notesByStableId[q.stableId.trim().toUpperCase()] ?? [])
              : [];
            return (
              <React.Fragment key={q.id}>
                {showPart && <h2 id={`${sectionId}-${q.part}`} className="exam-section-heading" ref={node => {
                  if (node) sectionElements.current.set(q.part!, node);
                  else sectionElements.current.delete(q.part!);
                }}>{sectionHeading(q.part!)}</h2>}
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
                  articleRef={node => {
                    if (node) {
                      questionElements.current.set(itemKey, node);
                      if (q.stableId) questionElements.current.set(q.stableId, node);
                    } else {
                      questionElements.current.delete(itemKey);
                      if (q.stableId) questionElements.current.delete(q.stableId);
                    }
                  }}
                  question={q}
                  index={i}
                  questionLabel={formatQuestionLabel(q, i)}
                  review={review}
                  reviewOpen={openReviewKey === itemKey}
                  sourceNotes={stableNotes}
                  verifying={verifyingQuestionId === q.id}
                  approving={approvingQuestionId === q.id}
                  appearing={i >= latestQuestionCount}
                  onEdit={onEditQuestion ? () => onEditQuestion(q.id) : undefined}
                  onVerify={onVerifyQuestion ? () => onVerifyQuestion(q.id) : undefined}
                  onApprove={onApproveQuestion ? reason => onApproveQuestion(q.id, reason) : undefined}
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
