"""
Energy Systems - From Fire to Nuclear Power

Implements:
- Energy sources progression (wood → coal → oil → electricity → nuclear)
- Power generation and consumption
- Energy storage and distribution
- Power plants and generators
- Energy efficiency and technology unlocks

Philosophy: Energy is the foundation of civilization advancement.
From cooking fires to nuclear reactors, energy drives progress.
"""

import random
from engine.ids import new_uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class EnergyType(Enum):
    """Types of energy sources"""
    # Primitive
    MANUAL = "manual"  # Human/animal labor
    FIRE = "fire"  # Wood burning

    # Industrial Age
    COAL = "coal"  # Coal burning
    OIL = "oil"  # Petroleum
    NATURAL_GAS = "natural_gas"  # Methane

    # Renewable
    WATER = "water"  # Hydroelectric
    WIND = "wind"  # Wind turbines
    SOLAR = "solar"  # Solar panels
    GEOTHERMAL = "geothermal"  # Earth's heat

    # Advanced
    ELECTRICITY = "electricity"  # Grid power
    NUCLEAR = "nuclear"  # Fission
    FUSION = "fusion"  # Future tech


class PowerPlantType(Enum):
    """Types of power generation facilities"""
    FIRE_PIT = "fire_pit"  # Basic fire
    FURNACE = "furnace"  # Coal furnace
    STEAM_ENGINE = "steam_engine"  # Steam power
    GENERATOR = "generator"  # Electric generator
    POWER_PLANT = "power_plant"  # Coal/oil plant
    HYDRO_DAM = "hydro_dam"  # Hydroelectric dam
    WIND_FARM = "wind_farm"  # Wind turbines
    SOLAR_FARM = "solar_farm"  # Solar panels
    NUCLEAR_REACTOR = "nuclear_reactor"  # Nuclear fission


@dataclass
class EnergySource:
    """An energy resource that can be harvested/used"""
    id: str
    energy_type: EnergyType
    name: str

    # Energy properties
    energy_density: float  # Energy per unit (kJ/kg or equivalent)
    burn_rate: float = 1.0  # How fast it's consumed
    efficiency: float = 0.5  # 0-1, how much energy is actually usable

    # Availability
    discovered: bool = False
    discoverer_id: Optional[str] = None
    discovered_tick: int = 0

    # Environmental impact
    pollution: float = 0.0  # 0-1, how polluting
    renewable: bool = False


@dataclass
class PowerPlant:
    """A facility that generates power"""
    id: str
    name: str
    plant_type: PowerPlantType

    # Location
    location: Tuple[float, float]
    owner_id: str

    # Construction
    built_tick: int
    builder_id: str

    # Power generation
    fuel_type: EnergyType  # What it burns/uses
    max_output: float = 100.0  # Maximum power output (kW)
    current_output: float = 0.0  # Current output
    efficiency: float = 0.5  # 0-1

    # Fuel
    fuel_stored: float = 0.0
    fuel_consumption_rate: float = 1.0  # Fuel per tick

    # Status
    operational: bool = True
    last_maintenance: int = 0


@dataclass
class EnergyGrid:
    """An electricity distribution network"""
    id: str
    name: str

    # Coverage area
    center: Tuple[float, float]
    radius: float = 50.0

    # Power
    total_generation: float = 0.0  # Total power generated (kW)
    total_consumption: float = 0.0  # Total power used (kW)
    storage_capacity: float = 1000.0  # Battery storage (kWh)
    stored_energy: float = 0.0

    # Connected infrastructure
    power_plants: Set[str] = field(default_factory=set)  # Plant IDs
    consumers: Set[str] = field(default_factory=set)  # Building/agent IDs

    # Status
    blackout: bool = False


