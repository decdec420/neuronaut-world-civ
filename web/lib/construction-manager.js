/**
 * Construction Progress Manager (Vanilla JS)
 * Adapted from construction-simulator.ts
 * 
 * Manages smooth construction progress animations
 */

class ConstructionManager {
    constructor() {
        this.buildings = new Map();
        this.lastUpdateTime = Date.now();
        this.ticksPerSecond = 10;
        this.callbacks = [];
    }

    /**
     * Add a building to track
     */
    addBuilding(building) {
        this.buildings.set(building.id, { ...building });
    }

    /**
     * Update a building's state
     */
    updateBuilding(buildingId, updates) {
        const building = this.buildings.get(buildingId);
        if (building) {
            Object.assign(building, updates);
        }
    }

    /**
     * Remove a building
     */
    removeBuilding(buildingId) {
        this.buildings.delete(buildingId);
    }

    /**
     * Get building by ID
     */
    getBuilding(buildingId) {
        return this.buildings.get(buildingId);
    }

    /**
     * Get all buildings
     */
    getAllBuildings() {
        return Array.from(this.buildings.values());
    }

    /**
     * Get buildings under construction
     */
    getUnderConstruction() {
        return Array.from(this.buildings.values()).filter(
            b => b.stage !== 'completed' && b.progress < 100
        );
    }

    /**
     * Update construction progress for all buildings
     * Call this in your animation loop
     */
    update() {
        const now = Date.now();
        const deltaTime = (now - this.lastUpdateTime) / 1000;
        this.lastUpdateTime = now;

        const updates = [];

        this.buildings.forEach(building => {
            // Only update buildings under construction
            if (building.stage === 'completed' || building.progress >= 100) {
                return;
            }

            // Calculate progress based on build time
            // This is a simple linear progression
            const oldProgress = building.progress;
            const oldStage = building.stage;

            // Progress per second (assuming buildTime is in ticks)
            const buildTime = building.buildTime || 1000;
            const progressPerSecond = (100 / buildTime) * this.ticksPerSecond;
            const progressIncrement = progressPerSecond * deltaTime;

            building.progress = Math.min(100, building.progress + progressIncrement);

            // Update construction stage based on progress
            const newStage = this.getConstructionStage(building.progress);
            building.stage = newStage;

            // Check if just completed
            const justCompleted = building.progress >= 100 && oldProgress < 100;
            if (justCompleted) {
                building.completed = Date.now();
            }

            // Track changes
            if (building.progress !== oldProgress || building.stage !== oldStage) {
                updates.push({
                    buildingId: building.id,
                    progress: building.progress,
                    stage: building.stage,
                    justCompleted,
                });
            }
        });

        // Notify callbacks
        if (updates.length > 0) {
            this.callbacks.forEach(cb => cb(updates));
        }

        return updates;
    }

    /**
     * Get construction stage based on progress percentage
     */
    getConstructionStage(progress) {
        if (progress >= 100) return 'completed';
        if (progress >= 75) return 'finishing';
        if (progress >= 50) return 'framing';
        if (progress >= 25) return 'foundation';
        return 'planning';
    }

    /**
     * Subscribe to construction updates
     */
    onUpdate(callback) {
        this.callbacks.push(callback);
        return () => {
            const index = this.callbacks.indexOf(callback);
            if (index > -1) {
                this.callbacks.splice(index, 1);
            }
        };
    }

    /**
     * Get stage color for visualization
     */
    getStageColor(stage) {
        const colors = {
            planning: '#64748b',     // Gray
            foundation: '#f59e0b',   // Orange
            framing: '#3b82f6',      // Blue
            finishing: '#22c55e',    // Green
            completed: '#10b981',    // Bright green
        };
        return colors[stage] || colors.planning;
    }

    /**
     * Get stage icon
     */
    getStageIcon(stage) {
        const icons = {
            planning: '📋',
            foundation: '🏗️',
            framing: '🔨',
            finishing: '🎨',
            completed: '✅',
        };
        return icons[stage] || icons.planning;
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConstructionManager;
}
