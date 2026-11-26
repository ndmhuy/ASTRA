import type { ExamSession } from '../state/examSessions.ts';
import type { ChatMessage } from '../types/exam.ts';
import { fold } from './recipes.ts';

export type Conversation = {
  schemaVersion: 1;
  revision: number;
  updatedAt: string;
  titleOrigin: 'default' | 'auto' | 'manual' | 'legacy';
  titleSourceId?: string;
  titleQuality?: number;
};

export function conversationFor(session: ExamSession): Conversation {
  if (session.conversation?.schemaVersion === 1 && Number.isInteger(session.conversation.revision) &&
      typeof session.conversation.updatedAt === 'string') return session.conversation;
  return {
    schemaVersion: 1, revision: 0,
    updatedAt: session.messages.at(-1)?.timestamp || session.createdAt,
    titleOrigin: /^Đề \d+ · (Theo yêu cầu|Từ mẫu)$/.test(session.title) ? 'default' : 'legacy',
  };
}

export function touched(session: ExamSession): Conversation {
  const previous = conversationFor(session);
  return { ...previous, revision: previous.revision + 1, updatedAt: new Date().toISOString() };
}

const sensitive = /(?:\bBearer\s+\S+|\bsk-[\w-]{12,}|\bAIza[\w-]{15,}|(?:api[_ -]?key|token|password|mật khẩu)\s*[:=]\s*\S+|\b[\w.+-]+@[\w.-]+\.\w{2,})/giu;
const clean = (value: string) => value.replace(/[\p{Cc}\p{Cf}]/gu, ' ').replace(/\s+/g, ' ').trim();
export const redact = (value: string) => value.replace(sensitive, '[ẩn thông tin nhạy cảm]');
export const scrub = (value: string) => clean(redact(value));
export const titleFrom = (value: string) => [...scrub(value)].slice(0, 60).join('').trim();

export function suggestedTitle(value: string, source: string) {
  if (redact(value) !== value || /\d{5,}|\b(sinh vien|hoc sinh|ma so|ho va ten|sdt|dien thoai)\b/.test(fold(value))) return '';
  const title = titleFrom(value);
  const words = title.split(/\s+/);
  const objective = fold(source).replace(/[.!?]+$/, '');
  return words.length >= 3 && words.length <= 10 && fold(title) !== objective ? title : '';
}

export function meaningful(message: ChatMessage) {
  if (message.role !== 'user') return false;
  const text = fold(message.content);
  return !/^(tao de|soan de|tao lai de)$/.test(text) && /\b(thpt|v-act|vact|dgnl|chuyen de|on tap|tao de|soan de)\b/.test(text) &&
    !/^(xin chao[!.]?|mo\b|dong\b|doi ten\b|neu\b|nhac lai\b)/.test(text) &&
    !/\b(la gi|the nao|phai lam sao|ngau nhien|docx)\b/.test(text);
}

export function retrievedContext(session: ExamSession, messageId: string, query: string) {
  const messages = session.messages.filter(message => message.id !== messageId && message.role === 'user');
  const terms = new Set(fold(query).match(/[a-z0-9]{3,}/g) ?? []);
  const latest = session.messages.filter(message => message.id !== messageId && message.role !== 'system').slice(-6);
  const recentIds = new Set(latest.map(message => message.id));
  const relevant = messages.filter(message => !recentIds.has(message.id)).map(message => ({
    message, score: [...new Set(fold(message.content).match(/[a-z0-9]{3,}/g) ?? [])]
      .filter(term => terms.has(term)).length,
  })).filter(item => item.score > 0).sort((a, b) => b.score - a.score).slice(0, 2);
  const format = session.intake;
  const source = format && session.messages.find(message => message.id === format.sourceId);
  return {
    history: [...relevant.map(item => item.message), ...latest].map(message => (message.role === 'assistant' ? 'Trợ lý: ' : '') + scrub(message.content).slice(0, 390)).filter(Boolean),
    facts: source && format ? [
      [format.family && 'Dạng ' + format.family, format.subject && 'môn ' + scrub(format.subject),
        format.formatId && 'mẫu ' + format.formatId + ' v' + format.version, format.phase,
        format.missing && 'đang thiếu ' + format.missing].filter(Boolean).join(', '),
      ...(format.topic ? ['Chuyên đề: ' + scrub(format.topic).slice(0, 390)] : []),
    ] : [],
  };
}

export function searchSessions(sessions: ExamSession[], name: string) {
  const text = fold(name);
  const exact = sessions.filter(session => fold(session.title) === text);
  if (exact.length) return exact;
  const titles = sessions.filter(session => fold(session.title).includes(text));
  if (titles.length) return titles;
  return sessions.filter(session => session.messages.some(message =>
    message.role === 'user' && fold(message.content).includes(text)));
}
