"""
Dynamic Building System - TRUE Architectural Freedom

Agents design and build custom structures with NO templates.
Buildings can be anything: homes, workshops, temples, factories, rockets!

Effectiveness is LEARNED through actual use, not predetermined.
Buildings can succeed, fail partially, or catastrophically collapse.

This enables progression from:
- Stone Age: Mud huts, stone shelters
- Bronze Age: Wooden houses, workshops
- Medieval: Castles, cathedrals, mills
- Industrial: Factories, warehouses, rail stations
- Modern: Skyscrapers, power plants, laboratories
- Space Age: Launch pads, satellites, space stations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import random
from engine.ids import new_uuid


# ==============================================================================
# BUILDING CATEGORIES - Organized types for clarity
# ==============================================================================

class BuildingCategory:
    """
    High-level categories for organizing buildings.
    Makes it easy to see what's being built!
    """
    RESIDENTIAL = "Residential"  # Homes, apartments, shelters
    INDUSTRIAL = "Industrial"    # Workshops, factories, forges
    RELIGIOUS = "Religious"      # Temples, churches, shrines
    INFRASTRUCTURE = "Infrastructure"  # Wells, roads, bridges, power
    DEFENSE = "Defense"          # Walls, towers, fortifications
    COMMERCE = "Commerce"        # Markets, banks, trading posts
    EDUCATION = "Education"      # Schools, libraries, research labs
    RECREATION = "Recreation"    # Theaters, arenas, parks
    ADVANCED = "Advanced"        # Rockets, satellites, power plants


# ==============================================================================
# BUILDING PURPOSES - What agents want buildings for
# ==============================================================================

class BuildingPurpose:
    """
    Open-ended purposes for buildings.
    Agents can combine these or invent new ones!
    """
    # Basic needs (RESIDENTIAL)
    SHELTER = "shelter"
    STORAGE = "storage"
    WARMTH = "warmth"

    # Production (INDUSTRIAL)
    CRAFTING = "crafting"
    FOOD_PRODUCTION = "food_production"
    RESOURCE_EXTRACTION = "resource_extraction"
    MANUFACTURING = "manufacturing"

    # Social (RELIGIOUS)
    GATHERING = "gathering"
    WORSHIP = "worship"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"

    # Economic (COMMERCE)
    TRADING = "trading"
    BANKING = "banking"

    # Defense (DEFENSE)
    PROTECTION = "protection"
    SURVEILLANCE = "surveillance"

    # Advanced (ADVANCED)
    RESEARCH = "research"
    ENERGY_GENERATION = "energy_generation"
    TRANSPORTATION = "transportation"
    SPACE_EXPLORATION = "space_exploration"

# Map purposes to categories
PURPOSE_TO_CATEGORY = {
    BuildingPurpose.SHELTER: BuildingCategory.RESIDENTIAL,
    BuildingPurpose.STORAGE: BuildingCategory.RESIDENTIAL,
    BuildingPurpose.WARMTH: BuildingCategory.RESIDENTIAL,

    BuildingPurpose.CRAFTING: BuildingCategory.INDUSTRIAL,
    BuildingPurpose.FOOD_PRODUCTION: BuildingCategory.INDUSTRIAL,
    BuildingPurpose.RESOURCE_EXTRACTION: BuildingCategory.INDUSTRIAL,
    BuildingPurpose.MANUFACTURING: BuildingCategory.INDUSTRIAL,

    BuildingPurpose.WORSHIP: BuildingCategory.RELIGIOUS,
    BuildingPurpose.GATHERING: BuildingCategory.RELIGIOUS,

    BuildingPurpose.TRADING: BuildingCategory.COMMERCE,
    BuildingPurpose.BANKING: BuildingCategory.COMMERCE,

    BuildingPurpose.PROTECTION: BuildingCategory.DEFENSE,
    BuildingPurpose.SURVEILLANCE: BuildingCategory.DEFENSE,

    BuildingPurpose.EDUCATION: BuildingCategory.EDUCATION,
    BuildingPurpose.ENTERTAINMENT: BuildingCategory.RECREATION,

    BuildingPurpose.RESEARCH: BuildingCategory.ADVANCED,
    BuildingPurpose.ENERGY_GENERATION: BuildingCategory.ADVANCED,
    BuildingPurpose.TRANSPORTATION: BuildingCategory.INFRASTRUCTURE,
    BuildingPurpose.SPACE_EXPLORATION: BuildingCategory.ADVANCED,
}


# ==============================================================================
# CONSTRUCTION METHODS
# ==============================================================================

class ConstructionMethod:
    """How agents build"""
    STACK = "stack"  # Pile materials
    FRAME = "frame"  # Build framework
    WEAVE = "weave"  # Interlace
    EXCAVATE = "excavate"  # Dig into ground/mountain
    CAST = "cast"  # Pour/mold
    ASSEMBLE = "assemble"  # Combine components
    WELD = "weld"  # Join with heat/force


# ==============================================================================
# BUILDING DESIGN
# ==============================================================================

@dataclass
class BuildingDesign:
    """
    A custom building design created by an agent.

    NO templates - agents estimate everything!
    """
    id: str
    name: str  # Agent chooses name!
    designer_id: str
    design_date: datetime

    # Purpose (can have multiple!)
    intended_purposes: List[str] = field(default_factory=list)

    # Category (derived from purposes)
    category: str = BuildingCategory.RESIDENTIAL

    # Materials plan
    materials_needed: Dict[str, int] = field(default_factory=dict)
    construction_method: str = ConstructionMethod.STACK

    # Structural estimates (agent's guess!)
    estimated_durability: float = 0.5
    estimated_capacity: int = 5
    estimated_build_time: int = 10

    # Actual performance (unknown until built!)
    actual_durability: Optional[float] = None
    actual_capacity: Optional[int] = None
    actual_shelter_value: Optional[float] = None
    actual_production_bonus: Optional[float] = None

    # Collaboration
    contributors: Set[str] = field(default_factory=set)
    votes_for: int = 0
    votes_against: int = 0

    # Status
    approved: bool = False
    construction_started: bool = False


@dataclass
class Building:
    """
    An actual constructed building.

    Performance is LEARNED through use!
    """
    id: str
    name: str
    design_id: str
    location: Tuple[float, float]

    # Construction
    builder_ids: Set[str] = field(default_factory=set)
    built_date: Optional[datetime] = None
    construction_progress: float = 0.0
    is_complete: bool = False

    # Materials used
    materials_used: Dict[str, int] = field(default_factory=dict)

    # Performance (learned!)
    durability: float = 1.0  # Degrades over time
    quality: Optional[float] = None  # the condition it was made with; repairs restore up to it
    shelter_value: Optional[float] = None
    storage_capacity: Optional[int] = None
    production_bonus: Optional[float] = None
    comfort_value: Optional[float] = None
    defense_value: Optional[float] = None

    # Usage tracking
    occupants: Set[str] = field(default_factory=set)
    workers: Set[str] = field(default_factory=set)
    times_used: int = 0
    maintenance_needed: bool = False

    # History
    events: List[str] = field(default_factory=list)
    repairs: int = 0
    collapsed: bool = False


# ==============================================================================
# DYNAMIC BUILDING SYSTEM
# ==============================================================================

class DynamicBuildingSystem:
    """
    Manages building design, construction, and performance learning.

    NO predetermined building types!
    """

    def __init__(self):
        self.designs: Dict[str, BuildingDesign] = {}
        self.buildings: Dict[str, Building] = {}
        self.construction_failures: List[Dict] = []

    def agent_designs_building(
        self,
        agent_id: str,
        agent_name: str,
        purposes: List[str],
        available_materials: Dict[str, int],
        agent_skill: float = 0.0,
        civilization_era: str = "Stone Age",
        agent_inventory: Optional[Dict[str, int]] = None
    ) -> Optional[BuildingDesign]:
        """
        Agent creates a custom building design.

        They estimate materials based on their skill and knowledge.
        NO templates - pure creativity!

        CRITICAL: Now scales to agent's ACTUAL inventory!
        """

        # Agent proposes a name
        name = self._generate_building_name(agent_name, purposes)

        # Determine building category from purposes
        category = self._determine_category(purposes)

        # Estimate materials needed (skill affects accuracy, era affects scale)
        # CRITICAL FIX: Pass agent's actual inventory to scale requirements realistically
        materials_needed = self._estimate_materials(
            purposes,
            available_materials,
            agent_skill,
            civilization_era,
            agent_inventory  # NEW: Agent's actual inventory
        )
        if not materials_needed:
            # Not enough suitable materials for a viable building. Don't store a
            # design with no materials: start_construction can only reject it.
            return None

        # Choose construction method
        method = self._choose_construction_method(materials_needed, agent_skill)

        # Create design
        design = BuildingDesign(
            id=str(new_uuid()),
            name=name,
            designer_id=agent_id,
            design_date=datetime.now(),
            intended_purposes=purposes,
            category=category,  # Add category!
            materials_needed=materials_needed,
            construction_method=method,
            estimated_durability=0.3 + (agent_skill * 0.5),
            estimated_capacity=max(1, int(5 + agent_skill * 10)),
            estimated_build_time=max(5, int(20 - agent_skill * 10)),
            contributors={agent_id}
        )

        self.designs[design.id] = design
        return design

    def _determine_category(self, purposes: List[str]) -> str:
        """
        Determine building category from its purposes.
        Takes the first recognized purpose's category.
        """
        for purpose in purposes:
            if purpose in PURPOSE_TO_CATEGORY:
                return PURPOSE_TO_CATEGORY[purpose]

        # Default to residential if unknown
        return BuildingCategory.RESIDENTIAL

    def _generate_building_name(self, agent_name: str, purposes: List[str]) -> str:
        """Agent names their building"""

        if "shelter" in purposes and len(purposes) == 1:
            names = [
                f"{agent_name}'s Home",
                f"{agent_name}'s Dwelling",
                f"The {agent_name} House",
                "Cozy Shelter",
                "Simple Home"
            ]
        elif "crafting" in purposes:
            names = [
                f"{agent_name}'s Workshop",
                "The Crafting Hall",
                "Innovation Space",
                "Maker's Den"
            ]
        elif "worship" in purposes:
            names = [
                "Sacred Hall",
                f"Temple of {agent_name}",
                "Meditation Chamber",
                "Holy Place"
            ]
        elif "protection" in purposes:
            names = [
                "The Fortress",
                "Guardian Tower",
                f"{agent_name}'s Stronghold",
                "Defensive Wall"
            ]
        elif "space_exploration" in purposes:
            names = [
                "Launch Facility",
                "Star Reach Platform",
                "Cosmos Gateway",
                f"{agent_name}'s Rocket Launch"
            ]
        else:
            names = [
                f"{agent_name}'s {purposes[0].replace('_', ' ').title()}",
                f"The {purposes[0].replace('_', ' ').title()} Building"
            ]

        return random.choice(names)

    def _estimate_materials(
        self,
        purposes: List[str],
        available: Dict[str, int],
        skill: float,
        civilization_era: str = "Stone Age",
        agent_inventory: Optional[Dict[str, int]] = None
    ) -> Dict[str, int]:
        """
        Agent estimates materials needed.

        Low skill = wild guesses
        High skill = accurate estimates

        CRITICAL FIX: Now scales to agent's ACTUAL inventory!
        Agents design buildings they can ACTUALLY build with what they have.

        SCALES BY CIVILIZATION ERA:
        - Stone Age: Small buildings (15-30 materials)
        - Bronze Age: Medium buildings (30-60 materials)
        - Iron Age: Larger buildings (50-100 materials)
        - Medieval: Substantial buildings (80-150 materials)
        - Industrial: Massive buildings (120-300 materials)
        - Modern: Huge buildings (200-500 materials)
        - Space Age: Gigantic projects (400-1500+ materials)
        """

        materials = {}

        # ========== CRITICAL FIX: REALISTIC MATERIAL ESTIMATION ==========
        # Agents now design buildings based on what they ACTUALLY have!

        # BASE amounts per purpose - REALISTIC material requirements
        # These are MINIMUM amounts needed for a functional building
        base_amounts = {
            "shelter": {"wood": 25, "stone": 15, "plant_fiber": 10, "clay": 5},  # Small hut
            "workshop": {"wood": 40, "stone": 30, "plant_fiber": 15},  # Work area with tools/storage
            "gathering_space": {"wood": 35, "stone": 20, "plant_fiber": 10},  # Community area
            "storage": {"wood": 30, "stone": 25, "clay": 10},  # Secure storage structure
            "crafting": {"wood": 45, "stone": 35, "metal_ore": 10, "plant_fiber": 20},
            "worship": {"stone": 50, "wood": 30, "clay": 20, "plant_fiber": 15},
            "protection": {"stone": 80, "wood": 40, "metal_ore": 20},  # Defensive structure
            "research": {"wood": 50, "stone": 40, "metal_ore": 15, "plant_fiber": 25},
            "manufacturing": {"wood": 60, "stone": 50, "metal_ore": 30, "iron_ore": 20},
            "energy_generation": {"metal_ore": 80, "iron_ore": 60, "coal": 100},
            "space_exploration": {"iron_ore": 200, "advanced_alloy": 150, "rocket_fuel": 300},
        }

        # ERA MULTIPLIERS - Scale building costs for realistic progression
        era_multipliers = {
            "Stone Age": 0.5,      # Simple buildings (20-40 total materials)
            "Bronze Age": 0.8,      # Sturdier buildings (32-64 materials)
            "Iron Age": 1.2,        # Substantial buildings (48-96 materials)
            "Medieval": 1.8,        # Large buildings (72-144 materials)
            "Industrial": 3.0,      # Massive structures (120-240 materials)
            "Modern": 5.0,          # Huge buildings (200-400 materials)
            "Space Age": 8.0,      # Gigantic projects (320-640+ materials)
        }

        # MINIMUM TOTALS per purpose - Buildings below this are not viable
        minimum_totals = {
            "shelter": 15,
            "workshop": 20,
            "gathering_space": 18,
            "storage": 18,
            "crafting": 25,
            "worship": 30,
            "protection": 40,
            "research": 35,
            "manufacturing": 50,
            "energy_generation": 80,
            "space_exploration": 200,
        }

        era_mult = era_multipliers.get(civilization_era, 0.5)

        # STEP 1: Calculate ideal material needs
        ideal_materials = {}
        for purpose in purposes:
            if purpose in base_amounts:
                for material, amount in base_amounts[purpose].items():
                    scaled_amount = int(amount * era_mult)
                    ideal_materials[material] = ideal_materials.get(material, 0) + scaled_amount

        # STEP 2: Filter to only materials available in the world
        ideal_materials = {
            mat: amt for mat, amt in ideal_materials.items()
            if mat in available
        }

        # STEP 3: CRITICAL FIX - Scale to agent's ACTUAL inventory!
        if agent_inventory:
            # Agent can only use materials they actually have
            for material in list(ideal_materials.keys()):
                agent_has = agent_inventory.get(material, 0)

                if agent_has == 0:
                    # Agent doesn't have this material, can't use it
                    del ideal_materials[material]
                else:
                    # Agent has some - use 60-80% of what they have (leave some for survival)
                    usage_percent = 0.6 + (skill * 0.2)  # Higher skill = willing to use more
                    max_can_use = int(agent_has * usage_percent)

                    # Use the minimum of what's needed and what agent can spare
                    ideal_materials[material] = min(ideal_materials[material], max_can_use)

                    # Ensure at least 1 if they have any
                    if ideal_materials[material] == 0 and agent_has > 0:
                        ideal_materials[material] = min(1, agent_has)

        materials = ideal_materials

        # ===== CHECK MINIMUM VIABILITY =====
        # Don't allow buildings that are too small to be functional
        total_materials = sum(materials.values())
        min_required = minimum_totals.get(purposes[0] if purposes else "shelter", 15)

        if total_materials < min_required:
            # Agent doesn't have enough materials - reject building
            # They need to gather more first!
            return None

        # If agent has NO usable materials from the ideal set, improvise with what they have!
        if not materials and agent_inventory:
            # Find materials agent actually has (excluding consumables)
            usable = {mat: amt for mat, amt in agent_inventory.items()
                     if amt > 0 and mat not in ['food', 'water']}

            if usable:
                # Use the material they have the most of
                best_material = max(usable.items(), key=lambda x: x[1])[0]
                agent_has = usable[best_material]

                # Use 50-70% of it
                usage_percent = 0.5 + (skill * 0.2)
                materials[best_material] = max(1, int(agent_has * usage_percent))

        # Fallback: If still no materials and no inventory provided, use old logic
        if not materials and available:
            mat = random.choice(list(available.keys()))
            materials[mat] = max(1, int(random.randint(8, 15) * era_mult))

        return materials

    def _choose_construction_method(
        self,
        materials: Dict[str, int],
        skill: float
    ) -> str:
        """Agent chooses construction method"""

        # Simple methods for beginners
        if skill < 0.3:
            return random.choice([
                ConstructionMethod.STACK,
                ConstructionMethod.STACK  # Repeat = more likely
            ])

        # Advanced methods for skilled builders
        if skill > 0.7:
            return random.choice([
                ConstructionMethod.FRAME,
                ConstructionMethod.CAST,
                ConstructionMethod.ASSEMBLE,
                ConstructionMethod.WELD
            ])

        # Medium skill
        return random.choice([
            ConstructionMethod.STACK,
            ConstructionMethod.FRAME,
            ConstructionMethod.WEAVE
        ])

    def start_construction(
        self,
        design_id: str,
        location: Tuple[float, float],
        builders: Set[str],
        actual_materials: Dict[str, int],
        builder_agent=None
    ) -> Optional[Building]:
        """
        Start building from a design.

        Can fail if design is bad or materials insufficient!
        CRITICAL: Actually consumes materials from builder's inventory!
        """

        design = self.designs.get(design_id)
        if not design or not design.materials_needed:
            return None

        # Check if materials are sufficient
        sufficient = all(
            actual_materials.get(mat, 0) >= needed
            for mat, needed in design.materials_needed.items()
        )

        if not sufficient:
            # Record failure
            self.construction_failures.append({
                "design_id": design_id,
                "reason": "Insufficient materials",
                "date": datetime.now()
            })
            return None

        # CRITICAL FIX: Actually consume materials from builder's inventory!
        if builder_agent and hasattr(builder_agent, 'inventory'):
            consumed = builder_agent.inventory.consume_items(design.materials_needed)
            if not consumed:
                # Failed to consume materials
                self.construction_failures.append({
                    "design_id": design_id,
                    "reason": "Failed to consume materials from inventory",
                    "date": datetime.now()
                })
                return None

        # Create building
        building = Building(
            id=str(new_uuid()),
            name=design.name,
            design_id=design_id,
            location=location,
            builder_ids=builders,
            materials_used=design.materials_needed.copy()  # Record what was used
        )

        self.buildings[building.id] = building
        design.construction_started = True

        return building

    def update_construction(self, building_id: str, labor_applied: float) -> bool:
        """
        Advance construction progress.

        Returns True if building is complete.
        """

        building = self.buildings.get(building_id)
        if not building or building.is_complete:
            return False

        design = self.designs.get(building.design_id)
        if not design:
            return False

        # Progress per labor unit
        progress_per_labor = 1.0 / design.estimated_build_time

        building.construction_progress += labor_applied * progress_per_labor

        # Check for completion
        if building.construction_progress >= 1.0:
            building.is_complete = True
            building.built_date = datetime.now()
            clock = getattr(self, 'time', None)
            building.built_tick = clock.current_tick if clock is not None else None

            # Determine actual performance through testing!
            self._test_building_performance(building, design)

            return True

        return False

    def _test_building_performance(self, building: Building, design: BuildingDesign):
        """
        Test building to discover actual performance.

        This is where buildings can FAIL spectacularly!
        """

        # Check structural integrity
        structure_roll = random.random()

        # Materials affect durability
        has_stone = any("stone" in mat for mat in building.materials_used.keys())
        has_metal = any("metal" in mat for mat in building.materials_used.keys())

        if has_metal:
            durability_base = 0.9
        elif has_stone:
            durability_base = 0.7
        else:
            durability_base = 0.5

        building.durability = durability_base + random.uniform(-0.2, 0.1)
        building.quality = building.durability

        # CATASTROPHIC FAILURE - building collapses!
        # REDUCED from 10% to 1% - agents are learning!
        if structure_roll < 0.01:
            building.collapsed = True
            building.durability = 0.0
            building.events.append("COLLAPSED during construction!")
            return

        # Test each intended purpose
        for purpose in design.intended_purposes:
            self._test_purpose_effectiveness(building, purpose, design)

        # Record completion
        # In sim time (built_date is the wall clock the server ran at)
        tick = getattr(building, 'built_tick', None)
        building.events.append(f"Completed on day {tick // 144 + 1}, {tick // 6 % 24:02d}:00" if tick is not None
                               else "Completed")

    def _test_purpose_effectiveness(
        self,
        building: Building,
        purpose: str,
        design: BuildingDesign
    ):
        """Test how well building serves its purpose"""

        # Base effectiveness: 50%
        effectiveness = 0.5

        # Materials matter
        materials = building.materials_used

        if purpose == BuildingPurpose.SHELTER:
            # More/better materials = better shelter
            total_materials = sum(materials.values())
            building.shelter_value = min(1.0, 0.3 + (total_materials / 50))

        elif purpose == BuildingPurpose.STORAGE:
            # Volume = capacity
            total_materials = sum(materials.values())
            building.storage_capacity = max(5, total_materials)

        elif purpose == BuildingPurpose.CRAFTING:
            # Production bonus from workspace
            building.production_bonus = 0.1 + random.uniform(0.0, 0.3)

        elif purpose == BuildingPurpose.PROTECTION:
            # Defense from thick walls
            stone_amount = sum(amt for mat, amt in materials.items() if "stone" in mat)
            building.defense_value = min(1.0, stone_amount / 100)

        elif purpose == BuildingPurpose.SPACE_EXPLORATION:
            # Rocket needs SPECIFIC materials and design
            has_fuel = any("fuel" in mat for mat in materials.keys())
            has_metal = any("metal" in mat for mat in materials.keys())

            if has_fuel and has_metal:
                # Can launch! (but might fail)
                building.production_bonus = 0.0  # Used for launch capability
                building.events.append("ROCKET CAPABLE!")
            else:
                building.events.append("Rocket design incomplete - missing components")

    def standing_building_near(self, x: float, y: float, radius: float) -> Optional[Building]:
        """The sturdiest finished, standing building within radius of (x, y), if any."""
        best = None
        for b in self.buildings.values():
            if b.is_complete and not b.collapsed:
                bx, by = b.location
                if ((x - bx) ** 2 + (y - by) ** 2) ** 0.5 < radius:
                    if best is None or b.durability > best.durability:
                        best = b
        return best

    def collapse_building(self, building_id: str, reason: str):
        """Mark a building as collapsed (it stays in the record but no longer stands)."""
        building = self.buildings.get(building_id)
        if building and not building.collapsed:
            building.collapsed = True
            building.durability = 0.0
            building.events.append(reason)

    def use_building(self, building_id: str, agent_id: str, purpose: str) -> Dict:
        """
        Agent uses building for a purpose.

        Buildings get better with use (or worse if poorly designed).
        """

        building = self.buildings.get(building_id)
        if not building or not building.is_complete:
            return {"success": False, "reason": "Building not ready"}

        if building.collapsed:
            return {"success": False, "reason": "Building has collapsed!"}

        building.times_used += 1
        building.occupants.add(agent_id)

        # Degrade durability
        building.durability -= 0.001
        if building.durability < 0.5:
            building.maintenance_needed = True

        # Catastrophic failure during use!
        if building.durability < 0.2 and random.random() < 0.05:
            building.collapsed = True
            building.events.append(f"COLLAPSED while {agent_id} was using it!")
            return {
                "success": False,
                "reason": "Building collapsed!",
                "injury": True
            }

        # Return benefits based on purpose
        benefits = {}
        if purpose == BuildingPurpose.SHELTER and building.shelter_value:
            benefits["shelter"] = building.shelter_value

        if purpose == BuildingPurpose.CRAFTING and building.production_bonus:
            benefits["production_bonus"] = building.production_bonus

        if purpose == BuildingPurpose.STORAGE and building.storage_capacity:
            benefits["storage"] = building.storage_capacity

        return {"success": True, "benefits": benefits}

    def get_statistics(self) -> Dict:
        """Get building statistics - CONSISTENT with /buildings endpoint"""

        total_designs = len(self.designs)
        started_construction = sum(1 for d in self.designs.values() if d.construction_started)

        # IMPORTANT: Match /buildings endpoint logic - only count non-collapsed completed buildings
        completed_standing = sum(1 for b in self.buildings.values() if b.is_complete and not b.collapsed)
        collapsed = sum(1 for b in self.buildings.values() if b.collapsed)
        total_completed = sum(1 for b in self.buildings.values() if b.is_complete)

        return {
            "total_designs": total_designs,
            "started_construction": started_construction,
            "completed_buildings": completed_standing,  # Only standing buildings (matches /buildings endpoint)
            "total_completed": total_completed,  # All completed (including collapsed)
            "collapsed_buildings": collapsed,
            "construction_failures": len(self.construction_failures),
            "success_rate": (
                total_completed / total_designs if total_designs > 0 else 0.0
            ),
            "collapse_rate": (
                collapsed / total_completed if total_completed > 0 else 0.0
            ),
            "designs_by_purpose": self._count_by_purpose(),
            "buildings_by_category": self._count_by_category(),  # NEW!
        }

    def _count_by_purpose(self) -> Dict[str, int]:
        """Count designs by purpose"""
        counts = {}
        for design in self.designs.values():
            for purpose in design.intended_purposes:
                counts[purpose] = counts.get(purpose, 0) + 1
        return counts

    def _count_by_category(self) -> Dict[str, int]:
        """Count completed buildings by category"""
        counts = {}
        for building in self.buildings.values():
            if building.is_complete and not building.collapsed:
                # Get category from design
                design = self.designs.get(building.design_id)
                if design:
                    category = design.category
                    counts[category] = counts.get(category, 0) + 1
        return counts
