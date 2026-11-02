import { useEffect } from 'react';
import { AstraLogo } from './AstraLogo';

const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
import './AstraWelcome.css';

export function AstraWelcome({ onComplete }: { onComplete: () => void }) {
  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const timer = window.setTimeout(onComplete, reduced ? 350 : 3650);
    return () => window.clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="astra-welcome" aria-label="Chào thầy cô">
      <div className="astra-welcome-content">
        <AstraLogo animated={!reducedMotion()} className="astra-welcome-logo" />
        <div className="astra-welcome-wordmark">ASTRA</div>
        <p>Chào thầy cô</p>
      </div>
    </div>
  );
}
