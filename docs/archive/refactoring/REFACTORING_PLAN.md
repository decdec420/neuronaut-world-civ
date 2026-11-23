# 📋 simulation.py Refactoring Plan

## Phase 1: Core Loop (Day 1) - SAFE START ✅ COMPLETE

### Step 1.1: Create directory structure ✅
```bash
mkdir -p engine/core
mkdir -p engine/agent_updates
mkdir -p engine/systems
mkdir -p engine/managers
mkdir -p engine/utils
touch engine/core/__init__.py
touch engine/agent_updates/__init__.py
touch engine/systems/__init__.py
touch engine/managers/__init__.py
touch engine/utils/__init__.py
```

### Step 1.2: Extract agent cache helpers ✅ COMPLETE
**New file**: `engine/utils/agent_helpers.py` ✅ CREATED

**Lines to move**: 1337-1370 (agent cache methods)

```python
# engine/utils/agent_helpers.py
from typing import Dict, Optional
from agents.agent import Agent

class AgentCacheHelper:
    """Helper for O(1) agent lookups"""
    
    def __init__(self):
        self._agent_cache: Dict[str, Agent] = {}
    
    def rebuild_cache(self, agents: list) -> None:
        """Rebuild the agent lookup cache"""
        self._agent_cache = {
            agent.id: agent 
            for agent in agents 
            if agent.alive
        }
    
    def get_agent_by_id(self, agent_id: str, agents: list) -> Optional[Agent]:
        """Fast O(1) agent lookup by ID"""
        # Try cache first
        agent = self._agent_cache.get(agent_id)
        if agent and agent.alive:
            return agent
        
        # Cache miss - linear search and update
        for agent in agents:
            if agent.id == agent_id and agent.alive:
                self._agent_cache[agent_id] = agent
                return agent
        
        return None
```

**In simulation.py**: Replace methods with:
```python
from engine.utils.agent_helpers import AgentCacheHelper

class SimulationEngine:
    def __init__(self, ...):
        # ... existing code ...
        self._agent_helper = AgentCacheHelper()
    
    def _rebuild_agent_cache(self):
        self._agent_helper.rebuild_cache(self.world.agents)
    
    def get_agent_by_id(self, agent_id: str):
        return self._agent_helper.get_agent_by_id(agent_id, self.world.agents)
```

---

## Phase 2: Extract Perception Building (Day 2)

### Step 2.1: Create perception builder
**New file**: `engine/agent_updates/perception_builder.py`

**Lines to move**: 1766-3070 (MASSIVE perception building section)

```python
# engine/agent_updates/perception_builder.py
from typing import Dict, Any
from agents.agent import Agent

class PerceptionBuilder:
    """Builds comprehensive perceptions for agent decision-making"""
    
    def __init__(self, simulation):
        self.sim = simulation  # Reference to main simulation
    
    def build_perceptions(self, agent: Agent, world_state: Dict) -> Dict[str, Any]:
        """Build full perceptions for an agent"""
        # Basic perception
        perceptions = agent.perceive(world_state)
        
        # Add combat info
        perceptions = self._add_combat_info(agent, perceptions)
        
        # Add governance info  
        perceptions = self._add_governance_info(agent, perceptions)
        
        # Add resource scarcity info
        perceptions = self._add_scarcity_info(agent, perceptions)
        
        # Add life info (romance, reproduction)
        perceptions = self._add_life_info(agent, perceptions)
        
        # Add economic info
        perceptions = self._add_economic_info(agent, perceptions)
        
        return perceptions
    
    def _add_combat_info(self, agent: Agent, perceptions: Dict) -> Dict:
        """Add nearby agents and combat opportunities"""
        # Move lines 1768-1818 here
        ...
    
    def _add_governance_info(self, agent: Agent, perceptions: Dict) -> Dict:
        """Add government and political info"""
        # Move lines 1819-1859 here
        ...
    
    # ... etc for each perception type
```

**In simulation.py**: Replace with:
```python
from engine.agent_updates.perception_builder import PerceptionBuilder

class SimulationEngine:
    def __init__(self, ...):
        self._perception_builder = PerceptionBuilder(self)
    
    async def tick(self):
        # ... in agent loop ...
        world_state = self.world.get_state()
        perceptions = self._perception_builder.build_perceptions(agent, world_state)
```

---

## Phase 3: Extract Agent Updater (Day 3)

### Step 3.1: Create agent updater
**New file**: `engine/agent_updates/agent_updater.py`

**Lines to move**: 1590-1760 (agent state updates, needs decay, disease effects)

