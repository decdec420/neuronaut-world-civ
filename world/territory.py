"""
Territory & Land Ownership System - Mine vs Yours

Implements:
- Land claiming (agents mark and defend territory)
- Borders and control zones
- Trespassing detection and consequences
- Resource ownership within territories
- Territorial disputes and warfare
- Patrol and guard behaviors

Philosophy: Property creates conflict and cooperation.
Without territory, no borders, no ownership, no wars over land.
Territory is the foundation of civilization and conflict.
"""

import random
from engine.ids import new_uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum


class TerritoryType(Enum):
    """Types of territorial claims"""
    PERSONAL = "personal"  # Individual agent's land
    FAMILY = "family"  # Family territory
    TRIBAL = "tribal"  # Group/clan territory
    NATIONAL = "national"  # Government territory
    SACRED = "sacred"  # Religious territory
    COMMON = "common"  # Shared community land


@dataclass
class Territory:
    """A claimed territorial area"""
    id: str
    name: str
    territory_type: TerritoryType

    # Ownership
    owner_id: str  # Agent or group ID
    owner_name: str
    claimed_at: int  # Tick when claimed

    # Bounds (simple rectangular for now)
    center: Tuple[float, float]
    radius: float = 20.0  # Territory extends this far from center

    # Resources within territory
    resources: Set[str] = field(default_factory=set)  # Resource types claimed

    # Control
    defended: bool = False
    guards: Set[str] = field(default_factory=set)  # Agent IDs patrolling
    last_patrol: int = 0

    # Access control
    allowed_agents: Set[str] = field(default_factory=set)  # Who can enter
    banned_agents: Set[str] = field(default_factory=set)  # Who is banned

    # Trespassing tracking
    trespassers: List[str] = field(default_factory=list)  # Recent trespassers
    total_trespasses: int = 0


@dataclass
class Border:
    """A border between territories"""
    id: str
    territory1_id: str
    territory2_id: str

    # Disputes
    contested: bool = False
    conflict_count: int = 0


@dataclass
class TrespassEvent:
    """A recorded trespassing incident"""
    id: str
    trespasser_id: str
    territory_id: str
    tick: int

    # Response
    detected: bool = False
    warned: bool = False
    expelled: bool = False
    led_to_conflict: bool = False


