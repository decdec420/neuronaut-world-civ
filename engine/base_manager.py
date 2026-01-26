"""
Base Manager Classes - Eliminate Code Duplication

This module provides abstract base classes for all manager systems,
eliminating the 31+ duplicate get_statistics() implementations.

Benefits:
- Consistent interface across all managers
- Easier maintenance and testing
- Clear contract for new managers
- Type safety with ABC
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ManagerStatistics:
    """
    Standardized statistics structure for all managers.

    All managers return this consistent format, making it easy to:
    - Display statistics in UI
    - Aggregate statistics across systems
    - Track metrics over time
    """
    manager_name: str
    active_count: int = 0
    total_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            'manager_name': self.manager_name,
            'active_count': self.active_count,
            'total_count': self.total_count,
        }
        result.update(self.metadata)
        return result


class BaseManager(ABC):
    """
    Abstract base class for all manager systems.

    All managers (BuildingManager, InnovationManager, etc.) should inherit
    from this class to ensure consistent interface.

    Required Methods:
    - get_statistics(): Return current statistics
    - update(tick): Update state for current tick

    Optional Methods:
    - reset(): Reset manager state
    - get_status(): Get current status string
    """

    def __init__(self):
        """Initialize base manager"""
        self._initialized = True
        self._last_update_tick = 0

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics for this manager.

        Should return a dictionary with at least:
        - 'active_count': Number of active entities
        - 'total_count': Total number of entities

        Additional metrics should be included in the dict.

        Returns:
            Dictionary of statistics
        """
        pass

    @abstractmethod
    def update(self, tick: int) -> None:
        """
        Update manager state for current tick.

        This is called every simulation tick to update the manager's
        internal state.

        Args:
            tick: Current simulation tick
        """
        pass

    def reset(self) -> None:
        """
        Reset manager to initial state.

        Override this if your manager needs custom reset logic.
        """
        self._last_update_tick = 0

    def get_status(self) -> str:
        """
        Get human-readable status string.

        Override this to provide custom status information.

        Returns:
            Status string (e.g., "Active: 5, Total: 20")
        """
        stats = self.get_statistics()
        active = stats.get('active_count', 0)
        total = stats.get('total_count', 0)
        return f"Active: {active}, Total: {total}"

    def is_initialized(self) -> bool:
        """Check if manager is initialized"""
        return self._initialized

    def get_last_update_tick(self) -> int:
        """Get the tick of the last update"""
        return self._last_update_tick

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<{self.__class__.__name__}: {self.get_status()}>"


