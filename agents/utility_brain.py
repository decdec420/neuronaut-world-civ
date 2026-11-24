"""
The rule-based brain: every action the world offers, weighed by the agent itself.

Used whenever the AI (LLM) brain doesn't decide: no model configured or
reachable, or an answer it couldn't read. Survival comes first and is handled
before this (AgentUpdater._survival_override).

Every action the engine can run (the same list the AI brain's menu is built
from) is a candidate. Each gets a utility from the agent's own state:

- needs: how urgently the needs this action tends to meet are felt
- personality: the traits that draw someone to it (or away from it)
- memory: how often it has worked for this agent before
- people: for actions with a partner, how much the agent likes them; for
  romance, how drawn it is to them, and whether they courted it first; for
  a child, whether the agent wants one (its life profile) and whether its
  partner has said it does; for looking after a child, how much the child
  needs it and whether it's the agent's own
- commitment: what it set out to do and is part-way through (a walk to a
  gathering, to shelter, to water) pulls it to carry on, more for a
  conscientious agent (agents/commitment.py)
- faith: an agent that holds a faith feels it fading the longer it goes
  without practising it (unpractised for long enough, it lapses)
- danger: actions that can get it killed weigh less for careful or hurt agents
- law: what its government has banned weighs less, the more conscientious
  and agreeable it is
- day plan and habits: rest pulls hard at night, work during work hours
  (the agent's own job most), company in the evening; the step its current
  goal calls for pulls a little

and the choice is sampled (softmax), so likely actions are likely and rare
ones are rare, never impossible. Nothing here makes a particular outcome
happen; there are only weights.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

from engine.psychology import NeedType as N

# What an action actually relieves when it runs, weighted by how much (weights
# add up to 1). Measured with scripts/need_effects.py, which runs every action and
# diffs the agent's needs; tests/test_need_effects.py keeps this table and the
# world in step. (It used to be written by hand, and 52 of 61 actions were
# credited with needs they never relieve: tell_story with recognition and
# creativity, which nothing relieved, so those needs stayed urgent and kept
# pulling agents to tell stories: 22% of everything they did.)
# Actions whose effect comes later than their first step, or only on success, or
# only rarely: one run can't see it, so their entries are read from the handlers,
# each with a note on why.
EFFECT_LATER = {"attend_event", "hide", "build", "gather_water", "discover_element", "discover_material",
                "discover_energy", "make_law", "fight", "separate", "experiment"}

ACTION_NEEDS: Dict[str, Dict[N, float]] = {
    "apply_for_loan": {N.SECURITY: 1},
    "attend_event": {N.BELONGING: 0.55, N.FRIENDSHIP: 0.45},  # on arriving (engine/handlers/gatherings.py)
    "build": {N.SHELTER: 0.5, N.ACHIEVEMENT: 0.3, N.SECURITY: 0.2},  # when it is finished: a home
    "build_power_plant": {N.ACHIEVEMENT: 1},
    "build_road": {N.ACHIEVEMENT: 0.75, N.BELONGING: 0.25},
    "build_streetlight": {N.ACHIEVEMENT: 0.5, N.SECURITY: 0.25, N.CREATIVITY: 0.25},
    "build_temple": {N.MEANING: 0.55, N.ACHIEVEMENT: 0.45},
    "care_for_child": {N.MEANING: 0.6, N.BELONGING: 0.4},
    "celebrate": {N.BELONGING: 0.55, N.MEANING: 0.45},
    "chop_wood": {N.RESOURCES: 1},
    "claim_territory": {N.SECURITY: 0.6, N.ACHIEVEMENT: 0.4},
    "convert": {N.MEANING: 1},  # speaking of one's faith; belonging too if they take it up
    "create_alloy": {N.ACHIEVEMENT: 1},
    "create_art": {N.CREATIVITY: 0.45, N.ACHIEVEMENT: 0.35, N.MEANING: 0.2},
    "cure": {N.ACHIEVEMENT: 0.55, N.MEANING: 0.45},
    "diagnose": {N.ACHIEVEMENT: 1},
    "dig_well": {N.ACHIEVEMENT: 0.65, N.SECURITY: 0.35},
    "discover_element": {N.GROWTH: 0.6, N.ACHIEVEMENT: 0.4},  # when something is found (chemistry handler)
    "discover_energy": {N.GROWTH: 0.6, N.ACHIEVEMENT: 0.4},  # when something is found (chemistry handler)
    "discover_material": {N.GROWTH: 0.6, N.ACHIEVEMENT: 0.4},  # when something is found (chemistry handler)
    "drink": {N.THIRST: 1},
    "eat": {N.HUNGER: 1},
    # when it makes something (engine/handlers/knowledge.py); a civilization
    # milestone (the first fire...) also meets recognition and meaning, but
    # there are only a handful per world, so the brain doesn't count on one
    "experiment": {N.CREATIVITY: 0.6, N.ACHIEVEMENT: 0.4},
    "explore": {},  # moving to new places relieves no need; traits and jobs draw people to it
    "fight": {N.STATUS: 1},  # for the winner (combat handler); see DANGER
    "gamble": {N.BELONGING: 1},
    "gather_food": {N.HUNGER: 1},
    "gather_materials": {N.RESOURCES: 1},
    "gather_water": {N.THIRST: 0.8, N.RESOURCES: 0.2},  # the water it brings is drunk
    "govern": {N.STATUS: 1},
    "guard": {N.SECURITY: 0.65, N.MEANING: 0.35},
    "harvest": {N.ACHIEVEMENT: 0.6, N.RESOURCES: 0.4},
    "heal": {N.ACHIEVEMENT: 0.55, N.MEANING: 0.45},
    "hide": {N.SECURITY: 0.3},  # on arriving; kept low on purpose, see _warning_pull
    "hunt": {N.HUNGER: 0.8, N.ACHIEVEMENT: 0.2},
    "join_tax_revolt": {N.STATUS: 1},
    "make_law": {N.STATUS: 1},  # when the law is proposed (governance handler)
    "mine": {N.RESOURCES: 1},
    "mint_coins": {N.ACHIEVEMENT: 0.6, N.RESOURCES: 0.4},
    "move": {},  # relieves no need
    "open_bank": {N.ACHIEVEMENT: 0.65, N.STATUS: 0.35},
    "operate_power_plant": {N.ACHIEVEMENT: 1},
    "organize_event": {N.BELONGING: 0.5, N.STATUS: 0.5},
    "patrol": {N.SECURITY: 1},
    "perform_chemistry": {N.GROWTH: 0.6, N.ACHIEVEMENT: 0.4},
    "perform_ritual": {N.MEANING: 0.6, N.STATUS: 0.4},
    "plant_crops": {N.ACHIEVEMENT: 1},
    "play_game": {N.BELONGING: 1},
    "pray": {N.MEANING: 0.65, N.SECURITY: 0.35},
    "raise_animals": {N.ACHIEVEMENT: 1},
    "refine_material": {N.ACHIEVEMENT: 1},
    "rest": {N.SLEEP: 1},
    "seek_romance": {N.ROMANCE: 0.55, N.SEX: 0.45},
    "send_caravan": {N.ACHIEVEMENT: 1},
    "separate": {N.ROMANCE: 1},  # not relieved now: leaving frees one to find love (see utility())
    "smelt_ore": {N.ACHIEVEMENT: 1},
    "socialize": {N.FRIENDSHIP: 0.6, N.BELONGING: 0.4},
    "teach": {},  # the teacher gets nothing (engine/handlers/knowledge.py); traits and jobs draw people to it
    "tell_story": {N.BELONGING: 0.55, N.MEANING: 0.45},
    "tend_crops": {N.RESOURCES: 1},
    "trade": {N.RESOURCES: 1},
    "try_for_child": {N.SEX: 0.5, N.ROMANCE: 0.5},
    "vote": {N.BELONGING: 1},
    "worship": {N.MEANING: 1},
    "write": {N.GROWTH: 1},
}

# Who is drawn to an action: trait -> weight (negative: drawn away)
ACTION_TRAITS: Dict[str, Dict[str, float]] = {
    "gather_food": {"conscientiousness": 0.3},
    "gather_water": {"conscientiousness": 0.2},
    "hunt": {"risk_taking": 0.5, "aggression": 0.3},
    "plant_crops": {"conscientiousness": 0.6},
    "tend_crops": {"conscientiousness": 0.6},
    "harvest": {"conscientiousness": 0.5},
    "raise_animals": {"conscientiousness": 0.4, "empathy": 0.2},
    "explore": {"openness": 0.6, "risk_taking": 0.4},
    "move": {"openness": 0.3},
    "heal": {"empathy": 0.7, "agreeableness": 0.3},
    "cure": {"empathy": 0.6, "rationality": 0.3},
    "diagnose": {"empathy": 0.4, "rationality": 0.5},
    "gather_materials": {"conscientiousness": 0.5},
    "chop_wood": {"conscientiousness": 0.4},
    "mine": {"conscientiousness": 0.4, "risk_taking": 0.2},
    "build": {"conscientiousness": 0.5, "ambition": 0.3},
    "build_road": {"conscientiousness": 0.4, "agreeableness": 0.3, "ambition": 0.2},
    "dig_well": {"conscientiousness": 0.4, "agreeableness": 0.3},
    "build_streetlight": {"creativity": 0.3, "agreeableness": 0.3, "conscientiousness": 0.2},
    "experiment": {"openness": 0.5, "creativity": 0.5},
    "smelt_ore": {"rationality": 0.5, "conscientiousness": 0.3},
    "refine_material": {"rationality": 0.5, "conscientiousness": 0.3},
    "create_alloy": {"rationality": 0.5, "openness": 0.3},
    "perform_chemistry": {"rationality": 0.5, "openness": 0.4},
    "discover_element": {"openness": 0.5, "rationality": 0.5},
    "discover_material": {"openness": 0.5, "rationality": 0.5},
    "discover_energy": {"openness": 0.5, "rationality": 0.5},
    "build_power_plant": {"ambition": 0.5, "rationality": 0.5},
    "operate_power_plant": {"conscientiousness": 0.5, "rationality": 0.3},
    "teach": {"agreeableness": 0.4, "empathy": 0.3, "extraversion": 0.3},
    "write": {"rationality": 0.5, "openness": 0.3, "extraversion": -0.2},
    "socialize": {"extraversion": 0.7, "agreeableness": 0.3},
    "seek_romance": {"sexuality": 0.7, "extraversion": 0.3},
    "separate": {"agreeableness": -0.5, "neuroticism": 0.3, "openness": 0.2},
    "try_for_child": {"empathy": 0.3, "agreeableness": 0.2},
    "care_for_child": {"empathy": 0.6, "agreeableness": 0.3, "conscientiousness": 0.2},
    "celebrate": {"extraversion": 0.6, "openness": 0.2},
    "organize_event": {"extraversion": 0.5, "agreeableness": 0.2, "ambition": 0.2},
    "hide": {"neuroticism": 0.4, "risk_taking": -0.3},
    "attend_event": {"extraversion": 0.4, "agreeableness": 0.3},
    "tell_story": {"extraversion": 0.5, "creativity": 0.5},
    "play_game": {"extraversion": 0.5, "risk_taking": 0.2},
    "create_art": {"creativity": 0.8, "openness": 0.2},
    "gamble": {"risk_taking": 0.8, "conscientiousness": -0.3},
    "trade": {"extraversion": 0.3, "ambition": 0.4, "rationality": 0.3},
    "mint_coins": {"ambition": 0.5, "rationality": 0.3},
    "open_bank": {"ambition": 0.6, "rationality": 0.3},
    "apply_for_loan": {"risk_taking": 0.5, "ambition": 0.3},
    "send_caravan": {"ambition": 0.5, "risk_taking": 0.4},
    "join_tax_revolt": {"aggression": 0.3, "agreeableness": -0.4, "risk_taking": 0.3},
    "govern": {"ambition": 0.6, "extraversion": 0.3},
    "make_law": {"ambition": 0.4, "conscientiousness": 0.4},
    "vote": {"conscientiousness": 0.3, "agreeableness": 0.2},
    "claim_territory": {"ambition": 0.5, "aggression": 0.3},
    "guard": {"conscientiousness": 0.4, "aggression": 0.3},
    "patrol": {"conscientiousness": 0.4, "aggression": 0.3},
    "pray": {"rationality": -0.5, "neuroticism": 0.3, "openness": 0.2},
    "worship": {"rationality": -0.5, "agreeableness": 0.3},
    "perform_ritual": {"rationality": -0.4, "extraversion": 0.3},
    "convert": {"rationality": -0.3, "extraversion": 0.5, "ambition": 0.2},
    "build_temple": {"rationality": -0.4, "conscientiousness": 0.3, "ambition": 0.3},
    "fight": {"aggression": 0.8, "risk_taking": 0.3, "agreeableness": -0.4},
}

SOCIAL_ACTIONS = {"socialize", "seek_romance", "celebrate", "tell_story", "play_game", "create_art",
                  "organize_event", "attend_event"}
NEEDS_TARGET = {"convert", "socialize", "seek_romance", "separate", "try_for_child", "care_for_child", "trade", "teach", "tell_story", "play_game", "gamble",
                "fight", "heal", "cure", "diagnose"}
NEEDS_SICK_TARGET = {"heal", "cure", "diagnose"}
ROMANCE_ACTIONS = {"seek_romance", "separate"}
FAMILY_ACTIONS = {"try_for_child", "care_for_child"}
# Skipped when there's nobody suitable (no sick person, nobody free to court...)
NEEDS_SUITABLE_TARGET = NEEDS_SICK_TARGET | ROMANCE_ACTIONS | FAMILY_ACTIONS
NEEDS_PLACE = {"move", "explore"}

# How much each part of the utility counts, and how sharply the agent picks
NEED_WEIGHT = 1.5
TRAIT_WEIGHT = 0.6
MEMORY_WEIGHT = 0.8
FRIEND_WEIGHT = 0.3
ROMANCE_WEIGHT = 0.8     # how much being drawn to someone counts for romance
ADMIRER_PULL = 1.0       # someone who courted you: answering them draws you more
UNANSWERED_PENALTY = 0.5 # someone you courted who never answered: less
FAMILY_WEIGHT = 1.0      # wanting a child (or not), and a partner who does
CARE_WEIGHT = 1.5        # a child who needs looking after
OTHERS_CHILD_BOND = 0.3  # someone else's child pulls less than your own
WALKING_PULL = 1.0       # an agent who walks a lot is drawn to pave and dig wells
GATHERING_PULL = 1.0     # a gathering one has heard of, by a host one likes
FAITH_PULL = 0.6         # one's own faith, felt more as it fades unpractised
COMMIT_PULL = 0.8        # carrying on with what one set out to do (x 0.5-1.5 by conscientiousness)
FAITH_ACTIONS = {"pray", "worship", "perform_ritual"}
WARNING_PULL = 2.5       # a warned disaster that will reach where one stands: take shelter
SEVERITY = {"minor": 0.25, "moderate": 0.5, "major": 0.75, "catastrophic": 1.0}
NIGHT_REST_PULL = 2.5
WORK_PULL = 0.3
OWN_JOB_PULL = 0.6
EVENING_SOCIAL_PULL = 0.3
GOAL_PULL = 0.5
TEMPERATURE = 0.15

# Actions that can get the agent killed, and how dangerous they are (0-1).
# A careful or already-hurt agent weighs that heavily; a reckless one doesn't.
DANGER = {"fight": 1.0}
DANGER_WEIGHT = 1.5

# Respect for the law: how much a ban in the agent's own government weighs
# against an action, scaled by how conscientious and agreeable it is.
LAW_WEIGHT = 1.5


class ActionMemory:
    """What has worked for one agent: a running success rate per action."""

    def __init__(self, learning_rate: float = 0.2):
        self.rate: Dict[str, float] = {}
        self.learning_rate = learning_rate

    def expectation(self, action: str) -> float:
        return self.rate.get(action, 0.5)  # untried: no opinion

    def record(self, action: str, worked: float) -> None:
        """worked: 0-1 (a bool counts as 0 or 1)."""
        old = self.expectation(action)
        self.rate[action] = old + self.learning_rate * (float(worked) - old)


class UtilityBrain:
    def __init__(self, sim, candidates: List[str]):
        self.sim = sim
        self.candidates = list(candidates)

    def considered_actions(self) -> List[str]:
        return list(self.candidates)

    # -- scoring -------------------------------------------------------------

    def utility(self, agent, action: str, part_of_day: Optional[str] = None,
                goal_action: Optional[str] = None, friendship: float = 0.0,
                banned: frozenset = frozenset()) -> float:
        from agents.daily_life import JOBS, SLEEP, WORK, FREE_TIME
        needs = agent.needs.needs
        need_term = sum(w * needs[n].get_urgency() for n, w in ACTION_NEEDS.get(action, {}).items() if n in needs)
        trait_term = sum(w * 2.0 * (agent.personality.get_trait(t) - 0.5)
                         for t, w in ACTION_TRAITS.get(action, {}).items())
        memory = getattr(agent, "action_memory", None)
        memory_term = (memory.expectation(action) - 0.5) if memory else 0.0

        plan_term = 0.0
        if part_of_day == SLEEP and action == "rest":
            plan_term += NIGHT_REST_PULL
        elif part_of_day == WORK:
            job = getattr(getattr(agent, "work_life", None), "job", None)
            if job and action in JOBS[job].actions:
                plan_term += OWN_JOB_PULL
            elif any(action in j.actions for j in JOBS.values()):
                plan_term += WORK_PULL
        elif part_of_day == FREE_TIME and action in SOCIAL_ACTIONS:
            plan_term += EVENING_SOCIAL_PULL
        if goal_action and action == goal_action:
            plan_term += GOAL_PULL
        from agents import commitment
        set_out = commitment.current(agent, self.sim.world.time.current_tick)
        if set_out is not None and action == set_out.action:
            plan_term += COMMIT_PULL * (0.5 + agent.personality.get_trait("conscientiousness"))

        danger = DANGER.get(action, 0.0)
        danger_term = 0.0
        if danger:
            caution = 1.0 - agent.personality.get_trait("risk_taking")
            hurt = 1.0 - max(0.0, min(100.0, agent.health)) / 100.0
            danger_term = danger * (caution + hurt)
        # Liking someone draws you to do things with them, and away from hurting
        # them or leaving them
        liking_term = -friendship if action in ("fight", "separate") else friendship
        if action == "separate":
            need_term *= max(0.0, 1.0 - friendship)
        person_weight = {"seek_romance": ROMANCE_WEIGHT, "try_for_child": FAMILY_WEIGHT,
                         "care_for_child": CARE_WEIGHT}.get(action, FRIEND_WEIGHT)

        law_term = 0.0
        if action in banned:
            p = agent.personality
            law_term = (p.get_trait("conscientiousness") + p.get_trait("agreeableness")) / 2.0

        return (NEED_WEIGHT * need_term + TRAIT_WEIGHT * trait_term + MEMORY_WEIGHT * memory_term
                + person_weight * liking_term + plan_term - DANGER_WEIGHT * danger_term
                - LAW_WEIGHT * law_term + self._state_pull(agent, action))

    def _state_pull(self, agent, action: str) -> float:
        """What the agent's own life adds: one who has been walking a lot feels
        the need for roads (and for water closer by); one who has heard a
        disaster is coming its way feels the pull of shelter."""
        if action == "hide":
            return self._warning_pull(agent)
        if action in FAITH_ACTIONS:
            return self._faith_pull(agent)
        if action == "attend_event":
            # A gathering it has heard of: more so if it likes the host
            gatherings = getattr(self.sim, "gatherings", None)
            if gatherings is None:
                return 0.0
            rm = self.sim.relationship_manager
            best = 0.0
            for g in gatherings.known_to(agent.id, self.sim.world.time.current_tick):
                rel = rm.get_relationship(agent.id, g.organizer)
                liking = rel.strength if rel is not None and rel.relationship_type.value != "rivalry" else 0.0
                best = max(best, GATHERING_PULL * (0.5 + liking))
            return best
        if action not in ("build_road", "dig_well"):
            return 0.0
        works = getattr(self.sim, "infrastructure", None)
        if works is None:
            return 0.0
        burden = works.walking_burden(agent.id, self.sim.world.time.current_tick)
        return WALKING_PULL * burden * (1.0 if action == "build_road" else 0.5)

    def _faith_pull(self, agent) -> float:
        """An agent's own faith, felt more the longer since it last practised
        it: nothing just after, FAITH_PULL by the time it would lapse. (Holding a
        faith used to weigh nothing at all: followers practised about once in
        400 ticks and lapsed.)"""
        religion = getattr(self.sim, "religion", None)
        if religion is None or religion.get_agent_religion(agent.id) is None:
            return 0.0
        last = getattr(religion, "last_practice", {}).get(agent.id)
        if last is None:
            return 0.0
        since = self.sim.world.time.current_tick - last
        return FAITH_PULL * min(1.0, max(0, since) / religion.LAPSE_TICKS)

    def _warning_pull(self, agent) -> float:
        """The worst warned disaster that will reach where the agent is: more
        the worse it is and the sooner it comes, and more for a careful agent
        than a reckless one. (The same warnings are in its perception.)"""
        disasters = getattr(self.sim, "disasters", None)
        if disasters is None:
            return 0.0
        now = self.sim.world.time.current_tick
        caution = 1.0 - agent.personality.get_trait("risk_taking")
        best = 0.0
        for warning in getattr(disasters, "pending_warnings", []):
            d = warning["disaster"]
            if math.hypot(agent.location.x - d.location_x, agent.location.y - d.location_y) >= d.radius:
                continue
            ticks = max(0, warning["impact_tick"] - now)
            urgency = 1.0 if ticks <= 6 else max(0.3, 1.0 - (ticks - 6) / 30.0)
            best = max(best, WARNING_PULL * SEVERITY.get(d.severity.value, 0.5) * urgency * (0.5 + caution))
        return best

    # -- targets -------------------------------------------------------------

    def _pick_target(self, agent, action: str, perceptions: Dict) -> Tuple[Optional[str], float]:
        """A partner for actions done with someone: sick people for healing,
        otherwise people nearby or known, favouring those the agent likes
        (or, for a fight, likes least). Returns (agent id, how much they're liked)."""
        if action in ROMANCE_ACTIONS:
            return self._romance_target(agent, action)
        if action == "try_for_child":
            return self._child_wish(agent)
        if action == "care_for_child":
            return self._child_in_need(agent)
        alive = {a.id: a for a in self.sim.world.agents if a.alive and a.id != agent.id}
        if action in NEEDS_SICK_TARGET:
            sick = [a for a in alive.values() if self.sim.health.is_agent_sick(a.id)]
            if not sick:
                return None, 0.0
            return min(sick, key=lambda a: agent.location.distance_to(a.location)).id, 0.0

        liking = {}
        for r in self.sim.relationship_manager.get_agent_relationships(agent.id):
            other = r.agent_b if r.agent_a == agent.id else r.agent_a
            if other in alive:
                liking[other] = r.strength if r.relationship_type.value != "rivalry" else -r.strength
        pool = {a["id"] for a in perceptions.get("nearby_agents", []) if a["id"] in alive} | set(liking)
        if not pool:
            pool = set(alive)
        if action == "convert":
            # someone who doesn't already share its faith
            religion = self.sim.religion
            mine = religion.get_agent_religion(agent.id)
            pool = {p for p in (pool or set(alive)) if religion.get_agent_religion(p) is not mine}
        if not pool:
            return None, 0.0
        people = sorted(pool)   # a set's order isn't stable; the dice must pick from a fixed order
        sign = -1.0 if action == "fight" else 1.0
        weights = [math.exp(2.0 * sign * liking.get(p, 0.0)) for p in people]
        chosen = random.choices(people, weights=weights)[0]
        return chosen, liking.get(chosen, 0.0)

    def _romance_target(self, agent, action: str) -> Tuple[Optional[str], float]:
        """The partner (for time together, or to leave); for someone single, a
        person it has met and is free to court, picked by how drawn the agent
        is to them. Someone
        who courted the agent pulls more; someone it courted who never answered
        pulls less. Returns (agent id, pull)."""
        from life import family
        rm = self.sim.relationship_manager
        partner = family.partner_of(agent, self.sim._get_agent_by_id)
        if action == "separate" or partner is not None:
            if partner is None:
                return None, 0.0
            return partner.id, family.liking(rm, agent, partner)
        now = self.sim.world.time.current_tick
        people, pulls = [], []
        for other in self.sim.world.agents:
            if not other.alive or other.id == agent.id or not family.free_to_court(agent, other, rm)[0]:
                continue
            pull = family.attraction(rm, agent, other)
            if family.recently(agent.admirers, other.id, now):
                pull += ADMIRER_PULL * pull
            elif family.recently(other.admirers, agent.id, now):
                pull -= UNANSWERED_PENALTY
            people.append(other.id)
            pulls.append(pull)
        if not people:
            return None, 0.0
        i = random.choices(range(len(people)), weights=[math.exp(2.0 * p) for p in pulls])[0]
        return people[i], pulls[i]

    def _child_wish(self, agent) -> Tuple[Optional[str], float]:
        """(partner id, pull): wanting a child pulls if the agent's life profile
        says it wants (more) children, pushes if not; a partner who has said
        they want one pulls by how much the agent likes them."""
        from life import family
        partner = family.partner_of(agent, self.sim._get_agent_by_id)
        if partner is None:
            return None, 0.0
        profile = self.sim.life_system.life_profiles.get(agent.id)
        if profile is not None and profile.wants_children and len(agent.children_ids) < profile.ideal_children_count:
            pull = profile.family_priority
        else:
            pull = -0.5
        if partner.child_wish_tick is not None and \
                self.sim.world.time.current_tick - partner.child_wish_tick <= family.INTEREST_MEMORY_TICKS:
            pull += max(0.0, family.liking(self.sim.relationship_manager, agent, partner))
        return partner.id, pull

    def _child_in_need(self, agent) -> Tuple[Optional[str], float]:
        """(child id, pull): the child who needs looking after most, weighted
        by bond (one's own children fully, others' less, closer ones first)."""
        from life import family
        best, best_pull = None, 0.0
        own = set(agent.children_ids)
        for child in self.sim.world.agents:
            if child.id == agent.id or not family.is_young(child):
                continue
            mine = child.id in own
            if not mine and agent.location.distance_to(child.location) > family.CARE_REACH:
                continue
            pull = (1.0 if mine else OTHERS_CHILD_BOND) * family.neediness(child)
            if best is None or pull > best_pull:
                best, best_pull = child.id, pull
        return best, best_pull

    # -- choosing ------------------------------------------------------------

    def options(self, agent, perceptions: Dict, can_run, part_of_day=None, goal_action=None):
        """Every runnable action with its utility, as (utility, Action)."""
        from agents.agent import Action, ActionType, Position
        banned = frozenset(law.prohibition for law in self.sim.governance_manager.laws_binding(agent.id)
                           if law.prohibition)
        scored = []
        for name in self.candidates:
            target, liked = (None, 0.0)
            if name in NEEDS_TARGET:
                target, liked = self._pick_target(agent, name, perceptions)
                if target is None and name in NEEDS_SUITABLE_TARGET:
                    continue
            position = None
            if name in NEEDS_PLACE:
                position = Position(agent.location.x + random.uniform(-20, 20),
                                    agent.location.y + random.uniform(-20, 20))
            action = Action(ActionType(name), target_agent=target, target_position=position)
            if not can_run(action):
                continue
            scored.append((self.utility(agent, name, part_of_day, goal_action, liked, banned), action))
        return scored

    def choose(self, agent, perceptions: Dict, can_run, part_of_day=None, goal_action=None):
        """Sample an action: softmax over every runnable action's utility."""
        from agents.agent import Action, ActionType
        scored = self.options(agent, perceptions, can_run, part_of_day, goal_action)
        if not scored:
            return Action(ActionType.REST)
        top = max(u for u, _ in scored)
        weights = [math.exp((u - top) / TEMPERATURE) for u, _ in scored]
        return random.choices([a for _, a in scored], weights=weights)[0]
