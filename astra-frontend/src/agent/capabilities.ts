import type { UiCapabilitySummary, UiContextSnapshot } from './contracts';
import { confirmationValid, stableValue } from './confirmation.ts';

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
      if (params.confirmationId !== pending.id || !confirmationValid(context)) return 'CONFIRMATION_REQUIRED';
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
    validate: (params, context) => !context.activeJob && !context.examId ? 'NO_ACTIVE_EXAM' : typeof params.requestedChange !== 'string' || !params.requestedChange.trim() || params.requestedChange.length > 500 ? 'INVALID_NOTE' : params.targetQuestion !== undefined && (!Number.isInteger(params.targetQuestion) || Number(params.targetQuestion) < 1) ? 'INVALID_QUESTION' : null,
    verify: (_before, after, params, result) => after.notes.some(note => note.id === result?.noteId && note.requestedChange === String(params.requestedChange).trim()),
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
      if (!pending || pending.kind !== 'revision' || pending.noteId !== params.noteId || params.confirmationId !== pending.id || !confirmationValid(context)) return 'CONFIRMATION_REQUIRED';
      if (!context.examId || !context.examRevision || context.approved) return 'REVISION_PRECONDITION_FAILED';
      return context.notes.some(note => note.id === params.noteId && note.status === 'approved') ? null : 'NOTE_NOT_APPROVED';
    },
    verify: (before, after, params) => after.notes.some(note => note.id === params.noteId && note.status === 'applied')
      && Boolean(after.examRevision && before.examRevision && after.examRevision > before.examRevision),
  },
};

const ACTION_PARAMETERS: Record<string, Record<string, unknown>> = {
  'ui.navigate': { destination: ['start', 'workspace'], workspaceId: 'existing session id when destination=workspace' },
  'ui.session.create': { mode: ['custom', 'template'] },
  'ui.session.open': { workspaceId: 'exact id from sessions' },
  'ui.exam.open_setup': {},
  'ui.exam.close_setup': {},
  'ui.exam.configure_setup': { formatId: 'available setup.formats id', prompt: 'teacher instructions, optional string' },
  'exam.generate.start': { confirmationId: 'React supplies only after explicit teacher confirmation' },
  'ui.exam.view_mode': { mode: ['paper', 'review', 'pdf'], meanings: { paper: 'exam questions', review: 'answers and solutions / đáp án, lời giải', pdf: 'PDF preview' } },
  'ui.question.focus': { questionId: 'integer id from questions; preserves current view mode' },
  'ui.question.open_editor': { questionId: 'integer id from questions' },
  'ui.sidebar.set_collapsed': { collapsed: 'boolean' },
  'ui.note.add': { targetQuestion: 'optional integer question id', requestedChange: 'nonempty string, max 500 characters' },
  'ui.note.update': { noteId: 'exact id from notes', requestedChange: 'nonempty string, max 500 characters' },
  'ui.note.cancel': { noteId: 'exact id from notes' },
  'ui.note.approve': { noteId: 'exact pending note id' },
  'exam.note.apply': { noteId: 'exact approved note id', confirmationId: 'React supplies after explicit teacher confirmation' },
};

