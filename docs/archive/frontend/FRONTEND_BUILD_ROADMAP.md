# 🗺️ FRONTEND BUILD ROADMAP
**Step-by-step guide to build the epic visualization**

---

## 🎯 WEEK 1: MVP - WATCHABLE CIVILIZATION

### Day 1: Setup & Foundation
- [ ] Install dependencies
  ```bash
  cd neuronaut-world
  npm install pixi.js pixi-viewport
  npm install zustand @tanstack/react-query
  npm install framer-motion
  ```
- [ ] Create folder structure
  ```
  src/
  ├── components/world/
  ├── components/agents/
  ├── components/simulation/
  ├── hooks/
  └── lib/
  ```
- [ ] Configure Tailwind for custom colors (already done ✅)
- [ ] Test Next.js dev server: `npm run dev`

### Day 2: Basic World Canvas
- [ ] Create `WorldCanvas.tsx`
  - Initialize Pixi.js application
  - Add viewport for pan/zoom
  - Render simple grid
  - Test in browser
- [ ] Create `pixi-setup.ts` helper
  - Reusable Pixi config
  - Canvas initialization
  - Viewport configuration

### Day 3: WebSocket Integration
- [ ] Create `use-simulation-websocket.ts`
  - Connect to `ws://localhost:8000/ws`
  - Handle messages
  - Auto-reconnect on disconnect
- [ ] Create `use-simulation-data.ts`
  - React Query setup
  - Fetch `/api/simulation/state`
  - Combine with WebSocket updates
- [ ] Test with running Python backend

### Day 4: Render Agents (Simple)
- [ ] Get agent data from backend
- [ ] Render agents as colored circles (temporary)
- [ ] Add agent labels (name above circle)
- [ ] Implement smooth movement interpolation
  - Backend sends position every 2s
  - Frontend interpolates at 60fps
- [ ] Add click handler (log to console)

### Day 5: Agent Detail Panel
- [ ] Create `AgentDetailPanel.tsx`
  - Basic layout with agent info
  - Personality bars
  - Needs display
  - Recent actions list
- [ ] Create slide-in animation (from right)
- [ ] Wire to WorldCanvas click event
- [ ] Test with multiple agents

### Day 6: Time Controls & Dashboard
- [ ] Create `TimeControls.tsx`
  - Play/pause button
  - Speed selector (1x, 2x, 4x)
  - Current tick display
- [ ] Create `SimulationStats.tsx`
  - Population count
  - Current era
  - Alive agents
- [ ] Create main layout in `simulation/page.tsx`
  - WorldCanvas (center)
  - AgentDetailPanel (right, conditional)
  - TimeControls (bottom)
  - Stats (top right)

### Day 7: Polish & Test MVP
- [ ] Add loading states
- [ ] Add error handling
- [ ] Test with 50+ agents
- [ ] Fix any performance issues
- [ ] Test on different screen sizes
- [ ] **CHECKPOINT: Can you watch agents move and click for details?**

---

## 🎨 WEEK 2: BEAUTIFUL VISUALIZATION

### Day 8: Upgrade to Isometric
- [ ] Create isometric coordinate converter
  ```typescript
  const toIsometric = (x, y) => ({
    x: (x - y) * 32,
    y: (x + y) * 16
  })
  ```
- [ ] Update agent positions to isometric
- [ ] Add terrain texture (grass)
- [ ] Test visual improvement

### Day 9: Agent Sprites
- [ ] Find/create sprite sheets (32x32px)
  - Option 1: Free assets from itch.io
  - Option 2: Generate with AI (Midjourney/DALL-E)
  - Option 3: Use simple colored shapes as placeholders
- [ ] Create `AgentSprite.tsx`
  - Load sprite textures
  - Implement walk animation (4 frames)
  - Add status glow (colored circle beneath)
- [ ] Replace circles with sprites

### Day 10: Buildings & Territories
- [ ] Create `BuildingMarkers.tsx`
  - Render buildings from backend data
  - Isometric building sprites (houses, temples, markets)
  - Click handler for building info
- [ ] Create `TerritoryOverlay.tsx`
  - Colored zones from territory data
  - Blur at borders
  - Semi-transparent overlay

### Day 11: UI Polish - Glass Morphism
- [ ] Update `AgentDetailPanel.tsx` styling
  - Glass morphism effect
  - Blur backdrop
  - Gradient borders
  - Smooth transitions
