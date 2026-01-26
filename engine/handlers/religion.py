"""Religion Action Handler - Handles agent religious and spiritual actions."""

from typing import TYPE_CHECKING
import random
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


class ReligionHandler(ActionHandler):
    """Handles religious and spiritual actions for agents."""

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [ActionType.PRAY, ActionType.WORSHIP, ActionType.PERFORM_RITUAL, ActionType.BUILD_TEMPLE]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive_valid = validate_agent_alive(agent)
        if not alive_valid[0]:
            return alive_valid

        if action.action_type == ActionType.BUILD_TEMPLE:
            if not (agent.inventory.has_item('stone') and agent.inventory.has_item('wood')):
                return False, "Need stone and wood for temple"

        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from world.religion import ReligionType, RitualType, DeityDomain

        religion = self.context.get_system('religion')
        if not religion:
            return ActionResult(success=False, emotional_impact=0.0, message="Religion system unavailable")

        current_tick = self.context.current_tick

        if action.action_type == ActionType.PRAY:
            agent_religion = religion.get_agent_religion(agent.id)
            if not agent_religion and random.random() < 0.1:
                # Found simple animistic belief
                deity_domain = random.choice(list(DeityDomain))
                deity = religion.create_deity(f"{deity_domain.value.title()} Spirit", deity_domain, agent.id)
                agent_religion = religion.found_religion(agent.id, agent.name, ReligionType.ANIMISM, current_tick)
                agent_religion.deities.append(deity.id)
                logger.info(f"🙏 {agent.name} began worshipping {deity.name}!")
                agent.needs.satisfy_need(NeedType.MEANING, 0.4)
                return ActionResult(success=True, emotional_impact=0.35, message=f"Founded faith in {deity.name}")

            agent.needs.satisfy_need(NeedType.MEANING, 0.2)
            agent.needs.satisfy_need(NeedType.SECURITY, 0.1)
            return ActionResult(success=True, emotional_impact=0.2, message="Prayed for guidance")

        elif action.action_type == ActionType.WORSHIP:
            agent_religion = religion.get_agent_religion(agent.id)
            if not agent_religion:
                return ActionResult(success=False, emotional_impact=0.0, message="Not religious")

            nearby_temples = religion.get_nearby_temples((agent.location.x, agent.location.y), radius=30.0)
            if nearby_temples:
                temple = nearby_temples[0]
                temple.worshippers.add(agent.id)
                temple.last_ritual = current_tick
                agent.needs.satisfy_need(NeedType.MEANING, 0.3)
                agent.needs.satisfy_need(NeedType.BELONGING, 0.2)
                logger.info(f"🙏 {agent.name} worshipped at {temple.name}")
                return ActionResult(success=True, emotional_impact=0.3, message=f"Worshipped at {temple.name}")
            else:
                agent.needs.satisfy_need(NeedType.MEANING, 0.15)
                return ActionResult(success=True, emotional_impact=0.15, message="Worshipped outdoors")

        elif action.action_type == ActionType.PERFORM_RITUAL:
            agent_religion = religion.get_agent_religion(agent.id)
            if not agent_religion:
                return ActionResult(success=False, emotional_impact=0.0, message="Not religious")

            is_priest = religion.is_priest(agent.id)
            ritual_type = random.choice(agent_religion.regular_rituals) if agent_religion.regular_rituals else RitualType.PRAYER

            ritual = religion.start_ritual(ritual_type, agent_religion.id, agent.id, (agent.location.x, agent.location.y), current_tick)
            ritual.participants.add(agent.id)

            for other_agent in self.context.world.agents:
                if other_agent.id != agent.id and other_agent.alive and other_agent.id in agent_religion.followers:
                    dist = agent.location.distance_to(other_agent.location)
                    if dist < 20:
                        ritual.participants.add(other_agent.id)

            if is_priest:
                agent.needs.satisfy_need(NeedType.MEANING, 0.3)
                agent.needs.satisfy_need(NeedType.LEADERSHIP, 0.2)
            else:
                agent.needs.satisfy_need(NeedType.MEANING, 0.2)

            logger.info(f"🙏 {agent.name} started {ritual_type.value} with {len(ritual.participants)} participants")
            return ActionResult(success=True, emotional_impact=0.3, message=f"Performed {ritual_type.value}", metadata={'participants': len(ritual.participants)})

        elif action.action_type == ActionType.BUILD_TEMPLE:
            agent_religion = religion.get_agent_religion(agent.id)
            if not agent_religion:
                charisma = getattr(agent.personality, 'charisma', 0.5) if hasattr(agent, 'personality') else 0.5
                if charisma > 0.7:
                    religion_type = random.choice(list(ReligionType))
                    agent_religion = religion.found_religion(agent.id, agent.name, religion_type, current_tick)
                    logger.info(f"🙏 {agent.name} founded {agent_religion.name}!")
                else:
                    return ActionResult(success=False, emotional_impact=0.0, message="Not religious")

            agent.inventory.remove_item('stone', 5)
            agent.inventory.remove_item('wood', 5)

            temple = religion.build_temple(agent_religion.id, agent.id, (agent.location.x, agent.location.y), current_tick, size=1)

            if temple:
                logger.info(f"🏛️ {agent.name} built {temple.name}!")
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.4)
                agent.needs.satisfy_need(NeedType.MEANING, 0.5)

                if not religion.is_priest(agent.id):
                    religion.ordain_priest(agent.id, agent_religion.id)

                return ActionResult(success=True, emotional_impact=0.5, message=f"Built {temple.name}", metadata={'temple_id': temple.id})

            return ActionResult(success=False, emotional_impact=0.0, message="Temple construction failed")

        return ActionResult(success=False, emotional_impact=0.0, message="Unknown religion action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'religion']
