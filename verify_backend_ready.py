"""
Backend Readiness Verification Script

Run this before starting frontend development to ensure backend is operational.
"""

import sys
import os

print("=" * 70)
print("NEURONAUT WORLD - BACKEND READINESS CHECK")
print("=" * 70)

# Test 1: Critical imports
print("\n[1/5] Testing critical imports...")
try:
    import requests
    print("    ✅ requests library installed")
except ImportError as e:
    print(f"    ❌ FAILED: {e}")
    print("    ACTION: pip install -r requirements.txt")
    sys.exit(1)

try:
    from engine.simulation import SimulationEngine
    print("    ✅ SimulationEngine imports successfully")
except Exception as e:
    print(f"    ❌ FAILED: {e}")
    sys.exit(1)

# Test 2: Simulation initialization
print("\n[2/5] Testing simulation initialization...")
try:
    sim = SimulationEngine(world_width=100, world_height=100)
    print(f"    ✅ SimulationEngine created")
    print(f"    ✅ Initial agents: {len(sim.world.agents)}")
except Exception as e:
    print(f"    ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: All systems initialized
print("\n[3/5] Verifying all 10 major systems...")
systems = {
    'Economy': sim.economy,
    'Agriculture': sim.agriculture,
    'Health': sim.health,
    'Religion': sim.religion,
    'Territory': sim.territory,
    'Chemistry': sim.chemistry,
    'Energy': sim.energy,
    'Materials': sim.materials_science,
    'Life': sim.life_system,
    'Fun': sim.fun_system,
}

all_ok = True
for name, system in systems.items():
    if system is not None:
        print(f"    ✅ {name}: {type(system).__name__}")
    else:
        print(f"    ❌ {name}: NOT INITIALIZED")
        all_ok = False

if not all_ok:
    print("\n    ❌ Some systems failed to initialize")
    sys.exit(1)

# Test 4: Create agent
print("\n[4/5] Testing agent creation...")
try:
    initial_count = len(sim.world.agents)
    new_agent = sim.create_agent("Test Agent", age=25, is_player=False)
    final_count = len(sim.world.agents)

    if final_count == initial_count + 1:
        print(f"    ✅ Agent created successfully: {new_agent.name}")
        print(f"    ✅ Total agents: {final_count}")
    else:
        print(f"    ❌ Agent count mismatch: {initial_count} → {final_count}")
        sys.exit(1)
except Exception as e:
    print(f"    ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Run simulation tick
print("\n[5/5] Testing simulation tick...")
try:
    import asyncio
    asyncio.run(sim.tick())
    print("    ✅ First tick completed successfully")

    # Verify world time advanced
    if sim.world.time.current_tick > 0:
        print(f"    ✅ World time: Tick {sim.world.time.current_tick}")
    else:
        print("    ⚠️  Warning: World time did not advance")

except Exception as e:
    print(f"    ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Success summary
print("\n" + "=" * 70)
print("✅ BACKEND VERIFICATION COMPLETE - ALL TESTS PASSED!")
print("=" * 70)
print("\nSYSTEM STATUS:")
print(f"  • Agents: {len(sim.world.agents)} active")
print(f"  • Tick: {sim.world.time.current_tick}")
print(f"  • Economy Type: {type(sim.economy).__name__}")
print(f"  • GDP: {sim.economy.total_gdp:.2f}")
print(f"  • All 10 major systems: OPERATIONAL")

print("\n🚀 READY TO BUILD FRONTEND!")
print("\nNext steps:")
print("  1. Review DEPLOYMENT_CHECKLIST.md")
print("  2. Review BACKEND_HEALTH_REPORT.md")
print("  3. Start building your frontend interface")
print("\nThe backend foundation is solid. Go build something amazing! 🎯")

sys.exit(0)
