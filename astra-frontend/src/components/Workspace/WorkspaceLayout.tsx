import React, { useEffect, useRef, useState } from 'react';
import { DotGrid } from './DotGrid';

interface WorkspaceLayoutProps { children: { left: React.ReactNode; right: React.ReactNode; composer?: React.ReactNode }; }
export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({ children }) => {
  const [mobilePane, setMobilePane] = useState<'chat' | 'paper'>('chat');
  const [width, setWidth] = useState(348);
  const container = useRef<HTMLDivElement>(null);
  const [maxWidth, setMaxWidth] = useState(460);
  useEffect(() => {
    const element = container.current;
    if (!element) return;
    const observer = new ResizeObserver(() => {
      const maximum = Math.max(280, Math.min(460, element.clientWidth - 460));
      setMaxWidth(maximum);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const visibleWidth = Math.min(width, maxWidth);
  const resize = (value: number) => setWidth(Math.max(280, Math.min(maxWidth, value)));
  return <div className="astra-workspace-stage">
    <DotGrid rotationDegrees={30} />
    <div ref={container} className={`astra-workspace-split mobile-${mobilePane}`} style={{ '--chat-width': `${visibleWidth}px` } as React.CSSProperties}>
      <nav className="studio-mobile-tabs" aria-label="Khung làm việc"><button type="button" aria-pressed={mobilePane === 'chat'} onClick={() => setMobilePane('chat')}>Trao đổi với ASTRA</button><button type="button" aria-pressed={mobilePane === 'paper'} onClick={() => setMobilePane('paper')}>Xem trang đề</button></nav>
      <div className="astra-canvas-pane" role="region" aria-label="Bản xem trước đề thi">{children.right}</div>
      <div className="workspace-divider" role="separator" aria-label="Điều chỉnh chiều rộng khung chat" aria-orientation="vertical" aria-valuemin={280} aria-valuemax={maxWidth} aria-valuenow={visibleWidth} aria-controls="studio-chat" tabIndex={0}
        onPointerDown={e => { e.currentTarget.setPointerCapture(e.pointerId); }}
        onPointerMove={e => { if (e.currentTarget.hasPointerCapture(e.pointerId)) resize((container.current?.getBoundingClientRect().right || 0) - e.clientX); }}
        onPointerUp={e => e.currentTarget.releasePointerCapture(e.pointerId)}
        onKeyDown={e => { if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); resize(visibleWidth + (e.key === 'ArrowLeft' ? -20 : 20)); } else if (e.key === 'Home' || e.key === 'End') { e.preventDefault(); resize(e.key === 'Home' ? 280 : maxWidth); } }} />
      <div id="studio-chat" className="astra-chat-pane" role="region" aria-label="Trao đổi và yêu cầu soạn đề">
        <div className="workspace-chat-body">{children.left}</div>
        {children.composer && <div className="workspace-composer-slot">{children.composer}</div>}
      </div>
    </div>
  </div>;
};
