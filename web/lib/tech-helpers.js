/**
 * Technology Helper Functions
 * 
 * Utility functions for technology status, prerequisites, and visualization.
 * Extracted from Next.js frontend for use in main HTML/JS UI.
 */

/**
 * Category icons for different tech types
 */
export const CATEGORY_ICONS = {
  survival: '🔥',
  construction: '🏗️',
  production: '⚙️',
  military: '⚔️',
  science: '🔬'
};

/**
 * Era colors for visualization
 */
export const ERA_COLORS = {
  stone_age: '#a78bfa',
  early_civilization: '#60a5fa',
  bronze_age: '#fbbf24',
  iron_age: '#f59e0b',
  classical_era: '#ec4899'
};

/**
 * Era display names
 */
export const ERA_NAMES = {
  stone_age: 'Stone Age',
  early_civilization: 'Early Civilization',
  bronze_age: 'Bronze Age',
  iron_age: 'Iron Age',
  classical_era: 'Classical Era'
};

/**
 * Get technology status for an agent
 * @param {string} techId - Technology identifier
 * @param {Set<string>} discoveredTechs - Set of discovered technology IDs
 * @param {string|null} researchingTech - Currently researching tech ID
 * @param {Object} techTree - Technology tree definition
 * @returns {string} Status: 'discovered', 'researching', 'available', or 'locked'
 */
export function getTechStatus(techId, discoveredTechs, researchingTech, techTree) {
  // Discovered
  if (discoveredTechs.has(techId)) {
    return 'discovered';
  }

  // Currently researching
  if (researchingTech === techId) {
    return 'researching';
  }

  // Check if available (prerequisites met)
  const tech = techTree[techId];
  if (!tech) return 'locked';

  const hasPrereqs = tech.prerequisites.every(prereq => 
    discoveredTechs.has(prereq)
  );

  if (hasPrereqs) {
    return 'available';
  }

  // Locked
  return 'locked';
}

/**
 * Check if technology can be researched
 * @param {string} techId - Technology identifier
 * @param {Set<string>} discoveredTechs - Set of discovered technology IDs
 * @param {Object} techTree - Technology tree definition
 * @returns {boolean} True if prerequisites are met
 */
export function canResearchTech(techId, discoveredTechs, techTree) {
  const tech = techTree[techId];
  if (!tech) return false;
  
  // Already discovered
  if (discoveredTechs.has(techId)) return false;
  
  // Check prerequisites
  return tech.prerequisites.every(prereq => discoveredTechs.has(prereq));
}

/**
 * Get all technologies available for research
 * @param {Set<string>} discoveredTechs - Set of discovered technology IDs
 * @param {Object} techTree - Technology tree definition
 * @returns {Array<string>} Array of available tech IDs
 */
export function getAvailableTechs(discoveredTechs, techTree) {
  return Object.keys(techTree).filter(techId => 
    canResearchTech(techId, discoveredTechs, techTree)
  );
}

/**
 * Get technologies by era
 * @param {string} era - Era name
 * @param {Object} techTree - Technology tree definition
 * @returns {Array<Object>} Array of technologies in that era
 */
export function getTechsByEra(era, techTree) {
  return Object.values(techTree).filter(tech => tech.era === era);
}

/**
 * Calculate research progress for display
 * @param {number} progress - Research progress (0-100)
 * @returns {Object} Formatted progress with percentage and visual info
 */
export function getResearchProgress(progress) {
  const percentage = Math.min(100, Math.max(0, progress));
  const isComplete = percentage >= 100;
  const isStarted = percentage > 0;
  
  return {
    percentage,
    isComplete,
    isStarted,
    barWidth: `${percentage}%`,
    color: isComplete ? '#10b981' : isStarted ? '#3b82f6' : '#64748b'
  };
}

/**
 * Get tech tree statistics
 * @param {Set<string>} discoveredTechs - Set of discovered technology IDs
 * @param {Object} techTree - Technology tree definition
 * @returns {Object} Statistics about tech progress
 */
export function getTechStats(discoveredTechs, techTree) {
  const total = Object.keys(techTree).length;
  const discovered = discoveredTechs.size;
  const available = getAvailableTechs(discoveredTechs, techTree).length;
  const locked = total - discovered - available;
  const percentage = Math.floor((discovered / total) * 100);
  
  return {
    total,
    discovered,
    available,
    locked,
    percentage
  };
}

// Export all functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    CATEGORY_ICONS,
    ERA_COLORS,
    ERA_NAMES,
    getTechStatus,
    canResearchTech,
    getAvailableTechs,
    getTechsByEra,
    getResearchProgress,
    getTechStats
  };
}
