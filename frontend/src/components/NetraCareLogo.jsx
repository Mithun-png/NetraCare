import React from 'react';

/**
 * NetraCareLogo
 * Custom ophthalmic emblem featuring an almond eye contour,
 * coral iris, optical pupil, specular catchlight, and precision clinical sparkle.
 */
export default function NetraCareLogo({ size = 32, className = '' }) {
  return (
    <div
      className={className}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
      aria-label="NetraCare Eye Clinic Logo"
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ display: 'block', overflow: 'visible' }}
      >
        {/* Soft background glow disc */}
        <circle cx="24" cy="24" r="22" fill="#FFF1F0" />
        
        {/* Outer almond eye contour with organic softness */}
        <path
          d="M 6 24 C 13 13, 35 13, 42 24 C 35 35, 13 35, 6 24 Z"
          stroke="#292524"
          strokeWidth="2.75"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="#FFFFFF"
        />

        {/* Coral iris disc */}
        <circle
          cx="24"
          cy="24"
          r="8.5"
          fill="#FFB7B2"
          stroke="rgba(255, 183, 178, 0.4)"
          strokeWidth="1.5"
        />

        {/* Pupil */}
        <circle cx="24" cy="24" r="4.5" fill="#292524" />

        {/* Specular catchlight / gleam */}
        <circle cx="26.2" cy="21.8" r="1.6" fill="#FFFFFF" />

        {/* Precision clinical sparkle mark */}
        <path
          d="M 37 8 L 37 14 M 34 11 L 40 11"
          stroke="#E07A72"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}
