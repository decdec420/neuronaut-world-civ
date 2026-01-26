"""
Logical Crafting Recipes

Each recipe makes realistic sense:
- Fire requires combustible materials + fire-starting
- Cooking requires food + fire
- Smelting requires ore + high heat
- Processing materials follows real-world logic

Agents can discover new recipes through experimentation!
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime


@dataclass
class Recipe:
    """A recipe for crafting an item"""
    id: str
    name: str
    description: str  # What this recipe does
    output_item: str
    output_quantity: int = 1

    # Inputs required
    inputs: Dict[str, int] = field(default_factory=dict)  # item -> quantity

    # Special requirements
    requires_fire: bool = False  # Needs active fire nearby
    requires_water: bool = False  # Needs water source
    requires_tool: Optional[str] = None  # Needs specific tool

    # Skills
    required_skill: Optional[str] = None
    min_skill_level: float = 0.0
    skill_bonus_multiplier: float = 1.0  # Skilled crafters produce more

    # Discovery
    is_basic: bool = True  # Known from start, or must be discovered
    discovered_by: Optional[str] = None
    discovered_at: Optional[datetime] = None

    # Stats
    times_crafted: int = 0
    difficulty: float = 0.5  # 0.0 (easy) to 1.0 (very hard)

    def can_craft(self, agent, has_fire: bool = False, has_water: bool = False) -> Tuple[bool, str]:
        """Check if agent can craft this"""
        # Check inputs
        for item, qty in self.inputs.items():
            if not agent.inventory.has_item(item, qty):
                return False, f"Need {qty} {item}"

        # Check fire requirement
        if self.requires_fire and not has_fire:
            return False, "Need active fire"

        # Check water requirement
        if self.requires_water and not has_water:
            return False, "Need water source"

        # Check tool
        if self.requires_tool:
            if not agent.inventory.has_item(self.requires_tool):
                return False, f"Need {self.requires_tool}"

        # Check skill
        if self.required_skill:
            skill_level = agent.skills.get_skill(self.required_skill)
            if skill_level < self.min_skill_level:
                return False, f"Need {self.required_skill} skill {self.min_skill_level:.2f}"

        return True, "Can craft"

    def execute_craft(self, agent) -> Tuple[bool, str]:
        """Execute crafting"""
        # Remove inputs
        for item, qty in self.inputs.items():
            if not agent.inventory.remove_item(item, qty):
                return False, f"Failed to consume {item}"

        # Calculate output (skill bonus)
        output_qty = self.output_quantity

        if self.required_skill:
            skill_level = agent.skills.get_skill(self.required_skill)
            bonus = skill_level * self.skill_bonus_multiplier
            output_qty = max(1, int(output_qty * (1.0 + bonus)))

        # Add output
        success = agent.inventory.add_item(self.output_item, output_qty)

        if not success:
            # Inventory full, give items back
            for item, qty in self.inputs.items():
                agent.inventory.add_item(item, qty)
            return False, "Inventory full"

        # Stats
        self.times_crafted += 1

        # Learn skill
        if self.required_skill:
            agent.skills.learn_skill(self.required_skill, amount=0.05)

        return True, f"Crafted {output_qty} {self.output_item}"


# ============================================================
# FIRE-MAKING & FUEL
# ============================================================

MAKE_FIRE = Recipe(
    id="make_fire",
    name="Make Fire",
    description="Create fire by friction using wood or plant fiber. Fire enables cooking, warmth, and smelting.",
    output_item="fire",
    output_quantity=1,
    inputs={"wood": 2},  # Need fuel to start fire
    required_skill="survival",
    min_skill_level=0.0,
    is_basic=True,
    difficulty=0.3
)

MAKE_FIRE_FIBER = Recipe(
    id="make_fire_fiber",
    name="Make Fire (Plant Fiber)",
    description="Create fire using dry plant fiber as tinder. Easier than wood but produces less fire.",
    output_item="fire",
    output_quantity=1,
    inputs={"plant_fiber": 4},
    required_skill="survival",
    min_skill_level=0.0,
    is_basic=True,
    difficulty=0.2
)

MAKE_CHARCOAL = Recipe(
    id="make_charcoal",
    name="Make Charcoal",
    description="Burn wood in low oxygen to create charcoal. Burns hotter than wood - essential for metalworking.",
    output_item="charcoal",
    output_quantity=2,
    inputs={"wood": 4},
    requires_fire=True,
    required_skill="fire_management",
    min_skill_level=0.3,
    is_basic=False,  # Must discover
    difficulty=0.6
)

# ============================================================
# COOKING
# ============================================================

COOK_FOOD = Recipe(
    id="cook_food",
    name="Cook Food",
    description="Cook raw food over fire. Cooked food is more nutritious and safer to eat.",
    output_item="cooked_food",
    output_quantity=1,
    inputs={"food": 1},
    requires_fire=True,
    required_skill="cooking",
    min_skill_level=0.0,
    is_basic=True,
    difficulty=0.2
)

# ============================================================
# SMELTING & METALWORKING
# ============================================================

SMELT_ORE = Recipe(
    id="smelt_ore",
    name="Smelt Metal Ore",
    description="Smelt raw ore into pure metal using high heat. Charcoal produces better results than wood.",
    output_item="metal",
    output_quantity=1,
    inputs={"metal_ore": 2, "charcoal": 1},  # Charcoal for high heat
    requires_fire=True,
    required_skill="metallurgy",
    min_skill_level=0.2,
    is_basic=False,  # Must discover
    difficulty=0.7
)

SMELT_ORE_WOOD = Recipe(
    id="smelt_ore_wood",
    name="Smelt Metal Ore (Wood Fuel)",
    description="Smelt ore using wood fuel. Less efficient than charcoal but workable.",
    output_item="metal",
    output_quantity=1,
    inputs={"metal_ore": 3, "wood": 4},  # More materials needed without charcoal
    requires_fire=True,
    required_skill="metallurgy",
    min_skill_level=0.3,
    is_basic=False,
    difficulty=0.8
)

MINT_COINS = Recipe(
    id="mint_coins",
    name="Mint Coins",
    description="Shape pure metal into standardized coins - the foundation of currency! 1 metal = 10 coins worth of wealth.",
    output_item="coins",
    output_quantity=10,  # 1 metal produces 10 coins
    inputs={"metal": 1},
    requires_fire=False,  # Don't need fire to stamp coins
    required_skill="metallurgy",
    min_skill_level=0.5,
    is_basic=False,  # Must discover!
    difficulty=0.6
)

# ============================================================
# BUILDING MATERIALS
# ============================================================

REFINE_WOOD = Recipe(
    id="refine_wood",
    name="Make Wooden Planks",
    description="Shape raw wood into smooth planks for building. More structurally sound than raw logs.",
    output_item="refine_wood",
    output_quantity=4,
    inputs={"wood": 1},
    required_skill="carpentry",
    min_skill_level=0.1,
    is_basic=True,
    difficulty=0.3
)

MAKE_BRICK = Recipe(
    id="make_brick",
    name="Fire Brick",
    description="Shape clay and harden in fire to create durable bricks for building.",
    output_item="brick",
    output_quantity=4,
    inputs={"clay": 2},
    requires_fire=True,
    required_skill="masonry",
    min_skill_level=0.2,
    is_basic=False,
    difficulty=0.5
)

# ============================================================
# TEXTILES & ROPE
# ============================================================

MAKE_ROPE = Recipe(
    id="make_rope",
    name="Twist Rope",
    description="Twist plant fibers together to create strong rope for binding and construction.",
    output_item="rope",
    output_quantity=2,
    inputs={"plant_fiber": 3},
    required_skill="weaving",
    min_skill_level=0.1,
    is_basic=True,
    difficulty=0.2
)

TAN_LEATHER = Recipe(
    id="tan_leather",
    name="Tan Leather",
    description="Process animal hide into durable leather. Requires water for tanning.",
    output_item="leather",
    output_quantity=1,
    inputs={"hide": 1},
    requires_water=True,
    required_skill="leatherworking",
    min_skill_level=0.2,
    is_basic=False,
    difficulty=0.5
)

# ============================================================
# WEAPONS - STONE AGE
# ============================================================

CRAFT_WOODEN_CLUB = Recipe(
    id="craft_wooden_club",
    name="Craft Wooden Club",
    description="Shape a heavy branch into a simple club. The most basic weapon for self-defense.",
    output_item="wooden_club",
    output_quantity=1,
    inputs={"wood": 2},
    required_skill="crafting",
    min_skill_level=0.0,
    is_basic=True,
    difficulty=0.1
)

CRAFT_STONE_SPEAR = Recipe(
    id="craft_stone_spear",
    name="Craft Stone Spear",
    description="Lash a sharp stone to a wooden shaft to create a spear. Good for hunting and combat.",
    output_item="stone_spear",
    output_quantity=1,
    inputs={"wood": 2, "stone": 2, "rope": 1},
    required_skill="crafting",
    min_skill_level=0.2,
    is_basic=True,
    difficulty=0.3
)

CRAFT_STONE_AXE = Recipe(
    id="craft_stone_axe",
    name="Craft Stone Axe",
    description="Bind a sharp stone to a wooden handle. Useful for chopping and combat.",
    output_item="stone_axe",
    output_quantity=1,
    inputs={"wood": 1, "stone": 3, "rope": 1},
    required_skill="crafting",
    min_skill_level=0.3,
    is_basic=True,
    difficulty=0.4
)

CRAFT_BOW = Recipe(
    id="craft_bow",
    name="Craft Bow",
    description="Bend wood and string it with plant fiber to create a hunting bow. Allows ranged combat.",
    output_item="bow",
    output_quantity=1,
    inputs={"wood": 2, "plant_fiber": 4},
    required_skill="crafting",
    min_skill_level=0.4,
    is_basic=False,
    difficulty=0.6
)

# ============================================================
# WEAPONS - METAL AGE
# ============================================================

CRAFT_BRONZE_SWORD = Recipe(
    id="craft_bronze_sword",
    name="Forge Bronze Sword",
    description="Forge metal into a deadly sword. The weapon of warriors and soldiers.",
    output_item="bronze_sword",
    output_quantity=1,
    inputs={"metal": 3, "wood": 1},
    requires_fire=True,
    required_skill="metallurgy",
    min_skill_level=0.5,
    is_basic=False,
    difficulty=0.7
)

CRAFT_BRONZE_SPEAR = Recipe(
    id="craft_bronze_spear",
    name="Forge Bronze Spear",
    description="Create a metal-tipped spear. Superior to stone spears in every way.",
    output_item="bronze_spear",
    output_quantity=1,
    inputs={"metal": 2, "wood": 2},
    requires_fire=True,
    required_skill="metallurgy",
    min_skill_level=0.4,
    is_basic=False,
    difficulty=0.6
)

CRAFT_IRON_SWORD = Recipe(
    id="craft_iron_sword",
    name="Forge Iron Sword",
    description="Forge iron into a superior sword. Stronger and sharper than bronze.",
    output_item="iron_sword",
    output_quantity=1,
    inputs={"metal": 4, "wood": 1},  # More metal needed for iron quality
    requires_fire=True,
    required_skill="metallurgy",
    min_skill_level=0.7,
    is_basic=False,
    difficulty=0.8
)

# ============================================================
# ARMOR - PRIMITIVE
# ============================================================

CRAFT_HIDE_ARMOR = Recipe(
    id="craft_hide_armor",
    name="Craft Hide Armor",
    description="Stitch together animal hides to create basic protective armor.",
    output_item="hide_armor",
    output_quantity=1,
    inputs={"hide": 4, "rope": 2},
    required_skill="leatherworking",
    min_skill_level=0.1,
    is_basic=True,
    difficulty=0.3
)

CRAFT_LEATHER_ARMOR = Recipe(
    id="craft_leather_armor",
    name="Craft Leather Armor",
    description="Craft tanned leather into flexible, durable armor. Better protection than hide.",
    output_item="leather_armor",
    output_quantity=1,
    inputs={"leather": 3, "rope": 2},
    required_skill="leatherworking",
    min_skill_level=0.3,
    is_basic=False,
    difficulty=0.5
)

# ============================================================
# ARMOR - METAL
# ============================================================

CRAFT_BRONZE_HELMET = Recipe(
    id="craft_bronze_helmet",
    name="Forge Bronze Helmet",
    description="Shape metal into a protective helmet. Protects the head in battle.",
    output_item="bronze_helmet",
    output_quantity=1,
    inputs={"metal": 2},
    requires_fire=True,
    required_skill="metallurgy",
    min_skill_level=0.5,
    is_basic=False,
    difficulty=0.6
)

CRAFT_BRONZE_ARMOR = Recipe(
    id="craft_bronze_armor",
    name="Forge Bronze Armor",
    description="Forge metal plates into body armor. Provides excellent protection but heavy.",
    output_item="bronze_armor",
    output_quantity=1,
    inputs={"metal": 6, "leather": 2},
    requires_fire=True,
    required_skill="metallurgy",
    min_skill_level=0.6,
    is_basic=False,
    difficulty=0.8
)

CRAFT_IRON_ARMOR = Recipe(
    id="craft_iron_armor",
    name="Forge Iron Armor",
    description="Forge superior iron armor. The pinnacle of personal protection.",
    output_item="iron_armor",
    output_quantity=1,
    inputs={"metal": 8, "leather": 2},
    requires_fire=True,
    required_skill="metallurgy",
    min_skill_level=0.8,
    is_basic=False,
    difficulty=0.9
)

CRAFT_SHIELD = Recipe(
    id="craft_shield",
    name="Craft Shield",
    description="Build a wooden shield reinforced with metal. Essential for defense in combat.",
    output_item="shield",
    output_quantity=1,
    inputs={"wood": 4, "metal": 2, "leather": 1},
    required_skill="crafting",
    min_skill_level=0.4,
    is_basic=False,
    difficulty=0.5
)

# ============================================================
# RECIPE REGISTRY
# ============================================================

ALL_RECIPES: Dict[str, Recipe] = {
    # Fire & Fuel
    "make_fire": MAKE_FIRE,
    "make_fire_fiber": MAKE_FIRE_FIBER,
    "make_charcoal": MAKE_CHARCOAL,

    # Cooking
    "cook_food": COOK_FOOD,

    # Smelting
    "smelt_ore": SMELT_ORE,
    "smelt_ore_wood": SMELT_ORE_WOOD,
    "mint_coins": MINT_COINS,

    # Building materials
    "refine_wood": REFINE_WOOD,
    "make_brick": MAKE_BRICK,

    # Textiles
    "make_rope": MAKE_ROPE,
    "tan_leather": TAN_LEATHER,

    # Weapons - Stone Age
    "craft_wooden_club": CRAFT_WOODEN_CLUB,
    "craft_stone_spear": CRAFT_STONE_SPEAR,
    "craft_stone_axe": CRAFT_STONE_AXE,
    "craft_bow": CRAFT_BOW,

    # Weapons - Metal Age
    "craft_bronze_sword": CRAFT_BRONZE_SWORD,
    "craft_bronze_spear": CRAFT_BRONZE_SPEAR,
    "craft_iron_sword": CRAFT_IRON_SWORD,

    # Armor - Primitive
    "craft_hide_armor": CRAFT_HIDE_ARMOR,
    "craft_leather_armor": CRAFT_LEATHER_ARMOR,

    # Armor - Metal
    "craft_bronze_helmet": CRAFT_BRONZE_HELMET,
    "craft_bronze_armor": CRAFT_BRONZE_ARMOR,
    "craft_iron_armor": CRAFT_IRON_ARMOR,
    "craft_shield": CRAFT_SHIELD,
}

# Basic recipes known from start
BASIC_RECIPES = {
    recipe_id: recipe
    for recipe_id, recipe in ALL_RECIPES.items()
    if recipe.is_basic
}

# Advanced recipes that must be discovered
ADVANCED_RECIPES = {
    recipe_id: recipe
    for recipe_id, recipe in ALL_RECIPES.items()
    if not recipe.is_basic
}


def get_recipe(recipe_id: str) -> Optional[Recipe]:
    """Get recipe by ID"""
    return ALL_RECIPES.get(recipe_id)


def get_craftable_recipes(agent, has_fire: bool = False, has_water: bool = False) -> List[Recipe]:
    """Get all recipes agent can currently craft"""
    craftable = []
    for recipe in ALL_RECIPES.values():
        can_craft, _ = recipe.can_craft(agent, has_fire, has_water)
        if can_craft:
            craftable.append(recipe)
    return craftable
