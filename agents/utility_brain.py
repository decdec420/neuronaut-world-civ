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
- people: for actions with a partner, how much the agent likes them
- danger: actions that can get it killed weigh less for careful or hurt agents
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

# What an action tends to satisfy (weights add up to ~1)
ACTION_NEEDS: Dict[str, Dict[N, float]] = {
    "eat": {N.HUNGER: 1.0},
    "drink": {N.THIRST: 1.0},
    "rest": {N.SLEEP: 1.0},
    "gather_food": {N.HUNGER: 0.7, N.RESOURCES: 0.3},
    "gather_water": {N.THIRST: 0.8, N.RESOURCES: 0.2},
    "hunt": {N.HUNGER: 0.6, N.ACHIEVEMENT: 0.2, N.RESOURCES: 0.2},
    "plant_crops": {N.HUNGER: 0.3, N.RESOURCES: 0.4, N.SECURITY: 0.3},
    "tend_crops": {N.HUNGER: 0.3, N.RESOURCES: 0.4, N.SECURITY: 0.3},
    "harvest": {N.HUNGER: 0.5, N.RESOURCES: 0.5},
    "raise_animals": {N.RESOURCES: 0.5, N.SECURITY: 0.3, N.HUNGER: 0.2},
    "explore": {N.GROWTH: 0.6, N.RESOURCES: 0.2, N.ACHIEVEMENT: 0.2},
    "move": {N.GROWTH: 0.3},
    "heal": {N.MEANING: 0.4, N.BELONGING: 0.3, N.RECOGNITION: 0.3},
    "cure": {N.MEANING: 0.4, N.BELONGING: 0.3, N.RECOGNITION: 0.3},
    "diagnose": {N.MEANING: 0.4, N.GROWTH: 0.3, N.RECOGNITION: 0.3},
    "gather_materials": {N.RESOURCES: 0.7, N.SECURITY: 0.3},
    "chop_wood": {N.RESOURCES: 0.8, N.SECURITY: 0.2},
    "mine": {N.RESOURCES: 0.8, N.SECURITY: 0.2},
    "build": {N.SHELTER: 0.5, N.SECURITY: 0.2, N.ACHIEVEMENT: 0.3},
    "experiment": {N.CREATIVITY: 0.4, N.ACHIEVEMENT: 0.3, N.GROWTH: 0.3},
    "smelt_ore": {N.ACHIEVEMENT: 0.4, N.GROWTH: 0.3, N.RESOURCES: 0.3},
    "refine_material": {N.ACHIEVEMENT: 0.4, N.GROWTH: 0.3, N.RESOURCES: 0.3},
    "create_alloy": {N.ACHIEVEMENT: 0.4, N.GROWTH: 0.3, N.CREATIVITY: 0.3},
    "perform_chemistry": {N.ACHIEVEMENT: 0.4, N.GROWTH: 0.3, N.CREATIVITY: 0.3},
    "discover_element": {N.GROWTH: 0.5, N.ACHIEVEMENT: 0.3, N.RECOGNITION: 0.2},
    "discover_material": {N.GROWTH: 0.5, N.ACHIEVEMENT: 0.3, N.RECOGNITION: 0.2},
    "discover_energy": {N.GROWTH: 0.5, N.ACHIEVEMENT: 0.3, N.RECOGNITION: 0.2},
    "build_power_plant": {N.ACHIEVEMENT: 0.5, N.STATUS: 0.3, N.RESOURCES: 0.2},
    "operate_power_plant": {N.ACHIEVEMENT: 0.4, N.STATUS: 0.3, N.RESOURCES: 0.3},
    "teach": {N.MEANING: 0.4, N.RECOGNITION: 0.3, N.BELONGING: 0.3},
    "write": {N.MEANING: 0.4, N.GROWTH: 0.3, N.RECOGNITION: 0.3},
    "socialize": {N.FRIENDSHIP: 0.5, N.BELONGING: 0.5},
    "seek_romance": {N.ROMANCE: 0.5, N.SEX: 0.5},
    "celebrate": {N.BELONGING: 0.6, N.MEANING: 0.4},
    "tell_story": {N.BELONGING: 0.4, N.RECOGNITION: 0.3, N.CREATIVITY: 0.3},
    "play_game": {N.BELONGING: 0.5, N.FRIENDSHIP: 0.3, N.ACHIEVEMENT: 0.2},
    "create_art": {N.CREATIVITY: 0.6, N.MEANING: 0.4},
    "gamble": {N.STATUS: 0.4, N.RESOURCES: 0.3, N.ACHIEVEMENT: 0.3},
    "trade": {N.RESOURCES: 0.6, N.FRIENDSHIP: 0.2, N.STATUS: 0.2},
    "mint_coins": {N.RESOURCES: 0.5, N.STATUS: 0.5},
    "open_bank": {N.STATUS: 0.5, N.RESOURCES: 0.5},
    "apply_for_loan": {N.RESOURCES: 1.0},
    "send_caravan": {N.RESOURCES: 0.5, N.STATUS: 0.3, N.GROWTH: 0.2},
    "join_tax_revolt": {N.STATUS: 0.5, N.SECURITY: 0.5},
    "govern": {N.STATUS: 0.5, N.RECOGNITION: 0.3, N.SECURITY: 0.2},
    "make_law": {N.STATUS: 0.3, N.SECURITY: 0.4, N.MEANING: 0.3},
    "vote": {N.BELONGING: 0.5, N.STATUS: 0.2, N.SECURITY: 0.3},
    "claim_territory": {N.SECURITY: 0.5, N.STATUS: 0.3, N.RESOURCES: 0.2},
    "guard": {N.SECURITY: 0.8, N.STATUS: 0.2},
    "patrol": {N.SECURITY: 0.8, N.STATUS: 0.2},
    "pray": {N.MEANING: 0.7, N.SECURITY: 0.3},
    "worship": {N.MEANING: 0.6, N.BELONGING: 0.4},
    "perform_ritual": {N.MEANING: 0.5, N.BELONGING: 0.3, N.STATUS: 0.2},
    "build_temple": {N.MEANING: 0.5, N.ACHIEVEMENT: 0.3, N.STATUS: 0.2},
    # Fighting puts you in danger rather than making you safe; what draws
    # people to it is standing and taking what others have (see DANGER below)
    "fight": {N.STATUS: 0.5, N.RESOURCES: 0.5},
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
    "celebrate": {"extraversion": 0.6, "openness": 0.2},
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
    "build_temple": {"rationality": -0.4, "conscientiousness": 0.3, "ambition": 0.3},
    "fight": {"aggression": 0.8, "risk_taking": 0.3, "agreeableness": -0.4},
}

