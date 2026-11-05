import React, { useRef, useState } from 'react';

interface WorkspaceLayoutProps { children: { left: React.ReactNode; right: React.ReactNode }; }
export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({ children }) => {
  const [mobilePane, setMobilePane] = useState<'chat' | 'paper'>('chat');
  const [width, setWidth] = useState(360);
  const container = useRef<HTMLDivElement>(null);
  const resize = (value: number) => setWidth(Math.max(300, Math.min(480, value, (container.current?.clientWidth || 1000) - 520)));
  return <div ref={container} className={`astra-workspace-split mobile-${mobilePane}`} style={{ '--chat-width': `${width}px` } as React.CSSProperties}>
    <nav className="studio-mobile-tabs" aria-label="Khung làm việc"><button aria-pressed={mobilePane === 'chat'} onClick={() => setMobilePane('chat')}>Trao đổi với ASTRA</button><button aria-pressed={mobilePane === 'paper'} onClick={() => setMobilePane('paper')}>Xem trang đề</button></nav>
    <div className="astra-chat-pane">{children.left}</div>
    <div className="workspace-divider" role="separator" aria-label="Điều chỉnh chiều rộng khung soạn đề" aria-orientation="vertical" aria-valuemin={300} aria-valuemax={480} aria-valuenow={width} tabIndex={0}
      onPointerDown={e => { e.currentTarget.setPointerCapture(e.pointerId); }}
      onPointerMove={e => { if (e.currentTarget.hasPointerCapture(e.pointerId)) resize(e.clientX - (container.current?.getBoundingClientRect().left || 0)); }}
      onPointerUp={e => e.currentTarget.releasePointerCapture(e.pointerId)}
      onKeyDown={e => { if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); resize(width + (e.key === 'ArrowLeft' ? -20 : 20)); } }} />
    <div className="astra-canvas-pane">{children.right}</div>
  </div>;
};
