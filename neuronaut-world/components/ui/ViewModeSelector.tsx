/**
 * View Mode Selector
 *
 * Allows users to switch between different view modes.
 */

'use client';

import React from 'react';
import type { ViewMode } from '@/types/view-modes';

interface ViewModeSelectorProps {
  currentMode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
}

const VIEW_MODE_CONFIGS: Record<ViewMode, { icon: string; label: string; color: string }> = {
  normal: {
    icon: '👁️',
    label: 'Normal',
    color: '#64748b',
  },
  agents: {
    icon: '👥',
    label: 'Agents',
    color: '#3b82f6',
  },
  buildings: {
    icon: '🏗️',
    label: 'Buildings',
    color: '#fbbf24',
  },
  resources: {
    icon: '🌲',
    label: 'Resources',
    color: '#22c55e',
  },
  technology: {
    icon: '🔬',
    label: 'Tech',
    color: '#22d3ee',
  },
  economy: {
    icon: '💰',
    label: 'Economy',
    color: '#a855f7',
  },
};

export default function ViewModeSelector({ currentMode, onModeChange }: ViewModeSelectorProps) {
  const modes: ViewMode[] = ['normal', 'agents', 'buildings', 'resources', 'technology', 'economy'];

  return (
    <div
      className="flex gap-2 p-2 rounded-lg"
      style={{
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.9) 100%)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(100, 116, 139, 0.3)',
      }}
    >
      {modes.map((mode) => {
        const config = VIEW_MODE_CONFIGS[mode];
        const isActive = currentMode === mode;

        return (
          <button
            key={mode}
            onClick={() => onModeChange(mode)}
            className="transition-all hover:scale-105"
            style={{
              padding: '8px 12px',
              borderRadius: '8px',
              background: isActive
                ? `linear-gradient(135deg, ${config.color}40 0%, ${config.color}30 100%)`
                : 'transparent',
              border: isActive
                ? `2px solid ${config.color}`
                : '1px solid rgba(100, 116, 139, 0.3)',
              color: isActive ? config.color : '#94a3b8',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              whiteSpace: 'nowrap',
            }}
            title={`Switch to ${config.label} view`}
          >
            <span style={{ fontSize: '16px' }}>{config.icon}</span>
            <span>{config.label}</span>
          </button>
        );
      })}
    </div>
  );
}
