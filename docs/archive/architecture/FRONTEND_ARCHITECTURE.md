# 🎨 NEURONAUT WORLD - FRONTEND ARCHITECTURE
**Epic Visualization for Autonomous AI Civilizations**

---

## 🎯 CORE VISION

**From**: Blue dots on a grid
**To**: Isometric living world where you watch AI civilizations rise and fall

**Philosophy**: You're not building a game UI. You're building an **observation deck for autonomous AI civilizations** - like NASA mission control meets Civilization.

---

## 🏗️ TECHNOLOGY STACK

### Core Framework
- **Next.js 14+** with App Router
- **React 18** with TypeScript
- **Tailwind CSS** + **Shadcn/ui** components
- Already configured in `/neuronaut-world/`

### Visualization Engine
- **Pixi.js** for world canvas (2D, GPU-accelerated)
- Handles 50-200 animated agents smoothly
- Isometric rendering with sprite animations

### Real-Time Data
- **WebSocket** connection to Python backend
- **React Query** for server state management
- **Zustand** for UI state (lightweight, simple)

### Data Visualization
- **Recharts** for standard charts (population, economy)
- **D3.js** for custom visualizations (relationship graphs, tech trees)

---

## 📱 PRIMARY VIEWS

### 1. WORLD VIEW (70% of user time)
**The main experience - watching civilization unfold**

**Features**:
- Isometric 2D map (30-degree angle)
- Animated agent sprites with walk cycles
- Buildings as 3D isometric landmarks
- Territory overlays with glowing borders
- Resource nodes with particle effects
- Click agent → quick card
- Hover agent → tooltip

**Technical**:
- Pixi.js canvas renderer
- 60fps interpolated movement
- Pan/zoom with Pixi Viewport
- Sprite sheet atlases for performance

### 2. AGENT DETAIL VIEW
**Deep dive into AI psychology - your unique selling point**

**Panels**:
- Personality radar chart
- Needs urgency bars
- Emotions display
- **AI Thoughts** (shows LLM reasoning!) ⭐
- Relationship network graph
- Recent actions timeline
- Current goals with progress

**Why Epic**: Users see WHY agents make decisions. No other sim shows this.

### 3. CIVILIZATION DASHBOARD
**Strategic overview - how's civilization doing?**

**Widgets**:
- Population chart (line graph over time)
- Economic health gauge (GDP, wealth distribution)
- Technology era progress bar
- 10 System cards (agriculture, health, religion, etc.)
- Major events feed
- Crisis alerts

### 4. EVENT FEED
**Narrative layer - emergent storytelling**

**Features**:
- Timeline view with day separators
- Dramatic event cards (full-width for major events)
- Event filtering by category
- Deep linking to agents/locations
- Search functionality

**Dramatic Events**:
- Tax revolts → Breaking news modal
- Bank runs → Economic crisis card
- Discoveries → Achievement celebration
- Deaths → Memorial notification

### 5. SYSTEMS DEEP DIVE
**10 dedicated panels for each system**

**Progressive Disclosure**:
- Level 1: Dashboard cards (glanceable)
- Level 2: System panel (on-demand details)
- Level 3: Agent-specific stats (deep dive)

**Example - Agriculture Panel**:
- Current season with countdown
- Farm list with crop maturity
- Domesticated animals count
- Food production chart
- Recent agriculture events

---

## 🎨 VISUAL DESIGN

### Map Style: Isometric 2D
**NOT top-down dots. Isometric living world!**

- 30-degree isometric perspective
- Textured terrain (grass, dirt, water)
- 32x32px agent sprites with animations
- Isometric building sprites
- Glowing effects for territories/resources

### Agent Representation
**Animated characters, not dots**

- Humanoid sprites with walk cycles
- Action animations (gathering, building, fighting)
- Status glow (green happy, red sad)
- Tool in hand shows current action
- Clothing indicates wealth tier

### Color Palette (Dark Theme)
```css
Background: #0f172a (deep blue-black)
Surface:    #1e293b (slate)
Border:     #334155 (lighter slate)
Text:       #e2e8f0 (off-white)
Accent:     #6366f1 (purple-blue gradient)

Status Colors:
Success:    #10b981 (green)
Warning:    #f59e0b (amber)
Danger:     #ef4444 (red)
Info:       #3b82f6 (blue)

System Colors:
Agriculture: #22c55e (green)
Health:      #ec4899 (pink)
Religion:    #fbbf24 (gold)
Territory:   #8b5cf6 (purple)
Chemistry:   #06b6d4 (cyan)
Energy:      #f97316 (orange)
Materials:   #78716c (gray)
Economy:     #eab308 (yellow)
Life:        #f43f5e (rose)
Fun:         #a78bfa (light purple)
```

### UI Style: Futuristic Mission Control
- Glass morphism (translucent panels with blur)
- Purple-blue gradients
- Smooth 200-300ms transitions
- Grid-based layouts
- Data visualization first
- Typography:
  - Headers: Bold, 24-28px
  - Body: Regular, 14-16px
  - Data: Roboto Mono (monospace)

