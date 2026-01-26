// Neuronaut World - Game Interface JavaScript
// 2D Civilization Simulator with Multiple Views

// ========================================
// Global State
// ========================================
let ws = null;
let worldState = null;
let isPaused = false;
let currentSpeed = 1;
let currentTab = 'world';

// Camera state for world view
const camera = {
    x: 0,
    y: 0,
    zoom: 1,
    targetZoom: 1,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
    dragStartCamX: 0,
    dragStartCamY: 0
};

// Tile rendering constants
const TILE_SIZE = 32; // Base tile size in pixels
const WORLD_WIDTH = 100;
const WORLD_HEIGHT = 100;

// Color schemes for different terrains
const TERRAIN_COLORS = {
    grass: '#2d5a2f',
    forest: '#1a4d2e',
    water: '#1e3a5f',
    mountain: '#4a4543',
    desert: '#c2b280',
    snow: '#e8f4f8'
};

// Sprite colors for agents (simple colored circles with faces)
const AGENT_SPRITES = {
    male: '#60a5fa',
    female: '#ec4899',
    non_binary: '#a78bfa'
};

// Activity feed icons
const ACTIVITY_ICONS = {
    birth: '👶',
    death: '💀',
    conflict: '⚔️',
    trade: '🤝',
    building: '🏗️',
    tech: '🔬',
    exploration: '🗺️',
    resource: '⛏️'
};

