"""
Building and Construction System - Civilization-Style Buildings

Agents can construct buildings that provide benefits:
- Houses: Shelter, comfort, storage
- Workshops: Craft items, improve efficiency
- Markets: Trading hub, economic boost
- Temples: Culture, happiness, community
- Walls: Defense, security
- Farms: Food production
- Mines: Resource extraction
- Libraries: Research, learning
- Barracks: Military training
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from datetime import datetime

from agents.agent import Position, Agent


class BuildingType(Enum):
    """Types of buildings agents can construct"""
    # BASIC STRUCTURES
    SHELTER = "shelter"  # Basic housing
    HOUSE = "house"  # Improved housing
    MANSION = "mansion"  # Luxury housing

    # PRODUCTION
    WORKSHOP = "workshop"  # Crafting facility
    SMITHY = "smithy"  # Metal working
    POTTERY_SHOP = "pottery_shop"  # Pottery and ceramics
    WEAVING_MILL = "weaving_mill"  # Textiles
    BREWERY = "brewery"  # Alcohol production
    BAKERY = "bakery"  # Food preparation

    # RESOURCE EXTRACTION
    FARM = "farm"  # Food production
    RANCH = "ranch"  # Animal husbandry
    MINE = "mine"  # Stone and metal extraction
    QUARRY = "quarry"  # Stone extraction
    LUMBER_MILL = "lumber_mill"  # Wood processing
    FISHERY = "fishery"  # Fish harvesting

    # ECONOMIC
    MARKET = "market"  # Trading hub
    BANK = "bank"  # Wealth storage and loans
    WAREHOUSE = "warehouse"  # Storage facility
    SHOP = "shop"  # Retail

    # CULTURAL & SOCIAL
    TEMPLE = "temple"  # Religious/spiritual center
    THEATER = "theater"  # Entertainment
    LIBRARY = "library"  # Knowledge and research
    SCHOOL = "school"  # Education
    TAVERN = "tavern"  # Social gathering
    BATHHOUSE = "bathhouse"  # Hygiene and relaxation

    # MILITARY & DEFENSE
    BARRACKS = "barracks"  # Military training
    ARMORY = "armory"  # Weapon storage
    WALL = "wall"  # Defensive structure
    TOWER = "tower"  # Watch tower
    GATE = "gate"  # Fortified entrance

    # INFRASTRUCTURE
    ROAD = "road"  # Transportation
    BRIDGE = "bridge"  # Water crossing
    AQUEDUCT = "aqueduct"  # Water supply
    GRANARY = "granary"  # Food storage

    # SPECIAL
    MONUMENT = "monument"  # Cultural landmark
    PALACE = "palace"  # Government center
    UNIVERSITY = "university"  # Advanced research
    HOSPITAL = "hospital"  # Healthcare
    LABORATORY = "laboratory"  # Scientific research


@dataclass
class BuildingCost:
    """Cost to construct a building"""
    wood: int = 0
    stone: int = 0
    metal: int = 0
    coins: float = 0.0
    labor_time: int = 10  # Ticks to complete
    required_skill: Optional[str] = None
    min_skill_level: float = 0.0


@dataclass
class BuildingBenefits:
    """Benefits provided by a building"""
    # Production
    produces_item: Optional[str] = None
    production_rate: float = 0.0  # Items per tick

    # Economic
    wealth_generation: float = 0.0  # Coins per tick
    storage_capacity: int = 0
    trade_bonus: float = 0.0  # Multiplier for trades

    # Social
    happiness_bonus: float = 0.0
    status_bonus: float = 0.0
    social_capacity: int = 0  # How many agents can gather

    # Safety
    defense_value: int = 0
    security_bonus: float = 0.0

    # Knowledge
    research_bonus: float = 0.0
    skill_training: Optional[str] = None
    training_rate: float = 0.0

    # Health
    health_bonus: float = 0.0
    healing_rate: float = 0.0

    # Needs satisfaction
    shelter_value: float = 0.0
    comfort_value: float = 0.0


# Building Templates
BUILDING_TEMPLATES: Dict[BuildingType, Tuple[BuildingCost, BuildingBenefits]] = {
    # BASIC HOUSING
    BuildingType.SHELTER: (
        BuildingCost(wood=10, labor_time=5),
        BuildingBenefits(shelter_value=0.3, storage_capacity=5)
    ),
    BuildingType.HOUSE: (
        BuildingCost(wood=30, stone=20, labor_time=20, required_skill="construction", min_skill_level=0.3),
        BuildingBenefits(shelter_value=0.6, comfort_value=0.3, storage_capacity=15, happiness_bonus=0.1)
    ),
    BuildingType.MANSION: (
        BuildingCost(wood=100, stone=80, metal=20, coins=500, labor_time=100, required_skill="construction", min_skill_level=0.7),
        BuildingBenefits(shelter_value=1.0, comfort_value=0.8, storage_capacity=50, happiness_bonus=0.3, status_bonus=0.2)
    ),

    # PRODUCTION BUILDINGS
    BuildingType.WORKSHOP: (
        BuildingCost(wood=40, stone=10, labor_time=15),
        BuildingBenefits(skill_training="crafting", training_rate=0.1, storage_capacity=20)
    ),
    BuildingType.SMITHY: (
        BuildingCost(wood=30, stone=50, metal=10, labor_time=30, required_skill="metalworking", min_skill_level=0.3),
        BuildingBenefits(
            produces_item="tools",
            production_rate=0.5,
            skill_training="metalworking",
            training_rate=0.15
        )
    ),
    BuildingType.BAKERY: (
        BuildingCost(wood=25, stone=15, labor_time=15),
        BuildingBenefits(
            produces_item="bread",
            production_rate=2.0,
            skill_training="cooking",
            training_rate=0.1
        )
    ),

    # RESOURCE EXTRACTION
    BuildingType.FARM: (
        BuildingCost(wood=50, labor_time=30, required_skill="farming", min_skill_level=0.2),
        BuildingBenefits(
            produces_item="food",
            production_rate=5.0,
            wealth_generation=2.0
        )
    ),
    BuildingType.MINE: (
        BuildingCost(wood=60, stone=30, labor_time=50, required_skill="mining", min_skill_level=0.4),
        BuildingBenefits(
            produces_item="stone",
            production_rate=3.0,
            wealth_generation=5.0
        )
    ),
    BuildingType.LUMBER_MILL: (
        BuildingCost(wood=40, stone=20, labor_time=25),
        BuildingBenefits(
            produces_item="wood",
            production_rate=4.0,
            wealth_generation=3.0
        )
    ),

    # ECONOMIC
    BuildingType.MARKET: (
        BuildingCost(wood=80, stone=40, labor_time=40),
        BuildingBenefits(
            trade_bonus=0.3,
            social_capacity=20,
            wealth_generation=10.0,
            status_bonus=0.1
        )
    ),
    BuildingType.BANK: (
        BuildingCost(wood=50, stone=100, metal=30, coins=1000, labor_time=60, required_skill="finance", min_skill_level=0.5),
        BuildingBenefits(
            wealth_generation=20.0,
            storage_capacity=100,
            status_bonus=0.2
        )
    ),
    BuildingType.WAREHOUSE: (
        BuildingCost(wood=60, stone=30, labor_time=25),
        BuildingBenefits(storage_capacity=100)
    ),

    # CULTURAL
    BuildingType.TEMPLE: (
        BuildingCost(wood=100, stone=150, metal=20, coins=500, labor_time=80),
        BuildingBenefits(
            happiness_bonus=0.4,
            social_capacity=50,
            comfort_value=0.3,
            status_bonus=0.15
        )
    ),
    BuildingType.LIBRARY: (
        BuildingCost(wood=80, stone=60, labor_time=50, required_skill="scholarly", min_skill_level=0.3),
        BuildingBenefits(
            research_bonus=0.5,
            skill_training="knowledge",
            training_rate=0.2,
            social_capacity=15
        )
    ),
    BuildingType.THEATER: (
        BuildingCost(wood=70, stone=50, labor_time=40),
        BuildingBenefits(
            happiness_bonus=0.3,
            social_capacity=30,
            status_bonus=0.1
        )
    ),
    BuildingType.TAVERN: (
        BuildingCost(wood=40, stone=20, labor_time=20),
        BuildingBenefits(
            happiness_bonus=0.2,
            social_capacity=25,
            wealth_generation=5.0
        )
    ),

    # MILITARY
    BuildingType.BARRACKS: (
        BuildingCost(wood=80, stone=60, metal=20, labor_time=50),
        BuildingBenefits(
            defense_value=50,
            skill_training="combat",
            training_rate=0.25,
            social_capacity=20
        )
    ),
    BuildingType.WALL: (
        BuildingCost(stone=200, labor_time=100, required_skill="construction", min_skill_level=0.5),
        BuildingBenefits(
            defense_value=100,
            security_bonus=0.5
        )
    ),
    BuildingType.TOWER: (
        BuildingCost(wood=30, stone=80, labor_time=40),
        BuildingBenefits(
            defense_value=30,
            security_bonus=0.3
        )
    ),

    # SPECIAL
    BuildingType.UNIVERSITY: (
        BuildingCost(wood=150, stone=200, metal=50, coins=2000, labor_time=150, required_skill="scholarly", min_skill_level=0.7),
        BuildingBenefits(
            research_bonus=1.0,
            skill_training="all",
            training_rate=0.3,
            social_capacity=40,
            status_bonus=0.3
        )
    ),
    BuildingType.PALACE: (
        BuildingCost(wood=300, stone=400, metal=100, coins=5000, labor_time=200, required_skill="construction", min_skill_level=0.9),
        BuildingBenefits(
            happiness_bonus=0.5,
            status_bonus=0.5,
            wealth_generation=50.0,
            social_capacity=100
        )
    ),
}


@dataclass
class Building:
    """A constructed building in the world"""
    id: str
    building_type: BuildingType
    name: str
    location: Position
    owner_id: Optional[str] = None

    # Construction
    construction_progress: float = 0.0  # 0-1, 1 = complete
    is_complete: bool = False
    constructed_at: Optional[datetime] = None

    # State
    health: float = 100.0  # Can be damaged
    active: bool = True

    # Workers
    workers: Set[str] = field(default_factory=set)  # Agent IDs working here
    max_workers: int = 4

    # Production tracking
    production_accumulator: float = 0.0
    inventory: Dict[str, int] = field(default_factory=dict)

    # Benefits
    cost: BuildingCost = field(default_factory=lambda: BuildingCost())
    benefits: BuildingBenefits = field(default_factory=lambda: BuildingBenefits())

    def advance_construction(self, labor_amount: float = 1.0, builder_skill: float = 1.0):
        """Advance construction progress"""
        if self.is_complete:
            return

        # Skill improves construction speed
        progress_delta = (labor_amount / self.cost.labor_time) * (0.5 + 0.5 * builder_skill)
        self.construction_progress = min(1.0, self.construction_progress + progress_delta)

        if self.construction_progress >= 1.0:
            self.complete_construction()

    def complete_construction(self):
        """Mark building as complete"""
        self.is_complete = True
        self.construction_progress = 1.0
        self.constructed_at = datetime.now()

    def add_worker(self, agent_id: str) -> bool:
        """Add worker to building"""
        if len(self.workers) >= self.max_workers:
            return False
        self.workers.add(agent_id)
        return True

    def remove_worker(self, agent_id: str):
        """Remove worker from building"""
        self.workers.discard(agent_id)

    def produce(self, delta_time: float = 1.0):
        """Produce items if applicable"""
        if not self.is_complete or not self.active:
            return

        if self.benefits.produces_item and self.benefits.production_rate > 0:
            # Production scaled by number of workers
            worker_multiplier = 0.5 + 0.5 * len(self.workers) / max(1, self.max_workers)
            production = self.benefits.production_rate * delta_time * worker_multiplier

            self.production_accumulator += production

            # Convert to full items
            if self.production_accumulator >= 1.0:
                items_produced = int(self.production_accumulator)
                self.production_accumulator -= items_produced

                item_name = self.benefits.produces_item
                self.inventory[item_name] = self.inventory.get(item_name, 0) + items_produced

    def take_damage(self, amount: float):
        """Damage the building"""
        self.health = max(0.0, self.health - amount)
        if self.health <= 0:
            self.active = False

    def repair(self, amount: float):
        """Repair the building"""
        self.health = min(100.0, self.health + amount)
        if self.health > 0:
            self.active = True

    def get_total_cost(self) -> Dict[str, float]:
        """Get total resource cost"""
        return {
            'wood': self.cost.wood,
            'stone': self.cost.stone,
            'metal': self.cost.metal,
            'coins': self.cost.coins,
        }

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'type': self.building_type.value,
            'name': self.name,
            'location': {'x': self.location.x, 'y': self.location.y},
            'owner_id': self.owner_id,
            'construction_progress': self.construction_progress,
            'is_complete': self.is_complete,
            'health': self.health,
            'active': self.active,
            'workers': list(self.workers),
            'inventory': self.inventory,
            'benefits': {
                'produces': self.benefits.produces_item,
                'production_rate': self.benefits.production_rate,
                'wealth_generation': self.benefits.wealth_generation,
                'happiness_bonus': self.benefits.happiness_bonus,
                'defense_value': self.benefits.defense_value,
            }
        }


class BuildingManager:
    """Manages all buildings in the world"""

    def __init__(self):
        self.buildings: Dict[str, Building] = {}
        # Index: location -> building IDs
        self.location_index: Dict[Tuple[int, int], Set[str]] = {}
        # Index: owner -> building IDs
        self.owner_index: Dict[str, Set[str]] = {}

    def create_building(
        self,
        building_type: BuildingType,
        location: Position,
        owner_id: Optional[str] = None,
        name: Optional[str] = None
    ) -> Building:
        """Create a new building"""
        building_id = str(uuid.uuid4())

        # Get template
        cost, benefits = BUILDING_TEMPLATES.get(
            building_type,
            (BuildingCost(), BuildingBenefits())
        )

        # Generate name if not provided
        if not name:
            name = f"{building_type.value.replace('_', ' ').title()}"

        building = Building(
            id=building_id,
            building_type=building_type,
            name=name,
            location=location,
            owner_id=owner_id,
            cost=cost,
            benefits=benefits
        )

        self.buildings[building_id] = building

        # Update indices
        loc_key = (int(location.x), int(location.y))
        if loc_key not in self.location_index:
            self.location_index[loc_key] = set()
        self.location_index[loc_key].add(building_id)

        if owner_id:
            if owner_id not in self.owner_index:
                self.owner_index[owner_id] = set()
            self.owner_index[owner_id].add(building_id)

        return building

    def get_building(self, building_id: str) -> Optional[Building]:
        """Get building by ID"""
        return self.buildings.get(building_id)

    def get_buildings_at(self, location: Position, radius: float = 1.0) -> List[Building]:
        """Get buildings near location"""
        buildings = []
        x, y = int(location.x), int(location.y)

        for dx in range(-int(radius), int(radius) + 1):
            for dy in range(-int(radius), int(radius) + 1):
                loc_key = (x + dx, y + dy)
                if loc_key in self.location_index:
                    for building_id in self.location_index[loc_key]:
                        if building_id in self.buildings:
                            building = self.buildings[building_id]
                            if building.location.distance_to(location) <= radius:
                                buildings.append(building)

        return buildings

    def get_agent_buildings(self, agent_id: str) -> List[Building]:
        """Get all buildings owned by agent"""
        building_ids = self.owner_index.get(agent_id, set())
        return [self.buildings[bid] for bid in building_ids if bid in self.buildings]

    def update_buildings(self, delta_time: float = 1.0):
        """Update all buildings (production, etc.)"""
        for building in self.buildings.values():
            if building.is_complete and building.active:
                building.produce(delta_time)

    def can_agent_build(
        self,
        agent: Agent,
        building_type: BuildingType
    ) -> Tuple[bool, str]:
        """Check if agent can build this building type"""
        cost, benefits = BUILDING_TEMPLATES.get(
            building_type,
            (BuildingCost(), BuildingBenefits())
        )

        # Check resources
        if not agent.inventory.has_item('wood', cost.wood):
            return False, f"Need {cost.wood} wood"
        if not agent.inventory.has_item('stone', cost.stone):
            return False, f"Need {cost.stone} stone"
        if not agent.inventory.has_item('metal', cost.metal):
            return False, f"Need {cost.metal} metal"
        if agent.wealth < cost.coins:
            return False, f"Need {cost.coins} coins"

        # Check skill if required
        if cost.required_skill:
            skill_level = agent.skills.get_skill(cost.required_skill)
            if skill_level < cost.min_skill_level:
                return False, f"Need {cost.required_skill} skill level {cost.min_skill_level}"

        return True, "Can build"

    def start_construction(
        self,
        agent: Agent,
        building_type: BuildingType,
        location: Position
    ) -> Tuple[Optional[Building], str]:
        """Agent starts constructing a building"""
        # Check if can build
        can_build, message = self.can_agent_build(agent, building_type)
        if not can_build:
            return None, message

        # Deduct resources
        cost, _ = BUILDING_TEMPLATES[building_type]
        agent.inventory.remove_item('wood', cost.wood)
        agent.inventory.remove_item('stone', cost.stone)
        agent.inventory.remove_item('metal', cost.metal)
        agent.wealth -= cost.coins

        # Create building
        building = self.create_building(
            building_type,
            location,
            owner_id=agent.id
        )

        return building, "Construction started"

    def get_statistics(self) -> Dict:
        """Get building statistics"""
        total = len(self.buildings)
        complete = sum(1 for b in self.buildings.values() if b.is_complete)
        in_progress = total - complete

        by_type = {}
        for building in self.buildings.values():
            type_name = building.building_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        return {
            'total_buildings': total,
            'complete': complete,
            'in_progress': in_progress,
            'by_type': by_type
        }
