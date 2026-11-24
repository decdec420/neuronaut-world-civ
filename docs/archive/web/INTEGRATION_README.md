# Frontend Integration - Cyborg Edition 🤖

This directory contains integrated utilities from the Next.js frontend, adapted for the main HTML/JS interface.

## 📁 Structure

```
web/
├── lib/                          # Utility libraries
│   ├── api-client.js            # Type-safe API client (adapted from TS)
│   ├── simulation-websocket.js  # WebSocket manager with auto-reconnect
│   ├── construction-manager.js  # Building progress animations
│   └── [TS files]               # Original TypeScript files (reference)
│
├── types/                        # Type definitions (TypeScript)
│   ├── technology.ts            # Tech tree types (20+ technologies)
│   ├── structures.ts            # Building types (13 buildings)
│   └── view-modes.ts            # View mode switching
│
├── hooks/                        # React hooks (reference only)
│   ├── use-api-client.ts        # Original TypeScript API client
│   ├── use-simulation-websocket.ts
│   └── use-simulation-data.ts
│
├── game_interface.html          # Main 12-tab UI
└── game_interface.js            # Main game logic
```

## 🔧 Integrated Features

### 1. **API Client** (`lib/api-client.js`)
Clean, organized API calls to FastAPI backend:

```javascript
// Usage in game_interface.js
const api = new SimulationAPI();

// Fetch agents
const agents = await api.getAgents();

// Get specific agent
const agent = await api.getAgent(agentId);

// Send action
await api.sendAction(agentId, { type: 'move', x: 10, y: 20 });

// Control simulation
await api.pauseSimulation();
await api.setSimulationSpeed(2);
```

### 2. **WebSocket Manager** (`lib/simulation-websocket.js`)
Robust WebSocket connection with auto-reconnect:

```javascript
// Usage in game_interface.js
const ws = new SimulationWebSocket({
    url: 'ws://localhost:8000/ws',
    autoConnect: true,
    reconnectDelay: 3000,
    onMessage: (update) => {
        console.log('Simulation update:', update);
        // Update UI
    },
    onConnect: () => console.log('Connected!'),
    onDisconnect: () => console.log('Disconnected...'),
});

// Send commands
ws.send({ command: 'pause' });

// Clean disconnect
ws.disconnect();
```

### 3. **Construction Manager** (`lib/construction-manager.js`)
Smooth building progress animations:

```javascript
const constructionMgr = new ConstructionManager();

// Add buildings
buildings.forEach(b => constructionMgr.addBuilding(b));

// In animation loop
function animate() {
    const updates = constructionMgr.update();
    updates.forEach(update => {
        // Update building visuals
        console.log(`${update.buildingId}: ${update.progress}% (${update.stage})`);
    });
    requestAnimationFrame(animate);
}

// Subscribe to updates
constructionMgr.onUpdate((updates) => {
    updates.forEach(u => {
        if (u.justCompleted) {
            showNotification(`Building completed!`);
        }
    });
});
```

## 📚 Type Definitions (Reference)

The TypeScript files in `types/` provide excellent data models:

### **Technology System** (`types/technology.ts`)
- 20+ technologies across 5 eras (Stone Age → Classical Era)
- Prerequisites, costs, unlock chains
- Categories: survival, construction, production, military, science

### **Building System** (`types/structures.ts`)
- 13 building types: campfire → laboratory
- Construction stages: planning → foundation → framing → finishing → completed
- Resource costs, build times, capacities

### **View Modes** (`types/view-modes.ts`)
- normal, agents, buildings, resources, tech, economy
- Filter settings for each mode

## 🎯 Next Steps

### TODO: Integrate into `game_interface.js`

1. **Replace fetch calls** with `SimulationAPI`:
   ```javascript
   // OLD
   fetch('/agents').then(r => r.json())
   
   // NEW
   simulationAPI.getAgents()
   ```

2. **Replace WebSocket** with `SimulationWebSocket`:
   ```javascript
   // OLD
   const ws = new WebSocket('ws://localhost:8000/ws')
   
   // NEW
   const ws = new SimulationWebSocket({ onMessage: handleUpdate })
   ```

3. **Add construction animations**:
   ```javascript
   const constructionMgr = new ConstructionManager();
   // Animate building progress smoothly
   ```

4. **Add type safety** (optional):
   - Convert `types/*.ts` to JSDoc comments
   - Or use TypeScript for `game_interface.js`

## 🚀 Benefits

- ✅ **Cleaner API calls** - No more scattered fetch() calls
- ✅ **Auto-reconnect WebSocket** - Handles connection drops gracefully  
- ✅ **Smooth animations** - Buildings progress realistically
- ✅ **Better organization** - Clear separation of concerns
- ✅ **Type reference** - TypeScript files document the data models

## 📖 Original Source

These files were adapted from `neuronaut-world/` (Next.js frontend):
- Converted React hooks → vanilla JS classes
- Kept TypeScript types as reference
- Maintained all core functionality

The original Next.js frontend can be removed once integration is complete.
