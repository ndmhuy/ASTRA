import { useId } from 'react';
import ASTRA_Star from '../assets/ASTRA_Star.svg';

export function AstraLogo({ animated = false, className, useAstraStar = false }: { animated?: boolean; className?: string; useAstraStar?: boolean }) {
  const orbitId = useId();
  const glowId = useId();
  const star = useAstraStar
    ? <image href={ASTRA_Star} x="-29" y="-29.725" width="58" height="58" />
    : <path d="M0-24C1-7 3-2 15 0C3 2 1 7 0 24C-1 7-3 2-15 0C-3-2-1-7 0-24Z" />;
  return (
        <svg className={className} viewBox="0 0 320 280" aria-hidden="true">
          <defs>
            <path id={orbitId} d="M52 187C11 161 48 99 125 77C179 61 222 63 253 78" />
            <filter id={glowId} x="-150%" y="-150%" width="400%" height="400%" colorInterpolationFilters="sRGB">
              <feGaussianBlur stdDeviation="4.5" />
            </filter>
          </defs>
          <use href={`#${orbitId}`} fill="none" stroke="#242323" strokeWidth="3.5" strokeLinecap="butt" />
          <path d="M160 224C134 206 100 201 65 207V119C101 113 133 121 160 139C187 121 219 113 255 119V207C220 201 186 206 160 224Z" fill="#F1F0ED" stroke="#242323" strokeWidth="5" strokeLinejoin="miter" />
          <g fill="none" stroke="#242323" strokeWidth="3.5" strokeLinecap="butt">
            <path d="M160 140V222" />
            <path d="M85 140Q112 139 138 153" />
            <path d="M85 160Q112 159 138 173" />
            <path d="M85 180Q109 179 129 189" />
            <path d="M182 153Q208 139 235 140" />
            <path d="M182 173Q208 159 235 160" />
            <path d="M182 193Q201 182 223 181" />
          </g>
          {animated ? <g fill="#F3C54B">
            <animateMotion dur="1.75s" repeatCount="1" fill="freeze" calcMode="paced">
              <mpath href={`#${orbitId}`} />
            </animateMotion>
            <g filter={`url(#${glowId})`} opacity="0">
              {star}
              <animate attributeName="opacity" from="0" to="0.55" begin="1.75s" dur="0.35s" fill="freeze" />
            </g>
            {star}
          </g> : <g transform="translate(253 78)" fill="#F3C54B">{star}</g>}
        </svg>
  );
}
