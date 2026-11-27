import type { ExamIntake, Intent, IntentId } from './contracts.ts';
import type { ExamFormat } from '../types/exam.ts';
import { fold } from './language.ts';
import { familyFor, shortSubjectIntake } from './knowledge.ts';

export type LocalMeaning = { text: string } | { intents: Intent[] } | { intake: ExamIntake } | { confirm: boolean };
const action = (id: IntentId, args: Intent['args'] = {}): LocalMeaning => ({ intents: [{ id, args }] });
const advice = 'Tạm dừng sẽ lưu kết quả hợp lệ sau lượt gọi đang chạy; Tiếp tục chỉ làm phần còn thiếu. Dừng kết thúc lượt chạy hiện tại. Thầy cô có thể dùng các nút trên bảng tiến độ.';

export function polite(message: string) {
  let text = fold(message).replace(/[.!?]+$/, '');
  for (let pass = 0; pass < 3; pass++) {
    text = text.replace(/^(?:astra(?: oi)?[, ]+|em oi[, ]+|(?:cho|giup|gium) (?:co|thay|toi|minh|tao|tui|em) |nho em |hay |vui long |lam on )/, '')
      .replace(/(?: (?:cho|giup|gium|ho)(?: (?:co|thay|toi|minh|tao|tui|em))?(?: voi)?| (?:di|nhe|nha|voi|em))$/, '');
  }
  return text;
}