```python
# engine/agent_updates/agent_updater.py

class AgentUpdater:
    """Handles all agent state updates each tick"""
    
    def __init__(self, simulation):
        self.sim = simulation
    
    def update_agent(self, agent: Agent, current_tick: int) -> None:
        """Update single agent for this tick"""
        if not agent.alive:
            return
        
        try:
            # Basic update
            agent.update()
            
            # Apply resource sinks
            self._apply_resource_sinks(agent)
            
            # Reputation decay
            agent.decay_reputation(decay_rate=0.001)
            
            # Weather effects
            self._apply_weather_effects(agent)
            
            # Disease effects
            self._apply_disease_effects(agent, current_tick)
            
            # Trespassing check
            self._check_trespassing(agent, current_tick)
            
        except Exception as e:
            # Error isolation
            logger.error(f"❌ Agent {agent.name} update failed: {e}")
            agent.health = max(0, agent.health - 10)
            if agent.health <= 0:
                agent.alive = False
                agent.death_cause = "system_error"
    
    def _apply_resource_sinks(self, agent: Agent) -> None:
        """Apply resource decay to prevent inflation"""
        # Move lines 1599-1601 here
        ...
    
    def _apply_weather_effects(self, agent: Agent) -> None:
        """Apply weather damage/energy drain"""
        # Move lines 1604-1622 here
        ...
    
    def _apply_disease_effects(self, agent: Agent, current_tick: int) -> None:
        """Apply disease damage"""
        # Move lines 1623-1633 here
        ...
    
    def _check_trespassing(self, agent: Agent, current_tick: int) -> None:
        """Check if agent is trespassing"""
        # Move lines 1634-1760 here
        ...
```

---

## Phase 4: Extract Decision Making (Day 4)

### Step 4.1: Create decision maker
**New file**: `engine/agent_updates/decision_maker.py`

**Lines to move**: 3075-3160 (AI decisions, goal evaluation, action selection)

```python
# engine/agent_updates/decision_maker.py

class DecisionMaker:
    """Handles agent decision-making (AI + rule-based)"""
    
    def __init__(self, simulation):
        self.sim = simulation
    
    def make_decision(self, agent: Agent, perceptions: Dict, current_tick: int) -> Action:
        """Agent decides what action to take"""
        
        # Try AI decision if enabled
        if self.sim.config.use_llm_decisions:
            action = self._try_ai_decision(agent, perceptions, current_tick)
            if action:
                return action
        
        # Fall back to rule-based
        return self._rule_based_decision(agent, perceptions)
    
    def _try_ai_decision(self, agent: Agent, perceptions: Dict, current_tick: int):
        """Try AI-powered decision"""
        try:
            return agent.autonomous_decide(perceptions, current_tick, self.sim.config)
        except Exception as e:
            logger.error(f"AI decision failed for {agent.name}: {e}")
            return None
    
    def _rule_based_decision(self, agent: Agent, perceptions: Dict) -> Action:
        """Rule-based fallback decision"""
        # Check strategic goals
        current_goal = self.sim.strategy_manager.get_current_goal(agent.id)
        if current_goal:
            goal_action = self.sim.strategy_manager.evaluate_goal_action(agent, current_goal)
            if goal_action:
                return goal_action
        
        # Default agent decision
        return agent.decide(perceptions)
```

---

## Phase 5: Extract Action Execution (Day 5)

### Step 5.1: Create action executor  
**New file**: `engine/agent_updates/action_executor.py`

**Lines to move**: 3161-3400 (execute_action and all action handlers)

```python
# engine/agent_updates/action_executor.py

class ActionExecutor:
    """Executes agent actions"""
    
    def __init__(self, simulation):
        self.sim = simulation
    
    async def execute_action(self, agent: Agent, action: Action) -> Dict:
        """Execute agent's chosen action"""
        try:
            # Use action handler registry
            outcome = await self.sim._action_context.execute_action(agent, action)
            return outcome
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {"success": False, "reason": str(e)}
```

---

## Phase 6: Extract System Updaters (Day 6-7)

### Step 6.1: Health updater
**New file**: `engine/systems/health_updater.py`

```python
class HealthUpdater:
    """Manages disease spread and health updates"""
    
    def update(self, current_tick: int, agents: list, health_manager):
        # Disease updates
        deaths = health_manager.update_diseases(current_tick, agents)
        
        # Disease spread
        health_manager.spread_diseases(agents, current_tick)
        
        return deaths
```

### Step 6.2: Life cycle manager
**New file**: `engine/systems/life_cycle.py`

```python
class LifeCycleManager:
    """Handles births, deaths, aging"""
    
    def process_births(self, agents: list, current_tick: int):
        """Check for births from pregnant agents"""
        ...
    
    def process_deaths(self, agents: list, current_tick: int):
        """Remove dead agents, create death stories"""
        ...
    
    def process_aging(self, agents: list, current_tick: int):
        """Age agents, update life stages"""
        ...
```

---

## Phase 7: Final Cleanup (Day 8)

