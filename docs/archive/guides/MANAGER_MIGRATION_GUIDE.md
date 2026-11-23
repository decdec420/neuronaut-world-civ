# Manager Migration Guide

## Overview

This guide shows how to migrate existing managers to use the new `BaseManager` abstract class, eliminating code duplication across 31+ managers.

## Why Migrate?

**Before:** 31 managers with duplicate `get_statistics()` implementations
**After:** All managers inherit from `BaseManager` with consistent interface

**Benefits:**
- ✅ Consistent interface across all managers
- ✅ Easier to test and maintain
- ✅ Type-safe with ABC
- ✅ Clear contract for new managers
- ✅ Utility functions for aggregation

## Base Classes Available

### 1. `BaseManager` - Abstract base class
Use for simple managers with custom logic.

### 2. `CollectionManager` - For dict-based collections
Use when managing entities with unique IDs (buildings, innovations, etc.)

### 3. `ListManager` - For list-based collections
Use when entities don't have IDs or order matters.

### 4. `TickBasedManager` - For periodic updates
Use when manager performs actions at intervals.

## Migration Examples

### Example 1: Simple Manager (BuildingManager)

**Before:**
```python
class BuildingManager:
    def __init__(self):
        self.buildings = []

    def get_statistics(self):
        return {
            'total_buildings': len(self.buildings),
            'building_types': self._count_types()
        }

    def update(self, tick):
        # Update logic
        pass
```

**After:**
```python
from engine.base_manager import ListManager

class BuildingManager(ListManager):
    def get_statistics(self):
        # Call parent for base stats
        stats = super().get_statistics()

        # Add custom stats
        stats['building_types'] = self._count_types()

        return stats

    def update(self, tick):
        # Call parent first
        super().update(tick)

        # Custom update logic
        for building in self._entities:
            building.update(tick)

    def _count_types(self):
        # Custom helper method
        types = {}
        for building in self._entities:
            types[building.type] = types.get(building.type, 0) + 1
        return types
```

### Example 2: Collection-Based Manager (InnovationManager)

**Before:**
```python
class InnovationManager:
    def __init__(self):
        self.innovations = {}  # id -> innovation

    def add_innovation(self, innovation):
        self.innovations[innovation.id] = innovation

    def get_statistics(self):
        return {
            'total_innovations': len(self.innovations),
            'innovation_ids': list(self.innovations.keys())
        }
```

**After:**
```python
from engine.base_manager import CollectionManager

class InnovationManager(CollectionManager):
    def add_innovation(self, innovation):
        # Use parent's add_entity method
        self.add_entity(innovation.id, innovation)

    def get_statistics(self):
        # Parent already provides total_count and entity_ids
        stats = super().get_statistics()

        # Rename for clarity
        stats['total_innovations'] = stats.pop('total_count')
        stats['innovation_ids'] = stats.pop('entity_ids')

        return stats
```

### Example 3: Tick-Based Manager (WeatherSystem)

**Before:**
```python
class WeatherSystem:
    def __init__(self):
        self.weather = 'clear'
        self.ticks_since_change = 0

    def update(self, tick):
        self.ticks_since_change += 1
        if self.ticks_since_change >= 100:  # Change every 100 ticks
            self._change_weather()
            self.ticks_since_change = 0
```

**After:**
```python
from engine.base_manager import TickBasedManager

class WeatherSystem(TickBasedManager):
    def __init__(self):
        super().__init__(update_interval=100)  # Update every 100 ticks
        self.weather = 'clear'

    def perform_update(self, tick):
        # This is called every 100 ticks automatically
        self._change_weather()

    def get_statistics(self):
        return {
            'current_weather': self.weather,
            'ticks_until_change': self._update_interval - self._ticks_since_update
        }
```

## Migration Checklist

For each manager:

1. ✅ **Choose appropriate base class**
   - Simple logic? → `BaseManager`
   - Dict of entities? → `CollectionManager`
   - List of entities? → `ListManager`
   - Periodic updates? → `TickBasedManager`

2. ✅ **Update inheritance**
   ```python
   from engine.base_manager import CollectionManager

   class MyManager(CollectionManager):  # Add base class
   ```

3. ✅ **Update __init__**
   ```python
   def __init__(self):
       super().__init__()  # Call parent __init__
       # Your custom init
   ```

4. ✅ **Update get_statistics()**
   ```python
   def get_statistics(self):
       stats = super().get_statistics()  # Get base stats
       # Add custom stats
       stats['my_custom_stat'] = self._calculate()
       return stats
   ```

5. ✅ **Update update()**
   ```python
   def update(self, tick):
       super().update(tick)  # Call parent update
       # Your custom update logic
   ```

