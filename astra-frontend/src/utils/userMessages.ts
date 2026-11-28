const ROLE_LABELS: Record<string, string> = {
  rag: 'Đang tra cứu tài liệu tham khảo',
  composer: 'Đang soạn câu hỏi',
  illustrator: 'Đang vẽ hình minh họa',
  solver: 'Đang giải kiểm tra đáp án',
  reviewer: 'Đang rà soát toàn bộ đề thi',
};

const PART_LABELS: Record<string, string> = {
  P1: 'Phần I (Trắc nghiệm)',
  P2: 'Phần II (Đúng/Sai)',
  P3: 'Phần III (Trả lời ngắn)',
  TV: 'Tiếng Việt',
  TA: 'Tiếng Anh',
  TO: 'Toán học',
  LOGIC: 'Logic & phân tích số liệu',
  SCIENCE: 'Suy luận khoa học',
};

export function humanizeErrorMessage(message?: string, code?: string): string {
  const raw = (message || '').trim();
  if (code === 'provider_connection_failed' || code === 'provider_connect_timeout') {
    return 'Không kết nối được tới máy chủ API. Mở Kết nối AI để kiểm tra API Base URL và kết nối Internet; bản nháp vẫn được giữ.';
  }
  if (code === 'provider_not_configured' || /Configure a real EXAM_PROVIDER/i.test(raw)) {
    return 'Hệ thống chưa được kết nối dịch vụ AI. Mở Kết nối AI để nhập API key dùng chung cho chat và sinh đề.';
  }
  if (/Bad Gateway|Failed to fetch|ECONNREFUSED|\b502\b/i.test(raw)) {
    return 'Chưa kết nối được với máy chủ tạo đề. Thầy cô hãy kiểm tra cửa sổ đang chạy start.cmd rồi thử lại.';
  }
  if (/Model provider failed/i.test(raw)) {
    return 'Dịch vụ AI đang bận hoặc gặp sự cố tạm thời. Thầy cô vui lòng thử lại sau ít phút.';
  }
  if (/Generation was interrupted/i.test(raw)) {
    return 'Quá trình tạo đề bị gián đoạn do máy chủ khởi động lại. Thầy cô vui lòng bấm thử tạo lại.';
  }
  if (/Exam job not found/i.test(raw)) {
    return 'Không tìm thấy phiên tạo đề này.';
  }
  if (/Exam generation has not completed/i.test(raw)) {
    return 'Đề thi vẫn đang được soạn, chưa sẵn sàng để xem.';
  }
  if (/Connection lost/i.test(raw)) {
    return 'Kết nối với máy chủ tạm thời bị gián đoạn. Thầy cô vui lòng thử lại.';
  }
  if (/Request failed/i.test(raw)) {
    return 'Yêu cầu chưa thực hiện được. Thầy cô vui lòng thử lại.';
  }
  if (/Export failed/i.test(raw)) {
    return 'Chưa tải xuống được tệp. Thầy cô vui lòng thử lại.';
  }
  return raw || 'Có lỗi xảy ra, thầy cô vui lòng thử lại.';
}

export function formatVisualWarning(code: string): string {
  if (code.startsWith('missing_illustration_request')) {
    return 'Câu hỏi có nhắc tới hình vẽ hoặc bảng biểu nhưng chưa có hình minh họa.';
  }
  if (code.startsWith('pseudo_table')) {
    return 'Bảng số liệu chưa đúng định dạng bảng chuẩn.';
  }
  return 'Cần kiểm tra lại hình vẽ hoặc bảng biểu.';
}

export function formatProgressStatus(message?: string): string {
  const raw = (message || '').trim();
  if (!raw) return '';
  const match = raw.match(/^(rag|composer|illustrator|solver|reviewer)(?:\s*\/\s*([^/]+?))?(?:\s*\/\s*revision\s*(\d+))?$/i);
  if (!match) return raw;
  const role = match[1].toLowerCase();
  const part = match[2]?.trim();
  const revision = match[3] ? Number(match[3]) : 1;
  const base = ROLE_LABELS[role] || 'Đang xử lý đề thi';
  let partLabel: string | undefined;
  if (part && !part.startsWith('drawings_')) {
    partLabel = PART_LABELS[part] || PART_LABELS[part.split('_')[0]];
  }
  const combined = partLabel ? `${base} · ${partLabel}` : base;
  return revision > 1 ? `${combined} (lượt rà soát lại)` : combined;
}