### Step 7.1: Slim down main simulation.py

**Final structure**:
```python
# engine/simulation.py (NOW ~300 LINES!)

from engine.core.simulation_engine import SimulationCore
from engine.agent_updates.agent_updater import AgentUpdater
from engine.agent_updates.perception_builder import PerceptionBuilder
from engine.agent_updates.decision_maker import DecisionMaker
from engine.agent_updates.action_executor import ActionExecutor
from engine.systems.health_updater import HealthUpdater
from engine.systems.life_cycle import LifeCycleManager
from engine.utils.agent_helpers import AgentCacheHelper

class SimulationEngine:
    """Main simulation orchestrator - delegates to specialized components"""
    
    def __init__(self, world_width: int = 100, world_height: int = 100):
        # Initialize all subsystems
        self.world = World(world_width, world_height)
        self.core = SimulationCore(self)
        self.agent_updater = AgentUpdater(self)
        self.perception_builder = PerceptionBuilder(self)
        self.decision_maker = DecisionMaker(self)
        self.action_executor = ActionExecutor(self)
        self.health_updater = HealthUpdater(self)
        self.life_cycle = LifeCycleManager(self)
        self.agent_helper = AgentCacheHelper()
        
        # ... all the managers ...
    
    async def tick(self):
        """Single simulation tick - orchestrate all updates"""
        current_tick = self.world.time.current_tick
        
        # Update world systems
        self.core.update_world_systems(current_tick)
        
        # Update all agents
        for agent in self.world.agents:
            if not agent.alive:
                continue
            
            # 1. Update agent state
            self.agent_updater.update_agent(agent, current_tick)
            
            # 2. Build perceptions
            world_state = self.world.get_state()
            perceptions = self.perception_builder.build_perceptions(agent, world_state)
            
            # 3. Make decision
            action = self.decision_maker.make_decision(agent, perceptions, current_tick)
            
            # 4. Execute action
            outcome = await self.action_executor.execute_action(agent, action)
        
        # Update life cycle
        self.life_cycle.process_births(self.world.agents, current_tick)
        self.life_cycle.process_deaths(self.world.agents, current_tick)
        
        # Update health
        self.health_updater.update(current_tick, self.world.agents, self.health)
        
        # Advance time
        self.world.time.advance()
    
    # Keep only high-level coordination methods
    def initialize_world(self, num_agents: int = 50):
        """Delegates to initialization module"""
        from engine.core.initialization import initialize_world
        initialize_world(self, num_agents)
    
    def get_state_snapshot(self):
        """Delegates to world state module"""
        from engine.core.world_state import get_state_snapshot
        return get_state_snapshot(self)
```

---

## ✅ Testing Strategy

After each phase, test:
```bash
# 1. Server starts
./start_game.sh

# 2. Simulation runs
curl http://localhost:8000/

# 3. Agents spawn
curl http://localhost:8000/agents?limit=5

# 4. No errors in logs
tail -50 server.log | grep -i error
```

---

## 📊 Benefits After Refactoring

| Metric | Before | After |
|--------|--------|-------|
| Main file lines | 6,500 | 300 |
| Files | 1 | 17 |
| Average file size | 6,500 | ~200 |
| Testability | Hard | Easy |
| Maintainability | Nightmare | Simple |
| Onboarding time | Days | Hours |

---

## 🎯 Key Principles

1. **Single Responsibility** - Each file does ONE thing
2. **Dependency Injection** - Pass simulation reference to subsystems
3. **Gradual Migration** - Do one phase at a time, test after each
4. **Keep It Working** - Don't break the simulation
5. **Document As You Go** - Comment why each module exists

---

## 🚨 Common Pitfalls to Avoid

1. **Don't do it all at once** - You'll get lost
2. **Don't change logic** - Just move code, don't refactor behavior
3. **Test after every phase** - Catch breaks early
4. **Keep imports working** - Update all import statements
5. **Don't optimize yet** - Refactor first, optimize later

---

## 📅 Timeline

- **Day 1**: Utils (agent helpers) - 2 hours
- **Day 2**: Perception builder - 4 hours  
- **Day 3**: Agent updater - 4 hours
- **Day 4**: Decision maker - 3 hours
- **Day 5**: Action executor - 3 hours
- **Day 6-7**: System updaters - 6 hours
- **Day 8**: Final cleanup & testing - 4 hours

**Total**: ~26 hours spread over 2 weeks

---

## 🎉 Result

You'll go from:
- ❌ One 6,500-line file nobody understands
- ❌ Can't find anything
- ❌ Afraid to change code

To:
- ✅ 17 focused files, each under 400 lines
- ✅ Clear organization
- ✅ Easy to test, maintain, extend
- ✅ Can work on perception logic without touching action logic

**You'll feel like a professional software engineer!** 🚀
