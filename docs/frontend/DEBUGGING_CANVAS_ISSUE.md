# 🔍 CANVAS RENDERING - DEBUGGING GUIDE

**Status**: Investigating empty canvas issue
**Date**: 2026-01-18

---

## ✅ FIXES APPLIED

### 1. SSR Error Fixed
- **Problem**: `window is not defined` during server-side rendering
- **Solution**: Used Next.js `dynamic()` import with `ssr: false`
- **File**: `app/simulation/page.tsx`
- **Status**: ✅ FIXED - No more 500 errors

### 2. Canvas Sizing Fixed
- **Problem**: Canvas might have 0 dimensions
- **Solution**:
  - Added `containerRef` to measure parent container
  - Set `minHeight: '500px'` fallback
  - Calculate dimensions from `getBoundingClientRect()`
- **File**: `components/world/WorldCanvas.tsx`
- **Status**: ✅ FIXED

### 3. Debug Logging Added
- Extensive console.log statements throughout initialization
- Logs canvas dimensions, layer counts, viewport bounds
- Error stack traces for debugging

---

## 🔍 HOW TO DEBUG IN BROWSER

### Open Browser Console
1. Open **http://localhost:3000/simulation**
2. Press `F12` or `Right-click → Inspect`
3. Go to **Console** tab
4. Look for messages starting with `[WorldCanvas]`

### Expected Console Output

If everything is working, you should see:
```
[WorldCanvas] Starting initialization...
[WorldCanvas] Container dimensions: { actualWidth: 1200, actualHeight: 800 }
[WorldCanvas] Pixi app created: Application {...}
[WorldCanvas] Viewport created: Viewport {...}
[WorldCanvas] Background layer added, children: 52  (50 stars + 2 glows + bg)
[WorldCanvas] Terrain layer added, children: 2  (base + highlights)
[WorldCanvas] Shadow layer added
[WorldCanvas] Agent layer added
[WorldCanvas] Effects layer added
[WorldCanvas] Total viewport children: 5
[WorldCanvas] Viewport bounds: Rectangle {...}
[WorldCanvas] Initialization complete!
```

### Common Issues to Look For

#### Issue 1: No Console Output
**Symptom**: No `[WorldCanvas]` messages at all
**Meaning**: Component not mounting
**Check**:
- Is "Loading World Canvas..." message showing?
- Any React errors in console?

#### Issue 2: Initialization Starts But Fails
**Symptom**: Starts logging then stops with error
**Meaning**: Pixi.js initialization failed
**Check**:
- Error messages after `[WorldCanvas] Starting initialization...`
- WebGL support issues

#### Issue 3: "Background layer added, children: 0"
**Symptom**: Layers are empty
**Meaning**: Rendering functions not working
**Check**:
- Math errors in isometric calculations
- PIXI Graphics API issues

#### Issue 4: Canvas has 0 dimensions
**Symptom**: `Container dimensions: { actualWidth: 100, actualHeight: 100 }`
**Meaning**: Container collapsed
**Check**:
- Parent flex layout
- CSS height issues

---

## 🎯 CURRENT ARCHITECTURE

### Component Loading Flow
```
app/simulation/page.tsx
  ↓ (dynamic import, ssr: false)
components/world/WorldCanvas.tsx
  ↓ (imports)
lib/pixi-setup.ts (Pixi.js utilities)
```

### Rendering Layers (bottom → top)
1. **Background Layer**: Radial gradient + 50 stars
2. **Terrain Layer**: Isometric tiles (base + highlights)
3. **Shadow Layer**: Agent shadows
4. **Agent Layer**: Animated sprites
5. **Effects Layer**: Particles (future)

### Initialization Steps
1. Get container dimensions
2. Create Pixi.js app
3. Create viewport (pan/zoom)
4. Render background layer
5. Render terrain layer
6. Create shadow layer
7. Create agent layer
8. Create effects layer
9. Start animation loop

---

## 🐛 POSSIBLE ISSUES

### WebGL Not Available
**Symptom**: Black canvas or error about WebGL
**Solution**: Pixi.js will fallback to Canvas2D, but check browser support

