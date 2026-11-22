"""
Romance and partnership, by consent.

SEEK_ROMANCE (flirt, court, propose and marry run it too):
  - toward your partner: time together; both feel it, the bond grows
  - toward someone free: you court them. That alone makes nobody a partner.
    If they court you back on their own turn while you're still remembered
    (life/family.py, INTEREST_MEMORY_TICKS), you become partners.
SEPARATE: either partner can end the partnership on their own.

The handler never decides for the other person: the one who acts is always
the one whose choice is recorded.
"""

from typing import TYPE_CHECKING, Optional

from engine.action_handlers import ActionHandler, ActionResult, validate_agent_alive
from agents.agent import ActionType, Action, NeedType
from life import family

if TYPE_CHECKING:
    from agents.agent import Agent


class FamilyHandler(ActionHandler):

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in (ActionType.SEEK_ROMANCE, ActionType.SEPARATE)

    def get_required_systems(self) -> list[str]:
        return ['world', 'relationship_manager']

    # -- helpers -----------------------------------------------------------------

    @property
    def relationships(self):
        return self.context.get_system('relationship_manager')

    def _partner(self, agent):
        return family.partner_of(agent, self.context.get_agent_by_id)

    def _romance_target(self, agent, action) -> Optional['Agent']:
        """The named person; else the partner; else whoever the agent is most
        drawn to among those free to court (admirers first)."""
        if action.target_agent:
            return self.context.get_agent_by_id(action.target_agent)
        partner = self._partner(agent)
        if partner is not None:
            return partner
        now = self.context.current_tick
        free = [o for o in self.context.world.agents
                if o.alive and o.id != agent.id and family.free_to_court(agent, o)[0]]
        if not free:
            return None
        return max(free, key=lambda o: family.attraction(self.relationships, agent, o)
                   + (1.0 if family.recently(agent.admirers, o.id, now) else 0.0))

    def _log(self, importance, title, description, ids):
        if self.context.event_logger:
            from engine.events import EventCategory
            self.context.event_logger.log_event(
                EventCategory.SOCIAL, importance, title, description, self.context.current_tick, ids)

    def _count(self, what: str) -> None:
        events = self.context.get_system('life_events')
        if events is not None:
            events[what] += 1

    def _set_spouse(self, agent_id, spouse_id):
        life_system = self.context.get_system('life_system')
        profile = life_system.life_profiles.get(agent_id) if life_system else None
        if profile is not None:
            profile.spouse = spouse_id

    # -- validation ----------------------------------------------------------------

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive = validate_agent_alive(agent)
        if not alive[0]:
            return alive
        if action.action_type == ActionType.SEPARATE:
            if self._partner(agent) is None:
                return False, "You have no partner"
            return True, ""
        target = self._romance_target(agent, action)
        if target is None:
            return False, "Nobody free to court" if family.is_adult(agent) else "Too young for romance"
        return family.free_to_court(agent, target)

    # -- actions -----------------------------------------------------------------

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        if action.action_type == ActionType.SEPARATE:
            return self._separate(agent)
        target = self._romance_target(agent, action)
        action.target_agent = target.id
        if agent.partner_id == target.id:
            return self._time_together(agent, target)
        return self._court(agent, target)

    def _time_together(self, agent, partner) -> ActionResult:
        from engine.psychology import EmotionType
        agent.needs.satisfy_need(NeedType.ROMANCE, 0.5)
        agent.needs.satisfy_need(NeedType.SEX, 0.4)
        partner.needs.satisfy_need(NeedType.ROMANCE, 0.3)
        self.relationships.update_relationship(agent.id, partner.id, 'romance', True)
        for who in (agent, partner):
            who.emotions.trigger_emotion(EmotionType.LOVE, 0.3)
        agent.emotions.trigger_emotion(EmotionType.JOY, 0.2)
        return ActionResult(success=True, emotional_impact=0.6,
                            message=f"Spent time with {partner.name}, your partner",
                            metadata={'partner_id': partner.id})

    def _court(self, agent, target) -> ActionResult:
        from engine.psychology import EmotionType
        from engine.events import EventImportance
        now = self.context.current_tick
        family.forget_old(agent.admirers, now)
        family.forget_old(target.admirers, now)

        if family.recently(agent.admirers, target.id, now):
            # They courted us and we answer: both chose this
            self._form_partnership(agent, target)
            return ActionResult(success=True, emotional_impact=0.9,
                                message=f"You and {target.name} are now partners",
                                metadata={'partnership_formed': True, 'partner_id': target.id})

        first_time = not family.recently(target.admirers, agent.id, now)
        target.admirers[agent.id] = now
        if first_time:
            agent.needs.satisfy_need(NeedType.ROMANCE, 0.1)
            agent.emotions.trigger_emotion(EmotionType.EXCITEMENT, 0.2)
            self._log(EventImportance.MINOR, f"{agent.name} is courting {target.name}",
                      f"{agent.name} let {target.name} know they're interested. It's up to {target.name} now.",
                      [agent.id, target.id])
            return ActionResult(success=True, emotional_impact=0.2,
                                message=f"Let {target.name} know you're interested",
                                metadata={'courting': target.id})
        agent.emotions.trigger_emotion(EmotionType.SADNESS, 0.2)
        return ActionResult(success=False, emotional_impact=-0.2,
                            message=f"{target.name} hasn't returned your interest",
                            metadata={'courting': target.id})

    def _form_partnership(self, a, b) -> None:
        from engine.psychology import EmotionType
        from engine.events import EventImportance
        from social.relationships import RelationshipType
        a.partner_id, b.partner_id = b.id, a.id
        a.admirers.pop(b.id, None)
        b.admirers.pop(a.id, None)
        rm = self.relationships
        rel = rm.get_relationship(a.id, b.id) or rm.create_relationship(a.id, b.id, RelationshipType.ROMANCE, 0.6)
        rel.relationship_type = RelationshipType.ROMANCE
        rel.strength = max(rel.strength, 0.6)
        self._set_spouse(a.id, b.id)
        self._set_spouse(b.id, a.id)
        for who in (a, b):
            who.needs.satisfy_need(NeedType.ROMANCE, 0.6)
            who.emotions.trigger_emotion(EmotionType.LOVE, 0.6)
            who.emotions.trigger_emotion(EmotionType.JOY, 0.4)
        self._count('partnered')
        self._log(EventImportance.MAJOR, f"💞 {a.name} and {b.name} are partners",
                  f"{b.name} courted {a.name}, and {a.name} courted {b.name} back.", [a.id, b.id])

    def _separate(self, agent) -> ActionResult:
        from engine.psychology import EmotionType
        from engine.events import EventImportance
        from social.relationships import RelationshipType
        partner = self._partner(agent)
        agent.partner_id = partner.partner_id = None
        self._set_spouse(agent.id, None)
        self._set_spouse(partner.id, None)
        rel = self.relationships.get_relationship(agent.id, partner.id)
        if rel is not None:
            rel.relationship_type = RelationshipType.FRIENDSHIP
            rel.strength *= 0.5
        agent.emotions.trigger_emotion(EmotionType.SADNESS, 0.3)
        partner.emotions.trigger_emotion(EmotionType.SADNESS, 0.6)
        self._count('separated')
        self._log(EventImportance.MAJOR, f"💔 {agent.name} and {partner.name} have separated",
                  f"{agent.name} ended their partnership with {partner.name}.", [agent.id, partner.id])
        return ActionResult(success=True, emotional_impact=-0.1,
                            message=f"Ended your partnership with {partner.name}",
                            metadata={'former_partner_id': partner.id})
