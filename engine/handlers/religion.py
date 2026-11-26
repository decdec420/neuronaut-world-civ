"""Religion Action Handler - Handles agent religious and spiritual actions.

pray, worship, perform_ritual, build_temple, and convert: telling someone
about your faith. Whether they take it up is theirs to decide, from their own
state (_listener_takes_it_up). Before convert was real it fell back to
worship, so nobody could share a faith: a faith grew only when someone who
already liked a follower happened to worship, and most had only their founder.
"""

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

# Telling someone about your faith: the chance they take it up, from things
# about the listener. A sketch of how persuasion works, not a target.
LISTEN_BASE = 0.05      # anyone might
LISTEN_LIKING = 0.35    # more if they like the one telling them (a rival never)
LISTEN_OPENNESS = 0.2   # more if they're open to new ideas
LISTEN_MEANING = 0.2    # more if they're looking for meaning
LISTEN_HELD = 0.6       # less if their own faith still holds them
LISTEN_MAX = 0.8


class ReligionHandler(ActionHandler):
    """Handles religious and spiritual actions for agents."""

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [ActionType.PRAY, ActionType.WORSHIP, ActionType.PERFORM_RITUAL, ActionType.BUILD_TEMPLE,
                               ActionType.CONVERT]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive_valid = validate_agent_alive(agent)
        if not alive_valid[0]:
            return alive_valid
        religion = self.context.get_system('religion')
        if religion is None:
            return False, "Religion system unavailable"
        if action.action_type in (ActionType.PERFORM_RITUAL, ActionType.BUILD_TEMPLE, ActionType.CONVERT):
            if religion.get_agent_religion(agent.id) is None:
                return False, "Not religious"
        if action.action_type == ActionType.CONVERT:
            listener = self.context.get_agent_by_id(action.target_agent) if action.target_agent else None
            if listener is None or not listener.alive:
                return False, "Nobody to tell about your faith"
            if religion.get_agent_religion(listener.id) is religion.get_agent_religion(agent.id):
                return False, f"{listener.name} already shares your faith"
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

    def _listener_takes_it_up(self, listener, speaker, tick: int) -> float:
        """The chance the listener joins the speaker's faith: from how much it
        likes the speaker, its openness, how much it's looking for meaning,
        and how strongly its own faith (if any) still holds it."""
        religion = self.context.get_system('religion')
        liking = self._liking(listener.id, speaker.id)
        if liking < 0:
            return 0.0
        held = 0.0
        theirs = religion.get_agent_religion(listener.id)
        if theirs is not None:
            last = getattr(religion, 'last_practice', {}).get(listener.id)
            since = tick - last if last is not None else religion.LAPSE_TICKS
            held = max(0.0, 1.0 - since / religion.LAPSE_TICKS, self._pull(listener, theirs))
        meaning = listener.needs.needs[NeedType.MEANING].get_urgency()
        chance = (LISTEN_BASE + LISTEN_LIKING * liking + LISTEN_OPENNESS * listener.personality.openness
                  + LISTEN_MEANING * meaning - LISTEN_HELD * held)
        return max(0.0, min(LISTEN_MAX, chance))

    def _share_faith(self, agent, faith, listener_id: str, tick: int) -> ActionResult:
        religion = self.context.get_system('religion')
        listener = self.context.get_agent_by_id(listener_id)
        religion.record_practice(agent.id, tick)       # speaking of it is practising it
        agent.needs.satisfy_need(NeedType.MEANING, 0.2)
        chance = self._listener_takes_it_up(listener, agent, tick)
        theirs = religion.get_agent_religion(listener.id)
        if random.random() < chance:
            religion.convert_agent(listener.id, faith.id, theirs.id if theirs else None, by=agent.id)
            religion.record_practice(listener.id, tick)
            listener.needs.satisfy_need(NeedType.MEANING, 0.3)
            listener.needs.satisfy_need(NeedType.BELONGING, 0.3)
            agent.needs.satisfy_need(NeedType.BELONGING, 0.2)
            left = f" (leaving {theirs.name})" if theirs else ""
            self._log(f"🙏 {listener.name} joined {faith.name}", f"{agent.name} told {listener.name} about "
                      f"{faith.name}, and {listener.name} took it up{left}.", tick, [agent.id, listener.id])
            return ActionResult(success=True, emotional_impact=0.4,
                                message=f"{listener.name} took up {faith.name}",
                                metadata={'religion_id': faith.id, 'converted': True, 'chance': round(chance, 2)})
        kept = f"kept to {theirs.name}" if theirs else "didn't take it up"
        return ActionResult(success=True, emotional_impact=0.05,
                            message=f"Told {listener.name} about {faith.name}; they {kept}",
                            metadata={'religion_id': faith.id, 'converted': False, 'chance': round(chance, 2)})

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
                religion.note(new, 'founded', by=agent.id)
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

        if action.action_type == ActionType.CONVERT:
            return self._share_faith(agent, faith, action.target_agent, current_tick)

        if action.action_type == ActionType.BUILD_TEMPLE:
            agent.inventory.remove_item('stone', 5)
            agent.inventory.remove_item('wood', 5)
            temple = religion.build_temple(faith.id, agent.id, (agent.location.x, agent.location.y), current_tick, size=1)
            if temple is not None:
                religion.note(faith, 'temple', by=agent.id, temple=temple.id)
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
