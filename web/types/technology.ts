/**
 * Technology & Knowledge System Types
 *
 * Defines the technology tree for civilization progression.
 * Agents discover technologies to unlock new capabilities.
 */

import type { ResourceCost, BuildingType } from './structures';

export type TechnologyId =
  // TIER 1: Primitive Knowledge (Stone Age)
  | 'fire_making'
  | 'basic_tools'
  | 'primitive_shelter'

  // TIER 2: Foundation Technologies (Early Civilization)
  | 'basic_construction'
  | 'stoneworking'
  | 'agriculture'
  | 'toolmaking'
  | 'pottery'

  // TIER 3: Advanced Knowledge (Bronze Age)
  | 'mining'
  | 'metalworking'
  | 'ironworking'
  | 'advanced_construction'
  | 'writing'

  // TIER 4: Complex Systems (Iron Age)
  | 'metallurgy'
  | 'defensive_architecture'
  | 'engineering'
  | 'mathematics'
  | 'astronomy'

  // TIER 5: Elite Knowledge (Classical Era)
  | 'architecture'
  | 'luxury_goods'
  | 'scientific_method'
  | 'advanced_tools'
  | 'philosophy';

export type TechnologyCategory =
  | 'survival'      // Basic needs: fire, shelter, food
  | 'construction'  // Building and structures
  | 'production'    // Resource generation
  | 'military'      // Defense and warfare
  | 'science';      // Research and knowledge

export type TechnologyEra =
  | 'stone_age'
  | 'early_civilization'
  | 'bronze_age'
  | 'iron_age'
  | 'classical_era';

export interface Technology {
  id: TechnologyId;
  name: string;
  description: string;
  icon: string;
  category: TechnologyCategory;
  era: TechnologyEra;

  // Unlock requirements
  prerequisites: TechnologyId[];  // Must have these techs first
  researchCost: ResourceCost;     // Resources needed to research
  wealthRequired: number;         // Minimum wealth to research

  // Benefits
  unlocksBuildings: BuildingType[];
  unlocksTechnologies: TechnologyId[];

  // Bonuses (future use)
  bonuses?: {
    productionMultiplier?: number;
    constructionSpeed?: number;
    defenseBonus?: number;
  };
}

/**
 * Agent's knowledge state
 */
export interface AgentKnowledge {
  agentId: string;
  discoveredTechnologies: Set<TechnologyId>;
  researchingTechnology: TechnologyId | null;
  researchProgress: number; // 0-100%
}

/**
 * Complete Technology Tree Configuration
 */
