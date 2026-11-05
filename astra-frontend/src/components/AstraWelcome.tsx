import { useEffect } from 'react';
import { AstraLogo } from './AstraLogo';
import { SchoolArt } from './SchoolArt';
import './AstraWelcome.css';

export function AstraWelcome({ onComplete }: { onComplete: () => void }) {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  useEffect(() => {
    const timer = window.setTimeout(onComplete, reduced ? 800 : 2800);
    return () => window.clearTimeout(timer);
  }, [onComplete, reduced]);
  return <div className="astra-welcome">
    <SchoolArt kind="globe" className="welcome-supply welcome-globe" />
    <SchoolArt kind="bag" className="welcome-supply welcome-bag" />
    <div className="welcome-frame"><div className="astra-welcome-content">
      <span className="welcome-eyebrow">MỘT NGÀY MỚI, MỘT Ý TƯỞNG HAY</span>
      <AstraLogo animated={!reduced} useAstraStar className="astra-welcome-logo" />
      <div className="astra-welcome-wordmark">ASTRA</div>
      <h1>Chào thầy cô!</h1><p>Cùng mở trang đề tiếp theo.</p>
      <div className="welcome-loader" role="status" aria-label="Đang mở không gian soạn đề"><span /></div>
      <button onClick={onComplete}>Vào ngay <span aria-hidden="true">↗</span></button>
    </div></div>
    <span className="welcome-spark" aria-hidden="true">✦</span>
  </div>;
}
