# 🚀 Quick Start - Game Interface

## Launch in 3 Steps

### Option 1: Auto-Launch Script (Easiest!)

```bash
cd /path/to/neuronaut-world
./launch_game.sh
```

This will:
1. ✅ Start the server
2. ✅ Open your browser automatically
3. ✅ Take you straight to the game!

---

### Option 2: Manual Launch

```bash
# 1. Start the server
cd /path/to/neuronaut-world
python3 api/server.py

# 2. Open browser to:
http://localhost:8000/game
```

---

## What You'll See

### 🎮 Main Screen Layout

```
┌─────────────────────────────────────────────────────┐
│  🧠 NEURONAUT WORLD    [Stats] [Status] [Speed]     │ ← Top Bar
├─────┬─────────────────────────────────────────┬─────┤
│     │ 🌍 World  👥 Agents  🌳 Resources ...   │     │ ← Tabs
│ 🗺️  ├─────────────────────────────────────────┤ 📰 │
│Mini │                                           │Feed │
│Map  │        Main View Area                    │     │
│     │     (Changes based on tab)               │     │
│📊   │                                           │     │
│Stats│                                           │     │
│     │                                           │     │
└─────┴─────────────────────────────────────────┴─────┘
│         ⏸ PAUSE   1x  2x  4x  8x                    │ ← Speed
└──────────────────────────────────────────────────────┘
```

---

## 🎯 Quick Actions

### Explore the World
1. Click the **🌍 World** tab (should be active by default)
2. **Drag** to pan around
3. **Scroll** to zoom in/out
4. **Click any agent** to see their full details

### View All Agents
1. Click the **👥 Agents** tab
2. Scroll through the grid of agent cards
3. Click any card for detailed stats

### Check Resources
1. Click **🌳 Resources** tab
2. See what you've gathered

### See Tech Progress
1. Click **🔬 Tech Tree** tab
2. View unlocked vs locked technologies
3. See your era progression

### Read the Story
1. Click **📜 Story** tab
2. Read the AI-generated narrative of your civilization

---

## 🎮 Controls

### World View
| Action | Control |
|--------|---------|
| Pan camera | Left-click + drag |
| Zoom in/out | Scroll wheel |
| Select agent | Click on sprite |
| Close modal | Click outside or X button |

### Speed Control
| Button | Effect |
|--------|--------|
| ⏸ PAUSE | Stop simulation |
| 1x | Normal speed |
| 2x | 2x faster |
| 4x | 4x faster |
| 8x | 8x faster (fastest) |

---

## 🌟 Cool Things to Try

### 1. Follow an Agent's Journey
- Click an agent in World view
- Read their stats, personality, emotions
- Check their memories
- Watch them move around
- Close modal and click again later to see changes

### 2. Watch a Civilization Grow
- Start with World view
- Speed up to 4x or 8x
- Watch agents spread out
- See population increase
- Check Agents tab periodically

### 3. Track Economic Progress
- Go to **💰 Economy** tab
- Note the starting wealth
- Speed up simulation
- Watch wealth accumulate
- See who becomes richest!

### 4. Monitor the Activity Feed
- Watch right sidebar
- See births, deaths, events in real-time
- Different colors for different event types
- Tells the story as it happens

### 5. Zoom In Close
- In World view, scroll to zoom way in
- See agent names appear
- Watch facial expressions change
- See details of terrain tiles

---

## 📱 Interface Tips

### Left Sidebar
- **Mini-map**: Overview of whole world, shows all agents
- **Quick Stats**: Key numbers at a glance
- **Current Era**: Shows progression (Stone Age → Bronze Age → etc.)

### Main View
- **9 tabs** for different information
- Click tab to switch instantly
- Each view has specific purpose

### Right Sidebar
- **Activity Feed**: Real-time events
- Scrollable history
- Color-coded by importance

### Top Bar
- **Always visible** stats
- Connection status (green = connected)
- Current tick number (simulation time)

