import React, { useEffect, useRef } from 'react';
import { SchoolArt } from '../../SchoolArt';
import type { ChatMessage } from '../../../types/exam';

interface ChatHistoryProps {
  messages: ChatMessage[];
  onSuggestion?: (value: string) => void;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages, onSuggestion }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'nearest' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="chat-empty"><SchoolArt kind="globe" /><h3>Mình bắt đầu từ đâu?</h3><p>Mô tả một chút về đề thi thầy cô muốn soạn, hoặc thử một gợi ý:</p><div className="prompt-suggestions">{['20 câu Toán lớp 12 về đạo hàm', 'Đề Vật lý: dao động điều hòa', '15 câu Tiếng Anh về câu điều kiện'].map(text => <button key={text} onClick={() => onSuggestion?.(text)}>{text}<span aria-hidden="true">↗</span></button>)}</div></div>
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
        return (
          <div key={msg.id} className={isUser ? 'chat-msg-user' : 'chat-msg-assistant'}>
            {!isUser && (
              <div className="chat-msg-label">ASTRA</div>
            )}
            <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{msg.content}</div>
            {msg.timestamp && (
              <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 3 }}>
                {new Date(msg.timestamp).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
              </div>
            )}
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
};
