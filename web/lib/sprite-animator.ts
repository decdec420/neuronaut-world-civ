/**
 * SpriteAnimator - Manages sprite sheet animations for agents
 *
 * Supports:
 * - 32x32 pixel art sprites
 * - 4-directional movement (down, up, left, right)
 * - Activity-based animations (idle, walking, working, building)
 * - Frame timing and state management
 */

export type Direction = 'down' | 'up' | 'left' | 'right';
export type Activity = 'idle' | 'walking' | 'working' | 'building' | 'fighting';

export interface SpriteFrame {
  x: number;      // X position in sprite sheet
  y: number;      // Y position in sprite sheet
  width: number;  // Frame width (usually 32px)
  height: number; // Frame height (usually 32px)
}

export interface AnimationConfig {
  frames: SpriteFrame[];
  frameDuration: number; // milliseconds per frame
  loop: boolean;
}

export interface SpriteSheetConfig {
  imagePath: string;
  frameWidth: number;
  frameHeight: number;
  animations: {
    [key in Activity]?: {
      [key in Direction]?: AnimationConfig;
    };
  };
}

export class SpriteAnimator {
  private config: SpriteSheetConfig;
  private currentActivity: Activity = 'idle';
  private currentDirection: Direction = 'down';
  private currentFrameIndex = 0;
  private lastFrameTime = 0;
  private image: HTMLImageElement | null = null;
  private imageLoaded = false;

  constructor(config: SpriteSheetConfig) {
    this.config = config;
    this.loadImage();
  }

  private loadImage() {
    this.image = new Image();
    this.image.src = this.config.imagePath;
    this.image.onload = () => {
      this.imageLoaded = true;
    };
  }

  /**
   * Update animation state based on elapsed time
   */
  update(timestamp: number) {
    if (!this.imageLoaded) return;

    const animation = this.getCurrentAnimation();
    if (!animation) return;

    const elapsed = timestamp - this.lastFrameTime;

    if (elapsed >= animation.frameDuration) {
      this.currentFrameIndex++;

      if (this.currentFrameIndex >= animation.frames.length) {
        if (animation.loop) {
          this.currentFrameIndex = 0;
        } else {
          this.currentFrameIndex = animation.frames.length - 1;
        }
      }

      this.lastFrameTime = timestamp;
    }
  }

  /**
   * Set the current activity (idle, walking, working, etc.)
   */
  setActivity(activity: Activity) {
    if (this.currentActivity !== activity) {
      this.currentActivity = activity;
      this.currentFrameIndex = 0;
      this.lastFrameTime = performance.now();
    }
  }

  /**
   * Set the current direction (down, up, left, right)
   */
  setDirection(direction: Direction) {
    if (this.currentDirection !== direction) {
      this.currentDirection = direction;
      this.currentFrameIndex = 0;
    }
  }

  /**
   * Get the current animation configuration
   */
  private getCurrentAnimation(): AnimationConfig | null {
    const activityAnims = this.config.animations[this.currentActivity];
    if (!activityAnims) return null;

    return activityAnims[this.currentDirection] || null;
  }

  /**
   * Get the current frame to render
   */
  getCurrentFrame(): SpriteFrame | null {
    const animation = this.getCurrentAnimation();
    if (!animation) return null;

    return animation.frames[this.currentFrameIndex] || null;
  }

  /**
   * Get the loaded image
   */
  getImage(): HTMLImageElement | null {
    return this.imageLoaded ? this.image : null;
  }

  /**
   * Check if sprite is ready to render
   */
  isReady(): boolean {
    return this.imageLoaded;
  }

  /**
   * Get current state for debugging
   */
  getState() {
    return {
      activity: this.currentActivity,
      direction: this.currentDirection,
      frameIndex: this.currentFrameIndex,
      imageLoaded: this.imageLoaded,
    };
  }
}

/**
 * Create a standard LPC-style sprite configuration
 * LPC sprites are organized in rows: down, up, left, right
 * Each row has 4 frames for walk cycle
 */
export function createLPCSpriteConfig(imagePath: string): SpriteSheetConfig {
  const frameWidth = 32;
  const frameHeight = 32;
  const frameDuration = 200; // 200ms per frame = 5 FPS animation

  // Helper to create frame array for a row
  const createFrames = (row: number): SpriteFrame[] => [
    { x: 0 * frameWidth, y: row * frameHeight, width: frameWidth, height: frameHeight },
    { x: 1 * frameWidth, y: row * frameHeight, width: frameWidth, height: frameHeight },
    { x: 2 * frameWidth, y: row * frameHeight, width: frameWidth, height: frameHeight },
    { x: 3 * frameWidth, y: row * frameHeight, width: frameWidth, height: frameHeight },
  ];

  // Helper to create idle frame (first frame of walk cycle)
  const createIdleFrame = (row: number): SpriteFrame[] => [
    { x: 0, y: row * frameHeight, width: frameWidth, height: frameHeight },
  ];

  // LPC standard layout:
  // Row 0: Walk down
  // Row 1: Walk up
  // Row 2: Walk left
  // Row 3: Walk right

  return {
    imagePath,
    frameWidth,
    frameHeight,
    animations: {
      idle: {
        down: { frames: createIdleFrame(0), frameDuration: 1000, loop: true },
        up: { frames: createIdleFrame(1), frameDuration: 1000, loop: true },
        left: { frames: createIdleFrame(2), frameDuration: 1000, loop: true },
        right: { frames: createIdleFrame(3), frameDuration: 1000, loop: true },
      },
      walking: {
        down: { frames: createFrames(0), frameDuration, loop: true },
        up: { frames: createFrames(1), frameDuration, loop: true },
        left: { frames: createFrames(2), frameDuration, loop: true },
        right: { frames: createFrames(3), frameDuration, loop: true },
      },
      // Working uses idle pose with slight animation
      working: {
        down: { frames: createIdleFrame(0), frameDuration: 500, loop: true },
        up: { frames: createIdleFrame(1), frameDuration: 500, loop: true },
        left: { frames: createIdleFrame(2), frameDuration: 500, loop: true },
        right: { frames: createIdleFrame(3), frameDuration: 500, loop: true },
      },
    },
  };
}