---

## 🚀 IMPLEMENTATION PHASES

### Phase 1: MVP (Week 1-2)
**Goal**: Ship something watchable

**Features**:
- ✅ Basic Pixi.js world canvas
- ✅ Agent sprites with movement
- ✅ WebSocket integration
- ✅ Agent quick view (click/hover)
- ✅ Simple dashboard (population, tick)
- ✅ Play/pause/speed controls
- ✅ Basic event log (text)

**Success**: User can watch agents move, click for details

### Phase 2: Beautiful (Week 3-4)
**Goal**: Make it visually stunning

**Enhancements**:
- 🎨 Proper isometric terrain
- 🎨 Building sprites
- 🎨 Territory overlays
- 🎨 Animated agents (walk cycles)
- 🎨 Glass morphism UI
- 🎨 Event cards with drama
- 🎨 Data visualizations (charts)

**Success**: Users say "wow, this is beautiful"

### Phase 3: Deep Engagement (Week 5-6)
**Goal**: Tools to explore deeply

**Features**:
- 📊 Civilization dashboard
- 📊 10 system panels
- 📊 Enhanced agent view (AI thoughts!)
- 📊 Search and filters
- 📊 Story summaries

**Success**: Users spend 30+ min exploring

### Phase 4: Advanced (Week 7-8+)
**Goal**: Unique differentiators

**Features**:
- ⚡ Time travel (replay history)
- ⚡ AI transparency (full decision logs)
- ⚡ Interactive elements
- ⚡ Data export
- ⚡ Mobile optimization

**Success**: "Best autonomous AI viewer ever"

---

## 🎯 KEY DESIGN SOLUTIONS

### Solution 1: Epic World Visualization
**Problem**: Blue dots aren't visually interesting
**Solution**: Isometric animated world with storytelling

- Pixi.js canvas with sprite animations
- 60fps interpolated movement
- Particle effects for resources
- Building landmarks
- Territory glow effects

### Solution 2: AI Transparency
**Problem**: Users can't see agent decision-making
**Solution**: "AI Thought Window" shows LLM reasoning

- Purple thought bubble panel
- Real LLM reasoning text
- Factor influence bars
- Warnings from past consequences
- Updates every decision

### Solution 3: Dramatic Events
**Problem**: Emergent events need to feel epic
**Solution**: Breaking news modals + cinematic cards

- Full-screen modal for major events
- Animated entrance
- Color-coded headers
- Clickable agent chips
- "View on Map" button

### Solution 4: 10 Systems Digestibility
**Problem**: Too many systems could overwhelm
**Solution**: Progressive disclosure hierarchy

- Level 1: Dashboard cards (always visible)
- Level 2: System panels (on-demand)
- Level 3: Agent-specific (deep dive)
- Only show relevant systems per context

---

## 📂 CRITICAL FILES TO CREATE

### Priority 1: Core Rendering
```
src/components/world/WorldCanvas.tsx
```
- Pixi.js renderer
- Agent sprites
- Terrain + buildings
- Pan/zoom controls

### Priority 2: Real-Time Data
```
src/hooks/use-simulation-websocket.ts
```
- WebSocket connection
- React Query integration
- Optimistic updates
- Auto-reconnect

### Priority 3: Agent Detail
```
src/components/agents/AgentDetailPanel.tsx
```
- Personality visualization
- AI thoughts display
- Relationship graph
- Goals/actions

### Priority 4: Main Layout
```
src/app/simulation/page.tsx
```
- WorldCanvas orchestration
- Panel layout
- Time controls
- Navigation

### Priority 5: Dramatic Events
```
src/components/events/DramaticEventModal.tsx
```
- Breaking news modal
- Event cards
- Animation
- Deep linking

### Bonus: API Client
```
src/lib/simulation-client.ts
```
- Type-safe backend wrapper
- API routes
- Data transforms

---

## 🎮 COMPONENT HIERARCHY

```
app/
├── layout.tsx (providers, theme)
├── page.tsx (landing)
└── simulation/
    ├── layout.tsx (simulation shell)
    ├── page.tsx (main view)
    ├── world/ (world map view)
    ├── agent/[id]/ (agent detail)
    ├── civilization/ (dashboard)
    ├── events/ (timeline)
    └── systems/ (10 panels)

components/
├── world/
│   ├── WorldCanvas.tsx ⭐
│   ├── AgentSprite.tsx
│   ├── TerritoryOverlay.tsx
│   └── BuildingMarkers.tsx
├── agents/
│   ├── AgentCard.tsx
│   ├── AgentDetailPanel.tsx ⭐
│   ├── PersonalityRadar.tsx
│   ├── AIThoughtBubble.tsx ⭐
│   └── RelationshipGraph.tsx
├── civilization/
│   ├── PopulationChart.tsx
│   ├── EconomicHealth.tsx
│   └── SystemCards.tsx
├── events/
│   ├── EventFeed.tsx
│   ├── EventCard.tsx
│   └── DramaticEventModal.tsx ⭐
├── systems/
│   ├── AgriculturePanel.tsx
│   ├── EconomyPanel.tsx
│   └── ... (10 panels)
└── ui/ (shadcn components)

hooks/
├── use-simulation-data.ts
├── use-simulation-websocket.ts ⭐
└── use-agent-detail.ts

lib/
├── simulation-client.ts ⭐
└── pixi-setup.ts
```

