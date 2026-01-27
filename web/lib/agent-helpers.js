/**
 * Agent Helper Functions
 * 
 * Utility functions for agent status, tiers, and derived statistics.
 * Extracted from Next.js frontend for use in main HTML/JS UI.
 */

/**
 * Get wealth tier classification
 * @param {number} wealth - Agent's wealth value
 * @returns {{tier: string, color: string, icon: string}}
 */
export function getWealthTier(wealth) {
  if (wealth >= 200) return { tier: 'Elite', color: '#fbbf24', icon: '👑' };
  if (wealth >= 150) return { tier: 'Rich', color: '#f59e0b', icon: '💎' };
  if (wealth >= 100) return { tier: 'Prosperous', color: '#eab308', icon: '💰' };
  if (wealth >= 50) return { tier: 'Comfortable', color: '#84cc16', icon: '🏠' };
  if (wealth >= 25) return { tier: 'Modest', color: '#22c55e', icon: '🌾' };
  return { tier: 'Poor', color: '#64748b', icon: '🥔' };
}

/**
 * Get health status classification
 * @param {number} health - Agent's health value (0-100)
 * @returns {{status: string, color: string, icon: string}}
 */
export function getHealthStatus(health) {
  if (health >= 90) return { status: 'Excellent', color: '#10b981', icon: '💪' };
  if (health >= 70) return { status: 'Good', color: '#22c55e', icon: '✅' };
  if (health >= 50) return { status: 'Fair', color: '#f59e0b', icon: '⚠️' };
  if (health >= 30) return { status: 'Poor', color: '#ef4444', icon: '🩹' };
  return { status: 'Critical', color: '#dc2626', icon: '☠️' };
}

/**
 * Get age category classification
 * @param {number} age - Agent's age in years
 * @returns {{category: string, color: string, icon: string}}
 */
export function getAgeCategory(age) {
  if (age >= 60) return { category: 'Elder', color: '#a78bfa', icon: '🧓' };
  if (age >= 40) return { category: 'Middle Age', color: '#60a5fa', icon: '🧑' };
  if (age >= 18) return { category: 'Adult', color: '#22d3ee', icon: '👨' };
  if (age >= 13) return { category: 'Teen', color: '#4ade80', icon: '🧒' };
  return { category: 'Child', color: '#fbbf24', icon: '👶' };
}

/**
 * Calculate life progress percentage
 * @param {number} age - Agent's current age
 * @param {number} maxAge - Maximum lifespan (default 80)
 * @returns {number} Progress percentage (0-100)
 */
export function getLifeProgress(age, maxAge = 80) {
  return Math.min(100, (age / maxAge) * 100);
}

/**
 * Calculate health score out of 10
 * @param {number} health - Agent's health (0-100)
 * @returns {number} Score from 0-10
 */
export function getHealthScore(health) {
  return Math.floor((health / 100) * 10);
}

/**
 * Calculate wealth rank percentage
 * @param {number} wealth - Agent's wealth
 * @param {number} maxWealth - Maximum wealth for ranking (default 250)
 * @returns {number} Rank percentage (0-100)
 */
export function getWealthRank(wealth, maxWealth = 250) {
  return Math.min(100, Math.floor((wealth / maxWealth) * 100));
}

/**
 * Get comprehensive agent status
 * @param {Object} agent - Agent object with wealth, health, age
 * @returns {Object} Complete status information
 */
export function getAgentStatus(agent) {
  return {
    wealth: getWealthTier(agent.wealth),
    health: getHealthStatus(agent.health),
    age: getAgeCategory(agent.age),
    lifeProgress: getLifeProgress(agent.age),
    healthScore: getHealthScore(agent.health),
    wealthRank: getWealthRank(agent.wealth)
  };
}

// Export all functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getWealthTier,
    getHealthStatus,
    getAgeCategory,
    getLifeProgress,
    getHealthScore,
    getWealthRank,
    getAgentStatus
  };
}
