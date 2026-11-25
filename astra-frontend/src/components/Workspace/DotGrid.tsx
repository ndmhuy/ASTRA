import React, { useEffect, useMemo, useRef, useState } from 'react';

interface DotGridProps {
  rotationDegrees: number;
}

/** Vector-rendered square dot lattice with a bottom-up size and opacity taper. */
export const DotGrid: React.FC<DotGridProps> = ({ rotationDegrees }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const observer = new ResizeObserver(([entry]) => {
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height });
    });
    observer.observe(svg);
    return () => observer.disconnect();
  }, []);

  const dots = useMemo(() => {
    const { width, height } = size;
    if (!width || !height) return [];
    const step = 24;
    const angle = (rotationDegrees * Math.PI) / 180;
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    const extent = Math.hypot(width, height);
    const count = Math.ceil(extent / step);
    const fadeStart = height * 0.6;
    const result: Array<{ key: string; x: number; y: number; radius: number; opacity: number }> = [];

    for (let column = -count; column <= count; column += 1) {
      for (let row = -count; row <= count; row += 1) {
        const x = column * step;
        const y = row * step;
        const screenX = width / 2 + x * cos - y * sin;
        const screenY = height / 2 + x * sin + y * cos;
        if (screenX < 0 || screenX > width || screenY < fadeStart || screenY > height) continue;

        const fade = Math.max(0, Math.min(1, (screenY - fadeStart) / (height - fadeStart)));
        result.push({
          key: `${column}:${row}`,
          x: screenX,
          y: screenY,
          radius: 0.25 + 7.25 * fade,
          opacity: 0.42 * fade,
        });
      }
    }
    return result;
  }, [rotationDegrees, size]);

  return (
    <svg
      ref={svgRef}
      className="create-dot-grid"
      viewBox={`0 0 ${size.width} ${size.height}`}
      aria-hidden="true"
    >
      {dots.map(dot => (
        <circle
          key={dot.key}
          cx={dot.x}
          cy={dot.y}
          r={dot.radius}
          fill={`rgba(64,112,57,${dot.opacity})`}
        />
      ))}
    </svg>
  );
};