# Neuronaut World - AI Agent Instructions

## Project Overview
Autonomous virtual world where AI agents with realistic psychology create emergent society, economy, and culture. Built autonomously by AI. Agents make LLM-powered decisions based on psychological needs, forming relationships, trading, building, fighting, and evolving civilization from Stone Age to Space Age.

## Architecture Fundamentals

### Core Stack
- **Python 3.10+** FastAPI simulation backend
- **FastAPI + WebSockets** for API and real-time updates (`api/server.py`)
- **Pure HTML/JS frontend** (no build step) in `web/`
- **SQLite** via SQLAlchemy for persistence
- **No Node.js** - this is NOT a JavaScript project

### System Hierarchy
```
SimulationEngine (engine/simulation.py)
  ├─ World (world/simulation.py) - terrain, resources, time
  ├─ Agents (agents/agent.py) - autonomous entities
  ├─ Managers - specialized subsystems (BaseManager pattern)
  │   ├─ BuildingManager, InnovationManager, WarfareManager
  │   ├─ RelationshipManager, GroupManager, EconomicEngine
  │   └─ 20+ other domain-specific managers
  └─ Action Handlers (engine/handlers/) - execute agent actions
```

### The Manager Pattern
All managers inherit from `BaseManager` (`engine/base_manager.py`):
- **CollectionManager** - for entity collections (buildings, innovations)
- **ListManager** - for simple lists
- **TickBasedManager** - for time-based processing

Every manager MUST implement:
- `get_statistics() -> Dict[str, Any]` - return {active_count, total_count, ...}
- `update(tick: int) -> None` - called every simulation tick

Never create duplicate statistics methods - use base class patterns.

### Action Handler Architecture
Agent actions execute via Strategy Pattern (`engine/action_handlers.py`):
- **ActionHandler** - abstract base for all handlers
- **ActionResult** - standardized return format
- **ActionContext** - provides controlled access to simulation systems
- Handlers live in `engine/handlers/` (movement, combat, social, etc.)

When adding new actions:
1. Add to `ActionType` enum in `agents/agent.py`
2. Create handler in appropriate `engine/handlers/*.py` file
3. Register in `SimulationEngine._register_action_handlers()`

## AI Autonomy System

### LLM Integration (`agents/llm_brain.py`)
Agents use **multiple free LLM providers** to make decisions:
- **Ollama (local)** - unlimited, always available
- **Groq** - 30/min, fast inference
- **Gemini Flash** - 15/min, smart
- **Hugging Face** - 30k/month
- **Together AI** - 60/min

`MultiLLMBrain` rotates providers to avoid rate limits. Configure in `.env`:
```bash
USE_LLM_DECISIONS=true
GROQ_API_KEY=...
GEMINI_API_KEY=...
```

### Autonomous Agent Mixin
`agents/autonomous_agent.py` gives agents:
- Long-term goal planning (`GoalType` enum)
- Memory system (episodic, semantic, procedural)
- Self-reflection and learning
- Creative problem-solving

Agents have COMPLETE autonomy - no scripted behavior.

## Key Development Patterns

### Running the Simulation
```bash
python3 main.py  # NOT npm run dev!
# Access at http://localhost:8000/app
```

Or use VS Code tasks:
- **F5** - Run simulation
- **Cmd+Shift+B** → "🚀 Run Neuronaut World"

### Testing Patterns
Tests are in root directory (`test_*.py`) and use pytest:
```bash
pytest test_economic_system.py
pytest test_governance_integration.py -v
```

Tests verify manager integration, NOT unit tests. They check:
- Manager statistics methods work
- Systems interact correctly
- No AttributeErrors on new features

### Configuration System
`config.py` loads from `.env`:
- LLM API keys
- Feature flags (`USE_LLM_DECISIONS`, `ENABLE_SWARM_INTELLIGENCE`)
- Simulation parameters (intervals, thresholds)

All config values have validation and defaults. Never hardcode values that belong in config.

### Psychology-Driven Design
Everything emerges from agent psychology (`engine/psychology.py`):
- **Needs** (hunger, sleep, social, status, meaning) drive action selection
- **Personality** (Big Five + extras) influences choices
- **Emotions** modulate behavior
- Agents act to satisfy needs, NOT scripted routines

When adding features, ask: "How would a real person's psychology drive this?"

## Common Gotchas

### Attribute Existence
New features often add agent attributes. Check existence:
```python
# BAD
needs_value = agent.needs.social

# GOOD
needs_value = getattr(agent.needs, 'social', 0.0)
```

Search for attribute access before adding features:
```bash
grep -r "\.needs\." --include="*.py"
```

### Agent Creation Flow
Agents are created in `ProfileBuilder.generate_random_profile()` (`agents/profiles.py`). When adding agent attributes:
1. Initialize in `Agent.__init__()` 
2. Add to `ProfileBuilder` generation
3. Include in serialization (`to_dict()`, `from_dict()`)

### Manager Integration
When creating new managers:
1. Inherit from appropriate base (`CollectionManager`, `BaseManager`)
2. Implement required methods
3. Add to `SimulationEngine.__init__()`
4. Register in `SimulationEngine._register_action_handlers()` if needed
5. Call `manager.update(tick)` in simulation loop

### WebSocket Updates
Real-time updates flow:
1. `SimulationEngine.update()` processes tick
2. State change detected
3. `_broadcast_update()` sends JSON to all WebSocket clients
4. Frontend (`web/game_interface.js`) receives and renders

Modify `_broadcast_update()` to add new real-time data.

## File Navigation

**Start here for understanding:**
- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture (612 lines)
- [SYSTEMS_OVERVIEW.md](SYSTEMS_OVERVIEW.md) - All 30+ systems explained
- [HOW_TO_RUN.md](HOW_TO_RUN.md) - Running the simulation

**Core systems:**
- [engine/simulation.py](engine/simulation.py) - Main simulation loop (6500+ lines)
- [agents/agent.py](agents/agent.py) - Agent definition and ActionType enum (1600+ lines)
- [engine/base_manager.py](engine/base_manager.py) - Manager base classes
- [engine/action_handlers.py](engine/action_handlers.py) - Action execution architecture

**AI autonomy:**
- [agents/llm_brain.py](agents/llm_brain.py) - Multi-LLM decision making (2000+ lines)
- [agents/autonomous_agent.py](agents/autonomous_agent.py) - Goals, memory, learning

**Domain systems:**
- `world/*.py` - World simulation (buildings, innovations, conflict, governance, tech progression)
- `engine/handlers/*.py` - Action handlers (18 specialized handlers)
- `economy/*.py` - Economic systems (trade, production, materials, recipes)
- `social/*.py` - Relationships, groups, culture

## Critical Commands

```bash
# Start simulation
python3 main.py

# Run tests
pytest test_*.py -v

# Check for attribute errors
grep -r "AttributeError" --include="*.py"

# Find all manager statistics
grep -r "get_statistics" --include="*.py"

# Search for action type usage
grep -r "ActionType\." --include="*.py"
```

## Innovation Philosophy
This project was **built autonomously by AI**. When adding features:
- Favor emergence over scripting
- Let psychology drive behavior
- Trust agent autonomy
- Create systems, not scripts
- Test integration, not units

Documentation is extensive (50+ MD files) - read before building!