- [ ] Create `Card` component (reusable)
  - Glass morphism base style
  - Variants for different contexts
- [ ] Update `TimeControls.tsx` with new style

### Day 12: Event System - Basic
- [ ] Create `EventFeed.tsx`
  - Connect to backend events
  - Display last 20 events
  - Auto-scroll to newest
- [ ] Create `EventCard.tsx`
  - Styled event display
  - Icon based on event type
  - Timestamp
  - Agent links

### Day 13: Data Visualizations
- [ ] Install Recharts: `npm install recharts`
- [ ] Create `PopulationChart.tsx`
  - Line chart of population over time
  - Data from backend history
- [ ] Create `PersonalityRadar.tsx` for agent detail
  - Radar chart showing personality traits
  - D3.js or Recharts
- [ ] Create `NeedsBarChart.tsx`
  - Horizontal bars for needs urgency

### Day 14: Polish & Performance
- [ ] Optimize sprite rendering
  - Sprite pools
  - Batch rendering
  - Off-screen culling
- [ ] Add particle effects for resources
  - PIXI.ParticleContainer
  - Simple glow particles
- [ ] Test with 100+ agents
- [ ] **CHECKPOINT: Does it look visually stunning?**

---

## 📊 WEEK 3: DEEP ENGAGEMENT

### Day 15: Civilization Dashboard
- [ ] Create `civilization/page.tsx`
- [ ] Create `CivilizationMetrics.tsx`
  - GDP, population, era display
  - Economic health gauge
  - Technology progress bar
- [ ] Create `SystemCards.tsx`
  - Grid of 10 system cards
  - Traffic light status
  - Click to expand

### Day 16: System Deep Dive Panels
- [ ] Create base `SystemPanel.tsx` component
- [ ] Create `AgriculturePanel.tsx`
  - Farm list
  - Food production chart
  - Season display
- [ ] Create `EconomyPanel.tsx`
  - Banks list
  - Wealth distribution chart
  - Active trade routes
- [ ] Test navigation between systems

### Day 17: Enhanced Agent View
- [ ] Add `AIThoughtBubble.tsx` to agent panel
  - Show LLM reasoning from backend
  - Factor influence visualization
  - Warnings display
- [ ] Add `RelationshipGraph.tsx`
  - D3.js network graph
  - Click node to navigate
- [ ] Add `GoalsProgress.tsx`
  - Goal list with progress bars
  - Strategy display

### Day 18: Dramatic Events
- [ ] Create `DramaticEventModal.tsx`
  - Full-screen modal
  - Animated entrance (Framer Motion)
  - Breaking news style
  - Color-coded by event type
- [ ] Wire to WebSocket major events
  - Auto-trigger on MAJOR importance
  - Queue if multiple events
- [ ] Add "View on Map" functionality
  - Pan/zoom to event location

### Day 19: Search & Filters
- [ ] Add search bar to agent list
  - Filter by name
  - Filter by role
  - Filter by wealth range
- [ ] Add event filtering
  - Category checkboxes
  - Date range selector
- [ ] Add system filtering on dashboard
  - Show/hide specific systems
  - Sort by status

### Day 20: Narrative Features
- [ ] Create "Story of the Day" widget
  - Auto-summarize top 3 events
  - LLM-generated narrative (optional)
- [ ] Add achievement display
  - Track from backend achievement system
  - Toast notifications
- [ ] Create dynasty/family tree view
  - D3.js tree layout
  - Click to see family members

### Day 21: Testing & Polish
- [ ] User testing with friends/family
- [ ] Fix bugs found
- [ ] Performance optimization
- [ ] Mobile responsiveness check
- [ ] **CHECKPOINT: Can users engage deeply for 30+ min?**

---

## ⚡ WEEK 4+: ADVANCED FEATURES

### Optional Enhancements (As Time Permits)

#### Time Travel
- [ ] Create timeline scrubber
- [ ] Backend endpoint for historical state
- [ ] Replay animation
- [ ] "On this day" feature

#### Mobile Optimization
- [ ] Responsive breakpoints
- [ ] Touch gestures for pan/zoom
- [ ] Simplified mobile views
- [ ] Bottom sheet for agent details

#### Advanced Visualizations
- [ ] Heatmaps (population density)
- [ ] Flow diagrams (trade routes animated)
- [ ] Cultural diffusion maps
- [ ] Tech tree visualization

