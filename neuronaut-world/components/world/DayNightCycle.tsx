/**
 * Day/Night Cycle Overlay
 *
 * Provides atmospheric lighting that changes based on time of day.
 */

'use client';

import React, { useEffect, useState } from 'react';

interface DayNightCycleProps {
  tick: number; // Current simulation tick
  cycleDuration?: number; // Ticks per full day/night cycle
  enabled?: boolean;
}

export default function DayNightCycle({
  tick,
  cycleDuration = 1000,
  enabled = true,
}: DayNightCycleProps) {
  const [timeOfDay, setTimeOfDay] = useState(0); // 0-1, where 0.5 is noon, 0/1 is midnight

  useEffect(() => {
    // Calculate time of day (0-1 range)
    const tod = (tick % cycleDuration) / cycleDuration;
    setTimeOfDay(tod);
  }, [tick, cycleDuration]);

  if (!enabled) return null;

  // Calculate lighting values based on time of day
  const { overlay, stars, sunMoon } = getDayNightColors(timeOfDay);

  return (
    <>
      {/* Day/Night Overlay */}
      <div
        className="absolute inset-0 pointer-events-none transition-opacity duration-1000"
        style={{
          background: overlay.gradient,
          opacity: overlay.opacity,
          zIndex: 5,
        }}
      />

      {/* Stars (visible at night) */}
      {stars.visible && (
        <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 4 }}>
          {Array.from({ length: 50 }).map((_, i) => (
            <div
              key={`star-${i}`}
              className="absolute rounded-full animate-pulse"
              style={{
                left: `${(i * 37 + 20) % 100}%`,
                top: `${(i * 53 + 10) % 60}%`,
                width: `${1 + (i % 3)}px`,
                height: `${1 + (i % 3)}px`,
                backgroundColor: '#ffffff',
                opacity: stars.opacity * (0.5 + (i % 5) * 0.1),
                boxShadow: `0 0 ${2 + (i % 3)}px rgba(255, 255, 255, ${stars.opacity})`,
                animationDuration: `${2 + (i % 4)}s`,
                animationDelay: `${i * 0.1}s`,
              }}
            />
          ))}
        </div>
      )}

      {/* Sun/Moon */}
      <div
        className="absolute pointer-events-none transition-all duration-1000"
        style={{
          left: '50%',
          top: `${getSunMoonPosition(timeOfDay)}%`,
          transform: 'translateX(-50%)',
          zIndex: 3,
        }}
      >
        <div
          className="rounded-full"
          style={{
            width: '40px',
            height: '40px',
            background: sunMoon.gradient,
            opacity: sunMoon.opacity,
            boxShadow: `0 0 ${sunMoon.glow}px ${sunMoon.color}`,
            filter: `blur(${sunMoon.blur}px)`,
          }}
        />
      </div>

      {/* Time of Day Indicator */}
      <div
        className="absolute top-20 left-4 z-20 text-xs font-semibold px-3 py-2 rounded-lg"
        style={{
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(100, 116, 139, 0.3)',
          color: '#94a3b8',
          pointerEvents: 'none',
        }}
      >
        {getTimeOfDayLabel(timeOfDay)} {getTimeIcon(timeOfDay)}
      </div>
    </>
  );
}

/**
 * Get day/night colors based on time of day
 */
