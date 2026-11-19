import React from 'react';

/**
 * GrainOverlay
 * High-end tactile analog paper texture for NetraCare.
 * Uses SVG fractal noise filter with 0.35 opacity and overlay blend mode.
 */
export default function GrainOverlay() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 999,
        opacity: 0.35,
        mixBlendMode: 'overlay',
      }}
    >
      <svg style={{ width: '100%', height: '100%' }} xmlns="http://www.w3.org/2000/svg">
        <filter id="netracare-fractal-grain">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.65"
            numOctaves="3"
            stitchTiles="stitch"
          />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0.16   0 0 0 0 0.14   0 0 0 0 0.14   0 0 0 0.45 0"
          />
        </filter>
        <rect
          width="100%"
          height="100%"
          filter="url(#netracare-fractal-grain)"
          fill="#808080"
        />
      </svg>
    </div>
  );
}