6. ✅ **Test the manager**
   - Verify statistics are correct
   - Verify update logic works
   - Check that existing code still works

## All Managers to Migrate (31 total)

### Core Systems (6)
- [ ] `BuildingManager` (world/buildings.py) → `ListManager`
- [ ] `InnovationManager` (world/innovations.py) → `CollectionManager`
- [ ] `WarfareManager` (world/conflict.py) → `CollectionManager`
- [ ] `GovernanceManager` (world/governance.py) → `CollectionManager`
- [ ] `ProductionManager` (economy/production.py) → `CollectionManager`
- [ ] `StrategyManager` (agents/strategy.py) → `BaseManager`

### Autonomous Systems (8)
- [ ] `ExperimentationEngine` (world/experimentation.py) → `CollectionManager`
- [ ] `DynamicBuildingSystem` (world/dynamic_buildings.py) → `CollectionManager`
- [ ] `KnowledgeSystem` (world/knowledge.py) → `CollectionManager`
- [ ] `ConsequenceEngine` (world/consequences.py) → `ListManager`
- [ ] `RoleEmergence` (world/roles.py) → `CollectionManager`
- [ ] `TechProgressionTracker` (world/tech_progression.py) → `BaseManager`
- [ ] `PurposefulActionEvaluator` (agents/purposeful_action.py) → `BaseManager`
- [ ] `CivilizationProgressionEngine` (world/civilization_progression.py) → `BaseManager`

### Specialized Systems (17)
- [ ] `LifeSystem` (life/life_system.py) → `CollectionManager`
- [ ] `FunSystem` (world/fun_system.py) → `CollectionManager`
- [ ] `AgricultureManager` (world/agriculture.py) → `CollectionManager`
- [ ] `HealthManager` (world/health.py) → `CollectionManager`
- [ ] `ReligionManager` (world/religion.py) → `CollectionManager`
- [ ] `TerritoryManager` (world/territory.py) → `CollectionManager`
- [ ] `ChemistryEngine` (world/chemistry.py) → `CollectionManager`
- [ ] `EnergyManager` (world/energy.py) → `CollectionManager`
- [ ] `MaterialsManager` (world/materials.py) → `CollectionManager`
- [ ] `WeatherSystem` (world/weather.py) → `TickBasedManager`
- [ ] `NaturalDisasterSystem` (world/disasters.py) → `TickBasedManager`
- [ ] `Pathfinder` (agents/pathfinding.py) → `BaseManager`
- [ ] `ResourceMemory` (agents/pathfinding.py) → `CollectionManager`
- [ ] `MetaProgressionEngine` (world/meta_progression.py) → `BaseManager`
- [ ] `EventLogger` (engine/events.py) → `ListManager`
- [ ] `StoryGenerator` (engine/storytelling.py) → `BaseManager`
- [ ] `AchievementTracker` (engine/achievements.py) → `CollectionManager`

## Testing After Migration

After migrating each manager, run these tests:

```python
# 1. Test instantiation
manager = MyManager()
assert manager.is_initialized()

# 2. Test statistics
stats = manager.get_statistics()
assert 'total_count' in stats or 'total_<entities>' in stats
assert isinstance(stats, dict)

# 3. Test update
manager.update(1)
assert manager.get_last_update_tick() == 1

# 4. Test status
status = manager.get_status()
assert isinstance(status, str)
```

## Utility Functions

After migration, you can use these utilities:

```python
from engine.base_manager import aggregate_manager_statistics, get_manager_status_report

# Aggregate stats from all managers
all_managers = [
    building_manager,
    innovation_manager,
    warfare_manager,
    # ... etc
]

total_stats = aggregate_manager_statistics(all_managers)
print(f"Total entities across all managers: {total_stats['total_entities']}")

# Generate status report
managers_dict = {
    'Buildings': building_manager,
    'Innovations': innovation_manager,
    'Warfare': warfare_manager,
}

report = get_manager_status_report(managers_dict)
print(report)
```

## Benefits After Migration

Once all managers are migrated:

1. ✅ **Consistent API** - All managers have same interface
2. ✅ **Type Safety** - ABC ensures contract compliance
3. ✅ **Easy Testing** - Test base functionality once
4. ✅ **Aggregation** - Utility functions work across all managers
5. ✅ **Maintenance** - Fix bugs in one place
6. ✅ **Documentation** - Clear base class docs apply to all

## Migration Priority

**Phase 1 (High Usage):**
1. BuildingManager
2. InnovationManager
3. AgricultureManager
4. HealthManager
5. EconomicEngine managers

**Phase 2 (Medium Usage):**
6-15. Specialized systems

**Phase 3 (Low Usage):**
16-31. Remaining managers

## Need Help?

See `engine/base_manager.py` for full base class documentation and examples.
