"""
Terrain is real: a map that doesn't repeat, and water nobody walks or builds
on (world/simulation.py WorldMap, agents/pathfinding.py).

    python3 -m pytest tests/test_terrain.py -q
"""

import asyncio
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import quiet  # noqa: E402


def _map(seed=1):
    from world.simulation import WorldMap
    random.seed(seed)
    return WorldMap(100, 100)


def _pathfinder(world_map):
    from agents.pathfinding import Pathfinder
    pf = Pathfinder(world_map.width, world_map.height)
    pf.set_terrain(world_map)
    return pf


def test_the_map_has_its_mix_and_does_not_repeat():
    from collections import Counter
    m = _map(1)
    shares = Counter(t.terrain.value for t in m.tiles.values())
    assert abs(shares["water"] / 10000 - 0.22) < 0.01
    assert all(shares[k] > 1200 for k in ("plains", "forest", "mountains", "desert"))
    # the old map was sums of sines: the same pattern again 63 tiles on
    same = sum(m.tiles[(x, y)].terrain == m.tiles[(x + 63, y)].terrain for x in range(37) for y in range(100))
    assert same / (37 * 100) < 0.6
    # and each world has its own shape
    other = _map(2)
    assert sum(m.tiles[c].terrain == other.tiles[c].terrain for c in m.tiles) / 10000 < 0.6


def test_paths_go_round_water_and_end_at_the_shore():
    m = _map(1)
    pf = _pathfinder(m)
    land = [c for c, comp in m.land_component.items() if comp == m.mainland]
    rng = random.Random(4)
    for _ in range(40):
        (sx, sy), (ex, ey) = rng.sample(land, 2)
        path = pf.find_path(sx, sy, ex, ey)
        assert path and path[-1] == (ex, ey)
        assert not any(c in pf.water for c in path)
    # a target in a lake: the path ends on the nearest dry tile
    lake = next(c for c in sorted(pf.water) if all((c[0] + dx, c[1] + dy) in pf.water
                                                   for dx in (-2, 0, 2) for dy in (-2, 0, 2)))
    start = min(land, key=lambda c: (c[0] - lake[0]) ** 2 + (c[1] - lake[1]) ** 2 + 400)
    path = pf.find_path(*start, *lake)
    assert path and path[-1] not in pf.water and not any(c in pf.water for c in path)


def test_an_island_cannot_be_walked_to_and_someone_stranded_can_wade_out():
    from world.simulation import TerrainType
    m = _map(1)
    for x in range(10):              # an island: a dry 2x2 inside water
        for y in range(10):
            m.tiles[(x, y)].terrain = TerrainType.WATER
    for c in [(4, 4), (4, 5), (5, 4), (5, 5)]:
        m.tiles[c].terrain = TerrainType.PLAINS
    m._label_land()
    pf = _pathfinder(m)
    mainland = next(c for c, comp in m.land_component.items() if comp == m.mainland)
    assert pf.find_path(*mainland, 4, 4) is None
    out = pf.find_path(2, 2, *mainland)      # standing in the water (an old save)
    assert out and out[-1] == mainland


def test_a_straight_walk_stops_at_the_shore():
    from agents.agent import Position
    m = _map(1)
    pf = _pathfinder(m)
    shore = next(c for c, comp in m.land_component.items()
                 if comp == m.mainland and (c[0] + 1, c[1]) in pf.water)
    start = Position(shore[0] + 0.5, shore[1] + 0.5)
    end = m.walk_line(start, Position(start.x + 8, start.y), 8)
    assert not m.is_water(end.x, end.y) and end.x < shore[0] + 1


def test_a_running_world_stays_on_dry_land():
    from engine.simulation import SimulationEngine
    random.seed(3)
    with quiet():
        sim = SimulationEngine(world_width=100, world_height=100)
        sim.initialize_world(num_agents=12)
    m = sim.world.map
    assert all(m.land_component.get((int(a.location.x), int(a.location.y))) == m.mainland
               for a in sim.world.agents)

    async def go():
        for _ in range(150):
            await sim.tick()
    with quiet():
        asyncio.run(go())
    wet = [a.name for a in sim.world.agents if a.alive and m.is_water(a.location.x, a.location.y)]
    assert wet == []
    built = [b for b in sim.dynamic_building_system.buildings.values()]
    assert not any(m.is_water(*b.location) for b in built)
    assert not any(m.is_water(x, y) for x, y in sim.infrastructure.roads)
