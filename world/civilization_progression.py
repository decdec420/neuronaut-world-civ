"""
CIVILIZATION PROGRESSION SYSTEM
From Stone Age Primitives → Space Age Pioneers

THE PROBLEM WE'RE SOLVING:
- Agents stuck in Stone Age forever (Day 6, 83 discoveries, still Stone Age)
- Discovering useless materials (mix_stone, shape_food) that don't lead anywhere
- No resource scarcity driving innovation
- No clear path from fire → bronze → steel → steam → rocket

THE SOLUTION:
1. RESOURCE SCARCITY - Can't build 3346 buildings from "a few rocks"
2. DISCOVERY DEPENDENCIES - Must discover fire BEFORE pottery, ore BEFORE bronze
3. ERA MILESTONES - Clear achievements unlock new possibilities
4. SPECIALIST PROGRESSION - Einsteins and Fords emerge naturally
5. STARTING POINT - Everyone begins primitive, must innovate to survive

HOW PROGRESSION WORKS:
Stone Age (Start):
  ├─ Resources: stone, wood, plant_fiber, food, water
  ├─ Goal: Survive (hunger, shelter, warmth)
  ├─ Key Discovery: FIRE (enables Bronze Age)
  └─ Milestone: First person to create fire = Bronze Age pioneer

Bronze Age (Fire discovered):
  ├─ New Resource Unlocked: metal_ore (from mining)
  ├─ Goal: Create tools that last
  ├─ Key Discovery: BRONZE (smelting metal_ore + fire)
  └─ Milestone: First bronze tool = 10x more effective

Iron Age (Bronze mastered):
  ├─ New Resource: iron_ore (requires bronze tools to mine)
  ├─ Goal: Create permanent structures
  ├─ Key Discovery: IRON/STEEL
  └─ Milestone: First steel building lasts 100x longer

Medieval (Iron Age infrastructure):
  ├─ New: Specialization (blacksmiths, farmers, scholars)
  ├─ Goal: Scale production
  ├─ Key Discovery: MILL (automated production)
  └─ Milestone: First mill = 10x production

Industrial (Medieval infrastructure):
  ├─ New: Coal, steam power
  ├─ Goal: Mass production
  ├─ Key Discovery: STEAM ENGINE
  └─ Milestone: First factory = 100x production

Modern (Industrial base):
  ├─ New: Oil, electricity
  ├─ Goal: Information & mobility
  ├─ Key Discovery: COMPUTER/ENGINE
  └─ Milestone: First computer = knowledge sharing

Space Age (Modern tech):
  ├─ New: Advanced alloys, rocket fuel
  ├─ Goal: Leave Earth
  ├─ Key Discovery: ROCKET
  └─ Milestone: First launch = civilization milestone

HOW TO CREATE "ROCKEFELLER" or "FORD":
1. Agent has high AMBITION + ACHIEVEMENT need
2. Focuses on ONE domain (trade/building/crafting)
3. Makes KEY DISCOVERY (bronze/steam/computer)
4. Success compounds (better tools → more resources → bigger projects)
5. Becomes SPECIALIST with influence
6. Changes civilization permanently
"""

import copy
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from datetime import datetime
from enum import Enum


# ==============================================================================
# CIVILIZATION ERAS
# ==============================================================================

class Era(Enum):
    """Progression through civilization stages"""
    STONE_AGE = "Stone Age"
    BRONZE_AGE = "Bronze Age"
    IRON_AGE = "Iron Age"
    MEDIEVAL = "Medieval"
    INDUSTRIAL = "Industrial"
    MODERN = "Modern"
    SPACE_AGE = "Space Age"


# ==============================================================================
# RESOURCE DISCOVERY SYSTEM
# ==============================================================================

@dataclass
class ResourceTier:
    """
    Resources unlocked at each era.

    You CAN'T discover bronze without first having fire!
    You CAN'T mine iron without bronze tools!
    """
    era: Era
    base_resources: List[str]  # Available from start of era
    discoverable_resources: List[str]  # Can be discovered in this era
    required_prerequisite: Optional[str]  # What discovery unlocks this?


