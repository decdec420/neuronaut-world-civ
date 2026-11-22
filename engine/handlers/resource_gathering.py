"""
Resource Gathering Action Handler - Handles agent resource gathering actions.

This handler manages all resource gathering actions including:
- GATHER_FOOD: Gathering food from the environment with pathfinding
- GATHER_MATERIALS: Gathering building materials (stone, wood, clay, etc.)
- CHOP_WOOD: Specialized wood gathering from trees
- MINE: Mining stone and minerals with tool requirements
- HUNT: Hunting animals for food with skill-based success
- GATHER_WATER: Gathering water with pathfinding and memory

These are critical actions that agents perform constantly to survive and build
civilization. The handler validates energy requirements and delegates to the
interaction_handler for execution.
"""

from typing import TYPE_CHECKING

from engine.action_handlers import (
    ActionHandler,
    ActionResult,
    ActionContext,
    DelegatingActionHandler,
    validate_agent_alive,
    validate_agent_energy,
    combine_validations,
)
from agents.agent import ActionType, Action

if TYPE_CHECKING:
    from agents.agent import Agent


class ResourceGatheringHandler(ActionHandler):
    """
    Handles resource gathering actions for agents.

    This handler processes all resource gathering action types by delegating to
    specialized methods in the interaction_handler. Each gathering action has
    different mechanics, tool requirements, and success conditions.

    Action Details:

    GATHER_FOOD:
    - Delegates to interaction_handler.handle_gather_food()
    - Uses resource memory and pathfinding
    - Finds and harvests food resources
    - Returns food to inventory
    - Requires target_position parameter

    GATHER_MATERIALS:
    - Delegates to interaction_handler.handle_gather_materials()
    - Gathers building materials (stone, wood, clay, metal_ore, etc.)
    - Priority-based selection of materials
    - Tool efficiency bonuses apply
    - Creates knowledge about gathering techniques
    - Critical for civilization building

    CHOP_WOOD:
    - Delegates to interaction_handler.handle_chop_wood()
    - Specialized wood gathering from trees
    - Stone tools provide 1.8x efficiency multiplier
    - Teaches gathering skill
    - Satisfies resource need
    - Restores small amount of energy

    MINE:
    - Delegates to interaction_handler.handle_mine()
    - Mines stone, metal_ore, iron_ore, or clay
    - Priority-based selection (stone > metal_ore > iron_ore > clay)
    - Advanced materials require stone tools
    - Tool efficiency bonuses (up to 1.6x for ore mining)
    - Teaches gathering skill
    - Satisfies resource need

    HUNT:
    - Delegates to interaction_handler.handle_hunt()
    - Skill-based hunting with 40-90% success rate
    - Tools improve success chance (stone +15%, wood +10%)
    - Successful hunt yields 8-15 food
    - Teaches hunting skill
    - Satisfies hunger and achievement needs
    - Restores energy from eating fresh meat

    GATHER_WATER:
    - Delegates to interaction_handler.handle_gather_water()
    - Uses resource memory and pathfinding
    - Finds and harvests water resources
    - Returns water to inventory
    - Requires current_tick for memory system

    Validation Requirements:
    - Agent must be alive for all actions
    - Agent must have sufficient energy (minimum 10%)

    Energy Costs:
    - Energy is consumed by agent.update() during the tick
    - Some actions restore energy (hunt, chop_wood, mine)
    - No explicit energy deduction in this handler

    Examples:
        >>> handler = ResourceGatheringHandler(context)
        >>> action = Action(ActionType.GATHER_FOOD, target_position=Position(10, 20))
        >>> result = handler.execute(agent, action)
        >>> print(result.success)  # True if food was gathered

        >>> action = Action(ActionType.HUNT)
        >>> result = handler.execute(agent, action)
        >>> print(result.message)  # "Successfully hunted and gained 12 food!"
    """

    # Minimum energy required for resource gathering (as fraction 0-1)
    MIN_ENERGY_FOR_GATHERING = 0.1

    def can_handle(self, action_type: ActionType) -> bool:
        """
        Check if this handler can process the given action type.

        Args:
            action_type: The type of action to check

        Returns:
            True if action_type is any resource gathering action, False otherwise
        """
        return action_type in [
            ActionType.GATHER_FOOD,
            ActionType.GATHER_MATERIALS,
            ActionType.CHOP_WOOD,
            ActionType.MINE,
            ActionType.HUNT,
            ActionType.GATHER_WATER,
        ]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        """
        Validate if the agent can perform the resource gathering action.

        Checks:
        1. Agent is alive
        2. Agent has sufficient energy (at least 10%)

        Note: Specific resource requirements (e.g., tools for mining ore) are
        checked by the interaction_handler methods, not here.

        Args:
            agent: The agent attempting to gather resources
            action: The gathering action to validate

        Returns:
            Tuple of (can_execute, reason):
            - (True, "") if validation passes
            - (False, reason_string) if validation fails

        Examples:
            >>> can_execute, reason = handler.validate(agent, action)
            >>> if not can_execute:
            ...     print(f"Cannot gather: {reason}")
        """
        # Check if agent is alive
        alive_valid = validate_agent_alive(agent)

        # Check if agent has sufficient energy
        # Food and water must always be reachable, even when exhausted
        if action.action_type.value in ('gather_food', 'gather_water', 'hunt'):
            energy_valid = (True, "")
        else:
            energy_valid = validate_agent_energy(agent, self.MIN_ENERGY_FOR_GATHERING)
            # Materials can't be carried once the inventory is full. Reject here so
            # the agent picks something else instead of failing every tick (food and
            # water are eaten/drunk on the spot, so they are never blocked).
            if agent.inventory.get_total_items() >= agent.inventory.capacity:
                return combine_validations(alive_valid, (False, "Inventory full"))

        # Combine validations - returns first failure or (True, "") if all pass
        return combine_validations(alive_valid, energy_valid)

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        """
        Execute the resource gathering action.

        Delegates to the appropriate interaction_handler method based on the
        action type. Each method has its own unique mechanics:

        - GATHER_FOOD: Pathfinding + memory-based food gathering
        - GATHER_MATERIALS: Priority-based material selection with tool bonuses
        - CHOP_WOOD: Tree harvesting with stone axe efficiency
        - MINE: Mineral extraction with tool requirements
        - HUNT: Skill-based hunting with probability mechanics
        - GATHER_WATER: Pathfinding + memory-based water gathering

        Args:
            agent: The agent performing the gathering action
            action: The gathering action to execute

        Returns:
            ActionResult with:
            - success: True if resources were gathered
            - emotional_impact: Emotional effect (positive on success, negative on failure)
            - message: Description of what was gathered or why it failed
            - metadata: Action-specific details (amounts, resources, skills, etc.)

        Raises:
            Returns failure result if interaction_handler is not available

        Examples:
            >>> action = Action(ActionType.CHOP_WOOD)
            >>> result = handler.execute(agent, action)
            >>> print(result.metadata.get('action_type'))  # 'chop_wood'
            >>> print(result.message)  # "Chopped 8 wood from trees"

            >>> action = Action(ActionType.MINE)
            >>> result = handler.execute(agent, action)
            >>> if result.success:
            ...     print(f"Mined {result.message}")
        """
        import logging
        logger = logging.getLogger(__name__)

        # Get interaction_handler from context
        interaction_handler = self.context.get_system('interaction_handler')

        if not interaction_handler:
            logger.error("Interaction handler not available for resource gathering")
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message="Interaction handler not available",
                metadata={
                    'action_type': action.action_type.value,
                    'reason': 'system_not_available',
                }
            )

        # Delegate to appropriate interaction_handler method based on action type
        try:
            if action.action_type == ActionType.GATHER_FOOD:
                # Food gathering requires target position and current tick
                result_dict = interaction_handler.handle_gather_food(
                    agent,
                    action.target_position,
                    self.context.current_tick
                )

            elif action.action_type == ActionType.GATHER_MATERIALS:
                # Material gathering requires current tick for knowledge system
                result_dict = interaction_handler.handle_gather_materials(
                    agent,
                    self.context.current_tick
                )

            elif action.action_type == ActionType.CHOP_WOOD:
                # Wood chopping is a simple agent-only action
                result_dict = interaction_handler.handle_chop_wood(agent)

            elif action.action_type == ActionType.MINE:
                # Mining is a simple agent-only action
                result_dict = interaction_handler.handle_mine(agent)

            elif action.action_type == ActionType.HUNT:
                # Hunting is a simple agent-only action
                result_dict = interaction_handler.handle_hunt(agent)

            elif action.action_type == ActionType.GATHER_WATER:
                # Water gathering requires current tick for memory and pathfinding
                result_dict = interaction_handler.handle_gather_water(
                    agent,
                    self.context.current_tick
                )

            else:
                # Should never reach here due to can_handle check, but safety fallback
                logger.warning(
                    f"Unknown resource gathering action type: {action.action_type}"
                )
                return ActionResult(
                    success=False,
                    emotional_impact=0.0,
                    message=f"Unknown resource gathering action: {action.action_type.value}",
                    metadata={
                        'action_type': action.action_type.value,
                        'reason': 'unknown_action_type',
                    }
                )

            # Convert legacy dict result to ActionResult
            result = ActionResult.from_dict(result_dict)

            # Ensure action_type is in metadata for tracking
            if 'action_type' not in result.metadata:
                result.metadata['action_type'] = action.action_type.value

            # Log successful gathering for debugging
            if result.success:
                logger.debug(
                    f"[{agent.name}] Successfully executed {action.action_type.value}: "
                    f"{result.message}"
                )
            else:
                logger.debug(
                    f"[{agent.name}] Failed {action.action_type.value}: {result.message}"
                )

            return result

        except Exception as e:
            # Catch any unexpected errors during delegation
            logger.error(
                f"Error executing {action.action_type.value} for {agent.name}: {e}",
                exc_info=True
            )
            return ActionResult(
                success=False,
                emotional_impact=-0.1,
                message=f"Error during {action.action_type.value}: {str(e)}",
                metadata={
                    'action_type': action.action_type.value,
                    'reason': 'execution_error',
                    'error': str(e),
                }
            )

    def get_required_systems(self) -> list[str]:
        """
        Return list of required system dependencies.

        Resource gathering handler requires:
        - world: For resource pools, pathfinding, and resource locations
        - interaction_handler: For delegating all gathering actions
        - event_logger: For logging resource gathering events (optional)

        Returns:
            List of required system attribute names
        """
        return ['world', 'interaction_handler']