const EXTRA_ACTIONS: Record<string, { description: string; params: Record<string, unknown>; validate: CapabilityDefinition['validate']; verify: CapabilityDefinition['verify']; consequential?: boolean }> = {
  'ui.details.set_expanded': { description: 'Expand/collapse question solutions/TikZ disclosures or source-warning details. Use review mode first for solutions.', params: { group: ['questions','warnings'], expanded: 'boolean' }, validate: (p,c) => !c.examId ? 'EXAM_NOT_READY' : !['questions','warnings'].includes(String(p.group)) || typeof p.expanded !== 'boolean' ? 'INVALID_DISCLOSURE' : null, verify: (_b,_a,_p,r) => r?.disclosureUpdated === true },
  'ui.chat.restore': { description: 'Restore an existing user message into the composer for editing, without sending.', params: { messageId: 'exact user message id' }, validate: (p,c) => c.messages?.some(m => m.id === p.messageId && m.role === 'user') ? null : 'MESSAGE_NOT_FOUND', verify: (_b,a,_p,r) => typeof r?.draftText === 'string' && a.composerDraft === r.draftText },
  'ui.chat.copy': { description: 'Copy an existing chat message to the local clipboard.', params: { messageId: 'exact id from messages' }, validate: (p,c) => c.messages?.some(m => m.id === p.messageId) ? null : 'MESSAGE_NOT_FOUND', verify: (_b,_a,_p,r) => r?.clipboardAcknowledged === true },
  'ui.editor.fill': { description: 'Fill the open question editor draft; does not save.', params: { patch: 'object with only stem, key, explanation, choices or statements matching the existing question type' }, validate: (p,c) => c.activeModal !== 'question_editor' ? 'EDITOR_NOT_OPEN' : !p.patch || typeof p.patch !== 'object' || Object.keys(p.patch).some(k => !['stem','key','explanation','choices','statements'].includes(k)) ? 'INVALID_PATCH' : null, verify: (_b,_a,_p,r) => r?.draftUpdated === true },
  'exam.editor.save': { description: 'Save the reviewed editor draft after confirmation.', params: {}, consequential: true, validate: (_p,c) => c.activeModal === 'question_editor' && c.examRevision ? null : 'EDITOR_NOT_OPEN', verify: (b,a) => Boolean(a.examRevision && b.examRevision && a.examRevision > b.examRevision) },
  'exam.question.regenerate': { description: 'Regenerate a question using the existing React service after confirmation.', params: { questionId: 'integer from questions', instruction: 'nonempty string up to 4000 characters' }, consequential: true, validate: (p,c) => !c.examRevision || c.activeJob || !c.questions.some(q => q.id === p.questionId) ? 'QUESTION_NOT_READY' : typeof p.instruction !== 'string' || !p.instruction.trim() || p.instruction.length > 4000 ? 'INVALID_INSTRUCTION' : null, verify: (b,a) => Boolean(a.examRevision && b.examRevision && a.examRevision > b.examRevision) },
  'ui.editor.close': { description: 'Close the question editor without saving.', params: {}, validate: (_p,c) => c.activeModal === 'question_editor' ? null : 'EDITOR_NOT_OPEN', verify: (_b,a) => a.activeModal !== 'question_editor' },
  'ui.task.cancel': { description: 'Cancel the pending Agent task/confirmation, not a Backend generation job.', params: {}, validate: () => null, verify: (_b,a) => !a.pendingConfirmation },
  'ui.chat.draft': { description: 'Fill the chat composer without sending.', params: { text: 'string, max 4000 characters' }, validate: (p,c) => !c.workspaceId ? 'NO_ACTIVE_WORKSPACE' : typeof p.text !== 'string' || p.text.length > 4000 ? 'INVALID_DRAFT' : null, verify: (_b,a,p) => a.composerDraft === p.text },
  'ui.chat.branch': { description: 'Create and open a conversation branch at an existing message.', params: { messageId: 'exact id from messages' }, validate: (p,c) => c.messages?.some(m => m.id === p.messageId) ? null : 'MESSAGE_NOT_FOUND', verify: (b,a,_p,r) => a.workspaceId !== b.workspaceId && a.workspaceId === r?.workspaceId },
  'ui.chat.retract': { description: 'Remove a user message and later messages after confirmation.', params: { messageId: 'exact user message id' }, consequential: true, validate: (p,c) => c.messages?.some(m => m.id === p.messageId && m.role === 'user') ? null : 'MESSAGE_NOT_FOUND', verify: (_b,a,p) => !a.messages?.some(m => m.id === p.messageId) },
  'ui.session.delete': { description: 'Delete a local workspace after confirmation.', params: { workspaceId: 'exact session id' }, consequential: true, validate: (p,c) => validWorkspace(p.workspaceId,c) ? null : 'WORKSPACE_NOT_FOUND', verify: (_b,a,p) => !a.sessions.some(s => s.id === p.workspaceId) },
  'exam.preview.retry': { description: 'Request/retry PDF compilation using the existing preview service.', params: {}, validate: (_p,c) => c.examId && !c.activeJob ? null : 'EXAM_NOT_READY', verify: (_b,_a,_p,r) => r?.previewRequested === true },
  'exam.approve': { description: 'Approve the current revision after reviewing its matching PDF and explicit confirmation.', params: {}, consequential: true, validate: (_p,c) => c.examId && c.preview?.status === 'ready' && c.preview.opened && c.preview.revision === c.examRevision && !c.approved ? null : 'PREVIEW_REVIEW_REQUIRED', verify: (_b,a) => a.approved },
  'exam.export.download': { description: 'Download approved student PDF/LaTeX or teacher answer JSON after confirmation.', params: { type: ['STUDENT_EXAM','TEACHER_KEY'], format: ['pdf','tex','json'] }, consequential: true, validate: (p,c) => !c.approved ? 'APPROVAL_REQUIRED' : !((p.type === 'STUDENT_EXAM' && ['pdf','tex'].includes(String(p.format))) || (p.type === 'TEACHER_KEY' && p.format === 'json')) ? 'INVALID_EXPORT' : p.format === 'pdf' && c.preview?.status !== 'ready' ? 'PREVIEW_NOT_READY' : null, verify: (_b,_a,_p,r) => r?.downloadDispatched === true },
  'ui.action.prepare': { description: 'Present a confirmation for a consequential action; performs no business mutation.', params: { capabilityId: 'consequential capability id', actionParams: 'parameters for that action' }, validate: (p,c) => { const d = EXTRA_ACTIONS[String(p.capabilityId)]; return !d?.consequential ? 'INVALID_CONFIRMATION_ACTION' : d.validate((p.actionParams || {}) as Record<string,unknown>,c); }, verify: (_b,a,_p,r) => a.pendingConfirmation?.id === r?.confirmationId },
};
for (const [id, spec] of Object.entries(EXTRA_ACTIONS)) {
  ACTION_PARAMETERS[id] = spec.params;
  CALLABLE_CAPABILITIES[id] = {
    id, description: spec.description, status: 'available_real', callable: true,
    requiresConfirmation: Boolean(spec.consequential),
    validate: (p,c) => {
      if (spec.consequential) {
        const pending = c.pendingConfirmation;
        if (!pending || pending.capabilityId !== id || pending.id !== p.confirmationId || !confirmationValid(c)) return 'CONFIRMATION_REQUIRED';
        const { confirmationId: _id, ...args } = p;
        if (stableValue(args) !== stableValue(pending.params || {})) return 'CONFIRMATION_MISMATCH';
      }
      return spec.validate(p,c);
    }, verify: spec.verify,
  };
}

