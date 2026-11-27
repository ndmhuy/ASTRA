import type { Intake } from './intake.ts';
import { MAX_ACTIONS, validIntent, type ExamIntake, type Intent, type IntentId } from './contracts.ts';
import workflows from '../../../src/exam_baseline/resources/agent/semantic-catalog.json' with { type: 'json' };

// Adapted from the legacy Agent's accent folding. Preserve the original text for data fields.
export const fold = (value: string) => value.toLocaleLowerCase('vi').replace(/đ/g, 'd')
  .normalize('NFD').replace(/\p{Mark}/gu, '').replace(/\s+/g, ' ').trim();
const command = (value: string) => fold(value).replace(/[.!]+$/, '');
const directCommand = (text: string) => text
  .replace(/^(?:astra oi[, ]+|hay |cho (?:co|thay|toi|minh|tao|t|em) )/, '')
  .replace(/ (?:giup|gium|ho) (?:co|thay|toi|minh|tao|t|em)(?: voi| nhe| nha)?$/, '')
  .replace(/ (?:voi|nhe|nha)$/, '');

export function admit(value: string): { text: string; error?: string } {
  const text = value.normalize('NFC').trim();
  if ([...text].length > 4000 || new TextEncoder().encode(text).length > 24 * 1024) {
    return { text, error: 'Tin nhắn quá dài. Thầy cô hãy chia nội dung thành từng phần dưới 4.000 ký tự.' };
  }
  if (!text || [...text].some(char => /\p{Cc}/u.test(char) && !['\n', '\r', '\t'].includes(char)) ||
      !/[\p{Letter}\p{Number}]/u.test(text) || /^(.)\1{11,}$/su.test(text)) {
    return { text, error: 'Thầy cô hãy nhập một yêu cầu ngắn để em có thể hỗ trợ.' };
  }
  return { text };
}

type Local = { text: string } | { intents: Intent[] } | { intake: ExamIntake } | { confirm: boolean };
const action = (id: IntentId, args: Intent['args'] = {}): Local => ({ intents: [{ id, args }] });