#### Interactive Features
- [ ] Create custom agent (if backend supports)
- [ ] Follow agent camera mode
- [ ] Screenshot/share functionality
- [ ] Export civilization report

---

## ✅ CRITICAL PATH (Minimum for Launch)

**Must Have**:
1. ✅ World canvas with agent sprites
2. ✅ Agent detail panel (basic)
3. ✅ Time controls
4. ✅ Event feed
5. ✅ WebSocket real-time updates

**Should Have** (for "beautiful"):
6. ✅ Isometric view
7. ✅ Glass morphism UI
8. ✅ Animated sprites
9. ✅ Dramatic event modals
10. ✅ Basic charts

**Nice to Have** (post-launch):
11. System panels (all 10)
12. Advanced graphs
13. Search/filters
14. Time travel
15. Mobile optimization

---

## 🎯 DECISION POINTS

### Sprint 1 (Week 1) Decision: Ship or Continue?
**Question**: Is MVP watchable and interesting?
- **YES** → Continue to Week 2 (beautify)
- **NO** → Debug issues, improve core experience

### Sprint 2 (Week 2) Decision: Ship or Polish?
**Question**: Is it visually stunning?
- **YES** → Ship to early testers
- **NO** → Polish visuals one more week

### Sprint 3 (Week 3) Decision: Features or Feedback?
**Question**: Do testers want more features or refinement?
- **FEATURES** → Build Week 3 scope
- **REFINEMENT** → Fix bugs, optimize performance

---

## 📦 DEPENDENCIES CHECKLIST

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "pixi.js": "^7.3.0",
    "pixi-viewport": "^5.0.0",
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.0.0",
    "recharts": "^2.10.0",
    "d3": "^7.8.0",
    "framer-motion": "^10.16.0",
    "lucide-react": "^0.294.0",
    "tailwindcss": "^3.3.0",
    "@radix-ui/react-*": "latest" (for Shadcn)
  }
}
```

---

## 🐛 COMMON PITFALLS TO AVOID

1. **Don't** build all 10 system panels at once → Start with 2-3
2. **Don't** optimize prematurely → Make it work, then make it fast
3. **Don't** add features before MVP → Ship something watchable first
4. **Don't** forget WebSocket reconnect → Users will lose connection
5. **Don't** render everything at once → Virtual scrolling for long lists
6. **Don't** skip mobile breakpoints → At least make it viewable
7. **Don't** ignore loading states → Show skeletons, not blank screens

---

## 🎉 SUCCESS CRITERIA

### Week 1 Success
- [ ] Can start simulation
- [ ] Can see agents moving
- [ ] Can click agent and see details
- [ ] Real-time updates work
- [ ] No crashes for 10+ minutes

### Week 2 Success
- [ ] Looks beautiful (isometric, sprites)
- [ ] UI is polished (glass morphism)
- [ ] Animations are smooth
- [ ] Friends say "wow!"
- [ ] Shareworthy screenshots

### Week 3 Success
- [ ] Users explore for 30+ min
- [ ] All 10 systems visible
- [ ] Events are dramatic
- [ ] AI thoughts visible
- [ ] Daily return visits

### Launch Success
- [ ] 100+ concurrent agents without lag
- [ ] No WebSocket disconnects
- [ ] Mobile viewable (even if not optimal)
- [ ] Users understand "watching vs controlling"
- [ ] At least 3 emergent events occur in demo

---

## 📊 METRICS TO TRACK

### Technical
- FPS (target: 60fps with 100 agents)
- WebSocket latency (target: <100ms)
- Bundle size (target: <500KB initial)
- Time to interactive (target: <3s)

### User Engagement
- Average session time
- Agent clicks per session
- Events viewed per session
- Return visits (day 2, day 7)
- Screenshot shares

---

## 🚀 READY TO START?

**Phase 1 Starting Point**:
```bash
cd /Users/hackerman/neuronaut-world/neuronaut-world
npm install pixi.js pixi-viewport zustand @tanstack/react-query
mkdir -p src/components/{world,agents,simulation}
mkdir -p src/{hooks,lib}
touch src/components/world/WorldCanvas.tsx
code src/components/world/WorldCanvas.tsx
```

**First File to Create**: `WorldCanvas.tsx`
**First Goal**: See a black canvas with a colored circle that represents an agent

**Then**: Build up from there, one component at a time.

---

**You've got this!** 🎯

The backend is solid. The architecture is planned.
Now it's time to make pixels dance.

Start with WorldCanvas.tsx and let's build something epic.
