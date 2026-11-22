"""
Governance Action Handler - Handles agent political and governance actions.

This handler manages all governance-related actions including:
- GOVERN: Forming governments and establishing political power
- MAKE_LAW: Proposing and creating laws within governments
- VOTE: Voting on laws and elections

These actions enable agents to create political structures, establish rules,
and participate in collective decision-making.
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


class GovernanceHandler(ActionHandler):
    """Handles political and governance actions for agents."""

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [ActionType.GOVERN, ActionType.MAKE_LAW, ActionType.VOTE]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive_valid = validate_agent_alive(agent)
        if not alive_valid[0]:
            return alive_valid

        if action.action_type == ActionType.GOVERN:
            charisma = agent.personality.charisma if hasattr(agent.personality, 'charisma') else 0.5
            governance_manager = self.context.get_system('governance_manager')
            power = governance_manager.political_power.get(agent.id, 0.0) if governance_manager else 0.0
            if charisma < 0.5 and power < 0.3:
                return False, "Not influential enough to govern"

        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from world.governance import GovernmentType
        from engine.events import EventCategory, EventImportance
        from engine.psychology import EmotionType

        governance_manager = self.context.get_system('governance_manager')
        if not governance_manager:
            return ActionResult(success=False, emotional_impact=0.0, message="Governance system unavailable")

        current_tick = self.context.current_tick

        if action.action_type == ActionType.GOVERN:
            # Determine government type
            # (there is no "dominance" trait; this used to raise AttributeError,
            # so no government could ever be founded)
            if agent.personality.aggression > 0.7:
                gov_type = GovernmentType.STRONGMAN
            elif agent.personality.conscientiousness > 0.7:
                gov_type = GovernmentType.COUNCIL
            elif agent.personality.openness > 0.7:
                gov_type = GovernmentType.DEMOCRACY
            else:
                gov_type = GovernmentType.OLIGARCHY

            gov_name = action.parameters.get('name', f"{agent.name}'s Government") if action.parameters else f"{agent.name}'s Government"

            government = governance_manager.agent_forms_government(
                founder_id=agent.id,
                name=gov_name,
                gov_type=gov_type
            )

            logger.info(f"🏛️ {agent.name} formed {gov_name} ({gov_type.value})")

            agent.emotions.trigger_emotion(EmotionType.PRIDE, 0.8)
            agent.emotions.trigger_emotion(EmotionType.JOY, 0.6)
            agent.needs.satisfy_need(NeedType.STATUS, 0.5)

            return ActionResult(
                success=True,
                emotional_impact=0.7,
                message=f"Formed {gov_name}",
                metadata={'government_id': government.id, 'type': gov_type.value}
            )

        elif action.action_type == ActionType.MAKE_LAW:
            params = action.parameters if action.parameters else {}
            government_id = params.get('government_id')
            law_name = params.get('law_name', 'Untitled Law')
            law_description = params.get('description', '')
            prohibition = params.get('prohibition')
            requirement = params.get('requirement')

            if not government_id:
                for gov_id, gov in governance_manager.governments.items():
                    if agent.id in gov.citizens:
                        government_id = gov_id
                        break

            if not government_id:
                return ActionResult(success=False, emotional_impact=-0.1, message="Not part of any government")

            law = governance_manager.agent_creates_law(
                creator_id=agent.id,
                government_id=government_id,
                name=law_name,
                description=law_description,
                prohibition=prohibition,
                requirement=requirement
            )

            if not law:
                return ActionResult(success=False, emotional_impact=-0.2, message="Insufficient authority to make laws")

            logger.info(f"📜 {agent.name} proposed law: {law_name}")

            agent.emotions.trigger_emotion(EmotionType.PRIDE, 0.5)
            agent.needs.satisfy_need(NeedType.STATUS, 0.3)

            return ActionResult(
                success=True,
                emotional_impact=0.4,
                message=f"Proposed law: {law_name}",
                metadata={'law_id': law.id, 'law_name': law_name}
            )

        elif action.action_type == ActionType.VOTE:
            params = action.parameters if action.parameters else {}
            vote_target = params.get('vote_target')
            vote_choice = params.get('choice')

            if not vote_target:
                return ActionResult(success=False, emotional_impact=0.0, message="No vote target specified")

            # Try voting on law
            if vote_target in governance_manager.laws:
                support = vote_choice if isinstance(vote_choice, bool) else vote_choice == 'yes'
                governance_manager.vote_on_law(agent.id, vote_target, support)
                law = governance_manager.laws[vote_target]
                vote_str = "supported" if support else "opposed"
                logger.info(f"🗳️ {agent.name} {vote_str} law: {law.name}")
                agent.needs.satisfy_need(NeedType.STATUS, 0.2)
                return ActionResult(success=True, emotional_impact=0.2, message=f"Voted on {law.name}", metadata={'vote_type': 'law'})

            # Try voting in election
            elif vote_target in governance_manager.elections:
                candidate_id = vote_choice if isinstance(vote_choice, str) else action.target_agent
                if not candidate_id:
                    return ActionResult(success=False, emotional_impact=0.0, message="No candidate specified")

                success = governance_manager.cast_vote(agent.id, vote_target, candidate_id)
                if success:
                    logger.info(f"🗳️ {agent.name} voted in election")
                    agent.needs.satisfy_need(NeedType.STATUS, 0.3)
                    return ActionResult(success=True, emotional_impact=0.2, message="Voted in election", metadata={'vote_type': 'election'})
                else:
                    return ActionResult(success=False, emotional_impact=-0.1, message="Cannot vote in this election")
            else:
                return ActionResult(success=False, emotional_impact=0.0, message="Invalid vote target")

        return ActionResult(success=False, emotional_impact=0.0, message="Unknown governance action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'governance_manager']
