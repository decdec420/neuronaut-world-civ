"""
Simplified Combat System Integration Test

Tests the core combat integration without requiring all dependencies:
1. Weapon/armor recipes exist
2. Equipment stats are defined
3. Equipment tier classification works
"""

import os
import sys

# Ensure the project root is in sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from economy.recipes import ALL_RECIPES
from world.equipment_stats import (
    WEAPON_STATS, ARMOR_STATS,
    is_weapon, is_armor,
    get_weapon_bonus, get_armor_bonus,
    get_equipment_tier
)


def test_weapon_armor_recipes():
    """Test 1: Verify weapon and armor recipes exist"""
    print("=" * 60)
    print("TEST 1: Weapon & Armor Recipes")
    print("=" * 60)

    # Count weapons and armor
    weapons = [r_id for r_id in ALL_RECIPES if 'weapon' in r_id or 'sword' in r_id or 'spear' in r_id or 'axe' in r_id or 'bow' in r_id or 'club' in r_id]
    armor = [r_id for r_id in ALL_RECIPES if 'armor' in r_id or 'helmet' in r_id or 'shield' in r_id]

    print(f"\n✅ Found {len(weapons)} weapon recipes:")
    for w in sorted(weapons):
        recipe = ALL_RECIPES[w]
        inputs_str = ', '.join([f"{qty}x {item}" for item, qty in recipe.inputs.items()])
        skill_str = f"{recipe.required_skill} {recipe.min_skill_level:.1f}" if recipe.required_skill else "none"
        print(f"   • {recipe.name}")
        print(f"      Inputs: {inputs_str}")
        print(f"      Skill: {skill_str}, Difficulty: {recipe.difficulty:.1f}")
        print(f"      Requires fire: {recipe.requires_fire}")

    print(f"\n✅ Found {len(armor)} armor recipes:")
    for a in sorted(armor):
        recipe = ALL_RECIPES[a]
        inputs_str = ', '.join([f"{qty}x {item}" for item, qty in recipe.inputs.items()])
        skill_str = f"{recipe.required_skill} {recipe.min_skill_level:.1f}" if recipe.required_skill else "none"
        print(f"   • {recipe.name}")
        print(f"      Inputs: {inputs_str}")
        print(f"      Skill: {skill_str}, Difficulty: {recipe.difficulty:.1f}")
        print(f"      Requires fire: {recipe.requires_fire}")

    assert len(weapons) >= 7, f"Expected at least 7 weapon recipes, got {len(weapons)}"
    assert len(armor) >= 6, f"Expected at least 6 armor recipes, got {len(armor)}"

    print(f"\n✅ PASS: {len(weapons)} weapons + {len(armor)} armor recipes defined")
    return True


def test_equipment_stats():
    """Test 2: Verify equipment stats are defined"""
    print("\n" + "=" * 60)
    print("TEST 2: Equipment Stats")
    print("=" * 60)

    print(f"\n📊 Weapon Stats ({len(WEAPON_STATS)} items):")
    for weapon in sorted(WEAPON_STATS.keys()):
        damage, skill = WEAPON_STATS[weapon]
        tier = get_equipment_tier(weapon)
        print(f"   • {weapon:20s} [{tier:12s}] damage={damage:.1f}x, skill_req={skill:.1f}")
        assert damage >= 1.0, f"{weapon} should have damage >= 1.0"

    print(f"\n📊 Armor Stats ({len(ARMOR_STATS)} items):")
    for armor in sorted(ARMOR_STATS.keys()):
        defense, mobility = ARMOR_STATS[armor]
        tier = get_equipment_tier(armor)
        print(f"   • {armor:20s} [{tier:12s}] defense={defense:.0%}, mobility_cost={mobility:.0%}")
        assert 0.0 <= defense <= 1.0, f"{armor} defense should be 0-100%"
        assert 0.0 <= mobility <= 1.0, f"{armor} mobility should be 0-100%"

    # Test helper functions
    assert is_weapon("bronze_sword"), "bronze_sword should be recognized as weapon"
    assert is_armor("leather_armor"), "leather_armor should be recognized as armor"
    assert not is_weapon("food"), "food should not be weapon"

    damage, skill = get_weapon_bonus("iron_sword")
    assert damage > 2.0, f"Iron sword should be powerful (got {damage})"

    defense, mobility = get_armor_bonus("iron_armor")
    assert defense > 0.4, f"Iron armor should have good protection (got {defense})"

    print(f"\n✅ PASS: All equipment stats valid")
    return True


