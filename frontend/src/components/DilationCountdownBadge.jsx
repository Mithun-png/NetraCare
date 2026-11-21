import React from 'react';
import { useDilationTimer } from '../hooks/useDilationTimer';
import { Clock, CheckCircle } from 'lucide-react';

export default function DilationCountdownBadge({
  dilationStartedAt,
  durationMins = 35,
  serverNow = null,
  visitStage = 'DILATING',
}) {
  const { formattedTime, isReady, progressPercent } = useDilationTimer(
    dilationStartedAt,
    durationMins,
    serverNow
  );

  if (visitStage === 'READY_FOR_DOCTOR' || isReady) {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 10px',
          borderRadius: '16px',
          background: '#ecfdf5',
          color: '#065f46',
          border: '1px solid #a7f3d0',
          fontWeight: 600,
          fontSize: '0.8rem',
        }}
      >
        <CheckCircle size={13} color="#059669" />
        Ready for Exam
      </span>
    );
  }

  if (visitStage === 'DILATING') {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '5px',
          padding: '4px 10px',
          borderRadius: '16px',
          background: '#fffbeb',
          color: '#92400e',
          border: '1px solid #fde68a',
          fontWeight: 600,
          fontSize: '0.8rem',
          fontFamily: 'monospace',
        }}
      >
        <Clock size={13} color="#d97706" />
        {formattedTime} left ({progressPercent}%)
      </span>
    );
  }

  if (visitStage === 'CHECKED_IN') {
    return (
      <span
        style={{
          padding: '3px 8px',
          borderRadius: '12px',
          background: '#f1f5f9',
          color: '#475569',
          fontSize: '0.78rem',
          fontWeight: 500,
        }}
      >
        Checked In
      </span>
    );
  }

  return (
    <span
      style={{
        padding: '3px 8px',
        borderRadius: '12px',
        background: '#f8fafc',
        color: '#64748b',
        fontSize: '0.78rem',
      }}
    >
      Scheduled
    </span>
  );
}
