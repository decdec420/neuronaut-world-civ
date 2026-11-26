"""
World Simulation - Physical environment, resources, and time

The world where agents live, containing:
- Spatial grid with terrain
- Resources (food, materials, water)
- Time progression
- Environmental dynamics
"""

import logging
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent import Position

logger = logging.getLogger(__name__)


class TerrainType(Enum):
    """Types of terrain"""
    PLAINS = "plains"
    FOREST = "forest"
    MOUNTAINS = "mountains"
    WATER = "water"
    DESERT = "desert"


class ResourceType(Enum):
    """Types of resources"""
    FOOD = "food"
    WATER = "water"
    WOOD = "wood"
    STONE = "stone"
    METAL = "metal"


@dataclass
class Resource:
    """A resource in the world"""
    id: str
    resource_type: ResourceType
    location: Position
    quantity: float
    regeneration_rate: float = 0.0  # Per tick

    def harvest(self, amount: float) -> float:
        """Harvest resource, returns actual amount harvested"""
        actual = min(amount, self.quantity)
        self.quantity -= actual
        return actual

    def regenerate(self, delta_time: float = 1.0):
        """Regenerate resource"""
        if self.regeneration_rate > 0:
            self.quantity += self.regeneration_rate * delta_time


@dataclass
class Tile:
    """A single tile in the world grid"""
    x: int
    y: int
    terrain: TerrainType
    resources: List[Resource] = field(default_factory=list)
    building_id: Optional[str] = None

    def get_position(self) -> Position:
        """Get center position of tile"""
        return Position(float(self.x), float(self.y))


