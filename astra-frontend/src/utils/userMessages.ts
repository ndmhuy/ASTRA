const DEFAULT_ERROR_MESSAGE = 'Hệ thống gặp trục trặc trong quá trình xử lý. Bạn vui lòng thử lại.';

const CAPABILITY_SUCCESS_MESSAGES: Record<string, string> = {
  'ui.navigate': 'Đã chuyển trang theo yêu cầu.',
  'ui.session.create': 'Đã tạo không gian soạn đề mới.',
  'ui.session.open': 'Đã mở đề thi bạn chọn.',
  'ui.session.delete': 'Đã xóa đề thi khỏi danh sách hiển thị.',
  'ui.sidebar.set_collapsed': 'Đã điều chỉnh thanh điều hướng.',
  'ui.exam.open_setup': 'Đã mở hộp thiết lập đề thi.',
  'ui.exam.close_setup': 'Đã đóng hộp thiết lập đề thi.',
  'ui.exam.configure_setup': 'Đã chuẩn bị cấu hình đề thi. Hãy xác nhận để bắt đầu tạo.',
  'exam.generate.start': 'Đã bắt đầu tạo đề thi.',
  'ui.exam.view_mode': 'Đã chuyển chế độ xem đề thi.',
  'ui.question.focus': 'Đã chuyển tới câu hỏi bạn chọn.',
  'ui.question.open_editor': 'Đã mở trình chỉnh sửa câu hỏi.',
  'ui.editor.fill': 'Đã cập nhật nội dung nháp trong trình chỉnh sửa.',
  'exam.editor.save': 'Đã lưu chỉnh sửa câu hỏi.',
  'exam.question.regenerate': 'Đã tạo lại và kiểm tra xong câu hỏi.',
  'ui.editor.close': 'Đã đóng trình chỉnh sửa câu hỏi.',
  'exam.preview.retry': 'Đã gửi yêu cầu tạo lại bản xem trước PDF.',
  'exam.approve': 'Đã phê duyệt phiên bản đề thi hiện tại.',
  'exam.export.download': 'Đã bắt đầu tải xuống tệp đề thi.',
  'ui.chat.draft': 'Đã điền nội dung vào ô nhập yêu cầu.',
  'ui.chat.restore': 'Đã khôi phục nội dung tin nhắn vào ô nhập.',
  'ui.chat.copy': 'Đã sao chép nội dung tin nhắn.',
  'ui.chat.branch': 'Đã tạo một nhánh hội thoại mới từ tin nhắn này.',
  'ui.chat.retract': 'Đã thu hồi tin nhắn theo yêu cầu.',
  'ui.note.add': 'Đã ghi nhận yêu cầu chỉnh sửa để xử lý sau khi tạo đề xong.',
  'ui.note.update': 'Đã cập nhật ghi chú chỉnh sửa.',
  'ui.note.cancel': 'Đã hủy ghi chú chỉnh sửa.',
  'ui.note.approve': 'Đã duyệt ghi chú. Hãy xác nhận để áp dụng vào câu hỏi.',
  'exam.note.apply': 'Đã áp dụng yêu cầu chỉnh sửa vào câu hỏi.',
  'ui.details.set_expanded': 'Đã cập nhật hiển thị phần chi tiết.',
  'ui.task.cancel': 'Đã hủy thao tác đang chờ xác nhận.',
  'ui.action.prepare': 'Đã chuẩn bị thao tác. Hãy xác nhận để thực hiện.',
};

function extractCodeAndMessage(errorOrMessage?: unknown, explicitCode?: string): { code: string; message: string } {
  const objectCode =
    errorOrMessage && typeof errorOrMessage === 'object' && 'code' in errorOrMessage && typeof errorOrMessage.code === 'string'
      ? errorOrMessage.code
      : '';
  const code = (explicitCode || objectCode || '').trim();
  const message =
    typeof errorOrMessage === 'string'
      ? errorOrMessage.trim()
      : errorOrMessage instanceof Error
        ? errorOrMessage.message.trim()
        : '';
  return { code, message };
}

