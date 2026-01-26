"""
Equipment Stats for Combat System

Defines combat effectiveness of weapons and armor that can be crafted.
These stats are used by the warfare system to calculate combat power.
"""

from typing import Dict, Tuple


# ============================================================
# WEAPON STATS
# ============================================================
# Format: item_name -> (damage_multiplier, skill_requirement)

WEAPON_STATS: Dict[str, Tuple[float, float]] = {
    # Stone Age Weapons
    "wooden_club": (1.2, 0.0),           # Basic melee weapon
    "stone_spear": (1.5, 0.2),           # Better reach and damage
    "stone_axe": (1.6, 0.3),             # Good damage but requires skill
    "bow": (1.8, 0.4),                   # Ranged advantage

    # Bronze Age Weapons
    "bronze_sword": (2.2, 0.5),          # Superior melee weapon
    "bronze_spear": (2.0, 0.4),          # Metal-tipped spear

    # Iron Age Weapons
    "iron_sword": (3.0, 0.7),            # Peak medieval weapon
}


# ============================================================
# ARMOR STATS
# ============================================================
# Format: item_name -> (defense_reduction, mobility_cost)
# defense_reduction: How much damage is reduced (0.0 to 1.0)
# mobility_cost: Speed penalty (0.0 = no penalty, 0.5 = half speed)

ARMOR_STATS: Dict[str, Tuple[float, float]] = {
    # Primitive Armor
    "hide_armor": (0.15, 0.05),          # Basic protection, minimal penalty
    "leather_armor": (0.25, 0.10),       # Better protection, light penalty

    # Metal Armor
    "bronze_helmet": (0.15, 0.05),       # Head protection only
    "bronze_armor": (0.40, 0.25),        # Excellent protection, heavy
    "iron_armor": (0.55, 0.30),          # Best protection, very heavy
    "shield": (0.20, 0.15),              # Defensive bonus, moderate penalty
}


# ============================================================
# EQUIPMENT BONUSES
# ============================================================

def get_weapon_bonus(item_name: str) -> Tuple[float, float]:
    """
    Get weapon combat stats

    Returns:
        (damage_multiplier, skill_requirement)
    """
    return WEAPON_STATS.get(item_name, (1.0, 0.0))


def get_armor_bonus(item_name: str) -> Tuple[float, float]:
    """
    Get armor defensive stats

    Returns:
        (defense_reduction, mobility_cost)
    """
    return ARMOR_STATS.get(item_name, (0.0, 0.0))


def is_weapon(item_name: str) -> bool:
    """Check if item is a weapon"""
    return item_name in WEAPON_STATS


def is_armor(item_name: str) -> bool:
    """Check if item is armor"""
    return item_name in ARMOR_STATS


def get_equipment_tier(item_name: str) -> str:
    """
    Get equipment tier for tech progression

    Returns:
        "stone_age", "bronze_age", "iron_age", or "unknown"
    """
    stone_age_items = {"wooden_club", "stone_spear", "stone_axe", "bow", "hide_armor"}
    bronze_age_items = {"bronze_sword", "bronze_spear", "bronze_helmet", "bronze_armor", "leather_armor", "shield"}
    iron_age_items = {"iron_sword", "iron_armor"}

    if item_name in stone_age_items:
        return "stone_age"
    elif item_name in bronze_age_items:
        return "bronze_age"
    elif item_name in iron_age_items:
        return "iron_age"
    else:
        return "unknown"