for (const [id, definition] of Object.entries(CALLABLE_CAPABILITIES)) {
  definition.parameterSchema = ACTION_PARAMETERS[id];
}

export function capabilityCatalog(context: Omit<UiContextSnapshot, 'stateVersion' | 'capabilities'>): UiCapabilitySummary[] {
  return UI_CAPABILITY_MANIFEST.map(item => {
    if (!item.callable) return { ...item, availability: item.status === 'unavailable' ? 'UNSUPPORTED' : 'SUPPORTED_BUT_UNAVAILABLE_NOW' };
    let reason: string | undefined;
    if (item.id.startsWith('ui.question.') && !context.questions.length) reason = 'EXAM_NOT_READY';
    if (['exam.approve', 'exam.export.download', 'exam.preview.retry', 'ui.exam.view_mode'].includes(item.id) && !context.examId) reason = 'EXAM_NOT_READY';
    if (item.id === 'ui.exam.configure_setup' && context.setup.status !== 'ready') reason = 'CATALOG_NOT_READY';
    if (item.id === 'ui.note.add' && !context.activeJob && !context.examId) reason = 'NO_ACTIVE_EXAM';
    if (['ui.editor.fill','ui.editor.close','exam.editor.save'].includes(item.id) && context.activeModal !== 'question_editor') reason = 'EDITOR_NOT_OPEN';
    if (item.id === 'ui.exam.close_setup' && context.activeModal !== 'exam_setup') reason = 'SETUP_NOT_OPEN';
    if (item.id === 'exam.approve' && context.examId && (!context.preview?.opened || context.preview.status !== 'ready')) reason = 'PREVIEW_REVIEW_REQUIRED';
    if (item.id === 'exam.export.download' && context.examId && !context.approved) reason = 'APPROVAL_REQUIRED';
    if (item.id === 'exam.generate.start' && context.activeJob) reason = 'GENERATION_ALREADY_RUNNING';
    if (item.id === 'ui.note.approve' && !context.notes.some(n => n.status === 'pending')) reason = 'NOTE_NOT_FOUND';
    if (item.id === 'exam.note.apply' && !context.notes.some(n => n.status === 'approved')) reason = 'NOTE_NOT_APPROVED';
    return { ...item, availability: reason ? 'SUPPORTED_BUT_UNAVAILABLE_NOW' : item.requiresConfirmation ? 'REQUIRES_CONFIRMATION' : 'SUPPORTED_AND_AVAILABLE', ...(reason ? { unavailableReason: reason } : {}) };
  });
}

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
