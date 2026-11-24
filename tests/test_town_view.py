"""
What the map viewer gets (world/town_view.py): the real terrain, and
buildings at their real places with who lives there and who is home.

    python3 -m pytest tests/test_town_view.py -q
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world  # noqa: E402


def test_the_map_is_the_world_terrain_and_resources():
    from world.town_view import map_layout, TERRAIN_CODES
    sim, _ = make_world()
    m = map_layout(sim)
    world_map = sim.world.map
    assert m["width"] == world_map.width and m["height"] == world_map.height
    assert len(m["terrain"]) == world_map.height and all(len(r) == world_map.width for r in m["terrain"])
    for (x, y), tile in list(world_map.tiles.items())[:500]:
        assert m["terrain"][y][x] == TERRAIN_CODES[tile.terrain.value]
    water = sum(1 for t in world_map.tiles.values() for r in t.resources if r.resource_type.value == "water")
    assert len(m["resources"]["water"]) == water
    json.dumps(m)  # it goes over HTTP


def test_buildings_are_where_they_stand_with_who_lives_there():
    from world.town_view import town_snapshot
    from life import homes
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    from test_homes import _hut
    dbs = sim.dynamic_building_system
    home = _hut(sim, a, x=50, y=50)
    homes.move_in(dbs, a, home, 0, "test")
    homes.move_in(dbs, b, home, 0, "test")
    from agents.agent import Position
    a.location = Position(home.location[0] + 1, home.location[1])     # at home
    b.location = Position(home.location[0] + 20, home.location[1])    # out

    snap = town_snapshot(sim)
    view = next(v for v in snap["buildings"] if v["id"] == home.id)
    assert (view["x"], view["y"]) == tuple(home.location)
    assert sorted(view["residents"]) == sorted([a.name, b.name])
    assert view["home_now"] == 1
    assert view["complete"] and not view["collapsed"]
    assert 0 <= snap["hour"] < 24 and snap["minute"] in range(0, 60, 10)
    json.dumps(snap)


def test_the_websocket_snapshot_carries_the_town():
    sim, _ = make_world()
    snap = sim.get_state_snapshot()
    assert "town" in snap and "buildings" in snap["town"] and "gatherings" in snap["town"]