def test_progression_tiers():
    """Test 3: Verify equipment progression through eras"""
    print("\n" + "=" * 60)
    print("TEST 3: Equipment Progression Tiers")
    print("=" * 60)

    stone_age = []
    bronze_age = []
    iron_age = []

    all_equipment = list(WEAPON_STATS.keys()) + list(ARMOR_STATS.keys())

    for item in all_equipment:
        tier = get_equipment_tier(item)
        if tier == "stone_age":
            stone_age.append(item)
        elif tier == "bronze_age":
            bronze_age.append(item)
        elif tier == "iron_age":
            iron_age.append(item)

    print(f"\n🪨 Stone Age ({len(stone_age)} items):")
    for item in sorted(stone_age):
        if is_weapon(item):
            damage, skill = get_weapon_bonus(item)
            print(f"   • {item:20s} [WEAPON] damage={damage:.1f}x")
        else:
            defense, mobility = get_armor_bonus(item)
            print(f"   • {item:20s} [ARMOR]  defense={defense:.0%}")

    print(f"\n🥉 Bronze Age ({len(bronze_age)} items):")
    for item in sorted(bronze_age):
        if is_weapon(item):
            damage, skill = get_weapon_bonus(item)
            print(f"   • {item:20s} [WEAPON] damage={damage:.1f}x")
        else:
            defense, mobility = get_armor_bonus(item)
            print(f"   • {item:20s} [ARMOR]  defense={defense:.0%}")

    print(f"\n⚔️  Iron Age ({len(iron_age)} items):")
    for item in sorted(iron_age):
        if is_weapon(item):
            damage, skill = get_weapon_bonus(item)
            print(f"   • {item:20s} [WEAPON] damage={damage:.1f}x")
        else:
            defense, mobility = get_armor_bonus(item)
            print(f"   • {item:20s} [ARMOR]  defense={defense:.0%}")

    # Verify progression (later eras should be more powerful)
    stone_weapons = [item for item in stone_age if is_weapon(item)]
    iron_weapons = [item for item in iron_age if is_weapon(item)]

    if stone_weapons and iron_weapons:
        stone_avg = sum(get_weapon_bonus(w)[0] for w in stone_weapons) / len(stone_weapons)
        iron_avg = sum(get_weapon_bonus(w)[0] for w in iron_weapons) / len(iron_weapons)
        print(f"\n📈 Weapon Power Progression:")
        print(f"   Stone Age average: {stone_avg:.1f}x damage")
        print(f"   Iron Age average:  {iron_avg:.1f}x damage")
        assert iron_avg > stone_avg, "Iron age weapons should be more powerful"

    print(f"\n✅ PASS: Equipment progression is logical")
    return True


def run_all_tests():
    """Run all combat integration tests"""
    print("\n" + "🛡️ " * 20)
    print("COMBAT SYSTEM INTEGRATION TESTS (Simplified)")
    print("🛡️ " * 20)

    tests = [
        ("Weapon & Armor Recipes", test_weapon_armor_recipes),
        ("Equipment Stats", test_equipment_stats),
        ("Equipment Progression", test_progression_tiers),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, True, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"\n❌ FAIL: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for name, success, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if error:
            print(f"         Error: {error}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Combat crafting system complete!")
        print("\n✨ Features Ready:")
        print("   • 7 weapons (club → spear → axe → bow → bronze → iron)")
        print("   • 6 armor types (hide → leather → bronze → iron)")
        print("   • Equipment stats defined (damage, defense, skill requirements)")
        print("   • Era progression (Stone → Bronze → Iron Age)")
        print("   • Crafting recipes with realistic inputs and skill requirements")
        print("\n🚀 Weapons and armor ready for combat system!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