export function formatUserError(errorOrMessage?: unknown, explicitCode?: string): string {
  const { code, message } = extractCodeAndMessage(errorOrMessage, explicitCode);
  const combined = `${code} ${message}`.trim();
  if (!combined) return DEFAULT_ERROR_MESSAGE;

  if (/^network_error$/i.test(code) || /failed to fetch|networkerror|econnrefused|load failed/i.test(combined)) {
    return 'Không thể kết nối đến hệ thống. Vui lòng kiểm tra kết nối và thử lại.';
  }
  if (/^session_expired$/i.test(code)) {
    return 'Phiên trò chuyện vừa được làm mới. Bạn vui lòng gửi lại yêu cầu.';
  }
  if (/^agent_unavailable|invalid_session$/i.test(code)) {
    return 'Trợ lý ASTRA tạm thời chưa sẵn sàng. Bạn vẫn có thể thao tác trực tiếp bằng các nút trên giao diện.';
  }
  if (/provider_not_configured|auth_error|invalid_api_key/i.test(combined) || /\b(401|403)\b/.test(combined)) {
    return 'Cấu hình dịch vụ AI chưa sẵn sàng hoặc không hợp lệ. Vui lòng kiểm tra lại thiết lập kết nối.';
  }
  if (/spend_limit_exceeded/i.test(combined)) {
    return 'Đã chạm giới hạn hạn mức sử dụng hiện tại. Vui lòng điều chỉnh hạn mức trước khi tạo thêm đề.';
  }
  if (
    /provider_unavailable|provider_http_error|provider_timeout|gemini_timeout|quota|rate_limit/i.test(combined) ||
    /\b(500|502|503|429|413)\b/.test(combined) ||
    /provider|overloaded|server error|service unavailable|timeout/i.test(combined)
  ) {
    return 'Hệ thống AI đang bận hoặc cấu hình dịch vụ gặp trục trặc tạm thời. Bạn vui lòng thử lại sau ít phút.';
  }
  if (/job_not_found/i.test(combined) || /\bnot found\b/i.test(combined)) {
    return 'Không tìm thấy phiên đề thi này. Bạn hãy mở đề khác hoặc tạo đề mới.';
  }
  if (/stale_revision/i.test(combined)) {
    return 'Nội dung đề vừa được cập nhật sang phiên bản mới hơn. Hệ thống đã tải lại bản mới nhất, bạn hãy thao tác lại.';
  }
  if (/artifact_changed|preview_artifact_changed/i.test(combined)) {
    return 'Tệp đề thi đã bị thay đổi bên ngoài ứng dụng. Vui lòng tạo lại bản xem trước trước khi phê duyệt.';
  }
  if (/latex_compiler_unavailable/i.test(combined)) {
    return 'Chưa bật tính năng tạo bản in PDF trên máy này. Bạn vẫn có thể xem và chỉnh sửa ở tab Đề thi hoặc Xem đáp án.';
  }
  if (/latex_compile_failed|latex_compile_timeout|preview_interrupted/i.test(combined)) {
    return 'Chưa thể tạo bản xem trước PDF lúc này. Bạn hãy thử tạo lại hoặc kiểm tra công thức ở tab Đề thi.';
  }
  if (/^(generation_failed|request_failed|unknown)$/i.test(code)) {
    return DEFAULT_ERROR_MESSAGE;
  }

  // Reject raw JSON payloads or purely ASCII English technical strings.
  if (message.startsWith('{') || message.startsWith('[') || /^[ -~\r\n\t]+$/.test(message)) {
    return DEFAULT_ERROR_MESSAGE;
  }

  return message || DEFAULT_ERROR_MESSAGE;
}

export function formatCapabilitySuccess(capabilityId: string): string {
  return CAPABILITY_SUCCESS_MESSAGES[capabilityId] || 'Đã thực hiện thao tác trên giao diện.';
}

export function formatVisualWarning(warning: { questionId: string; code?: string }): string {
  const idLabel = warning.questionId ? `Câu ${warning.questionId}` : 'Một câu hỏi';
  return `${idLabel} cần kiểm tra hoặc bổ sung mô tả hình vẽ/bảng biểu trước khi in.`;
}
