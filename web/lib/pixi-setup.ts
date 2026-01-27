import * as PIXI from 'pixi.js';
import { Viewport } from 'pixi-viewport';

/**
 * Initialize Pixi.js application with optimal settings for the civilization viewer
 * PIXI v8 uses async initialization
 */
export async function createPixiApp(canvas: HTMLCanvasElement, width: number, height: number): Promise<PIXI.Application> {
  // Don't pass 0 or invalid values for width/height
  const safeWidth = Math.max(width || 800, 1);
  const safeHeight = Math.max(height || 600, 1);

  console.log('[Pixi] Creating app...');

  // PIXI v8 requires async initialization
  const app = new PIXI.Application();

  await app.init({
    canvas,
    width: safeWidth,
    height: safeHeight,
    backgroundAlpha: 1,
    background: 0x1a2332,
    antialias: true,
    resolution: typeof window !== 'undefined' ? Math.max(window.devicePixelRatio || 1, 1) : 1,
    preference: 'webgl',
  });

  console.log('[Pixi] Renderer type:', app.renderer.type);
  console.log('[Pixi] Canvas size:', { width: safeWidth, height: safeHeight });

  return app;
}

/**
 * Create and configure a viewport for pan/zoom functionality
 * OPTIMIZED for smooth performance
 */
export function createViewport(
  app: PIXI.Application,
  worldWidth: number,
  worldHeight: number
): Viewport {
  // Use BIGGER tile size for more dramatic isometric view
  const tileSize = 128; // Was 64, now 128 for dramatic effect

  // PIXI v8 + pixi-viewport v6 requires the events system
  const viewport = new Viewport({
    events: app.renderer.events,
    screenWidth: app.screen.width,
    screenHeight: app.screen.height,
    worldWidth: worldWidth * tileSize,
    worldHeight: worldHeight * tileSize,
    passiveWheel: false,
    stopPropagation: false,
    disableOnContextMenu: true,
  });

  // Add viewport to stage
  app.stage.addChild(viewport);

  // Activate plugins with OPTIMIZED settings for smoothness
  viewport
    .drag({
      wheel: false,
      pressDrag: true, // Better drag responsiveness
    })
    .pinch()
    .wheel({
      smooth: 3, // Reduced from 5 for faster zoom response
      percent: 0.15, // Slightly faster zoom
      interrupt: true, // Better zoom interruption
    })
    .decelerate({
      friction: 0.92, // Slightly more friction for better control
    })
    .clamp({
      left: -worldWidth * tileSize * 0.5,
      right: worldWidth * tileSize * 1.5,
      top: -worldHeight * tileSize * 0.5,
      bottom: worldHeight * tileSize * 1.5,
      underflow: 'center', // Better edge handling
    })
    .clampZoom({
      minScale: 0.3, // Allow zooming out more
      maxScale: 3.0, // Allow zooming in more
    });

  // Set initial zoom to show more of the world
  viewport.setZoom(0.8);
  viewport.moveCenter(worldWidth * tileSize * 0.5, worldHeight * tileSize * 0.5);

  return viewport;
}

/**
 * Convert world coordinates to isometric screen coordinates
 * Uses a 2:1 ratio isometric projection (30-degree angle)
 * UPDATED for DRAMATIC larger tiles (128x64 instead of 64x32)
 */
export function toIsometric(worldX: number, worldY: number, tileWidth = 128, tileHeight = 64) {
  return {
    x: (worldX - worldY) * (tileWidth / 2),
    y: (worldX + worldY) * (tileHeight / 2),
  };
}

/**
 * Convert isometric screen coordinates back to world coordinates
 */
export function fromIsometric(isoX: number, isoY: number, tileWidth = 128, tileHeight = 64) {
  return {
    x: (isoX / (tileWidth / 2) + isoY / (tileHeight / 2)) / 2,
    y: (isoY / (tileHeight / 2) - isoX / (tileWidth / 2)) / 2,
  };
}

/**
 * Create a sprite pool for performance optimization
 */
export class SpritePool {
  private pool: PIXI.Sprite[] = [];
  private texture: PIXI.Texture;

  constructor(texture: PIXI.Texture, initialSize = 50) {
    this.texture = texture;
    for (let i = 0; i < initialSize; i++) {
      this.pool.push(this.createSprite());
    }
  }

  private createSprite(): PIXI.Sprite {
    const sprite = new PIXI.Sprite(this.texture);
    sprite.visible = false;
    return sprite;
  }

  acquire(): PIXI.Sprite {
    const sprite = this.pool.pop();
    if (sprite) {
      sprite.visible = true;
      return sprite;
    }
    return this.createSprite();
  }

  release(sprite: PIXI.Sprite): void {
    sprite.visible = false;
    this.pool.push(sprite);
  }
}

/**
 * Interpolate between two positions smoothly
 */
export function lerp(start: number, end: number, t: number): number {
  return start + (end - start) * t;
}

/**
 * Easing function for smooth animations (ease-out cubic)
 */
export function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

/**
 * Custom particle type with physics properties
 */
interface Particle extends PIXI.Graphics {
  vx: number;
  vy: number;
  life: number;
}

/**
 * Create a simple particle effect
 */
export function createParticleEffect(
  x: number,
  y: number,
  color: number,
  count = 10
): PIXI.Container {
  const container = new PIXI.Container();
  container.x = x;
  container.y = y;

  for (let i = 0; i < count; i++) {
    const particle = new PIXI.Graphics() as Particle;
    
    // Use PIXI v8 API for drawing
    particle.circle(0, 0, 2 + Math.random() * 3);
    particle.fill(color);

    const angle = (Math.PI * 2 * i) / count;
    const speed = 1 + Math.random() * 2;

    // Set custom physics properties
    particle.vx = Math.cos(angle) * speed;
    particle.vy = Math.sin(angle) * speed;
    particle.life = 1.0;

    container.addChild(particle);
  }

  return container;
}

/**
 * Update particle effect (call each frame)
 */
export function updateParticles(container: PIXI.Container, delta: number): boolean {
  let anyAlive = false;

  container.children.forEach((child) => {
    const particle = child as Particle;

    if (particle.life !== undefined && particle.vx !== undefined && particle.vy !== undefined) {
      particle.x += particle.vx * delta;
      particle.y += particle.vy * delta;
      particle.life -= delta * 0.02;
      particle.alpha = particle.life;

      if (particle.life > 0) {
        anyAlive = true;
      }
    }
  });

  return anyAlive;
}

/**
 * Color constants for different states and systems
 */
export const COLORS = {
  // Agent health status
  HEALTH_GOOD: 0x10b981,
  HEALTH_OK: 0xf59e0b,
  HEALTH_BAD: 0xef4444,

  // Emotion particles
  HAPPY: 0xfbbf24,
  SAD: 0x3b82f6,
  ANGRY: 0xef4444,
  EXCITED: 0xec4899,

  // Systems
  AGRICULTURE: 0x22c55e,
  HEALTH: 0xec4899,
  RELIGION: 0xfbbf24,
  TERRITORY: 0x8b5cf6,
  CHEMISTRY: 0x06b6d4,
  ENERGY: 0xf97316,
  MATERIALS: 0x78716c,
  ECONOMY: 0xeab308,
  LIFE: 0xf43f5e,
  FUN: 0xa78bfa,

  // Special effects
  DEATH: 0x8b5cf6,
  BIRTH: 0xfbbf24,
  DISCOVERY: 0x06b6d4,
  CRISIS: 0xef4444,
};
