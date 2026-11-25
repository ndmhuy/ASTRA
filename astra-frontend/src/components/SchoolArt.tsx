/** Original vector school supplies, drawn in the Classroom Hub reference palette. */
export function SchoolArt({ kind, className = '' }: { kind: 'globe' | 'book' | 'bag'; className?: string }) {
  return <svg className={className} viewBox="0 0 260 240" fill="none" stroke="#181815" strokeWidth="2" strokeLinejoin="round" aria-hidden="true">
    {kind === 'globe' && <>
      <path d="M139 184v28h-35v13h96v-13h-37v-29" fill="#ffcf48" />
      <path d="M172 18C274 72 222 208 115 185l-5 10C233 227 293 69 178 8Z" fill="#ffcf48" />
      <path d="m166 19 9-17M111 194l7-20" />
      <circle cx="141" cy="100" r="77" fill="#75a8ff" />
      <path d="M117 27c-3 21 17 12 24 24s21 4 28-9l6-10M205 58c-28-12-40 17-62 21s-17 24-6 33 8 22 20 24 5 28 26 28c32-24 44-63 22-106ZM66 108c24 2 10 19 26 30s-2 20-2 20M133 118c-14 0-21 27-9 28 8 2 3-13 11-18Z" fill="#3c5bc0" />
      <path d="M34 39v23m-12-12h24M224 184v18m-9-9h18" stroke="#181815" />
    </>}
    {kind === 'book' && <>
      <path d="M31 57h88l13 8 13-8h85v157h-85l-13 7-13-7H31Z" fill="#3c5bc0" />
      <path d="M40 46h65q15 0 27 9 12-9 28-9h60v156h-62q-15 0-26 9-12-9-28-9H40Z" fill="#ffffff" />
      <path d="M132 55v156M57 77h55m-55 24h55m-55 24h55m-55 24h55m-55 24h55m43-96h45m-45 24h45m-45 24h45m-45 24h45m-45 24h45" />
      <g transform="rotate(42 180 100)"><path d="M163 27h28v132l-14 25-14-25Z" fill="#ff704f" /><path d="M163 137h28v22l-14 25-14-25Z" fill="#ffdd62" /><path d="m172 175 5 9 5-9" fill="#181815" /><rect x="159" y="14" width="36" height="42" rx="5" fill="#a3a3a3" /><rect x="170" y="14" width="25" height="36" rx="7" fill="#ff704f" /></g>
    </>}
    {kind === 'bag' && <>
      <path d="M106 55V35c0-30 49-30 49 0v20h-10V34c0-17-29-17-29 0v21Z" fill="#51b982" />
      <path d="m63 98-15-36q-2-8 7-10l12-3q8-2 10 6l12 40m86 0 12-40q2-8 10-6l12 3q9 2 7 10l-15 36" fill="#ff704f" />
      <path d="M55 123H40v64q0 12 16 10m149-74h15v64q0 12-16 10" fill="#ff704f" />
      <path d="M63 62h133l14 145q1 15-14 15H64q-15 0-14-15Z" fill="#ffdd62" />
      <path d="M50 199h160v10q0 13-14 13H64q-14 0-14-13Z" fill="#51b982" />
      <rect x="57" y="45" width="147" height="79" rx="25" fill="#51b982" />
      <path d="M78 106h11v39H78Zm94 0h11v39h-11Z" fill="#fffef7" />
      <path d="M84 193v-15a46 40 0 0 1 92 0v15Z" fill="#ff704f" /><path d="M86 165h87" /><circle cx="130" cy="139" r="6" fill="#51b982" />
    </>}
  </svg>;
}
