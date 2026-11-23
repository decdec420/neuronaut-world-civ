# COMPLETE File-by-File Analysis: neuronaut-world/

## Summary Statistics
- **Total source files**: 105 files
- **Substantial files (>100 lines)**: 17 files
- **Empty/stub files**: 15 files
- **React UI components**: 12 files
- **Already extracted**: 10 files
- **Need to extract**: 7 files ⚠️

---

## ✅ ALREADY EXTRACTED (10 files)

### Types (3 files)
1. ✅ `types/structures.ts` (310 lines) → `web/types/structures.ts`
2. ✅ `types/technology.ts` (574 lines) → `web/types/technology.ts`
3. ✅ `types/view-modes.ts` (113 lines) → `web/types/view-modes.ts`

### Libraries (4 files)
4. ✅ `lib/construction-simulator.ts` (140 lines) → `web/lib/construction-simulator.ts`
5. ✅ `lib/sprite-animator.ts` (209 lines) → `web/lib/sprite-animator.ts`
6. ✅ `lib/sprite-manager.ts` (254 lines) → `web/lib/sprite-manager.ts`
7. ✅ `lib/research-simulator.ts` (262 lines) → `web/lib/research-simulator.ts`

### Hooks (3 files)
8. ✅ `hooks/use-api-client.ts` (1237 lines) → `web/hooks/use-api-client.ts`
9. ✅ `hooks/use-simulation-websocket.ts` (126 lines) → `web/hooks/use-simulation-websocket.ts`
10. ✅ `hooks/use-simulation-data.ts` (97 lines) → `web/hooks/use-simulation-data.ts`

---

## ⚠️ NEED TO EXTRACT (7 files)

### 1. lib/pixi-setup.ts (266 lines) 🔴 CRITICAL
**What it does**: PIXI.js WebGL rendering engine setup for world visualization

**Content**:
- `createPixiApp()` - Initialize PIXI v8 application
- `createViewport()` - Pan/zoom viewport with pixi-viewport
- Optimized rendering settings
- Isometric projection helpers
- Performance optimizations

**Status**: NOT EXTRACTED
**Decision**: EXTRACT - This is the core rendering engine
**Action**: Copy to `web/lib/pixi-setup.ts`

### 2. components/api-client-demo.tsx (743 lines) 🟡 VALUABLE
**What it does**: Complete demo of ALL 45 API endpoints with React Query

**Content**:
- Live examples of every API hook
- Best practices for API integration
- Shows data structure for each endpoint
- Error handling patterns
- Loading state management

**Status**: NOT EXTRACTED
**Decision**: EXTRACT - Excellent reference/documentation
**Action**: Copy to `web/components/api-client-demo.tsx` (or convert to vanilla JS demo page)

### 3. components/world/WorldCanvasSimple.tsx (1177 lines) 🟡 VALUABLE
**What it does**: Complete Canvas 2D world renderer with agents, buildings, animations

**Content**:
- Canvas-based world rendering (NOT WebGL)
- Agent sprite rendering with animations
- Building placement and visualization
- Pan/zoom controls
- Performance optimizations (throttling, culling)
- Day/night cycle integration
- Construction progress visualization

**Status**: NOT EXTRACTED
**Decision**: EXTRACT - This is similar to our existing `web/game_interface.js` but more advanced
**Action**: Review and extract useful patterns/algorithms

### 4. components/agents/AgentDetailPanel.tsx (489 lines) 🟢 USEFUL
**What it does**: Beautiful agent inspection UI with stats, visual indicators

**Content**:
- Wealth tier display (Poor → Elite)
- Health status visualization
- Age categories
- Life progress bars
- Animated effects
- Stat breakdowns

**Status**: NOT EXTRACTED
**Decision**: EXTRACT LOGIC (not React UI)
**Action**: Extract wealth/health/age tier algorithms to vanilla JS helpers

### 5. components/technology/TechTreePanel.tsx (370 lines) 🟢 USEFUL
**What it does**: Technology tree visualization with discovery status

**Content**:
- Era-based tech organization
- Tech status (discovered, researching, available, locked)
- Prerequisite checking
- Visual tech progression
- Research progress display

**Status**: NOT EXTRACTED
**Decision**: EXTRACT LOGIC (tech status algorithms)
**Action**: Extract tech status checking logic to vanilla JS

### 6. components/world/BuildingSprite.tsx (473 lines) 🟢 USEFUL
**What it does**: Building rendering with construction stages, health indicators

**Content**:
- Construction stage visualization
- Health bar rendering
- Production indicators
- Worker count display
- Animated effects

**Status**: NOT EXTRACTED
**Decision**: EXTRACT RENDERING LOGIC
**Action**: Extract building rendering algorithms

