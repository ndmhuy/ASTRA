import { MAX_ACTIONS, validIntent, type Intent, type IntentId } from './contracts.ts';

// Adapted from the legacy Agent's accent folding. Preserve the original text for data fields.
export const fold = (value: string) => value.toLocaleLowerCase('vi').replace(/đ/g, 'd')
  .normalize('NFD').replace(/\p{Mark}/gu, '').replace(/\s+/g, ' ').trim();
const command = (value: string) => fold(value).replace(/[.!]+$/, '');

export function admit(value: string): { text: string; error?: string } {
  const text = value.normalize('NFC').trim();
  if ([...text].length > 4000 || new TextEncoder().encode(text).length > 24 * 1024) {
    return { text, error: 'Tin nhắn quá dài. Thầy cô hãy chia nội dung thành từng phần dưới 4.000 ký tự.' };
  }
  if (!text || /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/u.test(text) ||
      !/[\p{Letter}\p{Number}]/u.test(text) || /^(.)\1{11,}$/su.test(text)) {
    return { text, error: 'Thầy cô hãy nhập một yêu cầu ngắn để em có thể hỗ trợ.' };
  }
  return { text };
}

type Local = { text: string } | { intents: Intent[] } | { confirm: boolean };
const action = (id: IntentId, args: Intent['args'] = {}): Local => ({ intents: [{ id, args }] });

export function fastRoute(message: string): Local | undefined {
  const text = command(message);
  if (/^(xin chao|chao( em| astra)?|hello|hi)$/.test(text)) {
    return { text: 'Em chào thầy cô! Em có thể giúp chọn mẫu đề hoặc thao tác trong ASTRA.' };
  }
  if (/^(cam on( em)?|thanks)$/.test(text)) return { text: 'Em sẵn sàng hỗ trợ khi thầy cô cần.' };
  if (/^(dong y|xac nhan|ok)$/.test(text)) return { confirm: true };
  if (/^(huy tac vu|huy yeu cau|thoi dung lai)$/.test(text)) return { confirm: false };
  if (/^(mo( phan)? (soan de|cau hinh|thiet lap)( giup co)?|mo mau de)$/.test(text)) return action('OPEN_SETUP');
  if (/^(tinh trang|tien do|toi dau roi|de toi dau roi|status)[?]?$/.test(text)) return action('STATUS');
  if (/^(xem dap an|review)$/.test(text)) return action('SET_VIEW', { view: 'review' });
  if (/^(xem de thi|mo de thi)$/.test(text)) return action('SET_VIEW', { view: 'paper' });
  if (/^(xem truoc pdf|mo ban xem truoc|preview pdf)$/.test(text)) return action('SET_VIEW', { view: 'pdf' });
  if (/^(xem canh bao|canh bao)$/.test(text)) return action('WARNINGS');
  if (/^(cuon len dau de|dau trang)$/.test(text)) return action('SCROLL_TOP');
  const question = text.match(/^(xem dap an|den|mo chinh sua|kiem tra lai dap an) cau (\d{1,3})(?: phan ([\w -]{1,25}))?$/);
  if (question) {
    const target = { number: Number(question[2]), ...(question[3] ? { part: question[3] } : {}) };
    if (question[1] === 'mo chinh sua') return action('OPEN_EDITOR', target);
    if (question[1] === 'kiem tra lai dap an') return action('VERIFY_QUESTION', target);
    return action('FOCUS_QUESTION', { ...target, ...(question[1] === 'xem dap an' ? { view: 'review' } : {}) });
  }
  if (/^(xem (cac )?mau de|co nhung mau nao|co khong biet chon de gi)[?]?$/.test(text)) return action('SHOW_FORMATS');
  const format = /\b(v-act|vact|dgnl)\b/.test(text) ? 'vact' : /\bthpt\b/.test(text) ? 'thpt-math' : null;
  if (format && /^(chon|doi sang|a doi tu thpt sang) (mau )?(thpt|toan thpt|v-act|vact)( va xem chi tiet)?$/.test(text)) {
    return action('SELECT_FORMAT', { format, details: text.endsWith('chi tiet') });
  }
  if (/^(xem chi tiet mau|mo chi tiet mau)$/.test(text)) return action('FORMAT_DETAILS');
  if (format && /^(tao|soan) de (toan )?(thpt|v-act|vact)(?: chuyen de:? [\p{Letter}\p{Number} ,_-]+)?(?: \d+ cau)?(?:,? \d+ phut)?$/u.test(text)) {
    const topic = message.match(/(?:chuyên đề|chuyen de):?\s+(.+?)(?=\s+\d+\s+câu|$)/iu)?.[1];
    if (text.includes('chuyen de') && !topic) return { text: 'Thầy cô muốn tập trung vào chuyên đề nào?' };
    return action('PREPARE_GENERATION', { format, ...(topic ? { topic: topic.replace(/[.!]$/, '') } : {}) });
  }
  if (/^(tao de|soan de|tao de toan 12|tao lai de)$/.test(text)) return action('PREPARE_GENERATION');
  const note = message.match(/^(?:ghi chú sửa|sửa) câu (\d{1,3})(?: phần ([a-z0-9]+))?\s+(.{2,300})$/iu);
  if (note) return action('ADD_NOTE', { number: Number(note[1]), ...(note[2] ? { part: note[2] } : {}), instruction: note[3] });
  const cancel = text.match(/^(?:a )?(?:thoi cau|bo ghi chu cau) (\d{1,3})(?: phan ([a-z0-9]+))?(?: giu nguyen)?$/);
  if (cancel) return action('CANCEL_NOTE', { number: Number(cancel[1]), ...(cancel[2] ? { part: cancel[2] } : {}) });
  if (/^(phe duyet|duyet de|phe duyet ban nay)$/.test(text)) return action('APPROVE');
  const exportFormat = text.match(/^(?:xuat|tai) (pdf|tex|json)$/)?.[1];
  if (exportFormat) return action('EXPORT', { format: exportFormat });
  if (/^(thu lai|tao lai) (ban )?xem truoc( pdf)?$/.test(text)) return action('RETRY_PREVIEW');
  if (/^(xem|liet ke) ghi chu$/.test(text)) return action('REVIEW_NOTES');
  if (/^(ap dung|sua theo) ghi chu$/.test(text)) return action('APPLY_NOTES');
  if (/^(dong (cau hinh|thiet lap)|dong mau de)$/.test(text)) return action('CLOSE_SETUP');
  if (/^(mo|liet ke|xem) (tu de|danh sach de)$/.test(text)) return action('LIST_SESSIONS');
  if (/^(ve (trang chu|man hinh bat dau)|home)$/.test(text)) return action('HOME');
  if (/^tao (workspace|khong gian soan de) moi$/.test(text)) return action('CREATE_SESSION');
  if (/^(mo de (vua tao|gan nhat)|mo cho co de vua tao di)$/.test(text)) return action('OPEN_SESSION');
  if (/^(thu gon|mo rong)( thanh dieu huong| sidebar)?$/.test(text)) {
    return action('SET_SIDEBAR', { collapsed: text.startsWith('thu gon') });
  }
  if (/\b(word|docx|random|ngau nhien|ngan hang cau hoi|upload|tim web|tim google|huy job)\b/.test(text)) {
    return { text: 'ASTRA hiện hỗ trợ mẫu Toán THPT và V-ACT, cùng xuất PDF, tệp nguồn TEX và đáp án JSON sau khi duyệt. Tính năng thầy cô yêu cầu chưa có.' };
  }
  if (/\b(ignore (previous|all)|bo qua.*(xac nhan|quyen)|export all)\b/.test(text)) {
    return { text: 'Thầy cô hãy gửi trực tiếp yêu cầu thao tác trong ASTRA.' };
  }
  if (/^(neu\b|lam sao\b|huong dan\b)|\b(phai lam sao|la gi|nhu the nao)\b/.test(text)) {
    return { text: 'Thầy cô có thể chọn mẫu Toán THPT hoặc V-ACT, xác nhận tạo đề, kiểm tra đề và bản PDF, rồi duyệt để tải tệp.' };
  }
  if (/\b(thoi tiet|du bao thoi tiet)\b/.test(text)) {
    return { text: 'Em hỗ trợ soạn, kiểm tra và quản lý đề thi trong ASTRA.' };
  }
}

