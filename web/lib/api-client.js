/**
 * Simulation API Client (Vanilla JS)
 * Adapted from use-api-client.ts
 * 
 * Type-safe(-ish) API client for FastAPI backend
 */

const API_URL = 'http://localhost:8000';

class SimulationAPI {
    constructor(baseUrl = API_URL) {
        this.baseUrl = baseUrl;
    }

    async fetch(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`[API] Error fetching ${endpoint}:`, error);
            throw error;
        }
    }

    // ============================================================================
    // SIMULATION STATE
    // ============================================================================

    async getSimulationState() {
        return this.fetch('/');
    }

    async getSimulationStats() {
        return this.fetch('/stats');
    }

    // ============================================================================
    // AGENTS
    // ============================================================================

    async getAgents() {
        return this.fetch('/agents');
    }

    async getAgent(agentId) {
        return this.fetch(`/agent/${agentId}`);
    }

    async getAgentProfile(agentId) {
        return this.fetch(`/agent/${agentId}/profile`);
    }

    async getAgentMemories(agentId) {
        return this.fetch(`/agent/${agentId}/memories`);
    }

    async getAgentRelationships(agentId) {
        return this.fetch(`/agent/${agentId}/relationships`);
    }

    // ============================================================================
    // BUILDINGS
    // ============================================================================

    async getBuildings() {
        return this.fetch('/buildings');
    }

    async getBuilding(buildingId) {
        return this.fetch(`/building/${buildingId}`);
    }

    // ============================================================================
    // WORLD
    // ============================================================================

    async getWorldState() {
        return this.fetch('/world');
    }

    async getResources(x, y) {
        return this.fetch(`/world/resources?x=${x}&y=${y}`);
    }

    // ============================================================================
    // ECONOMY
    // ============================================================================

    async getMarketState() {
        return this.fetch('/economy/market');
    }

    async getTradingPosts() {
        return this.fetch('/economy/trading-posts');
    }

    // ============================================================================
    // TECHNOLOGY
    // ============================================================================

    async getTechnologies() {
        return this.fetch('/technologies');
    }

    async getAgentTechnologies(agentId) {
        return this.fetch(`/agent/${agentId}/technologies`);
    }

    // ============================================================================
    // ACTIONS (POST requests)
    // ============================================================================

    async sendAction(agentId, action) {
        return this.fetch(`/agent/${agentId}/action`, {
            method: 'POST',
            body: JSON.stringify(action),
        });
    }

    async pauseSimulation() {
        return this.fetch('/control/pause', { method: 'POST' });
    }

    async resumeSimulation() {
        return this.fetch('/control/resume', { method: 'POST' });
    }

    async setSimulationSpeed(speed) {
        return this.fetch('/control/speed', {
            method: 'POST',
            body: JSON.stringify({ speed }),
        });
    }

    // ============================================================================
    // SAVE/LOAD
    // ============================================================================

    async saveSimulation(name = null) {
        return this.fetch('/save', {
            method: 'POST',
            body: JSON.stringify({ name }),
        });
    }

    async loadSimulation(filename) {
        return this.fetch('/load', {
            method: 'POST',
            body: JSON.stringify({ filename }),
        });
    }

    async listSaves() {
        return this.fetch('/saves');
    }
}

// Create singleton instance
const simulationAPI = new SimulationAPI();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SimulationAPI, simulationAPI };
}
