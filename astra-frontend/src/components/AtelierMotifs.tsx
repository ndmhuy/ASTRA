import React from 'react';

interface MotifProps {
  className?: string;
}

const ASTROLABE_TICKS = Array.from({ length: 24 }, (_, index) => {
  const angle = (index * 15 * Math.PI) / 180;
  const inner = index % 3 === 0 ? 137 : 142;
  const outer = 148;
  return {
    key: index,
    x1: Number((160 + inner * Math.cos(angle)).toFixed(2)),
    y1: Number((160 + inner * Math.sin(angle)).toFixed(2)),
    x2: Number((160 + outer * Math.cos(angle)).toFixed(2)),
    y2: Number((160 + outer * Math.sin(angle)).toFixed(2)),
    major: index % 3 === 0,
  };
});

export const AstrolabeMotif: React.FC<MotifProps> = ({ className = '' }) => (
  <svg
    className={className}
    viewBox="0 0 320 320"
    fill="none"
    stroke="currentColor"
    strokeWidth="0.9"
    aria-hidden="true"
    focusable="false"
  >
    <circle cx="160" cy="160" r="148" strokeOpacity="0.45" />
    <circle cx="160" cy="160" r="132" strokeDasharray="3 5" strokeOpacity="0.55" />
    <circle cx="160" cy="160" r="106" strokeOpacity="0.32" />
    <circle cx="172" cy="146" r="68" strokeOpacity="0.42" strokeDasharray="2 4" />
    <circle cx="160" cy="160" r="44" strokeOpacity="0.28" />
    {ASTROLABE_TICKS.map(tick => (
      <line
        key={tick.key}
        x1={tick.x1}
        y1={tick.y1}
        x2={tick.x2}
        y2={tick.y2}
        strokeWidth={tick.major ? 1.15 : 0.75}
        strokeOpacity={tick.major ? 0.65 : 0.35}
      />
    ))}
    <line x1="12" y1="160" x2="308" y2="160" strokeOpacity="0.26" />
    <line x1="160" y1="12" x2="160" y2="308" strokeOpacity="0.26" />
    <line x1="56" y1="56" x2="264" y2="264" strokeOpacity="0.18" />
    <line x1="56" y1="264" x2="264" y2="56" strokeOpacity="0.18" />
    <polygon
      points="160,48 164,160 160,272 156,160"
      fill="currentColor"
      fillOpacity="0.12"
      strokeOpacity="0.55"
    />
    <path
      d="M160 144C161 154 166 159 176 160C166 161 161 166 160 176C159 166 154 161 144 160C154 159 159 154 160 144Z"
      fill="currentColor"
      fillOpacity="0.45"
      stroke="none"
    />
    <path
      d="M240 82C240.6 87 243 89.4 248 90C243 90.6 240.6 93 240 98C239.4 93 237 90.6 232 90C237 89.4 239.4 87 240 82Z"
      fill="currentColor"
      fillOpacity="0.7"
      stroke="none"
    />
  </svg>
);

export const MathDraftingMotif: React.FC<MotifProps> = ({ className = '' }) => (
  <svg
    className={className}
    viewBox="0 0 280 220"
    fill="none"
    stroke="currentColor"
    strokeWidth="0.95"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    {/* Coordinate axes Ox / Oy */}
    <line x1="24" y1="168" x2="256" y2="168" strokeOpacity="0.48" />
    <path d="M250 164l6 4-6 4" strokeOpacity="0.48" />
    <line x1="68" y1="204" x2="68" y2="20" strokeOpacity="0.48" />
    <path d="M64 26l4-6 4 6" strokeOpacity="0.48" />
    {/* Axis tick marks */}
    <line x1="116" y1="164" x2="116" y2="172" strokeOpacity="0.4" />
    <line x1="168" y1="164" x2="168" y2="172" strokeOpacity="0.4" />
    <line x1="216" y1="164" x2="216" y2="172" strokeOpacity="0.4" />
    <line x1="64" y1="120" x2="72" y2="120" strokeOpacity="0.4" />
    <line x1="64" y1="74" x2="72" y2="74" strokeOpacity="0.4" />
    {/* Smooth cubic curve & tangent line */}
    <path d="M36 184C68 176 82 54 128 84C164 108 184 152 246 44" strokeOpacity="0.72" strokeWidth="1.2" />
    <line x1="82" y1="126" x2="188" y2="58" strokeDasharray="3 4" strokeOpacity="0.52" />
    {/* Point projections */}
    <line x1="128" y1="84" x2="128" y2="168" strokeDasharray="2 3" strokeOpacity="0.34" />
    <line x1="128" y1="84" x2="68" y2="84" strokeDasharray="2 3" strokeOpacity="0.34" />
    <circle cx="128" cy="84" r="3" fill="currentColor" fillOpacity="0.65" />
    <circle cx="216" cy="96" r="2.2" fill="currentColor" fillOpacity="0.5" />
    {/* Geometric triangle & circumcircle arc */}
    <circle cx="204" cy="144" r="38" strokeOpacity="0.32" />
    <polygon points="174,166 204,108 238,158" strokeOpacity="0.48" />
    <path d="M166 144A38 38 0 0 1 204 106" strokeOpacity="0.65" />
  </svg>
);

