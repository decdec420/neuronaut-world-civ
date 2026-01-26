"""
Multi-Civilization System - Multiple AI Societies Compete & Cooperate

This system enables MULTIPLE independent AI civilizations to develop simultaneously.
Each civilization has unique culture, territory, and goals - creating rich dynamics:
- Competition for resources and territory
- Emergent diplomacy and alliances
- Cultural diffusion and trade
- Wars, peace treaties, and espionage
- Technology races and knowledge sharing

Key Features:
- **Multiple Spawn Points**: Civs start in different locations
- **Cultural Differentiation**: Each has unique traits, values, specializations
- **Border Detection**: Automatic detection when civs make contact
- **Emergent Diplomacy**: Relations form through swarm consensus, not hardcoding
- **Territory Management**: Dynamic borders, contested zones
- **Cultural Diffusion**: Knowledge/customs spread between civs
- **Civilization Lifecycle**: Birth, growth, decline, death of societies

This creates LIVING WORLDS where civilizations rise and fall, compete and cooperate,
discover and destroy - all through emergent AI behavior.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import math

logger = logging.getLogger(__name__)


class DiplomaticRelation(Enum):
    """Relationship between two civilizations"""
    UNKNOWN = "unknown"  # Haven't made contact yet
    NEUTRAL = "neutral"  # Aware of each other, no strong feelings
    FRIENDLY = "friendly"  # Positive interactions
    ALLIED = "allied"  # Formal alliance
    TENSE = "tense"  # Negative interactions
    HOSTILE = "hostile"  # Active conflict
    WAR = "war"  # Declared war


class CultureType(Enum):
    """Cultural archetypes that emerge"""
    NOMADIC = "nomadic"  # Mobile, adaptive
    AGRARIAN = "agrarian"  # Farming-focused
    MARITIME = "maritime"  # Water/trade-focused
    MILITARISTIC = "militaristic"  # Conquest-focused
    SCHOLARLY = "scholarly"  # Knowledge-focused
    SPIRITUAL = "spiritual"  # Religion-focused
    MERCANTILE = "mercantile"  # Trade-focused


@dataclass
class Territory:
    """Defined territory for a civilization"""
    civilization_id: str
    tiles: Set[Tuple[int, int]] = field(default_factory=set)
    border_tiles: Set[Tuple[int, int]] = field(default_factory=set)
    contested_tiles: Set[Tuple[int, int]] = field(default_factory=set)

    def add_tile(self, x: int, y: int):
        """Add a tile to territory"""
        self.tiles.add((x, y))

    def remove_tile(self, x: int, y: int):
        """Remove a tile from territory"""
        self.tiles.discard((x, y))

    def update_borders(self, world_tiles: Set[Tuple[int, int]]):
        """Recalculate border tiles (tiles adjacent to non-territory)"""
        self.border_tiles.clear()

        for x, y in self.tiles:
            # Check 4 cardinal directions
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (x + dx, y + dy)
                if neighbor not in self.tiles and neighbor in world_tiles:
                    self.border_tiles.add((x, y))
                    break

    def get_size(self) -> int:
        """Get territory size in tiles"""
        return len(self.tiles)


@dataclass
class CivilizationState:
    """Complete state of a civilization"""
    civilization_id: str
    name: Optional[str] = None

    # Location & Territory
    spawn_location: Tuple[int, int] = (0, 0)
    capital_location: Optional[Tuple[int, int]] = None
    territory: Territory = None

    # Population
    agent_ids: Set[str] = field(default_factory=set)
    population: int = 0
    founding_tick: int = 0

    # Culture
    culture_type: CultureType = CultureType.NOMADIC
    values: List[str] = field(default_factory=list)
    specializations: Dict[str, int] = field(default_factory=dict)  # activity -> count

    # Technology & Knowledge
    technologies: Set[str] = field(default_factory=set)
    discoveries: List[str] = field(default_factory=list)

    # Diplomacy
    known_civilizations: Set[str] = field(default_factory=set)
    diplomatic_relations: Dict[str, DiplomaticRelation] = field(default_factory=dict)
    treaties: List[str] = field(default_factory=list)

    # Resources & Economy
    total_resources: Dict[str, int] = field(default_factory=dict)
    trade_routes: List[str] = field(default_factory=list)

    # Military
    military_strength: float = 0.0
    active_wars: Set[str] = field(default_factory=set)

    # Statistics
    total_births: int = 0
    total_deaths: int = 0
    major_achievements: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.territory is None:
            self.territory = Territory(civilization_id=self.civilization_id)


@dataclass
class DiplomaticContact:
    """Record of contact between civilizations"""
    civ1_id: str
    civ2_id: str
    first_contact_tick: int
    contact_location: Tuple[int, int]
    first_contact_type: str  # "border", "agent_meeting", "trade"
    contact_count: int = 1


class CivilizationManager:
    """
    Manages multiple independent AI civilizations

    Handles:
    - Civilization spawning and initialization
    - Territory management and borders
    - Diplomatic relations and contact
    - Cultural differentiation
    - Inter-civilization dynamics
    - Resource competition
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Configuration
        self.max_civilizations = self.config.get('max_civilizations', 10)
        self.min_spawn_distance = self.config.get('min_spawn_distance', 20)
        self.initial_population = self.config.get('initial_population', 3)
        self.contact_detection_radius = self.config.get('contact_detection_radius', 3)

        # Civilizations
        self.civilizations: Dict[str, CivilizationState] = {}
        self.active_contacts: Dict[Tuple[str, str], DiplomaticContact] = {}

        # World state
        self.world_size: Tuple[int, int] = (100, 100)  # Will be updated
        self.occupied_tiles: Dict[Tuple[int, int], str] = {}  # tile -> civ_id

        # Statistics
        self.total_civilizations_created = 0
        self.total_contacts_made = 0
        self.total_wars = 0
        self.total_treaties = 0

    # ============================================================================
    # CIVILIZATION SPAWNING
    # ============================================================================

    def spawn_civilization(
        self,
        world_size: Tuple[int, int],
        spawn_location: Optional[Tuple[int, int]] = None,
        culture_type: Optional[CultureType] = None,
        initial_agents: List[str] = None
    ) -> CivilizationState:
        """
        Spawn a new civilization

        Args:
            world_size: (width, height) of the world
            spawn_location: Where to spawn (None = random valid location)
            culture_type: Cultural archetype (None = random based on terrain)
            initial_agents: Agent IDs for founding population

        Returns:
            CivilizationState for the new civilization
        """

        self.world_size = world_size

        # Generate civilization ID
        civ_id = f"civ_{self.total_civilizations_created}"

        # Determine spawn location
        if spawn_location is None:
            spawn_location = self._find_valid_spawn_location()

        if spawn_location is None:
            raise ValueError("No valid spawn location found")

        # Determine culture type based on terrain if not specified
        if culture_type is None:
            culture_type = self._determine_culture_from_location(spawn_location)

        # Create civilization
        civ = CivilizationState(
            civilization_id=civ_id,
            spawn_location=spawn_location,
            capital_location=spawn_location,
            culture_type=culture_type,
            founding_tick=0,  # Will be updated by caller
            agent_ids=set(initial_agents or []),
            population=len(initial_agents or [])
        )

        # Initialize territory with spawn location
        civ.territory.add_tile(*spawn_location)
        self.occupied_tiles[spawn_location] = civ_id

        # Assign cultural values based on type
        civ.values = self._generate_cultural_values(culture_type)

        # Store civilization
        self.civilizations[civ_id] = civ
        self.total_civilizations_created += 1

        logger.info(f"🌍 Spawned civilization {civ_id} at {spawn_location} ({culture_type.value})")

        return civ

    def _find_valid_spawn_location(self) -> Optional[Tuple[int, int]]:
        """Find a valid spawn location away from existing civilizations"""

        width, height = self.world_size
        max_attempts = 100

        for _ in range(max_attempts):
            x = random.randint(5, width - 5)
            y = random.randint(5, height - 5)

            # Check distance from existing civilizations
            valid = True
            for civ in self.civilizations.values():
                spawn_x, spawn_y = civ.spawn_location
                distance = math.sqrt((x - spawn_x)**2 + (y - spawn_y)**2)

                if distance < self.min_spawn_distance:
                    valid = False
                    break

            if valid:
                return (x, y)

        return None

    def _determine_culture_from_location(self, location: Tuple[int, int]) -> CultureType:
        """Determine culture type based on spawn terrain"""
        # TODO: Check actual terrain type when integrated
        # For now, random with weights
        return random.choice([
            CultureType.NOMADIC,
            CultureType.AGRARIAN,
            CultureType.MILITARISTIC,
            CultureType.SCHOLARLY,
            CultureType.MERCANTILE
        ])

    def _generate_cultural_values(self, culture_type: CultureType) -> List[str]:
        """Generate cultural values based on type"""

        value_sets = {
            CultureType.NOMADIC: ["freedom", "adaptability", "exploration"],
            CultureType.AGRARIAN: ["stability", "cooperation", "patience"],
            CultureType.MARITIME: ["trade", "exploration", "innovation"],
            CultureType.MILITARISTIC: ["honor", "strength", "discipline"],
            CultureType.SCHOLARLY: ["knowledge", "wisdom", "curiosity"],
            CultureType.SPIRITUAL: ["harmony", "enlightenment", "tradition"],
            CultureType.MERCANTILE: ["prosperity", "cunning", "negotiation"]
        }

        return value_sets.get(culture_type, ["survival", "growth"])

    # ============================================================================
    # TERRITORY MANAGEMENT
    # ============================================================================

    def expand_territory(
        self,
        civilization_id: str,
        new_tile: Tuple[int, int],
        force: bool = False
    ) -> bool:
        """
        Expand civilization's territory to include new tile

        Args:
            civilization_id: Civilization expanding
            new_tile: Tile to claim
            force: If True, can claim contested tiles

        Returns:
            True if successfully claimed
        """

        if civilization_id not in self.civilizations:
            return False

        civ = self.civilizations[civilization_id]
        x, y = new_tile

        # Check if tile is already owned
        current_owner = self.occupied_tiles.get(new_tile)

        if current_owner and current_owner != civilization_id:
            if not force:
                # Mark as contested
                civ.territory.contested_tiles.add(new_tile)
                other_civ = self.civilizations[current_owner]
                other_civ.territory.contested_tiles.add(new_tile)

                logger.debug(f"⚔️ Tile {new_tile} contested between {civilization_id} and {current_owner}")
                return False
            else:
                # Take from other civilization
                other_civ = self.civilizations[current_owner]
                other_civ.territory.remove_tile(x, y)
                logger.info(f"⚔️ {civilization_id} claimed {new_tile} from {current_owner}")

        # Claim tile
        civ.territory.add_tile(x, y)
        self.occupied_tiles[new_tile] = civilization_id

        # Update borders
        all_tiles = set(self.occupied_tiles.keys())
        civ.territory.update_borders(all_tiles)

        return True

    def get_civilization_at_location(self, location: Tuple[int, int]) -> Optional[str]:
        """Get civilization ID that controls this tile"""
        return self.occupied_tiles.get(location)

    def get_border_tiles(self, civilization_id: str) -> Set[Tuple[int, int]]:
        """Get border tiles for a civilization"""
        if civilization_id not in self.civilizations:
            return set()
        return self.civilizations[civilization_id].territory.border_tiles

    # ============================================================================
    # CONTACT & DIPLOMACY
    # ============================================================================

    def detect_contact(
        self,
        civilization_id: str,
        agent_location: Tuple[int, int],
        tick: int
    ) -> Optional[str]:
        """
        Detect if an agent has made contact with another civilization

        Args:
            civilization_id: Agent's civilization
            agent_location: Agent's current location
            tick: Current simulation tick

        Returns:
            ID of contacted civilization, or None
        """

        if civilization_id not in self.civilizations:
            return None

        x, y = agent_location

        # Check nearby tiles for other civilizations
        for dx in range(-self.contact_detection_radius, self.contact_detection_radius + 1):
            for dy in range(-self.contact_detection_radius, self.contact_detection_radius + 1):
                check_tile = (x + dx, y + dy)
                other_civ = self.occupied_tiles.get(check_tile)

                if other_civ and other_civ != civilization_id:
                    # Contact made!
                    self._record_contact(
                        civ1_id=civilization_id,
                        civ2_id=other_civ,
                        tick=tick,
                        location=agent_location,
                        contact_type="agent_meeting"
                    )
                    return other_civ

        return None

    def _record_contact(
        self,
        civ1_id: str,
        civ2_id: str,
        tick: int,
        location: Tuple[int, int],
        contact_type: str
    ):
        """Record contact between two civilizations"""

        # Ensure consistent ordering
        key = tuple(sorted([civ1_id, civ2_id]))

        if key in self.active_contacts:
            # Update existing contact
            self.active_contacts[key].contact_count += 1
        else:
            # New contact!
            contact = DiplomaticContact(
                civ1_id=key[0],
                civ2_id=key[1],
                first_contact_tick=tick,
                contact_location=location,
                first_contact_type=contact_type
            )
            self.active_contacts[key] = contact
            self.total_contacts_made += 1

            # Update civilizations' awareness
            civ1 = self.civilizations[civ1_id]
            civ2 = self.civilizations[civ2_id]

            civ1.known_civilizations.add(civ2_id)
            civ2.known_civilizations.add(civ1_id)

            # Initialize as neutral
            civ1.diplomatic_relations[civ2_id] = DiplomaticRelation.NEUTRAL
            civ2.diplomatic_relations[civ1_id] = DiplomaticRelation.NEUTRAL

            logger.info(f"🤝 First contact: {civ1_id} met {civ2_id} at {location}")

    def update_diplomatic_relation(
        self,
        civ1_id: str,
        civ2_id: str,
        new_relation: DiplomaticRelation,
        reason: str = ""
    ):
        """Update relationship between two civilizations"""

        if civ1_id not in self.civilizations or civ2_id not in self.civilizations:
            return

        civ1 = self.civilizations[civ1_id]
        civ2 = self.civilizations[civ2_id]

        old_relation = civ1.diplomatic_relations.get(civ2_id, DiplomaticRelation.UNKNOWN)

        # Update both sides
        civ1.diplomatic_relations[civ2_id] = new_relation
        civ2.diplomatic_relations[civ1_id] = new_relation

        # Track wars
        if new_relation == DiplomaticRelation.WAR and old_relation != DiplomaticRelation.WAR:
            civ1.active_wars.add(civ2_id)
            civ2.active_wars.add(civ1_id)
            self.total_wars += 1
            logger.info(f"⚔️ WAR declared: {civ1_id} vs {civ2_id} - {reason}")

        elif old_relation == DiplomaticRelation.WAR and new_relation != DiplomaticRelation.WAR:
            civ1.active_wars.discard(civ2_id)
            civ2.active_wars.discard(civ1_id)
            logger.info(f"🕊️ Peace: {civ1_id} and {civ2_id} - {reason}")

        # Track alliances
        if new_relation == DiplomaticRelation.ALLIED and old_relation != DiplomaticRelation.ALLIED:
            self.total_treaties += 1
            logger.info(f"🤝 Alliance formed: {civ1_id} and {civ2_id}")

    def get_diplomatic_relation(self, civ1_id: str, civ2_id: str) -> DiplomaticRelation:
        """Get relationship between two civilizations"""
        if civ1_id not in self.civilizations:
            return DiplomaticRelation.UNKNOWN

        return self.civilizations[civ1_id].diplomatic_relations.get(
            civ2_id,
            DiplomaticRelation.UNKNOWN
        )

    # ============================================================================
    # CULTURAL DIFFUSION
    # ============================================================================

    def transfer_knowledge(
        self,
        from_civ: str,
        to_civ: str,
        technology: str,
        through_trade: bool = True
    ) -> bool:
        """
        Transfer knowledge/technology between civilizations

        Args:
            from_civ: Source civilization
            to_civ: Receiving civilization
            technology: Technology name
            through_trade: If True, peaceful transfer; if False, espionage/war

        Returns:
            True if successful
        """

        if from_civ not in self.civilizations or to_civ not in self.civilizations:
            return False

        source = self.civilizations[from_civ]
        recipient = self.civilizations[to_civ]

        # Check if source has the technology
        if technology not in source.technologies:
            return False

        # Check if recipient already has it
        if technology in recipient.technologies:
            return False

        # Check diplomatic relation
        relation = self.get_diplomatic_relation(from_civ, to_civ)

        if through_trade and relation not in [DiplomaticRelation.FRIENDLY, DiplomaticRelation.ALLIED]:
            return False

        # Transfer!
        recipient.technologies.add(technology)
        recipient.discoveries.append(f"Learned {technology} from {source.name or from_civ}")

        logger.info(f"📚 Knowledge transfer: {from_civ} → {to_civ} ({technology})")

        return True

    # ============================================================================
    # QUERIES & STATISTICS
    # ============================================================================

    def get_civilization(self, civilization_id: str) -> Optional[CivilizationState]:
        """Get civilization state"""
        return self.civilizations.get(civilization_id)

    def get_all_civilizations(self) -> List[CivilizationState]:
        """Get all civilizations"""
        return list(self.civilizations.values())

    def get_active_wars(self) -> List[Tuple[str, str]]:
        """Get all active wars"""
        wars = []
        seen = set()

        for civ_id, civ in self.civilizations.items():
            for enemy_id in civ.active_wars:
                key = tuple(sorted([civ_id, enemy_id]))
                if key not in seen:
                    wars.append(key)
                    seen.add(key)

        return wars

    def get_statistics(self) -> Dict[str, Any]:
        """Get multi-civilization statistics"""

        total_population = sum(civ.population for civ in self.civilizations.values())
        total_territory = sum(civ.territory.get_size() for civ in self.civilizations.values())

        # Count relations
        relation_counts = {}
        for civ in self.civilizations.values():
            for relation in civ.diplomatic_relations.values():
                relation_counts[relation.value] = relation_counts.get(relation.value, 0) + 1

        return {
            'total_civilizations': len(self.civilizations),
            'active_civilizations': sum(1 for c in self.civilizations.values() if c.population > 0),
            'total_population': total_population,
            'total_territory_tiles': total_territory,
            'total_contacts': self.total_contacts_made,
            'active_wars': len(self.get_active_wars()),
            'total_wars_ever': self.total_wars,
            'total_treaties': self.total_treaties,
            'diplomatic_relations': relation_counts,
            'largest_civilization': max(
                self.civilizations.values(),
                key=lambda c: c.population
            ).civilization_id if self.civilizations else None
        }

    def export_civilization_summary(self, civilization_id: str) -> Optional[Dict[str, Any]]:
        """Export complete summary of a civilization"""

        if civilization_id not in self.civilizations:
            return None

        civ = self.civilizations[civilization_id]

        return {
            'id': civ.civilization_id,
            'name': civ.name,
            'culture_type': civ.culture_type.value,
            'values': civ.values,
            'population': civ.population,
            'territory_size': civ.territory.get_size(),
            'capital': civ.capital_location,
            'technologies': list(civ.technologies),
            'known_civilizations': list(civ.known_civilizations),
            'diplomatic_relations': {
                civ_id: relation.value
                for civ_id, relation in civ.diplomatic_relations.items()
            },
            'active_wars': list(civ.active_wars),
            'major_achievements': civ.major_achievements,
            'total_births': civ.total_births,
            'total_deaths': civ.total_deaths
        }