export const TECHNOLOGY_TREE: Record<TechnologyId, Technology> = {
  // ========================================
  // TIER 1: PRIMITIVE KNOWLEDGE (Stone Age)
  // ========================================

  fire_making: {
    id: 'fire_making',
    name: 'Fire Making',
    description: 'Harness the power of fire for warmth, cooking, and protection.',
    icon: '🔥',
    category: 'survival',
    era: 'stone_age',
    prerequisites: [],
    researchCost: { wood: 10 },
    wealthRequired: 5,
    unlocksBuildings: ['campfire'],
    unlocksTechnologies: ['basic_tools', 'pottery'],
  },

  basic_tools: {
    id: 'basic_tools',
    name: 'Basic Tools',
    description: 'Craft simple stone tools for gathering and crafting.',
    icon: '🪨',
    category: 'production',
    era: 'stone_age',
    prerequisites: ['fire_making'],
    researchCost: { wood: 15, stone: 10 },
    wealthRequired: 15,
    unlocksBuildings: [],
    unlocksTechnologies: ['toolmaking', 'stoneworking'],
    bonuses: {
      productionMultiplier: 1.2,
    },
  },

  primitive_shelter: {
    id: 'primitive_shelter',
    name: 'Primitive Shelter',
    description: 'Build basic shelters for protection from elements.',
    icon: '⛺',
    category: 'construction',
    era: 'stone_age',
    prerequisites: [],
    researchCost: { wood: 20 },
    wealthRequired: 20,
    unlocksBuildings: ['tent'],
    unlocksTechnologies: ['basic_construction'],
  },

  // ========================================
  // TIER 2: FOUNDATION (Early Civilization)
  // ========================================

  basic_construction: {
    id: 'basic_construction',
    name: 'Basic Construction',
    description: 'Fundamental building techniques for permanent structures.',
    icon: '🏗️',
    category: 'construction',
    era: 'early_civilization',
    prerequisites: ['primitive_shelter'],
    researchCost: { wood: 40, stone: 20 },
    wealthRequired: 40,
    unlocksBuildings: ['shelter', 'storage'],
    unlocksTechnologies: ['advanced_construction'],
    bonuses: {
      constructionSpeed: 1.1,
    },
  },

  stoneworking: {
    id: 'stoneworking',
    name: 'Stoneworking',
    description: 'Shape and craft with stone for durable structures.',
    icon: '🗿',
    category: 'construction',
    era: 'early_civilization',
    prerequisites: ['basic_tools'],
    researchCost: { stone: 50 },
    wealthRequired: 50,
    unlocksBuildings: ['hut'],
    unlocksTechnologies: ['mining'],
  },

  agriculture: {
    id: 'agriculture',
    name: 'Agriculture',
    description: 'Cultivate crops for reliable food production.',
    icon: '🌾',
    category: 'production',
    era: 'early_civilization',
    prerequisites: ['basic_tools'],
    researchCost: { wood: 30, food: 20 },
    wealthRequired: 60,
    unlocksBuildings: ['farm'],
    unlocksTechnologies: [],
    bonuses: {
      productionMultiplier: 1.5,
    },
  },

  toolmaking: {
    id: 'toolmaking',
    name: 'Toolmaking',
    description: 'Craft advanced tools and implements.',
    icon: '🔨',
    category: 'production',
    era: 'early_civilization',
    prerequisites: ['basic_tools'],
    researchCost: { wood: 50, stone: 30 },
    wealthRequired: 70,
    unlocksBuildings: ['workshop'],
    unlocksTechnologies: ['advanced_tools'],
    bonuses: {
      productionMultiplier: 1.3,
    },
  },

  pottery: {
    id: 'pottery',
    name: 'Pottery',
    description: 'Create vessels for storage and transport.',
    icon: '🏺',
    category: 'production',
    era: 'early_civilization',
    prerequisites: ['fire_making'],
    researchCost: { stone: 25 },
    wealthRequired: 35,
    unlocksBuildings: [],
    unlocksTechnologies: [],
  },

  // ========================================
  // TIER 3: ADVANCED KNOWLEDGE (Bronze Age)
  // ========================================

  mining: {
    id: 'mining',
    name: 'Mining',
    description: 'Extract valuable resources from the earth.',
    icon: '⛏️',
    category: 'production',
    era: 'bronze_age',
    prerequisites: ['stoneworking'],
    researchCost: { wood: 60, stone: 80 },
    wealthRequired: 100,
    unlocksBuildings: ['mine'],
    unlocksTechnologies: ['metalworking'],
  },

  metalworking: {
    id: 'metalworking',
    name: 'Metalworking',
    description: 'Work with bronze and basic metals.',
    icon: '⚙️',
    category: 'production',
    era: 'bronze_age',
    prerequisites: ['mining', 'fire_making'],
    researchCost: { stone: 70, iron: 30 },
    wealthRequired: 120,
    unlocksBuildings: [],
    unlocksTechnologies: ['ironworking', 'metallurgy'],
  },

  ironworking: {
    id: 'ironworking',
    name: 'Ironworking',
    description: 'Forge iron tools and weapons.',
    icon: '🔩',
    category: 'production',
    era: 'bronze_age',
    prerequisites: ['metalworking'],
    researchCost: { iron: 50, stone: 40 },
    wealthRequired: 140,
    unlocksBuildings: ['house'],
    unlocksTechnologies: ['metallurgy'],
  },

  advanced_construction: {
    id: 'advanced_construction',
    name: 'Advanced Construction',
    description: 'Complex building techniques for larger structures.',
    icon: '🏛️',
    category: 'construction',
    era: 'bronze_age',
    prerequisites: ['basic_construction', 'stoneworking'],
    researchCost: { wood: 80, stone: 100 },
    wealthRequired: 130,
    unlocksBuildings: ['house', 'tower'],
    unlocksTechnologies: ['defensive_architecture', 'architecture'],
    bonuses: {
      constructionSpeed: 1.25,
    },
  },

  writing: {
    id: 'writing',
    name: 'Writing',
    description: 'Record knowledge and communicate across distances.',
    icon: '📜',
    category: 'science',
    era: 'bronze_age',
    prerequisites: ['pottery'],
    researchCost: { wood: 60 },
    wealthRequired: 90,
    unlocksBuildings: [],
    unlocksTechnologies: ['mathematics', 'philosophy'],
  },

  // ========================================
  // TIER 4: COMPLEX SYSTEMS (Iron Age)
  // ========================================

  metallurgy: {
    id: 'metallurgy',
    name: 'Metallurgy',
    description: 'Advanced metal processing and alloy creation.',
    icon: '⚒️',
    category: 'production',
    era: 'iron_age',
    prerequisites: ['ironworking'],
    researchCost: { iron: 80, stone: 60 },
    wealthRequired: 160,
    unlocksBuildings: ['smelter'],
    unlocksTechnologies: [],
    bonuses: {
      productionMultiplier: 1.4,
    },
  },

  defensive_architecture: {
    id: 'defensive_architecture',
    name: 'Defensive Architecture',
    description: 'Design fortifications and defensive structures.',
    icon: '🛡️',
    category: 'military',
    era: 'iron_age',
    prerequisites: ['advanced_construction'],
    researchCost: { stone: 120, iron: 60 },
    wealthRequired: 180,
    unlocksBuildings: ['tower'],
    unlocksTechnologies: [],
    bonuses: {
      defenseBonus: 50,
    },
  },

  engineering: {
    id: 'engineering',
    name: 'Engineering',
    description: 'Apply mechanical principles to construction.',
    icon: '⚙️',
    category: 'construction',
    era: 'iron_age',
    prerequisites: ['advanced_construction', 'mathematics'],
    researchCost: { wood: 100, stone: 100, iron: 50 },
    wealthRequired: 190,
    unlocksBuildings: [],
    unlocksTechnologies: ['architecture'],
    bonuses: {
      constructionSpeed: 1.5,
    },
  },

  mathematics: {
    id: 'mathematics',
    name: 'Mathematics',
    description: 'Understand numbers, geometry, and calculations.',
    icon: '➗',
    category: 'science',
    era: 'iron_age',
    prerequisites: ['writing'],
    researchCost: { wood: 80 },
    wealthRequired: 150,
    unlocksBuildings: [],
    unlocksTechnologies: ['engineering', 'astronomy', 'scientific_method'],
  },

  astronomy: {
    id: 'astronomy',
    name: 'Astronomy',
    description: 'Study the stars and celestial patterns.',
    icon: '🌟',
    category: 'science',
    era: 'iron_age',
    prerequisites: ['mathematics'],
    researchCost: { wood: 90 },
    wealthRequired: 170,
    unlocksBuildings: [],
    unlocksTechnologies: ['scientific_method'],
  },

  // ========================================
  // TIER 5: ELITE KNOWLEDGE (Classical Era)
  // ========================================

  architecture: {
    id: 'architecture',
    name: 'Architecture',
    description: 'Grand designs for magnificent buildings.',
    icon: '🏰',
    category: 'construction',
    era: 'classical_era',
    prerequisites: ['advanced_construction', 'engineering'],
    researchCost: { wood: 150, stone: 150, iron: 80 },
    wealthRequired: 220,
    unlocksBuildings: ['mansion'],
    unlocksTechnologies: [],
    bonuses: {
      constructionSpeed: 1.75,
    },
  },

  luxury_goods: {
    id: 'luxury_goods',
    name: 'Luxury Goods',
    description: 'Craft fine items for the wealthy elite.',
    icon: '💎',
    category: 'production',
    era: 'classical_era',
    prerequisites: ['metallurgy', 'pottery'],
    researchCost: { iron: 100, gold: 50 },
    wealthRequired: 240,
    unlocksBuildings: ['mansion'],
    unlocksTechnologies: [],
  },

  scientific_method: {
    id: 'scientific_method',
    name: 'Scientific Method',
    description: 'Systematic approach to knowledge and discovery.',
    icon: '🔬',
    category: 'science',
    era: 'classical_era',
    prerequisites: ['mathematics', 'astronomy'],
    researchCost: { wood: 120, gold: 40 },
    wealthRequired: 260,
    unlocksBuildings: ['laboratory'],
    unlocksTechnologies: [],
  },

  advanced_tools: {
    id: 'advanced_tools',
    name: 'Advanced Tools',
    description: 'Precision instruments for complex tasks.',
    icon: '🔧',
    category: 'production',
    era: 'classical_era',
    prerequisites: ['toolmaking', 'ironworking'],
    researchCost: { iron: 80, wood: 60 },
    wealthRequired: 200,
    unlocksBuildings: ['laboratory'],
    unlocksTechnologies: [],
    bonuses: {
      productionMultiplier: 1.6,
    },
  },

  philosophy: {
    id: 'philosophy',
    name: 'Philosophy',
    description: 'Contemplate existence, ethics, and knowledge.',
    icon: '🧠',
    category: 'science',
    era: 'classical_era',
    prerequisites: ['writing', 'mathematics'],
    researchCost: { wood: 100 },
    wealthRequired: 210,
    unlocksBuildings: [],
    unlocksTechnologies: [],
  },
};

