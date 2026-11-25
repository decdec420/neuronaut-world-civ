"""
Romance and partnership, by consent.

SEEK_ROMANCE (flirt, court, propose and marry run it too):
  - toward your partner: time together; both feel it, the bond grows
  - toward someone free whom you have met: you court them. That alone makes
    nobody a partner. If they court you too, on their own turn, while you're
    still remembered (life/family.py, INTEREST_MEMORY_TICKS), you're getting
    to know each other: every visit deepens the bond, and once it's deep
    enough (PARTNER_BOND) you become partners.
  Both are done in person: farther than COURT_REACH, you walk to them first.
SEPARATE: either partner can end the partnership on their own.
TRY_FOR_CHILD: say you want a child with your partner. Only once both have
  said so (each on its own turn, within INTEREST_MEMORY_TICKS) is there a
  chance of conceiving, by age; a female and a male partner are needed.
CARE_FOR_CHILD (parent runs it too): look after a baby or child: feed it
  from what you carry, give it water, keep it company. Your own children
  first, otherwise a child nearby.

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
        return action_type in (ActionType.SEEK_ROMANCE, ActionType.SEPARATE,
                               ActionType.TRY_FOR_CHILD, ActionType.CARE_FOR_CHILD)

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
        drawn to among those it has met and is free to court (admirers first)."""
        if action.target_agent:
            return self.context.get_agent_by_id(action.target_agent)
        partner = self._partner(agent)
        if partner is not None:
            return partner
        now = self.context.current_tick
        free = [o for o in self.context.world.agents
                if o.alive and o.id != agent.id and family.drawn_to(agent, o)
                and family.free_to_court(agent, o, self.relationships)[0]]
        if not free:
            return None
        return max(free, key=lambda o: family.attraction(self.relationships, agent, o)
                   + (1.0 if family.recently(agent.admirers, o.id, now) else 0.0))

    def _child_to_care_for(self, agent, action) -> Optional['Agent']:
        """The named child; else the agent's own child who needs it most;
        else the neediest child within reach."""
        if action.target_agent:
            child = self.context.get_agent_by_id(action.target_agent)
            return child if child is not None and family.is_young(child) else None
        own = [self.context.get_agent_by_id(cid) for cid in agent.children_ids]
        own = [c for c in own if c is not None and family.is_young(c)]
        if own:
            return max(own, key=family.neediness)
        near = [o for o in self.context.world.agents if o.id != agent.id and family.is_young(o)
                and agent.location.distance_to(o.location) <= family.CARE_REACH]
        return max(near, key=family.neediness) if near else None

    def _recent(self, tick) -> bool:
        return tick is not None and self.context.current_tick - tick <= family.INTEREST_MEMORY_TICKS

    def _log(self, importance, title, description, ids, category=None):
        if self.context.event_logger:
            from engine.events import EventCategory
            self.context.event_logger.log_event(
                category or EventCategory.SOCIAL, importance, title, description, self.context.current_tick, ids)

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
        if action.action_type == ActionType.TRY_FOR_CHILD:
            return self._can_try_for_child(agent)
        if action.action_type == ActionType.CARE_FOR_CHILD:
            if not family.is_adult(agent):
                return False, "Too young to look after a child"
            if self._child_to_care_for(agent, action) is None:
                return False, "No child of yours, and none nearby, to look after"
            return True, ""
        target = self._romance_target(agent, action)
        if target is None:
            return False, "Nobody you know is free to court" if family.is_adult(agent) else "Too young for romance"
        return family.free_to_court(agent, target, self.relationships)

    def _can_try_for_child(self, agent) -> tuple[bool, str]:
        if not family.is_adult(agent):
            return False, "Too young to have a child"
        partner = self._partner(agent)
        if partner is None:
            return False, "You have no partner"
        pair = family.mother_and_father(agent, partner)
        if pair is None:
            return False, f"You and {partner.name} can't conceive together (you could look after a child)"
        mother, father = pair
        if mother.is_pregnant:
            return False, f"{'You are' if mother is agent else mother.name + ' is'} already expecting"
        if family.fertility(mother.age) == 0 or family.fertility(father.age) == 0:
            return False, "Not at an age to have children"
        # A technical limit for performance (MAX_POPULATION), not a rule of the world
        config = self.context.get_system('config')
        living = sum(1 + a.is_pregnant for a in self.context.world.agents if a.alive)
        if config is not None and living >= config.max_population:
            return False, f"The world is at its population limit ({config.max_population}, a technical cap)"
        return True, ""

    # -- actions -----------------------------------------------------------------

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        if action.action_type == ActionType.SEPARATE:
            return self._separate(agent)
        if action.action_type == ActionType.TRY_FOR_CHILD:
            return self._try_for_child(agent)
        if action.action_type == ActionType.CARE_FOR_CHILD:
            child = self._child_to_care_for(agent, action)
            action.target_agent = child.id
            return self._care_for(agent, child)
        target = self._romance_target(agent, action)
        action.target_agent = target.id
        distance = agent.location.distance_to(target.location)
        if distance > family.COURT_REACH:
            # In person: go to them first (a long walk takes a few turns)
            works = self.context.get_system('infrastructure')
            works.step_toward(agent, self.context.get_system('pathfinder'),
                              target.location.x, target.location.y, self.context.current_tick)
            return ActionResult(success=True, emotional_impact=0.05,
                                message=f"On your way to see {target.name}",
                                metadata={'underway': True, 'target': target.id})
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
            # They court us and we court them: both chose this
            if family.liking(self.relationships, agent, target) >= family.PARTNER_BOND:
                self._form_partnership(agent, target)
                return ActionResult(success=True, emotional_impact=0.9,
                                    message=f"You and {target.name} are now partners",
                                    metadata={'partnership_formed': True, 'partner_id': target.id})
            # Still getting to know each other: the visit deepens the bond
            # (as time together does: social/relationships.py BOND_SPACING)
            self.relationships.update_relationship(agent.id, target.id, 'romance', True)
            target.admirers[agent.id] = now
            for who in (agent, target):
                who.needs.satisfy_need(NeedType.ROMANCE, 0.2)
            agent.emotions.trigger_emotion(EmotionType.JOY, 0.2)
            target.emotions.trigger_emotion(EmotionType.JOY, 0.1)
            return ActionResult(success=True, emotional_impact=0.4,
                                message=f"You and {target.name} are getting to know each other",
                                metadata={'courting': target.id, 'mutual': True})

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
        a.child_wish_tick = b.child_wish_tick = None  # wishes belong to a partnership
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
        # Partners share a home: one without moves in with the other
        from life import homes
        dbs, events = self.context.get_system('dynamic_building_system'), self.context.get_system('life_events')
        if dbs is not None:
            home_a, home_b = homes.home_of(dbs, a), homes.home_of(dbs, b)
            if home_a is not None and home_b is None:
                homes.move_in(dbs, b, home_a, self.context.current_tick, f"living with {a.name}", events)
            elif home_b is not None and home_a is None:
                homes.move_in(dbs, a, home_b, self.context.current_tick, f"living with {b.name}", events)
        self._count('partnered')
        self._log(EventImportance.MAJOR, f"💞 {a.name} and {b.name} are partners",
                  f"{b.name} courted {a.name}, and {a.name} courted {b.name} back.", [a.id, b.id])

    def _separate(self, agent) -> ActionResult:
        from engine.psychology import EmotionType
        from engine.events import EventImportance
        from social.relationships import RelationshipType
        partner = self._partner(agent)
        agent.partner_id = partner.partner_id = None
        agent.child_wish_tick = partner.child_wish_tick = None
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

    def _try_for_child(self, agent) -> ActionResult:
        import random
        from engine.psychology import EmotionType
        from engine.events import EventImportance, EventCategory
        partner = self._partner(agent)
        mother, father = family.mother_and_father(agent, partner)
        said_before = self._recent(agent.child_wish_tick)
        agent.child_wish_tick = self.context.current_tick

        if not self._recent(partner.child_wish_tick):
            if said_before:
                return ActionResult(success=False, emotional_impact=-0.1,
                                    message=f"{partner.name} hasn't said they want a child")
            return ActionResult(success=True, emotional_impact=0.2,
                                message=f"Told {partner.name} you'd like a child")

        # Both want one: they try
        for who in (agent, partner):
            who.needs.satisfy_need(NeedType.ROMANCE, 0.3)
            who.needs.satisfy_need(NeedType.SEX, 0.3)
            who.emotions.trigger_emotion(EmotionType.LOVE, 0.3)
        chance = family.CONCEPTION_CHANCE * family.fertility(mother.age) * family.fertility(father.age)
        if random.random() >= chance:
            return ActionResult(success=True, emotional_impact=0.4,
                                message=f"You and {partner.name} tried for a child", metadata={'tried': True})
        config = self.context.get_system('config')
        mother.is_pregnant = True
        mother.pregnancy_partner_id = father.id
        mother.pregnancy_start_tick = self.context.current_tick
        mother.pregnancy_duration_ticks = max(1, round(family.PREGNANCY_YEARS * config.ticks_per_life_year))
        agent.child_wish_tick = partner.child_wish_tick = None
        self._count('conceived')
        self._log(EventImportance.MAJOR, f"🤰 {mother.name} and {father.name} are expecting a child",
                  "They both wanted one.", [mother.id, father.id], EventCategory.LIFE)
        return ActionResult(success=True, emotional_impact=0.8,
                            message=f"You and {partner.name} are expecting a child", metadata={'conceived': True})

    def _care_for(self, agent, child) -> ActionResult:
        from engine.psychology import EmotionType
        distance = agent.location.distance_to(child.location)
        if distance > family.CARE_REACH:
            # Go to them first (a long walk takes a few turns)
            # (a straight walk that stops at any water on the way)
            agent.location = self.context.world.map.walk_line(agent.location, child.location,
                                                              min(10.0, distance - 1.0))
            agent.stepped_toward = (child.location.x, child.location.y)
            return ActionResult(success=True, emotional_impact=0.05,
                                message=f"On your way to look after {child.name}")
        given = []
        needs = child.needs.needs
        if needs[NeedType.HUNGER].level > 0.3 and agent.inventory.has_item('food', 1):
            agent.inventory.remove_item('food', 1)
            child.needs.satisfy_need(NeedType.HUNGER, 0.6)
            given.append("fed")
        if needs[NeedType.THIRST].level > 0.3 and agent.inventory.has_item('water', 1):
            agent.inventory.remove_item('water', 1)
            child.needs.satisfy_need(NeedType.THIRST, 0.6)
            given.append("gave water to")
        child.needs.satisfy_need(NeedType.BELONGING, 0.3)
        child.needs.satisfy_need(NeedType.SECURITY, 0.3)
        child.emotions.trigger_emotion(EmotionType.JOY, 0.2)
        agent.needs.satisfy_need(NeedType.MEANING, 0.3)
        agent.needs.satisfy_need(NeedType.BELONGING, 0.2)
        agent.emotions.trigger_emotion(EmotionType.LOVE, 0.2)
        self.relationships.update_relationship(agent.id, child.id, 'care', True)
        what = " and ".join(given) + f" {child.name}" if given else f"kept {child.name} company"
        return ActionResult(success=True, emotional_impact=0.4, message=f"Looked after {child.name}: {what}",
                            metadata={'child_id': child.id, 'fed': 'fed' in given})
