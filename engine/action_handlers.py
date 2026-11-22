"""
Action Handler Architecture - SOLID-Compliant Action Execution System

This module implements the Strategy Pattern + Command Pattern to replace the
monolithic execute_action() method with modular, testable action handlers.

Key Components:
- ActionHandler: Abstract base class for all action handlers
- ActionResult: Standardized action execution result
- ActionContext: Facade providing controlled access to simulation systems
- ActionHandlerRegistry: Registration and dispatch system

Benefits:
- Single Responsibility: Each handler manages one action category
- Open/Closed: Add new actions without modifying existing code
- Testability: Unit test handlers in isolation
- Maintainability: Clear dependencies and focused classes
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from engine.simulation import SimulationEngine
    from agents.agent import Agent, Action, ActionType
    from world.simulation import World
    from engine.events import EventLogger


@dataclass
class ActionResult:
    """
    Standardized action execution result.

    All action handlers return this consistent format, which is then
    converted to the legacy dictionary format for backward compatibility.

    Attributes:
        success: Whether the action completed successfully
        emotional_impact: Emotional effect on agent (-1.0 to 1.0)
        message: Human-readable result message
        metadata: Additional action-specific data
    """
    success: bool
    emotional_impact: float = 0.0
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to legacy dictionary format for backward compatibility.

        Returns:
            Dictionary with success, emotional_impact, message, and metadata fields
        """
        result = {
            'success': self.success,
            'emotional_impact': self.emotional_impact
        }
        if self.message:
            result['message'] = self.message
        result.update(self.metadata)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionResult':
        """
        Create ActionResult from legacy dictionary format.

        Args:
            data: Legacy result dictionary

        Returns:
            ActionResult instance
        """
        return cls(
            success=data.get('success', False),
            emotional_impact=data.get('emotional_impact', 0.0),
            message=data.get('message', ''),
            metadata={k: v for k, v in data.items()
                     if k not in ['success', 'emotional_impact', 'message']}
        )


