import { useId } from 'react';

export function AstraLogo({ animated = false, className }: { animated?: boolean; className?: string }) {
  const orbitId = useId();
  const glowId = useId();
  return (
        <svg className={className} viewBox="0 0 320 280" aria-hidden="true">
          <defs>
            <path id={orbitId} d="M52 187C11 161 48 99 125 77C179 61 222 63 253 78" />
            <filter id={glowId} x="-150%" y="-150%" width="400%" height="400%" colorInterpolationFilters="sRGB">
              <feGaussianBlur stdDeviation="7" />
            </filter>
          </defs>
          <use href={`#${orbitId}`} fill="none" stroke="#242323" strokeWidth="7" strokeLinecap="round" />
          <path d="M160 224C134 206 100 201 65 207V119C101 113 133 121 160 139C187 121 219 113 255 119V207C220 201 186 206 160 224Z" fill="#F1F0ED" stroke="#242323" strokeWidth="8" strokeLinejoin="round" />
          <g fill="none" stroke="#242323" strokeWidth="6" strokeLinecap="round">
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
            <path d="M0-19 5-6 19 0 5 6 0 19-5 6-19 0-5-6Z" filter={`url(#${glowId})`} opacity="0">
              <animate attributeName="opacity" from="0" to="0.85" begin="1.75s" dur="0.35s" fill="freeze" />
            </path>
            <path d="M0-19 5-6 19 0 5 6 0 19-5 6-19 0-5-6Z">
              <animate attributeName="fill" from="#F3C54B" to="#FFDA66" begin="1.75s" dur="0.35s" fill="freeze" />
            </path>
          </g> : <path d="M253 59 258 72 272 78 258 84 253 97 248 84 234 78 248 72Z" fill="#F3C54B" />}
        </svg>
  );
}
