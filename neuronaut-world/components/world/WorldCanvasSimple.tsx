'use client';

import { useEffect, useRef, useState, useCallback, memo } from 'react';
import { getSpriteManager } from '@/lib/sprite-manager';
import type { Direction, Activity } from '@/lib/sprite-animator';
import type { Building } from '@/types/structures';
import BuildingSprite from '@/components/world/BuildingSprite';
import { ConstructionSimulator } from '@/lib/construction-simulator';
import { ResearchSimulator } from '@/lib/research-simulator';
import type { AgentKnowledge } from '@/types/technology';
import type { ViewMode, ViewSettings } from '@/types/view-modes';
import { getViewSettings, getDetailLevelFromZoom } from '@/types/view-modes';
import DayNightCycle from '@/components/world/DayNightCycle';

interface Agent {
  id: string;
  name: string;
  position: { x: number; y: number };
  wealth: number;
  health: number;
  age: number;
  alive: boolean;
}

interface WorldCanvasSimpleProps {
  width?: number;
  height?: number;
  worldWidth?: number;
  worldHeight?: number;
  agents?: Agent[];
  buildings?: Building[];
  viewMode?: ViewMode;
  viewSettings?: ViewSettings;
  selectedAgentId?: string | null;
  onAgentClick?: (agent: Agent) => void;
  onBuildingClick?: (building: Building) => void;
  onAgentKnowledgeUpdate?: (knowledge: AgentKnowledge[]) => void;
  onViewChange?: (view: { x: number; y: number; zoom: number }) => void;
}

// Throttle utility function
function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  let lastResult: ReturnType<T>;

  return function(this: any, ...args: Parameters<T>) {
    if (!inThrottle) {
      inThrottle = true;
      lastResult = func.apply(this, args);
      setTimeout(() => inThrottle = false, limit);
    }
    return lastResult;
  };
}

// Memoized terrain tile component
interface TerrainTileProps {
  x: number;
  y: number;
  screenX: number;
  screenY: number;
  scale: number;
  terrainType: 'grassland' | 'forest' | 'water';
  seed: number;
}