### 7. components/ui/FilterControlsPanel.tsx (299 lines) 🟢 USEFUL
**What it does**: Advanced filtering UI for agents/buildings

**Content**:
- Multi-criteria filtering
- Wealth range sliders
- Health filters
- Status toggles
- Search functionality

**Status**: NOT EXTRACTED
**Decision**: EXTRACT FILTER ALGORITHMS
**Action**: Extract filtering logic to vanilla JS

---

## 🚫 DO NOT EXTRACT (React UI Only)

### Next.js App Router (5 files)
- `app/layout.tsx` (22 lines) - Next.js layout
- `app/page.tsx` (91 lines) - Landing page
- `app/providers.tsx` (24 lines) - React providers  
- `app/simulation/page.tsx` (319 lines) - Main simulation page
- Next.js specific, not relevant

### UI Components (6 files)
- `components/simulation/SimulationStats.tsx` (48 lines)
- `components/simulation/TimeControls.tsx` (98 lines)
- `components/ui/ViewModeSelector.tsx` (98 lines)
- `components/ui/MiniMap.tsx` (201 lines)
- `components/ui/NotificationSystem.tsx` (239 lines)
- `components/world/DayNightCycle.tsx` (240 lines)
- Pure React UI, main project has own HTML/JS UI

### src/ Directory (Old/Unrelated Code)
All files in `src/` are either:
- Empty stub files (15+ files)
- Auth/dashboard UI (unrelated to simulation)
- PDF parsing utilities (not simulation)
- Supabase integration (not using this)

**Decision**: IGNORE entire `src/` directory

---

## 📋 EXTRACTION CHECKLIST

### High Priority (Must Extract Before Delete)
- [ ] 🔴 `lib/pixi-setup.ts` → Extract rendering engine setup
- [ ] 🟡 `components/world/WorldCanvasSimple.tsx` → Extract rendering algorithms
- [ ] 🟡 `components/api-client-demo.tsx` → Extract as reference/docs

### Medium Priority (Useful Algorithms)
- [ ] 🟢 `components/agents/AgentDetailPanel.tsx` → Extract tier/status algorithms
- [ ] 🟢 `components/technology/TechTreePanel.tsx` → Extract tech status logic
- [ ] 🟢 `components/world/BuildingSprite.tsx` → Extract building render logic
- [ ] 🟢 `components/ui/FilterControlsPanel.tsx` → Extract filter algorithms

### Optional (Reference Only)
- [ ] Review `components/world/WorldCanvas.tsx` (473 lines) - PIXI version
- [ ] Review other UI components for design patterns

---

## 🎯 ACTION PLAN

### Step 1: Extract Critical Files
```bash
# Copy PIXI setup
cp neuronaut-world/lib/pixi-setup.ts web/lib/pixi-setup.ts

# Copy API demo for reference
cp neuronaut-world/components/api-client-demo.tsx web/examples/api-client-demo.tsx
```

### Step 2: Extract Rendering Logic
- Read `WorldCanvasSimple.tsx`
- Extract useful algorithms (culling, throttling, sprite batching)
- Create `web/lib/rendering-utils.js` with vanilla JS versions

### Step 3: Extract Helper Algorithms
- Extract tier/status algorithms from `AgentDetailPanel.tsx`
- Create `web/lib/agent-helpers.js`
- Extract tech status logic from `TechTreePanel.tsx`
- Create `web/lib/tech-helpers.js`
- Extract filter logic from `FilterControlsPanel.tsx`
- Create `web/lib/filter-utils.js`

### Step 4: Document & Delete
- Update `INTEGRATION_SUMMARY.md` with all extracted files
- Create migration guide for rendering engine
- Delete `neuronaut-world/` directory

---

## 📊 File Categories

| Category | Count | Status |
|----------|-------|--------|
| Already Extracted | 10 | ✅ Done |
| Must Extract | 3 | ⚠️ Pending |
| Should Extract (algorithms) | 4 | 🟡 Pending |
| React UI Only | 11 | 🚫 Skip |
| Empty/Stub Files | 15+ | 🚫 Skip |
| Config Files | 10+ | 🚫 Skip |
| **TOTAL** | **53+** | **7 pending** |

---

## ⏰ Time Estimate
- Extract critical files: 10 minutes
- Extract algorithms: 30 minutes
- Test integration: 15 minutes
- Documentation: 10 minutes
- **TOTAL**: ~65 minutes

---

## 🚨 CRITICAL FINDING

The [`neuronaut-world/lib/pixi-setup.ts`](neuronaut-world/lib/pixi-setup.ts ) file contains the **WebGL rendering engine** that was NOT in our initial extraction. This is ESSENTIAL for high-performance world visualization!

**Must extract before deleting directory!**
