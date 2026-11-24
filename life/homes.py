"""
Homes: where an agent lives, and going home to sleep.

In Smallville every agent wakes up at home, goes out into town and comes back
at night; the town's paths are worn by those trips. Here:

- When an agent finishes a shelter (a building whose purpose is shelter),
  it becomes home to its builders who don't have a standing home yet.
- Partners share a home (one without moves in with the other when they
  pair up); a newborn lives with its mother.
- An agent that chooses to rest at night while its home is farther than
  HOME_RADIUS walks home first (one step a turn; roads help), unless it is
  exhausted, when it sleeps where it is.
- Sleeping at home is better: more energy and sleep, and the shelter and
  security needs are met. Sleeping out is what everyone did before.

A home that collapses is no longer anyone's home. Nobody is assigned a home
they didn't build or move into.
"""

from typing import Optional

HOME_RADIUS = 3.0
SLEEP_FROM, SLEEP_UNTIL = 20, 6
EXHAUSTED_ENERGY = 15.0
HOME_ENERGY, HOME_SLEEP = 30.0, 0.7          # vs 20 and 0.5 sleeping out


def is_night(hour: int) -> bool:
    return hour >= SLEEP_FROM or hour < SLEEP_UNTIL


def home_of(dbs, agent) -> Optional[object]:
    """The agent's home building, if it still stands. dbs: the building system."""
    home_id = getattr(agent, "home_id", None)
    if not home_id:
        return None
    building = dbs.buildings.get(home_id) if dbs is not None else None
    if building is None or building.collapsed or not building.is_complete:
        agent.home_id = None
        return None
    return building


def move_in(dbs, agent, building, tick: int, why: str, counter=None) -> bool:
    """Make `building` the agent's home if it has none. Returns True if it did."""
    if home_of(dbs, agent) is not None:
        return False
    agent.home_id = building.id
    agent.memory_stream.add(tick, f"{building.name} is my home now ({why})", 0.6)
    if counter is not None:
        counter["moved_in"] += 1
    return True


def is_shelter(dbs, building) -> bool:
    design = dbs.designs.get(building.design_id)
    purposes = getattr(design, "intended_purposes", []) if design is not None else []
    return "shelter" in purposes or bool(building.shelter_value)


def distance_home(dbs, agent) -> Optional[float]:
    home = home_of(dbs, agent)
    if home is None:
        return None
    hx, hy = home.location
    return ((agent.location.x - hx) ** 2 + (agent.location.y - hy) ** 2) ** 0.5