export function localMeaning(message: string): LocalMeaning | undefined {
  const text = polite(message);
  if (/^thu lai (?:ban )?xem truoc(?: pdf)?$/.test(text)) return;
  if (/^(?:dung|chua can) (?:tao|sinh) de[,;]? (?:co |toi |minh )?chi (?:muon )?xem cau truc$/.test(text)) return action('SHOW_FORMATS');
  if (/^(?:vi sao|tai sao) (?:de|phien)(?: bi)? (?:dung|tam dung|gian doan)$/.test(text)) return action('STATUS');
  if (/^(?:xem|liet ke|cho xem) (?:cac |nhung |danh sach )?(?:phien|de|cong viec) (?:dang do|tam dung|bi gian doan|co the tiep tuc)$/.test(text)) return action('RECOVERABLE_JOBS');
  const lifecycle = /\b(?:tam dung|tam nghi|chua can dung|cach dung|dung (?:tao|gen|de|cai de)|lam tiep|tiep tuc|gen tiep|tao tiep|thu lai|pause|resume|continue|retry|huy (?:job|tao de))\b/.test(text);
  if (lifecycle) {
    const negative = /đừng/iu.test(message) || /\b(?:khong|ko|chua|k)\b/.test(text);
    const hypothetical = /\b(?:neu|gia su|vi du|cach|lam sao|the nao|huong dan|co the)\b/.test(text);
    const quoted = /["“”«»`]/.test(message);
    if (negative || hypothetical || quoted || message.trim().endsWith('?')) return { text: advice };
    if (/\b(?:va|roi|sau do|dong thoi|nhung)\b/.test(text)) return { text: 'Thầy cô hãy chọn một thao tác tạm dừng, tiếp tục hoặc thử lại trước. Em chưa thay đổi phiên chạy.' };
    // Accent folding must never confuse “dừng” with the negation “đừng”.
    if (/^dung\b/.test(text) && !/dừng/iu.test(message)) return { text: '“dung” chưa rõ là dừng hay đừng. Thầy cô muốn tạm dừng phiên tạo đề phải không?' };
    const match = text.match(/^(tam dung|tam nghi|dung|pause|lam tiep|tiep tuc|gen tiep|tao tiep|resume|continue|thu lai|retry|huy job|huy tao de)(?: (.*))?$/);
    if (!match) return { text: 'Thầy cô muốn tạm dừng, tiếp tục hay thử lại phiên nào? Em chưa thay đổi công việc.' };
    const tail = (match[2] ?? '').replace(/\b(?:mot chut|mot ti|chut|ti|nua|lai)\b/g, '').trim();
    const generic = /^(?:(?:viec |cai )?(?:tao |soan |gen |lam )?(?:de(?: thi)?|cong viec|phien|bai|job|phan))?(?: (?:dang (?:tao|soan|lam)|dang do|hien tai|nay|luc nay|hom nay|vua roi|bi loi|dang bi loi|con thieu))*$/;
    const title = tail && !generic.test(tail) ? (match[1] === 'huy job' ? tail : tail.match(/^(?:cai )?(?:de|phien|job)(?: ten)? (.+)$/)?.[1]) : undefined;
    if (tail && !generic.test(tail) && !title) return { text: 'Em cần xác định đúng đề trước khi thay đổi phiên chạy. Thầy cô hãy mở đề hoặc ghi tên đề.' };
    const id: IntentId = /^(?:tam dung|tam nghi|dung|pause)$/.test(match[1]) ? 'PAUSE_GENERATION'
      : /^(?:thu lai|retry)$/.test(match[1]) ? 'RETRY_GENERATION'
      : /^huy/.test(match[1]) ? 'CANCEL_GENERATION' : 'RESUME_GENERATION';
    return action(id, title ? { title } : {});
  }
  if (/^(?:(?:nay|de) )?(?:(?:lam|tao) (?:duoc )?)?(?:toi|den) dau(?: roi)?$|^(?:de )?(?:dang )?(?:lam|tao) (?:toi|den) dau(?: roi)?$|^con (?:bao nhieu|bn) cau(?: nua)?$/.test(text)) return action('STATUS');
  if (/^(?:xem|mo) (?:cai )?de (?:gan day nhat|gan nhat|vua tao|hom nay|luc nay|hoi nay)$/.test(text)) return action('OPEN_SESSION');
  if (/^(?:mo|xem) (?:lich su|cac phien ban)(?: (?:cua )?de(?: nay)?)?$/.test(text)) return action('OPEN_HISTORY');
  if (/^(?:xuat|tai|luu|download) (?:file |de(?: thi)?(?: sang | thanh | )?)?(word|docx|markdown|md)(?: (?:cua )?de(?: nay)?)?$/.test(text)) {
    if (/đừng/iu.test(message) || /["“”«»`?]/.test(message)) return { text: 'Em chưa xuất tệp. Word và Markdown chỉ được tải sau khi phiên bản hiện tại đã được giáo viên duyệt.' };
    return action('EXPORT_DOCUMENT', { format: /\b(?:word|docx)\b/.test(text) ? 'docx' : 'md' });
  }
  if (/^(?:co (?:the )?)?(?:xuat|tai)(?: duoc)? (?:word|docx|markdown|md)(?: duoc)?(?: khong)?$/.test(text)) return { text: 'ASTRA hỗ trợ tải đề Word và Markdown sau khi thầy cô duyệt phiên bản hiện tại.' };
  if (/^(?:upload|(?:mo|xem|them|tai len|dinh kem) (?:tai lieu|tep|file)(?: (?:dau vao|tham khao))?)$/.test(text)) return { text: 'Thầy cô dùng “Đính kèm tài liệu” trên ô nhập, chọn loại tài liệu rồi chọn tệp. Tài liệu được giữ theo từng workspace; tải tệp chưa tự sinh đề.' };
  if (/^(?:tim web|tim google|tim mang|tim kiem web)$/.test(text)) return { text: 'Thầy cô bật “Tìm mạng” trong ô nhập và nêu chủ đề lân cận được hỗ trợ. Kết quả tìm kiếm chưa tự sinh đề; cần xác nhận riêng.' };
}

export function catalogCandidate(message: string) {
  const text = polite(message);
  return !/["“”«»`]/.test(message) && !/đừng/iu.test(message) &&
    /^(?:chon|doi (?:qua|sang)|xem cau truc|cau truc|co nhung mon nao|thpt .*bao nhieu cau|mon .*bao nhieu cau)/.test(text);
}

export function catalogMeaning(message: string, formats: ExamFormat[]): LocalMeaning | undefined {
  if (!catalogCandidate(message)) return;
  const text = polite(message);
  if (/\b(?:khong|chua|neu|gia su)\b/.test(text)) return;
  if (/^co nhung mon nao$/.test(text)) return { text: [...new Set(formats.filter(format => format.available).flatMap(format => format.subjects))].join(', ') };
  const mode = /cau truc|bao nhieu cau/.test(text) ? 'structure' : 'request';
  const name = text.replace(/^(?:chon|doi (?:qua|sang)|xem cau truc|cau truc)\s+(?:mau\s+)?/, '')
    .replace(/^thpt\s+/, '').replace(/\s+bao nhieu cau$/, '').replace(/\s+thpt$/, '');
  const subject = shortSubjectIntake(name, formats);
  if (!subject?.subject) return;
  const candidates = formats.filter(format => format.available && format.subjects.some(item => item === subject.subject));
  const families = [...new Set(candidates.map(familyFor).filter(Boolean))];
  if (families.length !== 1) return { text: 'Có nhiều hoặc chưa có mẫu khớp môn này. Thầy cô hãy xem danh mục mẫu đề.' };
  return { intake: { ...subject, mode, family: families[0] } };
}
