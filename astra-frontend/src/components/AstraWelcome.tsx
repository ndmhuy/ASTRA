import { useEffect } from 'react';
import { ArrowRight } from 'lucide-react';
import { AstraLogo } from './AstraLogo';
import './AstraWelcome.css';

export function AstraWelcome({ onComplete }: { onComplete: () => void }) {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  useEffect(() => {
    const timer = window.setTimeout(onComplete, reduced ? 350 : 1350);
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' || event.key === 'Enter') {
        event.preventDefault();
        onComplete();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener('keydown', handleKey);
    };
  }, [onComplete, reduced]);

  return (
    <div className="astra-welcome">
      <div className="welcome-frame">
        <div className="astra-welcome-content">
          <AstraLogo animated={!reduced} useAstraStar className="astra-welcome-logo" />
          <div className="astra-welcome-wordmark">ASTRA</div>
          <h1>Chào thầy cô!</h1>
          <p>Cùng mở trang đề tiếp theo.</p>
          <div className="welcome-loader" role="status" aria-label="Đang mở không gian soạn đề">
            <span />
          </div>
          <button type="button" className="welcome-enter-btn" onClick={onComplete}>
            <span>Vào ngay</span>
            <ArrowRight size={15} aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
}
