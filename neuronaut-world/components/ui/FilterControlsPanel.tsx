/**
 * Filter Controls Panel
 *
 * Provides fine-grained control over what information is displayed.
 */

'use client';

import React from 'react';
import type { ViewSettings } from '@/types/view-modes';

interface FilterControlsPanelProps {
  settings: ViewSettings;
  onSettingsChange: (settings: Partial<ViewSettings>) => void;
  isExpanded: boolean;
  onToggleExpanded: () => void;
}

interface FilterOption {
  key: keyof ViewSettings;
  label: string;
  icon: string;
  category: 'agents' | 'buildings' | 'resources' | 'display';
}

const FILTER_OPTIONS: FilterOption[] = [
  // Agent filters
  { key: 'showAgentNames', label: 'Agent Names', icon: '👤', category: 'agents' },
  { key: 'showAgentActivities', label: 'Activities', icon: '🎯', category: 'agents' },
  { key: 'showAgentHealth', label: 'Health Glow', icon: '❤️', category: 'agents' },

  // Building filters
  { key: 'showBuildingOwners', label: 'Building Owners', icon: '🏠', category: 'buildings' },
  { key: 'showBuildingProgress', label: 'Construction Progress', icon: '📊', category: 'buildings' },

  // Resource filters
  { key: 'showResourceNodes', label: 'Resource Nodes', icon: '💎', category: 'resources' },
  { key: 'showResourceQuantities', label: 'Quantities', icon: '🔢', category: 'resources' },

  // Display options
  { key: 'hoverOnly', label: 'Hover-Only Mode', icon: '👆', category: 'display' },
];

const CATEGORY_LABELS: Record<string, string> = {
  agents: 'Agents',
  buildings: 'Buildings',
  resources: 'Resources',
  display: 'Display',
};

const CATEGORY_COLORS: Record<string, string> = {
  agents: '#3b82f6',
  buildings: '#fbbf24',
  resources: '#22c55e',
  display: '#a855f7',
};

