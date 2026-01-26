"""
Survival Action Handler - Handles agent survival actions.

This handler manages all survival-related actions including:
- REST: Resting to restore energy and satisfy sleep need
- EAT: Consuming food to satisfy hunger
- DRINK: Consuming water to satisfy thirst

The handler validates that agents are alive and have necessary resources
before allowing survival actions to proceed.
"""

from typing import TYPE_CHECKING

from engine.action_handlers import (
    ActionHandler,
    ActionResult,
    ActionContext,
    DelegatingActionHandler,
    validate_agent_alive,
    combine_validations,
)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent


class SurvivalActionHandler(ActionHandler):
    """
    Handles survival actions for agents.

    This handler processes ActionType.REST, ActionType.EAT, and ActionType.DRINK
    actions that are essential for agent survival and well-being.

    Action Details:

    REST:
    - Delegates to interaction_handler.handle_rest()
    - Restores energy (adds 20.0, max 100.0)
    - Satisfies sleep need (50%)
    - Reduces stress (reduces by 0.2)
    - May trigger story creation for creative agents

    EAT:
    - Consumes 1 food from inventory
    - Satisfies hunger need (50%)
    - Positive emotional impact (0.3)
    - Fails if no food available

    DRINK:
    - Consumes 1 water from inventory
    - Satisfies thirst need (50%)
    - Positive emotional impact (0.3)
    - Fails if no water available

    Validation Requirements:
    - Agent must be alive for all actions
    - EAT requires food in inventory
    - DRINK requires water in inventory

    Examples:
        >>> handler = SurvivalActionHandler(context)
        >>> action = Action(ActionType.REST)
        >>> result = handler.execute(agent, action)
        >>> print(result.success)  # True if agent rested successfully

        >>> action = Action(ActionType.EAT)
        >>> result = handler.execute(agent, action)
        >>> print(result.success)  # True if agent had food and ate it
    """

    def can_handle(self, action_type: ActionType) -> bool:
        """
        Check if this handler can process the given action type.

        Args:
            action_type: The type of action to check

        Returns:
            True if action_type is REST, EAT, or DRINK, False otherwise
        """
        return action_type in [ActionType.REST, ActionType.EAT, ActionType.DRINK]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        """
        Validate if the agent can perform the survival action.

        Checks:
        1. Agent is alive (all actions)
        2. Agent has food in inventory (EAT only)
        3. Agent has water in inventory (DRINK only)

        Args:
            agent: The agent attempting the action
            action: The survival action to validate

        Returns:
            Tuple of (can_execute, reason):
            - (True, "") if validation passes
            - (False, reason_string) if validation fails

        Examples:
            >>> can_execute, reason = handler.validate(agent, eat_action)
            >>> if not can_execute:
            ...     print(f"Cannot eat: {reason}")
        """
        # Check if agent is alive (required for all actions)
        alive_valid = validate_agent_alive(agent)

        # For REST, only need to be alive
        if action.action_type == ActionType.REST:
            return alive_valid

        # For EAT, also need food in inventory
        elif action.action_type == ActionType.EAT:
            if not alive_valid[0]:
                return alive_valid

            if not agent.inventory.has_item('food'):
                return False, "No food in inventory"

            return True, ""

        # For DRINK, also need water in inventory
        elif action.action_type == ActionType.DRINK:
            if not alive_valid[0]:
                return alive_valid

            if not agent.inventory.has_item('water'):
                return False, "No water in inventory"

            return True, ""

        # Should never reach here, but return safe default
        return False, "Unknown action type"

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        """
        Execute the survival action.

        Processes REST, EAT, or DRINK actions, updating agent state accordingly.

        REST Algorithm:
        1. Delegate to interaction_handler.handle_rest()
        2. This restores energy, satisfies sleep, reduces stress
        3. May trigger story creation for creative agents

        EAT Algorithm:
        1. Verify food is available in inventory
        2. Remove 1 food from inventory
        3. Satisfy hunger need by 50%
        4. Log the eating action with before/after states

        DRINK Algorithm:
        1. Verify water is available in inventory
        2. Remove 1 water from inventory
        3. Satisfy thirst need by 50%

        Args:
            agent: The agent performing the action
            action: The survival action to execute

        Returns:
            ActionResult with:
            - success: True if action completed successfully
            - emotional_impact: Emotional effect (0.1 for rest, 0.3 for eat/drink, -0.1 for failure)
            - message: Description of what occurred
            - metadata: Dictionary with action-specific details

        Examples:
            >>> action = Action(ActionType.REST)
            >>> result = handler.execute(agent, action)
            >>> print(result.message)  # "Rested and recovered"
        """
        import logging
        logger = logging.getLogger(__name__)

        if action.action_type == ActionType.REST:
            # Delegate to interaction_handler for rest logic
            # This handles energy restoration, sleep satisfaction, stress reduction,
            # and potential story creation for creative agents
            interaction_handler = self.context.get_system('interaction_handler')

            if not interaction_handler:
                return ActionResult(
                    success=False,
                    emotional_impact=0.0,
                    message="Interaction handler not available"
                )

            result_dict = interaction_handler.handle_rest(agent)
            return ActionResult.from_dict(result_dict)

        elif action.action_type == ActionType.EAT:
            # Consume food to satisfy hunger
            if agent.inventory.has_item('food'):
                # Capture state before eating for logging
                food_before = agent.inventory.items.get('food', 0)
                hunger_before = agent.needs.needs[NeedType.HUNGER].level

                # Consume the food
                agent.inventory.remove_item('food', 1)
                agent.needs.satisfy_need(NeedType.HUNGER, 0.5)  # Eating satisfies 50% of hunger

                # Capture state after eating
                hunger_after = agent.needs.needs[NeedType.HUNGER].level

                # Log the action with detailed state changes
                logger.info(
                    f"[{agent.name}] EXECUTED EAT: food {food_before}→{food_before-1}, "
                    f"hunger {hunger_before:.2f}→{hunger_after:.2f}"
                )

                return ActionResult(
                    success=True,
                    emotional_impact=0.3,
                    message=f'{agent.name} ate food',
                    metadata={
                        'action_type': action.action_type.value,
                        'food_before': food_before,
                        'food_after': food_before - 1,
                        'hunger_before': hunger_before,
                        'hunger_after': hunger_after,
                        'hunger_satisfied': 0.5,
                    }
                )
            else:
                # No food available
                logger.warning(f"[{agent.name}] FAILED TO EAT: No food in inventory!")

                return ActionResult(
                    success=False,
                    emotional_impact=-0.1,
                    message='No food to eat',
                    metadata={
                        'action_type': action.action_type.value,
                        'reason': 'no_food_in_inventory',
                    }
                )

        elif action.action_type == ActionType.DRINK:
            # Consume water to satisfy thirst
            if agent.inventory.has_item('water'):
                # Capture state before drinking for metadata
                water_before = agent.inventory.items.get('water', 0)
                thirst_before = agent.needs.needs[NeedType.THIRST].level

                # Consume the water
                agent.inventory.remove_item('water', 1)
                agent.needs.satisfy_need(NeedType.THIRST, 0.5)  # Drinking satisfies 50% of thirst

                # Capture state after drinking
                thirst_after = agent.needs.needs[NeedType.THIRST].level

                return ActionResult(
                    success=True,
                    emotional_impact=0.3,
                    message=f'{agent.name} drank water',
                    metadata={
                        'action_type': action.action_type.value,
                        'water_before': water_before,
                        'water_after': water_before - 1,
                        'thirst_before': thirst_before,
                        'thirst_after': thirst_after,
                        'thirst_satisfied': 0.5,
                    }
                )
            else:
                # No water available
                return ActionResult(
                    success=False,
                    emotional_impact=-0.1,
                    message='No water to drink',
                    metadata={
                        'action_type': action.action_type.value,
                        'reason': 'no_water_in_inventory',
                    }
                )

        # Should never reach here, but return safe default
        return ActionResult(
            success=False,
            emotional_impact=0.0,
            message=f"Unknown survival action type: {action.action_type}",
            metadata={
                'action_type': action.action_type.value,
            }
        )

    def get_required_systems(self) -> list[str]:
        """
        Return list of required system dependencies.

        Survival handler requires:
        - world: For basic world access
        - interaction_handler: For handling REST action delegation

        Returns:
            List of required system attribute names
        """
        return ['world', 'interaction_handler']
