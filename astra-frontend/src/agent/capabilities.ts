import type { UiCapabilitySummary, UiContextSnapshot } from './contracts';

export interface CapabilityDefinition extends UiCapabilitySummary {
  validate: (params: Record<string, unknown>, context: UiContextSnapshot) => string | null;
  verify: (before: UiContextSnapshot, after: UiContextSnapshot, params: Record<string, unknown>, result?: Record<string, unknown>) => boolean;
}

const validWorkspace = (value: unknown, context: UiContextSnapshot) => typeof value === 'string' && context.sessions.some(session => session.id === value);

export const CALLABLE_CAPABILITIES: Record<string, CapabilityDefinition> = {
  'ui.navigate': {
    id: 'ui.navigate',
    description: 'Đi đến trang bắt đầu hoặc workspace đã tồn tại.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: (params, context) => params.destination === 'start' || params.destination === 'workspace' && validWorkspace(params.workspaceId, context) ? null : 'INVALID_DESTINATION',
    verify: (_before, after, params) => after.screen === params.destination && (params.destination !== 'workspace' || after.workspaceId === params.workspaceId),
  },
  'ui.session.create': {
    id: 'ui.session.create',
    description: 'Tạo và mở một workspace soạn đề mới trong giao diện.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: params => params.mode === 'custom' || params.mode === 'template' ? null : 'INVALID_MODE',
    verify: (before, after, _params, result) => after.screen === 'workspace' && typeof result?.workspaceId === 'string' && after.workspaceId === result.workspaceId && !before.sessions.some(item => item.id === result.workspaceId),
  },
  'ui.session.open': {
    id: 'ui.session.open',
    description: 'Mở chính xác một workspace hiện có.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: (params, context) => validWorkspace(params.workspaceId, context) ? null : 'WORKSPACE_NOT_FOUND',
    verify: (_before, after, params) => after.screen === 'workspace' && after.workspaceId === params.workspaceId,
  },
  'ui.exam.open_setup': {
    id: 'ui.exam.open_setup',
    description: 'Mở hộp thiết lập thật của đề Toán THPT; không tự bắt đầu tạo đề.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: () => null,
    verify: (_before, after) => after.activeModal === 'exam_setup',
  },
  'ui.exam.close_setup': {
    id: 'ui.exam.close_setup',
    description: 'Đóng hộp thiết lập đề mà không bắt đầu tạo đề.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: (_params, context) => context.activeModal === 'exam_setup' ? null : 'SETUP_NOT_OPEN',
    verify: (_before, after) => after.activeModal === null,
  },
  'ui.exam.configure_setup': {
    id: 'ui.exam.configure_setup',
    description: 'Đọc catalog thật, chọn định dạng được hỗ trợ và chuẩn bị bản tóm tắt; chưa tạo đề.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: (params, context) => {
      if (context.activeModal !== 'exam_setup') return 'SETUP_NOT_OPEN';
      if (context.setup.status !== 'ready') return 'CATALOG_NOT_READY';
      const formatId = typeof params.formatId === 'string' ? params.formatId : context.setup.selectedFormatId;
      if (!formatId || !context.setup.formats.some(format => format.id === formatId && format.available)) return 'FORMAT_UNAVAILABLE';
      return typeof params.prompt === 'string' && params.prompt.length > 1000 ? 'PROMPT_TOO_LONG' : null;
    },
    verify: (_before, after, params, result) => after.activeModal === 'exam_setup'
      && after.setup.status === 'ready'
      && after.setup.selectedFormatId === (params.formatId || after.setup.selectedFormatId)
      && result?.pendingConfirmation === 'generation',
  },
  'exam.generate.start': {
    id: 'exam.generate.start',
    description: 'Bắt đầu job tạo đề qua handler React hiện có sau xác nhận rõ ràng của giáo viên.',
    status: 'available_real', callable: true, requiresConfirmation: true,
    validate: (params, context) => {
      const pending = context.pendingConfirmation;
      if (!pending || pending.kind !== 'generation' || pending.workspaceId !== context.workspaceId) return 'CONFIRMATION_REQUIRED';
      if (params.confirmationId !== pending.id) return 'CONFIRMATION_REQUIRED';
      if (context.activeModal !== 'exam_setup' || context.setup.status !== 'ready' || !context.setup.selectedFormatId) return 'SETUP_NOT_READY';
      if (context.activeJob) return 'GENERATION_ALREADY_RUNNING';
      return null;
    },
    verify: (_before, after, _params, result) => typeof result?.jobId === 'string'
      && after.activeJob?.id === result.jobId,
  },
  'ui.exam.view_mode': {
    id: 'ui.exam.view_mode',
    description: 'Chuyển giữa trang đề, xem đáp án và xem trước PDF của đề hiện tại.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: (params, context) => !context.workspaceId
      ? 'NO_ACTIVE_WORKSPACE'
      : !['paper', 'review', 'pdf'].includes(String(params.mode))
        ? 'INVALID_VIEW_MODE'
        : params.mode !== 'paper' && !context.examId ? 'EXAM_NOT_READY' : null,
    verify: (_before, after, params) => after.viewMode === params.mode,
  },
  'ui.question.focus': {
    id: 'ui.question.focus',
    description: 'Chuyển tiêu điểm tới một câu hỏi thật đang có trong đề hiện tại.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: (params, context) => !Number.isInteger(params.questionId)
      ? 'INVALID_QUESTION'
      : !context.questions.some(question => question.id === params.questionId)
        ? 'QUESTION_NOT_FOUND' : null,
    verify: (_before, after, params) => after.selectedQuestion?.id === params.questionId,
  },
  'ui.question.open_editor': {
    id: 'ui.question.open_editor',
    description: 'Mở trình sửa câu hỏi hiện có; chưa lưu hoặc tạo lại câu hỏi.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: (params, context) => !context.examId
      ? 'EXAM_NOT_READY'
      : !Number.isInteger(params.questionId) || !context.questions.some(question => question.id === params.questionId)
        ? 'QUESTION_NOT_FOUND' : null,
    verify: (_before, after, params) => after.selectedQuestion?.id === params.questionId && after.activeModal === 'question_editor',
  },
  'ui.sidebar.set_collapsed': {
    id: 'ui.sidebar.set_collapsed',
    description: 'Thu gọn hoặc mở rộng thanh điều hướng.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: params => typeof params.collapsed === 'boolean' ? null : 'INVALID_COLLAPSED_VALUE',
    verify: (_before, after, params) => after.sidebarCollapsed === params.collapsed,
  },
  'ui.note.add': {
    id: 'ui.note.add',
    description: 'Ghi một yêu cầu chỉnh sửa để xem lại sau khi tác vụ tạo đề hoàn tất; không sửa đề đang chạy.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: (params, context) => !context.activeJob ? 'NO_ACTIVE_JOB' : typeof params.requestedChange !== 'string' || !params.requestedChange.trim() || params.requestedChange.length > 500 ? 'INVALID_NOTE' : params.targetQuestion !== undefined && (!Number.isInteger(params.targetQuestion) || Number(params.targetQuestion) < 1) ? 'INVALID_QUESTION' : null,
    verify: (before, after) => after.notes.filter(note => note.status === 'pending').length === before.notes.filter(note => note.status === 'pending').length + 1,
  },
  'ui.note.update': {
    id: 'ui.note.update',
    description: 'Cập nhật nội dung một ghi chú chỉnh sửa đang chờ.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: (params, context) => typeof params.noteId !== 'string' || !context.notes.some(note => note.id === params.noteId && note.status === 'pending') ? 'NOTE_NOT_FOUND' : typeof params.requestedChange !== 'string' || !params.requestedChange.trim() || params.requestedChange.length > 500 ? 'INVALID_NOTE' : null,
    verify: (_before, after, params) => after.notes.some(note => note.id === params.noteId && note.status === 'pending' && note.requestedChange === params.requestedChange),
  },
  'ui.note.cancel': {
    id: 'ui.note.cancel',
    description: 'Hủy một ghi chú chỉnh sửa đang chờ.',
    status: 'available_real', callable: true, requiresConfirmation: false,
    validate: (params, context) => typeof params.noteId === 'string' && context.notes.some(note => note.id === params.noteId && ['pending', 'approved', 'failed'].includes(note.status)) ? null : 'NOTE_NOT_FOUND',
    verify: (_before, after, params) => after.notes.some(note => note.id === params.noteId && note.status === 'cancelled'),
  },
  'ui.note.approve': {
    id: 'ui.note.approve',
    description: 'Duyệt một ghi chú sau khi đề hoàn tất; chưa gọi Backend revision.',
    status: 'available_real', callable: true, requiresConfirmation: true,
    validate: (params, context) => !context.examId || !context.examRevision
      ? 'EXAM_NOT_READY'
      : typeof params.noteId !== 'string' || !context.notes.some(note => note.id === params.noteId && note.status === 'pending')
        ? 'NOTE_NOT_FOUND' : null,
    verify: (_before, after, params, result) => after.notes.some(note => note.id === params.noteId && note.status === 'approved')
      && result?.pendingConfirmation === 'revision',
  },
  'exam.note.apply': {
    id: 'exam.note.apply',
    description: 'Áp dụng tuần tự một ghi chú đã duyệt qua handler regenerate câu hỏi hiện có.',
    status: 'available_real', callable: true, requiresConfirmation: true,
    validate: (params, context) => {
      const pending = context.pendingConfirmation;
      if (!pending || pending.kind !== 'revision' || pending.noteId !== params.noteId || params.confirmationId !== pending.id) return 'CONFIRMATION_REQUIRED';
      if (!context.examId || !context.examRevision || context.approved) return 'REVISION_PRECONDITION_FAILED';
      return context.notes.some(note => note.id === params.noteId && note.status === 'approved') ? null : 'NOTE_NOT_APPROVED';
    },
    verify: (before, after, params) => after.notes.some(note => note.id === params.noteId && note.status === 'applied')
      && Boolean(after.examRevision && before.examRevision && after.examRevision > before.examRevision),
  },
};

