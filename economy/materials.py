"""
Material System - Categorized, logical material definitions

Materials are organized into categories for inventory display.
Each material has properties that determine what it can be used for.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class MaterialCategory(Enum):
    """Material categories for organization"""
    # Natural resources (found in world)
    NATURAL_MINERALS = "natural_minerals"  # Stone, ore, clay, sand
    NATURAL_ORGANICS = "natural_organics"  # Wood, plant_fiber, hide
    NATURAL_SUSTENANCE = "natural_sustenance"  # Food, water (gathered)

    # Processed materials (refined from natural)
    PROCESSED_BUILDING = "processed_building"  # Planks, bricks, metal bars
    PROCESSED_TEXTILES = "processed_textiles"  # Cloth, leather, rope
    PROCESSED_FUEL = "processed_fuel"  # Charcoal, coal, oil

    # Crafted items
    TOOLS = "tools"  # Axe, pickaxe, hoe
    WEAPONS = "weapons"  # Spear, bow, sword
    COOKED_FOOD = "cooked_food"  # Cooked meat, bread, stew
    CONTAINERS = "containers"  # Basket, pot, barrel

    # Advanced/Discovered
    DISCOVERED = "discovered"  # Agent-created materials
    ALIEN = "alien"  # Materials from space/other planets
    UNKNOWN = "unknown"  # Experimental compounds


@dataclass
class Material:
    """A material with properties and metadata"""
    id: str
    name: str
    category: MaterialCategory
    description: str

    # Physical properties
    hardness: float  # 0.0 (liquid) to 1.0 (diamond-hard)
    weight: float  # kg per unit
    durability: float  # 0.0 (fragile) to 1.0 (indestructible)

    # Functional properties
    flammable: bool = False
    edible: bool = False
    liquid: bool = False
    stackable: bool = True

    # Tags for crafting logic
    tags: List[str] = None  # e.g., ['fuel', 'combustible', 'building_material']

    # Discovery info
    discovered_by: Optional[str] = None  # Agent ID who discovered it
    discovery_method: Optional[str] = None  # How it was discovered

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


# ============================================================
# NATURAL MINERALS - Found in the world
# ============================================================

STONE = Material(
    id="stone",
    name="Stone",
    category=MaterialCategory.NATURAL_MINERALS,
    description="Hard sedimentary rock. Can be shaped into tools or used for building.",
    hardness=0.7,
    weight=2.5,
    durability=0.8,
    tags=['building_material', 'tool_material', 'hard']
)

METAL_ORE = Material(
    id="metal_ore",
    name="Metal Ore",
    category=MaterialCategory.NATURAL_MINERALS,
    description="Raw metallic ore. Must be smelted to extract pure metal.",
    hardness=0.6,
    weight=4.0,
    durability=0.5,
    tags=['smeltable', 'heavy']
)

CLAY = Material(
    id="clay",
    name="Clay",
    category=MaterialCategory.NATURAL_MINERALS,
    description="Malleable earth. Can be shaped when wet and hardened by fire.",
    hardness=0.2,
    weight=1.8,
    durability=0.3,
    tags=['moldable', 'fireable', 'building_material']
)

SAND = Material(
    id="sand",
    name="Sand",
    category=MaterialCategory.NATURAL_MINERALS,
    description="Fine granular material. Can be melted into glass or mixed with clay for building.",
    hardness=0.1,
    weight=1.5,
    durability=0.1,
    tags=['granular', 'meltable']
)

# ============================================================
# NATURAL ORGANICS - Biological materials
# ============================================================

WOOD = Material(
    id="wood",
    name="Wood",
    category=MaterialCategory.NATURAL_ORGANICS,
    description="Raw timber from trees. Burns well and can be shaped into many forms.",
    hardness=0.3,
    weight=0.8,
    durability=0.4,
    flammable=True,
    tags=['fuel', 'building_material', 'combustible', 'carvable']
)

PLANT_FIBER = Material(
    id="plant_fiber",
    name="Plant Fiber",
    category=MaterialCategory.NATURAL_ORGANICS,
    description="Fibrous plant material. Can be woven into rope or cloth.",
    hardness=0.1,
    weight=0.2,
    durability=0.3,
    flammable=True,
    tags=['weavable', 'fuel', 'light']
)

HIDE = Material(
    id="hide",
    name="Animal Hide",
    category=MaterialCategory.NATURAL_ORGANICS,
    description="Raw animal skin. Can be tanned into leather for clothing and containers.",
    hardness=0.2,
    weight=1.2,
    durability=0.4,
    tags=['tannable', 'flexible']
)

# ============================================================
# NATURAL SUSTENANCE - Food and water
# ============================================================

FOOD_RAW = Material(
    id="food",
    name="Raw Food",
    category=MaterialCategory.NATURAL_SUSTENANCE,
    description="Uncooked food gathered from plants or hunted animals. Can be eaten or cooked.",
    hardness=0.1,
    weight=0.5,
    durability=0.2,
    edible=True,
    tags=['perishable', 'cookable']
)

WATER = Material(
    id="water",
    name="Water",
    category=MaterialCategory.NATURAL_SUSTENANCE,
    description="Fresh water. Essential for survival, cooking, and many crafts.",
    hardness=0.0,
    weight=1.0,
    durability=0.0,
    liquid=True,
    edible=True,
    tags=['liquid', 'essential']
)

# ============================================================
# PROCESSED BUILDING MATERIALS
# ============================================================

REFINED_WOOD = Material(
    id="refine_wood",
    name="Wooden Planks",
    category=MaterialCategory.PROCESSED_BUILDING,
    description="Wood shaped and smoothed into planks. Better for building than raw wood.",
    hardness=0.3,
    weight=0.6,
    durability=0.5,
    flammable=True,
    tags=['building_material', 'refined', 'fuel']
)

METAL_BAR = Material(
    id="metal",
    name="Metal Bar",
    category=MaterialCategory.PROCESSED_BUILDING,
    description="Smelted and purified metal. Strong and durable for tools and structures.",
    hardness=0.9,
    weight=7.8,
    durability=0.9,
    tags=['building_material', 'tool_material', 'strong', 'refined']
)

COINS = Material(
    id="coins",
    name="Coins",
    category=MaterialCategory.PROCESSED_BUILDING,
    description="Standardized metal currency. Pure metal shaped into coins - the foundation of trade! Adds to agent wealth when created.",
    hardness=0.8,
    weight=0.1,
    durability=0.9,
    tags=['currency', 'trade', 'valuable', 'refined']
)

BRICK = Material(
    id="brick",
    name="Fired Brick",
    category=MaterialCategory.PROCESSED_BUILDING,
    description="Clay shaped and hardened by fire. Excellent building material.",
    hardness=0.7,
    weight=2.0,
    durability=0.8,
    tags=['building_material', 'fire_resistant']
)

# ============================================================
# PROCESSED FUEL
# ============================================================

FIRE = Material(
    id="fire",
    name="Fire",
    category=MaterialCategory.PROCESSED_FUEL,
    description="Controlled flame. Provides heat for cooking, warmth, and smelting. Created from wood/plant_fiber + fire-starting.",
    hardness=0.0,
    weight=0.0,
    durability=0.1,
    flammable=False,  # Fire itself doesn't burn, it IS burning
    tags=['heat_source', 'light_source', 'ephemeral']
)

CHARCOAL = Material(
    id="charcoal",
    name="Charcoal",
    category=MaterialCategory.PROCESSED_FUEL,
    description="Wood burned in low oxygen. Burns hotter than wood, essential for smelting.",
    hardness=0.2,
    weight=0.3,
    durability=0.2,
    flammable=True,
    tags=['fuel', 'high_heat', 'combustible']
)

# ============================================================
# PROCESSED TEXTILES
# ============================================================

ROPE = Material(
    id="rope",
    name="Rope",
    category=MaterialCategory.PROCESSED_TEXTILES,
    description="Plant fiber twisted into strong cord. Useful for binding and construction.",
    hardness=0.2,
    weight=0.3,
    durability=0.6,
    flammable=True,
    tags=['binding', 'flexible']
)

LEATHER = Material(
    id="leather",
    name="Leather",
    category=MaterialCategory.PROCESSED_TEXTILES,
    description="Tanned animal hide. Durable and flexible for clothing and containers.",
    hardness=0.3,
    weight=0.8,
    durability=0.7,
    tags=['clothing_material', 'flexible', 'water_resistant']
)

# ============================================================
# COOKED FOOD
# ============================================================

COOKED_FOOD = Material(
    id="cooked_food",
    name="Cooked Food",
    category=MaterialCategory.COOKED_FOOD,
    description="Food prepared with fire. More nutritious and safer than raw food.",
    hardness=0.1,
    weight=0.4,
    durability=0.3,
    edible=True,
    tags=['nutritious', 'perishable']
)

# ============================================================
# ALL MATERIALS REGISTRY
# ============================================================

ALL_MATERIALS: Dict[str, Material] = {
    # Natural minerals
    "stone": STONE,
    "metal_ore": METAL_ORE,
    "clay": CLAY,
    "sand": SAND,

    # Natural organics
    "wood": WOOD,
    "plant_fiber": PLANT_FIBER,
    "hide": HIDE,

    # Natural sustenance
    "food": FOOD_RAW,
    "water": WATER,

    # Processed building
    "refine_wood": REFINED_WOOD,
    "metal": METAL_BAR,
    "coins": COINS,
    "brick": BRICK,

    # Processed fuel
    "fire": FIRE,
    "charcoal": CHARCOAL,

    # Processed textiles
    "rope": ROPE,
    "leather": LEATHER,

    # Cooked food
    "cooked_food": COOKED_FOOD,
}


def get_material(material_id: str) -> Optional[Material]:
    """Get material by ID"""
    return ALL_MATERIALS.get(material_id)


def get_materials_by_category(category: MaterialCategory) -> List[Material]:
    """Get all materials in a category"""
    return [m for m in ALL_MATERIALS.values() if m.category == category]


def get_category_summary() -> Dict[MaterialCategory, int]:
    """Get count of materials in each category"""
    summary = {}
    for material in ALL_MATERIALS.values():
        if material.category not in summary:
            summary[material.category] = 0
        summary[material.category] += 1
    return summary
