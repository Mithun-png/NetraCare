import React from 'react';
import emblemImg from '../assets/netracare-emblem.png';
import logoImg from '../assets/netracare-logo.png';

/**
 * NetraCareLogo
 * Renders the official NetraCare ophthalmic branding:
 * - variant="emblem" (default): Circular eye emblem with shutter iris & caring hands.
 * - variant="full": Complete horizontal brand lockup (emblem + "NetraCare EYE CLINIC").
 */
export default function NetraCareLogo({
  size = 36,
  height,
  width,
  variant = 'emblem',
  className = '',
  style = {},
}) {
  if (variant === 'full') {
    const h = height || size || 40;
    return (
      <img
        src={logoImg}
        alt="NetraCare Eye Clinic"
        className={className}
        style={{
          height: `${h}px`,
          width: width ? `${width}px` : 'auto',
          maxWidth: '100%',
          objectFit: 'contain',
          display: 'inline-block',
          verticalAlign: 'middle',
          ...style,
        }}
      />
    );
  }

  const s = size || height || 36;
  return (
    <div
      className={className}
      style={{
        width: `${s}px`,
        height: `${s}px`,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        ...style,
      }}
      aria-label="NetraCare Eye Clinic Logo"
    >
      <img
        src={emblemImg}
        alt="NetraCare Emblem"
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          display: 'block',
          borderRadius: '50%',
          filter: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.06))',
        }}
      />
    </div>
  );
}
