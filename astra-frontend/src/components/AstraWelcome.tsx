import { useEffect } from 'react';
import { ArrowRight } from 'lucide-react';
import { AstraLogo } from './AstraLogo';
import { CornerPlate, MathDraftingMotif } from './AtelierMotifs';
import './AstraWelcome.css';

export function AstraWelcome({ onComplete }: { onComplete: () => void }) {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  useEffect(() => {
    const timer = window.setTimeout(onComplete, reduced ? 300 : 1400);
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
        <MathDraftingMotif className="welcome-math-plate" />
        <CornerPlate className="welcome-corner is-tl" />
        <CornerPlate className="welcome-corner is-tr" />
        <CornerPlate className="welcome-corner is-bl" />
        <CornerPlate className="welcome-corner is-br" />
      </div>

      <div className="welcome-frame">
        <div className="astra-welcome-content">
          <AstraLogo animated={!reduced} useAstraStar className="astra-welcome-logo" />
          <div className="astra-welcome-wordmark">ASTRA</div>
          <h1>Chào thầy cô!</h1>
          <p role="status" aria-live="polite">Đang mở không gian soạn đề…</p>
          <div className="welcome-loader" aria-hidden="true">
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
