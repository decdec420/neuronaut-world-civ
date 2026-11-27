"""
Damaged buildings can be mended (engine/handlers/repair.py).

A disaster takes half a building's condition, a weak building shelters less
and falls more easily in the next one, and nothing could mend it: 'repair'
fell back to starting a new building. Now an agent who knows how to build
shelters can mend one with wood, stone or clay, its own home first, up to
the quality the building was made with.

    python3 -m pytest tests/test_repair.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act  # noqa: E402
from test_reachability import make_world, quiet  # noqa: E402


def house(sim, hid, at, durability, quality=0.8, builders=()):
    from world.dynamic_buildings import Building
    b = Building(id=hid, name=f"House {hid}", design_id="none", location=at, is_complete=True,
                 durability=durability, quality=quality, builder_ids=set(builders))
    sim.dynamic_building_system.buildings[hid] = b
    return b


def test_repair_is_its_own_action_now():
    from engine.simulation import UNHANDLED_ACTION_FALLBACKS
    from world.knowhow import needed_for
    assert "repair" not in UNHANDLED_ACTION_FALLBACKS
    assert needed_for("repair") == "shelter"


def test_an_agent_mends_its_own_home_first_up_to_its_quality():
    sim, roles = make_world()
    a = roles["actor"]
    x, y = a.location.x, a.location.y
    other = house(sim, "other", (x + 1, y), 0.2, builders=[a.id])
    home = house(sim, "home", (x, y), 0.3, quality=0.4)
    a.home_id = "home"
    a.inventory.items.clear()
    a.inventory.items.update({"wood": 2, "stone": 5})
    result = act(sim, a, "repair")
    assert result.success and result.metadata["building_id"] == "home", result.message
    assert round(home.durability, 2) == 0.4                       # +0.15, but no better than it was made
    assert sum(result.metadata["used"].values()) == 3 and a.inventory.items.get("stone") == 2
    assert other.durability == 0.2 and "mended it" in home.events[-1] and a.name in home.events[-1]
    assert home.repairs == 1


def test_nothing_to_mend_or_nothing_to_mend_it_with_is_refused():
    sim, roles = make_world()
    a = roles["actor"]
    a.inventory.items.update({"wood": 5})
    house(sim, "sound", (a.location.x, a.location.y), 0.9)
    from agents.agent import Action, ActionType
    handler = sim._handler_registry.get_handler(ActionType.REPAIR)
    ok, why = handler.validate(a, Action(ActionType.REPAIR))
    assert not ok and "Nothing" in why
    house(sim, "hurt", (a.location.x + 3, a.location.y), 0.2)
    a.inventory.items.clear()
    ok, why = handler.validate(a, Action(ActionType.REPAIR))
    assert not ok and "wood, stone or clay" in why


def test_a_far_building_is_walked_to_first():
    sim, roles = make_world()
    a = roles["actor"]
    a.inventory.items.update({"clay": 4})
    far = house(sim, "far", (a.location.x + 12, a.location.y), 0.2)
    start = (a.location.x, a.location.y)
    result = act(sim, a, "repair")
    assert result.success and result.metadata["arrived"] is False
    assert (a.location.x, a.location.y) != start and far.durability == 0.2


def test_at_the_dawn_only_those_who_can_build_shelters_can_mend_them():
    from test_knowhow import dawn_world
    sim, roles = dawn_world()
    a = roles["actor"]
    a.inventory.items.update({"wood": 5})
    house(sim, "hurt", (a.location.x, a.location.y), 0.2)
    assert not sim._agent_updater._can_run(a, _action("repair"))
    with quiet():
        sim.knowhow.learn(a, "stone_tools", "insight", 1)
        sim.knowhow.learn(a, "shelter", "insight", 2)
    assert sim._agent_updater._can_run(a, _action("repair"))


def _action(name):
    from agents.agent import Action, ActionType
    return Action(ActionType(name))


def test_a_damaged_home_draws_its_people_to_mend_it_more_the_worse_it_is():
    """A home relieves the shelter need whatever its state, so damage weighed
    nothing in the rule brain (agents/utility_brain.py _repair_pull)."""
    sim, roles = make_world()
    a = roles["actor"]
    brain = sim._agent_updater.utility_brain
    home = house(sim, "home", (a.location.x, a.location.y), 0.9, quality=0.9)
    a.home_id = "home"
    assert brain._repair_pull(a) == 0.0                           # sound: nothing to feel
    home.durability = 0.45
    slight = brain._repair_pull(a)
    home.durability = 0.1
    assert brain._repair_pull(a) > slight > 0.0
    a.home_id = None
    assert brain._repair_pull(a) == 0.0                           # someone else's house: no pull
