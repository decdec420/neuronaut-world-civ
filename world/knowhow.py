"""
Know-how: what each person knows how to do, and how it is found and passed on.

A world can start at the dawn (WORLD_START=dawn): its first people know only
what comes with being human (finding food and water, resting, talking, love,
looking after children, play, stories, barter, prayer, tinkering...). Every
other thing they might do needs know-how somebody has to work out first:
making fire, stone tools, shelters, farming, metal, writing, coins... A world
started with settlers (WORLD_START=settlers) begins with all of it known, as
every world did before.

How know-how appears and spreads (nothing makes it happen; it can):
- Insight: doing something related may give someone the idea (working stone
  may lead to stone tools; foraging the same plants, to farming). Tinkering
  (experiment) may lead to anything whose groundwork the person already has.
  An open, creative mind has more ideas.
- Watching: someone nearby doing it may be copied.
- Teaching: someone who knows can show someone who doesn't (teach).
- It lives only in people: when the last one who knew it dies, it is lost
  until someone works it out again.

Every first is recorded with the day and generation it happened in, next to
when humans first did it, so a run can be read against our own history.
Actions no know-how unlocks are innate. Children start knowing nothing more
than that, and learn from the people around them.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

TICKS_PER_DAY = 144
WATCH_RADIUS = 5.0     # close enough to see how it's done
WATCH_CHANCE = 0.03    # each time a learner sees it done
TEACH_REACH = 3.0      # teaching is done in person
TEACH_CHANCE = 0.5     # a lesson takes, for an average teacher and pupil
EXPERIMENT_BOOST = 3.0  # tinkering on purpose gives ideas more often than doing chores


@dataclass(frozen=True)
class KnowHow:
    name: str
    label: str                    # how it reads: "making fire"
    needs: Tuple[str, ...]        # know-how that has to come first
    unlocks: Tuple[str, ...]      # what it lets you do
    sparks: Tuple[str, ...]       # doing these may give you the idea
    chance: float                 # of the idea, each time, for an average mind
    # (Set from how often a village of 12 does the sparking things: roughly,
    # stone tools in the first week, fire within two, farming in the second
    # generation, metal and writing later; science and electricity only in
    # long runs. Tinkering (experiment) gives EXPERIMENT_BOOST times the chance
    # of anything the person has the groundwork for. A bigger village does
    # more, so it has more ideas.)
    humans: str                   # when humans first did it


KNOWHOW: Dict[str, KnowHow] = {k.name: k for k in (
    KnowHow("stone_tools", "making stone tools", (), ("chop_wood",),
            ("gather_materials", "explore", "gather_food"), 1 / 1500,
            "about 3.3 million years ago"),
    KnowHow("fire", "making fire", (), (),
            ("gather_materials", "chop_wood"), 1 / 1500,
            "about 1 million years ago"),
    KnowHow("hunting", "hunting", ("stone_tools",), ("hunt",),
            ("gather_food", "explore"), 1 / 2000,
            "about 500,000 years ago"),
    KnowHow("shelter", "building shelters", ("stone_tools",), ("build",),
            ("gather_materials", "chop_wood"), 1 / 1000,
            "about 400,000 years ago"),
    KnowHow("medicine", "healing with herbs", (), ("heal", "cure", "diagnose"),
            ("gather_food", "care_for_child"), 1 / 4000,
            "about 60,000 years ago"),
    KnowHow("art", "painting and carving", (), ("create_art",),
            ("tell_story", "celebrate", "gather_materials"), 1 / 2500,
            "about 45,000 years ago"),
    KnowHow("mining", "mining", ("stone_tools",), ("mine",),
            ("gather_materials", "explore"), 1 / 2500,
            "about 40,000 years ago"),
    KnowHow("farming", "farming", ("stone_tools",), ("plant_crops", "tend_crops", "harvest"),
            ("gather_food",), 1 / 8000,
            "about 12,000 years ago"),
    KnowHow("masonry", "masonry", ("shelter",), ("build_temple", "build_road", "dig_well"),
            ("build", "gather_materials"), 1 / 4000,
            "about 11,000 years ago"),
    KnowHow("herding", "herding animals", ("hunting",), ("raise_animals", "send_caravan"),
            ("hunt", "harvest"), 1 / 3000,
            "about 11,000 years ago"),
    KnowHow("metalworking", "smelting metal", ("fire", "mining"), ("smelt_ore", "create_alloy"),
            ("mine",), 1 / 6000,
            "about 7,000 years ago"),
    KnowHow("writing", "writing", ("art",), ("write",),
            ("create_art", "tell_story", "teach", "make_law"), 1 / 10000,
            "about 5,200 years ago"),
    KnowHow("glassmaking", "glassmaking", ("fire", "metalworking"), ("refine_material",),
            ("smelt_ore",), 1 / 5000,
            "about 4,500 years ago"),
    KnowHow("coinage", "coins and money", ("metalworking", "writing"),
            ("mint_coins", "open_bank", "apply_for_loan"),
            ("trade", "smelt_ore"), 1 / 8000,
            "about 2,600 years ago"),
    KnowHow("science", "natural science", ("writing", "metalworking"),
            ("perform_chemistry", "discover_element", "discover_material", "discover_energy"),
            ("write", "create_alloy", "refine_material"), 1 / 20000,
            "about 400 years ago"),
    KnowHow("electricity", "electricity", ("science", "glassmaking"),
            ("build_power_plant", "operate_power_plant", "build_streetlight"),
            ("discover_energy", "perform_chemistry"), 1 / 30000,
            "about 150 years ago"),
)}

# action -> the know-how it takes (actions not here are innate)
NEEDED_FOR: Dict[str, str] = {action: k.name for k in KNOWHOW.values() for action in k.unlocks}
# action -> know-how doing it may give the idea of
SPARKED_BY: Dict[str, List[str]] = {}
for _k in KNOWHOW.values():
    for _action in _k.sparks:
        SPARKED_BY.setdefault(_action, []).append(_k.name)
SPARKED_BY = {a: sorted(ks) for a, ks in SPARKED_BY.items()}


def needed_for(action_name: str) -> Optional[str]:
    return NEEDED_FOR.get(action_name)


def knows(agent, name: str) -> bool:
    known = getattr(agent, 'knowhow', None)
    return known is None or name in known


def knows_action(agent, action_name: str) -> bool:
    """Whether the agent knows how to do this (innate, or know-how it has).
    An agent whose knowhow is None knows everything (a settlers' world, or a
    world saved before know-how existed)."""
    need = NEEDED_FOR.get(action_name)
    return need is None or knows(agent, need)


def can_learn(agent, name: str) -> bool:
    """Not known yet, and everything it builds on is."""
    known = getattr(agent, 'knowhow', None)
    if known is None or name in known:
        return False
    return all(n in known for n in KNOWHOW[name].needs)


def not_known_message(action_name: str) -> str:
    return f"You don't know how to {action_name.replace('_', ' ')} yet (it takes {KNOWHOW[NEEDED_FOR[action_name]].label})"


def mind(agent) -> float:
    """0.5-1.5: how readily this person has ideas."""
    p = agent.personality
    return 0.5 + 0.5 * p.get_trait("openness") + 0.5 * p.get_trait("creativity")


class KnowHowLedger:
    """Firsts, losses and teaching for one world (sim.knowhow)."""

    def __init__(self, sim, active: bool):
        self.sim = sim
        self.active = active            # False: a settlers' world, everyone knows everything
        self.firsts: Dict[str, Dict] = {}
        self.lost: List[Dict] = []
        self.counts = {'insight': 0, 'watched': 0, 'taught': 0, 'lost': 0}
        self._known_last: set = set()

    # -- learning --------------------------------------------------------------

    def learn(self, agent, name: str, how: str, tick: int, teacher=None) -> bool:
        """Agent now knows `name` (how: insight, watched or taught). Logs a
        first, or a rediscovery of something lost."""
        known = getattr(agent, 'knowhow', None)
        if known is None or name in known:
            return False
        lost_before = name in self.firsts and name not in self._known_now()
        known.add(name)
        self.counts[how] = self.counts.get(how, 0) + 1
        k = KNOWHOW[name]
        from engine.events import EventCategory, EventImportance
        log = getattr(self.sim, 'event_logger', None)
        day = tick // TICKS_PER_DAY + 1
        generation = getattr(agent, 'generation', 1)
        if name not in self.firsts or lost_before:
            if name not in self.firsts:
                self.firsts[name] = {'knowhow': name, 'label': k.label, 'who': agent.name, 'agent_id': agent.id,
                                     'tick': tick, 'day': day, 'generation': generation, 'how': how,
                                     'humans': k.humans}
                title = f"💡 {agent.name} worked out {k.label}: the first in the world"
            else:
                title = f"💡 {agent.name} worked out {k.label} again, after it was lost"
            if log:
                log.log_event(EventCategory.CULTURAL, EventImportance.MAJOR, title,
                              f"Day {day}, generation {generation}. Humans first did this {k.humans}.",
                              tick, [agent.id])
        elif how == 'taught' and teacher is not None and log:
            log.log_event(EventCategory.SOCIAL, EventImportance.MINOR,
                          f"{teacher.name} taught {agent.name} {k.label}", "", tick, [agent.id, teacher.id])
        self._known_last.add(name)
        return True

    def _known_now(self) -> set:
        known = set()
        for a in self.sim.world.agents:
            if a.alive and getattr(a, 'knowhow', None) is not None:
                known |= a.knowhow
        return known

    def after_action(self, agent, action_name: str, result: Dict, tick: int) -> None:
        """An idea from what it just did, and onlookers who saw how it's done."""
        if not self.active or getattr(agent, 'knowhow', None) is None or not isinstance(result, dict):
            return
        if action_name == 'experiment':
            ideas = [n for n in sorted(KNOWHOW) if can_learn(agent, n)]
            boost = EXPERIMENT_BOOST
        else:
            ideas = [n for n in SPARKED_BY.get(action_name, ()) if can_learn(agent, n)]
            boost = 1.0
        for name in ideas:
            if random.random() < KNOWHOW[name].chance * boost * mind(agent):
                self.learn(agent, name, 'insight', tick)
                break
        need = NEEDED_FOR.get(action_name)
        if need is not None and result.get('success'):
            for other in self.sim.world.agents:
                if (other is not agent and other.alive and can_learn(other, need)
                        and other.location.distance_to(agent.location) <= WATCH_RADIUS
                        and random.random() < WATCH_CHANCE):
                    self.learn(other, need, 'watched', tick)

    def lesson(self, teacher, pupil) -> Optional[str]:
        """What teacher would show pupil: something it knows that pupil can learn."""
        for name in sorted(KNOWHOW):
            if knows(teacher, name) and can_learn(pupil, name):
                return name
        return None

    def teach(self, teacher, pupil, tick: int) -> Tuple[Optional[str], bool]:
        """(what was taught, whether it took)."""
        name = self.lesson(teacher, pupil)
        if name is None:
            return None, False
        skill = min(1.0, teacher.skills.get_skill('teaching'))
        chance = TEACH_CHANCE * (0.5 + skill) * (0.5 + pupil.personality.get_trait("openness"))
        took = random.random() < chance
        if took:
            self.learn(pupil, name, 'taught', tick, teacher=teacher)
        return name, took

    # -- loss ----------------------------------------------------------------------

    def update(self, tick: int) -> None:
        """Know-how nobody alive knows any more is lost."""
        if not self.active or tick % 12:
            return
        now = self._known_now()
        for name in sorted(self._known_last - now):
            k = KNOWHOW[name]
            self.lost.append({'knowhow': name, 'label': k.label, 'tick': tick, 'day': tick // TICKS_PER_DAY + 1})
            self.counts['lost'] += 1
            log = getattr(self.sim, 'event_logger', None)
            if log:
                from engine.events import EventCategory, EventImportance
                log.log_event(EventCategory.CULTURAL, EventImportance.MAJOR,
                              f"🕯️ The knowledge of {k.label} has been lost",
                              "Nobody alive knows how any more.", tick, [])
        self._known_last = now

    # -- reading -------------------------------------------------------------------

    def snapshot(self) -> Dict:
        now = self._known_now() if self.active else set(KNOWHOW)
        alive = [a for a in self.sim.world.agents if a.alive]
        return {
            'active': self.active,
            'firsts': sorted(self.firsts.values(), key=lambda f: f['tick']),
            'lost': self.lost[-20:],
            'known_now': sorted(now),
            'knowers': {n: sum(1 for a in alive if knows(a, n)) for n in sorted(now)},
            'not_yet': [{'knowhow': k.name, 'label': k.label, 'humans': k.humans}
                        for k in KNOWHOW.values() if k.name not in now],
            'counts': dict(self.counts),
        }
