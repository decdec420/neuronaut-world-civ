# Phase 5 Refactoring Quick Reference

## Where to Find Things Now

### Birth and Death Logic
**File:** `lifecycle_manager.py` (193 lines)
- Birth handling → `LifecycleManager.handle_birth()`
- Death processing → `LifecycleManager.handle_deaths()`
- Death stories and achievements

### System Coordination
**File:** `system_coordinator.py` (275 lines)
- Disaster effects → `SystemCoordinator.apply_disaster_to_world()`
- Civilization milestones → `SystemCoordinator.check_civilization_milestones()`
- Resource decay → `SystemCoordinator.apply_resource_sinks()`

### Statistics and Reporting
**File:** `statistics_exporter.py` (190 lines)
- Population stats → `StatisticsExporter.get_population_statistics()`
- State snapshots → `StatisticsExporter.get_state_snapshot()`
- Population history → `StatisticsExporter.update_population_history()`

### World Setup
**File:** `world_initializer.py` (194 lines)
- World initialization → `WorldInitializer.initialize_world()`
- Agent creation → `WorldInitializer.create_agent()`
- Starting resources and positions

### System Creation
**File:** `system_factory.py` (268 lines)
- All system instantiation → `SystemFactory.create_simulation_systems()`
- 30+ game systems configured
- Returns organized dictionary

### Main Orchestrator
**File:** `simulation.py` (620 lines - reduced from 1,481!)
- Simulation loop → `run()` and `tick()`
- Action execution → `execute_action()`
- System coordination (delegates to specialists)

## Usage Examples

### Creating a Simulation
```python
# All system creation now handled by SystemFactory
from engine.simulation import SimulationEngine

sim = SimulationEngine(world_width=100, world_height=100)
# Systems automatically created and configured
sim.initialize_world(num_agents=50)  # Delegates to WorldInitializer
```

### Handling Births (Internal)
```python
# Called automatically by simulation during reproduction
# Now delegated to LifecycleManager
self.lifecycle_manager.handle_birth(parent_a, parent_b, child_data, tick)
```

### Getting Statistics
```python
# Now delegated to StatisticsExporter
stats = sim.get_population_statistics()
snapshot = sim.get_state_snapshot()
```

### Applying Disasters (Internal)
```python
# Called during tick() when disaster occurs
# Now delegated to SystemCoordinator
self.system_coordinator.apply_disaster_to_world(disaster)
```

## Module Responsibilities (At a Glance)

| Module | Primary Responsibility | Line Count |
|--------|----------------------|------------|
| `lifecycle_manager.py` | Birth and death handling | 193 |
| `system_coordinator.py` | System updates and coordination | 275 |
| `statistics_exporter.py` | Data aggregation and export | 190 |
| `world_initializer.py` | World and agent setup | 194 |
| `system_factory.py` | System instantiation | 268 |
| `simulation.py` | Orchestration and delegation | 620 |

## Import Structure

```python
# simulation.py imports all specialists
from engine.system_factory import SystemFactory
from engine.lifecycle_manager import LifecycleManager
from engine.system_coordinator import SystemCoordinator
from engine.statistics_exporter import StatisticsExporter
from engine.world_initializer import WorldInitializer

# Each specialist imports only what it needs
# All use TYPE_CHECKING to avoid circular imports
```

## Testing Strategy

Each module can be tested independently:

```python
# Mock the simulation
class MockSimulation:
    def __init__(self):
        self.world = MockWorld()
        self.event_logger = MockEventLogger()
        # ... etc

# Test lifecycle_manager
lifecycle = LifecycleManager(mock_sim)
lifecycle.handle_birth(parent_a, parent_b, child_data, 100)

# Test system_coordinator
coordinator = SystemCoordinator(mock_sim)
coordinator.apply_disaster_to_world(disaster)

# Test statistics_exporter
exporter = StatisticsExporter(mock_sim)
stats = exporter.get_population_statistics()
```

## Key Benefits

1. **Single Responsibility** - Each file does ONE thing
2. **Easy to Find** - Logic grouped by responsibility
3. **Testable** - Mock simulation, test specialists
4. **Maintainable** - Changes isolated to specific modules
5. **Clean** - simulation.py reduced by 58%

## Migration Notes

No breaking changes! All public APIs remain the same:
- `sim.initialize_world()` still works (delegates internally)
- `sim.create_agent()` still works (delegates internally)
- `sim.get_population_statistics()` still works (delegates internally)
- `sim.get_state_snapshot()` still works (delegates internally)

Internal changes only affect simulation.py internals.
