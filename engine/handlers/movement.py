"""
Movement Action Handler - Handles agent movement and exploration actions.

This handler manages all movement-related actions including:
- MOVE: Direct movement to a specific location
- EXPLORE: Exploratory movement to discover new areas

The handler validates that agents are alive and have sufficient energy before
allowing movement actions to proceed.
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


class MovementActionHandler(ActionHandler):
    """
    Handles movement and exploration actions.

    This handler processes ActionType.MOVE and ActionType.EXPLORE by updating
    the agent's location based on the target position specified in the action.

    Movement Mechanics:
    - Agents move toward a target position at a fixed speed (2.0 units per tick)
    - If target is within movement range, agent arrives at exact position
    - If target is further, agent moves 2.0 units closer

    Validation Requirements:
    - Agent must be alive
    - Agent must have sufficient energy (minimum 10%)

    Energy Costs:
    - Movement actions have minimal energy cost (handled by agent.update())
    - No explicit energy deduction in this handler

    Examples:
        >>> handler = MovementActionHandler(context)
        >>> action = Action(ActionType.MOVE, target_position=Position(10, 20))
        >>> result = handler.execute(agent, action)
        >>> print(result.success)  # True if agent moved successfully
    """

    # Movement speed in units per tick
    MOVEMENT_SPEED = 2.0

    # Minimum energy required for movement (as fraction 0-1)
    MIN_ENERGY_FOR_MOVEMENT = 0.1

    def can_handle(self, action_type: ActionType) -> bool:
        """
        Check if this handler can process the given action type.

        Args:
            action_type: The type of action to check

        Returns:
            True if action_type is MOVE or EXPLORE, False otherwise
        """
        return action_type in [ActionType.MOVE, ActionType.EXPLORE]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        """
        Validate if the agent can perform the movement action.

        Checks:
        1. Agent is alive
        2. Agent has sufficient energy (at least 10%)
        3. Action has a valid target_position (optional but recommended)

        Args:
            agent: The agent attempting to move
            action: The movement action to validate

        Returns:
            Tuple of (can_execute, reason):
            - (True, "") if validation passes
            - (False, reason_string) if validation fails

        Examples:
            >>> can_execute, reason = handler.validate(agent, action)
            >>> if not can_execute:
            ...     print(f"Cannot move: {reason}")
        """
        # Check if agent is alive
        alive_valid = validate_agent_alive(agent)

        # Check if agent has sufficient energy
        energy_valid = validate_agent_energy(agent, self.MIN_ENERGY_FOR_MOVEMENT)

        # Combine validations - returns first failure or (True, "") if all pass
        validation_result = combine_validations(alive_valid, energy_valid)

        # If basic validations pass, check for target position (warning only)
        if validation_result[0] and not action.target_position:
            # Movement without target is allowed but ineffective
            # This will result in agent staying in place
            pass

        return validation_result

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        """
        Execute the movement action.

        Updates the agent's location by moving toward the target position
        at the configured movement speed. If no target position is specified,
        the agent remains stationary.

        Movement Algorithm:
        1. Check if action has a target_position
        2. If yes, move agent toward target at MOVEMENT_SPEED units per tick
        3. Use Position.move_toward() to calculate new position
        4. Update agent.location to new position

        Args:
            agent: The agent performing the movement
            action: The movement action containing target_position

        Returns:
            ActionResult with:
            - success: True if movement occurred (even if no target)
            - emotional_impact: 0.0 (movement is neutral)
            - message: Description of movement or lack thereof
            - metadata: Dictionary with movement details (old_pos, new_pos, distance)

        Examples:
            >>> action = Action(ActionType.MOVE, target_position=Position(50, 50))
            >>> result = handler.execute(agent, action)
            >>> print(result.metadata['distance_traveled'])
        """
        # Store original position for metadata
        old_position = agent.location

        # Check if action has a target position
        if action.target_position:
            # Move agent toward target position at configured speed
            # Straight toward it, stopping at the shore (water isn't walkable)
            new_position = self.context.world.map.walk_line(
                agent.location, action.target_position, self.MOVEMENT_SPEED)

            # Update agent's location
            agent.location = new_position

            # Calculate distance traveled
            distance_traveled = old_position.distance_to(new_position)

            # Determine if agent reached destination
            reached_destination = (
                new_position.x == action.target_position.x and
                new_position.y == action.target_position.y
            )

            # Build result message
            if reached_destination:
                message = f"Reached destination ({new_position.x:.1f}, {new_position.y:.1f})"
            else:
                remaining_distance = new_position.distance_to(action.target_position)
                message = (
                    f"Moved {distance_traveled:.1f} units toward target "
                    f"({remaining_distance:.1f} remaining)"
                )

            return ActionResult(
                success=True,
                emotional_impact=0.0,
                message=message,
                metadata={
                    'action_type': action.action_type.value,
                    'old_position': {'x': old_position.x, 'y': old_position.y},
                    'new_position': {'x': new_position.x, 'y': new_position.y},
                    'target_position': {
                        'x': action.target_position.x,
                        'y': action.target_position.y
                    },
                    'distance_traveled': distance_traveled,
                    'reached_destination': reached_destination,
                }
            )
        else:
            # No target position - agent stays in place
            return ActionResult(
                success=True,
                emotional_impact=0.0,
                message="No movement (no target position specified)",
                metadata={
                    'action_type': action.action_type.value,
                    'position': {'x': old_position.x, 'y': old_position.y},
                    'distance_traveled': 0.0,
                }
            )

    def get_required_systems(self) -> list[str]:
        """
        Return list of required system dependencies.

        Movement handler only requires basic world access for position validation,
        which is provided by the base ActionContext.

        Returns:
            List of required system attribute names
        """
        return ['world']