/**
 * Get technology by ID
 */
export function getTechnology(id: TechnologyId): Technology {
  return TECHNOLOGY_TREE[id];
}

/**
 * Check if agent can research a technology
 */
export function canResearchTechnology(
  techId: TechnologyId,
  knownTechnologies: Set<TechnologyId>,
  resources: Record<string, number>,
  wealth: number
): boolean {
  const tech = getTechnology(techId);

  // Check wealth requirement
  if (wealth < tech.wealthRequired) {
    return false;
  }

  // Check prerequisites
  for (const prereq of tech.prerequisites) {
    if (!knownTechnologies.has(prereq)) {
      return false;
    }
  }

  // Check resource cost
  for (const [resource, cost] of Object.entries(tech.researchCost)) {
    if ((resources[resource] || 0) < (cost || 0)) {
      return false;
    }
  }

  return true;
}

/**
 * Get all technologies available for research
 */
export function getAvailableTechnologies(
  knownTechnologies: Set<TechnologyId>,
  wealth: number
): TechnologyId[] {
  return Object.values(TECHNOLOGY_TREE)
    .filter(tech => {
      // Not already known
      if (knownTechnologies.has(tech.id)) {
        return false;
      }

      // Has wealth requirement
      if (wealth < tech.wealthRequired) {
        return false;
      }

      // Has all prerequisites
      return tech.prerequisites.every(prereq => knownTechnologies.has(prereq));
    })
    .map(tech => tech.id);
}

/**
 * Get technologies by era
 */
export function getTechnologiesByEra(era: TechnologyEra): Technology[] {
  return Object.values(TECHNOLOGY_TREE).filter(tech => tech.era === era);
}

/**
 * Get technologies by category
 */
export function getTechnologiesByCategory(category: TechnologyCategory): Technology[] {
  return Object.values(TECHNOLOGY_TREE).filter(tech => tech.category === category);
}

/**
 * Get technology tree depth (for visualization)
 */
export function getTechnologyDepth(techId: TechnologyId): number {
  const tech = getTechnology(techId);

  if (tech.prerequisites.length === 0) {
    return 0;
  }

  return 1 + Math.max(...tech.prerequisites.map(prereq => getTechnologyDepth(prereq)));
}

/**
 * Get all buildings unlocked by known technologies
 */
export function getUnlockedBuildings(knownTechnologies: Set<TechnologyId>): BuildingType[] {
  const buildings = new Set<BuildingType>();

  knownTechnologies.forEach(techId => {
    const tech = getTechnology(techId);
    tech.unlocksBuildings.forEach(building => buildings.add(building));
  });

  return Array.from(buildings);
}