export function mayDispatch(message: string): boolean {
  const text = fold(message);
  // A correction with negation, a hypothetical, or quoted instructions needs clarification.
  return !/["“”«»`]|\b(dung|khong|chua)\s+(mo|tao|sinh|xoa|sua|xuat|tai|duyet|chon|kiem tra)\b|^(neu|gia su)\b|\bnhi[?.!]*$/.test(text);
}

export type Effect = { expectedAfter?: string; status: 'succeeded' | 'accepted' | 'failed' | 'pending' | 'unknown'; text: string };
export type Receipt = Effect & { actionId: string; capability: IntentId; before: string; after: string };
export type Runtime = {
  binding(): string;
  dispatch(intent: Intent, expected: string, message?: string, messageId?: string): Promise<Effect> | Effect;
};

export async function execute(
  intents: Intent[], runtime: Runtime, binding: string, alive: () => boolean, message?: string, messageId?: string,
): Promise<Receipt[]> {
  if (!intents.length || intents.length > MAX_ACTIONS || !intents.every(validIntent)) return [];
  const signatures = intents.map(({ id, args }) => JSON.stringify([id, Object.entries(args).sort()]));
  if (new Set(signatures).size !== signatures.length) return [];
  const receipts: Receipt[] = [];
  let expected = binding;
  for (const intent of intents) {
    if (!alive() || runtime.binding() !== expected) break;
    const actionId = crypto.randomUUID();
    const operation = runtime.dispatch(intent, expected, message, messageId);
    const beforeAwait = runtime.binding();
    const effect = operation instanceof Promise ? await operation : operation;
    if (!alive()) break;
    const after = runtime.binding();
    if (operation instanceof Promise && effect.status === 'succeeded' && (effect.expectedAfter ?? beforeAwait) !== after) {
      receipts.push({ ...effect, status: 'pending', actionId, capability: intent.id, before: expected, after });
      break;
    }
    receipts.push({ ...effect, actionId, capability: intent.id, before: expected, after });
    if (effect.status !== 'succeeded') break;
    expected = after;
  }
  return receipts;
}
