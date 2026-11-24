"""
Public works agents can build: roads, wells, street lights (world/infrastructure.py).

    python3 -m pytest tests/test_infrastructure.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act  # noqa: E402
from test_reachability import make_world  # noqa: E402


def _land(sim, x, y):
    """The nearest dry tile to (x, y)."""
    from agents.agent import Position
    tiles = [t for t in sim.world.map.tiles.values() if t.terrain.value != "water"]
    t = min(tiles, key=lambda t: (t.x - x) ** 2 + (t.y - y) ** 2)
    return Position(float(t.x), float(t.y))


def _walk(sim, agent, tx, ty, times=8):
    for tick in range(times):
        sim.infrastructure.step_toward(agent, sim.pathfinder, tx, ty, tick)


def test_roads_go_where_agents_walk_and_make_walking_faster():
    from agents.agent import Action, ActionType, Position
    sim, roles = make_world()
    a, b = roles["actor"], roles["neighbour"]
    handler = sim._handler_registry.get_handler(ActionType.BUILD_ROAD)
    ok, why = handler.validate(a, Action(ActionType.BUILD_ROAD))
    assert not ok and "walk" in why  # nowhere it walks yet

    _walk(sim, a, 90, 50)            # a keeps going east
    assert sim.infrastructure.walking_burden(a.id, 8) > 0
    a.location = Position(50, 50)
    stone = a.inventory.items["stone"]
    result = act(sim, a, "build_road")
    assert result.success and len(sim.infrastructure.roads) == 6
    assert a.inventory.items["stone"] == stone - 12
    assert all(48 <= y <= 52 and x >= 50 for x, y in sim.infrastructure.roads)  # from here toward where it walks

    # Off road: one tile a tick. Along the road: three.
    b.location = Position(20, 20)
    sim.infrastructure.step_toward(b, sim.pathfinder, 20, 40, 1)
    assert abs(b.location.y - 20) == 1
    b.location = Position(50, 50)
    sim.infrastructure.step_toward(b, sim.pathfinder, 90, 50, 2)
    assert b.location.x - 50 == 3


def test_a_well_is_a_water_source_and_wells_are_spread_out():
    from agents.agent import Action, ActionType, Position
    from world.simulation import ResourceType
    sim, roles = make_world()
    a, b = roles["actor"], roles["neighbour"]
    a.location = _land(sim, 30, 30)
    assert act(sim, a, "dig_well").success
    source = sim.world.find_nearest_resource(a.location, ResourceType.WATER)
    assert source is not None and source.id.startswith("well_") and source.location.distance_to(a.location) < 1
    b.location = Position(a.location.x + 5, a.location.y)
    ok, why = sim._handler_registry.get_handler(ActionType.DIG_WELL).validate(b, Action(ActionType.DIG_WELL))
    assert not ok and "well close by" in why


def test_street_lights_need_glass_a_post_and_fuel_and_light_the_night():
    from agents.agent import Action, ActionType
    from engine.psychology import NeedType
    sim, roles = make_world()
    a, b = roles["actor"], roles["neighbour"]
    handler = sim._handler_registry.get_handler(ActionType.BUILD_STREETLIGHT)
    a.inventory.items.pop("glass", None)
    ok, why = handler.validate(a, Action(ActionType.BUILD_STREETLIGHT))
    assert not ok and "glass" in why

    a.inventory.items["glass"] = 1
    assert act(sim, a, "build_streetlight").success
    lamp = next(iter(sim.infrastructure.lights.values()))
    assert lamp.fuel == 6 and a.inventory.items.get("glass", 0) == 0

    # Dusk: it burns a night's fuel and is lit; people near it feel safer
    world = sim.world
    world.time.current_tick, world.time.hour = 20 * 6, 20
    b.location = a.location
    b.needs.needs[NeedType.SECURITY].level = 0.8
    sim.infrastructure.update_lights(world, 20 * 6)
    assert lamp.lit and lamp.fuel == 5 and b.needs.needs[NeedType.SECURITY].level < 0.8
    # Dawn: out. With no fuel left it stays dark until someone tops it up.
    world.time.hour = 6
    sim.infrastructure.update_lights(world, 30 * 6)
    assert not lamp.lit
    lamp.fuel = 0
    world.time.hour = 20
    sim.infrastructure.update_lights(world, 44 * 6)
    assert not lamp.lit
    assert act(sim, b, "build_streetlight").metadata["refuelled"] > 0  # b adds fuel instead of building


def test_firsts_of_public_works_are_chronicled():
    from agents.agent import Position
    sim, roles = make_world()
    a = roles["actor"]
    a.location = _land(sim, 30, 30)
    act(sim, a, "dig_well")
    sim.chronicle.observe(sim, 1)
    assert "first_well" in sim.chronicle.done
