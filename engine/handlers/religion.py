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
        religion = self.context.get_system('religion')
        if religion is None:
            return False, "Religion system unavailable"
        if action.action_type in (ActionType.PERFORM_RITUAL, ActionType.BUILD_TEMPLE):
            if religion.get_agent_religion(agent.id) is None:
                return False, "Not religious"
        if action.action_type == ActionType.BUILD_TEMPLE:
            if not (agent.inventory.has_item('stone', 5) and agent.inventory.has_item('wood', 5)):
                return False, "Need 5 stone and 5 wood for a temple"
        return True, ""

    # -- helpers ---------------------------------------------------------------

    def _liking(self, agent_id: str, other_id: str) -> float:
        rel = self.context.get_system('relationship_manager').get_relationship(agent_id, other_id)
        if rel is None:
            return 0.0
        return -rel.strength if rel.relationship_type.value == 'rivalry' else rel.strength

    def _pull(self, agent, faith) -> float:
        """How drawn an agent is to a faith: how much it likes the faithful."""
        return max((self._liking(agent.id, f) for f in faith.followers if f != agent.id), default=0.0)

    def _faith_to_join(self, agent, current=None, target_id=None):
        religion = self.context.get_system('religion')
        if target_id:
            theirs = religion.get_agent_religion(target_id)
            if theirs and theirs is not current:
                return theirs
        best, best_pull = None, (self._pull(agent, current) + 0.2) if current else 0.0
        for faith in religion.religions.values():
            if faith is current or not faith.followers:
                continue
            pull = self._pull(agent, faith)
            if pull > best_pull:
                best, best_pull = faith, pull
        return best

    @staticmethod
    def _founding_type(agent):
        """The kind of faith follows the founder's temperament."""
        from world.religion import ReligionType
        p = agent.personality
        if p.openness > 0.7:
            return ReligionType.PANTHEISM
        if p.conscientiousness > 0.7:
            return ReligionType.MONOTHEISM
        if p.agreeableness > 0.7:
            return ReligionType.ANCESTOR_WORSHIP
        if p.extraversion > 0.7:
            return ReligionType.POLYTHEISM
        return ReligionType.ANIMISM

    def _log(self, title, description, tick, agent_ids):
        from engine.events import EventCategory, EventImportance
        if self.context.event_logger:
            self.context.event_logger.log_event(EventCategory.CULTURAL, EventImportance.MAJOR,
                                                title, description, tick, agent_ids)

    # -- actions -----------------------------------------------------------------

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from world.religion import RitualType

        religion = self.context.get_system('religion')
        current_tick = self.context.current_tick
        faith = religion.get_agent_religion(agent.id)

        if action.action_type == ActionType.PRAY:
            # Private prayer: meaning and comfort. Founding a faith is a choice
            # made by worshipping (it used to happen by a 10% chance here).
            religion.record_practice(agent.id, current_tick)
            agent.needs.satisfy_need(NeedType.MEANING, 0.2)
            agent.needs.satisfy_need(NeedType.SECURITY, 0.1)
            return ActionResult(success=True, emotional_impact=0.2, message="Prayed for guidance")

        if action.action_type == ActionType.WORSHIP:
            other = self._faith_to_join(agent, faith, action.target_agent)
            if other is not None:
                religion.convert_agent(agent.id, other.id, faith.id if faith else None)
                religion.record_practice(agent.id, current_tick)
                agent.needs.satisfy_need(NeedType.BELONGING, 0.3)
                agent.needs.satisfy_need(NeedType.MEANING, 0.3)
                verb = f"left {faith.name} for" if faith else "joined"
                self._log(f"🙏 {agent.name} {verb} {other.name}", f"{agent.name} {verb} {other.name}.",
                          current_tick, [agent.id])
                return ActionResult(success=True, emotional_impact=0.35, message=f"Joined {other.name}",
                                    metadata={'religion_id': other.id, 'joined': True})

            if faith is None:
                # Nobody this agent cares about holds a faith: it starts its own
                new = religion.found_religion(agent.id, agent.name, self._founding_type(agent), current_tick)
                religion.record_practice(agent.id, current_tick)
                agent.needs.satisfy_need(NeedType.MEANING, 0.5)
                self._log(f"✨ {agent.name} founded {new.name}",
                          f"{agent.name} founded {new.name} ({new.religion_type.value}).", current_tick, [agent.id])
                return ActionResult(success=True, emotional_impact=0.5, message=f"Founded {new.name}",
                                    metadata={'religion_id': new.id, 'founded': True})

            religion.record_practice(agent.id, current_tick)
            nearby_temples = religion.get_nearby_temples((agent.location.x, agent.location.y), radius=30.0)
            if nearby_temples:
                temple = nearby_temples[0]
                temple.worshippers.add(agent.id)
                temple.last_ritual = current_tick
                agent.needs.satisfy_need(NeedType.MEANING, 0.3)
                agent.needs.satisfy_need(NeedType.BELONGING, 0.2)
                return ActionResult(success=True, emotional_impact=0.3, message=f"Worshipped at {temple.name}")
            agent.needs.satisfy_need(NeedType.MEANING, 0.15)
            return ActionResult(success=True, emotional_impact=0.15, message="Worshipped outdoors")

        if action.action_type == ActionType.PERFORM_RITUAL:
            religion.record_practice(agent.id, current_tick)
            is_priest = religion.is_priest(agent.id)
            ritual_type = random.choice(faith.regular_rituals) if faith.regular_rituals else RitualType.PRAYER
            ritual = religion.start_ritual(ritual_type, faith.id, agent.id, (agent.location.x, agent.location.y), current_tick)
            ritual.participants.add(agent.id)
            for other_agent in self.context.world.agents:
                if other_agent.id != agent.id and other_agent.alive and other_agent.id in faith.followers:
                    if agent.location.distance_to(other_agent.location) < 20:
                        ritual.participants.add(other_agent.id)
                        religion.record_practice(other_agent.id, current_tick)
            agent.needs.satisfy_need(NeedType.MEANING, 0.3 if is_priest else 0.2)
            if is_priest:
                agent.needs.satisfy_need(NeedType.STATUS, 0.2)
            return ActionResult(success=True, emotional_impact=0.3, message=f"Performed {ritual_type.value}",
                                metadata={'participants': len(ritual.participants)})

        if action.action_type == ActionType.BUILD_TEMPLE:
            agent.inventory.remove_item('stone', 5)
            agent.inventory.remove_item('wood', 5)
            temple = religion.build_temple(faith.id, agent.id, (agent.location.x, agent.location.y), current_tick, size=1)
            if temple:
                religion.record_practice(agent.id, current_tick)
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.4)
                agent.needs.satisfy_need(NeedType.MEANING, 0.5)
                if not religion.is_priest(agent.id):
                    religion.ordain_priest(agent.id, faith.id)
                self._log(f"🏛️ {agent.name} built {temple.name}", f"A temple for {faith.name}.",
                          current_tick, [agent.id])
                return ActionResult(success=True, emotional_impact=0.5, message=f"Built {temple.name}",
                                    metadata={'temple_id': temple.id})
            return ActionResult(success=False, emotional_impact=0.0, message="Temple construction failed")

        return ActionResult(success=False, emotional_impact=0.0, message="Unknown religion action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'religion']
