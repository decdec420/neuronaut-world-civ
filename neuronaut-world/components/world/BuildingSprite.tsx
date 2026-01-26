/**
 * BuildingSprite Component
 *
 * Renders visual representation of buildings at various construction stages.
 * Production-quality component with proper scaling and animations.
 */

'use client';

import React from 'react';
import type { Building, BuildingType, ConstructionStage } from '@/types/structures';
import { getBuildingConfig } from '@/types/structures';

interface BuildingSpriteProps {
  building: Building;
  scale: number;
  onClick?: (building: Building) => void;
  showOwner?: boolean;
  showProgress?: boolean;
}

export default function BuildingSprite({
  building,
  scale,
  onClick,
  showOwner = true,
  showProgress = true
}: BuildingSpriteProps) {
  const config = getBuildingConfig(building.type);
  const size = getBuildingSize(building.type, scale);

  return (
    <div
      className="absolute cursor-pointer hover:scale-110 transition-transform"
      onClick={() => onClick?.(building)}
      style={{
        width: size.width,
        height: size.height,
        pointerEvents: 'auto',
      }}
      title={`${config.name}\n${config.description}\nProgress: ${building.progress}%`}
    >
      {/* Construction Stage Visualization */}
      {building.stage !== 'completed' && (
        <ConstructionVisual
          type={building.type}
          stage={building.stage}
          progress={building.progress}
          size={size}
          color={config.color}
        />
      )}

      {/* Completed Building */}
      {building.stage === 'completed' && (
        <CompletedBuilding
          type={building.type}
          size={size}
          icon={config.icon}
          color={config.color}
        />
      )}

      {/* Progress Bar (during construction) */}
      {showProgress && building.stage !== 'completed' && (
        <div
          className="absolute -bottom-6 left-0 right-0"
          style={{ pointerEvents: 'none' }}
        >
          <div className="text-xs text-center mb-1" style={{ color: config.color }}>
            {Math.floor(building.progress)}%
          </div>
          <div
            className="w-full h-1 rounded-full"
            style={{ background: 'rgba(100, 116, 139, 0.3)' }}
          >
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${building.progress}%`,
                background: config.color,
                boxShadow: `0 0 6px ${config.color}`,
              }}
            />
          </div>
        </div>
      )}

      {/* Owner Badge (completed buildings) */}
      {showOwner && building.stage === 'completed' && building.ownerId && (
        <div
          className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
          style={{
            background: `${config.color}30`,
            border: `1px solid ${config.color}60`,
            color: config.color,
            pointerEvents: 'none',
          }}
        >
          {config.icon} Owner: {building.ownerId}
        </div>
      )}
    </div>
  );
}

/**
 * Construction Visual - Shows building in progress
 */
function ConstructionVisual({
  type,
  stage,
  progress,
  size,
  color,
}: {
  type: BuildingType;
  stage: ConstructionStage;
  progress: number;
  size: { width: number; height: number };
  color: string;
}) {
  return (
    <div className="relative w-full h-full">
      {/* Foundation Markers */}
      {stage === 'planning' && (
        <div className="w-full h-full border-2 border-dashed animate-pulse" style={{ borderColor: color }}>
          <div className="text-center mt-1 text-xs" style={{ color }}>📐</div>
        </div>
      )}

      {/* Foundation */}
      {stage === 'foundation' && (
        <div className="w-full h-full">
          <div
            className="absolute bottom-0 left-0 right-0"
            style={{
              height: '30%',
              background: `linear-gradient(180deg, ${color}40 0%, ${color}60 100%)`,
              border: `2px solid ${color}`,
            }}
          />
          <div className="absolute bottom-1 left-1/2 transform -translate-x-1/2 text-xs">
            🔨
          </div>
        </div>
      )}

      {/* Framing */}
      {stage === 'framing' && (
        <div className="w-full h-full relative">
          {/* Floor */}
          <div
            className="absolute bottom-0 left-0 right-0"
            style={{
              height: '20%',
              background: `${color}80`,
              border: `1px solid ${color}`,
            }}
          />

          {/* Walls (scaffolding) */}
          <div
            className="absolute"
            style={{
              bottom: '20%',
              left: 0,
              right: 0,
              height: '60%',
              borderLeft: `3px solid ${color}`,
              borderRight: `3px solid ${color}`,
            }}
          >
            {/* Horizontal beams */}
            <div
              className="absolute left-0 right-0"
              style={{
                top: '33%',
                height: '2px',
                background: color,
              }}
            />
            <div
              className="absolute left-0 right-0"
              style={{
                top: '66%',
                height: '2px',
                background: color,
              }}
            />
          </div>

          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 text-lg">
            🏗️
          </div>
        </div>
      )}

      {/* Finishing */}
      {stage === 'finishing' && (
        <div className="w-full h-full relative">
          <BuildingShape
            type={type}
            size={size}
            color={color}
            opacity={0.8}
          />
          <div className="absolute top-1 right-1 text-sm animate-bounce">
            ✨
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Completed Building - Full visual representation
 */
function CompletedBuilding({
  type,
  size,
  icon,
  color,
}: {
  type: BuildingType;
  size: { width: number; height: number };
  icon: string;
  color: string;
}) {
  return (
    <div className="relative w-full h-full">
      <BuildingShape type={type} size={size} color={color} opacity={1.0} />

      {/* Icon overlay */}
      <div
        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
        style={{ fontSize: size.width * 0.4 }}
      >
        {icon}
      </div>

      {/* Subtle glow effect - reduced to make buildings less prominent */}
      <div
        className="absolute inset-0 rounded-lg blur-sm opacity-15 -z-10"
        style={{ background: color }}
      />
    </div>
  );
}

/**
 * Building Shape - Base visual structure
 */
function BuildingShape({
  type,
  size,
  color,
  opacity,
}: {
  type: BuildingType;
  size: { width: number; height: number };
  color: string;
  opacity: number;
}) {
  // Different shapes for different building types
  const shapes: Record<BuildingType, React.ReactNode> = {
    // Simple structures
    campfire: (
      <div
        className="w-full h-full rounded-full"
        style={{
          background: `radial-gradient(circle, ${color} 0%, ${color}80 100%)`,
          opacity,
        }}
      />
    ),

    tent: (
      <div
        className="w-full h-full"
        style={{
          clipPath: 'polygon(50% 0%, 100% 100%, 0% 100%)',
          background: `linear-gradient(180deg, ${color} 0%, ${color}cc 100%)`,
          opacity,
        }}
      />
    ),

    // Basic structures (rectangular)
    shelter: <RectangularBuilding color={color} opacity={opacity} hasRoof />,
    hut: <RectangularBuilding color={color} opacity={opacity} hasRoof />,
    storage: <RectangularBuilding color={color} opacity={opacity} hasRoof={false} />,

    // Production buildings
    farm: <RectangularBuilding color={color} opacity={opacity} hasRoof={false} />,
    workshop: <RectangularBuilding color={color} opacity={opacity} hasRoof />,
    mine: <RectangularBuilding color={color} opacity={opacity} hasRoof />,

    // Advanced structures
    house: <RectangularBuilding color={color} opacity={opacity} hasRoof hasChimney />,
    smelter: <RectangularBuilding color={color} opacity={opacity} hasRoof hasChimney />,
    tower: <TowerBuilding color={color} opacity={opacity} />,

    // Elite structures
    mansion: <MansionBuilding color={color} opacity={opacity} />,
    laboratory: <RectangularBuilding color={color} opacity={opacity} hasRoof />,
  };

  return shapes[type] || shapes.shelter;
}

/**
 * Rectangular Building Component
 */
function RectangularBuilding({
  color,
  opacity,
  hasRoof = true,
  hasChimney = false,
}: {
  color: string;
  opacity: number;
  hasRoof?: boolean;
  hasChimney?: boolean;
}) {
  return (
    <div className="w-full h-full relative">
      {/* Roof */}
      {hasRoof && (
        <div
          className="absolute left-0 right-0"
          style={{
            top: 0,
            height: '40%',
            clipPath: 'polygon(50% 0%, 100% 100%, 0% 100%)',
            background: `linear-gradient(180deg, ${color} 0%, ${color}dd 100%)`,
            opacity,
          }}
        />
      )}

      {/* Walls */}
      <div
        className="absolute left-0 right-0 bottom-0"
        style={{
          height: hasRoof ? '65%' : '100%',
          background: `linear-gradient(180deg, ${color}dd 0%, ${color} 100%)`,
          border: `2px solid ${color}`,
          borderRadius: '4px',
          opacity,
          boxShadow: `0 4px 8px ${color}40`,
        }}
      />

      {/* Chimney */}
      {hasChimney && (
        <div
          className="absolute"
          style={{
            right: '20%',
            top: '-5%',
            width: '15%',
            height: '25%',
            background: color,
            border: `1px solid ${color}`,
            opacity,
          }}
        />
      )}
    </div>
  );
}

/**
 * Tower Building Component
 */
function TowerBuilding({ color, opacity }: { color: string; opacity: number }) {
  return (
    <div className="w-full h-full relative">
      {/* Top */}
      <div
        className="absolute left-0 right-0"
        style={{
          top: 0,
          height: '30%',
          clipPath: 'polygon(50% 0%, 90% 30%, 90% 100%, 10% 100%, 10% 30%)',
          background: color,
          opacity,
        }}
      />

      {/* Main body */}
      <div
        className="absolute"
        style={{
          left: '15%',
          right: '15%',
          top: '25%',
          bottom: 0,
          background: `linear-gradient(180deg, ${color}dd 0%, ${color} 100%)`,
          border: `2px solid ${color}`,
          opacity,
        }}
      />
    </div>
  );
}

/**
 * Mansion Building Component
 */
function MansionBuilding({ color, opacity }: { color: string; opacity: number }) {
  return (
    <div className="w-full h-full relative">
      {/* Multiple roofs */}
      <div
        className="absolute"
        style={{
          left: '10%',
          right: '10%',
          top: 0,
          height: '35%',
          clipPath: 'polygon(50% 0%, 100% 100%, 0% 100%)',
          background: color,
          opacity,
        }}
      />

      {/* Main building */}
      <div
        className="absolute left-0 right-0 bottom-0"
        style={{
          height: '70%',
          background: `linear-gradient(180deg, ${color}dd 0%, ${color} 100%)`,
          border: `3px solid ${color}`,
          borderRadius: '8px',
          opacity,
          boxShadow: `0 8px 16px ${color}40, inset 0 2px 4px ${color}60`,
        }}
      />
    </div>
  );
}

/**
 * Get building size based on type and scale
 */
function getBuildingSize(type: BuildingType, scale: number): { width: number; height: number } {
  // Reduced building sizes to make agents more prominent
  const baseSizes: Record<BuildingType, { width: number; height: number }> = {
    campfire: { width: 14, height: 14 },
    tent: { width: 20, height: 20 },
    shelter: { width: 26, height: 26 },
    hut: { width: 30, height: 30 },
    house: { width: 38, height: 38 },
    storage: { width: 26, height: 24 },
    farm: { width: 32, height: 26 },
    workshop: { width: 32, height: 30 },
    mine: { width: 30, height: 26 },
    smelter: { width: 32, height: 32 },
    tower: { width: 26, height: 46 },
    mansion: { width: 52, height: 52 },
    laboratory: { width: 38, height: 36 },
  };

  const base = baseSizes[type] || { width: 26, height: 26 };

  return {
    width: Math.max(base.width * scale, base.width * 0.8),
    height: Math.max(base.height * scale, base.height * 0.8),
  };
}
