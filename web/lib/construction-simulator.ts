/**
 * Construction Progress Simulator
 *
 * Manages automatic construction progress for buildings.
 * Simulates workers building over time with realistic progression.
 */

import type { Building, ConstructionStage } from '@/types/structures';
import { getBuildingConfig, getConstructionStage } from '@/types/structures';

export interface ConstructionUpdate {
  buildingId: string;
  progress: number;
  stage: ConstructionStage;
  justCompleted: boolean;
}

export class ConstructionSimulator {
  private buildings: Map<string, Building> = new Map();
  private lastUpdateTime: number = Date.now();
  private ticksPerSecond: number = 10; // Simulation speed

  constructor(buildings: Building[] = []) {
    buildings.forEach(building => {
      this.buildings.set(building.id, building);
    });
  }

  /**
   * Update construction progress for all buildings
   * Returns list of buildings that had progress updates
   */
  update(): ConstructionUpdate[] {
    const now = Date.now();
    const deltaTime = (now - this.lastUpdateTime) / 1000; // Convert to seconds
    this.lastUpdateTime = now;

    const updates: ConstructionUpdate[] = [];

    this.buildings.forEach(building => {
      // Only update buildings that are under construction
      if (building.stage === 'completed' || building.progress >= 100) {
        return;
      }

      const config = getBuildingConfig(building.type);

      // Calculate progress increment
      // Progress per second = 100 / (buildTime in ticks / ticksPerSecond)
      const progressPerSecond = (100 / config.buildTime) * this.ticksPerSecond;
      const progressIncrement = progressPerSecond * deltaTime;

      // Update progress
      const oldProgress = building.progress;
      const oldStage = building.stage;

      building.progress = Math.min(100, building.progress + progressIncrement);

      // Update construction stage based on new progress
      const newStage = getConstructionStage(building.progress);
      building.stage = newStage;

      // Check if building just completed
      const justCompleted = building.progress >= 100 && oldProgress < 100;
      if (justCompleted) {
        building.completed = Math.floor(now / 100); // Rough tick count
      }

      // Only add to updates if progress or stage changed
      if (building.progress !== oldProgress || building.stage !== oldStage) {
        updates.push({
          buildingId: building.id,
          progress: building.progress,
          stage: building.stage,
          justCompleted,
        });
      }
    });

    return updates;
  }

  /**
   * Add a new building to the simulator
   */
  addBuilding(building: Building): void {
    this.buildings.set(building.id, building);
  }

  /**
   * Remove a building from the simulator
   */
  removeBuilding(buildingId: string): void {
    this.buildings.delete(buildingId);
  }

  /**
   * Get current state of a building
   */
  getBuilding(buildingId: string): Building | undefined {
    return this.buildings.get(buildingId);
  }

  /**
   * Get all buildings currently being simulated
   */
  getAllBuildings(): Building[] {
    return Array.from(this.buildings.values());
  }

  /**
   * Update simulation speed
   */
  setTicksPerSecond(tps: number): void {
    this.ticksPerSecond = tps;
  }

  /**
   * Reset simulation time (useful when pausing/resuming)
   */
  resetTime(): void {
    this.lastUpdateTime = Date.now();
  }
}

/**
 * Create a singleton instance for global use
 */
let simulatorInstance: ConstructionSimulator | null = null;

export function getConstructionSimulator(buildings?: Building[]): ConstructionSimulator {
  if (!simulatorInstance) {
    simulatorInstance = new ConstructionSimulator(buildings);
  }
  return simulatorInstance;
}

export function resetConstructionSimulator(): void {
  simulatorInstance = null;
}