class CollectionManager(BaseManager):
    """
    Base class for managers that maintain a collection of entities.

    This is useful for managers like BuildingManager, InnovationManager, etc.
    that maintain lists or dicts of entities.

    Provides common functionality:
    - add_entity(entity)
    - remove_entity(entity_id)
    - get_entity(entity_id)
    - get_all_entities()
    - clear()
    """

    def __init__(self):
        """Initialize collection manager"""
        super().__init__()
        self._entities: Dict[str, Any] = {}

    def add_entity(self, entity_id: str, entity: Any) -> None:
        """
        Add an entity to the collection.

        Args:
            entity_id: Unique identifier for the entity
            entity: The entity object to add
        """
        self._entities[entity_id] = entity

    def remove_entity(self, entity_id: str) -> Optional[Any]:
        """
        Remove an entity from the collection.

        Args:
            entity_id: ID of entity to remove

        Returns:
            The removed entity, or None if not found
        """
        return self._entities.pop(entity_id, None)

    def get_entity(self, entity_id: str) -> Optional[Any]:
        """
        Get an entity by ID.

        Args:
            entity_id: ID of entity to retrieve

        Returns:
            The entity, or None if not found
        """
        return self._entities.get(entity_id)

    def get_all_entities(self) -> Dict[str, Any]:
        """
        Get all entities.

        Returns:
            Dictionary of all entities (entity_id -> entity)
        """
        return self._entities.copy()

    def clear(self) -> None:
        """Remove all entities"""
        self._entities.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics for collection-based manager.

        Returns:
            Dictionary with entity counts
        """
        return {
            'total_count': len(self._entities),
            'active_count': len(self._entities),
            'entity_ids': list(self._entities.keys())
        }

    def update(self, tick: int) -> None:
        """
        Update collection for current tick.

        Default implementation just updates the last tick.
        Override for custom behavior.
        """
        self._last_update_tick = tick


class ListManager(BaseManager):
    """
    Base class for managers that maintain a list of entities.

    Similar to CollectionManager but uses a list instead of dict.
    Useful when entities don't have unique IDs or order matters.
    """

    def __init__(self):
        """Initialize list manager"""
        super().__init__()
        self._entities: List[Any] = []

    def add_entity(self, entity: Any) -> None:
        """Add an entity to the list"""
        self._entities.append(entity)

    def remove_entity(self, entity: Any) -> bool:
        """
        Remove an entity from the list.

        Returns:
            True if entity was removed, False if not found
        """
        try:
            self._entities.remove(entity)
            return True
        except ValueError:
            return False

    def get_all_entities(self) -> List[Any]:
        """Get all entities"""
        return self._entities.copy()

    def clear(self) -> None:
        """Remove all entities"""
        self._entities.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for list-based manager"""
        return {
            'total_count': len(self._entities),
            'active_count': len(self._entities),
        }

    def update(self, tick: int) -> None:
        """Update list for current tick"""
        self._last_update_tick = tick


class TickBasedManager(BaseManager):
    """
    Base class for managers that perform actions on specific ticks.

    Useful for managers that need to do periodic updates, spawning,
    or cleanup at regular intervals.
    """

    def __init__(self, update_interval: int = 1):
        """
        Initialize tick-based manager.

        Args:
            update_interval: How many ticks between updates
        """
        super().__init__()
        self._update_interval = update_interval
        self._ticks_since_update = 0

    @abstractmethod
    def perform_update(self, tick: int) -> None:
        """
        Perform the actual update logic.

        This is called when it's time for an update (every update_interval ticks).

        Args:
            tick: Current simulation tick
        """
        pass

    def update(self, tick: int) -> None:
        """
        Update manager, calling perform_update at intervals.

        Args:
            tick: Current simulation tick
        """
        self._last_update_tick = tick
        self._ticks_since_update += 1

        if self._ticks_since_update >= self._update_interval:
            self.perform_update(tick)
            self._ticks_since_update = 0

    def set_update_interval(self, interval: int) -> None:
        """Change the update interval"""
        self._update_interval = max(1, interval)

    def get_update_interval(self) -> int:
        """Get current update interval"""
        return self._update_interval


# Utility functions for manager aggregation

def aggregate_manager_statistics(managers: List[BaseManager]) -> Dict[str, Any]:
    """
    Aggregate statistics from multiple managers.

    Args:
        managers: List of manager instances

    Returns:
        Dictionary with aggregated statistics
    """
    total_stats = {
        'managers': [],
        'total_entities': 0,
        'total_active': 0,
    }

    for manager in managers:
        stats = manager.get_statistics()
        manager_name = manager.__class__.__name__

        total_stats['managers'].append({
            'name': manager_name,
            'stats': stats
        })

        total_stats['total_entities'] += stats.get('total_count', 0)
        total_stats['total_active'] += stats.get('active_count', 0)

    return total_stats


def get_manager_status_report(managers: Dict[str, BaseManager]) -> str:
    """
    Generate a status report for all managers.

    Args:
        managers: Dictionary of manager_name -> manager_instance

    Returns:
        Formatted status report string
    """
    lines = ["=" * 60, "MANAGER STATUS REPORT", "=" * 60]

    for name, manager in managers.items():
        status = manager.get_status()
        lines.append(f"{name:30s} | {status}")

    lines.append("=" * 60)
    return "\n".join(lines)
