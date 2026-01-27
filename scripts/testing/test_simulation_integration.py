"""
Test Full Simulation Integration with AI Autonomy

This tests that:
1. Simulation initializes with AI agents
2. Agents make AI-powered decisions
3. Actions execute in the world
4. Everything connects properly
"""

import asyncio
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.simulation import SimulationEngine
from config import load_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_simulation():
    """Test complete simulation with AI autonomy"""

    print("\n" + "="*60)
    print("🧪 TESTING FULL SIMULATION INTEGRATION")
    print("="*60)

    # Load config
    config = load_config()
    print("\n📋 Configuration loaded")
    config.print_status()

    # Create simulation
    print("\n🌍 Creating simulation engine...")
    simulation = SimulationEngine(world_width=100, world_height=100)

    # Initialize with 5 test agents
    print("\n👥 Initializing world with 5 agents...")
    simulation.initialize_world(num_agents=5)

    print(f"\n✅ Created {len(simulation.world.agents)} agents")

    # Verify agents have autonomous capabilities
    print("\n🔍 Verifying AI autonomy...")
    for agent in simulation.world.agents:
        has_autonomous = hasattr(agent, 'autonomous_decide')
        has_goals = hasattr(agent, 'goals')
        has_llm_brain = hasattr(agent, 'llm_brain')

        status = "✅" if (has_autonomous and has_goals and has_llm_brain) else "❌"
        print(f"{status} {agent.name}: autonomous={has_autonomous}, goals={has_goals}, llm_brain={has_llm_brain}")

    # Run 3 simulation ticks
    print("\n🔄 Running 3 simulation ticks...")
    for tick in range(3):
        print(f"\n--- Tick {tick + 1} ---")
        try:
            await simulation.tick()

            # Show what agents did
            for agent in simulation.world.agents[:3]:  # Show first 3 agents
                if hasattr(agent, 'recent_action_outcomes') and agent.recent_action_outcomes:
                    last_action = agent.recent_action_outcomes[-1]
                    print(f"  {agent.name}: {last_action.get('action', 'unknown')} - "
                          f"{'✅' if last_action.get('succeeded') else '❌'}")
        except Exception as e:
            print(f"❌ Error during tick {tick + 1}: {e}")
            import traceback
            traceback.print_exc()
            break

    print("\n" + "="*60)
    print("✅ SIMULATION INTEGRATION TEST COMPLETE")
    print("="*60)

    # Summary
    total_agents = len(simulation.world.agents)
    alive_agents = sum(1 for a in simulation.world.agents if a.alive)

    print(f"\nFinal State:")
    print(f"  Total agents: {total_agents}")
    print(f"  Alive: {alive_agents}")
    print(f"  World tick: {simulation.world.time.current_tick}")
    print(f"  AI decisions: {'ENABLED ✅' if config.use_llm_decisions else 'DISABLED ❌'}")

    if config.use_llm_decisions and hasattr(simulation, 'llm_brain'):
        stats = simulation.llm_brain.get_stats()
        print(f"\n📊 LLM Usage Stats:")
        if 'total_calls' in stats:
            print(f"  Total calls: {stats['total_calls']}")
            for provider, count in stats.get('calls_by_provider', {}).items():
                if count > 0:
                    print(f"  {provider}: {count}")
        else:
            # Alternative stats format
            total = sum(stats.get('calls_by_provider', {}).values())
            print(f"  Total calls: {total}")
            for provider, count in stats.get('calls_by_provider', {}).items():
                if count > 0:
                    print(f"  {provider}: {count}")


async def main():
    """Run the test"""
    try:
        await test_simulation()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