const TerrainTile = memo(({ x, y, screenX, screenY, scale, terrainType, seed }: TerrainTileProps) => {
  const tileW = 100 * scale;
  const tileH = 50 * scale;

  // Biome information
  const biomeInfo = {
    grassland: {
      name: '🌾 Grassland Biome',
      description: 'Fertile plains ideal for farming and gathering',
      resources: ['Wheat', 'Vegetables', 'Small Game'],
      difficulty: 'Easy',
    },
    forest: {
      name: '🌲 Forest Biome',
      description: 'Dense woodland rich in timber and wildlife',
      resources: ['Wood', 'Berries', 'Deer'],
      difficulty: 'Medium',
    },
    water: {
      name: '💧 Water Biome',
      description: 'Lakes and rivers teeming with aquatic life',
      resources: ['Fish', 'Fresh Water', 'Reed'],
      difficulty: 'Easy',
    },
  };

  // Enhanced terrain colors with gradients
  const terrainStyles = {
    grassland: {
      bg: 'linear-gradient(135deg, rgba(74, 222, 128, 0.4) 0%, rgba(34, 197, 94, 0.35) 50%, rgba(22, 163, 74, 0.3) 100%)',
      border: 'rgba(34, 197, 94, 0.5)',
      shadow: 'rgba(22, 163, 74, 0.3)',
      accent: '#4ade80',
    },
    forest: {
      bg: 'linear-gradient(135deg, rgba(34, 197, 94, 0.45) 0%, rgba(22, 163, 74, 0.4) 50%, rgba(21, 128, 61, 0.35) 100%)',
      border: 'rgba(21, 128, 61, 0.6)',
      shadow: 'rgba(20, 83, 45, 0.4)',
      accent: '#15803d',
    },
    water: {
      bg: 'linear-gradient(135deg, rgba(96, 165, 250, 0.4) 0%, rgba(59, 130, 246, 0.35) 50%, rgba(37, 99, 235, 0.3) 100%)',
      border: 'rgba(59, 130, 246, 0.5)',
      shadow: 'rgba(29, 78, 216, 0.3)',
      accent: '#3b82f6',
    },
  };

  const style = terrainStyles[terrainType];
  const info = biomeInfo[terrainType];

  return (
    <div
      className="absolute group"
      style={{
        left: screenX,
        top: screenY,
        transform: 'translate(-50%, -50%)',
        cursor: 'default',
      }}
      title={`${info.name}\n${info.description}\nResources: ${info.resources.join(', ')}`}
    >
      {/* Main tile body with gradient */}
      <div
        style={{
          width: tileW,
          height: tileH,
          background: style.bg,
          border: `1.5px solid ${style.border}`,
          clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
          boxShadow: `
            0 6px 12px ${style.shadow},
            inset 0 2px 4px rgba(255, 255, 255, 0.1),
            inset 0 -2px 4px rgba(0, 0, 0, 0.2)
          `,
          position: 'relative',
        }}
      >
        {/* Texture overlay for grassland */}
        {terrainType === 'grassland' && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundImage: `
                radial-gradient(circle at 20% 30%, rgba(74, 222, 128, 0.3) 1px, transparent 1px),
                radial-gradient(circle at 60% 70%, rgba(74, 222, 128, 0.25) 1px, transparent 1px),
                radial-gradient(circle at 80% 40%, rgba(74, 222, 128, 0.2) 1px, transparent 1px)
              `,
              backgroundSize: '15px 15px, 20px 20px, 18px 18px',
              backgroundPosition: '0 0, 5px 5px, 10px 10px',
              opacity: 0.6,
            }}
          />
        )}

        {/* Resource Nodes - VISIBLE gameplay elements */}

        {/* Forest: Harvestable Trees */}
        {terrainType === 'forest' && seed % 3 === 0 && (
          <div
            className="absolute cursor-pointer hover:scale-110 transition-transform"
            style={{
              left: '50%',
              top: '30%',
              transform: 'translate(-50%, -50%)',
            }}
            title="🌲 Oak Tree\nProvides: 15 Wood\nHealth: 100%"
          >
            {/* Tree trunk */}
            <div style={{
              width: '4px',
              height: '16px',
              background: '#6b4423',
              marginLeft: '6px',
            }} />
            {/* Tree foliage */}
            <div style={{
              width: '16px',
              height: '16px',
              background: 'radial-gradient(circle, #22c55e 0%, #15803d 100%)',
              borderRadius: '50%',
              marginTop: '-18px',
              border: '2px solid #15803d',
              filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
            }}>
              <div className="text-xs text-center leading-4">🌲</div>
            </div>
          </div>
        )}

        {/* Grassland: Rocks and Berry Bushes */}
        {terrainType === 'grassland' && seed % 4 === 0 && (
          <div
            className="absolute cursor-pointer hover:scale-110 transition-transform"
            style={{
              left: '40%',
              top: '35%',
              transform: 'translate(-50%, -50%)',
            }}
            title="⛰️ Stone Deposit\nProvides: 20 Stone\nHealth: 100%"
          >
            <div style={{
              width: '14px',
              height: '10px',
              background: 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)',
              borderRadius: '30% 70% 70% 30% / 60% 40% 60% 40%',
              border: '1px solid #475569',
              filter: 'drop-shadow(0 2px 3px rgba(0,0,0,0.4))',
            }}>
              <div className="text-xs text-center">⛰️</div>
            </div>
          </div>
        )}

        {terrainType === 'grassland' && seed % 5 === 0 && (
          <div
            className="absolute cursor-pointer hover:scale-110 transition-transform"
            style={{
              left: '60%',
              top: '40%',
              transform: 'translate(-50%, -50%)',
            }}
            title="🫐 Berry Bush\nProvides: 8 Food\nHealth: 100%"
          >
            <div style={{
              width: '12px',
              height: '12px',
              background: 'radial-gradient(circle, #4ade80 0%, #22c55e 100%)',
              borderRadius: '40% 60% 60% 40% / 50% 50% 50% 50%',
              border: '1px solid #16a34a',
              filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.3))',
            }}>
              <div className="text-xs text-center leading-3">🫐</div>
            </div>
          </div>
        )}

        {/* Water ripple effect */}
        {terrainType === 'water' && (
          <div
            className="animate-pulse"
            style={{
              position: 'absolute',
              inset: 0,
              background: `
                radial-gradient(ellipse at 30% 40%, rgba(147, 197, 253, 0.3) 0%, transparent 50%),
                radial-gradient(ellipse at 70% 60%, rgba(147, 197, 253, 0.25) 0%, transparent 50%)
              `,
              animationDuration: '3s',
              opacity: 0.6,
            }}
          />
        )}

        {/* Top highlight for depth */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: '50%',
            transform: 'translateX(-50%)',
            width: '80%',
            height: '30%',
            background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.15) 0%, transparent 100%)',
            clipPath: 'polygon(50% 0%, 100% 30%, 50% 60%, 0% 30%)',
          }}
        />
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison - only re-render if these specific props change
  return (
    prevProps.x === nextProps.x &&
    prevProps.y === nextProps.y &&
    prevProps.screenX === nextProps.screenX &&
    prevProps.screenY === nextProps.screenY &&
    prevProps.scale === nextProps.scale &&
    prevProps.terrainType === nextProps.terrainType &&
    prevProps.seed === nextProps.seed
  );
});