# PROGRESSIVE RESOURCE TIERS
RESOURCE_TIERS = {
    Era.STONE_AGE: ResourceTier(
        era=Era.STONE_AGE,
        base_resources=['stone', 'wood', 'plant_fiber', 'food', 'water', 'clay', 'sand', 'hide'],
        discoverable_resources=['fire', 'sharp_stone', 'stone_tool', 'pottery'],
        required_prerequisite=None  # Start of game
    ),

    Era.BRONZE_AGE: ResourceTier(
        era=Era.BRONZE_AGE,
        base_resources=['metal_ore'],  # Unlocked after fire discovered
        discoverable_resources=['bronze', 'copper', 'refined_metal', 'metal_tool', 'wheel'],
        required_prerequisite='fire'  # Need fire to unlock Bronze Age
    ),

    Era.IRON_AGE: ResourceTier(
        era=Era.IRON_AGE,
        base_resources=['iron_ore'],  # Requires bronze tools to mine
        discoverable_resources=['iron', 'steel', 'advanced_tool', 'plow'],
        required_prerequisite='bronze'
    ),

    Era.MEDIEVAL: ResourceTier(
        era=Era.MEDIEVAL,
        base_resources=['coal'],
        discoverable_resources=['mill', 'waterwheel', 'windmill', 'advanced_forge', 'glass'],
        required_prerequisite='iron'
    ),

    Era.INDUSTRIAL: ResourceTier(
        era=Era.INDUSTRIAL,
        base_resources=['coal', 'oil'],
        discoverable_resources=['steam_engine', 'factory', 'rail', 'machinery'],
        required_prerequisite='mill'
    ),

    Era.MODERN: ResourceTier(
        era=Era.MODERN,
        base_resources=['electricity', 'rubber', 'plastic'],
        discoverable_resources=['computer', 'engine', 'aircraft', 'electronics'],
        required_prerequisite='steam_engine'
    ),

    Era.SPACE_AGE: ResourceTier(
        era=Era.SPACE_AGE,
        base_resources=['advanced_alloy', 'rocket_fuel'],
        discoverable_resources=['rocket', 'satellite', 'spacecraft', 'space_station'],
        required_prerequisite='computer'
    )
}


# ==============================================================================
# MILESTONE TRACKING
# ==============================================================================

@dataclass
class CivilizationMilestone:
    """
    A significant achievement that changes everything.

    Like the first person to create fire, discover bronze, or invent the steam engine.
    These are the "Rockefeller moments" - game-changing breakthroughs.
    """
    milestone_id: str
    name: str
    description: str
    achieved_by_agent_id: Optional[str] = None
    achieved_by_name: Optional[str] = None
    achieved_date: Optional[datetime] = None
    impact: str = ""  # How this changed civilization

    # Mechanical effects
    unlocks_era: Optional[Era] = None
    unlocks_resources: List[str] = field(default_factory=list)
    production_multiplier: float = 1.0  # How much more effective things become

    # Legacy
    is_achieved: bool = False
    agents_who_know: Set[str] = field(default_factory=set)  # Knowledge spreads


