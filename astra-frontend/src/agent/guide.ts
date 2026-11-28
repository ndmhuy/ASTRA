import guide from '../../../src/exam_baseline/resources/agent/app-guide.json' with { type: 'json' };
import type { ExamFormat } from '../types/exam.ts';
import { familyFor, shortSubjectIntake } from './knowledge.ts';
import { fold } from './language.ts';
import { polite, requestText } from './local.ts';

export type GuideTopic = keyof typeof guide.topics;
type Stage = 'choose' | 'select' | 'details' | 'start' | 'review';
export type GuideProgress = { stage: Stage; formatId?: string };
type GuideReply = { text: string; progress?: GuideProgress };

const aliases = new Map(Object.entries(guide.topics).flatMap(([topic, card]) =>
  card.examples.map(example => [requestText(example), topic as GuideTopic] as const)));
const choices = (formats: ExamFormat[]) => formats.filter(format => format.available);
const numbered = (steps: string[]) => steps.map((step, index) => `${index + 1}. ${step}`).join('\n');

export function guideQuestion(text: string, formats: ExamFormat[]): { helpTopic: GuideTopic; subject?: string; family?: string } | undefined {
  const topic = aliases.get(text);
  if (topic) return { helpTopic: topic };
  const subject = /^(?:cach (?:tao|soan)|huong dan (?:tao|soan)|lam sao de (?:tao|soan)) de(?: thi)?(?: (.+))?$/.exec(text);
  if (!subject) return;
  if (!subject[1]) return { helpTopic: 'create' };
  const name = subject[1].replace(/ (?:nhu the nao|the nao|sao vay)$/, '');
  if (/^(?:v-?act|dgnl|danh gia nang luc)$/.test(name)) return { helpTopic: 'create', family: 'vact' };
  const known = shortSubjectIntake(name.replace(/ thpt$/, ''), formats)?.subject;
  if (known) return { helpTopic: 'create', subject: known };
}

function findFormat(raw: string, formats: ExamFormat[], family?: string) {
  const text = requestText(raw)
    .replace(/^(?:(?:minh|toi|tao|tui|em) )?chon /, '')
    .replace(/^(?:mon |mau )/, '');
  const exact = formats.find(format => fold(format.displayName) === text);
  if (exact) return exact;
  if (/^(?:v-?act|dgnl|danh gia nang luc)$/.test(text) || family === 'vact') {
    return formats.find(format => familyFor(format) === 'vact');
  }
  const subject = shortSubjectIntake(text.replace(/ thpt$/, ''), formats)?.subject;
  const matches = formats.filter(format => format.subjects.some(candidate => candidate === subject));
  return matches.length === 1 ? matches[0] : undefined;
}

export function startGuide(topic: GuideTopic, formats: ExamFormat[], subject = '', family?: string): GuideReply {
  const card = guide.topics[topic];
  if (topic !== 'create') return { text: numbered(card.steps) };
  const available = choices(formats);
  if (!available.length) {
    return { text: 'Mình chưa xem được danh sách mẫu đề lúc này. Bạn có thể mở Soạn từ mẫu để xem lại.' };
  }
  const selected = findFormat(subject, available, family);
  if (!selected) return {
    text: `${subject ? 'Mình chưa tìm thấy mẫu khớp với yêu cầu trong danh sách hiện có. ' : ''}Mình sẽ hướng dẫn bạn từng bước. Bạn muốn dùng mẫu nào?\n${available.map(format => `• ${format.displayName}`).join('\n')}\nBạn chỉ cần nhắn tên mẫu hoặc môn học.`,
    progress: { stage: 'choose' },
  };
  return {
    text: `Mẫu ${selected.displayName} có ${selected.totalQuestions} câu, ${selected.durationMinutes} phút.\n${numbered(card.steps.slice(0, 2))}\nBạn đã chọn được mẫu chưa? Nhắn “đã chọn mẫu” để mình chỉ bước tiếp theo.`,
    progress: { stage: 'select', formatId: selected.id },
  };
}

export function continueGuide(progress: GuideProgress, message: string, formats: ExamFormat[]): GuideReply | undefined {
  const text = polite(message);
  const selected = choices(formats).find(format => format.id === progress.formatId);
  if (progress.stage === 'choose') {
    const format = findFormat(text, choices(formats));
    if (format) return startGuide('create', formats, format.displayName);
  }
  if (!selected) return;
  if (progress.stage === 'select' && /^(?:minh |toi |tao )?(?:da )?chon (?:mau|de)(?: xong| roi)?$/.test(text)) {
    return {
      text: `Giữ mẫu ${selected.displayName} và xem lại số câu, thời gian. ${guide.topics.create.steps[2]}\nKhi sẵn sàng, nhắn “đã nhập yêu cầu” hoặc “dùng mẫu mặc định”.`,
      progress: { ...progress, stage: 'details' },
    };
  }
  if (progress.stage === 'details' && /^(?:da nhap yeu cau|nhap xong roi|dung mau mac dinh|giu nguyen mau|khong them gi)$/.test(text)) {
    return {
      text: `${guide.topics.create.steps[3]}\nKhi đã bấm, bạn có thể hỏi “tới đâu rồi?” để xem tiến độ.`,
      progress: { ...progress, stage: 'start' },
    };
  }
  if (progress.stage === 'start' && /^(?:da )?bam tao de(?: thi)?(?: roi)?$/.test(text)) {
    return {
      text: 'Bạn có thể theo dõi từng bước ngay trong đề. Khi app báo đã soạn xong, hãy mở Xem đáp án để kiểm tra. Bạn muốn mình chỉ cách xem lại đề hay cách tải về?',
      progress: { ...progress, stage: 'review' },
    };
  }
  if (progress.stage === 'review') {
    if (/^(?:xem (?:lai )?de|xem dap an)$/.test(text)) return startGuide('review', formats);
    if (/^(?:tai (?:de )?ve|xuat de)$/.test(text)) return startGuide('export', formats);
  }
}

export function guideContext(progress: GuideProgress, formats: ExamFormat[]) {
  return { stage: progress.stage, selected: choices(formats).find(format => format.id === progress.formatId)?.displayName };
}
