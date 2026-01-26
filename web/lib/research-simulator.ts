/**
 * Research & Technology Simulator
 *
 * Manages technology research progress for agents.
 * Simulates knowledge discovery and tech progression.
 */

import type { TechnologyId, AgentKnowledge } from '@/types/technology';
import { getTechnology, canResearchTechnology } from '@/types/technology';

export interface ResearchUpdate {
  agentId: string;
  technology: TechnologyId;
  progress: number;
  justCompleted: boolean;
}

export class ResearchSimulator {
  private agentKnowledge: Map<string, AgentKnowledge> = new Map();
  private lastUpdateTime: number = Date.now();
  private researchSpeedMultiplier: number = 1.0; // Global research speed modifier

  constructor(agents: { id: string; wealth: number }[] = []) {
    // Initialize knowledge for all agents
    agents.forEach(agent => {
      this.agentKnowledge.set(agent.id, {
        agentId: agent.id,
        discoveredTechnologies: new Set<TechnologyId>(),
        researchingTechnology: null,
        researchProgress: 0,
      });

      // Auto-start primitive techs if wealthy enough
      if (agent.wealth >= 5) {
        this.startResearch(agent.id, 'fire_making');
      }
    });
  }

  /**
   * Update all research progress
   */
  update(): ResearchUpdate[] {
    const now = Date.now();
    const deltaTime = (now - this.lastUpdateTime) / 1000; // Seconds
    this.lastUpdateTime = now;

    const updates: ResearchUpdate[] = [];

    this.agentKnowledge.forEach(knowledge => {
      // Only update if actively researching
      if (!knowledge.researchingTechnology) {
        return;
      }

      const tech = getTechnology(knowledge.researchingTechnology);
      const oldProgress = knowledge.researchProgress;

      // Calculate research progress
      // Base: complete in ~30 seconds for stone age, ~60 seconds for classical
      const baseResearchTime = this.getResearchTime(tech.era);
      const progressPerSecond = (100 / baseResearchTime) * this.researchSpeedMultiplier;
      const progressIncrement = progressPerSecond * deltaTime;

      knowledge.researchProgress = Math.min(100, knowledge.researchProgress + progressIncrement);

      // Check for completion
      const justCompleted = knowledge.researchProgress >= 100 && oldProgress < 100;
      if (justCompleted) {
        // Add to discovered technologies
        knowledge.discoveredTechnologies.add(knowledge.researchingTechnology);

        // Log discovery
        console.log(
          `🎓 Agent ${knowledge.agentId} discovered ${tech.name}! (${knowledge.discoveredTechnologies.size} techs known)`
        );

        updates.push({
          agentId: knowledge.agentId,
          technology: knowledge.researchingTechnology,
          progress: 100,
          justCompleted: true,
        });

        // Clear research state
        knowledge.researchingTechnology = null;
        knowledge.researchProgress = 0;
      } else if (knowledge.researchProgress !== oldProgress) {
        // Progress update
        updates.push({
          agentId: knowledge.agentId,
          technology: knowledge.researchingTechnology,
          progress: knowledge.researchProgress,
          justCompleted: false,
        });
      }
    });

    return updates;
  }

  /**
   * Get research time based on era (in seconds)
   */
  private getResearchTime(era: string): number {
    const times: Record<string, number> = {
      stone_age: 20,
      early_civilization: 30,
      bronze_age: 45,
      iron_age: 60,
      classical_era: 80,
    };
    return times[era] || 30;
  }

  /**
   * Start researching a technology
   */
  startResearch(agentId: string, techId: TechnologyId): boolean {
    const knowledge = this.agentKnowledge.get(agentId);
    if (!knowledge) {
      console.warn(`Agent ${agentId} not found in research simulator`);
      return false;
    }

    // Check if already known
    if (knowledge.discoveredTechnologies.has(techId)) {
      console.warn(`Agent ${agentId} already knows ${techId}`);
      return false;
    }

    // Check if already researching
    if (knowledge.researchingTechnology) {
      console.warn(`Agent ${agentId} already researching ${knowledge.researchingTechnology}`);
      return false;
    }

    const tech = getTechnology(techId);

    // Set research state
    knowledge.researchingTechnology = techId;
    knowledge.researchProgress = 0;

    console.log(`🔬 Agent ${agentId} started researching ${tech.name}`);
    return true;
  }

  /**
   * Cancel current research
   */
  cancelResearch(agentId: string): void {
    const knowledge = this.agentKnowledge.get(agentId);
    if (knowledge) {
      knowledge.researchingTechnology = null;
      knowledge.researchProgress = 0;
    }
  }

  /**
   * Add a new agent to the simulator
   */
  addAgent(agentId: string, wealth: number = 0): void {
    if (!this.agentKnowledge.has(agentId)) {
      this.agentKnowledge.set(agentId, {
        agentId,
        discoveredTechnologies: new Set<TechnologyId>(),
        researchingTechnology: null,
        researchProgress: 0,
      });

      // Auto-start basic research if wealthy enough
      if (wealth >= 5) {
        this.startResearch(agentId, 'fire_making');
      }
    }
  }

  /**
   * Get agent's knowledge state
   */
  getAgentKnowledge(agentId: string): AgentKnowledge | undefined {
    return this.agentKnowledge.get(agentId);
  }

  /**
   * Get all agents with their knowledge
   */
  getAllKnowledge(): AgentKnowledge[] {
    return Array.from(this.agentKnowledge.values());
  }

  /**
   * Manually unlock a technology (for testing or events)
   */
  unlockTechnology(agentId: string, techId: TechnologyId): void {
    const knowledge = this.agentKnowledge.get(agentId);
    if (knowledge) {
      knowledge.discoveredTechnologies.add(techId);
      const tech = getTechnology(techId);
      console.log(`✨ Agent ${agentId} unlocked ${tech.name} (manual unlock)`);
    }
  }

  /**
   * Set research speed multiplier (e.g., 2.0 for double speed)
   */
  setResearchSpeed(multiplier: number): void {
    this.researchSpeedMultiplier = multiplier;
  }

  /**
   * Get total technologies discovered across all agents
   */
  getTotalDiscoveries(): number {
    let total = 0;
    this.agentKnowledge.forEach(knowledge => {
      total += knowledge.discoveredTechnologies.size;
    });
    return total;
  }

  /**
   * Get most advanced agent (by tech count)
   */
  getMostAdvancedAgent(): string | null {
    let maxTechs = 0;
    let advancedAgent: string | null = null;

    this.agentKnowledge.forEach(knowledge => {
      const techCount = knowledge.discoveredTechnologies.size;
      if (techCount > maxTechs) {
        maxTechs = techCount;
        advancedAgent = knowledge.agentId;
      }
    });

    return advancedAgent;
  }

  /**
   * Reset simulation time (for pause/resume)
   */
  resetTime(): void {
    this.lastUpdateTime = Date.now();
  }
}

/**
 * Singleton instance for global use
 */
let simulatorInstance: ResearchSimulator | null = null;

export function getResearchSimulator(agents?: { id: string; wealth: number }[]): ResearchSimulator {
  if (!simulatorInstance && agents) {
    simulatorInstance = new ResearchSimulator(agents);
  }
  return simulatorInstance!;
}

export function resetResearchSimulator(): void {
  simulatorInstance = null;
}