export function fastRoute(message: string): Local | undefined {
  const text = command(message);
  const direct = directCommand(text);
  if (/^(xin chao|chao( em| astra)?|hello|hi)$/.test(text)) {
    return { text: 'Em chào thầy cô! Em có thể giúp chọn mẫu đề hoặc thao tác trong ASTRA.' };
  }
  if (/^(lam|thuc hien) (cai |viec )?(nay|do|kia)( di)?$/.test(text)) {
    return { text: 'Thầy cô muốn em mở màn hình nào hoặc thao tác với đề nào? Hãy ghi tên đề hoặc số câu nếu có.' };
  }
  if (/^(cam on( em)?|thanks)$/.test(text)) return { text: 'Em sẵn sàng hỗ trợ khi thầy cô cần.' };
  if (/^(dong y|xac nhan|ok)$/.test(text)) return { confirm: true };
  if (/^(huy tac vu|huy yeu cau|thoi dung lai)$/.test(text)) return { confirm: false };
  if (/^(mo (?:phan )?(?:soan de|cau hinh|thiet lap)(?: de thi)?|mo mau de|vao (?:phan )?soan de)$/.test(direct)) return action('OPEN_SETUP');
  if (/^(tinh trang|tien do|toi dau roi|(?:tao )?de (?:toi|den) dau roi|xem (?:tinh trang|tien do)(?: tao de)?|status)[?]?$/.test(direct)) return action('STATUS');
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
  if (/^(xem (?:cac |danh sach )?mau de|co nhung mau(?: de)? nao|co khong biet chon de gi)[?]?$/.test(direct)) return action('SHOW_FORMATS');
  const format = /\b(v-act|vact|dgnl)\b/.test(text) ? 'vact' : /\bthpt\b/.test(text) ? 'thpt-math' : null;
  if (format && /^(chon|doi sang|a doi tu thpt sang) (mau )?(thpt|toan thpt|v-act|vact)( va xem chi tiet)?$/.test(direct)) {
    if (format === 'thpt-math' && !/\btoan\b/.test(direct)) return { intake: { mode: 'request', family: 'thpt' } };
    return action('SELECT_FORMAT', { format, details: direct.endsWith('chi tiet') });
  }
  if (/^(xem chi tiet mau|mo chi tiet mau)$/.test(text)) return action('FORMAT_DETAILS');
  if (/^(tao|soan) de thpt$/.test(text)) return { intake: { mode: 'request', family: 'thpt' } };
  if (format && /^(tao|soan) de (toan thpt|v-act|vact)$/.test(text)) {
    return action('PREPARE_GENERATION', { format });
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
  if (/\b(chat|hoi thoai|doan chat) (cua )?(nguoi khac|tai khoan khac)\b/.test(text)) {
    return { text: 'Em chỉ có thể tìm trong tủ đề hiện có trên trình duyệt này.' };
  }
  const rename = message.match(/^đổi tên (?:đoạn chat|cuộc trò chuyện|chat)(?: này)? thành (.{1,120})$/iu);
  if (rename) return action('RENAME', { title: rename[1] });
  const correction = message.match(/^đừng mở (?:đề|chat) [^,;]+[,;]\s*mở (?:đề|chat) ([^,;]{1,120})$/iu);
  if (correction && !/\b(roi|sau do|va mo)\b/.test(fold(correction[1]))) {
    return action('OPEN_SESSION', { title: correction[1] });
  }
  if (/^mo (?:cho (?:co|thay|toi|minh|tao|t|em) )?de (?:vua tao|gan nhat|moi nhat)(?: di)?$/.test(direct)) {
    return action('OPEN_SESSION');
  }
  const named = message.match(/^(mở|tìm) (?:chat|cuộc trò chuyện|đề) (.{1,120})$/iu);
  if (named && !/^(thi|nay|do|kia|vua roi|vua tao|gan nhat)$|\b(roi|sau do|va (xem|mo|xuat|sua|duyet))\b/.test(fold(named[2]))) {
    return action(named[1].toLocaleLowerCase('vi') === 'mở' ? 'OPEN_SESSION' : 'LIST_SESSIONS', { title: named[2] });
  }
  if (/^(co da chon (dang|mau) de nao|nhac lai mau de da chon)[?]?$/.test(text)) return action('RECALL', { what: 'format' });
  if (/^(nhac lai (nguyen van )?(yeu cau|loi nhan) (luc |ban )?dau|co noi gi luc dau)[?]?$/.test(text)) return action('RECALL', { what: 'first' });
  const editMessage = text.match(/^(sao chep|sua|thu hoi|tao nhanh tu) tin nhan (\d{1,3})$/);
  if (editMessage) {
    const operations: Record<string, string> = { 'sao chep': 'copy', sua: 'draft', 'thu hoi': 'retract', 'tao nhanh tu': 'branch' };
    return action('CHAT_MESSAGE', { operation: operations[editMessage[1]], number: Number(editMessage[2]) });
  }
  if (/^(dong (cau hinh|thiet lap)|dong mau de)$/.test(text)) return action('CLOSE_SETUP');
  if (/^(mo|liet ke|xem) (tu de|danh sach de)$/.test(text)) return action('LIST_SESSIONS');
  if (/^(ve (trang chu|man hinh bat dau)|home)$/.test(text)) return action('HOME');
  if (/^tao (workspace|khong gian soan de) moi$/.test(text)) return action('CREATE_SESSION');
  if (/^(thu gon|mo rong)( thanh dieu huong| sidebar)?$/.test(direct)) {
    return action('SET_SIDEBAR', { collapsed: direct.startsWith('thu gon') });
  }
  if (/^(?:xuat|tai) (?:de (?:thanh|sang) )?(?:word|docx)$/.test(text) ||
      /^(?:random|ngau nhien|ngan hang cau hoi|upload|tim web|tim google|huy job)$/.test(text)) {
    return { text: 'ASTRA chưa hỗ trợ thao tác này. Nhắn “Xem các mẫu đề” để xem danh mục hiện có.' };
  }
  if (/\b(ignore (previous|all)|bo qua.*(xac nhan|quyen)|export all)\b/.test(text)) {
    return { text: 'Thầy cô hãy gửi trực tiếp yêu cầu thao tác trong ASTRA.' };
  }
}

export function mayDispatch(message: string): boolean {
  const text = fold(message);
  // A correction with negation, a hypothetical, or quoted instructions needs clarification.
  return !/["“”«»`]|\b(dung|khong|chua)\s+(mo|tao|sinh|xoa|sua|xuat|tai|duyet|chon|kiem tra)\b|^(neu|gia su)\b|\bnhi[?.!]*$|\bco (?:the|ho tro|tao duoc)\b.*\bkhong[?.!]*$|\bbao nhieu\b/.test(text);
}

export type Effect = { expectedAfter?: string; status: 'succeeded' | 'accepted' | 'failed' | 'pending' | 'unknown'; text: string };
export type Receipt = Effect & { actionId: string; capability: IntentId; before: string; after: string };
export type Runtime = {
  binding(): string;
  dispatch(intent: Intent, expected: string, message?: string, messageId?: string, intake?: Intake): Promise<Effect> | Effect;
};

export async function execute(
  intents: Intent[], runtime: Runtime, binding: string, alive: () => boolean, message?: string, messageId?: string,
): Promise<Receipt[]> {
  if (!intents.length || intents.length > MAX_ACTIONS || !intents.every(validIntent)) return [];
  const signatures = intents.map(({ id, args }) => JSON.stringify([id, Object.entries(args).sort()]));
  if (new Set(signatures).size !== signatures.length) return [];
  const receipts: Receipt[] = [];
  const deadline = performance.now() + workflows.limits.executionMs;
  let expected = binding;
  for (const intent of intents) {
    if (!alive() || performance.now() >= deadline || runtime.binding() !== expected) break;
    const actionId = crypto.randomUUID();
    const operation = runtime.dispatch(intent, expected, message, messageId);
    const beforeAwait = runtime.binding();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const effect = operation instanceof Promise ? await Promise.race([
      operation,
      new Promise<Effect>(resolve => {
        timer = setTimeout(() => resolve({ status: 'unknown',
          text: 'Chưa quan sát được kết quả trong thời gian chờ. Thầy cô hãy kiểm tra trạng thái trước khi thử lại.' }),
        Math.max(0, deadline - performance.now()));
      }),
    ]).finally(() => { if (timer !== undefined) clearTimeout(timer); }) : operation;
    if (!alive()) break;
    const after = runtime.binding();
    if (operation instanceof Promise && effect.status === 'succeeded' && (effect.expectedAfter ?? beforeAwait) !== after) {
      receipts.push({ ...effect, status: 'pending', actionId, capability: intent.id, before: expected, after });
      break;
    }
    receipts.push({ ...effect, actionId, capability: intent.id, before: expected, after });
    if (import.meta.env?.VITE_AGENT_TRACE === '1') {
      console.info('[ASTRA Agent]', { intent: intent.id, instruction: intent.id, receipt: effect.status });
    }
    if (effect.status !== 'succeeded') break;
    expected = after;
  }
  return receipts;
}
