"""
Public works agents can choose to build: roads, wells and street lights.

What the world allows (agents decide whether, where and when):

- Road: paves up to ROAD_TILES_PER_BUILD tiles, from where the agent stands
  toward the place it walks to most (a spring, its fields, the square...),
  for ROAD_STONE_PER_TILE stone a tile. On a road an agent covers up to
  ROAD_SPEED tiles a tick instead of 1, and paths prefer roads, so a well-
  trodden way gets quicker for everyone who uses it.
- Well: dug where the agent stands (not within WELL_SPACING of another), for
  WELL_COST. It becomes a water source on the map: gather_water finds it like
  a spring. Groundwater refills slowly (WELL_REFILL a tick) and still comes
  out of the world's water.
- Street light: a lamp with a glass pane on a post, where the agent stands
  (not within LIGHT_SPACING of another): glass, a post (wood or metal) and
  fuel to burn (wood or coal), up to LIGHT_FUEL_MAX nights' worth. Each night
  it burns one; with none left it stays dark until someone adds fuel (doing
  build_streetlight next to a lamp that is low tops it up). At night, people
  within LIGHT_RADIUS of a lit lamp feel safer.

Every move an agent makes toward a place goes through step_toward(), which
also keeps a short record of where each agent walks (used to lay roads, and
part of the agent's own state: one who walks a lot feels the need for roads).
"""

import collections
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

ROAD_SPEED = 3
ROAD_TILES_PER_BUILD = 6
ROAD_STONE_PER_TILE = 2
ROAD_COST = 0.4                # path cost of a road tile (open ground is 1)
WELL_COST = {"stone": 10, "wood": 2}
WELL_SPACING = 15.0
WELL_CAPACITY = 300.0
WELL_REFILL = 1.0
LIGHT_SPACING = 6.0
LIGHT_RADIUS = 8.0
LIGHT_FUEL_MAX = 6
LIGHT_POSTS = (("wood", 2), ("iron", 1), ("steel", 1), ("copper", 1), ("bronze", 1))
FUELS = ("coal", "charcoal", "wood")
NIGHT_FROM, NIGHT_UNTIL = 20, 6
WALK_MEMORY = 0.99             # recent walking decays by this per tick
DESTINATION_GRID = 5           # destinations are remembered to the nearest 5 tiles


@dataclass
class Well:
    id: str
    x: int
    y: int
    builder: str
    built_tick: int


@dataclass
class StreetLight:
    id: str
    x: int
    y: int
    builder: str
    built_tick: int
    fuel: int = 0
    lit: bool = False


@dataclass
class Travel:
    """One agent's walking: how much lately, and where to."""
    recent: float = 0.0
    last_tick: int = 0
    destinations: collections.Counter = field(default_factory=collections.Counter)

    def walked(self, tick: int, steps: int, destination: Tuple[int, int]) -> None:
        self.recent = self.recent * WALK_MEMORY ** max(0, tick - self.last_tick) + steps
        self.last_tick = tick
        self.destinations[destination] += 1
        if len(self.destinations) > 20:  # bounded: keep the most visited
            self.destinations = collections.Counter(dict(self.destinations.most_common(10)))

    def burden(self, tick: int) -> float:
        """0-1: how much walking the agent has been doing lately."""
        return min(1.0, self.recent * WALK_MEMORY ** max(0, tick - self.last_tick) / 60.0)


