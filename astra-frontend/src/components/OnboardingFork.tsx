import React from 'react';

interface OnboardingForkProps {
  onQuickMode: () => void;
  onProMode: () => void;
  /** Nếu có phiên làm việc đang mở, hiện nút "Quay lại" */
  hasActiveSession?: boolean;
  onResumeSession?: () => void;
}

export const OnboardingFork: React.FC<OnboardingForkProps> = ({
  onQuickMode,
  onProMode,
  hasActiveSession = false,
  onResumeSession,
}) => {
  return (
    <div
      style={{
        minHeight: 'calc(100vh - 58px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#fafbfa',
        padding: '32px 16px',
      }}
    >
      <div style={{ textAlign: 'center', maxWidth: 480, width: '100%' }}>
        {/* Brand */}
        <h1
          style={{
            fontSize: '2.5rem',
            fontWeight: 800,
            color: '#0f172a',
            letterSpacing: '-0.02em',
            marginBottom: 8,
            lineHeight: 1.1,
          }}
        >
          ASTRA
        </h1>
        <p
          style={{
            fontSize: 15,
            color: '#64748b',
            marginBottom: hasActiveSession ? 28 : 40,
            lineHeight: 1.5,
          }}
        >
          Hệ thống soạn &amp; kiểm định đề thi thông minh
        </p>

        {/* Resume session banner — chỉ hiện khi đang có phiên làm việc */}
        {hasActiveSession && onResumeSession && (
          <div
            style={{
              marginBottom: 28,
              padding: '16px 20px',
              border: '1.5px solid #a7f3d0',
              borderRadius: 6,
              background: '#f0fdf4',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              textAlign: 'left',
            }}
          >
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#065f46' }}>
                Bạn có phiên làm việc đang mở
              </div>
              <div style={{ fontSize: 13, color: '#047857', marginTop: 2 }}>
                Đề thi và hội thoại vẫn còn đó
              </div>
            </div>
            <button
              onClick={onResumeSession}
              style={{
                flexShrink: 0,
                padding: '10px 20px',
                background: '#059669',
                color: '#ffffff',
                border: 'none',
                borderRadius: 6,
                fontSize: 14,
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = '#047857'; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = '#059669'; }}
            >
              Quay lại →
            </button>
          </div>
        )}

        {/* Divider khi có session */}
        {hasActiveSession && (
          <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 20, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Hoặc bắt đầu phiên mới
          </p>
        )}

        {/* Question */}
        {!hasActiveSession && (
          <p
            style={{
              fontSize: 17,
              fontWeight: 600,
              color: '#334155',
              marginBottom: 24,
            }}
          >
            Bạn muốn tạo đề như thế nào?
          </p>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, alignItems: 'center', width: '100%', maxWidth: 360, margin: '0 auto' }}>
          <button
            onClick={onQuickMode}
            style={{
              width: '100%',
              padding: '16px 32px',
              background: hasActiveSession ? 'transparent' : '#059669',
              color: hasActiveSession ? '#334155' : '#ffffff',
              border: hasActiveSession ? '1.5px solid #cbd5e1' : 'none',
              borderRadius: 6,
              fontSize: 17,
              fontWeight: 700,
              cursor: 'pointer',
              letterSpacing: '-0.01em',
              transition: 'background 150ms ease, border-color 150ms ease',
            }}
            onMouseEnter={(e) => {
              const btn = e.currentTarget as HTMLButtonElement;
              btn.style.background = hasActiveSession ? '#f1f5f9' : '#047857';
              if (hasActiveSession) btn.style.borderColor = '#94a3b8';
            }}
            onMouseLeave={(e) => {
              const btn = e.currentTarget as HTMLButtonElement;
              btn.style.background = hasActiveSession ? 'transparent' : '#059669';
              if (hasActiveSession) btn.style.borderColor = '#cbd5e1';
            }}
          >
            Tạo nhanh
          </button>

          <button
            onClick={onProMode}
            style={{
              width: '100%',
              padding: '14px 32px',
              background: 'transparent',
              color: '#334155',
              border: '1.5px solid #cbd5e1',
              borderRadius: 6,
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'border-color 150ms ease, background 150ms ease',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = '#94a3b8';
              (e.currentTarget as HTMLButtonElement).style.background = '#f1f5f9';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = '#cbd5e1';
              (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
            }}
          >
            Chế độ Chuyên nghiệp
          </button>

          <p style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>
            "Tạo nhanh" phù hợp cho hầu hết giáo viên · Chuyên nghiệp dành cho tùy chỉnh sâu
          </p>
        </div>
      </div>
    </div>
  );
};
