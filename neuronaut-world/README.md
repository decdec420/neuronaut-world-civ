# Neuronaut World - Frontend

Epic visualization for autonomous AI civilizations.

## 🚀 Quick Start

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the landing page.
Open [http://localhost:3000/simulation](http://localhost:3000/simulation) to see the simulation viewer.

### Environment Variables

Copy `.env.example` to `.env.local` and configure:

```bash
cp .env.example .env.local
```

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_WS_URL` - WebSocket URL (default: ws://localhost:8000/ws)

## 🎨 Features

### Current (MVP Phase 1)

- ✅ Isometric world canvas with Pixi.js
- ✅ Animated agent sprites with smooth interpolation
- ✅ Pan/zoom controls
- ✅ Agent detail panel (glass morphism UI)
- ✅ Time controls (play/pause, speed)
- ✅ WebSocket real-time updates
- ✅ Simulation stats dashboard

### Coming Soon (Phase 2)

- 🎨 Enhanced agent sprites with walk animations
- 🎨 Building landmarks
- 🎨 Territory overlays
- 🎨 Particle effects for resources
- 🎨 Dramatic event modals
- 📊 Population charts
- 📊 Economic visualizations

### Future (Phase 3+)

- 🔬 AI thought bubbles (show LLM reasoning)
- 🌐 Relationship network graphs
- 📈 System deep dive panels (all 10 systems)
- ⚡ Time travel / replay
- 📱 Mobile optimization

## 🏗️ Architecture

Built with:

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Pixi.js** - GPU-accelerated 2D rendering
- **Zustand** - Lightweight state management
- **React Query** - Server state management
- **Framer Motion** - Animations
- **Recharts** - Data visualization

## 📂 Project Structure

```
app/
├── layout.tsx          # Root layout
├── page.tsx            # Landing page
└── simulation/
    └── page.tsx        # Main simulation viewer

components/
├── world/
│   └── WorldCanvas.tsx # Pixi.js isometric renderer
├── agents/
│   └── AgentDetailPanel.tsx
├── simulation/
│   ├── TimeControls.tsx
│   └── SimulationStats.tsx
└── ui/                 # Reusable UI components

hooks/
├── use-simulation-websocket.ts
└── use-simulation-data.ts

lib/
└── pixi-setup.ts       # Pixi.js utilities
```

## 🎮 Controls

- **🖱️ Drag** - Pan the world
- **🔍 Scroll** - Zoom in/out
- **👆 Click Agent** - View details
- **Space** - Play/Pause (future)
- **1-8** - Speed controls (future)

## 🐛 Development

### Build for Production

```bash
npm run build
npm start
```

### Lint

```bash
npm run lint
```

## 📝 Notes

- Backend must be running on port 8000 for real-time updates
- Currently using mock data when backend is unavailable
- All visualizations are GPU-accelerated via Pixi.js
- Glass morphism UI follows the design system from VISUAL_DESIGN_MASTERPLAN.md

## 🎯 Vision

This is not "blue dots on a grid." This is a window into an AI civilization.

Watch autonomous agents:
- Build economies from barter to banking
- Form religions and territories
- Start tax revolts
- Discover technologies
- Create emergent stories

**You don't control them. You watch them evolve.**

---

Built with ❤️ for autonomous AI civilization simulation.
