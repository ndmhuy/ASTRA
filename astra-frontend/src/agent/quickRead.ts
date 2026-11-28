import type { Frame, GoalId } from './intelligence.ts';
import type { Intent } from './contracts.ts';
import utterances from '../../../src/exam_baseline/resources/agent/local-utterances.json' with { type: 'json' };
import { requestText } from './local.ts';

type Reading = { goal: GoalId; parameters: Intent['args']; act: Frame['dialogueAct'] };
const known = new Map(utterances.routes.flatMap(({examples, ...reading}) =>
  examples.map(phrase => [requestText(phrase), reading as Reading] as const)));

/** Match a whole request, so the quick path cannot consume part of a compound instruction. */
export function quickRead(text: string): Reading | undefined {
  const phrase = text.replace(/^(?:bay gio |hien tai )/, '');
  const matched = known.get(phrase) ?? known.get(phrase.replace(/[, ]+(?:nhi|vay|the|a)$/, ''));
  if (matched) return matched;
  const question = (goal: GoalId, parameters: Intent['args'] = {}): Reading =>
    ({ goal, parameters, act: 'QUESTION' });

  if (/^(?:(?:de(?: thi)?(?: nay)? )?(?:khi nao|bao gio|luc nao) (?:moi )?(?:xong|hoan tat)(?: de(?: thi)?)?|con (?:bao lau|may phut|lau khong)(?: nua)?(?: thi xong)?)$/.test(phrase)) {
    return question('READ_PROGRESS', { estimate: true });
  }
  if (/^(?:(?:may|ban|em|astra|de(?: nay)?) )?(?:dang )?(?:tao|soan|sinh|lam) (?:de(?: thi)? )?(?:toi|den) dau(?: roi)?$/.test(phrase)) {
    return question('READ_PROGRESS');
  }
  if (/^(?:(?:cai |ung dung )?app(?: nay)?|ung dung nay|astra) (?:lam duoc gi|co the lam gi|dung de lam gi|co (?:nhung )?chuc nang gi)$/.test(phrase)) {
    return question('CAPABILITY_INQUIRY');
  }
  if (/^(?:xem|mo) (?:lich su|cac phien ban)(?: (?:cua )?de(?: nay)?)?$/.test(phrase)) {
    return { goal: 'OPEN_HISTORY', parameters: {}, act: 'REQUEST' };
  }
  if (/^(?:xem|liet ke) (?:danh sach )?tai lieu(?: dinh kem)?(?: (?:cua )?de nay)?$/.test(phrase)) {
    return question('LIST_DOCUMENTS');
  }
  const views = [
    ['paper', /^(?:xem|mo)(?: lai)? (?:cai |ban )?de thi(?: (?:nay|hien tai))?$/],
    ['review', /^(?:xem|mo)(?: lai)? (?:phan |bang )?dap an(?: (?:cua )?de(?: nay)?)?$/],
    ['pdf', /^(?:xem truoc pdf|xem ban pdf|mo (?:ban xem truoc|ban pdf))$/],
  ] as const;
  const view = views.find(([, pattern]) => pattern.test(phrase))?.[0];
  if (view) return { goal: 'VIEW_EXAM', parameters: { view }, act: 'REQUEST' };
}

/** Current product overview, also used when the interpreter detects a general help question. */
export function productOverview(): string {
  return 'ASTRA giúp bạn soạn đề theo mẫu, xem và chỉnh câu hỏi hoặc đáp án, rồi duyệt và xuất đề. Bạn có thể đính kèm tài liệu và theo dõi, tạm dừng hoặc tiếp tục lượt soạn.';
}
