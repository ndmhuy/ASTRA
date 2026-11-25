import { useEffect } from 'react';
import { ArrowRight } from 'lucide-react';
import { AstraLogo } from './AstraLogo';
import { AstrolabeMotif, ConstellationMotif, CornerPlate, MathDraftingMotif } from './AtelierMotifs';
import './AstraWelcome.css';

export function AstraWelcome({ onComplete }: { onComplete: () => void }) {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  useEffect(() => {
    const timer = window.setTimeout(onComplete, reduced ? 400 : 2100);
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
      <div className="welcome-backdrop-motifs" aria-hidden="true">
        <AstrolabeMotif className="welcome-astrolabe" />
        <MathDraftingMotif className="welcome-math-plate" />
        <ConstellationMotif className="welcome-constellation" />
        <CornerPlate className="welcome-corner is-tl" />
        <CornerPlate className="welcome-corner is-tr" />
        <CornerPlate className="welcome-corner is-bl" />
        <CornerPlate className="welcome-corner is-br" />
      </div>

      <div className="welcome-frame">
        <div className="astra-welcome-content">
          <span className="welcome-eyebrow">MỘT NGÀY MỚI · MỘT Ý TƯỞNG HAY</span>
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
