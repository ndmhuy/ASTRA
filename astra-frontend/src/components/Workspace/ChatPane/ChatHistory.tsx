import React, { useEffect, useRef } from 'react';
import { Check, Copy, GitBranch, Pencil, RotateCcw, Calculator, FileCheck2, GraduationCap, ArrowUpRight } from 'lucide-react';
import type { ChatMessage } from '../../../types/exam';
import { SchoolArt } from '../../SchoolArt';

interface ChatHistoryProps {
  messages: ChatMessage[];
  onSuggestion?: (value: string) => void;
  onEditMessage?: (message: ChatMessage) => void;
  onRetractMessage?: (message: ChatMessage) => void;
  onBranchMessage?: (message: ChatMessage) => void;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages, onSuggestion, onEditMessage, onRetractMessage, onBranchMessage }) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'nearest' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="chat-empty">
        <SchoolArt kind="globe" />
        <h3>Mình bắt đầu từ đâu?</h3>
        <p>Mô tả một chút về đề thi thầy cô muốn soạn, hoặc chọn nhanh một gợi ý:</p>
        <div className="prompt-suggestions">
          {[
            { text: 'Đề ôn tập Toán 12 chương Hàm số', icon: Calculator },
            { text: 'Đề thi thử THPT Quốc gia môn Toán', icon: FileCheck2 },
            { text: 'Đề Đánh giá năng lực ĐHQG-HCM (V-ACT)', icon: GraduationCap },
          ].map(({ text, icon: Icon }) => (
            <button key={text} type="button" onClick={() => onSuggestion?.(text)}>
              <Icon size={16} aria-hidden="true" />
              <span>{text}</span>
              <ArrowUpRight size={14} aria-hidden="true" />
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="chat-history"
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '12px 0',
      }}
    >
      {messages.map((msg) => {
        if (msg.role === 'system') return null;

        const isUser = msg.role === 'user';
        const isCopied = copiedId === msg.id;
        const copyMessage = async () => {
          try {
            await navigator.clipboard.writeText(msg.content);
            setCopiedId(msg.id);
            window.setTimeout(() => setCopiedId(current => current === msg.id ? null : current), 1400);
          } catch { /* Clipboard access may be unavailable in non-secure contexts. */ }
        };
        return <article key={msg.id} className={`chat-message-row ${isUser ? 'is-user' : 'is-assistant'}`}>
          <div className={isUser ? 'chat-msg-user' : 'chat-msg-assistant'}>
            {!isUser && <div className="chat-msg-label">ASTRA</div>}
            <div className="chat-message-content">{msg.content}</div>
            {msg.timestamp && <div className="chat-message-time">{new Date(msg.timestamp).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}</div>}
          </div>
          <div className="chat-message-actions" aria-label="Thao tác tin nhắn">
            <button type="button" className={isCopied ? 'is-copied' : undefined} title={isCopied ? 'Đã sao chép' : 'Sao chép'} aria-label="Sao chép tin nhắn" onClick={() => void copyMessage()}>
              {isCopied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
              <span>{isCopied ? 'Đã chép' : 'Sao chép'}</span>
            </button>
            {isUser && <button type="button" title="Chỉnh sửa tin nhắn" aria-label="Chỉnh sửa tin nhắn" onClick={() => onEditMessage?.(msg)}><Pencil size={14} aria-hidden="true" /><span>Sửa</span></button>}
            {isUser && <button type="button" title="Thu hồi tin nhắn này và các tin sau" aria-label="Thu hồi tin nhắn" onClick={() => onRetractMessage?.(msg)}><RotateCcw size={14} aria-hidden="true" /><span>Thu hồi</span></button>}
            <button type="button" title="Tạo nhánh hội thoại tại đây" aria-label="Tạo nhánh hội thoại" onClick={() => onBranchMessage?.(msg)}><GitBranch size={14} aria-hidden="true" /><span>Tạo nhánh</span></button>
          </div>
        </article>;
      })}
      <div ref={bottomRef} />
    </div>
  );
};