export const UI_CAPABILITY_MANIFEST: UiCapabilitySummary[] = [
  ...Object.values(CALLABLE_CAPABILITIES),
  { id: 'exam.generate.via_ui', description: 'Alias mô tả cũ; dùng ui.exam.configure_setup rồi exam.generate.start.', status: 'available_real', callable: false, requiresConfirmation: true },
  { id: 'exam.progress.stage', description: 'Xem tiến độ thật theo giai đoạn; không có phát trực tiếp đáng tin cậy theo từng câu.', status: 'available_real', callable: false, requiresConfirmation: false },
  { id: 'exam.question.edit', description: 'Sửa trực tiếp vẫn qua trình sửa; Agent có thể mở editor và áp dụng ghi chú đã duyệt bằng regenerate từng câu.', status: 'available_real', callable: false, requiresConfirmation: true },
  { id: 'exam.preview.approve', description: 'Xem trước PDF và phê duyệt đúng phiên bản trước khi xuất.', status: 'available_real', callable: false, requiresConfirmation: true },
  { id: 'exam.export', description: 'Xuất PDF, LaTeX hoặc JSON sau các điều kiện xem trước và phê duyệt.', status: 'available_real', callable: false, requiresConfirmation: true },
  { id: 'exam.export.word', description: 'Xuất Word/DOCX chưa được hỗ trợ trong phiên bản hiện tại.', status: 'unavailable', callable: false, requiresConfirmation: false },
  { id: 'exam.vact', description: 'Luồng V-ACT chưa được hỗ trợ trong giao diện hiện tại.', status: 'unavailable', callable: false, requiresConfirmation: false },
  { id: 'ui.attachment.upload', description: 'Tải và đọc tệp đính kèm chưa được hỗ trợ.', status: 'unavailable', callable: false, requiresConfirmation: false },
  { id: 'ui.web_search', description: 'Tìm web chưa có đường thực thi đã xác minh.', status: 'unavailable', callable: false, requiresConfirmation: false },
];
