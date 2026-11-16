import React, { useEffect, useRef } from 'react';
import { Copy, GitBranch, Pencil, RotateCcw, Calculator, Atom, Languages, ArrowUpRight } from 'lucide-react';
import { SchoolArt } from '../../SchoolArt';
import type { ChatMessage } from '../../../types/exam';

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
      <div className="chat-empty"><SchoolArt kind="globe" /><h3>Mình bắt đầu từ đâu?</h3><p>Mô tả một chút về đề thi thầy cô muốn soạn, hoặc thử một gợi ý:</p><div className="prompt-suggestions">{[{text:'20 câu Toán lớp 12 về đạo hàm',icon:Calculator}, {text:'Đề Vật lý: dao động điều hòa',icon:Atom}, {text:'15 câu Tiếng Anh về câu điều kiện',icon:Languages}].map(({text,icon:Icon}) => <button key={text} onClick={() => onSuggestion?.(text)}><Icon size={17} aria-hidden="true" /><span>{text}</span><ArrowUpRight size={15} aria-hidden="true" /></button>)}</div></div>
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
            <button type="button" title={copiedId === msg.id ? 'Đã sao chép' : 'Sao chép'} aria-label="Sao chép tin nhắn" onClick={() => void copyMessage()}><Copy size={14} /><span>{copiedId === msg.id ? 'Đã chép' : 'Sao chép'}</span></button>
            {isUser && <button type="button" title="Chỉnh sửa tin nhắn" aria-label="Chỉnh sửa tin nhắn" onClick={() => onEditMessage?.(msg)}><Pencil size={14} /><span>Sửa</span></button>}
            {isUser && <button type="button" title="Thu hồi tin nhắn này và các tin sau" aria-label="Thu hồi tin nhắn" onClick={() => onRetractMessage?.(msg)}><RotateCcw size={14} /><span>Thu hồi</span></button>}
            <button type="button" title="Tạo nhánh hội thoại tại đây" aria-label="Tạo nhánh hội thoại" onClick={() => onBranchMessage?.(msg)}><GitBranch size={14} /><span>Tạo nhánh</span></button>
          </div>
        </article>;
      })}
      <div ref={bottomRef} />
    </div>
  );
};
