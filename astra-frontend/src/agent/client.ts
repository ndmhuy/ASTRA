import { parseDecision, VERSION, type AgentContext } from './contracts.ts';

export function interpretationUnavailable(reason?: string): string {
  switch (reason) {
    case 'disabled':
      return 'AI cho chat đang tắt. Thầy cô vẫn có thể nhắn “Mở cấu hình”, “Xem các mẫu đề” hoặc “Tới đâu rồi?”.';
    case 'configuration':
      return 'Kết nối AI cho chat chưa dùng được. Người quản trị cần kiểm tra cấu hình Gemini và Cloudflare AI Gateway.';
    case 'budget':
      return 'Agent đã hết ngân sách gọi AI. Các lệnh trực tiếp như “Mở cấu hình” vẫn dùng được.';
    case 'quota':
      return 'Dịch vụ AI đang giới hạn lượt gọi. Thầy cô thử lại sau hoặc dùng lệnh trực tiếp như “Mở cấu hình”.';
    case 'schema':
      return 'Kết quả từ AI chưa đọc được. Thầy cô có thể gửi một yêu cầu ngắn, ví dụ “Chọn V-ACT”.';
    default:
      return 'Kết nối AI cho chat đang chậm hoặc gián đoạn. Thầy cô thử lại sau hoặc nhắn lệnh trực tiếp.';
  }
}

export async function interpret(
  workspaceId: string, clientMessageId: string, message: string, context: AgentContext, signal: AbortSignal,
) {
  const response = await fetch('/agent/turn', {
    method: 'POST',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json', 'X-Astra-Agent': VERSION },
    body: JSON.stringify({ schemaVersion: VERSION, workspaceId, clientMessageId, message, context }),
    signal: AbortSignal.any([signal, AbortSignal.timeout(5500)]),
  });
  if (!response.ok) throw new Error(response.status === 429 ? 'agent_rate' : 'agent_unavailable');
  return parseDecision(await response.json(), clientMessageId);
}
