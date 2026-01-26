/**
 * SpriteManager - Manages loading and caching of sprite sheets
 *
 * Provides:
 * - Sprite sheet preloading
 * - Placeholder sprite generation
 * - Character variation system
 */

import { SpriteAnimator, createLPCSpriteConfig } from './sprite-animator';

export interface CharacterVariation {
  name: string;
  skinColor: string;
  hairColor: string;
  shirtColor: string;
  pantsColor: string;
}

/**
 * Generate a simple 32x32 pixel art character sprite as a data URL
 * Creates a sprite sheet with 4 rows (down, up, left, right) x 4 frames each
 */
export function generatePlaceholderSprite(variation: CharacterVariation): string {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (!ctx) return '';

  // Sprite sheet: 4 frames wide x 4 rows tall
  canvas.width = 128; // 4 frames * 32px
  canvas.height = 128; // 4 rows * 32px

  ctx.imageSmoothingEnabled = false;

  const { skinColor, hairColor, shirtColor, pantsColor } = variation;

  // Helper to draw a pixel
  const pixel = (x: number, y: number, color: string, size = 2) => {
    ctx.fillStyle = color;
    ctx.fillRect(x, y, size, size);
  };

  // Helper to draw a character at a specific position
  const drawCharacter = (frameX: number, frameY: number, facingDown = true, facingUp = false, facingLeft = false) => {
    const baseX = frameX * 32;
    const baseY = frameY * 32;

    // Head (8x8 pixels, centered)
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 8; x++) {
        if (y === 0 && (x === 0 || x === 7)) continue; // Round corners
        if (y === 7 && (x === 0 || x === 7)) continue;
        pixel(baseX + 12 + x * 2, baseY + 2 + y * 2, skinColor);
      }
    }

    // Hair (simple top layer)
    for (let x = 0; x < 8; x++) {
      pixel(baseX + 12 + x * 2, baseY + 2, hairColor);
      pixel(baseX + 12 + x * 2, baseY + 4, hairColor);
    }

    // Eyes (2 pixels)
    if (facingDown) {
      pixel(baseX + 16, baseY + 10, '#000000');
      pixel(baseX + 24, baseY + 10, '#000000');
    } else if (facingUp) {
      // Back of head - no eyes
    } else if (facingLeft) {
      pixel(baseX + 16, baseY + 10, '#000000');
    } else {
      pixel(baseX + 24, baseY + 10, '#000000');
    }

    // Body - Shirt (6x6 pixels)
    for (let y = 0; y < 6; y++) {
      for (let x = 0; x < 6; x++) {
        pixel(baseX + 13 + x * 2, baseY + 18 + y * 2, shirtColor);
      }
    }

    // Legs - Pants (two legs, 3x4 pixels each)
    for (let y = 0; y < 4; y++) {
      // Left leg
      pixel(baseX + 14, baseY + 30 + y * 2, pantsColor);
      pixel(baseX + 16, baseY + 30 + y * 2, pantsColor);
      pixel(baseX + 18, baseY + 30 + y * 2, pantsColor);
      // Right leg
      pixel(baseX + 22, baseY + 30 + y * 2, pantsColor);
      pixel(baseX + 24, baseY + 30 + y * 2, pantsColor);
      pixel(baseX + 26, baseY + 30 + y * 2, pantsColor);
    }
  };

  // Generate 4 rows x 4 frames
  // Row 0: Walk down
  for (let frame = 0; frame < 4; frame++) {
    drawCharacter(frame, 0, true, false, false);
  }

  // Row 1: Walk up
  for (let frame = 0; frame < 4; frame++) {
    drawCharacter(frame, 1, false, true, false);
  }

  // Row 2: Walk left
  for (let frame = 0; frame < 4; frame++) {
    drawCharacter(frame, 2, false, false, true);
  }

  // Row 3: Walk right
  for (let frame = 0; frame < 4; frame++) {
    drawCharacter(frame, 3, false, false, false);
  }

  return canvas.toDataURL();
}

/**
 * Predefined character variations for diversity
 */
export const CHARACTER_VARIATIONS: CharacterVariation[] = [
  {
    name: 'Default',
    skinColor: '#ffdbac',
    hairColor: '#8b4513',
    shirtColor: '#4a90e2',
    pantsColor: '#2c5f2d',
  },
  {
    name: 'Red Hair',
    skinColor: '#f4c7a0',
    hairColor: '#d32f2f',
    shirtColor: '#7b1fa2',
    pantsColor: '#424242',
  },
  {
    name: 'Blonde',
    skinColor: '#ffdbac',
    hairColor: '#ffd700',
    shirtColor: '#00897b',
    pantsColor: '#5d4037',
  },
  {
    name: 'Dark',
    skinColor: '#8d5524',
    hairColor: '#2e1a1a',
    shirtColor: '#e53935',
    pantsColor: '#263238',
  },
  {
    name: 'Pale',
    skinColor: '#fce4d8',
    hairColor: '#4a4a4a',
    shirtColor: '#43a047',
    pantsColor: '#1e88e5',
  },
  {
    name: 'Purple',
    skinColor: '#ffdbac',
    hairColor: '#9c27b0',
    shirtColor: '#ffa726',
    pantsColor: '#455a64',
  },
  {
    name: 'Green',
    skinColor: '#f4c7a0',
    hairColor: '#388e3c',
    shirtColor: '#f57c00',
    pantsColor: '#5d4037',
  },
  {
    name: 'Blue',
    skinColor: '#ffdbac',
    hairColor: '#1976d2',
    shirtColor: '#ef5350',
    pantsColor: '#424242',
  },
];

/**
 * SpriteManager class - Handles loading and caching sprites
 */
export class SpriteManager {
  private sprites: Map<string, SpriteAnimator> = new Map();
  private placeholderSprites: Map<string, string> = new Map();

  /**
   * Generate placeholder sprites for all variations
   */
  generatePlaceholders() {
    CHARACTER_VARIATIONS.forEach((variation, index) => {
      const dataUrl = generatePlaceholderSprite(variation);
      this.placeholderSprites.set(variation.name, dataUrl);
    });
  }

  /**
   * Get or create a sprite animator for an agent
   */
  getSpriteAnimator(agentId: string, variationIndex: number = 0): SpriteAnimator {
    // Check if we already have a sprite for this agent
    if (this.sprites.has(agentId)) {
      return this.sprites.get(agentId)!;
    }

    // Create new sprite animator
    const variation = CHARACTER_VARIATIONS[variationIndex % CHARACTER_VARIATIONS.length];

    // Generate placeholder if not exists
    if (!this.placeholderSprites.has(variation.name)) {
      this.generatePlaceholders();
    }

    const spritePath = this.placeholderSprites.get(variation.name) || '';
    const config = createLPCSpriteConfig(spritePath);
    const animator = new SpriteAnimator(config);

    this.sprites.set(agentId, animator);
    return animator;
  }

  /**
   * Update all sprite animations
   */
  updateAll(timestamp: number) {
    this.sprites.forEach(sprite => sprite.update(timestamp));
  }

  /**
   * Clear all cached sprites
   */
  clear() {
    this.sprites.clear();
  }

  /**
   * Get sprite count
   */
  getSpriteCount(): number {
    return this.sprites.size;
  }
}

// Singleton instance
let spriteManagerInstance: SpriteManager | null = null;

export function getSpriteManager(): SpriteManager {
  if (!spriteManagerInstance) {
    spriteManagerInstance = new SpriteManager();
    spriteManagerInstance.generatePlaceholders();
  }
  return spriteManagerInstance;
}
