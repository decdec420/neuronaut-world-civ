"""
Social Interaction Handler - Handles agent social and economic interactions.

This handler manages all social and economic interaction actions including:
- SOCIALIZE: Social interactions and friendship building
- SEEK_ROMANCE: Romantic interactions and relationship development
- TRADE: Economic trading between agents

The handler validates that agents are alive and have valid targets before
allowing social interactions to proceed.
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
from agents.agent import ActionType, Action

if TYPE_CHECKING:
    from agents.agent import Agent


class SocialInteractionHandler(ActionHandler):
    """
    Handles social and economic interaction actions.

    This handler processes ActionType.SOCIALIZE, ActionType.SEEK_ROMANCE,
    and ActionType.TRADE by delegating to the interaction_handler system.

    Action Details:

    SOCIALIZE:
    - Delegates to interaction_handler.handle_socialize()
    - Checks personality compatibility between agents
    - Updates relationships (friendship formation/strengthening)
    - Satisfies social needs (friendship, belonging)
    - Triggers positive/negative emotions based on compatibility
    - May trigger story creation for creative agents
    - Requires valid target_agent

    SEEK_ROMANCE:
    - Delegates to interaction_handler.handle_romance()
    - Checks attraction based on personality and needs
    - Updates romantic relationships
    - Satisfies romance and intimacy needs
    - Triggers love, lust, and joy emotions on success
    - Triggers sadness and shame on rejection
    - May trigger pregnancy for compatible pairs
    - May trigger reproduction in execute_action() if successful
    - Requires valid target_agent

    TRADE:
    - Delegates to interaction_handler.handle_trade()
    - Checks reputation and trust between agents
    - Negotiates prices based on learned value estimates
    - Executes trade through economy system
    - Updates reputation scores and relationships
    - Both agents learn from trade outcomes
    - Satisfies resource needs on success
    - Requires valid target_agent

    Validation Requirements:
    - Agent must be alive for all actions
    - Action must have a valid target_agent specified
    - Target agent must exist in the simulation

    Examples:
        >>> handler = SocialInteractionHandler(context)
        >>> action = Action(ActionType.SOCIALIZE, target_agent="agent_123")
        >>> result = handler.execute(agent, action)
        >>> print(result.success)  # True if agents successfully socialized

        >>> action = Action(ActionType.TRADE, target_agent="agent_456")
        >>> result = handler.execute(agent, action)
        >>> print(result.success)  # True if trade completed successfully
    """

    def can_handle(self, action_type: ActionType) -> bool:
        """
        Check if this handler can process the given action type.

        Args:
            action_type: The type of action to check

        Returns:
            True if action_type is SOCIALIZE, SEEK_ROMANCE, or TRADE, False otherwise
        """
        return action_type in [
            ActionType.SOCIALIZE,
            ActionType.SEEK_ROMANCE,
            ActionType.TRADE
        ]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        """
        Validate if the agent can perform the social interaction.

        Checks:
        1. Agent is alive (all actions)
        2. Action has a target_agent specified
        3. Target agent exists in the simulation

        Args:
            agent: The agent attempting the interaction
            action: The social interaction action to validate

        Returns:
            Tuple of (can_execute, reason):
            - (True, "") if validation passes
            - (False, reason_string) if validation fails

        Examples:
            >>> can_execute, reason = handler.validate(agent, action)
            >>> if not can_execute:
            ...     print(f"Cannot interact: {reason}")
        """
        # Check if agent is alive (required for all actions)
        alive_valid = validate_agent_alive(agent)

        if not alive_valid[0]:
            return alive_valid

        # Check if action has a target_agent specified
        if not action.target_agent:
            return False, "No target agent specified for social interaction"

        # Check if target agent exists in the simulation
        target = self.context.get_agent_by_id(action.target_agent)
        if not target:
            return False, f"Target agent not found: {action.target_agent}"

        # Check if target agent is alive
        target_alive_valid = validate_agent_alive(target)
        if not target_alive_valid[0]:
            return False, f"Target agent is dead: {target.name}"

        # A buyer with no room can't take anything home
        if action.action_type == ActionType.TRADE and agent.inventory.get_total_items() >= agent.inventory.capacity:
            return False, "Inventory full"

        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        """
        Execute the social interaction action.

        Processes SOCIALIZE, SEEK_ROMANCE, or TRADE actions by delegating
        to the appropriate interaction_handler method.

        SOCIALIZE Algorithm:
        1. Retrieve target agent from simulation
        2. Delegate to interaction_handler.handle_socialize()
        3. This checks compatibility, updates relationships, satisfies needs
        4. Returns result with emotional impact based on compatibility

        SEEK_ROMANCE Algorithm:
        1. Retrieve target agent from simulation
        2. Delegate to interaction_handler.handle_romance()
        3. This checks attraction, updates relationships, satisfies needs
        4. May trigger pregnancy for compatible pairs
        5. Returns result with reproduction_attempted flag if successful
        6. Note: execute_action() in simulation.py handles child creation

        TRADE Algorithm:
        1. Retrieve target agent from simulation
        2. Delegate to interaction_handler.handle_trade()
        3. This checks trust, negotiates price, executes trade
        4. Updates reputation and relationships
        5. Both agents learn from the trade outcome
        6. Returns result with trade details

        Args:
            agent: The agent performing the interaction
            action: The social interaction action containing target_agent

        Returns:
            ActionResult with:
            - success: True if interaction completed successfully
            - emotional_impact: Emotional effect (varies by action and outcome)
            - message: Description of what occurred
            - metadata: Dictionary with interaction-specific details

        Examples:
            >>> action = Action(ActionType.SOCIALIZE, target_agent="agent_123")
            >>> result = handler.execute(agent, action)
            >>> print(result.message)  # "Pleasant conversation" or "Awkward interaction"
        """
        import logging
        logger = logging.getLogger(__name__)

        # Get the interaction handler system
        interaction_handler = self.context.get_system('interaction_handler')

        if not interaction_handler:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message="Interaction handler not available",
                metadata={
                    'action_type': action.action_type.value,
                }
            )

        # Get target agent
        target = self.context.get_agent_by_id(action.target_agent)

        if not target:
            # This should have been caught by validate(), but handle gracefully
            return ActionResult(
                success=False,
                emotional_impact=-0.1,
                message=f"Target agent not found: {action.target_agent}",
                metadata={
                    'action_type': action.action_type.value,
                    'target_agent_id': action.target_agent,
                }
            )

        # Get current tick for event logging
        current_tick = self.context.current_tick

        # Delegate to appropriate interaction handler method
        if action.action_type == ActionType.SOCIALIZE:
            result_dict = interaction_handler.handle_socialize(
                agent, target, current_tick
            )

            logger.info(
                f"[{agent.name}] EXECUTED SOCIALIZE with {target.name}: "
                f"success={result_dict.get('success')}, "
                f"emotional_impact={result_dict.get('emotional_impact', 0.0):.2f}"
            )

            return ActionResult.from_dict(result_dict)

        elif action.action_type == ActionType.SEEK_ROMANCE:
            result_dict = interaction_handler.handle_romance(
                agent, target, current_tick
            )

            logger.info(
                f"[{agent.name}] EXECUTED SEEK_ROMANCE with {target.name}: "
                f"success={result_dict.get('success')}, "
                f"emotional_impact={result_dict.get('emotional_impact', 0.0):.2f}, "
                f"reproduction_attempted={result_dict.get('reproduction_attempted', False)}"
            )

            # Note: The reproduction_attempted flag is preserved in metadata
            # execute_action() in simulation.py will check this and handle
            # child creation through life_system.attempt_reproduction()
            return ActionResult.from_dict(result_dict)

        elif action.action_type == ActionType.TRADE:
            result_dict = interaction_handler.handle_trade(
                agent, target, current_tick
            )

            logger.info(
                f"[{agent.name}] EXECUTED TRADE with {target.name}: "
                f"success={result_dict.get('success')}, "
                f"emotional_impact={result_dict.get('emotional_impact', 0.0):.2f}"
            )

            return ActionResult.from_dict(result_dict)

        # Should never reach here due to can_handle() check, but return safe default
        return ActionResult(
            success=False,
            emotional_impact=0.0,
            message=f"Unknown social action type: {action.action_type}",
            metadata={
                'action_type': action.action_type.value,
            }
        )

    def get_required_systems(self) -> list[str]:
        """
        Return list of required system dependencies.

        Social interaction handler requires:
        - world: For basic world access
        - interaction_handler: For handling all social interaction delegation
        - relationship_manager: Used by interaction_handler for relationships
        - economy: Used by interaction_handler for trade execution

        Returns:
            List of required system attribute names
        """
        return ['world', 'interaction_handler']
