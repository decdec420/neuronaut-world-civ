# Next.js Frontend - Complete Extraction Verification

## Files We've Already Extracted

### ✅ Types (from neuronaut-world/types/)
- ✅ `structures.ts` → copied to `web/types/structures.ts`
- ✅ `technology.ts` → copied to `web/types/technology.ts`
- ✅ `view-modes.ts` → copied to `web/types/view-modes.ts`

### ✅ Hooks (from neuronaut-world/hooks/)
- ✅ `use-api-client.ts` → copied to `web/hooks/use-api-client.ts`
- ✅ `use-simulation-data.ts` → copied to `web/hooks/use-simulation-data.ts`
- ✅ `use-simulation-websocket.ts` → copied to `web/hooks/use-simulation-websocket.ts`

### ✅ Simulation Libraries (from neuronaut-world/lib/)
- ✅ `construction-simulator.ts` → copied to `web/lib/construction-simulator.ts`
- ✅ `research-simulator.ts` → copied to `web/lib/research-simulator.ts`
- ✅ `sprite-animator.ts` → copied to `web/lib/sprite-animator.ts`
- ✅ `sprite-manager.ts` → copied to `web/lib/sprite-manager.ts`
- ❌ `pixi-setup.ts` → NOT YET COPIED (needs review)

### ✅ Vanilla JS Versions Created
- ✅ `web/lib/api-client.js` - Vanilla JS version of use-api-client
- ✅ `web/lib/simulation-websocket.js` - Vanilla JS version of use-simulation-websocket
- ✅ `web/lib/construction-manager.js` - Vanilla JS version of construction-simulator

## Files to Review Before Deletion

### 🔍 pixi-setup.ts
**Location**: `neuronaut-world/lib/pixi-setup.ts`
**Purpose**: PIXI.js initialization and viewport setup
**Decision needed**: Should we copy this? The main web/ frontend doesn't use PIXI.js currently.
**Size**: 267 lines

### ❌ Not Needed (React/Next.js UI Components)
All files in:
- `app/` - Next.js app router pages
- `components/` - React UI components
- `src/app/` - More Next.js pages
- `src/components/` - More React components
- `src/lib/ai/` - Supabase AI integration (not relevant to Python backend)
- `src/lib/supabase/` - Supabase client (not relevant to Python backend)
- `src/lib/analytics/`, `collaboration/`, `hyperfocus/`, `notifications/` - All Supabase-related

### ❌ Not Needed (Configuration)
- `package.json`, `package-lock.json` - Node.js dependencies
- `tsconfig.json` - TypeScript config
- `tailwind.config.ts` - Tailwind CSS config
- `next.config.ts` - Next.js config
- `eslint.config.mjs` - ESLint config

### ❌ Not Needed (Tests/Scripts)
- All `__tests__/` files - React component tests
- `test-auth*.js` - Authentication tests for Supabase
- `scripts/extract-pdfs.ts` - PDF extraction (already have in root)
- `debug-pdf.ts` - PDF debugging

### ❌ Not Needed (Documentation)
- `README.md` - Next.js project readme
- Various `.md` files - Next.js project documentation

## Recommendation

### Files to Copy Now:
1. ❓ `lib/pixi-setup.ts` - Only if we plan to use PIXI.js in the main frontend

### Safe to Delete:
Everything else in `neuronaut-world/` directory because:
- All simulation logic and types have been extracted
- All React UI components are not needed (we have our own 12-tab HTML/JS UI)
- All Supabase/auth code is not relevant (Python backend handles this)
- All configuration files are Next.js-specific

## Final Check Commands

```bash
# Compare what we have vs what's in neuronaut-world
diff -r web/types/ neuronaut-world/types/
diff -r web/hooks/ neuronaut-world/hooks/

# List only simulation-related lib files
ls -la neuronaut-world/lib/
ls -la web/lib/
```

## Decision Point

**Should we copy pixi-setup.ts?**
- ✅ YES if: We plan to use PIXI.js for rendering in the main frontend
- ❌ NO if: We stick with the current canvas/rendering approach

**Current frontend rendering**: The main `web/` uses HTML canvas without PIXI.js library.
