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

    def _generate_terrain(self):
        """Generate terrain using simple noise"""
        for x in range(self.width):
            for y in range(self.height):
                # Simple terrain generation
                noise = self._perlin_noise(x / 10.0, y / 10.0)

                if noise < -0.3:
                    terrain = TerrainType.WATER
                elif noise < 0.0:
                    terrain = TerrainType.PLAINS
                elif noise < 0.3:
                    terrain = TerrainType.FOREST
                elif noise < 0.6:
                    terrain = TerrainType.MOUNTAINS
                else:
                    terrain = TerrainType.DESERT

                self.tiles[(x, y)] = Tile(x, y, terrain)

    def _perlin_noise(self, x: float, y: float) -> float:
        """Simplified Perlin-like noise"""
        # Not real Perlin, but good enough for terrain
        return math.sin(x) * math.cos(y) + \
               0.5 * math.sin(2*x) * math.cos(2*y) + \
               0.25 * math.sin(4*x) * math.cos(4*y)

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
        # Collect all resources
        all_resources = []
        for tile in self.map.tiles.values():
            for resource in tile.resources:
                if resource.quantity > 0:
                    all_resources.append({
                        'id': resource.id,
                        'type': resource.resource_type.value,
                        'location': resource.location,
                        'quantity': resource.quantity,
                    })

        return {
            'time_of_day': self.time.hour,
            'is_day': self.time.is_day(),
            'season': self.time.season,
            'day': self.time.day,
            'tick': self.time.current_tick,
            'agents': self.agents,
            'resources': all_resources,
            'buildings': list(self.buildings.values()),
        }

    def find_nearest_resource(
        self,
        position: Position,
        resource_type: ResourceType
    ) -> Optional[Resource]:
        """Find nearest resource of type"""
        nearest = None
        min_dist = float('inf')

        resources = self.map.get_resources_near(position, radius=50.0)

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