class WorldMap:
    """2D grid-based world map"""

    def __init__(self, width: int = 100, height: int = 100):
        self.width = width
        self.height = height
        self.tiles: Dict[Tuple[int, int], Tile] = {}

        self._generate_terrain()
        self._spawn_resources()

    # Shares of the map by terrain. Water used to be 31% of a map that was the
    # same pattern tiled (sums of sines); land keeps the old proportions.
    WATER_SHARE, MOUNTAIN_SHARE = 0.22, 0.167
    DESERT_OF_MIDLAND, FOREST_OF_MIDLAND = 0.287, 0.352

    def _generate_terrain(self):
        """Terrain from seeded value noise: lakes are the lowest ground and
        mountains the highest; in between, moisture decides desert, plains or
        forest. Shares are fixed by quantile, so every world has about the
        same mix but its own shape. The noise has its own generator, seeded
        with one draw from the world's dice."""
        rng = random.Random(random.getrandbits(32))
        cells = [(x, y) for x in range(self.width) for y in range(self.height)]
        elevation = self._fractal_noise(rng, [(24, 1.0), (12, 0.5), (6, 0.25), (3, 0.12)])
        moisture = self._fractal_noise(rng, [(20, 1.0), (10, 0.5), (5, 0.25)])

        by_height = sorted(cells, key=lambda c: elevation[c])
        n = len(by_height)
        n_water, n_mountain = int(n * self.WATER_SHARE), int(n * self.MOUNTAIN_SHARE)
        terrain = {}
        for c in by_height[:n_water]:
            terrain[c] = TerrainType.WATER
        for c in by_height[n - n_mountain:]:
            terrain[c] = TerrainType.MOUNTAINS
        midland = sorted(by_height[n_water:n - n_mountain], key=lambda c: moisture[c])
        m = len(midland)
        n_desert, n_forest = int(m * self.DESERT_OF_MIDLAND), int(m * self.FOREST_OF_MIDLAND)
        for i, c in enumerate(midland):
            terrain[c] = (TerrainType.DESERT if i < n_desert else
                          TerrainType.FOREST if i >= m - n_forest else TerrainType.PLAINS)
        for (x, y), t in terrain.items():
            self.tiles[(x, y)] = Tile(x, y, t)
        self._label_land()

    def _fractal_noise(self, rng: random.Random, octaves) -> Dict[Tuple[int, int], float]:
        """Value noise: random heights on a coarse lattice, smoothly blended,
        summed over octaves of (lattice spacing, weight). Not periodic."""
        w, h = self.width, self.height
        grid = [[0.0] * h for _ in range(w)]
        for spacing, weight in octaves:
            gw, gh = w // spacing + 2, h // spacing + 2
            lattice = [[rng.random() for _ in range(gh)] for _ in range(gw)]

            def axis(n):
                out = []
                for v in range(n):
                    g = v / spacing
                    i = int(g)
                    f = g - i
                    out.append((i, f * f * (3 - 2 * f)))
                return out
            xs, ys = axis(w), axis(h)
            for x, (ix, sx) in enumerate(xs):
                col0, col1, row = lattice[ix], lattice[ix + 1], grid[x]
                for y, (iy, sy) in enumerate(ys):
                    top = col0[iy] + (col1[iy] - col0[iy]) * sx
                    bottom = col0[iy + 1] + (col1[iy + 1] - col0[iy + 1]) * sx
                    row[y] += weight * (top + (bottom - top) * sy)
        return {(x, y): grid[x][y] for x in range(w) for y in range(h)}

    def _label_land(self) -> None:
        """Connected pieces of land (8-way, as agents walk). The largest is
        the mainland, where people start."""
        self.land_component: Dict[Tuple[int, int], int] = {}
        sizes = []
        for start, tile in self.tiles.items():
            if tile.terrain == TerrainType.WATER or start in self.land_component:
                continue
            label, stack, size = len(sizes), [start], 0
            self.land_component[start] = label
            while stack:
                x, y = stack.pop()
                size += 1
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nxt = (x + dx, y + dy)
                        t = self.tiles.get(nxt)
                        if t is not None and t.terrain != TerrainType.WATER and nxt not in self.land_component:
                            self.land_component[nxt] = label
                            stack.append(nxt)
            sizes.append(size)
        self.mainland = max(range(len(sizes)), key=sizes.__getitem__) if sizes else None

    # -- what's walkable ---------------------------------------------------------

    def is_water(self, x: float, y: float) -> bool:
        """True for water and for anywhere off the map."""
        tile = self.tiles.get((int(x), int(y)))
        return tile is None or tile.terrain == TerrainType.WATER

    def random_mainland_position(self, x_range=(20, 80), y_range=(20, 80), tries: int = 500) -> Position:
        """A random place on the mainland, within the given box if possible."""
        components = getattr(self, 'land_component', {})
        mainland = getattr(self, 'mainland', None)
        for i in range(tries):
            box = (x_range, y_range) if i < tries // 2 else ((0, self.width), (0, self.height))
            x, y = random.uniform(*box[0]), random.uniform(*box[1])
            if not self.is_water(x, y) and (mainland is None or components.get((int(x), int(y))) == mainland):
                return Position(x, y)
        return Position(random.uniform(*x_range), random.uniform(*y_range))

    def walk_line(self, start: Position, target: Position, distance: float) -> Position:
        """Where a straight walk of up to `distance` toward `target` ends: at
        the target, or the last dry ground before water. Someone already in
        the water (from an old save) may walk out through it."""
        if self.is_water(start.x, start.y):
            return start.move_toward(target, distance)
        end = start.move_toward(target, distance)
        length = start.distance_to(end)
        steps = max(1, int(length / 0.5))
        last = start
        for i in range(1, steps + 1):
            t = i / steps
            p = Position(start.x + (end.x - start.x) * t, start.y + (end.y - start.y) * t)
            if self.is_water(p.x, p.y):
                return last
            last = p
        return end

    def _spawn_resources(self):
        """Spawn initial resources"""
        resource_count = 0

        for tile in self.tiles.values():
            # Food in plains and forests
            if tile.terrain in [TerrainType.PLAINS, TerrainType.FOREST]:
                if random.random() < 0.3:  # 30% chance
                    resource = Resource(
                        id=f"food_{resource_count}",
                        resource_type=ResourceType.FOOD,
                        location=tile.get_position(),
                        quantity=random.uniform(10, 50),
                        regeneration_rate=0.5  # Renewable
                    )
                    tile.resources.append(resource)
                    resource_count += 1

            # Wood in forests
            if tile.terrain == TerrainType.FOREST:
                if random.random() < 0.4:
                    resource = Resource(
                        id=f"wood_{resource_count}",
                        resource_type=ResourceType.WOOD,
                        location=tile.get_position(),
                        quantity=random.uniform(20, 80),
                        regeneration_rate=0.2
                    )
                    tile.resources.append(resource)
                    resource_count += 1

            # Stone in mountains
            if tile.terrain == TerrainType.MOUNTAINS:
                if random.random() < 0.5:
                    resource = Resource(
                        id=f"stone_{resource_count}",
                        resource_type=ResourceType.STONE,
                        location=tile.get_position(),
                        quantity=random.uniform(30, 100),
                        regeneration_rate=0.0  # Non-renewable
                    )
                    tile.resources.append(resource)
                    resource_count += 1

            # Water near water tiles
            if tile.terrain == TerrainType.WATER:
                resource = Resource(
                    id=f"water_{resource_count}",
                    resource_type=ResourceType.WATER,
                    location=tile.get_position(),
                    quantity=1000,  # Abundant
                    regeneration_rate=10.0
                )
                tile.resources.append(resource)
                resource_count += 1

    def get_tile(self, position: Position) -> Optional[Tile]:
        """Get tile at position"""
        x, y = int(position.x), int(position.y)
        return self.tiles.get((x, y))

    def get_resources_near(self, position: Position, radius: float) -> List[Resource]:
        """Get all resources within radius of position"""
        resources = []

        x_min = max(0, int(position.x - radius))
        x_max = min(self.width, int(position.x + radius) + 1)
        y_min = max(0, int(position.y - radius))
        y_max = min(self.height, int(position.y + radius) + 1)

        for x in range(x_min, x_max):
            for y in range(y_min, y_max):
                tile = self.tiles.get((x, y))
                if tile:
                    for resource in tile.resources:
                        if resource.location.distance_to(position) <= radius:
                            resources.append(resource)

        return resources

    def update_resources(self, delta_time: float = 1.0):
        """Update all resources (regeneration)"""
        for tile in self.tiles.values():
            for resource in tile.resources:
                resource.regenerate(delta_time)


