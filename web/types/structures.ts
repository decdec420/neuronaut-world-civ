/**
 * Structure/Building System Types
 *
 * Defines all building types, construction stages, and requirements
 * for the civilization emergence simulation.
 */

export type BuildingType =
  | 'campfire'
  | 'tent'
  | 'shelter'
  | 'hut'
  | 'house'
  | 'workshop'
  | 'storage'
  | 'farm'
  | 'mine'
  | 'smelter'
  | 'tower'
  | 'mansion'
  | 'laboratory';

export type ConstructionStage =
  | 'planning'      // Just a marker/blueprint
  | 'foundation'    // Ground work started
  | 'framing'       // Structure being built
  | 'finishing'     // Almost done
  | 'completed';    // Fully functional

export type ResourceType = 'wood' | 'stone' | 'food' | 'iron' | 'gold';

export interface ResourceCost {
  wood?: number;
  stone?: number;
  food?: number;
  iron?: number;
  gold?: number;
}

export interface Building {
  id: string;
  type: BuildingType;
  position: { x: number; y: number };
  ownerId: string;  // Agent who built/owns it
  stage: ConstructionStage;
  progress: number; // 0-100% construction progress
  health: number;   // 0-100% structural integrity
  built: number;    // Tick when construction started
  completed?: number; // Tick when finished
}

export interface BuildingConfig {
  type: BuildingType;
  name: string;
  description: string;
  icon: string;
  color: string;

  // Requirements
  cost: ResourceCost;
  buildTime: number; // Ticks to complete
  techRequired?: string[]; // Prerequisites

  // Properties
  capacity?: number;  // Storage/housing capacity
  production?: { resource: ResourceType; rate: number }; // Production buildings
  defense?: number;   // Protection value

  // Unlock conditions
  wealthRequired: number;
  agentsRequired?: number;
}

/**
 * Building Configurations
 * Progression: Primitive → Basic → Advanced → Elite
 */