// ========================================
// WebSocket Connection
// ========================================
function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('🌍 Connected to Neuronaut World');
        document.getElementById('connectionStatus').textContent = 'Connected';
        hideLoading();
    };

    ws.onmessage = (event) => {
        worldState = JSON.parse(event.data);
        updateUI();
    };

    ws.onclose = () => {
        console.log('Connection lost, reconnecting...');
        document.getElementById('connectionStatus').textContent = 'Reconnecting...';
        setTimeout(connect, 2000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// ========================================
// UI Updates
// ========================================
function updateUI() {
    if (!worldState) return;

    // Update top bar stats
    updateTopBar();

    // Update mini-map
    updateMiniMap();

    // Update sidebar stats
    updateSidebarStats();

    // Update current tab content
    updateCurrentTab();

    // Update activity feed
    updateActivityFeed();
}

function updateTopBar() {
    const agents = worldState.agents || [];
    const aliveAgents = agents.filter(a => a.alive);

    document.getElementById('topPopulation').textContent = agents.length;
    document.getElementById('topAlive').textContent = aliveAgents.length;
    document.getElementById('topTick').textContent = worldState.world?.current_tick || 0;
    document.getElementById('topCivs').textContent = worldState.civilizations?.length || 1;
}

function updateSidebarStats() {
    const agents = worldState.agents || [];
    const aliveAgents = agents.filter(a => a.alive);

    // Total wealth
    const totalWealth = agents.reduce((sum, a) => sum + (a.wealth || 0), 0);
    document.getElementById('totalWealth').textContent = '$' + Math.floor(totalWealth);

    // Avg satisfaction
    const avgSat = aliveAgents.length > 0
        ? aliveAgents.reduce((sum, a) => sum + (a.life_satisfaction || 0), 0) / aliveAgents.length
        : 0;
    document.getElementById('avgSatisfaction').textContent = Math.floor(avgSat * 100) + '%';

    // Buildings (placeholder)
    document.getElementById('totalBuildings').textContent = worldState.buildings?.length || 0;

    // Technologies (placeholder)
    document.getElementById('totalTech').textContent = worldState.technologies?.length || 0;

    // Resources (placeholder)
    document.getElementById('totalResources').textContent = Object.keys(worldState.resources || {}).length;

    // Conflicts (placeholder)
    document.getElementById('totalConflicts').textContent = worldState.conflicts?.length || 0;
}

function updateCurrentTab() {
    switch(currentTab) {
        case 'world':
            renderWorldCanvas();
            break;
        case 'agents':
            renderAgentsGrid();
            break;
        case 'resources':
            renderResourcesGrid();
            break;
        case 'buildings':
            renderBuildingsGrid();
            break;
        case 'tech':
            renderTechTree();
            break;
        case 'civs':
            renderCivilizations();
            break;
        case 'economy':
            renderEconomy();
            break;
        case 'conflicts':
            renderConflicts();
            break;
        case 'narrative':
            renderNarrative();
            break;
    }
}

// ========================================
// World Canvas Rendering
// ========================================
function renderWorldCanvas() {
    const canvas = document.getElementById('worldCanvas');
    const ctx = canvas.getContext('2d');

    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // Clear canvas
    ctx.fillStyle = '#0a0e1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!worldState || !worldState.agents) return;

    // Apply camera transform
    ctx.save();
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.scale(camera.zoom, camera.zoom);
    ctx.translate(-camera.x, -camera.y);

    // Draw terrain grid
    drawTerrainGrid(ctx);

    // Draw resource nodes
    drawResourceNodes(ctx);

    // Draw buildings
    drawBuildings(ctx);

    // Draw agents with sprites
    drawAgents(ctx);

    // Draw territories (if multiple civs)
    drawTerritories(ctx);

    ctx.restore();

    // Update zoom indicator
    document.getElementById('zoomIndicator').textContent =
        `Zoom: ${Math.floor(camera.zoom * 100)}%`;
}

function drawTerrainGrid(ctx) {
    const tileSize = TILE_SIZE;
    const visibleTilesX = Math.ceil(WORLD_WIDTH);
    const visibleTilesY = Math.ceil(WORLD_HEIGHT);

    // Draw grid pattern
    for (let x = 0; x < visibleTilesX; x++) {
        for (let y = 0; y < visibleTilesY; y++) {
            const px = x * tileSize;
            const py = y * tileSize;

            // Varied terrain based on position (simple procedural)
            let color = TERRAIN_COLORS.grass;

            // Water areas
            if ((x < 20 && y > 60) || (x > 70 && y < 30)) {
                color = TERRAIN_COLORS.water;
            }
            // Mountains
            else if ((x > 40 && x < 60 && y > 20 && y < 40)) {
                color = TERRAIN_COLORS.mountain;
            }
            // Forest
            else if (x > 60 && y > 60) {
                color = TERRAIN_COLORS.forest;
            }

            // Add some variation
            const variation = (Math.sin(x * 0.1) * Math.cos(y * 0.1)) * 20;
            const r = parseInt(color.slice(1, 3), 16) + variation;
            const g = parseInt(color.slice(3, 5), 16) + variation;
            const b = parseInt(color.slice(5, 7), 16) + variation;

            ctx.fillStyle = `rgb(${Math.max(0, Math.min(255, r))}, ${Math.max(0, Math.min(255, g))}, ${Math.max(0, Math.min(255, b))})`;
            ctx.fillRect(px, py, tileSize, tileSize);

            // Grid lines
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
            ctx.lineWidth = 1;
            ctx.strokeRect(px, py, tileSize, tileSize);
        }
    }
}

function drawResourceNodes(ctx) {
    // Placeholder: draw some resource nodes
    const resourceNodes = [
        { x: 30, y: 30, type: 'wood', icon: '🌲' },
        { x: 70, y: 70, type: 'wood', icon: '🌲' },
        { x: 50, y: 50, type: 'stone', icon: '🪨' },
        { x: 20, y: 80, type: 'food', icon: '🌾' },
        { x: 80, y: 20, type: 'food', icon: '🌾' }
    ];

    resourceNodes.forEach(node => {
        const px = node.x * TILE_SIZE + TILE_SIZE / 2;
        const py = node.y * TILE_SIZE + TILE_SIZE / 2;

        // Draw resource icon
        ctx.font = '20px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.icon, px, py);
    });
}

function drawBuildings(ctx) {
    // Placeholder: draw some buildings
    const buildings = worldState.buildings || [];

    buildings.forEach(building => {
        const px = (building.location?.x || 50) * TILE_SIZE / 100 * WORLD_WIDTH;
        const py = (building.location?.y || 50) * TILE_SIZE / 100 * WORLD_HEIGHT;

        // Draw building as a rectangle with icon
        ctx.fillStyle = '#8b5cf6';
        ctx.fillRect(px - 12, py - 12, 24, 24);
        ctx.strokeStyle = '#a78bfa';
        ctx.lineWidth = 2;
        ctx.strokeRect(px - 12, py - 12, 24, 24);

        // Icon
        ctx.font = '16px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#fff';
        ctx.fillText('🏛️', px, py);
    });
}

function drawAgents(ctx) {
    const agents = worldState.agents || [];

    agents.forEach(agent => {
        if (!agent.alive) return;

        const px = (agent.location?.x || 50) * TILE_SIZE / 100 * WORLD_WIDTH;
        const py = (agent.location?.y || 50) * TILE_SIZE / 100 * WORLD_HEIGHT;

        // Agent color based on gender
        const color = AGENT_SPRITES[agent.gender] || AGENT_SPRITES.non_binary;

        // Draw shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.beginPath();
        ctx.ellipse(px, py + 10, 6, 3, 0, 0, Math.PI * 2);
        ctx.fill();

        // Draw agent body (circle)
        const size = agent.is_player ? 10 : 8;

        // Glow effect based on mood
        let glowColor = '#fbbf24';
        if (agent.mood > 0.3) glowColor = '#4ade80';
        else if (agent.mood < -0.3) glowColor = '#f87171';

        const gradient = ctx.createRadialGradient(px, py, 0, px, py, size * 2);
        gradient.addColorStop(0, glowColor + '40');
        gradient.addColorStop(1, glowColor + '00');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(px, py, size * 2, 0, Math.PI * 2);
        ctx.fill();

        // Agent circle
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(px, py, size, 0, Math.PI * 2);
        ctx.fill();

        // Border
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Face (simple dots for eyes)
        ctx.fillStyle = '#000';
        ctx.beginPath();
        ctx.arc(px - 3, py - 2, 1.5, 0, Math.PI * 2);
        ctx.arc(px + 3, py - 2, 1.5, 0, Math.PI * 2);
        ctx.fill();

        // Smile or frown based on mood
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        if (agent.mood > 0) {
            ctx.arc(px, py + 1, 4, 0.2, Math.PI - 0.2); // Smile
        } else {
            ctx.arc(px, py + 4, 4, Math.PI + 0.2, Math.PI * 2 - 0.2); // Frown
        }
        ctx.stroke();

        // Name label for players or if zoomed in
        if (agent.is_player || camera.zoom > 1.5) {
            ctx.font = 'bold 10px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            ctx.fillStyle = '#000';
            ctx.fillText(agent.name, px + 1, py - size - 3);
            ctx.fillStyle = '#fbbf24';
            ctx.fillText(agent.name, px, py - size - 4);
        }
    });
}

function drawTerritories(ctx) {
    // Placeholder for civilization territories
    // Would draw borders between different civilizations
}

// ========================================
// Mini-Map Rendering
// ========================================
function updateMiniMap() {
    const canvas = document.getElementById('miniMapCanvas');
    const ctx = canvas.getContext('2d');

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // Background
    ctx.fillStyle = '#0a0e1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!worldState || !worldState.agents) return;

    const scaleX = canvas.width / WORLD_WIDTH;
    const scaleY = canvas.height / WORLD_HEIGHT;

    // Draw agents as colored dots
    worldState.agents.forEach(agent => {
        if (!agent.alive) return;

        const x = (agent.location?.x || 50) * scaleX;
        const y = (agent.location?.y || 50) * scaleY;

        const color = AGENT_SPRITES[agent.gender] || AGENT_SPRITES.non_binary;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();

        // Larger ring for players
        if (agent.is_player) {
            ctx.strokeStyle = '#fbbf24';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(x, y, 5, 0, Math.PI * 2);
            ctx.stroke();
        }
    });

    // Draw camera viewport
    const viewX = (camera.x / TILE_SIZE) * scaleX;
    const viewY = (camera.y / TILE_SIZE) * scaleY;
    const viewW = (canvas.width / camera.zoom) * 0.3;
    const viewH = (canvas.height / camera.zoom) * 0.3;

    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 2;
    ctx.strokeRect(
        viewX - viewW / 2,
        viewY - viewH / 2,
        viewW,
        viewH
    );
}

// ========================================
// Agents Grid Rendering
// ========================================
function renderAgentsGrid() {
    const grid = document.getElementById('agentsGrid');
    const agents = worldState.agents || [];

    const html = agents.map(agent => {
        const moodClass = agent.mood > 0.3 ? 'mood-happy' :
                         agent.mood < -0.3 ? 'mood-sad' : 'mood-neutral';

        const emoji = agent.gender === 'male' ? '👨' :
                     agent.gender === 'female' ? '👩' : '🧑';

        const role = agent.current_action || 'Idle';

        return `
            <div class="agent-card" onclick="showAgentDetails('${agent.id}')">
                <div class="agent-card-header">
                    <div class="agent-avatar ${moodClass}">
                        ${emoji}
                    </div>
                    <div class="agent-info">
                        <div class="agent-name">${agent.name}</div>
                        <div class="agent-role">${role}</div>
                        <div class="agent-location">📍 (${Math.floor(agent.location?.x || 0)}, ${Math.floor(agent.location?.y || 0)})</div>
                    </div>
                </div>
                <div class="agent-stats">
                    <div class="agent-stat-bar">
                        <div class="agent-stat-label">Health</div>
                        <div class="stat-bar">
                            <div class="stat-bar-fill health" style="width: ${(agent.health || 0) * 100}%"></div>
                        </div>
                    </div>
                    <div class="agent-stat-bar">
                        <div class="agent-stat-label">Energy</div>
                        <div class="stat-bar">
                            <div class="stat-bar-fill energy" style="width: ${(agent.energy || 0) * 100}%"></div>
                        </div>
                    </div>
                    <div class="agent-stat-bar">
                        <div class="agent-stat-label">Satisfaction</div>
                        <div class="stat-bar">
                            <div class="stat-bar-fill satisfaction" style="width: ${(agent.life_satisfaction || 0) * 100}%"></div>
                        </div>
                    </div>
                    <div class="agent-stat-bar">
                        <div class="agent-stat-label">Wealth</div>
                        <div class="stat-bar">
                            <div class="stat-bar-fill wealth" style="width: ${Math.min(100, (agent.wealth || 0) / 10)}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    grid.innerHTML = html || '<div style="padding: 20px; text-align: center; color: #a0aec0;">No agents yet</div>';
}

// ========================================
// Resources Grid
// ========================================
function renderResourcesGrid() {
    const grid = document.getElementById('resourcesGrid');

    const resources = [
        { name: 'Wood', icon: '🌲', amount: 1250 },
        { name: 'Stone', icon: '🪨', amount: 830 },
        { name: 'Food', icon: '🌾', amount: 2100 },
        { name: 'Gold', icon: '💰', amount: 450 },
        { name: 'Iron', icon: '⚙️', amount: 620 },
        { name: 'Water', icon: '💧', amount: 3000 }
    ];

    const html = resources.map(res => `
        <div class="resource-card">
            <div class="resource-icon">${res.icon}</div>
            <div class="resource-name">${res.name}</div>
            <div class="resource-amount">${res.amount}</div>
        </div>
    `).join('');

    grid.innerHTML = html;
}

// ========================================
// Buildings Grid
// ========================================
function renderBuildingsGrid() {
    const grid = document.getElementById('buildingsGrid');

    const buildings = [
        { name: 'Homes', icon: '🏠', count: 5 },
        { name: 'Farms', icon: '🌾', count: 3 },
        { name: 'Workshops', icon: '🔨', count: 2 },
        { name: 'Markets', icon: '🏪', count: 1 },
        { name: 'Libraries', icon: '📚', count: 1 }
    ];

    const html = buildings.map(building => `
        <div class="resource-card">
            <div class="resource-icon">${building.icon}</div>
            <div class="resource-name">${building.name}</div>
            <div class="resource-amount">${building.count}</div>
        </div>
    `).join('');

    grid.innerHTML = html;
}

// ========================================
// Tech Tree
// ========================================
function renderTechTree() {
    const techTree = document.getElementById('techTree');

    const eras = [
        {
            name: 'Stone Age',
            techs: [
                { name: 'Fire', icon: '🔥', unlocked: true },
                { name: 'Hunting', icon: '🏹', unlocked: true },
                { name: 'Gathering', icon: '🌾', unlocked: true },
                { name: 'Basic Tools', icon: '🔨', unlocked: false }
            ]
        },
        {
            name: 'Bronze Age',
            techs: [
                { name: 'Agriculture', icon: '🚜', unlocked: false },
                { name: 'Metalworking', icon: '⚒️', unlocked: false },
                { name: 'Writing', icon: '✍️', unlocked: false },
                { name: 'Trade', icon: '🤝', unlocked: false }
            ]
        },
        {
            name: 'Iron Age',
            techs: [
                { name: 'Iron Tools', icon: '⚙️', unlocked: false },
                { name: 'Architecture', icon: '🏛️', unlocked: false },
                { name: 'Mathematics', icon: '📐', unlocked: false }
            ]
        }
    ];

    const html = eras.map(era => `
        <div class="tech-era">
            <div class="tech-era-title">${era.name}</div>
            <div class="tech-grid">
                ${era.techs.map(tech => `
                    <div class="tech-node ${tech.unlocked ? 'unlocked' : 'locked'}">
                        <div class="tech-icon">${tech.icon}</div>
                        <div class="tech-name">${tech.name}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');

    techTree.innerHTML = html;
}

// ========================================
// Civilizations
// ========================================
function renderCivilizations() {
    const civsList = document.getElementById('civsList');

    const civs = [
        {
            name: 'The First People',
            population: worldState?.agents?.filter(a => a.alive).length || 0,
            wealth: 5000,
            territory: 25,
            tech: 3,
            military: 2
        }
    ];

    const html = civs.map(civ => `
        <div class="civ-card">
            <div class="civ-header">
                <div class="civ-name">${civ.name}</div>
                <div class="civ-population">👥 ${civ.population} Citizens</div>
            </div>
            <div class="civ-stats">
                <div class="civ-stat">
                    <div class="civ-stat-label">Wealth</div>
                    <div class="civ-stat-value">$${civ.wealth}</div>
                </div>
                <div class="civ-stat">
                    <div class="civ-stat-label">Territory</div>
                    <div class="civ-stat-value">${civ.territory}%</div>
                </div>
                <div class="civ-stat">
                    <div class="civ-stat-label">Technology</div>
                    <div class="civ-stat-value">${civ.tech}</div>
                </div>
                <div class="civ-stat">
                    <div class="civ-stat-label">Military</div>
                    <div class="civ-stat-value">${civ.military}</div>
                </div>
            </div>
        </div>
    `).join('');

    civsList.innerHTML = html;
}

// ========================================
// Economy
// ========================================
function renderEconomy() {
    if (!worldState || !worldState.agents) return;

    const agents = worldState.agents.filter(a => a.alive);
    const totalWealth = agents.reduce((sum, a) => sum + (a.wealth || 0), 0);
    const avgWealth = agents.length > 0 ? totalWealth / agents.length : 0;

    const sorted = [...agents].sort((a, b) => (b.wealth || 0) - (a.wealth || 0));
    const wealthiest = sorted[0];
    const poorest = sorted[sorted.length - 1];

    document.getElementById('ecoTotalWealth').textContent = '$' + Math.floor(totalWealth);
    document.getElementById('ecoAvgWealth').textContent = '$' + Math.floor(avgWealth);
    document.getElementById('ecoWealthiest').textContent = wealthiest ?
        `${wealthiest.name} ($${Math.floor(wealthiest.wealth)})` : '-';
    document.getElementById('ecoPoorest').textContent = poorest ?
        `${poorest.name} ($${Math.floor(poorest.wealth)})` : '-';
}

// ========================================
// Conflicts
// ========================================
function renderConflicts() {
    const conflictsList = document.getElementById('conflictsList');

    const conflicts = worldState?.conflicts || [];

    if (conflicts.length === 0) {
        conflictsList.innerHTML = '<div style="padding: 20px; text-align: center; color: #a0aec0;">No conflicts yet. Peace reigns!</div>';
        return;
    }

    const html = conflicts.map(conflict => `
        <div class="activity-item event-conflict">
            <div class="activity-time">Tick ${conflict.tick}</div>
            <div class="activity-title">⚔️ ${conflict.title}</div>
            <div class="activity-desc">${conflict.description}</div>
        </div>
    `).join('');

    conflictsList.innerHTML = html;
}

// ========================================
// Narrative
// ========================================
function renderNarrative() {
    const narrativeContent = document.getElementById('narrativeContent');

    // Placeholder narrative
    const narrative = worldState?.narrative || `
        <p><strong>In the beginning...</strong></p>
        <p>A small group of people emerged in a vast, untamed world. They knew nothing of what lay ahead, only that they must survive.</p>
        <p>The early days were harsh. Food was scarce, and shelter was a luxury few could afford. But slowly, through trial and error, they learned.</p>
        <p>Fire was discovered. Tools were crafted. The first homes were built.</p>
        <p>And so began the story of <span style="color: #fbbf24;">The First People</span>...</p>
    `;

    narrativeContent.innerHTML = narrative;
}

// ========================================
// Activity Feed
// ========================================
function updateActivityFeed() {
    const feed = document.getElementById('activityFeed');
    const events = worldState?.recent_events || [];

    if (events.length === 0) {
        feed.innerHTML = '<div style="padding: 15px; text-align: center; color: #718096;">No recent activity</div>';
        return;
    }

    const html = events.slice(0, 20).reverse().map(event => {
        const eventType = event.type || 'default';
        const icon = ACTIVITY_ICONS[eventType] || '📌';

        return `
            <div class="activity-item event-${eventType}">
                <div class="activity-time">Tick ${event.tick}</div>
                <div class="activity-title">${icon} ${event.title || 'Event'}</div>
                <div class="activity-desc">${event.description || ''}</div>
            </div>
        `;
    }).join('');

    feed.innerHTML = html;
}

// ========================================
// Agent Details Modal
// ========================================
async function showAgentDetails(agentId) {
    try {
        const response = await fetch(`http://localhost:8000/agents/${agentId}`);
        const agent = await response.json();

        document.getElementById('modalTitle').textContent =
            `${agent.name} - ${agent.age} yo ${agent.gender}`;

        const html = `
            <div class="detail-section">
                <div class="detail-section-title">📊 Vital Stats</div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <div class="detail-label">Health</div>
                        <div class="detail-value">${Math.floor((agent.health || 0) * 100)}%</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Energy</div>
                        <div class="detail-value">${Math.floor((agent.energy || 0) * 100)}%</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Wealth</div>
                        <div class="detail-value">$${Math.floor(agent.wealth || 0)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Satisfaction</div>
                        <div class="detail-value">${Math.floor((agent.life_satisfaction || 0) * 100)}%</div>
                    </div>
                </div>
            </div>

            <div class="detail-section">
                <div class="detail-section-title">🧬 Personality</div>
                <div class="detail-grid">
                    ${Object.entries(agent.personality || {}).map(([trait, value]) => `
                        <div class="detail-item">
                            <div class="detail-label">${formatLabel(trait)}</div>
                            <div class="detail-value">${Math.floor(value * 100)}%</div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="detail-section">
                <div class="detail-section-title">❤️ Emotions</div>
                <div class="detail-grid">
                    ${Object.entries(agent.emotions || {}).map(([emotion, value]) => `
                        <div class="detail-item">
                            <div class="detail-label">${formatLabel(emotion)}</div>
                            <div class="detail-value">${Math.floor(value * 100)}%</div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="detail-section">
                <div class="detail-section-title">🎯 Current Needs</div>
                <div class="detail-grid">
                    ${Object.entries(agent.needs || {}).map(([need, value]) => `
                        <div class="detail-item">
                            <div class="detail-label">${formatLabel(need)}</div>
                            <div class="detail-value">${Math.floor(value * 100)}%</div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="detail-section">
                <div class="detail-section-title">🎒 Inventory</div>
                <div class="badge-list">
                    ${Object.keys(agent.inventory || {}).length > 0 ?
                        Object.entries(agent.inventory).map(([item, qty]) => `
                            <div class="badge">${formatLabel(item)}: ${qty}</div>
                        `).join('') :
                        '<div class="badge">Empty</div>'
                    }
                </div>
            </div>

            <div class="detail-section">
                <div class="detail-section-title">🧠 Recent Memories</div>
                <div class="memory-list">
                    ${(agent.memories || []).length > 0 ?
                        agent.memories.slice(-5).reverse().map(mem => `
                            <div class="memory-item">${mem.description || mem.event || JSON.stringify(mem)}</div>
                        `).join('') :
                        '<div class="memory-item">No memories yet</div>'
                    }
                </div>
            </div>
        `;

        document.getElementById('modalBody').innerHTML = html;
        document.getElementById('agentModal').classList.add('active');
    } catch (error) {
        console.error('Error loading agent details:', error);
    }
}

function closeModal() {
    document.getElementById('agentModal').classList.remove('active');
}

function formatLabel(str) {
    return str.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// ========================================
// Tab Switching
// ========================================
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const panels = document.querySelectorAll('.tab-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;

            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update active panel
            panels.forEach(p => p.classList.remove('active'));
            document.getElementById(`panel-${tabName}`).classList.add('active');

            // Update current tab
            currentTab = tabName;

            // Render content
            updateCurrentTab();
        });
    });
}

// ========================================
// Camera Controls (Pan & Zoom)
// ========================================
function initCameraControls() {
    const canvas = document.getElementById('worldCanvas');

    // Mouse wheel zoom
    canvas.addEventListener('wheel', (e) => {
        e.preventDefault();

        const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
        camera.targetZoom = Math.max(0.3, Math.min(3, camera.zoom * zoomFactor));
    });

    // Mouse drag pan
    canvas.addEventListener('mousedown', (e) => {
        camera.isDragging = true;
        camera.dragStartX = e.clientX;
        camera.dragStartY = e.clientY;
        camera.dragStartCamX = camera.x;
        camera.dragStartCamY = camera.y;
    });

    canvas.addEventListener('mousemove', (e) => {
        if (!camera.isDragging) return;

        const dx = (e.clientX - camera.dragStartX) / camera.zoom;
        const dy = (e.clientY - camera.dragStartY) / camera.zoom;

        camera.x = camera.dragStartCamX - dx;
        camera.y = camera.dragStartCamY - dy;
    });

    canvas.addEventListener('mouseup', () => {
        camera.isDragging = false;
    });

    canvas.addEventListener('mouseleave', () => {
        camera.isDragging = false;
    });

    // Click to select agent
    canvas.addEventListener('click', (e) => {
        if (!worldState || !worldState.agents) return;

        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        // Transform to world coordinates
        const worldX = ((mouseX - canvas.width / 2) / camera.zoom + camera.x) / TILE_SIZE * 100;
        const worldY = ((mouseY - canvas.height / 2) / camera.zoom + camera.y) / TILE_SIZE * 100;

        // Find clicked agent
        for (const agent of worldState.agents) {
            const ax = agent.location?.x || 50;
            const ay = agent.location?.y || 50;
            const distance = Math.sqrt((worldX - ax) ** 2 + (worldY - ay) ** 2);

            if (distance < 3) {
                showAgentDetails(agent.id);
                break;
            }
        }
    });

    // Smooth zoom animation
    setInterval(() => {
        camera.zoom += (camera.targetZoom - camera.zoom) * 0.1;
    }, 16);
}

// ========================================
// Speed Controls
// ========================================
function togglePause() {
    isPaused = !isPaused;
    const btn = document.getElementById('pauseBtn');

    if (isPaused) {
        btn.classList.add('active');
        btn.innerHTML = '▶ RESUME';
    } else {
        btn.classList.remove('active');
        btn.innerHTML = '⏸ PAUSE';
    }

    // Send pause command to server
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ command: 'pause', value: isPaused }));
    }
}

function setSpeed(speed) {
    currentSpeed = speed;

    // Update UI
    document.querySelectorAll('.speed-btn:not(.pause-btn)').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-speed="${speed}"]`).classList.add('active');
    document.getElementById('speedDisplay').textContent = speed + 'x';

    // Send speed command to server
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ command: 'speed', value: speed }));
    }
}

// ========================================
// Loading Screen
// ========================================
function hideLoading() {
    setTimeout(() => {
        document.getElementById('loadingScreen').classList.add('hidden');
    }, 1000);
}

// ========================================
// Initialization
// ========================================
function init() {
    console.log('🎮 Initializing Neuronaut World Game Interface...');

    // Initialize tabs
    initTabs();

    // Initialize camera controls
    initCameraControls();

    // Connect to WebSocket
    connect();

    // Render loop for animations
    function renderLoop() {
        if (currentTab === 'world') {
            renderWorldCanvas();
        }
        requestAnimationFrame(renderLoop);
    }
    renderLoop();

    // Mini-map update loop
    setInterval(() => {
        updateMiniMap();
    }, 100);

    console.log('✅ Game interface ready!');
}

// Start when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    const modal = document.getElementById('agentModal');
    if (e.target === modal) {
        closeModal();
    }
});