# MAJOR MILESTONES
CIVILIZATION_MILESTONES = {
    'first_fire': CivilizationMilestone(
        milestone_id='first_fire',
        name='Discovery of Fire',
        description='The first agent to create fire through experimentation',
        impact='Enables cooking, warmth, and metallurgy. Unlocks Bronze Age.',
        unlocks_era=Era.BRONZE_AGE,
        unlocks_resources=['metal_ore'],
        production_multiplier=2.0  # Everything becomes 2x easier with fire
    ),

    'first_bronze': CivilizationMilestone(
        milestone_id='first_bronze',
        name='Discovery of Bronze',
        description='The first metallurgist to smelt bronze from ore',
        impact='Tools last 10x longer. Enables permanent structures.',
        unlocks_era=Era.IRON_AGE,
        unlocks_resources=['iron_ore'],
        production_multiplier=10.0  # Bronze tools are 10x better than stone
    ),

    'first_iron': CivilizationMilestone(
        milestone_id='first_iron',
        name='Discovery of Iron',
        description='The first smith to forge iron into steel',
        impact='Enables large-scale construction and agriculture.',
        unlocks_era=Era.MEDIEVAL,
        unlocks_resources=['coal'],
        production_multiplier=5.0
    ),

    'first_mill': CivilizationMilestone(
        milestone_id='first_mill',
        name='Invention of the Mill',
        description='The first engineer to harness water/wind power',
        impact='Automated production. 10x output with same labor.',
        unlocks_era=Era.INDUSTRIAL,
        unlocks_resources=['coal', 'oil'],
        production_multiplier=10.0
    ),

    'first_steam_engine': CivilizationMilestone(
        milestone_id='first_steam_engine',
        name='Invention of Steam Engine',
        description='The first inventor to harness steam power',
        impact='Mass production. Factories. Transportation revolution.',
        unlocks_era=Era.MODERN,
        unlocks_resources=['electricity', 'rubber'],
        production_multiplier=100.0
    ),

    'first_computer': CivilizationMilestone(
        milestone_id='first_computer',
        name='Invention of Computer',
        description='The first scientist to create a computing machine',
        impact='Information age. Knowledge sharing. Scientific breakthroughs.',
        unlocks_era=Era.SPACE_AGE,
        unlocks_resources=['advanced_alloy', 'rocket_fuel'],
        production_multiplier=10.0
    ),

    'first_rocket': CivilizationMilestone(
        milestone_id='first_rocket',
        name='First Successful Rocket Launch',
        description='The first engineer to launch a rocket to space',
        impact='Space age begins. Civilization can leave Earth.',
        unlocks_era=None,  # Final milestone
        unlocks_resources=[],
        production_multiplier=1.0
    )
}


# ==============================================================================
# CIVILIZATION PROGRESSION ENGINE
# ==============================================================================