---

## 🐛 Troubleshooting

### "Can't connect to server"
```bash
# Make sure server is running:
python3 api/server.py

# Check it's responding:
curl http://localhost:8000/world
```

### "Page loads but no agents"
- Wait a few seconds for first update
- Check that simulation started (look for "Neuronaut World is running" in server logs)
- Refresh the page

### "World view is black"
- This is normal at first (dark space background)
- Wait for agents to spawn
- Try clicking Agents tab to verify data is loading

### "Can't see any agents in World view"
- Try zooming out (scroll down)
- Check camera position (might be looking at empty area)
- Look at mini-map to see where agents are

### "Simulation seems slow"
- Use speed controls at bottom
- Try 2x or 4x for faster gameplay
- Note: 1x is realistic time

---

## 🎨 Visual Guide

### Agent Sprite Colors
- **Blue** 👨 = Male
- **Pink** 👩 = Female
- **Purple** 🧑 = Non-binary

### Mood Indicators
- **Green glow** 😊 = Happy (mood > 0.3)
- **Yellow glow** 😐 = Neutral (mood -0.3 to 0.3)
- **Red glow** 😔 = Sad (mood < -0.3)

### Event Colors (Activity Feed)
- **Green border** = Birth 👶
- **Red border** = Death 💀
- **Orange border** = Conflict ⚔️
- **Blue border** = Trade 🤝
- **Purple border** = Building 🏗️

### Terrain Colors
- **Dark green** = Grass 🌱
- **Darker green** = Forest 🌲
- **Blue** = Water 💧
- **Grey** = Mountain ⛰️
- **Tan** = Desert 🏜️

---

## 🏆 Goals & Challenges

Try these objectives:

### Beginner
- [ ] Keep 5 agents alive for 100 ticks
- [ ] Reach $1000 total wealth
- [ ] Build 3 different building types
- [ ] Have at least one agent with 80%+ satisfaction

### Intermediate
- [ ] Grow population to 20 agents
- [ ] Reach Bronze Age
- [ ] Accumulate 10,000 total wealth
- [ ] Have zero conflicts for 50 ticks

### Advanced
- [ ] Sustain 50+ population
- [ ] Reach Iron Age or beyond
- [ ] Have wealthiest agent with $5000+
- [ ] Establish 2 separate civilizations
- [ ] Unlock 10+ technologies

### Expert
- [ ] Hit 100+ population
- [ ] Space Age technology
- [ ] $100,000 total wealth
- [ ] Multiple thriving civilizations
- [ ] Generate an epic 1000-word narrative

---

## 💡 Pro Tips

1. **Speed it up!** - Use 4x or 8x to see results faster
2. **Check agents often** - Their personalities evolve based on experiences
3. **Watch the feed** - Activity feed tells you what's important
4. **Use mini-map** - Quick way to see population distribution
5. **Compare eras** - Tech tree shows your civilization's progress
6. **Read the story** - Narrative tab captures epic moments
7. **Economy matters** - Wealth = survival = happiness
8. **Zoom for details** - Get close to see agent names and expressions
9. **Multiple tabs** - Don't just stay on World view, explore all views!
10. **Pause to study** - Hit pause when you want to examine things closely

---

## 📚 Learn More

- **Full features**: See `GAME_INTERFACE_README.md`
- **Visual design**: See `web/VISUAL_FEATURES.md`
- **AI autonomy**: See `AI_AUTONOMY_V2_FINAL_REPORT.md`
- **Quick reference**: See `V2_QUICK_REFERENCE.md`

---

## 🎉 Have Fun!

This is **your world**. The AI agents will:
- Make their own decisions
- Form relationships
- Build civilizations
- Create stories
- Surprise you!

Just **watch, explore, and enjoy** the emergent chaos! 🌍✨

---

**Ready? Let's go!**

```bash
./launch_game.sh
```

🚀🎮🧠
