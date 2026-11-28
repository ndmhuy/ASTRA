/** Local configuration only. These endpoints never probe the model. */
export interface ConnectionStatus {
  managed: true;
  configured: boolean;
  model: string;
  baseUrl: string;
  setupToken: string;
  verified: boolean;
  busy: boolean;
  configurationError: string | null;
  lastFailure: { code: string; status: number | null; role: string; field: string | null; message: string } | null;
}

async function connectionRequest(init?: RequestInit): Promise<ConnectionStatus | null> {
  const response = await fetch('/api/connection', {
    ...init, cache: 'no-store', credentials: 'same-origin', signal: AbortSignal.timeout(8000),
  });
  if (response.status === 404 || response.status === 405) return null; // Explicit legacy/demo entry points.
  if (!response.ok) {
    const messages: Record<number, string> = {
      409: 'Chat hoặc sinh đề đang chạy. Hãy chờ hoàn tất hoặc dừng tác vụ trước khi đổi key.',
      422: 'Kiểm tra API key, model và URL. Key không được chứa khoảng trắng; URL dùng HTTPS.',
      403: 'Phiên cấu hình đã hết hiệu lực. Hãy tải lại trang rồi thử lại.',
      413: 'Nội dung cấu hình quá dài.',
      503: 'Chưa ghi được file .env. Kiểm tra quyền ghi thư mục ứng dụng rồi thử lại.',
    };
    throw new Error(messages[response.status] ?? 'Chưa lưu được kết nối. Cấu hình trước vẫn được giữ.');
  }
  return response.json();
}

export const readConnection = () => connectionRequest();
export const saveConnection = (status: ConnectionStatus, apiKey: string, model: string, baseUrl: string) =>
  connectionRequest({ method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Astra-Setup': status.setupToken },
    body: JSON.stringify({ apiKey: apiKey || undefined, model, baseUrl }) });