export default function WorldCanvasSimple({
  width = 1200,
  height = 800,
  worldWidth = 100,
  worldHeight = 100,
  agents = [],
  buildings = [],
  viewMode = 'normal',
  viewSettings: externalViewSettings,
  selectedAgentId = null,
  onAgentClick,
  onBuildingClick,
  onAgentKnowledgeUpdate,
  onViewChange,
}: WorldCanvasSimpleProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.8);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Momentum/inertia for smooth panning
  const velocityRef = useRef({ x: 0, y: 0 });
  const lastPosRef = useRef({ x: 0, y: 0, time: 0 });
  const animationFrameRef = useRef<number>();

  // Smooth zoom state
  const targetScaleRef = useRef(0.8);
  const currentScaleRef = useRef(0.8);

  // Sprite animation state
  const spriteManagerRef = useRef(getSpriteManager());
  const lastAgentPositionsRef = useRef<Map<string, { x: number; y: number }>>(new Map());
  const [spriteUpdateTrigger, setSpriteUpdateTrigger] = useState(0);

  // Construction progress animation
  const constructionSimulatorRef = useRef<ConstructionSimulator | null>(null);
  const [liveBuildings, setLiveBuildings] = useState<Building[]>(buildings);

  // Research progress animation
  const researchSimulatorRef = useRef<ResearchSimulator | null>(null);

  // View settings based on current mode and zoom
  const [internalViewSettings, setInternalViewSettings] = useState<ViewSettings>(
    externalViewSettings || getViewSettings(viewMode)
  );
  const viewSettings = externalViewSettings || internalViewSettings;
  const [hoveredAgentId, setHoveredAgentId] = useState<string | null>(null);
  const [hoveredBuildingId, setHoveredBuildingId] = useState<string | null>(null);

  // Day/night cycle tick
  const [currentTick, setCurrentTick] = useState(0);

  // PERFORMANCE: Dirty flag for animation loop
  const dirtyFlagRef = useRef(true);
  const setDirty = useCallback(() => {
    dirtyFlagRef.current = true;
  }, []);

  // PERFORMANCE: Lazy-loaded sprite images cache
  const loadedSpritesRef = useRef<Set<string>>(new Set());

  // Update internal view settings when external settings change
  useEffect(() => {
    if (externalViewSettings) {
      setInternalViewSettings(externalViewSettings);
    }
  }, [externalViewSettings]);

  // Update view settings when mode changes (only if no external settings)
  useEffect(() => {
    if (!externalViewSettings) {
      setInternalViewSettings(getViewSettings(viewMode));
    }
  }, [viewMode, externalViewSettings]);

  // Update detail level based on zoom (only if no external settings)
  useEffect(() => {
    if (!externalViewSettings) {
      const detailLevel = getDetailLevelFromZoom(scale);
      setInternalViewSettings((prev) => ({ ...prev, detailLevel }));
    }
  }, [scale, externalViewSettings]);

  // Notify parent of view changes
  useEffect(() => {
    if (onViewChange) {
      onViewChange({ x: offset.x, y: offset.y, zoom: scale });
    }
  }, [offset, scale, onViewChange]);

  // Day/night cycle ticker - increments every 100ms (10 ticks per second)
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTick((prev) => prev + 1);
    }, 100);

    return () => clearInterval(interval);
  }, []);

  // Get health color
  const getHealthColor = (health: number): string => {
    if (health > 70) return '#10b981'; // green
    if (health > 30) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  // Get life stage based on age
  const getLifeStage = (age: number): 'child' | 'young' | 'adult' | 'elder' => {
    if (age < 15) return 'child';
    if (age < 25) return 'young';
    if (age < 55) return 'adult';
    return 'elder';
  };

  // Get size multiplier based on life stage
  const getLifeStageSize = (stage: 'child' | 'young' | 'adult' | 'elder'): number => {
    switch (stage) {
      case 'child': return 0.65;
      case 'young': return 0.85;
      case 'adult': return 1.0;
      case 'elder': return 0.9;
    }
  };

  // Get life stage indicator emoji
  const getLifeStageIndicator = (stage: 'child' | 'young' | 'adult' | 'elder'): string => {
    switch (stage) {
      case 'child': return '👶';
      case 'young': return '🧒';
      case 'adult': return '🧑';
      case 'elder': return '👴';
    }
  };

  // Convert world coordinates to screen coordinates - memoized
  const worldToScreen = useCallback((wx: number, wy: number) => {
    const tileSize = 8; // Pixels per world unit
    return {
      x: (wx * tileSize * scale) + offset.x + (width / 2),
      y: (wy * tileSize * scale) + offset.y + (height / 2),
    };
  }, [scale, offset.x, offset.y, width]);

  // Calculate direction based on position change
  const calculateDirection = (oldPos: { x: number; y: number }, newPos: { x: number; y: number }): Direction => {
    const dx = newPos.x - oldPos.x;
    const dy = newPos.y - oldPos.y;

    if (Math.abs(dx) > Math.abs(dy)) {
      return dx > 0 ? 'right' : 'left';
    } else {
      return dy > 0 ? 'down' : 'up';
    }
  };

  // Calculate activity based on position change and agent state
  const calculateActivity = (agent: Agent, isMoving: boolean): Activity => {
    // TODO: Add more sophisticated activity detection based on agent state
    // For now, just use walking vs idle
    return isMoving ? 'walking' : 'idle';
  };

  // Initialize construction simulator when buildings change
  useEffect(() => {
    // Create deep copy of buildings to avoid mutating props
    const buildingsCopy = buildings.map(b => ({ ...b }));

    if (!constructionSimulatorRef.current) {
      constructionSimulatorRef.current = new ConstructionSimulator(buildingsCopy);
    }

    setLiveBuildings(buildingsCopy);
  }, [buildings]);

  // Initialize research simulator when agents change
  useEffect(() => {
    if (!researchSimulatorRef.current && agents.length > 0) {
      const agentData = agents.map(a => ({ id: a.id, wealth: a.wealth }));
      researchSimulatorRef.current = new ResearchSimulator(agentData);
    }
  }, [agents]);

  // Update sprite animations when agents change
  useEffect(() => {
    agents.forEach((agent) => {
      if (!agent.alive) return;

      const spriteManager = spriteManagerRef.current;
      const lastPos = lastAgentPositionsRef.current.get(agent.id);

      // Get or create sprite animator for this agent
      const variationIndex = agent.id.charCodeAt(0) % 8; // Use agent ID to determine variation
      const sprite = spriteManager.getSpriteAnimator(agent.id, variationIndex);

      // PERFORMANCE: Lazy load sprite images
      if (!loadedSpritesRef.current.has(agent.id)) {
        loadedSpritesRef.current.add(agent.id);
      }

      // Check if agent moved
      const isMoving = lastPos && (lastPos.x !== agent.position.x || lastPos.y !== agent.position.y);

      if (isMoving && lastPos) {
        // Agent is moving - calculate direction and set to walking
        const direction = calculateDirection(lastPos, agent.position);
        sprite.setDirection(direction);
        sprite.setActivity('walking');
        setDirty(); // Mark dirty when agent moves
      } else {
        // Agent is idle
        sprite.setActivity('idle');
      }

      // Update last position
      lastAgentPositionsRef.current.set(agent.id, { ...agent.position });
    });
  }, [agents, setDirty]);

  // PERFORMANCE: Smooth zoom, momentum, and construction animation loop with dirty flag
  useEffect(() => {
    const animate = (timestamp: number) => {
      let needsUpdate = false;

      // PERFORMANCE: Only update if dirty flag is set
      if (dirtyFlagRef.current) {
        // Update all sprite animations
        spriteManagerRef.current.updateAll(timestamp);
        setSpriteUpdateTrigger(prev => prev + 1); // Trigger re-render for sprite frames
        needsUpdate = true;
      }

      // Update construction progress
      if (constructionSimulatorRef.current) {
        const updates = constructionSimulatorRef.current.update();
        if (updates.length > 0) {
          // Get updated buildings from simulator
          const updatedBuildings = constructionSimulatorRef.current.getAllBuildings();
          setLiveBuildings([...updatedBuildings]); // Create new array to trigger re-render

          // Log completion events
          updates.forEach(update => {
            if (update.justCompleted) {
              console.log(`🎉 Building ${update.buildingId} construction completed!`);
            }
          });

          needsUpdate = true;
        }
      }

      // Update research progress
      if (researchSimulatorRef.current) {
        const updates = researchSimulatorRef.current.update();
        if (updates.length > 0) {
          // Notify parent component of knowledge updates
          if (onAgentKnowledgeUpdate) {
            const allKnowledge = researchSimulatorRef.current.getAllKnowledge();
            onAgentKnowledgeUpdate(allKnowledge);
          }

          needsUpdate = true;
        }
      }

      // Smooth zoom animation (lerp towards target)
      const zoomDiff = Math.abs(targetScaleRef.current - currentScaleRef.current);
      if (zoomDiff > 0.001) {
        currentScaleRef.current += (targetScaleRef.current - currentScaleRef.current) * 0.15;
        setScale(currentScaleRef.current);
        needsUpdate = true;
      }

      // Momentum/deceleration for panning (friction: 0.92)
      if (!isDragging && (Math.abs(velocityRef.current.x) > 0.1 || Math.abs(velocityRef.current.y) > 0.1)) {
        velocityRef.current.x *= 0.92;
        velocityRef.current.y *= 0.92;

        setOffset(prev => ({
          x: prev.x + velocityRef.current.x,
          y: prev.y + velocityRef.current.y,
        }));
        needsUpdate = true;
      } else if (!isDragging) {
        velocityRef.current = { x: 0, y: 0 };
      }

      // PERFORMANCE: Clear dirty flag if nothing needs update
      if (!needsUpdate) {
        dirtyFlagRef.current = false;
      }

      // Continue animation loop
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isDragging, onAgentKnowledgeUpdate]);

  // PERFORMANCE: Throttled mouse handlers (16ms = ~60fps max)
  const handleWheel = useCallback(throttle((e: React.WheelEvent) => {
    e.preventDefault();

    // Zoom 15% per wheel tick (matching pixi-viewport percent: 0.15)
    const zoomFactor = e.deltaY > 0 ? 0.85 : 1.15;
    const newScale = Math.max(0.3, Math.min(3.0, targetScaleRef.current * zoomFactor));

    targetScaleRef.current = newScale;
    setDirty(); // Mark dirty for zoom change

    // Trigger animation
    if (!animationFrameRef.current) {
      animationFrameRef.current = requestAnimationFrame(() => {});
    }
  }, 16), []);

  // Handle mouse down for panning
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
    lastPosRef.current = { x: e.clientX, y: e.clientY, time: Date.now() };
    velocityRef.current = { x: 0, y: 0 };
    setDirty(); // Mark dirty when drag starts
  }, [offset.x, offset.y, setDirty]);

  // PERFORMANCE: Throttled mouse move handler
  const handleMouseMove = useCallback(throttle((e: React.MouseEvent) => {
    if (isDragging) {
      const now = Date.now();
      const dt = now - lastPosRef.current.time;

      if (dt > 0) {
        // Calculate velocity for momentum
        const dx = e.clientX - lastPosRef.current.x;
        const dy = e.clientY - lastPosRef.current.y;

        velocityRef.current.x = dx / Math.max(dt, 1) * 16; // Convert to per-frame velocity
        velocityRef.current.y = dy / Math.max(dt, 1) * 16;
      }

      setOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });

      lastPosRef.current = { x: e.clientX, y: e.clientY, time: now };
      setDirty(); // Mark dirty on mouse move
    }
  }, 16), [isDragging, dragStart.x, dragStart.y, setDirty]);

  // Handle mouse up
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    // Momentum will continue in the animation loop
  }, []);

  return (
    <div className="relative w-full h-full" style={{ minHeight: '500px' }}>
      <div
        ref={containerRef}
        className="absolute inset-0 bg-slate-900 overflow-hidden cursor-move"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Enhanced background with depth */}
        <div className="absolute inset-0" style={{
          background: 'radial-gradient(circle at 50% 50%, rgba(30, 41, 59, 1) 0%, rgba(15, 23, 42, 1) 100%)',
        }} />

        {/* Day/Night Cycle */}
        <DayNightCycle tick={currentTick} cycleDuration={600} enabled={true} />

        {/* Static reference grid - subtle */}
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: `
            linear-gradient(rgba(100, 116, 139, 0.2) 1px, transparent 1px),
            linear-gradient(90deg, rgba(100, 116, 139, 0.2) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }} />

        {/* Floating particles for ambiance */}
        {Array.from({ length: 15 }).map((_, i) => (
          <div
            key={`particle-${i}`}
            className="absolute rounded-full animate-pulse"
            style={{
              left: `${(i * 37 + 10) % 90}%`,
              top: `${(i * 53 + 15) % 80}%`,
              width: `${2 + (i % 3)}px`,
              height: `${2 + (i % 3)}px`,
              backgroundColor: `rgba(147, 197, 253, ${0.3 + (i % 3) * 0.1})`,
              filter: 'blur(1px)',
              animationDuration: `${3 + (i % 4)}s`,
              animationDelay: `${i * 0.3}s`,
              pointerEvents: 'none',
            }}
          />
        ))}

        {/* PERFORMANCE: Terrain tiles - Memoized components */}
        {Array.from({ length: 15 }, (_, y) => y * 10).map(y =>
          Array.from({ length: 15 }, (_, x) => x * 10).map(x => {
            const screenPos = worldToScreen(x, y);

            // Create terrain variation based on position
            const seed = (x * 7 + y * 13) % 10;
            const terrainType = seed > 7 ? 'water' : seed > 5 ? 'forest' : 'grassland';

            return (
              <TerrainTile
                key={`tile-${x}-${y}`}
                x={x}
                y={y}
                screenX={screenPos.x}
                screenY={screenPos.y}
                scale={scale}
                terrainType={terrainType}
                seed={seed}
              />
            );
          })
        )}

        {/* Buildings - Rendered between terrain and agents */}
        {liveBuildings.map(building => {
          const screenPos = worldToScreen(building.position.x, building.position.y);

          return (
            <div
              key={building.id}
              className="absolute"
              style={{
                left: screenPos.x,
                top: screenPos.y,
                transform: 'translate(-50%, -50%)',
                zIndex: 10, // Above terrain, below agents
              }}
            >
              <BuildingSprite
                building={building}
                scale={scale}
                onClick={onBuildingClick}
                showOwner={viewSettings.showBuildingOwners}
                showProgress={viewSettings.showBuildingProgress}
              />
            </div>
          );
        })}

        {/* Agents - Sprite Based */}
        {agents.map(agent => {
          if (!agent.alive) return null;

          const screenPos = worldToScreen(agent.position.x, agent.position.y);
          const healthColor = getHealthColor(agent.health);

          // Get sprite for this agent
          const variationIndex = agent.id.charCodeAt(0) % 8;
          const sprite = spriteManagerRef.current.getSpriteAnimator(agent.id, variationIndex);

          // Determine life stage based on age and adjust sprite size accordingly
          const lifeStage = getLifeStage(agent.age);
          const lifeStageSizeMultiplier = getLifeStageSize(lifeStage);
          const spriteSize = Math.max(32, 32 * scale * lifeStageSizeMultiplier); // Scale sprites but keep minimum readable size

          // Get current sprite frame
          const frame = sprite.getCurrentFrame();
          const image = sprite.getImage();

          const isSelected = agent.id === selectedAgentId;
          const isHovered = agent.id === hoveredAgentId;
          const shouldShowName = viewSettings.showAgentNames || (viewSettings.hoverOnly && isHovered) || isSelected;
          const shouldShowActivity = viewSettings.showAgentActivities && (viewSettings.detailLevel !== 'minimal');
          const shouldShowHealth = viewSettings.showAgentHealth;

          return (
            <div
              key={agent.id}
              className="absolute cursor-pointer hover:scale-110 hover:z-50"
              style={{
                left: screenPos.x,
                top: screenPos.y,
                transform: 'translate(-50%, -50%)',
                transition: 'transform 0.2s ease-out',
                zIndex: isSelected ? 100 : 20,
              }}
              onClick={() => onAgentClick?.(agent)}
              onMouseEnter={() => setHoveredAgentId(agent.id)}
              onMouseLeave={() => setHoveredAgentId(null)}
            >
              {/* Selection highlight ring */}
              {isSelected && (
                <div
                  className="absolute rounded-full animate-pulse"
                  style={{
                    width: spriteSize * 1.8,
                    height: spriteSize * 1.8,
                    border: '3px solid #ffffff',
                    left: '50%',
                    top: '50%',
                    transform: 'translate(-50%, -50%)',
                    pointerEvents: 'none',
                    boxShadow: '0 0 12px rgba(255, 255, 255, 0.8)',
                    animationDuration: '1.5s',
                  }}
                />
              )}

              {/* Multi-layer health glow for depth */}
              {shouldShowHealth && (
                <>
                  <div
                    className="absolute rounded-full blur-xl animate-pulse"
                    style={{
                      width: spriteSize * 2,
                      height: spriteSize * 2,
                      background: `radial-gradient(circle, ${healthColor}40 0%, ${healthColor}10 50%, transparent 100%)`,
                      left: '50%',
                      top: '50%',
                      transform: 'translate(-50%, -50%)',
                      animationDuration: '2.5s',
                      pointerEvents: 'none',
                    }}
                  />
                  <div
                    className="absolute rounded-full blur-md animate-pulse"
                    style={{
                      width: spriteSize * 1.3,
                      height: spriteSize * 1.3,
                      backgroundColor: healthColor,
                      opacity: 0.3,
                      left: '50%',
                      top: '50%',
                      transform: 'translate(-50%, -50%)',
                      animationDuration: '2s',
                      pointerEvents: 'none',
                    }}
                  />
                </>
              )}

              {/* Wealth ring with shimmer effect */}
              {agent.wealth > 120 && (
                <>
                  <div
                    className="absolute rounded-full animate-spin"
                    style={{
                      width: spriteSize * 1.5,
                      height: spriteSize * 1.5,
                      border: `2.5px solid #fbbf24`,
                      borderTopColor: 'transparent',
                      borderRightColor: 'transparent',
                      left: '50%',
                      top: '50%',
                      transform: 'translate(-50%, -50%)',
                      animationDuration: '3s',
                      opacity: 0.9,
                      filter: 'drop-shadow(0 0 6px #fbbf24)',
                      pointerEvents: 'none',
                    }}
                  />
                  <div
                    className="absolute rounded-full blur-sm animate-pulse"
                    style={{
                      width: spriteSize * 1.6,
                      height: spriteSize * 1.6,
                      backgroundColor: '#fbbf24',
                      left: '50%',
                      top: '50%',
                      transform: 'translate(-50%, -50%)',
                      animationDuration: '2s',
                      opacity: 0.15,
                      pointerEvents: 'none',
                    }}
                  />
                </>
              )}

              {/* Sprite rendering */}
              {sprite.isReady() && frame && image && (
                <canvas
                  ref={(canvas) => {
                    if (canvas) {
                      const ctx = canvas.getContext('2d');
                      if (ctx) {
                        canvas.width = spriteSize;
                        canvas.height = spriteSize;
                        ctx.imageSmoothingEnabled = false; // Pixel-perfect rendering
                        ctx.clearRect(0, 0, spriteSize, spriteSize);

                        // Draw current sprite frame
                        ctx.drawImage(
                          image,
                          frame.x, frame.y, frame.width, frame.height,  // Source rectangle
                          0, 0, spriteSize, spriteSize                   // Destination rectangle
                        );
                      }
                    }
                  }}
                  className="relative"
                  style={{
                    width: spriteSize,
                    height: spriteSize,
                    imageRendering: 'pixelated',
                    filter: `drop-shadow(0 2px 4px rgba(0,0,0,0.5))`,
                  }}
                />
              )}

              {/* Activity Indicator - Shows what agent is doing */}
              {shouldShowActivity && (
                <div
                  className="absolute whitespace-nowrap"
                  style={{
                    left: '50%',
                    top: -spriteSize / 2 - 32,
                    transform: 'translateX(-50%)',
                    pointerEvents: 'none',
                  }}
                >
                  <div
                    className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold"
                    style={{
                      background: 'linear-gradient(135deg, rgba(167, 139, 250, 0.9) 0%, rgba(96, 165, 250, 0.9) 100%)',
                      border: '1px solid rgba(255, 255, 255, 0.3)',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
                      color: '#ffffff',
                    }}
                  >
                    {/* Determine activity based on agent state */}
                    {agent.health < 50 ? (
                      <>💤 Resting</>
                    ) : agent.wealth < 50 ? (
                      <>🫐 Gathering</>
                    ) : agent.wealth > 120 ? (
                      <>🏗️ Building</>
                    ) : (
                      <>🚶 Exploring</>
                    )}
                  </div>
                </div>
              )}

              {/* Name label with enhanced styling */}
              {shouldShowName && (
                <div
                  className="absolute whitespace-nowrap text-xs font-bold"
                  style={{
                    left: '50%',
                    top: -spriteSize / 2 - 12,
                    transform: 'translateX(-50%)',
                    fontSize: `${12 * Math.min(scale, 1.5)}px`,
                    letterSpacing: '0.5px',
                    background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(240,240,240,0.9) 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.8)) drop-shadow(0 0 8px rgba(0,0,0,0.6))',
                    padding: '2px 6px',
                    pointerEvents: 'none',
                  }}
                >
                  {agent.name}
                </div>
              )}

              {/* Life Stage Indicator */}
              {viewSettings.detailLevel !== 'minimal' && (
                <div
                  className="absolute"
                  style={{
                    left: '50%',
                    bottom: -spriteSize / 2 - 20,
                    transform: 'translateX(-50%)',
                    pointerEvents: 'none',
                  }}
                >
                  <div
                    className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold"
                    style={{
                      background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)',
                      border: '1px solid rgba(100, 116, 139, 0.4)',
                      boxShadow: '0 2px 6px rgba(0, 0, 0, 0.3)',
                      color: '#94a3b8',
                      fontSize: `${10 * Math.min(scale, 1.2)}px`,
                    }}
                  >
                    <span>{getLifeStageIndicator(lifeStage)}</span>
                    <span style={{ color: lifeStage === 'elder' ? '#fbbf24' : lifeStage === 'child' ? '#22c55e' : '#94a3b8' }}>
                      {agent.age}y
                    </span>
                  </div>
                </div>
              )}

              {/* Multi-layer shadow for depth */}
              <div
                className="absolute"
                style={{
                  left: '50%',
                  top: spriteSize / 2 + 6,
                  transform: 'translateX(-50%)',
                  pointerEvents: 'none',
                }}
              >
                {/* Outer shadow (larger, softer) */}
                <div
                  className="absolute rounded-full"
                  style={{
                    width: spriteSize * 1.1,
                    height: spriteSize * 0.4,
                    backgroundColor: 'rgba(0, 0, 0, 0.2)',
                    left: '50%',
                    top: 0,
                    transform: 'translateX(-50%)',
                    filter: 'blur(10px)',
                  }}
                />
                {/* Inner shadow (smaller, darker) */}
                <div
                  className="absolute rounded-full"
                  style={{
                    width: spriteSize * 0.7,
                    height: spriteSize * 0.25,
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    left: '50%',
                    top: 0,
                    transform: 'translateX(-50%)',
                    filter: 'blur(5px)',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Controls Overlay - Enhanced with glassmorphism */}
      <div
        className="absolute top-4 left-4 space-y-3 text-sm z-10"
        style={{
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.9) 100%)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          border: '1px solid rgba(100, 116, 139, 0.3)',
          borderRadius: '12px',
          padding: '16px',
          boxShadow: `
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1)
          `,
        }}
      >
        {/* Title with gradient */}
        <div
          className="font-bold text-base"
          style={{
            background: 'linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            letterSpacing: '0.5px',
          }}
        >
          🎮 World Controls
        </div>

        {/* Instructions */}
        <div className="space-y-2 text-xs" style={{ color: 'rgba(203, 213, 225, 0.9)' }}>
          <div className="flex items-center gap-2">
            <span className="text-base">🖱️</span>
            <span>Drag to pan (with momentum)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-base">🔍</span>
            <span>Scroll to zoom</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-base">👆</span>
            <span>Click agent for details</span>
          </div>
        </div>

        {/* Divider */}
        <div
          style={{
            height: '1px',
            background: 'linear-gradient(90deg, transparent 0%, rgba(100, 116, 139, 0.5) 50%, transparent 100%)',
          }}
        />

        {/* Stats with enhanced styling */}
        <div className="space-y-2 text-xs">
          <div className="flex justify-between items-center">
            <span style={{ color: 'rgba(148, 163, 184, 0.8)' }}>Zoom</span>
            <span
              className="font-semibold px-2 py-0.5 rounded"
              style={{
                background: 'linear-gradient(135deg, rgba(167, 139, 250, 0.2) 0%, rgba(96, 165, 250, 0.2) 100%)',
                color: '#a78bfa',
                border: '1px solid rgba(167, 139, 250, 0.3)',
              }}
            >
              {(scale * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span style={{ color: 'rgba(148, 163, 184, 0.8)' }}>Agents</span>
            <span
              className="font-semibold px-2 py-0.5 rounded"
              style={{
                background: 'linear-gradient(135deg, rgba(96, 165, 250, 0.2) 0%, rgba(34, 211, 238, 0.2) 100%)',
                color: '#60a5fa',
                border: '1px solid rgba(96, 165, 250, 0.3)',
              }}
            >
              {agents.length}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span style={{ color: 'rgba(148, 163, 184, 0.8)' }}>Alive</span>
            <span
              className="font-semibold px-2 py-0.5 rounded"
              style={{
                background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(74, 222, 128, 0.2) 100%)',
                color: '#4ade80',
                border: '1px solid rgba(74, 222, 128, 0.3)',
              }}
            >
              {agents.filter((a) => a.alive).length}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span style={{ color: 'rgba(148, 163, 184, 0.8)' }}>Buildings</span>
            <span
              className="font-semibold px-2 py-0.5 rounded"
              style={{
                background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2) 0%, rgba(245, 158, 11, 0.2) 100%)',
                color: '#fbbf24',
                border: '1px solid rgba(251, 191, 36, 0.3)',
              }}
            >
              {liveBuildings.length}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span style={{ color: 'rgba(148, 163, 184, 0.8)' }}>Under Construction</span>
            <span
              className="font-semibold px-2 py-0.5 rounded"
              style={{
                background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(147, 51, 234, 0.2) 100%)',
                color: '#a855f7',
                border: '1px solid rgba(168, 85, 247, 0.3)',
              }}
            >
              {liveBuildings.filter(b => b.stage !== 'completed').length}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span style={{ color: 'rgba(148, 163, 184, 0.8)' }}>Technologies</span>
            <span
              className="font-semibold px-2 py-0.5 rounded"
              style={{
                background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%)',
                color: '#22d3ee',
                border: '1px solid rgba(34, 211, 238, 0.3)',
              }}
            >
              {researchSimulatorRef.current?.getTotalDiscoveries() || 0}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
