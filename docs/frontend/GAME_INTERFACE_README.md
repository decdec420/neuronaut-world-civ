# 🎮 Neuronaut World - 2D Game Interface

## COOL AS SHIT Features! ✨

Your new game-style interface with **9 TABS** of pure visual goodness:

### 🌍 **World Tab**
- **2D tile-based map** with terrain (grass, forest, water, mountains)
- **Sprite-based agents** - colored circles with faces that show mood
- **Pan and zoom** - drag to move, scroll to zoom
- **Click agents** for detailed stats
- **Mini-map** in sidebar showing all agents
- **Resource nodes** (trees, rocks, food) visible on map
- **Buildings** rendered as structures
- **Smooth animations** and glowing effects

### 👥 **Agents Tab**
- **Card-based grid** of all agents
- **Agent avatars** with mood indicators (happy/neutral/sad)
- **Health, Energy, Satisfaction, Wealth bars** for each agent
- **Current role** (Hunter, Builder, Explorer, etc.)
- **Click any card** to see FULL details

### 🌳 **Resources Tab**
- **Visual grid** of all resources (Wood, Stone, Food, Gold, Iron, Water)
- **Icons and quantities** for each resource type
- **Real-time updates** as resources are gathered

### 🏛️ **Buildings Tab**
- **All structures** in your civilization (Homes, Farms, Workshops, Markets, Libraries)
- **Building counts** and icons
- **Quick overview** of infrastructure

### 🔬 **Tech Tree Tab**
- **Era-based progression** (Stone Age → Bronze Age → Iron Age → Space Age)
- **Technology nodes** with unlock status
- **Visual tech tree** showing dependencies
- **Unlocked vs Locked** states with different styles

### 🏰 **Civilizations Tab**
- **Multi-civ overview** when you have multiple civilizations
- **Stats for each civ**: Population, Wealth, Territory %, Technology Level, Military Power
- **Diplomatic relations** (when implemented)
- **Cultural info** and era status

### 💰 **Economy Tab**
- **Total wealth** across all agents
- **Average wealth** per person
- **Wealthiest agent** and their fortune
- **Poorest agent** stats
- **Economic inequality** visualization

### ⚔️ **Conflicts Tab**
- **All battles and conflicts** in chronological order
- **Conflict details**: who fought, outcome, casualties
- **Peace status** when no conflicts

### 📜 **Story/Narrative Tab**
- **Epic narrative** of your civilization's journey
- **AI-generated stories** from the Civilization Narrator
- **Major events** written as dramatic prose
- **Era transitions** and legendary moments

## How to Access

1. **Start the server:**
   ```bash
   cd /path/to/neuronaut-world
   python api/server.py
   ```

2. **Open in browser:**
   ```
   http://localhost:8000/game
   ```

3. **Alternative URLs:**
   - Classic interface: `http://localhost:8000/app/classic`
   - Enhanced interface: `http://localhost:8000/app`
   - NEW Game interface: `http://localhost:8000/game` ← **USE THIS ONE!**

## Visual Style

### Color Scheme
- **Dark background**: Deep space blues (#0a0e1a, #141824)
- **Gold accents**: (#fbbf24) for highlights and important info
- **Purple gradients**: (#667eea, #764ba2) for headers
- **Status colors**:
  - 🟢 Green (#4ade80) = happy/healthy
  - 🟡 Yellow (#fbbf24) = neutral
  - 🔴 Red (#f87171) = sad/danger

### Agent Sprites
- **Males**: Blue circles 👨
- **Females**: Pink circles 👩
- **Non-binary**: Purple circles 🧑
- **Faces change** based on mood (smile/frown)
- **Glow effects** around agents
- **Name labels** when zoomed in

### World Rendering
- **32px tiles** for retro pixel-art feel
- **Procedural terrain** with color variations
- **Resource nodes** (🌲 🪨 🌾)
- **Buildings** as colored structures
- **Grid overlay** for that strategy game feel

## Controls

### World View
- **🖱️ Left-click + drag**: Pan camera
- **🔍 Scroll wheel**: Zoom in/out (30% - 300%)
- **👆 Click agent**: Open detailed stats modal
- **Mini-map**: Click to jump to location (when implemented)

### Speed Controls (Bottom Bar)
- **⏸ PAUSE**: Stop simulation
- **1x / 2x / 4x / 8x**: Change simulation speed
- Real-time speed display

### Navigation
- **Top tabs**: Switch between different views
- **Active tab**: Highlighted in gold
- **Smooth transitions** between views

## What Makes It COOL AS SHIT

1. **Pixel-perfect 2D rendering** like classic civ games
2. **Multiple information layers** - pick what you want to see
3. **Real-time updates** via WebSocket (updates every 2 seconds)
4. **Smooth animations** - zoom, pan, agent movement trails
5. **Rich tooltips** on hover
6. **Detailed modals** for deep dives into agents
7. **Professional game UI** with sidebars, mini-map, activity feed
8. **Responsive design** that works on different screen sizes
9. **Visual feedback** everywhere (hover effects, transitions, glows)
10. **Epic color scheme** that screams "this is a GAME!"

## Extending the Interface

Want to add more views? Here's how:

1. **Add a new tab** in the HTML:
   ```html
   <button class="tab" data-tab="yourview">
       <span class="tab-icon">🎯</span>
       <span>Your View</span>
   </button>
   ```

2. **Add a panel**:
   ```html
   <div class="tab-panel" id="panel-yourview">
       <!-- Your content -->
   </div>
   ```

3. **Add render function** in JavaScript:
   ```javascript
   function renderYourView() {
       // Your rendering code
   }
   ```

4. **Add to switch statement**:
   ```javascript
   case 'yourview':
       renderYourView();
       break;
   ```

## Performance

- **Canvas rendering**: 60 FPS for smooth animations
- **Efficient updates**: Only redraws when data changes
- **Lazy rendering**: Tabs only render when active
- **Optimized WebSocket**: 2-second update interval (configurable)

## Future Enhancements

Potential additions:
- 🎵 **Sound effects** for births, deaths, conflicts
- 🎨 **Custom agent sprites** (not just circles)
- 🗺️ **Clickable mini-map** to jump to locations
- 📊 **Charts and graphs** for economy/population over time
- 🎭 **Agent relationships** visualized as network graph
- 🏗️ **Building placement** - click to build on map
- 🌊 **Animated terrain** (water flowing, trees swaying)
- ⚡ **Particle effects** for special events
- 📷 **Screenshot capture** to save epic moments
- 🎬 **Replay mode** to watch history unfold

## Comparison to Original

| Feature | Original (`/app/classic`) | NEW Game Interface (`/game`) |
|---------|---------------------------|------------------------------|
| World view | Single canvas | Canvas + 8 additional tabs |
| Agent display | Dots | Sprites with faces |
| Terrain | Gradient background | Tile-based with types |
| Navigation | Limited | Full pan/zoom |
| Stats | Left sidebar only | Multiple dedicated views |
| Resources | Not shown | Full resource tab |
| Tech tree | Not shown | Interactive tech tree |
| Civilizations | Not shown | Dedicated civ tab |
| Economy | Basic stats | Full economy breakdown |
| Conflicts | Event feed | Dedicated conflicts tab |
| Narrative | Not shown | Epic story tab |
| Visual style | Clean/minimal | Game-like/rich |

## Enjoy Your New Game Interface! 🚀

This is what you wanted - **COOL AS SHIT** visuals that rival Pokemon and Civ games, but perfectly suited for a web-based AI civilization simulator!

Now sit back, zoom in, click around, and watch your AI civilization THRIVE! 🌍✨
