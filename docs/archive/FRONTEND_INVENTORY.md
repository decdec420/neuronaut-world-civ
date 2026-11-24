# Complete Next.js Frontend File Inventory & Integration Status

## Already Extracted ✅

### Types
- ✅ `types/structures.ts` → Copied to `web/types/structures.ts`
- ✅ `types/technology.ts` → Copied to `web/types/technology.ts`
- ✅ `types/view-modes.ts` → Copied to `web/types/view-modes.ts`

### Libraries
- ✅ `lib/construction-simulator.ts` → Copied to `web/lib/construction-simulator.ts`
- ✅ `lib/sprite-animator.ts` → Copied to `web/lib/sprite-animator.ts`
- ✅ `lib/sprite-manager.ts` → Copied to `web/lib/sprite-manager.ts`
- ✅ `lib/research-simulator.ts` → Copied to `web/lib/research-simulator.ts`

### Hooks
- ✅ `hooks/use-api-client.ts` → Copied to `web/hooks/use-api-client.ts`
- ✅ `hooks/use-simulation-websocket.ts` → Copied to `web/hooks/use-simulation-websocket.ts`
- ✅ `hooks/use-simulation-data.ts` → Copied to `web/hooks/use-simulation-data.ts`

### Vanilla JS Adaptations Created
- ✅ Created `web/lib/api-client.js` (non-React version)
- ✅ Created `web/lib/simulation-websocket.js` (non-React version)
- ✅ Created `web/lib/construction-manager.js` (non-React version)

---

## Missing - Needs Review 🔍

### lib/pixi-setup.ts
**Status**: ✅ EXTRACTED

```typescript
// PIXI.js v8 WebGL setup for high-performance world rendering
// Includes: viewport, isometric projection, sprite pooling, particle effects
```

**Decision**: ✅ Copied to `web/lib/pixi-setup.ts` for future WebGL rendering
**Current**: Main frontend uses Canvas 2D (`web/game_interface.js`)
**Future**: Can upgrade to WebGL using this file for better performance with 1000+ agents

### components/ (UI Components)
**Status**: NOT EXTRACTED (intentional - React-specific)

React components that are frontend-UI only:
- `components/agents/AgentDetailPanel.tsx` - Agent inspection UI
- `components/simulation/SimulationStats.tsx` - Stats display
- `components/simulation/TimeControls.tsx` - Play/pause/speed controls
- `components/technology/TechTreePanel.tsx` - Tech tree visualization
- `components/ui/*.tsx` - UI controls (filters, minimap, notifications, view modes)
- `components/world/*.tsx` - World canvas, sprites, day/night cycle

**Note**: These are pure UI. The main project has its own HTML/JS UI in `web/game_interface.html` and `web/game_interface.js`.

### app/ (Next.js App Router)
**Status**: NOT EXTRACTED (intentional - Next.js specific)

- `app/layout.tsx` - Next.js layout
- `app/page.tsx` - Landing page
- `app/providers.tsx` - React providers
- `app/simulation/page.tsx` - Main simulation page

**Note**: Next.js routing logic, not relevant to Python backend.

### src/ (Older Attempt?)
**Status**: NOT EXTRACTED (appears to be old/duplicate code)

- `src/app/` - Duplicate Next.js app
- `src/lib/pdf-reader*.ts` - PDF parsing utilities (not simulation-related)
- `src/lib/utils.ts` - Generic utils
- `src/middleware.ts` - Next.js middleware
- `src/contexts/user-context.tsx` - User auth context

**Note**: Seems like an older version or different feature set. Not core simulation logic.

### test-*.js
**Status**: NOT EXTRACTED (intentional - auth testing only)

- `test-auth.js`
- `test-auth-debug.js`
- `test-complete-flow.js`

**Note**: Authentication testing scripts, not relevant to main simulation.

---

## Integration with Python Backend ✅

### Building System
✅ **COMPLETED**: Added `ConstructionStage` enum to `world/buildings.py`
- Added stages: PLANNING → FOUNDATION → FRAMING → FINISHING → COMPLETED
- Updated `Building` dataclass with `construction_stage` field
- Added `get_construction_stage()` method
- Updated `to_dict()` to include stage for frontend
- Progress thresholds: 0% planning, >0% foundation, >25% framing, >60% finishing, 100% completed

### Technology System
🔄 **PENDING**: Python uses emergent tech discovery, TypeScript has fixed tech tree
- **Backend**: `world/tech_progression.py` - EMERGENT progression (Stone Age → Space Age)
- **Frontend**: `web/types/technology.ts` - FIXED tech tree with prerequisites

**Recommendation**: Keep Python emergent system, document it for frontend integration.

---

## Critical Missing File: lib/pixi-setup.ts

This file likely contains the WebGL/Canvas rendering setup. Let's check if we need it.

**Action Required**: Review `lib/pixi-setup.ts` before deleting `neuronaut-world/` directory.

---

## Summary

### Extracted & Integrated: 14 files

- 3 type definition files
- 5 simulation library files (including pixi-setup)
- 3 React hooks
- 3 vanilla JS adaptations

### Intentionally Not Extracted: 30+ files

- React UI components (main project has own UI)
- Next.js app router pages
- Auth/PDF utilities
- Test files

### Next Steps

1. ✅ Review `lib/pixi-setup.ts` - COMPLETED
2. ✅ Extracted PIXI.js setup for future WebGL rendering
3. ✅ Backend construction stages integrated
4. 🔄 **READY**: Remove `neuronaut-world/` directory
5. 🔄 **READY**: Final commit with all integration work