class Infrastructure:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.roads: Set[Tuple[int, int]] = set()
        self.wells: Dict[str, Well] = {}
        self.lights: Dict[str, StreetLight] = {}
        self.travel: Dict[str, Travel] = {}
        self.road_steps = 0          # tiles covered on roads beyond the first step (time saved)
        self._next_id = 0

    def _id(self, kind: str) -> str:
        self._next_id += 1
        return f"{kind}_{self._next_id}"

    # -- walking -----------------------------------------------------------------

    def step_toward(self, agent, pathfinder, tx: float, ty: float, tick: int) -> bool:
        """Move the agent one tile toward (tx, ty), or up to ROAD_SPEED tiles if
        it walks along a road. Returns False if there's no way there."""
        from agents.agent import Position
        path = pathfinder.find_path(agent.location.x, agent.location.y, tx, ty)
        if not path or len(path) < 2:
            return False
        steps = 1
        while (steps < ROAD_SPEED and steps + 1 < len(path)
               and tuple(path[steps]) in self.roads and tuple(path[steps + 1]) in self.roads):
            steps += 1
        x, y = path[steps]
        agent.location = Position(float(x), float(y))
        self.road_steps += steps - 1
        destination = (int(tx) // DESTINATION_GRID * DESTINATION_GRID, int(ty) // DESTINATION_GRID * DESTINATION_GRID)
        self.travel.setdefault(agent.id, Travel()).walked(tick, steps, destination)
        return True

    def walking_burden(self, agent_id: str, tick: int) -> float:
        travel = self.travel.get(agent_id)
        return travel.burden(tick) if travel else 0.0

    def favourite_destination(self, agent_id: str) -> Optional[Tuple[int, int]]:
        travel = self.travel.get(agent_id)
        if not travel or not travel.destinations:
            return None
        return travel.destinations.most_common(1)[0][0]

    # -- roads -------------------------------------------------------------------

    def road_plan(self, agent, pathfinder) -> List[Tuple[int, int]]:
        """Tiles a road built now would pave: along the agent's path to where it
        walks most, the first ROAD_TILES_PER_BUILD not yet paved."""
        destination = self.favourite_destination(agent.id)
        if destination is None:
            return []
        tx, ty = destination[0] + DESTINATION_GRID // 2, destination[1] + DESTINATION_GRID // 2
        if math.hypot(agent.location.x - tx, agent.location.y - ty) < 4:
            return []
        path = pathfinder.find_path(agent.location.x, agent.location.y, tx, ty) or []
        return [tuple(p) for p in path if tuple(p) not in self.roads][:ROAD_TILES_PER_BUILD]

    def pave(self, tiles: List[Tuple[int, int]], pathfinder) -> None:
        self.roads.update(tiles)
        pathfinder.path_cache.clear()  # routes may now go by road

    # -- wells -------------------------------------------------------------------

    def well_near(self, x: float, y: float, radius: float) -> Optional[Well]:
        return next((w for w in self.wells.values() if math.hypot(w.x - x, w.y - y) < radius), None)

    def dig_well(self, world, agent, tick: int) -> Well:
        from world.simulation import Resource, ResourceType
        from agents.agent import Position
        x, y = int(agent.location.x), int(agent.location.y)
        well = Well(self._id("well"), x, y, agent.id, tick)
        self.wells[well.id] = well
        tile = world.map.tiles.get((x, y))
        if tile is not None:
            tile.resources.append(Resource(id=well.id, resource_type=ResourceType.WATER,
                                           location=Position(float(x), float(y)),
                                           quantity=WELL_CAPACITY, regeneration_rate=WELL_REFILL))
        return well

    # -- street lights -------------------------------------------------------------

    def light_near(self, x: float, y: float, radius: float) -> Optional[StreetLight]:
        near = [l for l in self.lights.values() if math.hypot(l.x - x, l.y - y) < radius]
        return min(near, key=lambda l: math.hypot(l.x - x, l.y - y)) if near else None

    @staticmethod
    def is_night(hour: int) -> bool:
        return hour >= NIGHT_FROM or hour < NIGHT_UNTIL

    def update_lights(self, world, tick: int) -> None:
        """At dusk each lamp with fuel burns one night's worth and is lit; at
        dawn they go out. At night, people near a lit lamp feel safer."""
        hour = world.time.hour
        if tick % 6 == 0 and hour == NIGHT_FROM:
            for light in self.lights.values():
                light.lit = light.fuel > 0
                if light.lit:
                    light.fuel -= 1
        elif hour == NIGHT_UNTIL:
            for light in self.lights.values():
                light.lit = False
        lit = [l for l in self.lights.values() if l.lit]
        if not lit or not self.is_night(hour):
            return
        from engine.psychology import NeedType
        for agent in world.agents:
            if agent.alive and any(math.hypot(l.x - agent.location.x, l.y - agent.location.y) < LIGHT_RADIUS
                                   for l in lit):
                agent.needs.satisfy_need(NeedType.SECURITY, 0.01)

    # -- views -------------------------------------------------------------------

    def to_dict(self) -> Dict:
        return {
            "roads": sorted([list(t) for t in self.roads]),
            "wells": [{"x": w.x, "y": w.y} for w in self.wells.values()],
            "lights": [{"x": l.x, "y": l.y, "lit": l.lit, "fuel": l.fuel} for l in self.lights.values()],
        }
