"""
Pathfinding System - A* Navigation for Agents

Agents can intelligently navigate to:
- Resources (food, water, materials)
- Buildings
- Other agents
- Exploration targets

Features:
- A* pathfinding algorithm
- Obstacle avoidance
- Path caching
- Movement memory
"""

import heapq
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PathNode:
    """A node in the pathfinding grid"""
    x: int
    y: int
    g_cost: float = 0.0  # Cost from start
    h_cost: float = 0.0  # Heuristic cost to end
    parent: Optional['PathNode'] = None

    @property
    def f_cost(self) -> float:
        """Total cost (g + h)"""
        return self.g_cost + self.h_cost

    def __lt__(self, other):
        return self.f_cost < other.f_cost

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


class Pathfinder:
    """A* pathfinding implementation"""

    MAX_CACHED_PATHS = 2000

    def __init__(self, world_width: int = 100, world_height: int = 100):
        self.world_width = world_width
        self.world_height = world_height
        self.path_cache = {}  # Cache paths for performance (up to MAX_CACHED_PATHS)
        self.cache_max_age = 50  # Clear cache after 50 ticks
        self.water: set = set()             # tiles nobody walks on (set_terrain)
        self.land_component: dict = {}      # which piece of land each tile is on
        self._shore: dict = {}              # water tile -> nearest dry tile

    WADING_COST = 4.0   # someone stranded in water (an old save) may wade out, slowly

    def set_terrain(self, world_map) -> None:
        """Water is impassable: paths go round lakes. A path to a water tile
        ends on the nearest dry tile (the shore, where you can drink)."""
        from world.simulation import TerrainType
        self.water = {pos for pos, t in world_map.tiles.items() if t.terrain == TerrainType.WATER}
        self.land_component = dict(getattr(world_map, 'land_component', {}))
        self._shore = {}
        self.path_cache.clear()

    def _nearest_dry(self, tile: Tuple[int, int], prefer=None) -> Optional[Tuple[int, int]]:
        """The nearest tile that isn't water, preferring the piece of land
        `prefer` (the walker's own), searching outward ring by ring."""
        key = (tile, prefer)
        if key in self._shore:
            return self._shore[key]
        x0, y0 = tile
        found = fallback = None
        for r in range(1, max(self.world_width, self.world_height)):
            ring = [(x0 + dx, y0 + dy) for dx in range(-r, r + 1) for dy in (-r, r)] + \
                   [(x0 + dx, y0 + dy) for dx in (-r, r) for dy in range(-r + 1, r)]
            dry = [c for c in ring if self._in_bounds(*c) and c not in self.water]
            if dry:
                dry.sort(key=lambda c: (c[0] - x0) ** 2 + (c[1] - y0) ** 2)
                same = [c for c in dry if prefer is None or self.land_component.get(c) == prefer]
                if same:
                    found = same[0]
                    break
                fallback = fallback or dry[0]
            if fallback and r > 12:        # nothing of our own land nearby: the nearest dry ground
                found = fallback
                break
        if len(self._shore) > 20000:
            self._shore.clear()
        self._shore[key] = found
        return found

    def find_path(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        obstacles: Optional[List[Tuple[int, int]]] = None
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Find path from start to end using A* algorithm.

        Returns list of (x, y) coordinates or None if no path found.
        """
        # Convert to grid coordinates
        start = (int(start_x), int(start_y))
        end = (int(end_x), int(end_y))

        # Bounds check
        if not self._in_bounds(start[0], start[1]) or not self._in_bounds(end[0], end[1]):
            return None

        # Water: a walker on land never steps into it; a target in the water
        # means its shore; land you can't reach (an island) has no path
        water = getattr(self, 'water', None) or set()
        wading = start in water
        if end in water:
            end = self._nearest_dry(end, prefer=None if wading else self.land_component.get(start))
            if end is None:
                return None
        components = getattr(self, 'land_component', None)
        if components and not wading and components.get(start) != components.get(end):
            return None

        # Check cache
        cache_key = (start, end)
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]

        # Initialize
        obstacles = set(obstacles) if obstacles else set()
        open_set = []
        closed_set = set()

        start_node = PathNode(start[0], start[1], 0, self._heuristic(start, end))
        heapq.heappush(open_set, start_node)

        nodes_dict = {(start[0], start[1]): start_node}

        # A* main loop
        while open_set:
            current = heapq.heappop(open_set)

            # Found goal
            if (current.x, current.y) == end:
                path = self._reconstruct_path(current)
                if len(self.path_cache) >= self.MAX_CACHED_PATHS:
                    self.path_cache.clear()  # bounded; paths are cheap to find again
                self.path_cache[cache_key] = path
                return path

            closed_set.add((current.x, current.y))

            # Check neighbors
            for neighbor_pos in self._get_neighbors(current.x, current.y):
                if neighbor_pos in closed_set or neighbor_pos in obstacles:
                    continue
                if neighbor_pos in water and not wading:
                    continue

                # Calculate costs
                move_cost = self._movement_cost(
                    current.x, current.y,
                    neighbor_pos[0], neighbor_pos[1]
                )
                if neighbor_pos in water:
                    move_cost *= self.WADING_COST
                tentative_g = current.g_cost + move_cost

                # Get or create neighbor node
                if neighbor_pos not in nodes_dict:
                    neighbor = PathNode(
                        neighbor_pos[0],
                        neighbor_pos[1],
                        tentative_g,
                        self._heuristic(neighbor_pos, end)
                    )
                    nodes_dict[neighbor_pos] = neighbor
                else:
                    neighbor = nodes_dict[neighbor_pos]
                    if tentative_g >= neighbor.g_cost:
                        continue
                    neighbor.g_cost = tentative_g

                neighbor.parent = current

                if neighbor not in open_set:
                    heapq.heappush(open_set, neighbor)

        # No path found
        return None

    def _heuristic(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Euclidean distance heuristic"""
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        return math.sqrt(dx * dx + dy * dy)

    def _movement_cost(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Cost to move from one tile to another (road tiles cost less, so
        paths follow roads agents have built: world/infrastructure.py)"""
        # Diagonal movement costs more
        cost = 1.414 if abs(x1 - x2) == 1 and abs(y1 - y2) == 1 else 1.0
        roads = getattr(self, 'road_tiles', None)
        if roads and (x2, y2) in roads:
            from world.infrastructure import ROAD_COST
            cost *= ROAD_COST
        return cost

    def _get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get valid neighboring positions (8-directional)"""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                nx, ny = x + dx, y + dy
                if self._in_bounds(nx, ny):
                    neighbors.append((nx, ny))

        return neighbors

    def _in_bounds(self, x: int, y: int) -> bool:
        """Check if position is within world bounds"""
        return 0 <= x < self.world_width and 0 <= y < self.world_height

    def _reconstruct_path(self, node: PathNode) -> List[Tuple[int, int]]:
        """Reconstruct path from end node to start"""
        path = []
        current = node

        while current:
            path.append((current.x, current.y))
            current = current.parent

        path.reverse()
        return path

    def clear_cache(self):
        """Clear path cache"""
        self.path_cache.clear()

    def get_next_step(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float
    ) -> Optional[Tuple[float, float]]:
        """
        Get next step towards target.
        Returns (x, y) coordinates or None.
        """
        path = self.find_path(start_x, start_y, end_x, end_y)

        if not path or len(path) < 2:
            return None

        # Return second point in path (first is current position)
        return (float(path[1][0]), float(path[1][1]))


class ResourceMemory:
    """
    Agent memory system for remembering resource locations.

    Agents remember where they found resources and can return to them.
    """

    def __init__(self, memory_capacity: int = 20):
        self.memory_capacity = memory_capacity
        self.resource_memories: Dict[str, List[Dict]] = {}

    def remember_resource(
        self,
        agent_id: str,
        resource_type: str,
        x: float,
        y: float,
        quantity: float,
        tick: int
    ):
        """Remember a resource location"""
        if agent_id not in self.resource_memories:
            self.resource_memories[agent_id] = []

        memory = {
            'resource_type': resource_type,
            'x': x,
            'y': y,
            'quantity': quantity,
            'last_seen_tick': tick,
            'visits': 1
        }

        # Check if already remembered
        for mem in self.resource_memories[agent_id]:
            if (mem['resource_type'] == resource_type and
                abs(mem['x'] - x) < 2 and abs(mem['y'] - y) < 2):
                # Update existing memory
                mem['quantity'] = quantity
                mem['last_seen_tick'] = tick
                mem['visits'] += 1
                return

        # Add new memory
        self.resource_memories[agent_id].append(memory)

        # Limit memory capacity
        if len(self.resource_memories[agent_id]) > self.memory_capacity:
            # Remove oldest memory
            self.resource_memories[agent_id].sort(key=lambda m: m['last_seen_tick'])
            self.resource_memories[agent_id].pop(0)

    def recall_resource(
        self,
        agent_id: str,
        resource_type: str,
        current_tick: int,
        max_age: int = 500
    ) -> Optional[Dict]:
        """
        Recall a resource location from memory.
        Returns closest remembered location that's not too old.
        """
        if agent_id not in self.resource_memories:
            return None

        # Filter by type and age
        valid_memories = [
            m for m in self.resource_memories[agent_id]
            if m['resource_type'] == resource_type
            and (current_tick - m['last_seen_tick']) < max_age
        ]

        if not valid_memories:
            return None

        # Return most recently visited
        valid_memories.sort(key=lambda m: m['visits'], reverse=True)
        return valid_memories[0]

    def forget_resource(self, agent_id: str, x: float, y: float):
        """Forget a resource at location (e.g., when depleted)"""
        if agent_id not in self.resource_memories:
            return

        self.resource_memories[agent_id] = [
            m for m in self.resource_memories[agent_id]
            if not (abs(m['x'] - x) < 2 and abs(m['y'] - y) < 2)
        ]

    def get_statistics(self, agent_id: str) -> Dict:
        """Get memory statistics for agent"""
        if agent_id not in self.resource_memories:
            return {'total_memories': 0, 'by_type': {}}

        memories = self.resource_memories[agent_id]
        by_type = {}

        for mem in memories:
            rtype = mem['resource_type']
            by_type[rtype] = by_type.get(rtype, 0) + 1

        return {
            'total_memories': len(memories),
            'by_type': by_type
        }
