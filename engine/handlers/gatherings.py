"""
organize_event and attend_event (world/gatherings.py).

organize_event announces a gathering; attend_event goes to one the agent has
heard about. Both are rejected up front when they can't work (already
hosting one, too many planned; never heard of any that's on or starting
soon), so agents choose something else.
"""

import math
from typing import TYPE_CHECKING

from engine.action_handlers import ActionHandler, ActionResult, validate_agent_alive
from agents.agent import ActionType, Action, NeedType
from world import gatherings as gath

if TYPE_CHECKING:
    from agents.agent import Agent


class GatheringHandler(ActionHandler):

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in (ActionType.ORGANIZE_EVENT, ActionType.ATTEND_EVENT)

    def get_required_systems(self) -> list[str]:
        return ['world', 'gatherings', 'news']

    def _choose(self, agent):
        """The gathering it heard of that it would most like to go to: one by
        someone it likes, starting soonest."""
        gatherings = self.context.get_system('gatherings')
        engine = self.context.get_system('relationship_manager')
        tick = self.context.current_tick
        options = gatherings.known_to(agent.id, tick)
        if not options:
            return None

        def appeal(g):
            rel = engine.get_relationship(agent.id, g.organizer) if g.organizer != agent.id else None
            liking = rel.strength if rel is not None and rel.relationship_type.value != "rivalry" else 0.0
            return (g.organizer == agent.id) * 2 + liking - max(0, g.start - tick) / 100.0
        return max(options, key=appeal)

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive = validate_agent_alive(agent)
        if not alive[0]:
            return alive
        gatherings = self.context.get_system('gatherings')
        if action.action_type == ActionType.ORGANIZE_EVENT:
            if gatherings.organized_by(agent.id) is not None:
                return False, "You're already hosting one"
            if len(gatherings.upcoming) >= gath.MAX_UPCOMING:
                return False, "The village has enough gatherings planned"
            return True, ""
        if self._choose(agent) is None:
            return False, "You haven't heard of any gathering that's on or about to start"
        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from engine.psychology import EmotionType
        gatherings = self.context.get_system('gatherings')
        tick = self.context.current_tick
        if action.action_type == ActionType.ORGANIZE_EVENT:
            details = str((action.parameters or {}).get('details', ''))
            g = gatherings.announce(agent, details, tick)
            agent.needs.satisfy_need(NeedType.STATUS, 0.2)
            agent.needs.satisfy_need(NeedType.BELONGING, 0.2)
            agent.memory_stream.add(tick, f"I'm hosting a {g.kind} at {g.place}, at {g.start // 6 % 24:02d}:00", 0.7,
                                    kind="plan")
            return ActionResult(success=True, emotional_impact=0.4,
                                message=f"Invited everyone to a {g.kind} at {g.place}",
                                metadata={'gathering_id': g.id, 'starts': g.start})

        g = self._choose(agent)
        distance = math.hypot(agent.location.x - g.x, agent.location.y - g.y)
        if distance > gath.JOIN_RADIUS:
            infra = self.context.get_system('infrastructure')
            infra.step_toward(agent, self.context.get_system('pathfinder'), g.x, g.y, tick)
            return ActionResult(success=True, emotional_impact=0.1,
                                message=f"On the way to {g.organizer_name}'s {g.kind} at {g.place}",
                                metadata={'gathering_id': g.id})
        if not g.is_on(tick):
            return ActionResult(success=True, emotional_impact=0.1,
                                message=f"Waiting for {g.organizer_name}'s {g.kind} to start",
                                metadata={'gathering_id': g.id, 'underway': True})
        new = agent.id not in g.attendees
        g.attendees.add(agent.id)
        agent.needs.satisfy_need(NeedType.BELONGING, 0.4)
        agent.needs.satisfy_need(NeedType.FRIENDSHIP, 0.3)
        agent.emotions.trigger_emotion(EmotionType.JOY, 0.4)
        rm = self.context.get_system('relationship_manager')
        for other_id in sorted(g.attendees):
            if other_id != agent.id:
                rm.update_relationship(agent.id, other_id, 'gathering', True)
        if new:
            agent.memory_stream.add(tick, f"Went to {g.organizer_name}'s {g.kind} at {g.place}", 0.5)
        return ActionResult(success=True, emotional_impact=0.5,
                            message=f"At {g.organizer_name}'s {g.kind} ({len(g.attendees)} here)",
                            metadata={'gathering_id': g.id, 'joined': new})
