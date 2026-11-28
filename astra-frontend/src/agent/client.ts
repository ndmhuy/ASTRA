import type { WebResearchResult } from '../types/exam.ts';
import { parseDecision, VERSION, type AgentContext } from './contracts.ts';
import { parseCanonical } from './intelligence.ts';

export function interpretationUnavailable(reason?: string): string {
  switch (reason) {
    case 'disabled':
      return 'AI cho chat đang tắt. Thầy cô vẫn có thể nhắn “Mở cấu hình”, “Xem các mẫu đề” hoặc “Tới đâu rồi?”.';
    case 'configuration':
      return 'Kết nối AI cho chat chưa dùng được. Người quản trị cần kiểm tra cấu hình dịch vụ AI.';
    case 'budget':
      return 'Agent đã hết ngân sách gọi AI. Các lệnh trực tiếp như “Mở cấu hình” vẫn dùng được.';
    case 'auth':
      return 'Dịch vụ AI từ chối thông tin xác thực. Người quản trị kiểm tra token và khóa đã lưu trên gateway.';
    case 'model':
      return 'Không tìm thấy model AI trên cấu hình hiện tại. Người quản trị kiểm tra tên model và đường dẫn gateway.';
    case 'timeout':
      return 'Dịch vụ AI chưa trả lời trong thời gian chờ. Yêu cầu chưa được thực hiện.';
    case 'rejected':
      return 'Dịch vụ AI từ chối yêu cầu. Người quản trị kiểm tra cấu hình gateway và định dạng phản hồi.';
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
    headers: { 'Content-Type': 'application/json', 'X-Astra-Agent': VERSION, 'X-Astra-Semantic': 'astra-semantic-v3' },
    body: JSON.stringify({ schemaVersion: VERSION, workspaceId, clientMessageId, message, context }),
    signal: AbortSignal.any([signal, AbortSignal.timeout(38000)]),
  });
  if (!response.ok) throw new Error(response.status === 429 ? 'agent_rate' : 'agent_unavailable');
  const result = await response.json();
  if (result.schemaVersion === 'astra-semantic-v3') {
    if (result.clientMessageId !== clientMessageId || !['astra-semantic-v1','astra-semantic-v3'].includes(result.sourceContract) || Object.keys(result).some(key => !['schemaVersion', 'clientMessageId', 'frame','sourceContract'].includes(key))) throw new Error('agent_semantic_contract');
    return parseCanonical(result.frame);
  }
  // A legacy non-action/unavailable envelope is allowed; an old semantic envelope
  // is not silently treated as V3. The backend must negotiate the bridge explicitly.
  if(result.schemaVersion === 'astra-semantic-v1') throw new Error('agent_contract_upgrade_required');
  return parseDecision(result, clientMessageId);
}

export async function researchAdjacentTopic(
  workspaceId: string,
  clientMessageId: string,
  adjacentTopicId: string,
  message: string,
  options: { count?: number; minutes?: number },
  signal: AbortSignal,
): Promise<WebResearchResult> {
  const response = await fetch('/agent/research', {
    method: 'POST',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json', 'X-Astra-Agent': VERSION },
    body: JSON.stringify({
      schemaVersion: 'astra-web-research-v1',
      workspaceId,
      clientMessageId,
      adjacentTopicId,
      message,
      ...(options.count !== undefined ? { count: options.count } : {}),
      ...(options.minutes !== undefined ? { minutes: options.minutes } : {}),
    }),
    signal: AbortSignal.any([signal, AbortSignal.timeout(15000)]),
  });
  if (!response.ok) throw new Error(response.status === 422 ? 'agent_research_unsupported' : 'agent_unavailable');
  return await response.json() as WebResearchResult;
}