SOCIAL_ACTIONS = {"socialize", "seek_romance", "celebrate", "tell_story", "play_game", "create_art"}
NEEDS_TARGET = {"socialize", "seek_romance", "trade", "teach", "tell_story", "play_game", "gamble",
                "fight", "heal", "cure", "diagnose"}
NEEDS_SICK_TARGET = {"heal", "cure", "diagnose"}
NEEDS_PLACE = {"move", "explore"}

# How much each part of the utility counts, and how sharply the agent picks
NEED_WEIGHT = 1.5
TRAIT_WEIGHT = 0.6
MEMORY_WEIGHT = 0.8
FRIEND_WEIGHT = 0.3
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


class ActionMemory:
    """What has worked for one agent: a running success rate per action."""

    def __init__(self, learning_rate: float = 0.2):
        self.rate: Dict[str, float] = {}
        self.learning_rate = learning_rate

    def expectation(self, action: str) -> float:
        return self.rate.get(action, 0.5)  # untried: no opinion

    def record(self, action: str, succeeded: bool) -> None:
        old = self.expectation(action)
        self.rate[action] = old + self.learning_rate * ((1.0 if succeeded else 0.0) - old)


class UtilityBrain:
    def __init__(self, sim, candidates: List[str]):
        self.sim = sim
        self.candidates = list(candidates)

    def considered_actions(self) -> List[str]:
        return list(self.candidates)

    # -- scoring -------------------------------------------------------------

    def utility(self, agent, action: str, part_of_day: Optional[str] = None,
                goal_action: Optional[str] = None, friendship: float = 0.0) -> float:
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

        danger = DANGER.get(action, 0.0)
        danger_term = 0.0
        if danger:
            caution = 1.0 - agent.personality.get_trait("risk_taking")
            hurt = 1.0 - max(0.0, min(100.0, agent.health)) / 100.0
            danger_term = danger * (caution + hurt)
        # Liking someone draws you to do things with them, and away from hurting them
        liking_term = -friendship if action == "fight" else friendship

        return (NEED_WEIGHT * need_term + TRAIT_WEIGHT * trait_term + MEMORY_WEIGHT * memory_term
                + FRIEND_WEIGHT * liking_term + plan_term - DANGER_WEIGHT * danger_term)

    # -- targets -------------------------------------------------------------

    def _pick_target(self, agent, action: str, perceptions: Dict) -> Tuple[Optional[str], float]:
        """A partner for actions done with someone: sick people for healing,
        otherwise people nearby or known, favouring those the agent likes
        (or, for a fight, likes least). Returns (agent id, how much they're liked)."""
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
        if not pool:
            return None, 0.0
        people = list(pool)
        sign = -1.0 if action == "fight" else 1.0
        weights = [math.exp(2.0 * sign * liking.get(p, 0.0)) for p in people]
        chosen = random.choices(people, weights=weights)[0]
        return chosen, liking.get(chosen, 0.0)

    # -- choosing ------------------------------------------------------------

    def options(self, agent, perceptions: Dict, can_run, part_of_day=None, goal_action=None):
        """Every runnable action with its utility, as (utility, Action)."""
        from agents.agent import Action, ActionType, Position
        scored = []
        for name in self.candidates:
            target, liked = (None, 0.0)
            if name in NEEDS_TARGET:
                target, liked = self._pick_target(agent, name, perceptions)
                if target is None and name in NEEDS_SICK_TARGET:
                    continue
            position = None
            if name in NEEDS_PLACE:
                position = Position(agent.location.x + random.uniform(-20, 20),
                                    agent.location.y + random.uniform(-20, 20))
            action = Action(ActionType(name), target_agent=target, target_position=position)
            if not can_run(action):
                continue
            scored.append((self.utility(agent, name, part_of_day, goal_action, liked), action))
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