export const BUILDING_CONFIGS: Record<BuildingType, BuildingConfig> = {
  // TIER 1: Primitive (Survival)
  campfire: {
    type: 'campfire',
    name: 'Campfire',
    description: 'Basic warmth and cooking. First step of civilization.',
    icon: '🔥',
    color: '#f59e0b',
    cost: { wood: 5 },
    buildTime: 50,
    wealthRequired: 10,
  },

  tent: {
    type: 'tent',
    name: 'Tent',
    description: 'Temporary shelter from elements.',
    icon: '⛺',
    color: '#84cc16',
    cost: { wood: 10, food: 5 },
    buildTime: 100,
    capacity: 1,
    wealthRequired: 25,
  },

  // TIER 2: Basic Structures
  shelter: {
    type: 'shelter',
    name: 'Wooden Shelter',
    description: 'Simple but permanent housing.',
    icon: '🛖',
    color: '#6b4423',
    cost: { wood: 25, stone: 10 },
    buildTime: 200,
    capacity: 1,
    defense: 20,
    wealthRequired: 50,
    techRequired: ['basic_construction'],
  },

  hut: {
    type: 'hut',
    name: 'Stone Hut',
    description: 'Durable dwelling with storage.',
    icon: '🏠',
    color: '#64748b',
    cost: { wood: 40, stone: 30 },
    buildTime: 300,
    capacity: 2,
    defense: 40,
    wealthRequired: 75,
    techRequired: ['basic_construction', 'stoneworking'],
  },

  storage: {
    type: 'storage',
    name: 'Storage Shed',
    description: 'Protects resources from decay.',
    icon: '📦',
    color: '#92400e',
    cost: { wood: 30, stone: 15 },
    buildTime: 150,
    capacity: 100,
    wealthRequired: 60,
    techRequired: ['basic_construction'],
  },

  // TIER 3: Production Buildings
  farm: {
    type: 'farm',
    name: 'Farm Plot',
    description: 'Generates food over time.',
    icon: '🌾',
    color: '#22c55e',
    cost: { wood: 20, stone: 10, food: 10 },
    buildTime: 250,
    production: { resource: 'food', rate: 5 },
    wealthRequired: 80,
    techRequired: ['agriculture'],
  },

  workshop: {
    type: 'workshop',
    name: 'Workshop',
    description: 'Craft tools and equipment.',
    icon: '🔨',
    color: '#475569',
    cost: { wood: 50, stone: 40 },
    buildTime: 400,
    wealthRequired: 100,
    techRequired: ['toolmaking'],
  },

  mine: {
    type: 'mine',
    name: 'Mine Shaft',
    description: 'Extracts stone and iron from ground.',
    icon: '⛏️',
    color: '#44403c',
    cost: { wood: 30, stone: 50 },
    buildTime: 500,
    production: { resource: 'stone', rate: 10 },
    wealthRequired: 120,
    techRequired: ['mining'],
  },

  // TIER 4: Advanced Structures
  house: {
    type: 'house',
    name: 'House',
    description: 'Comfortable dwelling for prosperous agents.',
    icon: '🏡',
    color: '#3b82f6',
    cost: { wood: 80, stone: 60, iron: 20 },
    buildTime: 600,
    capacity: 4,
    defense: 60,
    wealthRequired: 150,
    techRequired: ['advanced_construction', 'ironworking'],
  },

  smelter: {
    type: 'smelter',
    name: 'Smelter',
    description: 'Process ore into metal.',
    icon: '⚒️',
    color: '#dc2626',
    cost: { wood: 40, stone: 80, iron: 30 },
    buildTime: 700,
    production: { resource: 'iron', rate: 3 },
    wealthRequired: 180,
    techRequired: ['metallurgy'],
  },

  tower: {
    type: 'tower',
    name: 'Watchtower',
    description: 'Defensive structure with surveillance.',
    icon: '🗼',
    color: '#0891b2',
    cost: { wood: 60, stone: 100, iron: 40 },
    buildTime: 800,
    defense: 100,
    wealthRequired: 200,
    techRequired: ['advanced_construction', 'defensive_architecture'],
  },

  // TIER 5: Elite Structures
  mansion: {
    type: 'mansion',
    name: 'Mansion',
    description: 'Luxurious estate for the wealthy elite.',
    icon: '🏰',
    color: '#a78bfa',
    cost: { wood: 150, stone: 120, iron: 80, gold: 50 },
    buildTime: 1200,
    capacity: 10,
    defense: 80,
    wealthRequired: 250,
    techRequired: ['architecture', 'luxury_goods'],
  },

  laboratory: {
    type: 'laboratory',
    name: 'Research Lab',
    description: 'Unlock new technologies and knowledge.',
    icon: '🔬',
    color: '#22d3ee',
    cost: { wood: 100, stone: 100, iron: 60, gold: 40 },
    buildTime: 1000,
    wealthRequired: 300,
    techRequired: ['scientific_method', 'advanced_tools'],
  },
};

/**
 * Get building configuration by type
 */
export function getBuildingConfig(type: BuildingType): BuildingConfig {
  return BUILDING_CONFIGS[type];
}

/**
 * Check if agent can afford building
 */
export function canAffordBuilding(
  type: BuildingType,
  resources: Record<ResourceType, number>
): boolean {
  const config = getBuildingConfig(type);

  for (const [resource, cost] of Object.entries(config.cost)) {
    if (resources[resource as ResourceType] < (cost || 0)) {
      return false;
    }
  }

  return true;
}

/**
 * Get buildings available for construction based on wealth
 */
export function getAvailableBuildings(wealth: number): BuildingType[] {
  return Object.values(BUILDING_CONFIGS)
    .filter(config => wealth >= config.wealthRequired)
    .map(config => config.type);
}

/**
 * Calculate construction progress based on time elapsed
 */
export function calculateProgress(
  building: Building,
  currentTick: number
): number {
  const config = getBuildingConfig(building.type);
  const ticksElapsed = currentTick - building.built;
  const progress = Math.min(100, (ticksElapsed / config.buildTime) * 100);

  return Math.floor(progress);
}

/**
 * Get construction stage based on progress
 */
export function getConstructionStage(progress: number): ConstructionStage {
  if (progress === 100) return 'completed';
  if (progress >= 75) return 'finishing';
  if (progress >= 40) return 'framing';
  if (progress >= 15) return 'foundation';
  return 'planning';
}