@dataclass
class TimeState:
    """World time"""
    current_tick: int = 0
    hour: int = 12  # 0-23
    day: int = 1
    season: str = "spring"  # spring, summer, fall, winter

    def advance(self, ticks: int = 1):
        """Advance time"""
        self.current_tick += ticks

        # Each tick = 10 minutes
        self.hour = (self.current_tick // 6) % 24
        self.day = (self.current_tick // (6 * 24)) + 1

        # Seasons (90 days each)
        day_of_year = self.day % 360
        if day_of_year < 90:
            self.season = "spring"
        elif day_of_year < 180:
            self.season = "summer"
        elif day_of_year < 270:
            self.season = "fall"
        else:
            self.season = "winter"

    def is_day(self) -> bool:
        """Check if it's daytime"""
        return 6 <= self.hour < 20

    def is_night(self) -> bool:
        """Check if it's nighttime"""
        return not self.is_day()


class World:
    """The complete world simulation"""

    def __init__(self, width: int = 100, height: int = 100):
        self.map = WorldMap(width, height)
        self.time = TimeState()

        # Will be populated by simulation engine
        self.agents: List = []
        self.buildings: Dict[str, 'Building'] = {}

        # RESOURCE SCARCITY - Finite global resource pools (INCREASED for playability!)
        # Resources are still LIMITED but more abundant to sustain civilization
        self.resource_pools = {
            'stone': 3000.0,      # INCREASED from 2000 - more abundant
            'wood': 2500.0,       # INCREASED from 1500 - lush forests
            'food': 2000.0,       # INCREASED from 1000 - abundant wildlife/plants
            'water': 3500.0,      # INCREASED from 2000 - plentiful water sources
            'clay': 1200.0,       # INCREASED from 800
            'sand': 1000.0,       # INCREASED from 600
            'hide': 600.0,        # INCREASED from 400
            'plant_fiber': 1500.0,  # INCREASED from 1000
            # Metal ores unlocked by civilization progression
            'metal_ore': 0.0,     # Unlocked after fire discovered
            'iron_ore': 0.0,      # Unlocked after bronze discovered
        }

        # Track resource generation rates - INCREASED for sustainable civilization!
        self.resource_regen_rates = {
            'stone': 0.5,         # Slow: new deposits get uncovered (was 0, ran out for good)
            'wood': 1.5,          # INCREASED from 0.2 to 1.5 - faster forest growth
            'food': 6.0,          # 12 agents eat ~6/tick; 3.0 ran the world dry
            'water': 8.0,         # 12 agents drink ~8/tick; 2.0 ran the world dry
            'clay': 0.3,          # Slow: riverbanks refill (was 0)
            'sand': 0.0,          # Non-renewable
            'hide': 0.3,          # INCREASED from 0.05 to 0.3 - wildlife reproduces
            'plant_fiber': 1.0,   # INCREASED from 0.15 to 1.0 - plants grow back
            'metal_ore': 0.0,
            'iron_ore': 0.0,
        }

        self.unlocked_resources = set()  # pools an era has opened up

        # Statistics
        self.total_ticks = 0
        self.started_at = datetime.now()

    def tick(self, delta_time: float = 1.0, weather_effects=None):
        """Advance world state by one tick (with weather effects)"""
        self.time.advance(1)
        self.map.update_resources(delta_time)
        self.total_ticks += 1

        # Regenerate global resource pools (affected by weather!)
        self._regenerate_resource_pools(delta_time, weather_effects)

    def _regenerate_resource_pools(self, delta_time: float = 1.0, weather_effects=None):
        """Regenerate renewable resources (affected by weather!)"""
        for resource_name, regen_rate in self.resource_regen_rates.items():
            if regen_rate > 0:
                # Add regenerated amount, but cap at reasonable max
                max_amounts = {
                    'wood': 3000.0,
                    'food': 2000.0,
                    'water': 4000.0,
                    'plant_fiber': 2000.0,
                    'hide': 800.0,
                }
                max_amount = max_amounts.get(resource_name, 5000.0)

                current = self.resource_pools.get(resource_name, 0.0)

                # Apply weather modifiers
                weather_multiplier = 1.0
                if weather_effects:
                    if resource_name == 'water':
                        weather_multiplier = weather_effects.water_regeneration
                    elif resource_name == 'food':
                        weather_multiplier = weather_effects.food_regeneration
                    elif resource_name == 'wood':
                        weather_multiplier = weather_effects.wood_regeneration
                    elif resource_name == 'plant_fiber':
                        weather_multiplier = weather_effects.food_regeneration  # Plants affected like food
                    else:
                        weather_multiplier = 1.0
                else:
                    weather_multiplier = 1.0

                regenerated = current + (regen_rate * delta_time * weather_multiplier)
                self.resource_pools[resource_name] = min(regenerated, max_amount)


    def harvest_from_pool(self, resource_name: str, amount: float) -> float:
        """
        Harvest from global resource pool.
        Returns actual amount harvested (may be less if depleted).
        """
        available = self.resource_pools.get(resource_name, 0.0)
        actual_amount = min(amount, available)

        if actual_amount > 0:
            self.resource_pools[resource_name] = available - actual_amount

        return actual_amount

    def unlock_resource(self, resource_name: str, initial_amount: float):
        """
        Unlock a new resource (called when civilization milestones are achieved).
        Example: metal_ore becomes available after fire is discovered.
        """
        if resource_name not in self.resource_pools:
            self.resource_pools[resource_name] = 0.0

        # Add initial amount if not already present
        if self.resource_pools[resource_name] == 0.0:
            self.resource_pools[resource_name] = initial_amount
            logger.info(f"🔓 New resource unlocked: {resource_name} ({initial_amount} available)")

    def get_resource_pool_status(self) -> Dict:
        """Get status of all resource pools"""
        return {
            'pools': self.resource_pools.copy(),
            'regen_rates': self.resource_regen_rates.copy(),
            'total_resources': sum(self.resource_pools.values()),
        }

    def get_state(self) -> Dict:
        """Get current world state for agents to perceive"""
        # Collect all resources, and the same ones by tile (their place in the
        # list kept) so an agent can look only at what's near it
        # (Agent.perceive: scanning every resource for every agent each tick
        # was half of all tick time with a band of 30)
        all_resources = []
        by_tile: Dict[Tuple[int, int], List[Tuple[int, Dict]]] = {}
        for tile in self.map.tiles.values():
            for resource in tile.resources:
                if resource.quantity > 0:
                    entry = {
                        'id': resource.id,
                        'type': resource.resource_type.value,
                        'location': resource.location,
                        'quantity': resource.quantity,
                    }
                    key = (math.floor(resource.location.x), math.floor(resource.location.y))
                    by_tile.setdefault(key, []).append((len(all_resources), entry))
                    all_resources.append(entry)

        return {
            'time_of_day': self.time.hour,
            'is_day': self.time.is_day(),
            'season': self.time.season,
            'day': self.time.day,
            'tick': self.time.current_tick,
            'agents': self.agents,
            'resources': all_resources,
            'resources_by_tile': by_tile,
            'buildings': list(self.buildings.values()),
        }

    def find_nearest_resource(
        self,
        position: Position,
        resource_type: ResourceType,
        radius: float = 50.0
    ) -> Optional[Resource]:
        """Find nearest resource of type, within radius"""
        nearest = None
        min_dist = float('inf')

        resources = self.map.get_resources_near(position, radius=radius)

        for resource in resources:
            if resource.resource_type == resource_type and resource.quantity > 0:
                dist = position.distance_to(resource.location)
                if dist < min_dist:
                    min_dist = dist
                    nearest = resource

        return nearest

    def harvest_resource(
        self,
        resource_id: str,
        amount: float
    ) -> float:
        """
        Harvest amount from resource, returns actual harvested.
        Now uses GLOBAL RESOURCE POOLS for scarcity!
        """
        # Find resource on map
        for tile in self.map.tiles.values():
            for resource in tile.resources:
                if resource.id == resource_id:
                    # Harvest from the tile first, then take only that much from
                    # the global pool. Debiting the pool by the requested amount
                    # lost food whenever the tile held less (about a third of it).
                    resource_type_name = resource.resource_type.value
                    tile_harvested = resource.harvest(amount)
                    if resource.resource_type == ResourceType.WATER:
                        # A lake, river or well is the water: it holds its own
                        # amount and refills. The global water pool was sized
                        # for 12 people ("12 agents drink ~8/tick"); with a band
                        # of 25 growing to 40 it ran dry, every attempt to fetch
                        # water failed beside full lakes, and people who carried
                        # none died (seed 3: 10,135 failed fetches by day 32)
                        return tile_harvested
                    available_in_pool = self.harvest_from_pool(resource_type_name, tile_harvested)

                    # Return the LESSER of the two (global pool constrains)
                    actual_harvested = min(available_in_pool, tile_harvested)

                    # If we couldn't get it all from pool, refund tile resource
                    if actual_harvested < tile_harvested:
                        refund = tile_harvested - actual_harvested
                        resource.quantity += refund

                    return actual_harvested
        return 0.0

    def get_statistics(self) -> Dict:
        """Get world statistics"""
        return {
            'total_ticks': self.total_ticks,
            'current_day': self.time.day,
            'current_hour': self.time.hour,
            'season': self.time.season,
            'total_agents': len(self.agents),
            'alive_agents': sum(1 for a in self.agents if a.alive),
            'total_resources': sum(
                len(tile.resources) for tile in self.map.tiles.values()
            ),
            'uptime_seconds': (datetime.now() - self.started_at).total_seconds(),
            # RESOURCE SCARCITY - Show global pool status
            'resource_pools': self.get_resource_pool_status(),
        }
