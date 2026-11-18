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
    validate: (params, context) => typeof params.noteId === 'string' && context.notes.some(note => note.id === params.noteId && note.status === 'pending') ? null : 'NOTE_NOT_FOUND',
    verify: (_before, after, params) => after.notes.some(note => note.id === params.noteId && note.status === 'cancelled'),
  },
};

export const UI_CAPABILITY_MANIFEST: UiCapabilitySummary[] = [
  ...Object.values(CALLABLE_CAPABILITIES),
  { id: 'exam.generate.via_ui', description: 'Thiết lập và tạo đề Toán THPT lớp 12, 22 câu, 90 phút sau xác nhận trực tiếp trong giao diện.', status: 'available_real', callable: false, requiresConfirmation: true },
  { id: 'exam.progress.stage', description: 'Xem tiến độ thật theo giai đoạn; không có phát trực tiếp đáng tin cậy theo từng câu.', status: 'available_real', callable: false, requiresConfirmation: false },
  { id: 'exam.question.edit', description: 'Sửa hoặc tạo lại từng câu sau khi đề hoàn tất bằng trình sửa của giao diện.', status: 'available_real', callable: false, requiresConfirmation: true },
  { id: 'exam.preview.approve', description: 'Xem trước PDF và phê duyệt đúng phiên bản trước khi xuất.', status: 'available_real', callable: false, requiresConfirmation: true },
  { id: 'exam.export', description: 'Xuất PDF, LaTeX hoặc JSON sau các điều kiện xem trước và phê duyệt.', status: 'available_real', callable: false, requiresConfirmation: true },
  { id: 'exam.export.word', description: 'Xuất Word/DOCX chưa được hỗ trợ trong phiên bản hiện tại.', status: 'unavailable', callable: false, requiresConfirmation: false },
  { id: 'exam.vact', description: 'Luồng V-ACT chưa được hỗ trợ trong giao diện hiện tại.', status: 'unavailable', callable: false, requiresConfirmation: false },
  { id: 'ui.attachment.upload', description: 'Tải và đọc tệp đính kèm chưa được hỗ trợ.', status: 'unavailable', callable: false, requiresConfirmation: false },
  { id: 'ui.web_search', description: 'Tìm web chưa có đường thực thi đã xác minh.', status: 'unavailable', callable: false, requiresConfirmation: false },
  { id: 'ui.question.focus', description: 'Agent chưa thể chuyển tiêu điểm tới câu hỏi cụ thể.', status: 'unavailable', callable: false, requiresConfirmation: false },
];