class ActionContext:
    """
    Provides action handlers with controlled access to simulation systems.

    This acts as a Facade pattern, preventing handlers from accessing all of
    SimulationEngine's internals while providing necessary dependencies.

    Benefits:
    - Encapsulation: Handlers can't accidentally modify engine state
    - Testability: Easy to mock context for unit tests
    - Flexibility: Can change internal implementation without breaking handlers
    """

    def __init__(self, simulation_engine: 'SimulationEngine'):
        """
        Initialize context with reference to simulation engine.

        Args:
            simulation_engine: The main simulation engine instance
        """
        self._engine = simulation_engine

    # Read-only properties for safe access to common systems

    @property
    def world(self) -> 'World':
        """Access to world state (read-only)"""
        return self._engine.world

    @property
    def current_tick(self) -> int:
        """Current simulation tick"""
        return self._engine.world.time.current_tick

    @property
    def event_logger(self) -> 'EventLogger':
        """Event logging system"""
        return self._engine.event_logger

    # System access methods

    def get_system(self, system_name: str) -> Any:
        """
        Get a specific system by name.

        This provides flexibility for handlers to access specialized systems
        without needing individual properties for each one.

        Args:
            system_name: Name of the system attribute (e.g., 'interaction_handler')

        Returns:
            The requested system, or None if not found
        """
        return getattr(self._engine, system_name, None)

    def get_agent_by_id(self, agent_id: str) -> Optional['Agent']:
        """
        Find an agent by ID.

        Args:
            agent_id: The agent's unique identifier

        Returns:
            Agent instance or None if not found
        """
        # Use cached lookup if available, otherwise delegate to engine
        if hasattr(self._engine, '_agent_cache'):
            return self._engine._agent_cache.get(agent_id)
        return self._engine._get_agent_by_id(agent_id)

    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log an event to the event system.

        Args:
            event_type: Type of event (e.g., 'resource_gathered')
            data: Event data dictionary
        """
        if self.event_logger:
            self.event_logger.log_event(event_type, data)


class ActionHandler(ABC):
    """
    Abstract base class for all action handlers.

    Handlers implement the Strategy pattern - each handler is a different
    strategy for executing a category of actions.

    Subclasses must implement:
    - can_handle(): Check if this handler processes an action type
    - execute(): Perform the action and return result
    - validate(): Check if action can be performed
    """

    def __init__(self, context: ActionContext):
        """
        Initialize handler with access to simulation systems.

        Args:
            context: ActionContext providing system access
        """
        self.context = context

    @abstractmethod
    def can_handle(self, action_type: 'ActionType') -> bool:
        """
        Check if this handler can process the given action type.

        Args:
            action_type: The type of action to check

        Returns:
            True if this handler can execute this action type
        """
        pass

    @abstractmethod
    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        """
        Execute the action and return standardized result.

        This method contains the core action logic. It should:
        1. Perform the action
        2. Update agent/world state as needed
        3. Log events
        4. Return standardized result

        Args:
            agent: The agent performing the action
            action: The action to execute

        Returns:
            ActionResult with success status, emotional impact, and metadata
        """
        pass

    @abstractmethod
    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        """
        Validate if action can be performed.

        This is called before execute() to check preconditions:
        - Agent is alive
        - Has required resources
        - Has required skills
        - Location/timing is valid

        Args:
            agent: The agent attempting the action
            action: The action to validate

        Returns:
            (can_execute: bool, reason: str)
            - If can_execute is True, reason is empty
            - If can_execute is False, reason explains why
        """
        pass

    def get_required_systems(self) -> List[str]:
        """
        Return list of required system dependencies.

        This is used for documentation and validation - ensuring
        all required systems are initialized before handler use.

        Returns:
            List of system attribute names (e.g., ['world', 'interaction_handler'])
        """
        return ['world', 'event_logger']

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<{self.__class__.__name__}>"


class ActionHandlerRegistry:
    """
    Manages registration and dispatch of action handlers.

    Uses Chain of Responsibility pattern - queries each handler in sequence
    until one claims responsibility for the action type.

    Features:
    - Handler registration
    - Cached lookup for performance
    - Coverage validation (ensure all action types have handlers)
    """

    def __init__(self):
        """Initialize empty registry"""
        self._handlers: List[ActionHandler] = []
        self._cache: Dict['ActionType', ActionHandler] = {}

    def register(self, handler: ActionHandler) -> None:
        """
        Register a new action handler.

        Args:
            handler: The handler instance to register
        """
        self._handlers.append(handler)
        # Clear cache when new handlers are registered
        self._cache.clear()

    def register_multiple(self, handlers: List[ActionHandler]) -> None:
        """
        Register multiple handlers at once.

        Args:
            handlers: List of handler instances
        """
        self._handlers.extend(handlers)
        self._cache.clear()

    def get_handler(self, action_type: 'ActionType') -> Optional[ActionHandler]:
        """
        Find appropriate handler for action type.

        Uses caching for performance - first lookup is O(n), subsequent
        lookups for same action type are O(1).

        Args:
            action_type: The type of action to find handler for

        Returns:
            Handler instance if found, None otherwise
        """
        # Check cache first
        if action_type in self._cache:
            return self._cache[action_type]

        # Search handlers using Chain of Responsibility
        for handler in self._handlers:
            if handler.can_handle(action_type):
                self._cache[action_type] = handler
                return handler

        return None

    def validate_coverage(self) -> Dict[str, List['ActionType']]:
        """
        Verify all action types have handlers.

        This is useful for testing and validation - ensures no action
        types are left unhandled after refactoring.

        Returns:
            Dictionary with 'covered' and 'uncovered' action type lists
        """
        from agents.agent import ActionType

        covered = []
        uncovered = []

        for action_type in ActionType:
            if self.get_handler(action_type):
                covered.append(action_type)
            else:
                uncovered.append(action_type)

        return {
            'covered': sorted(covered, key=lambda x: x.name),
            'uncovered': sorted(uncovered, key=lambda x: x.name)
        }

    def get_coverage_stats(self) -> Dict[str, Any]:
        """
        Get coverage statistics.

        Returns:
            Statistics about handler coverage
        """
        coverage = self.validate_coverage()
        total = len(coverage['covered']) + len(coverage['uncovered'])

        return {
            'total_action_types': total,
            'covered_count': len(coverage['covered']),
            'uncovered_count': len(coverage['uncovered']),
            'coverage_percentage': (len(coverage['covered']) / total * 100) if total > 0 else 0,
            'covered': [at.name for at in coverage['covered']],
            'uncovered': [at.name for at in coverage['uncovered']]
        }

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<ActionHandlerRegistry: {len(self._handlers)} handlers registered>"


class DelegatingActionHandler(ActionHandler):
    """
    Convenience base class for handlers that delegate to existing systems.

    Many handlers simply delegate to methods in interaction_handler or other
    existing systems. This base class provides common delegation patterns.
    """

    def delegate_to_system(
        self,
        system_name: str,
        method_name: str,
        *args,
        **kwargs
    ) -> ActionResult:
        """
        Delegate action to a method on an existing system.

        Args:
            system_name: Name of the system (e.g., 'interaction_handler')
            method_name: Method to call on the system
            *args: Positional arguments to pass
            **kwargs: Keyword arguments to pass

        Returns:
            ActionResult from the delegated method
        """
        system = self.context.get_system(system_name)
        if not system:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message=f"System '{system_name}' not available"
            )

        method = getattr(system, method_name, None)
        if not method:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message=f"Method '{method_name}' not found on '{system_name}'"
            )

        try:
            # Call the method and get legacy dict result
            result_dict = method(*args, **kwargs)

            # Convert to ActionResult
            return ActionResult.from_dict(result_dict)
        except Exception as e:
            return ActionResult(
                success=False,
                emotional_impact=-0.1,
                message=f"Error executing {system_name}.{method_name}: {str(e)}"
            )


# Validation helpers for common checks

def validate_agent_alive(agent: 'Agent') -> tuple[bool, str]:
    """Check if agent is alive"""
    if not agent.alive:
        return False, "Agent is dead"
    return True, ""


def validate_agent_energy(agent: 'Agent', min_energy: float = 0.1) -> tuple[bool, str]:
    """Check if agent has minimum energy (derived from HUNGER and SLEEP needs)"""
    from engine.psychology import NeedType

    # Energy is derived from physiological needs - if they're too high (unsatisfied), energy is low
    hunger_level = agent.needs.needs.get(NeedType.HUNGER, type('obj', (), {'level': 0.5})()).level
    sleep_level = agent.needs.needs.get(NeedType.SLEEP, type('obj', (), {'level': 0.5})()).level

    # Use the agent's actual energy stat (0-100). The old formula derived energy
    # from hunger, so a hungry agent had 0% energy and could not gather food:
    # a death spiral. Fall back to the derived value only if the stat is missing.
    if hasattr(agent, 'energy'):
        energy = max(0.0, min(1.0, agent.energy / 100.0))
    else:
        energy = 1.0 - ((hunger_level + sleep_level) / 2.0)

    if energy < min_energy:
        return False, f"Not enough energy (has {energy:.1%}, needs {min_energy:.0%})"
    return True, ""


def validate_agent_inventory(agent: 'Agent', required_items: Dict[str, int]) -> tuple[bool, str]:
    """Check if agent has required items in inventory"""
    for item_name, required_count in required_items.items():
        actual_count = agent.inventory.resources.get(item_name, 0)
        if actual_count < required_count:
            return False, f"Missing {item_name} (has {actual_count}, needs {required_count})"
    return True, ""


def combine_validations(*validations: tuple[bool, str]) -> tuple[bool, str]:
    """
    Combine multiple validation results.

    Returns the first failing validation, or (True, "") if all pass.
    """
    for can_execute, reason in validations:
        if not can_execute:
            return can_execute, reason
    return True, ""