---

## 🔧 TECHNICAL PATTERNS

### State Management
```typescript
// Global UI state (Zustand)
interface UIState {
  currentView: 'world' | 'agents' | 'civilization'
  selectedAgentId: string | null
  cameraPosition: { x: number; y: number; zoom: number }
  isPaused: boolean
  playbackSpeed: 1 | 2 | 4 | 8
}

// Server state (React Query)
useQuery(['simulation'], fetchSimulation, {
  refetchInterval: 2000 // Fallback polling
})

// WebSocket updates
ws.onmessage = (msg) => {
  queryClient.setQueryData(['simulation'], msg.data)
}
```

### Performance Optimizations
- Sprite pools (reuse sprites)
- Off-screen culling (don't render invisible)
- LOD system (far = simple, near = detailed)
- Batch rendering (one draw call per layer)
- React.memo for expensive components
- Virtual scrolling for long lists

### Real-Time Flow
```
Backend (Python)
  ↓ WebSocket (2s intervals)
Next.js API Routes
  ↓ Transform data
React Query Cache
  ↓ Selectors
React Components
  ↓ Render
Pixi.js Canvas (60fps)
```

---

## 📱 RESPONSIVE STRATEGY

### Desktop First (Primary)
- Multi-panel layouts
- Large world canvas
- All features visible

### Tablet (768-1024px)
- 2-column layouts
- Smaller canvas
- Collapsible sidebars

### Mobile (< 768px)
- Single column
- Agent list instead of canvas
- Swipe navigation
- Simplified views

---

## ♿ ACCESSIBILITY

### Baseline
- Semantic HTML
- ARIA labels
- Keyboard navigation
- WCAG AA color contrast

### Enhanced
- High contrast mode
- Font size controls
- Reduced motion mode
- Screen reader friendly

---

## 📊 SUCCESS METRICS

### MVP Success
- ✅ Simulation runs without crash
- ✅ Agents visible and moving
- ✅ Users can click agents for details
- ✅ Real-time updates work
- ✅ "This is cool!" reaction

### Phase 2 Success
- ✅ "This is beautiful!" reaction
- ✅ Users share screenshots
- ✅ 5+ min average session

### Phase 3 Success
- ✅ 30+ min session time
- ✅ Daily return visits
- ✅ Users explore all systems

### Phase 4 Success
- ✅ "Best AI civilization viewer ever"
- ✅ Organic growth
- ✅ Community forming

---

## 🚦 NEXT STEPS

### 1. Environment Setup (30 min)
```bash
cd /Users/hackerman/neuronaut-world/neuronaut-world
npm install pixi.js pixi-viewport
npm install zustand @tanstack/react-query
npm install recharts d3
npm install framer-motion
npm install lucide-react
```

### 2. Create Core Files (Week 1)
Start with the 5 critical files:
1. WorldCanvas.tsx
2. use-simulation-websocket.ts
3. AgentDetailPanel.tsx
4. simulation/page.tsx
5. DramaticEventModal.tsx

### 3. Connect to Backend (Week 1)
- Test WebSocket connection
- Verify data structure matches
- Build simulation-client.ts

### 4. Build MVP Features (Week 1-2)
- Basic world rendering
- Agent sprites
- Click interactions
- Time controls

### 5. Iterate Based on Visual Impact (Week 2+)
- Add animations
- Refine UI
- Polish interactions
- Test with real backend data

---

## 💎 WHAT MAKES THIS EPIC

1. **Isometric Living World** - Not dots, not abstract, a beautiful civilization
2. **AI Transparency** - Show LLM reasoning (unique!)
3. **Dramatic Events** - Make emergent behavior cinematic
4. **Deep Exploration** - Click anything, understand everything
5. **Real-Time Storytelling** - Watch AI create stories as they unfold

---

## 🎯 THE VISION

Users open Neuronaut World and:
1. See a beautiful isometric world with tiny AI agents
2. Watch a tax revolt erupt → dramatic modal appears
3. Click the rebel leader → see her AI thoughts: *"Economic desperation drove me..."*
4. Explore her personality, relationships, goals
5. Zoom out to dashboard → see wealth inequality triggered it
6. Come back daily to see what happens next

**This is not "blue dots on a grid."**
**This is a window into an AI civilization.**

---

Ready to build? 🚀

Start with `WorldCanvas.tsx` and let's make this stunning.