**Test WebGL**:
```javascript
// In browser console:
const canvas = document.createElement('canvas');
const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
console.log('WebGL supported:', !!gl);
```

### Pixi.js Version Mismatch
**Current**: v8.15.0
**Issue**: API changed significantly in v8
**Check**: package.json should show `"pixi.js": "^8.15.0"`

### Canvas Not Attached to DOM
**Symptom**: Canvas element exists but is not visible
**Check**:
- Canvas parent has proper dimensions
- Canvas is not hidden by CSS
- Z-index issues

### Viewport Not Showing Content
**Symptom**: Layers added but nothing visible
**Check**:
- Viewport position/zoom
- World bounds calculation
- Camera position

---

## 🔧 QUICK TESTS

### Test 1: Check Canvas Element
```javascript
// In browser console:
const canvas = document.querySelector('canvas');
console.log('Canvas found:', !!canvas);
console.log('Canvas dimensions:', {
  width: canvas.width,
  height: canvas.height,
  clientWidth: canvas.clientWidth,
  clientHeight: canvas.clientHeight
});
```

### Test 2: Check Pixi App
```javascript
// Should see a Pixi Application on window if exposed
console.log('Pixi app:', window.PIXI);
```

### Test 3: Check Container
```javascript
const container = document.querySelector('[class*="glass-panel"]');
const rect = container.getBoundingClientRect();
console.log('Container rect:', rect);
```

---

## 📊 WHAT SHOULD BE VISIBLE

If rendering correctly, you should see:
- **Dark background** with radial gradient (purple-blue glow)
- **50 small purple dots** (stars) scattered across background
- **Green isometric tiles** forming a grid pattern
- **5 large glowing circles** (agents: Alice, Bob, Charlie, Diana, Eve)
  - Each with name label
  - Health-based color (green/yellow/red)
  - Floating gently
  - Pulsing slightly
- **Shadows** under each agent (ellipse)
- **Gold rings** around wealthy agents (Bob, Diana)

### Visual Scale
- World: 100x100 units
- Tile size: 128x64 px (isometric)
- Agent size: 24px radius (with 36px glow)
- Total rendered area: ~12,800 x 6,400 px (zoomed out to 0.8x)

---

## ⚡ NEXT STEPS IF STILL BROKEN

1. **Check Browser Console**
   - Look for `[WorldCanvas]` logs
   - Check for errors
   - Verify dimensions are not 0

2. **Verify Pixi.js Loaded**
   - Should see "Pixi app created" log
   - No errors about PIXI being undefined

3. **Test Simpler Canvas**
   - Comment out background/terrain layers
   - Just try to render one circle
   - Verify Pixi basics work

4. **Check CSS Conflicts**
   - Canvas might be hidden
   - Z-index issues
   - Overflow clipping

5. **Try Forcing Dimensions**
   - Hardcode canvas width/height
   - Remove dynamic sizing
   - Rule out sizing issues

---

## 📝 CONSOLE COMMAND FOR USER

**Please open browser console (F12) and paste this:**

```javascript
// Diagnostic script
console.log('=== NEURONAUT WORLD DIAGNOSTIC ===');
const canvas = document.querySelector('canvas');
console.log('Canvas exists:', !!canvas);
if (canvas) {
  console.log('Canvas size:', {
    width: canvas.width,
    height: canvas.height,
    style: canvas.style.width + ' x ' + canvas.style.height
  });
}
const container = document.querySelector('[class*="relative w-full h-full"]');
console.log('Container exists:', !!container);
if (container) {
  const rect = container.getBoundingClientRect();
  console.log('Container rect:', rect);
}
console.log('Look for [WorldCanvas] initialization logs above');
```

**Then share the output!**

---

## 🎯 STATUS

- ✅ SSR errors fixed
- ✅ Canvas sizing logic updated
- ✅ Debug logging added
- ✅ Code compiling successfully
- ⏳ Waiting for browser console output to diagnose

**Ready to debug!** 🔍