export default function FilterControlsPanel({
  settings,
  onSettingsChange,
  isExpanded,
  onToggleExpanded,
}: FilterControlsPanelProps) {
  const categories = ['agents', 'buildings', 'resources', 'display'] as const;

  const handleToggle = (key: keyof ViewSettings) => {
    const currentValue = settings[key];
    if (typeof currentValue === 'boolean') {
      onSettingsChange({ [key]: !currentValue });
    }
  };

  return (
    <div
      className="absolute bottom-4 left-4 z-20 transition-all duration-300"
      style={{
        width: isExpanded ? '320px' : '48px',
      }}
    >
      {/* Collapse/Expand Button */}
      <button
        onClick={onToggleExpanded}
        className="transition-all hover:scale-105"
        style={{
          width: '48px',
          height: '48px',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(100, 116, 139, 0.4)',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
          color: '#94a3b8',
          fontSize: '20px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: isExpanded ? '12px' : '0',
        }}
        title={isExpanded ? 'Collapse filters' : 'Expand filters'}
      >
        {isExpanded ? '✕' : '⚙️'}
      </button>

      {/* Expanded Panel */}
      {isExpanded && (
        <div
          style={{
            background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(100, 116, 139, 0.3)',
            borderRadius: '12px',
            padding: '16px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
            maxHeight: '500px',
            overflowY: 'auto',
          }}
        >
          {/* Header */}
          <div
            className="text-sm font-bold mb-4"
            style={{
              color: '#ffffff',
              letterSpacing: '0.5px',
            }}
          >
            ⚙️ DISPLAY FILTERS
          </div>

          {/* Filter Categories */}
          <div className="space-y-4">
            {categories.map((category) => {
              const categoryOptions = FILTER_OPTIONS.filter((opt) => opt.category === category);
              const color = CATEGORY_COLORS[category];

              return (
                <div key={category}>
                  {/* Category Header */}
                  <div
                    className="text-xs font-semibold mb-2 pb-1"
                    style={{
                      color: color,
                      borderBottom: `1px solid ${color}40`,
                      letterSpacing: '0.5px',
                    }}
                  >
                    {CATEGORY_LABELS[category]}
                  </div>

                  {/* Category Options */}
                  <div className="space-y-2">
                    {categoryOptions.map((option) => {
                      const isEnabled = settings[option.key] as boolean;

                      return (
                        <button
                          key={option.key}
                          onClick={() => handleToggle(option.key)}
                          className="w-full transition-all hover:scale-102"
                          style={{
                            padding: '8px 12px',
                            borderRadius: '8px',
                            background: isEnabled
                              ? `linear-gradient(135deg, ${color}30 0%, ${color}20 100%)`
                              : 'rgba(30, 41, 59, 0.5)',
                            border: isEnabled ? `1px solid ${color}60` : '1px solid rgba(100, 116, 139, 0.2)',
                            color: isEnabled ? '#ffffff' : '#94a3b8',
                            fontSize: '13px',
                            fontWeight: '500',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            textAlign: 'left',
                          }}
                        >
                          <span style={{ fontSize: '16px' }}>{option.icon}</span>
                          <span className="flex-1">{option.label}</span>
                          <span
                            style={{
                              width: '16px',
                              height: '16px',
                              borderRadius: '4px',
                              background: isEnabled ? color : 'rgba(100, 116, 139, 0.3)',
                              border: `1px solid ${isEnabled ? color : 'rgba(100, 116, 139, 0.5)'}`,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '10px',
                              color: '#ffffff',
                            }}
                          >
                            {isEnabled ? '✓' : ''}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Detail Level Indicator */}
          <div
            className="mt-4 pt-4"
            style={{
              borderTop: '1px solid rgba(100, 116, 139, 0.2)',
            }}
          >
            <div
              className="text-xs font-semibold mb-2"
              style={{
                color: '#94a3b8',
                letterSpacing: '0.5px',
              }}
            >
              CURRENT DETAIL LEVEL
            </div>
            <div
              className="text-sm font-bold"
              style={{
                color: '#22d3ee',
                textTransform: 'uppercase',
              }}
            >
              {settings.detailLevel === 'minimal' && '🔍 Minimal (Zoom in for more)'}
              {settings.detailLevel === 'medium' && '👁️ Medium (Standard view)'}
              {settings.detailLevel === 'full' && '🔬 Full (Maximum detail)'}
            </div>
          </div>

          {/* Quick Actions */}
          <div
            className="mt-4 pt-4 space-y-2"
            style={{
              borderTop: '1px solid rgba(100, 116, 139, 0.2)',
            }}
          >
            <button
              onClick={() => {
                // Enable all filters
                const allEnabled: Partial<ViewSettings> = {};
                FILTER_OPTIONS.forEach((opt) => {
                  if (opt.key !== 'hoverOnly') {
                    allEnabled[opt.key] = true;
                  }
                });
                onSettingsChange(allEnabled);
              }}
              className="w-full transition-all hover:scale-102"
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%)',
                border: '1px solid rgba(34, 211, 238, 0.4)',
                color: '#22d3ee',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              ✨ Show All
            </button>
            <button
              onClick={() => {
                // Disable all filters except essentials
                const minimal: Partial<ViewSettings> = {
                  showAgentNames: false,
                  showAgentActivities: false,
                  showAgentHealth: false,
                  showBuildingOwners: false,
                  showBuildingProgress: false,
                  showResourceNodes: false,
                  showResourceQuantities: false,
                  hoverOnly: true,
                };
                onSettingsChange(minimal);
              }}
              className="w-full transition-all hover:scale-102"
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, rgba(100, 116, 139, 0.2) 0%, rgba(71, 85, 105, 0.2) 100%)',
                border: '1px solid rgba(100, 116, 139, 0.4)',
                color: '#94a3b8',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              🧹 Minimize All
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
