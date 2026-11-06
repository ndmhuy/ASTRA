import React, { useEffect, useRef, useState } from 'react';

interface WorkspaceLayoutProps { children: { left: React.ReactNode; right: React.ReactNode }; }
export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({ children }) => {
  const [mobilePane, setMobilePane] = useState<'chat' | 'paper'>('chat');
  const [width, setWidth] = useState(420);
  const container = useRef<HTMLDivElement>(null);
  const [maxWidth, setMaxWidth] = useState(640);
  useEffect(() => {
    const element = container.current;
    if (!element) return;
    const observer = new ResizeObserver(() => {
      const maximum = Math.max(300, Math.min(640, element.clientWidth - 440));
      setMaxWidth(maximum);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const visibleWidth = Math.min(width, maxWidth);
  const resize = (value: number) => setWidth(Math.max(300, Math.min(maxWidth, value)));
  return <div ref={container} className={`astra-workspace-split mobile-${mobilePane}`} style={{ '--chat-width': `${visibleWidth}px` } as React.CSSProperties}>
    <nav className="studio-mobile-tabs" aria-label="Khung làm việc"><button aria-pressed={mobilePane === 'chat'} onClick={() => setMobilePane('chat')}>Trao đổi với ASTRA</button><button aria-pressed={mobilePane === 'paper'} onClick={() => setMobilePane('paper')}>Xem trang đề</button></nav>
    <div id="studio-chat" className="astra-chat-pane" role="region" aria-label="Trao đổi và yêu cầu soạn đề">{children.left}</div>
    <div className="workspace-divider" role="separator" aria-label="Điều chỉnh chiều rộng khung soạn đề" aria-orientation="vertical" aria-valuemin={300} aria-valuemax={maxWidth} aria-valuenow={visibleWidth} aria-controls="studio-chat" tabIndex={0}
      onPointerDown={e => { e.currentTarget.setPointerCapture(e.pointerId); }}
      onPointerMove={e => { if (e.currentTarget.hasPointerCapture(e.pointerId)) resize(e.clientX - (container.current?.getBoundingClientRect().left || 0)); }}
      onPointerUp={e => e.currentTarget.releasePointerCapture(e.pointerId)}
      onKeyDown={e => { if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); resize(visibleWidth + (e.key === 'ArrowLeft' ? -20 : 20)); } else if (e.key === 'Home' || e.key === 'End') { e.preventDefault(); resize(e.key === 'Home' ? 300 : maxWidth); } }} />
    <div className="astra-canvas-pane" role="region" aria-label="Bản xem trước đề thi">{children.right}</div>
  </div>;
};
