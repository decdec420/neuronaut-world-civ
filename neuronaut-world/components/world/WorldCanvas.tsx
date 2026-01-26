'use client';

import { useEffect, useRef, useState } from 'react';
import * as PIXI from 'pixi.js';
import { Viewport } from 'pixi-viewport';
import {
  createPixiApp,
  createViewport,
  toIsometric,
  COLORS,
  lerp,
  easeOutCubic,
} from '@/lib/pixi-setup';

interface Agent {
  id: string;
  name: string;
  position: { x: number; y: number };
  wealth: number;
  health: number;
  age: number;
  alive: boolean;
}

interface WorldCanvasProps {
  width?: number;
  height?: number;
  worldWidth?: number;
  worldHeight?: number;
  agents?: Agent[];
  onAgentClick?: (agent: Agent) => void;
}

export default function WorldCanvas({
  width = 1200,
  height = 800,
  worldWidth = 100,
  worldHeight = 100,
  agents = [],
  onAgentClick,
}: WorldCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<PIXI.Application | null>(null);
  const viewportRef = useRef<Viewport | null>(null);
  const agentSpritesRef = useRef<Map<string, PIXI.Container>>(new Map());
  const agentDataRef = useRef<Map<string, { targetX: number; targetY: number; currentX: number; currentY: number }>>(
    new Map()
  );
  const agentTexturesRef = useRef<Map<number, PIXI.Texture>>(new Map());

  // Handle window resize to update canvas dimensions
  useEffect(() => {
    const handleResize = () => {
      if (!appRef.current || !containerRef.current) return;

      const container = containerRef.current;
      const rect = container.getBoundingClientRect();
      const newWidth = Math.max(rect.width || width, 100);
      const newHeight = Math.max(rect.height || height, 100);

      console.log('[WorldCanvas] Resizing to:', { newWidth, newHeight });
      appRef.current.renderer.resize(newWidth, newHeight);

      // Update viewport screen size
      if (viewportRef.current) {
        viewportRef.current.resize(newWidth, newHeight);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [width, height]);

  // Initialize Pixi.js
  useEffect(() => {
    if (!canvasRef.current || appRef.current) return;

    console.log('[WorldCanvas] Starting initialization...');

    // Wait for next frame to ensure canvas is properly mounted
    const initPixi = async () => {
      if (!canvasRef.current || appRef.current) return;

      try {
        // Get dimensions from container
        const canvas = canvasRef.current;
        const container = containerRef.current;

        let actualWidth = width;
        let actualHeight = height;

        // If container exists, use its dimensions
        if (container) {
          const rect = container.getBoundingClientRect();
          actualWidth = Math.max(rect.width || width, 100);
          actualHeight = Math.max(rect.height || height, 100);
        } else {
          actualWidth = Math.max(width || 800, 100);
          actualHeight = Math.max(height || 600, 100);
        }

        console.log('[WorldCanvas] Container dimensions:', { actualWidth, actualHeight });
        
        // PIXI v8 requires async initialization
        const app = await createPixiApp(canvas, actualWidth, actualHeight);
        console.log('[WorldCanvas] Pixi app created:', app);

        appRef.current = app;

        // Create viewport for pan/zoom
        const viewport = createViewport(app, worldWidth, worldHeight);
        viewportRef.current = viewport;
        console.log('[WorldCanvas] Viewport created:', viewport);

        // Wait for next frame to ensure viewport is fully initialized
        await new Promise(resolve => requestAnimationFrame(resolve));

        // Create EPIC background layer with gradient
        const bgLayer = new PIXI.Container();
        renderBackground(bgLayer, worldWidth, worldHeight);
        viewport.addChild(bgLayer);
        console.log('[WorldCanvas] Background layer added, children:', bgLayer.children.length);

        // Create terrain layer with depth
        const terrainLayer = new PIXI.Container();
        renderTerrain(terrainLayer, worldWidth, worldHeight);
        viewport.addChild(terrainLayer);
        console.log('[WorldCanvas] Terrain layer added, children:', terrainLayer.children.length);

        // Create shadow layer (rendered before agents)
        const shadowLayer = new PIXI.Container();
        shadowLayer.alpha = 0.3;
        viewport.addChild(shadowLayer);
        console.log('[WorldCanvas] Shadow layer added');

        // Create agent layer with depth sorting
        const agentLayer = new PIXI.Container();
        agentLayer.sortableChildren = true; // Enable depth sorting
        viewport.addChild(agentLayer);
        console.log('[WorldCanvas] Agent layer added');

        // Create effects layer (particles, etc.) - on top
        const effectsLayer = new PIXI.Container();
        viewport.addChild(effectsLayer);
        console.log('[WorldCanvas] Effects layer added');

        console.log('[WorldCanvas] Total viewport children:', viewport.children.length);
        console.log('[WorldCanvas] Viewport bounds:', viewport.getBounds());

        // Animation loop
        app.ticker.add((ticker) => {
          updateAgentPositions(ticker.deltaTime);
        });

        console.log('[WorldCanvas] Initialization complete!');
      } catch (error) {
        console.error('[WorldCanvas] Failed to initialize PIXI:', error);
        console.error('[WorldCanvas] Error stack:', (error as Error).stack);
      }
    };

    initPixi();

    return () => {
      if (appRef.current) {
        appRef.current.destroy(true, { children: true });
        appRef.current = null;
      }
    };
  }, [width, height, worldWidth, worldHeight]);

  // Render background using Canvas2D texture (avoids WebGL shader issues)
  const renderBackground = (layer: PIXI.Container, worldW: number, worldH: number) => {
    const tileSize = 128;
    const worldPixelW = worldW * tileSize;
    const worldPixelH = worldH * tileSize;

    console.log('[WorldCanvas] Rendering background...');

    // Create background using Canvas2D to avoid Graphics API
    const bgCanvas = document.createElement('canvas');
    const bgSize = Math.max(worldPixelW, worldPixelH) * 3;
    bgCanvas.width = bgSize;
    bgCanvas.height = bgSize;
    const bgCtx = bgCanvas.getContext('2d')!;

    // Fill with dark background color
    bgCtx.fillStyle = '#0a0f1a';
    bgCtx.fillRect(0, 0, bgSize, bgSize);

    // Create sprite from canvas texture
    const bgTexture = PIXI.Texture.from(bgCanvas);
    const bgSprite = new PIXI.Sprite(bgTexture);
    bgSprite.x = -worldPixelW;
    bgSprite.y = -worldPixelH;
    layer.addChild(bgSprite);

    console.log('[WorldCanvas] Background complete');
  };

  // Render terrain using Canvas2D texture (avoids WebGL shader issues)
  const renderTerrain = (layer: PIXI.Container, worldW: number, worldH: number) => {
    console.log('[WorldCanvas] Rendering terrain...');

    const tileWidth = 128;
    const tileHeight = 64;

    // Create a single texture for all tiles to minimize draw calls
    const tileCanvas = document.createElement('canvas');
    tileCanvas.width = 60;
    tileCanvas.height = 30;
    const tileCtx = tileCanvas.getContext('2d')!;

    // Draw terrain tile on canvas
    tileCtx.fillStyle = 'rgba(34, 197, 94, 0.2)'; // COLORS.AGRICULTURE with alpha
    tileCtx.fillRect(0, 0, 60, 30);

    // Create texture once
    const tileTexture = PIXI.Texture.from(tileCanvas);

    // Create sprites for each tile position
    for (let y = 0; y < worldH; y += 20) {
      for (let x = 0; x < worldW; x += 20) {
        const iso = toIsometric(x, y, tileWidth, tileHeight);

        const tileSprite = new PIXI.Sprite(tileTexture);
        tileSprite.x = iso.x - 30;
        tileSprite.y = iso.y - 15;
        layer.addChild(tileSprite);
      }
    }

    console.log('[WorldCanvas] Terrain complete');
  };

  // Update agents when prop changes
  useEffect(() => {
    if (!viewportRef.current) return;

    console.log('[WorldCanvas] Updating agents, count:', agents.length);

    const viewport = viewportRef.current;
    // Agent layer is now 4th child (0: bg, 1: terrain, 2: shadow, 3: agent, 4: effects)
    const agentLayer = viewport.children[3] as PIXI.Container;
    if (!agentLayer) {
      console.error('[WorldCanvas] Agent layer not found!');
      return;
    }

    // Remove dead agents and their shadows
    agentSpritesRef.current.forEach((sprite, agentId) => {
      if (!agents.find((a) => a.id === agentId)) {
        // Remove shadow if exists
        const shadow = (sprite as any).shadowRef;
        if (shadow && shadow.parent) {
          shadow.parent.removeChild(shadow);
        }

        // Remove sprite
        agentLayer.removeChild(sprite);
        agentSpritesRef.current.delete(agentId);
        agentDataRef.current.delete(agentId);
      }
    });

    // Update or create agents
    agents.forEach((agent) => {
      let sprite = agentSpritesRef.current.get(agent.id);

      if (!sprite) {
        console.log('[WorldCanvas] Creating agent:', agent.name, 'at', agent.position);

        // Create new agent sprite
        sprite = createAgentSprite(agent);
        agentLayer.addChild(sprite);
        agentSpritesRef.current.set(agent.id, sprite);

        // Initialize position data
        const iso = toIsometric(agent.position.x, agent.position.y);
        console.log('[WorldCanvas] Agent', agent.name, 'isometric position:', iso);

        agentDataRef.current.set(agent.id, {
          targetX: iso.x,
          targetY: iso.y,
          currentX: iso.x,
          currentY: iso.y,
        });

        // Set initial position
        sprite.x = iso.x;
        sprite.y = iso.y;
        sprite.zIndex = Math.floor(agent.position.y + agent.position.x); // Depth sorting

        console.log('[WorldCanvas] Agent', agent.name, 'sprite position:', {x: sprite.x, y: sprite.y, visible: sprite.visible});

        // Create simple shadow for this agent using Canvas2D texture
        const shadowLayer = viewport.children[2] as PIXI.Container;
        if (shadowLayer) {
          // Create shadow texture once (could be cached if needed)
          const shadowCanvas = document.createElement('canvas');
          shadowCanvas.width = 30;
          shadowCanvas.height = 30;
          const shadowCtx = shadowCanvas.getContext('2d')!;

          // Draw shadow circle
          shadowCtx.fillStyle = 'rgba(0, 0, 0, 0.3)';
          shadowCtx.beginPath();
          shadowCtx.arc(15, 15, 15, 0, Math.PI * 2);
          shadowCtx.fill();

          const shadowTexture = PIXI.Texture.from(shadowCanvas);
          const shadow = new PIXI.Sprite(shadowTexture);
          shadow.anchor.set(0.5, 0.5);
          shadow.x = iso.x;
          shadow.y = iso.y + 15;
          shadowLayer.addChild(shadow);

          // Store shadow reference
          (sprite as any).shadowRef = shadow;
        }

        // Add click handler (eventMode already set in createAgentSprite)
        sprite.on('pointerdown', () => {
          if (onAgentClick) onAgentClick(agent);
        });
      } else {
        // Update existing sprite
        const iso = toIsometric(agent.position.x, agent.position.y);
        const data = agentDataRef.current.get(agent.id)!;
        data.targetX = iso.x;
        data.targetY = iso.y;

        // Update visual state
        updateAgentVisuals(sprite, agent);
      }
    });
  }, [agents, onAgentClick]);

  // Create a texture for an agent sprite (pre-rendered to avoid Graphics API shader issues)
  const createAgentTexture = (color: number, radius: number = 20): PIXI.Texture => {
    // Create a simple canvas to draw the agent
    const size = radius * 3; // Extra space for glow
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d')!;

    const centerX = size / 2;
    const centerY = size / 2;

    // Draw glow
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius * 1.5);
    gradient.addColorStop(0, `rgba(${(color >> 16) & 0xff}, ${(color >> 8) & 0xff}, ${color & 0xff}, 0.4)`);
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, size, size);

    // Draw main circle
    ctx.fillStyle = `#${color.toString(16).padStart(6, '0')}`;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.fill();

    // Draw outline
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Create texture from canvas
    return PIXI.Texture.from(canvas);
  };

  // Create visual representation of an agent using Sprite (avoids Graphics API shader issues)
  const createAgentSprite = (agent: Agent): PIXI.Container => {
    const container = new PIXI.Container();

    // Enable interactivity
    container.eventMode = 'static';
    container.cursor = 'pointer';
    container.hitArea = new PIXI.Circle(0, 0, 30);

    const radius = 20;
    const healthColor = getHealthColor(agent.health);

    // Get or create texture for this color
    if (!agentTexturesRef.current.has(healthColor)) {
      const texture = createAgentTexture(healthColor, radius);
      agentTexturesRef.current.set(healthColor, texture);
    }

    const texture = agentTexturesRef.current.get(healthColor);
    if (texture) {
      // Create sprite from pre-rendered texture
      const sprite = new PIXI.Sprite(texture);
      sprite.anchor.set(0.5, 0.5);
      container.addChild(sprite);
    }

    // Add name label
    const nameText = new PIXI.Text({
      text: agent.name,
      style: {
        fontSize: 12,
        fill: 0xffffff,
        stroke: { color: 0x000000, width: 2 },
      },
    });
    nameText.anchor.set(0.5, 1);
    nameText.y = -radius - 5;
    container.addChild(nameText);

    return container;
  };

  // Update agent visuals based on state - SIMPLIFIED
  const updateAgentVisuals = (sprite: PIXI.Container, agent: Agent) => {
    // Just recreate the sprite for now (simple approach)
    // Full redraw would be needed to change colors efficiently
  };

  // Smooth position interpolation - SIMPLIFIED
  const updateAgentPositions = (delta: number) => {
    agentDataRef.current.forEach((data, agentId) => {
      const sprite = agentSpritesRef.current.get(agentId);
      if (!sprite) return;

      // Simple interpolation
      const speed = 0.05 * delta;
      data.currentX = lerp(data.currentX, data.targetX, speed);
      data.currentY = lerp(data.currentY, data.targetY, speed);

      sprite.x = data.currentX;
      sprite.y = data.currentY;

      // Update shadow position
      const shadow = (sprite as any).shadowRef;
      if (shadow) {
        shadow.x = data.currentX;
        shadow.y = data.currentY + 15;
      }
    });
  };

  // Get color based on health
  const getHealthColor = (health: number): number => {
    if (health > 70) return COLORS.HEALTH_GOOD;
    if (health > 30) return COLORS.HEALTH_OK;
    return COLORS.HEALTH_BAD;
  };

  return (
    <div ref={containerRef} className="relative w-full h-full" style={{ minHeight: '500px' }}>
      <canvas ref={canvasRef} />

      {/* Controls Overlay */}
      <div className="absolute top-4 left-4 glass-panel space-y-2 text-sm z-10">
        <div className="font-semibold text-accent">World Controls</div>
        <div className="text-text-muted">
          <div>🖱️ Drag to pan</div>
          <div>🔍 Scroll to zoom</div>
          <div>👆 Click agent for details</div>
        </div>
        <div className="border-t border-border pt-2 mt-2">
          <div className="text-text-muted">Agents: {agents.length}</div>
          <div className="text-text-muted">
            Alive: {agents.filter((a) => a.alive).length}
          </div>
        </div>
      </div>
    </div>
  );
}
