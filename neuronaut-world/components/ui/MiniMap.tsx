/**
 * Mini Map Component
 *
 * Provides an overview of the world with agents and buildings.
 */

'use client';

import React from 'react';
import type { Building } from '@/types/structures';

interface Agent {
  id: string;
  position: { x: number; y: number };
  alive: boolean;
}

interface MiniMapProps {
  agents: Agent[];
  buildings: Building[];
  worldWidth: number;
  worldHeight: number;
  currentView: { x: number; y: number; zoom: number };
  onLocationClick?: (x: number, y: number) => void;
}

export default function MiniMap({
  agents,
  buildings,
  worldWidth,
  worldHeight,
  currentView,
  onLocationClick,
}: MiniMapProps) {
  const mapSize = 180; // Fixed size in pixels
  const scaleX = mapSize / worldWidth;
  const scaleY = mapSize / worldHeight;

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!onLocationClick) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / scaleX;
    const y = (e.clientY - rect.top) / scaleY;

    onLocationClick(x, y);
  };

  return (
    <div
      className="absolute top-4 right-4 z-20"
      style={{
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(100, 116, 139, 0.3)',
        borderRadius: '12px',
        padding: '12px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
      }}
    >
      {/* Header */}
      <div
        className="text-xs font-semibold mb-2"
        style={{
          color: '#94a3b8',
          letterSpacing: '0.5px',
        }}
      >
        🗺️ MINI-MAP
      </div>

      {/* Map Canvas */}
      <div
        style={{
          position: 'relative',
          width: `${mapSize}px`,
          height: `${mapSize}px`,
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 1) 0%, rgba(30, 41, 59, 1) 100%)',
          borderRadius: '8px',
          border: '2px solid rgba(100, 116, 139, 0.3)',
          cursor: 'pointer',
          overflow: 'hidden',
        }}
        onClick={handleClick}
      >
        {/* Grid background */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `
              linear-gradient(rgba(100, 116, 139, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(100, 116, 139, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: `${mapSize / 10}px ${mapSize / 10}px`,
          }}
        />

        {/* Buildings */}
        {buildings.map((building) => {
          const x = building.position.x * scaleX;
          const y = building.position.y * scaleY;

          return (
            <div
              key={building.id}
              style={{
                position: 'absolute',
                left: `${x}px`,
                top: `${y}px`,
                width: '6px',
                height: '6px',
                borderRadius: building.stage === 'completed' ? '2px' : '1px',
                background: building.stage === 'completed' ? '#fbbf24' : '#f59e0b',
                opacity: building.stage === 'completed' ? 0.9 : 0.5,
                transform: 'translate(-50%, -50%)',
                boxShadow: building.stage === 'completed' ? '0 0 4px #fbbf24' : 'none',
              }}
            />
          );
        })}

        {/* Agents */}
        {agents.filter((a) => a.alive).map((agent) => {
          const x = agent.position.x * scaleX;
          const y = agent.position.y * scaleY;

          return (
            <div
              key={agent.id}
              style={{
                position: 'absolute',
                left: `${x}px`,
                top: `${y}px`,
                width: '4px',
                height: '4px',
                borderRadius: '50%',
                background: '#3b82f6',
                opacity: 0.9,
                transform: 'translate(-50%, -50%)',
                boxShadow: '0 0 3px #3b82f6',
              }}
            />
          );
        })}

        {/* Current view indicator */}
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            width: `${100 * currentView.zoom}px`,
            height: `${100 * currentView.zoom}px`,
            border: '2px solid rgba(167, 139, 250, 0.6)',
            borderRadius: '4px',
            pointerEvents: 'none',
            boxShadow: '0 0 8px rgba(167, 139, 250, 0.4)',
          }}
        />
      </div>

      {/* Legend */}
      <div className="mt-3 space-y-1 text-xs" style={{ color: '#94a3b8' }}>
        <div className="flex items-center gap-2">
          <div
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '2px',
              background: '#fbbf24',
            }}
          />
          <span>Buildings ({buildings.filter((b) => b.stage === 'completed').length})</span>
        </div>
        <div className="flex items-center gap-2">
          <div
            style={{
              width: '4px',
              height: '4px',
              borderRadius: '50%',
              background: '#3b82f6',
            }}
          />
          <span>Agents ({agents.filter((a) => a.alive).length})</span>
        </div>
      </div>

      {/* Hint */}
      <div
        className="mt-2 text-xs italic"
        style={{
          color: 'rgba(148, 163, 184, 0.6)',
        }}
      >
        Click to jump to location
      </div>
    </div>
  );
}