class EnergyManager:
    """
    Manages energy sources, power generation, and distribution.

    Key mechanics:
    - Progressive energy tech discovery (fire → coal → oil → nuclear)
    - Power plants require fuel and maintenance
    - Electricity grids distribute power to consumers
    - Energy efficiency improves with technology
    """

    def __init__(self):
        self.energy_sources: Dict[str, EnergySource] = {}
        self.power_plants: Dict[str, PowerPlant] = {}
        self.energy_grids: Dict[str, EnergyGrid] = {}

        # Discovery tracking
        self.discovered_energy_types: Set[EnergyType] = set()

        # Statistics
        self.total_power_plants_built: int = 0
        self.total_energy_generated: float = 0.0
        self.total_energy_consumed: float = 0.0

        # Initialize energy sources
        self._init_energy_sources()

    # ===== ENERGY SOURCE INITIALIZATION =====

    def _init_energy_sources(self):
        """Initialize all energy source types"""

        sources_data = [
            # Primitive (always available)
            (EnergyType.MANUAL, "Manual Labor", 0.1, 1.0, 0.3, True, 0.0, True),
            (EnergyType.FIRE, "Wood Fire", 15.0, 1.0, 0.2, True, 0.2, True),

            # Fossil Fuels (discovered through mining/exploration)
            (EnergyType.COAL, "Coal", 24.0, 1.0, 0.4, False, 0.8, False),
            (EnergyType.OIL, "Petroleum", 42.0, 1.0, 0.5, False, 0.9, False),
            (EnergyType.NATURAL_GAS, "Natural Gas", 38.0, 1.0, 0.6, False, 0.6, False),

            # Renewable (discovered through research)
            (EnergyType.WATER, "Hydroelectric", 1000.0, 0.0, 0.9, False, 0.1, True),
            (EnergyType.WIND, "Wind Power", 800.0, 0.0, 0.4, False, 0.0, True),
            (EnergyType.SOLAR, "Solar Power", 600.0, 0.0, 0.2, False, 0.0, True),

            # Advanced (late-game)
            (EnergyType.NUCLEAR, "Nuclear Fission", 80000.0, 0.01, 0.33, False, 0.4, False),
            (EnergyType.FUSION, "Nuclear Fusion", 340000.0, 0.001, 0.5, False, 0.0, True),
        ]

        for energy_type, name, density, burn_rate, efficiency, discovered, pollution, renewable in sources_data:
            source_id = str(new_uuid())
            source = EnergySource(
                id=source_id,
                energy_type=energy_type,
                name=name,
                energy_density=density,
                burn_rate=burn_rate,
                efficiency=efficiency,
                discovered=discovered,
                pollution=pollution,
                renewable=renewable
            )
            self.energy_sources[energy_type.value] = source

            if discovered:
                self.discovered_energy_types.add(energy_type)

    # ===== ENERGY DISCOVERY =====

    def discover_energy_source(
        self,
        energy_type: EnergyType,
        discoverer_id: str,
        current_tick: int
    ) -> Optional[EnergySource]:
        """Agent discovers a new energy source"""

        source = self.energy_sources.get(energy_type.value)
        if not source:
            return None

        if source.discovered:
            return source  # Already discovered

        # Discovery successful!
        source.discovered = True
        source.discoverer_id = discoverer_id
        source.discovered_tick = current_tick

        self.discovered_energy_types.add(energy_type)

        return source

    # ===== POWER PLANT CONSTRUCTION =====

    def build_power_plant(
        self,
        plant_type: PowerPlantType,
        fuel_type: EnergyType,
        location: Tuple[float, float],
        owner_id: str,
        builder_id: str,
        current_tick: int
    ) -> Optional[PowerPlant]:
        """Build a power generation facility"""

        # Check if fuel type is discovered
        if fuel_type not in self.discovered_energy_types:
            return None

        plant_id = str(new_uuid())

        # Get plant specifications
        specs = self._get_plant_specs(plant_type)

        plant = PowerPlant(
            id=plant_id,
            name=f"{plant_type.value.replace('_', ' ').title()}",
            plant_type=plant_type,
            location=location,
            owner_id=owner_id,
            built_tick=current_tick,
            builder_id=builder_id,
            fuel_type=fuel_type,
            max_output=specs['max_output'],
            efficiency=specs['efficiency'],
            fuel_consumption_rate=specs['fuel_consumption']
        )

        self.power_plants[plant_id] = plant
        self.total_power_plants_built += 1

        return plant

    def _get_plant_specs(self, plant_type: PowerPlantType) -> Dict:
        """Get power plant specifications"""

        specs = {
            PowerPlantType.FIRE_PIT: {
                'max_output': 10.0,
                'efficiency': 0.1,
                'fuel_consumption': 2.0
            },
            PowerPlantType.FURNACE: {
                'max_output': 50.0,
                'efficiency': 0.3,
                'fuel_consumption': 1.5
            },
            PowerPlantType.STEAM_ENGINE: {
                'max_output': 200.0,
                'efficiency': 0.2,
                'fuel_consumption': 3.0
            },
            PowerPlantType.GENERATOR: {
                'max_output': 500.0,
                'efficiency': 0.6,
                'fuel_consumption': 2.0
            },
            PowerPlantType.POWER_PLANT: {
                'max_output': 2000.0,
                'efficiency': 0.4,
                'fuel_consumption': 5.0
            },
            PowerPlantType.HYDRO_DAM: {
                'max_output': 3000.0,
                'efficiency': 0.9,
                'fuel_consumption': 0.0  # No fuel needed
            },
            PowerPlantType.WIND_FARM: {
                'max_output': 1000.0,
                'efficiency': 0.4,
                'fuel_consumption': 0.0
            },
            PowerPlantType.SOLAR_FARM: {
                'max_output': 800.0,
                'efficiency': 0.2,
                'fuel_consumption': 0.0
            },
            PowerPlantType.NUCLEAR_REACTOR: {
                'max_output': 5000.0,
                'efficiency': 0.33,
                'fuel_consumption': 0.1
            }
        }

        return specs.get(plant_type, {'max_output': 100.0, 'efficiency': 0.5, 'fuel_consumption': 1.0})

    # ===== POWER GENERATION =====

    def operate_power_plant(
        self,
        plant_id: str,
        fuel_amount: float
    ) -> float:
        """Operate power plant, consume fuel, return energy generated"""

        if plant_id not in self.power_plants:
            return 0.0

        plant = self.power_plants[plant_id]

        if not plant.operational:
            return 0.0

        # Add fuel to plant
        plant.fuel_stored += fuel_amount

        # Calculate energy generation
        fuel_consumed = min(plant.fuel_stored, plant.fuel_consumption_rate)
        plant.fuel_stored -= fuel_consumed

        # Get energy source properties
        energy_source = self.energy_sources.get(plant.fuel_type.value)
        if not energy_source:
            return 0.0

        # Calculate power output
        energy_density = energy_source.energy_density
        plant_efficiency = plant.efficiency

        energy_generated = fuel_consumed * energy_density * plant_efficiency

        # Cap at max output
        energy_generated = min(energy_generated, plant.max_output)
        plant.current_output = energy_generated

        self.total_energy_generated += energy_generated

        return energy_generated

    # ===== ELECTRICITY GRID =====

    def create_energy_grid(
        self,
        name: str,
        center: Tuple[float, float],
        radius: float
    ) -> EnergyGrid:
        """Create an electricity distribution grid"""

        grid_id = str(new_uuid())

        grid = EnergyGrid(
            id=grid_id,
            name=name,
            center=center,
            radius=radius
        )

        self.energy_grids[grid_id] = grid

        return grid

    def connect_plant_to_grid(self, plant_id: str, grid_id: str) -> bool:
        """Connect a power plant to an energy grid"""

        if plant_id not in self.power_plants or grid_id not in self.energy_grids:
            return False

        grid = self.energy_grids[grid_id]
        grid.power_plants.add(plant_id)

        return True

    def update_grids(self):
        """Update all energy grids - balance supply and demand"""

        for grid in self.energy_grids.values():
            # Calculate total generation
            total_gen = 0.0
            for plant_id in sorted(grid.power_plants):
                plant = self.power_plants.get(plant_id)
                if plant and plant.operational:
                    total_gen += plant.current_output

            grid.total_generation = total_gen

            # Check if supply meets demand
            if grid.total_generation < grid.total_consumption:
                # Not enough power - potential blackout
                deficit = grid.total_consumption - grid.total_generation

                # Use stored energy if available
                if grid.stored_energy >= deficit:
                    grid.stored_energy -= deficit
                else:
                    # Blackout!
                    grid.blackout = True
            else:
                # Surplus - store excess energy
                surplus = grid.total_generation - grid.total_consumption
                grid.stored_energy = min(grid.storage_capacity, grid.stored_energy + surplus)
                grid.blackout = False

    # ===== QUERIES =====

    def get_discovered_energy_sources(self) -> List[EnergySource]:
        """Get all discovered energy sources"""
        return [s for s in self.energy_sources.values() if s.discovered]

    def get_available_energy_types(self) -> List[EnergyType]:
        """Get list of discovered energy types"""
        return list(self.discovered_energy_types)

    def get_plants_by_owner(self, owner_id: str) -> List[PowerPlant]:
        """Get all power plants owned by agent/faction"""
        return [p for p in self.power_plants.values() if p.owner_id == owner_id]

    def get_statistics(self) -> Dict:
        """Get energy system statistics"""

        total_capacity = sum(p.max_output for p in self.power_plants.values())
        total_current_output = sum(p.current_output for p in self.power_plants.values())
        operational_plants = sum(1 for p in self.power_plants.values() if p.operational)

        # Energy type breakdown
        energy_breakdown = {}
        for plant in self.power_plants.values():
            fuel_type = plant.fuel_type.value
            energy_breakdown[fuel_type] = energy_breakdown.get(fuel_type, 0) + plant.current_output

        return {
            'discovered_energy_types': len(self.discovered_energy_types),
            'total_power_plants': len(self.power_plants),
            'operational_plants': operational_plants,
            'total_capacity_kw': round(total_capacity, 1),
            'current_output_kw': round(total_current_output, 1),
            'capacity_utilization': round((total_current_output / max(1, total_capacity)) * 100, 1),
            'total_energy_generated': round(self.total_energy_generated, 1),
            'total_energy_consumed': round(self.total_energy_consumed, 1),
            'energy_grids': len(self.energy_grids),
            'energy_by_type': energy_breakdown
        }
