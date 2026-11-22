"""
Partnership and family: what the world allows, not what anyone does.

Agents court, partner and separate only by choosing to (the actions live in
engine/handlers/family.py). This module holds what the handlers, both brains
and the perception builder must agree on: who is old enough, who is free to
partner, how drawn one agent is to another, and how long an expressed wish is
remembered.

Consent: a partnership forms only when each of the two has chosen, on its own
turn, to court the other. Either partner can end it alone. A child is
conceived only after both partners have said, each on its own turn, that they
want one (try_for_child), and even then not every time.

Children: babies (0-1) can only rest, eat and drink what they're given, and
reach out to people; children (2-15) can also fetch food and water, play,
explore and make things. Anyone grown can look after a child
(care_for_child): feed it, give it water, keep it company. Parents feel that
pull most.
"""

from typing import Dict, Optional, Tuple

ADULT_AGE = 16
# How long courting someone, or saying you want a child, is remembered (3 days)
INTEREST_MEMORY_TICKS = 432
CONCEPTION_CHANCE = 0.3   # each time both partners try, at peak fertility
PREGNANCY_YEARS = 0.75    # in life years (life/aging.py)
CARE_REACH = 10.0         # how close you must be to look after a child

BABY_ACTIONS = frozenset({"rest", "eat", "drink", "socialize"})
CHILD_ACTIONS = BABY_ACTIONS | frozenset({
    "gather_food", "gather_water", "explore", "move", "play_game", "tell_story",
    "create_art", "celebrate", "pray", "worship", "experiment"})


def allowed_at_stage(agent, action_name: str) -> bool:
    """Whether someone this age can do this (action_name: the action that runs)."""
    if agent.life_stage == "baby":
        return action_name in BABY_ACTIONS
    if agent.life_stage == "child":
        return action_name in CHILD_ACTIONS
    return True


def is_young(agent) -> bool:
    return agent.alive and agent.life_stage in ("baby", "child")


def fertility(age: int) -> float:
    """0-1, by age (the table LifeSystem has always used)."""
    if age < 18:
        return 0.0
    if age < 25:
        return 0.8
    if age < 35:
        return 1.0
    if age < 45:
        return 0.6
    if age < 55:
        return 0.2
    return 0.0


def mother_and_father(a, b) -> Optional[Tuple[object, object]]:
    """(mother, father) if these two could conceive together, else None."""
    genders = {a.gender.value: a, b.gender.value: b}
    if set(genders) != {"female", "male"}:
        return None
    return genders["female"], genders["male"]


def neediness(child) -> float:
    """0-1: how much a child needs looking after right now."""
    from engine.psychology import NeedType
    needs = child.needs.needs
    return max(needs[n].get_urgency() for n in (NeedType.HUNGER, NeedType.THIRST, NeedType.BELONGING,
                                                 NeedType.SECURITY) if n in needs)


def is_adult(agent) -> bool:
    return agent.age >= ADULT_AGE


def recently(marks: Dict[str, int], who: str, now: int) -> bool:
    """True if `who` is in `marks` (id -> tick) within INTEREST_MEMORY_TICKS."""
    tick = marks.get(who)
    return tick is not None and now - tick <= INTEREST_MEMORY_TICKS


def forget_old(marks: Dict[str, int], now: int) -> None:
    for who in [w for w, tick in marks.items() if now - tick > INTEREST_MEMORY_TICKS]:
        del marks[who]


def free_to_court(agent, other) -> Tuple[bool, str]:
    """Whether `agent` may court `other` (its own partner always counts)."""
    if other is None or other.id == agent.id or not other.alive:
        return False, "Nobody to court"
    if not is_adult(agent):
        return False, "Too young for romance"
    if not is_adult(other):
        return False, f"{other.name} is a child"
    if agent.partner_id == other.id:
        return True, ""
    if agent.partner_id:
        return False, "You already have a partner (separate first)"
    if other.partner_id:
        return False, f"{other.name} already has a partner"
    return True, ""


def liking(relationships, agent, other) -> float:
    """-1..1: how much `agent` likes `other` (rivals count against)."""
    rel = relationships.get_relationship(agent.id, other.id)
    if rel is None:
        return 0.0
    return -rel.strength if rel.relationship_type.value == "rivalry" else rel.strength


def attraction(relationships, agent, other) -> float:
    """0-1: how drawn `agent` is to `other`: how well they'd get on, its own
    romantic drive, and how much it already likes them."""
    compatibility = agent.personality.compatibility_with(other.personality)
    value = 0.4 * compatibility + 0.3 * agent.personality.sexuality + 0.3 * max(0.0, liking(relationships, agent, other))
    return max(0.0, min(1.0, value))


def partner_of(agent, find_agent) -> Optional[object]:
    """The agent's living partner, or None. find_agent: id -> agent."""
    if not agent.partner_id:
        return None
    partner = find_agent(agent.partner_id)
    return partner if partner is not None and partner.alive else None