class CivilizationProgressionEngine:
    """
    Manages the REAL progression from Stone Age → Space Age.

    This creates the "watch it unfold" experience with:
    - Logical starting point (Stone Age primitives)
    - Clear milestones (fire → bronze → iron → steam → rocket)
    - Specialists who drive progress (the Einsteins and Fords)
    - Resource scarcity forcing innovation
    """

    def __init__(self):
        self.current_era = Era.STONE_AGE
        # Each world gets its own milestones. A shallow copy shared the milestone
        # objects, so once one world (a test, or the server before a reset) lit
        # the first fire, every later world in the process found it already lit.
        self.milestones = copy.deepcopy(CIVILIZATION_MILESTONES)
        self.discoveries_made: Set[str] = set()
        self.era_history: List[Dict] = []

        # Track pioneers (agents who achieved milestones)
        self.pioneers: Dict[str, str] = {}  # milestone_id -> agent_id

        # Resource availability (what can agents find in the world?)
        self.available_resources = RESOURCE_TIERS[Era.STONE_AGE].base_resources.copy()

    def check_discovery(self, material_name: str, agent_id: str, agent_name: str) -> Optional[CivilizationMilestone]:
        """
        When an agent discovers something, check if it's a MILESTONE.

        Returns milestone if this discovery changes civilization, None otherwise.
        """
        self.discoveries_made.add(material_name)

        # Check if this discovery achieves a milestone
        for milestone in self.milestones.values():
            if milestone.is_achieved:
                continue

            # Check if discovery matches milestone
            if self._discovery_matches_milestone(material_name, milestone):
                # MILESTONE ACHIEVED!
                milestone.is_achieved = True
                milestone.achieved_by_agent_id = agent_id
                milestone.achieved_by_name = agent_name
                milestone.achieved_date = datetime.now()
                milestone.agents_who_know.add(agent_id)

                # Record pioneer
                self.pioneers[milestone.milestone_id] = agent_id

                # Unlock new era if applicable
                if milestone.unlocks_era:
                    self._advance_to_era(milestone.unlocks_era, milestone)

                # Unlock new resources
                for resource in milestone.unlocks_resources:
                    if resource not in self.available_resources:
                        self.available_resources.append(resource)

                return milestone

        return None

    def _discovery_matches_milestone(self, material_name: str, milestone: CivilizationMilestone) -> bool:
        """Check if a discovery matches a milestone"""
        # Map material names to milestones
        material_to_milestone = {
            'fire': 'first_fire',
            'bronze': 'first_bronze',
            'refined_metal': 'first_bronze',
            'iron': 'first_iron',
            'steel': 'first_iron',
            'mill': 'first_mill',
            'waterwheel': 'first_mill',
            'windmill': 'first_mill',
            'steam_engine': 'first_steam_engine',
            'steam': 'first_steam_engine',
            'computer': 'first_computer',
            'electronics': 'first_computer',
            'rocket': 'first_rocket',
            'spacecraft': 'first_rocket'
        }

        return material_to_milestone.get(material_name) == milestone.milestone_id

    def _advance_to_era(self, new_era: Era, milestone: CivilizationMilestone):
        """Advance civilization to new era"""
        old_era = self.current_era
        self.current_era = new_era

        # Record in history
        self.era_history.append({
            'era': new_era.value,
            'achieved_date': datetime.now(),
            'milestone': milestone.name,
            'pioneer': milestone.achieved_by_name,
            'from_era': old_era.value
        })

        # Unlock base resources for new era
        new_tier = RESOURCE_TIERS.get(new_era)
        if new_tier:
            for resource in new_tier.base_resources:
                if resource not in self.available_resources:
                    self.available_resources.append(resource)

    def can_discover_material(self, material_name: str) -> bool:
        """
        Can agents discover this material at current era?

        This prevents discovering "rocket_fuel" in Stone Age!
        """
        # Check if material is in current era's discoverable list
        current_tier = RESOURCE_TIERS[self.current_era]

        # Can always discover current era's materials
        if material_name in current_tier.discoverable_resources:
            return True

        # Can discover materials from previous eras
        for era in Era:
            if era.value == self.current_era.value:
                break
            tier = RESOURCE_TIERS[era]
            if material_name in tier.discoverable_resources:
                return True

        return False

    def get_production_multiplier(self) -> float:
        """
        How much more effective is production in current era?

        Stone Age: 1.0x (baseline)
        Bronze Age: 2.0x (fire)
        Iron Age: 20.0x (bronze tools)
        Industrial: 2000.0x (steam engines)
        Modern: 20000.0x (computers)
        """
        multiplier = 1.0

        for milestone in self.milestones.values():
            if milestone.is_achieved:
                multiplier *= milestone.production_multiplier

        return multiplier

    def get_current_pioneers(self) -> Dict[str, str]:
        """Get agents who achieved major milestones"""
        return {
            milestone_id: self.milestones[milestone_id].achieved_by_name
            for milestone_id, agent_id in self.pioneers.items()
        }

    def get_next_milestone(self) -> Optional[CivilizationMilestone]:
        """What's the next major achievement to unlock?"""
        for milestone in self.milestones.values():
            if not milestone.is_achieved:
                return milestone
        return None

    def get_stats(self) -> Dict:
        """Get progression statistics"""
        # Convert era history dates to ISO format strings for JSON serialization
        serializable_history = []
        for entry in self.era_history:
            serializable_entry = entry.copy()
            if 'achieved_date' in serializable_entry and isinstance(serializable_entry['achieved_date'], datetime):
                serializable_entry['achieved_date'] = serializable_entry['achieved_date'].isoformat()
            serializable_history.append(serializable_entry)

        return {
            'current_era': self.current_era.value,
            'total_discoveries': len(self.discoveries_made),
            'milestones_achieved': sum(1 for m in self.milestones.values() if m.is_achieved),
            'milestones_total': len(self.milestones),
            'production_multiplier': self.get_production_multiplier(),
            'available_resources': len(self.available_resources),
            'pioneers': self.get_current_pioneers(),
            'next_milestone': self.get_next_milestone().name if self.get_next_milestone() else None,
            'era_history': serializable_history
        }