function getDayNightColors(tod: number): {
  overlay: { gradient: string; opacity: number };
  stars: { visible: boolean; opacity: number };
  sunMoon: { gradient: string; opacity: number; glow: number; blur: number; color: string };
} {
  // Time of day: 0 = midnight, 0.25 = dawn, 0.5 = noon, 0.75 = dusk, 1 = midnight

  // Night (0-0.2 and 0.8-1)
  if (tod < 0.2 || tod > 0.8) {
    const nightIntensity = tod < 0.2 ? 1 - tod / 0.2 : (tod - 0.8) / 0.2;
    return {
      overlay: {
        gradient: 'linear-gradient(180deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%)',
        opacity: 0.3 + nightIntensity * 0.4,
      },
      stars: {
        visible: true,
        opacity: 0.3 + nightIntensity * 0.5,
      },
      sunMoon: {
        gradient: 'radial-gradient(circle, rgba(226, 232, 240, 1) 0%, rgba(203, 213, 225, 0.8) 100%)',
        opacity: 0.6 + nightIntensity * 0.3,
        glow: 15,
        blur: 0.5,
        color: 'rgba(226, 232, 240, 0.6)',
      },
    };
  }

  // Dawn (0.2-0.35)
  if (tod >= 0.2 && tod < 0.35) {
    const dawnProgress = (tod - 0.2) / 0.15;
    return {
      overlay: {
        gradient: 'linear-gradient(180deg, rgba(251, 146, 60, 0.3) 0%, rgba(249, 115, 22, 0.2) 50%, rgba(15, 23, 42, 0.4) 100%)',
        opacity: 0.4 - dawnProgress * 0.2,
      },
      stars: {
        visible: true,
        opacity: 0.5 - dawnProgress * 0.5,
      },
      sunMoon: {
        gradient: 'radial-gradient(circle, rgba(251, 191, 36, 1) 0%, rgba(245, 158, 11, 0.9) 100%)',
        opacity: 0.7 + dawnProgress * 0.2,
        glow: 20 + dawnProgress * 10,
        blur: 1,
        color: 'rgba(251, 191, 36, 0.7)',
      },
    };
  }

  // Day (0.35-0.65)
  if (tod >= 0.35 && tod < 0.65) {
    return {
      overlay: {
        gradient: 'linear-gradient(180deg, rgba(147, 197, 253, 0.15) 0%, rgba(191, 219, 254, 0.1) 100%)',
        opacity: 0.2,
      },
      stars: {
        visible: false,
        opacity: 0,
      },
      sunMoon: {
        gradient: 'radial-gradient(circle, rgba(253, 224, 71, 1) 0%, rgba(250, 204, 21, 1) 100%)',
        opacity: 0.9,
        glow: 30,
        blur: 1.5,
        color: 'rgba(253, 224, 71, 0.8)',
      },
    };
  }

  // Dusk (0.65-0.8)
  const duskProgress = (tod - 0.65) / 0.15;
  return {
    overlay: {
      gradient: 'linear-gradient(180deg, rgba(124, 58, 237, 0.2) 0%, rgba(249, 115, 22, 0.25) 50%, rgba(15, 23, 42, 0.3) 100%)',
      opacity: 0.2 + duskProgress * 0.3,
    },
    stars: {
      visible: duskProgress > 0.5,
      opacity: (duskProgress - 0.5) * 1.0,
    },
    sunMoon: {
      gradient: 'radial-gradient(circle, rgba(251, 146, 60, 1) 0%, rgba(249, 115, 22, 0.9) 100%)',
      opacity: 0.9 - duskProgress * 0.3,
      glow: 30 - duskProgress * 15,
      blur: 1.5,
      color: 'rgba(251, 146, 60, 0.7)',
    },
  };
}

/**
 * Get sun/moon vertical position based on time of day (arc across the sky)
 */
function getSunMoonPosition(tod: number): number {
  // Create an arc from bottom-left to top-center to bottom-right
  const angle = tod * Math.PI; // 0 to PI
  const baseY = 80; // Bottom position
  const peakY = 10; // Top position
  const y = baseY - (Math.sin(angle) * (baseY - peakY));
  return y;
}

/**
 * Get time of day label
 */
function getTimeOfDayLabel(tod: number): string {
  if (tod < 0.2 || tod > 0.8) return 'Night';
  if (tod >= 0.2 && tod < 0.35) return 'Dawn';
  if (tod >= 0.35 && tod < 0.45) return 'Morning';
  if (tod >= 0.45 && tod < 0.55) return 'Noon';
  if (tod >= 0.55 && tod < 0.65) return 'Afternoon';
  if (tod >= 0.65 && tod < 0.8) return 'Dusk';
  return 'Night';
}

/**
 * Get time icon
 */
function getTimeIcon(tod: number): string {
  if (tod < 0.2 || tod > 0.8) return '🌙';
  if (tod >= 0.2 && tod < 0.35) return '🌅';
  if (tod >= 0.35 && tod < 0.65) return '☀️';
  if (tod >= 0.65 && tod < 0.8) return '🌆';
  return '🌙';
}
