"""
Agriculture System - From Hunter-Gatherer to Farmer

Enables the agricultural revolution:
- Crop farming (plant → grow → harvest)
- Animal domestication (hunt → raise → breed)
- Seasonal cycles affect growth
- Food surplus enables population growth
- Irrigation and farming techniques

Philosophy: Agriculture is THE foundation of civilization.
Without farming, no cities, no specialization, no progress.
"""

import random
from engine.ids import new_uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum


class Season(Enum):
    """Four seasons affecting crop growth"""
    SPRING = "spring"  # Best for planting
    SUMMER = "summer"  # Active growth
    AUTUMN = "autumn"  # Harvest time
    WINTER = "winter"  # Poor growth, survival mode


class CropType(Enum):
    """Types of crops agents can grow"""
    WHEAT = "wheat"
    CORN = "corn"
    RICE = "rice"
    VEGETABLES = "vegetables"
    FRUIT = "fruit"
    BEANS = "beans"


class AnimalType(Enum):
    """Domesticatable animals"""
    CHICKEN = "chicken"
    PIG = "pig"
    COW = "cow"
    SHEEP = "sheep"
    GOAT = "goat"
    HORSE = "horse"


@dataclass
class CropField:
    """A planted crop field"""
    id: str
    crop_type: CropType
    owner_id: str
    location: Tuple[float, float]

    # Growth tracking
    planted_at: int  # Tick planted
    growth_progress: float = 0.0  # 0-1
    maturity_time: int = 100  # Ticks to mature

    # Yield
    expected_yield: int = 50  # Base food produced
    actual_yield: int = 0  # Determined at harvest

    # Conditions
    has_water: bool = False  # Irrigation
    soil_quality: float = 1.0  # 0.5-1.5 multiplier
    disease_infected: bool = False

    # Status
    harvested: bool = False


@dataclass
class DomesticatedAnimal:
    """A domesticated animal"""
    id: str
    animal_type: AnimalType
    owner_id: str
    age: int = 0  # Ticks alive

    # Production
    produces_food: bool = True  # Can be slaughtered
    produces_material: Optional[str] = None  # wool, leather, milk
    production_rate: int = 50  # Ticks between production
    last_production: int = 0

    # Breeding
    can_breed: bool = False
    breeding_age: int = 200  # Ticks until can breed

    # Health
    health: float = 1.0
    fed: bool = True
    disease_chance: float = 0.05


@dataclass
class Farm:
    """An agent's farm (multiple fields + animals)"""
    id: str
    owner_id: str
    owner_name: str
    location: Tuple[float, float]

    # Farming infrastructure
    fields: List[str] = field(default_factory=list)  # CropField IDs
    animals: List[str] = field(default_factory=list)  # Animal IDs
    has_irrigation: bool = False
    has_barn: bool = False
    has_fence: bool = False

    # Statistics
    total_harvests: int = 0
    total_food_produced: int = 0
    farming_skill: float = 0.5  # Improves with experience


