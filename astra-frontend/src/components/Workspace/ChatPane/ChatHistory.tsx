import React, { useEffect, useRef } from 'react';
import type { ChatMessage } from '../../../types/exam';

interface ChatHistoryProps {
  messages: ChatMessage[];
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px 16px',
        }}
      >
        <p style={{ fontSize: 13, color: '#94a3b8', textAlign: 'center', lineHeight: 1.6 }}>
          Nhập yêu cầu bên dưới để bắt đầu.<br />
          ASTRA sẽ hỗ trợ soạn và kiểm định đề thi.
        </p>
      </div>
    );
  }

  return (
    <div
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