export const ConstellationMotif: React.FC<MotifProps> = ({ className = '' }) => (
  <svg
    className={className}
    viewBox="0 0 240 160"
    fill="none"
    stroke="currentColor"
    strokeWidth="0.9"
    aria-hidden="true"
    focusable="false"
  >
    <path d="M16 122C68 62 146 38 226 48" strokeDasharray="3 5" strokeOpacity="0.42" />
    <polyline
      points="36,108 84,74 134,88 184,46 212,68"
      strokeOpacity="0.5"
    />
    <circle cx="36" cy="108" r="2.2" fill="currentColor" fillOpacity="0.65" />
    <circle cx="84" cy="74" r="2.8" fill="currentColor" fillOpacity="0.75" />
    <circle cx="134" cy="88" r="2" fill="currentColor" fillOpacity="0.6" />
    <circle cx="212" cy="68" r="2.2" fill="currentColor" fillOpacity="0.65" />
    <path
      d="M184 34C185 41 188 45 196 46C188 47 185 51 184 58C183 51 180 47 172 46C180 45 183 41 184 34Z"
      fill="currentColor"
      fillOpacity="0.8"
      stroke="none"
    />
    <circle cx="184" cy="46" r="14" strokeOpacity="0.3" />
  </svg>
);

export const CompassDivider: React.FC<MotifProps> = ({ className = '' }) => (
  <svg
    className={className}
    viewBox="0 0 420 28"
    fill="none"
    stroke="currentColor"
    strokeWidth="0.9"
    aria-hidden="true"
    focusable="false"
  >
    <line x1="0" y1="14" x2="178" y2="14" strokeOpacity="0.32" />
    <circle cx="184" cy="14" r="1.5" fill="currentColor" fillOpacity="0.55" stroke="none" />
    <circle cx="210" cy="14" r="10" strokeOpacity="0.38" />
    <path
      d="M210 5C210.7 10.5 213.5 13.3 219 14C213.5 14.7 210.7 17.5 210 23C209.3 17.5 206.5 14.7 201 14C206.5 13.3 209.3 10.5 210 5Z"
      fill="currentColor"
      fillOpacity="0.7"
      stroke="none"
    />
    <circle cx="236" cy="14" r="1.5" fill="currentColor" fillOpacity="0.55" stroke="none" />
    <line x1="242" y1="14" x2="420" y2="14" strokeOpacity="0.32" />
  </svg>
);

export const CornerPlate: React.FC<MotifProps> = ({ className = '' }) => (
  <svg
    className={className}
    viewBox="0 0 48 48"
    fill="none"
    stroke="currentColor"
    strokeWidth="1"
    aria-hidden="true"
    focusable="false"
  >
    <path d="M4 44V8A4 4 0 0 1 8 4H44" strokeOpacity="0.55" />
    <path d="M12 44V14A2 2 0 0 1 14 12H44" strokeOpacity="0.22" />
    <path d="M44 4A40 40 0 0 1 4 44" strokeDasharray="2 3" strokeOpacity="0.25" />
    <circle cx="12" cy="12" r="1.5" fill="currentColor" fillOpacity="0.6" stroke="none" />
  </svg>
);