class AgricultureManager:
    """
    Manages all agriculture in the simulation.

    Key mechanics:
    - Crops take time to grow, affected by seasons
    - Animals produce food/materials over time
    - Farming skill improves with practice
    - Food surplus enables population growth
    """

    def __init__(self):
        self.crop_fields: Dict[str, CropField] = {}
        self.domesticated_animals: Dict[str, DomesticatedAnimal] = {}
        self.farms: Dict[str, Farm] = {}

        # Season tracking
        self.current_season: Season = Season.SPRING
        self.season_length: int = 250  # Ticks per season
        self.ticks_in_season: int = 0

        # Discovery tracking
        self.crops_discovered: Set[CropType] = set()
        self.animals_domesticated: Set[AnimalType] = set()

        # Statistics
        self.total_farms: int = 0
        self.total_crops_planted: int = 0
        self.total_crops_harvested: int = 0
        self.total_food_from_agriculture: int = 0
        self.total_animals_domesticated: int = 0

    # ===== SEASON SYSTEM =====

    def update_season(self, current_tick: int):
        """Update seasonal cycle"""
        self.ticks_in_season += 1

        if self.ticks_in_season >= self.season_length:
            # Advance to next season
            self.ticks_in_season = 0

            seasons = [Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER]
            current_index = seasons.index(self.current_season)
            next_index = (current_index + 1) % 4

            self.current_season = seasons[next_index]

            return True  # Season changed

        return False

    def get_season_growth_multiplier(self) -> float:
        """Get crop growth rate multiplier for current season"""
        multipliers = {
            Season.SPRING: 1.2,  # Fast growth
            Season.SUMMER: 1.5,  # Fastest growth
            Season.AUTUMN: 0.8,  # Slow growth
            Season.WINTER: 0.3,  # Very slow
        }

        return multipliers[self.current_season]

    # ===== FARMING OPERATIONS =====

    def create_farm(
        self,
        owner_id: str,
        owner_name: str,
        location: Tuple[float, float]
    ) -> Farm:
        """Agent creates a farm"""
        farm_id = str(new_uuid())

        farm = Farm(
            id=farm_id,
            owner_id=owner_id,
            owner_name=owner_name,
            location=location
        )

        self.farms[farm_id] = farm
        self.total_farms += 1

        return farm

    def get_agent_farm(self, agent_id: str) -> Optional[Farm]:
        """Get agent's farm if they have one"""
        for farm in self.farms.values():
            if farm.owner_id == agent_id:
                return farm
        return None

    def plant_crop(
        self,
        agent_id: str,
        crop_type: CropType,
        location: Tuple[float, float],
        current_tick: int
    ) -> Optional[CropField]:
        """Agent plants a crop field"""

        # Get or create farm
        farm = self.get_agent_farm(agent_id)
        if not farm:
            # Create farm automatically
            farm = self.create_farm(agent_id, f"Agent{agent_id[:8]}", location)

        field_id = str(new_uuid())

        # Determine maturity time based on crop
        maturity_times = {
            CropType.WHEAT: 80,
            CropType.CORN: 100,
            CropType.RICE: 120,
            CropType.VEGETABLES: 60,
            CropType.FRUIT: 150,
            CropType.BEANS: 70,
        }

        # Expected yield
        yields = {
            CropType.WHEAT: 60,
            CropType.CORN: 80,
            CropType.RICE: 70,
            CropType.VEGETABLES: 40,
            CropType.FRUIT: 50,
            CropType.BEANS: 45,
        }

        field = CropField(
            id=field_id,
            crop_type=crop_type,
            owner_id=agent_id,
            location=location,
            planted_at=current_tick,
            maturity_time=maturity_times.get(crop_type, 100),
            expected_yield=yields.get(crop_type, 50),
            has_water=farm.has_irrigation,
            soil_quality=random.uniform(0.8, 1.2)
        )

        self.crop_fields[field_id] = field
        farm.fields.append(field_id)

        # Track discovery
        if crop_type not in self.crops_discovered:
            self.crops_discovered.add(crop_type)

        self.total_crops_planted += 1

        return field

    def update_crops(self, current_tick: int):
        """Update all growing crops"""
        season_multiplier = self.get_season_growth_multiplier()

        for field in self.crop_fields.values():
            if field.harvested:
                continue

            # Calculate growth rate
            base_growth = 1.0 / field.maturity_time

            # Modifiers
            water_bonus = 1.3 if field.has_water else 1.0
            soil_modifier = field.soil_quality
            disease_penalty = 0.5 if field.disease_infected else 1.0

            growth_rate = base_growth * season_multiplier * water_bonus * soil_modifier * disease_penalty

            field.growth_progress = min(1.0, field.growth_progress + growth_rate)

            # Random disease chance
            if random.random() < 0.001:  # 0.1% per tick
                field.disease_infected = True

    def can_harvest_field(self, field_id: str) -> bool:
        """Check if field is ready to harvest"""
        if field_id not in self.crop_fields:
            return False

        field = self.crop_fields[field_id]
        return field.growth_progress >= 1.0 and not field.harvested

    def harvest_crop(
        self,
        field_id: str,
        harvester_id: str
    ) -> int:
        """Harvest a crop field, returns food yield"""
        if field_id not in self.crop_fields:
            return 0

        field = self.crop_fields[field_id]

        if field.harvested or field.growth_progress < 1.0:
            return 0

        # Calculate actual yield
        base_yield = field.expected_yield

        # Farming skill bonus (from farm owner)
        farm = self.get_agent_farm(field.owner_id)
        skill_bonus = 1.0 + (farm.farming_skill * 0.5) if farm else 1.0

        # Season bonus (best in autumn)
        season_bonus = 1.3 if self.current_season == Season.AUTUMN else 1.0

        # Apply modifiers
        actual_yield = int(base_yield * skill_bonus * season_bonus * field.soil_quality)

        # Disease reduces yield significantly
        if field.disease_infected:
            actual_yield = int(actual_yield * 0.3)

        field.actual_yield = actual_yield
        field.harvested = True

        # Update farm statistics
        if farm:
            farm.total_harvests += 1
            farm.total_food_produced += actual_yield
            farm.farming_skill = min(1.0, farm.farming_skill + 0.01)  # Skill improves

        self.total_crops_harvested += 1
        self.total_food_from_agriculture += actual_yield

        return actual_yield

    # ===== ANIMAL DOMESTICATION =====

    def domesticate_animal(
        self,
        agent_id: str,
        animal_type: AnimalType,
        current_tick: int
    ) -> Optional[DomesticatedAnimal]:
        """Agent domesticates a wild animal"""

        # Get or create farm
        farm = self.get_agent_farm(agent_id)
        if not farm:
            return None  # Need farm first

        animal_id = str(new_uuid())

        # Animal properties
        properties = {
            AnimalType.CHICKEN: {'material': 'eggs', 'rate': 30, 'breed_age': 100},
            AnimalType.PIG: {'material': 'meat', 'rate': 200, 'breed_age': 150},
            AnimalType.COW: {'material': 'milk', 'rate': 50, 'breed_age': 200},
            AnimalType.SHEEP: {'material': 'wool', 'rate': 100, 'breed_age': 180},
            AnimalType.GOAT: {'material': 'milk', 'rate': 60, 'breed_age': 150},
            AnimalType.HORSE: {'material': None, 'rate': 0, 'breed_age': 250},
        }

        props = properties.get(animal_type, {'material': None, 'rate': 50, 'breed_age': 200})

        animal = DomesticatedAnimal(
            id=animal_id,
            animal_type=animal_type,
            owner_id=agent_id,
            produces_material=props['material'],
            production_rate=props['rate'],
            breeding_age=props['breed_age'],
            last_production=current_tick
        )

        self.domesticated_animals[animal_id] = animal
        farm.animals.append(animal_id)

        # Track discovery
        if animal_type not in self.animals_domesticated:
            self.animals_domesticated.add(animal_type)

        self.total_animals_domesticated += 1

        return animal

    def update_animals(self, current_tick: int):
        """Update all domesticated animals"""
        for animal in self.domesticated_animals.values():
            animal.age += 1

            # Can breed when old enough
            if animal.age >= animal.breeding_age:
                animal.can_breed = True

            # Produce materials
            if animal.produces_material and animal.fed:
                if current_tick - animal.last_production >= animal.production_rate:
                    animal.last_production = current_tick
                    # Production happens (handled externally)

            # Random disease
            if random.random() < animal.disease_chance:
                animal.health = max(0.0, animal.health - 0.1)

            # Die if health reaches 0
            if animal.health <= 0:
                # Animal dies (handled externally)
                pass

    def breed_animals(
        self,
        animal1_id: str,
        animal2_id: str,
        current_tick: int
    ) -> Optional[DomesticatedAnimal]:
        """Breed two animals of the same type"""
        if animal1_id not in self.domesticated_animals or animal2_id not in self.domesticated_animals:
            return None

        animal1 = self.domesticated_animals[animal1_id]
        animal2 = self.domesticated_animals[animal2_id]

        # Must be same type and breedable
        if animal1.animal_type != animal2.animal_type:
            return None

        if not (animal1.can_breed and animal2.can_breed):
            return None

        # Create offspring
        offspring = self.domesticate_animal(animal1.owner_id, animal1.animal_type, current_tick)

        return offspring

    # ===== QUERIES =====

    def get_agent_crops(self, agent_id: str) -> List[CropField]:
        """Get all crop fields owned by agent"""
        return [f for f in self.crop_fields.values() if f.owner_id == agent_id]

    def get_agent_animals(self, agent_id: str) -> List[DomesticatedAnimal]:
        """Get all animals owned by agent"""
        return [a for a in self.domesticated_animals.values() if a.owner_id == agent_id]

    def get_harvestable_crops(self, agent_id: str) -> List[CropField]:
        """Get agent's crops ready to harvest"""
        return [f for f in self.get_agent_crops(agent_id)
                if f.growth_progress >= 1.0 and not f.harvested]

    def get_statistics(self) -> Dict:
        """Get agriculture statistics"""

        active_fields = sum(1 for f in self.crop_fields.values() if not f.harvested)
        active_animals = len(self.domesticated_animals)

        return {
            'current_season': self.current_season.value,
            'total_farms': self.total_farms,
            'active_crop_fields': active_fields,
            'total_crops_planted': self.total_crops_planted,
            'total_crops_harvested': self.total_crops_harvested,
            'total_food_produced': self.total_food_from_agriculture,
            'active_animals': active_animals,
            'total_animals_domesticated': self.total_animals_domesticated,
            'crops_discovered': [c.value for c in self.crops_discovered],
            'animals_domesticated_types': [a.value for a in self.animals_domesticated],
        }
