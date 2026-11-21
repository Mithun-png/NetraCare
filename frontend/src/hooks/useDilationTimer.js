import { useState, useEffect } from 'react';

/**
 * Custom hook to track real-time pupil dilation countdown.
 *
 * @param {string|null} dilationStartedAt - ISO timestamp when dilation began
 * @param {number} durationMins - Planned dilation window in minutes (default 35)
 * @param {string|null} serverNow - Server timestamp at time of response
 * @returns {{ remainingSeconds: number, formattedTime: string, progressPercent: number, isReady: boolean }}
 */
export function useDilationTimer(dilationStartedAt, durationMins = 35, serverNow = null) {
  const [remainingSeconds, setRemainingSeconds] = useState(0);

  useEffect(() => {
    if (!dilationStartedAt) {
      setRemainingSeconds(0);
      return;
    }

    const durationSec = (durationMins || 35) * 60;
    const startTime = new Date(dilationStartedAt).getTime();
    const serverTime = serverNow ? new Date(serverNow).getTime() : Date.now();
    const clientOffset = Date.now() - serverTime;

    const calculateRemaining = () => {
      const now = Date.now() - clientOffset;
      const elapsedSec = Math.max(0, Math.floor((now - startTime) / 1000));
      const remaining = Math.max(0, durationSec - elapsedSec);
      setRemainingSeconds(remaining);
    };

    calculateRemaining();
    const timer = setInterval(calculateRemaining, 1000);
    return () => clearInterval(timer);
  }, [dilationStartedAt, durationMins, serverNow]);

  const totalSec = (durationMins || 35) * 60;
  const elapsed = Math.max(0, totalSec - remainingSeconds);
  const progressPercent = totalSec > 0 ? Math.min(100, Math.round((elapsed / totalSec) * 100)) : 100;

  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;
  const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  const isReady = !!dilationStartedAt && remainingSeconds === 0;

  return {
    remainingSeconds,
    formattedTime,
    progressPercent,
    isReady,
  };
}
