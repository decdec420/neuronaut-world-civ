"""
Combat Action Handler - Handles agent combat and conflict actions.

This handler manages the FIGHT action including:
- Initiating duels between agents
- Resolving combat with warfare_manager
- Applying emotional impacts based on outcomes
- Tracking casualties and victories

Combat provides conflict resolution and status competition between agents.
"""

from typing import TYPE_CHECKING
import logging

from engine.action_handlers import (
    ActionHandler,
    ActionResult,
    ActionContext,
    validate_agent_alive,
)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)


class CombatActionHandler(ActionHandler):
    """Handles combat actions for agents."""

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type == ActionType.FIGHT

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive_valid = validate_agent_alive(agent)
        if not alive_valid[0]:
            return alive_valid

        if not action.target_agent:
            return False, "No target specified"

        target = self.context.get_agent_by_id(action.target_agent)
        if not target or not target.alive:
            return False, "Target not found or dead"

        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from world.conflict import ConflictReason
        from engine.events import EventCategory, EventImportance
        from engine.psychology import EmotionType

        warfare_manager = self.context.get_system('warfare_manager')
        if not warfare_manager:
            return ActionResult(success=False, emotional_impact=0.0, message="Warfare system unavailable")

        target = self.context.get_agent_by_id(action.target_agent)
        if not target:
            return ActionResult(success=False, emotional_impact=0.0, message="Target not found")

        # Determine conflict reason
        params = action.parameters if action.parameters else {}
        reason = params.get('reason', ConflictReason.RESOURCES)
        if isinstance(reason, str):
            try:
                reason = ConflictReason(reason)
            except ValueError:
                reason = ConflictReason.RESOURCES

        current_tick = self.context.current_tick

        # Initiate duel
        conflict = warfare_manager.initiate_duel(agent.id, target.id, reason)
        logger.info(f"⚔️ {agent.name} initiated combat with {target.name} (reason: {reason.value})")

        # Resolve combat immediately
        agents_dict = {a.id: a for a in self.context.world.agents if a.alive}
        combat_result = warfare_manager.resolve_combat_turn(conflict.id, agents_dict)

        # Apply emotional impacts
        if combat_result.get('status') == 'ended':
            winner = combat_result.get('winner')

            if winner == 'side_a':
                # Agent won!
                agent.emotions.trigger_emotion(EmotionType.PRIDE, 0.7)
                agent.emotions.trigger_emotion(EmotionType.JOY, 0.5)
                agent.needs.satisfy_need(NeedType.STATUS, 0.4)
                agent.skills.learn_skill('combat', 0.1)

                target.emotions.trigger_emotion(EmotionType.SADNESS, 0.6)
                target.emotions.trigger_emotion(EmotionType.FEAR, 0.5)
                target.needs.satisfy_need(NeedType.SECURITY, -0.5)

                emotional_impact = 0.3
                logger.info(f"⚔️ {agent.name} defeated {target.name} in combat!")
            else:
                # Agent lost!
                agent.emotions.trigger_emotion(EmotionType.SADNESS, 0.6)
                agent.emotions.trigger_emotion(EmotionType.FEAR, 0.5)
                agent.needs.satisfy_need(NeedType.SECURITY, -0.5)

                target.emotions.trigger_emotion(EmotionType.PRIDE, 0.7)
                target.emotions.trigger_emotion(EmotionType.JOY, 0.5)
                target.needs.satisfy_need(NeedType.STATUS, 0.4)
                target.skills.learn_skill('combat', 0.1)

                emotional_impact = -0.4
                logger.info(f"⚔️ {target.name} defeated {agent.name} in combat!")

            casualties = combat_result.get('casualties', [])
            if agent.id in casualties:
                logger.warning(f"💀 {agent.name} died in combat!")
            if target.id in casualties:
                logger.warning(f"💀 {target.name} died in combat!")

            return ActionResult(
                success=True,
                emotional_impact=emotional_impact,
                message=f"Combat ended: {winner}",
                metadata={'combat_result': combat_result, 'winner': winner, 'casualties': casualties}
            )
        else:
            # Combat ongoing
            return ActionResult(
                success=True,
                emotional_impact=0.1,
                message="Combat ongoing",
                metadata={'combat_result': combat_result}
            )

    def get_required_systems(self) -> list[str]:
        return ['world', 'warfare_manager']