class TerritoryManager:
    """
    Manages land ownership, borders, and territorial disputes.

    Key mechanics:
    - Agents claim land around resources/settlements
    - Territories can be defended or abandoned
    - Trespassing creates social conflict
    - Resource control drives territorial expansion
    """

    MAX_TRESPASS_EVENTS = 500

    def __init__(self):
        self.territories: Dict[str, Territory] = {}
        self.borders: Dict[str, Border] = {}
        self.trespass_events: Dict[str, TrespassEvent] = {}  # recent ones (MAX_TRESPASS_EVENTS)

        # Statistics
        self.total_claims: int = 0
        self.total_trespasses: int = 0
        self.total_territorial_conflicts: int = 0

    # ===== LAND CLAIMING =====

    def claim_territory(
        self,
        owner_id: str,
        owner_name: str,
        location: Tuple[float, float],
        radius: float,
        territory_type: TerritoryType,
        current_tick: int,
        resources: Optional[Set[str]] = None
    ) -> Optional[Territory]:
        """Agent claims a territory"""

        # Check if location already claimed by someone else
        existing = self.get_territory_at_location(location)
        if existing and existing.owner_id != owner_id:
            # Already claimed by another agent
            return None

        territory_id = str(new_uuid())

        # Generate name
        name = self._generate_territory_name(owner_name, territory_type, location)

        territory = Territory(
            id=territory_id,
            name=name,
            territory_type=territory_type,
            owner_id=owner_id,
            owner_name=owner_name,
            claimed_at=current_tick,
            center=location,
            radius=radius,
            resources=resources or set(),
            allowed_agents={owner_id}  # Owner always allowed
        )

        self.territories[territory_id] = territory
        self.total_claims += 1

        # Create borders with adjacent territories
        self._create_borders_for_territory(territory_id)

        return territory

    def _generate_territory_name(
        self,
        owner_name: str,
        territory_type: TerritoryType,
        location: Tuple[float, float]
    ) -> str:
        """Generate name for territory"""

        if territory_type == TerritoryType.PERSONAL:
            return f"{owner_name}'s Land"
        elif territory_type == TerritoryType.FAMILY:
            return f"{owner_name} Family Lands"
        elif territory_type == TerritoryType.TRIBAL:
            return f"{owner_name} Tribe Territory"
        elif territory_type == TerritoryType.SACRED:
            return f"Sacred Grounds of {owner_name}"
        else:
            # Use location-based names
            x, y = location
            directions = []
            if x < 50:
                directions.append("Western")
            elif x > 150:
                directions.append("Eastern")
            if y < 50:
                directions.append("Northern")
            elif y > 150:
                directions.append("Southern")

            direction_str = " ".join(directions) if directions else "Central"
            return f"{direction_str} Territory"

    def _create_borders_for_territory(self, territory_id: str):
        """Create borders with adjacent territories"""

        if territory_id not in self.territories:
            return

        new_territory = self.territories[territory_id]

        # Find adjacent territories (within 2x radius)
        for other_id, other_territory in self.territories.items():
            if other_id == territory_id:
                continue

            # Calculate distance between centers
            dist = ((new_territory.center[0] - other_territory.center[0])**2 +
                   (new_territory.center[1] - other_territory.center[1])**2)**0.5

            max_dist = (new_territory.radius + other_territory.radius) * 1.5

            if dist < max_dist:
                # Adjacent - create border
                border_id = str(new_uuid())
                border = Border(
                    id=border_id,
                    territory1_id=territory_id,
                    territory2_id=other_id
                )

                self.borders[border_id] = border

    # ===== TRESPASSING =====

    def check_trespassing(
        self,
        agent_id: str,
        location: Tuple[float, float],
        current_tick: int
    ) -> Optional[Territory]:
        """Check if agent is trespassing, return territory if so"""

        territory = self.get_territory_at_location(location)

        if not territory:
            return None  # No territory here

        # Check if agent is allowed
        if agent_id in territory.allowed_agents:
            return None  # Allowed

        if agent_id == territory.owner_id:
            return None  # Owner can't trespass

        # TRESPASSING DETECTED!
        if agent_id not in territory.trespassers:
            territory.trespassers.append(agent_id)

        territory.total_trespasses += 1

        # Record event
        event_id = str(new_uuid())
        event = TrespassEvent(
            id=event_id,
            trespasser_id=agent_id,
            territory_id=territory.id,
            tick=current_tick,
            detected=territory.defended  # Only detected if defended
        )

        self.trespass_events[event_id] = event
        self.total_trespasses += 1
        # Keep the recent incidents (the totals keep counting); this grew by
        # ~7 a tick, 35,000 in a 6,000-tick run
        if len(self.trespass_events) > self.MAX_TRESPASS_EVENTS * 1.2:
            for old_id in list(self.trespass_events)[:len(self.trespass_events) - self.MAX_TRESPASS_EVENTS]:
                del self.trespass_events[old_id]

        return territory

    # ===== TERRITORY CONTROL =====

    def add_guard(self, territory_id: str, guard_id: str) -> bool:
        """Add guard to patrol territory"""

        if territory_id not in self.territories:
            return False

        territory = self.territories[territory_id]
        territory.guards.add(guard_id)
        territory.defended = True

        return True

    def forget_the_dead(self, is_alive) -> List[str]:
        """The dead guard nothing and hold nothing: they leave every guard
        list (land with no living guard is undefended), and land whose owner
        is dead is no one's, free to claim again. Nothing did this: a dead
        owner's land stayed defended by dead guards for good, and everyone
        standing in it went on feeling they trespassed. Returns the names of
        the lands let go."""
        released = []
        for territory_id in sorted(self.territories):
            territory = self.territories[territory_id]
            dead = {g for g in territory.guards if not is_alive(g)}
            if dead:
                territory.guards -= dead
                territory.defended = bool(territory.guards)
            territory.allowed_agents = {a for a in territory.allowed_agents if is_alive(a)}
            if not is_alive(territory.owner_id):
                released.append(territory.name)
                del self.territories[territory_id]
                for border_id in [b for b, border in self.borders.items()
                                  if territory_id in (border.territory1_id, border.territory2_id)]:
                    del self.borders[border_id]
        return released

    def remove_guard(self, territory_id: str, guard_id: str) -> bool:
        """Remove guard from territory"""

        if territory_id not in self.territories:
            return False

        territory = self.territories[territory_id]
        territory.guards.discard(guard_id)

        # If no more guards, not defended
        if len(territory.guards) == 0:
            territory.defended = False

        return True

    def grant_access(self, territory_id: str, agent_id: str) -> bool:
        """Grant agent access to territory"""

        if territory_id not in self.territories:
            return False

        territory = self.territories[territory_id]
        territory.allowed_agents.add(agent_id)
        territory.banned_agents.discard(agent_id)  # Remove from banned if present

        return True

    def ban_agent(self, territory_id: str, agent_id: str) -> bool:
        """Ban agent from territory"""

        if territory_id not in self.territories:
            return False

        territory = self.territories[territory_id]
        territory.banned_agents.add(agent_id)
        territory.allowed_agents.discard(agent_id)  # Remove from allowed if present

        return True

    # ===== TERRITORIAL CONFLICTS =====

    def create_border_dispute(
        self,
        territory1_id: str,
        territory2_id: str
    ) -> Optional[Border]:
        """Create or escalate a border dispute"""

        # Find existing border
        border = None
        for b in self.borders.values():
            if (b.territory1_id == territory1_id and b.territory2_id == territory2_id) or \
               (b.territory1_id == territory2_id and b.territory2_id == territory1_id):
                border = b
                break

        if not border:
            # Create new border
            border_id = str(new_uuid())
            border = Border(
                id=border_id,
                territory1_id=territory1_id,
                territory2_id=territory2_id,
                contested=True,
                conflict_count=1
            )
            self.borders[border_id] = border
        else:
            # Escalate existing border
            border.contested = True
            border.conflict_count += 1

        self.total_territorial_conflicts += 1

        return border

    # ===== QUERIES =====

    def get_territory_at_location(self, location: Tuple[float, float]) -> Optional[Territory]:
        """Get territory containing this location"""

        for territory in self.territories.values():
            # Check if location is within radius of territory center
            dist = ((location[0] - territory.center[0])**2 +
                   (location[1] - territory.center[1])**2)**0.5

            if dist <= territory.radius:
                return territory

        return None

    def get_agent_territories(self, agent_id: str) -> List[Territory]:
        """Get all territories owned by agent"""
        return [t for t in self.territories.values() if t.owner_id == agent_id]

    def get_nearby_territories(
        self,
        location: Tuple[float, float],
        radius: float = 50.0
    ) -> List[Territory]:
        """Get territories within radius of location"""

        nearby = []
        for territory in self.territories.values():
            dist = ((location[0] - territory.center[0])**2 +
                   (location[1] - territory.center[1])**2)**0.5

            if dist < radius:
                nearby.append(territory)

        return nearby

    def is_location_claimed(self, location: Tuple[float, float]) -> bool:
        """Check if location is within any claimed territory"""
        return self.get_territory_at_location(location) is not None

    def get_statistics(self) -> Dict:
        """Get territory system statistics"""

        total_land_claimed = sum(3.14159 * t.radius**2 for t in self.territories.values())
        avg_territory_size = total_land_claimed / max(1, len(self.territories))

        contested_borders = sum(1 for b in self.borders.values() if b.contested)
        defended_territories = sum(1 for t in self.territories.values() if t.defended)

        return {
            'total_territories': len(self.territories),
            'total_claims': self.total_claims,
            'total_land_area': round(total_land_claimed, 1),
            'avg_territory_size': round(avg_territory_size, 1),
            'total_borders': len(self.borders),
            'contested_borders': contested_borders,
            'total_trespasses': self.total_trespasses,
            'territorial_conflicts': self.total_territorial_conflicts,
            'defended_territories': defended_territories
        }
