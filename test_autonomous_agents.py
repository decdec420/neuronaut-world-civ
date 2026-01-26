"""
Test Script for Autonomous Agent System

This script tests the LLM integration and autonomous decision-making
with a few test agents before running the full simulation.

Run this to verify everything is working!
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.agent import Agent, Gender, ActionType
from agents.llm_brain import MultiLLMBrain
from agents.autonomous_agent import AutonomousAgentMixin, GoalType
from engine.psychology import PersonalityProfile, NeedState, EmotionalState
from config import load_config
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Create a test agent class that combines Agent with autonomous capabilities
class TestAgent(Agent, AutonomousAgentMixin):
    """Test agent with autonomous capabilities"""

    def __init__(self, **kwargs):
        # Call parent Agent.__init__
        super().__init__(**kwargs)

        # Initialize autonomous systems
        self.init_autonomous_systems(llm_brain=None)  # Brain set later


def test_llm_providers():
    """Test each LLM provider"""

    print("\n" + "="*60)
    print("🧪 TESTING LLM PROVIDERS")
    print("="*60)

    config = load_config()
    llm_brain = MultiLLMBrain(api_keys=config.get_api_keys())

    test_prompt = "You are a hungry agent. What do you do? (Answer in one sentence)"

    from agents.llm_brain import LLMProvider

    providers_to_test = [
        LLMProvider.OLLAMA_LOCAL,
        LLMProvider.GROQ,
        LLMProvider.GEMINI_FLASH,
    ]

    for provider in providers_to_test:
        if provider != LLMProvider.OLLAMA_LOCAL:
            # Check if API key exists
            provider_name = provider.value
            if not llm_brain.api_keys.get(provider_name.replace('_flash', '')):
                print(f"\n❌ {provider.value}: No API key configured (skipping)")
                continue

        print(f"\n🔄 Testing {provider.value}...")

        try:
            response = llm_brain.call_llm(
                provider=provider,
                prompt=test_prompt,
                temperature=0.7,
                max_tokens=50
            )

            if response:
                print(f"✅ {provider.value}: Working!")
                print(f"   Response: {response.text[:100]}")
                print(f"   Time: {response.response_time:.2f}s")
            else:
                print(f"❌ {provider.value}: Failed (returned None)")

        except Exception as e:
            print(f"❌ {provider.value}: Error - {e}")

    print("\n" + "="*60)


def test_agent_decision():
    """Test autonomous agent decision-making"""

    print("\n" + "="*60)
    print("🤖 TESTING AUTONOMOUS AGENT DECISIONS")
    print("="*60)

    config = load_config()

    if not config.use_llm_decisions:
        print("\n⚠️  LLM decisions are DISABLED in config")
        print("   Set USE_LLM_DECISIONS=true in .env to enable")
        return

    llm_brain = MultiLLMBrain(api_keys=config.get_api_keys())

    # Create test agent
    print("\n📝 Creating test agent...")

    agent = TestAgent(
        age=25,
        gender=Gender.FEMALE,
        personality=PersonalityProfile(
            ambition=0.8,
            creativity=0.9,
            extraversion=0.6,
            openness=0.8,
            conscientiousness=0.5
        )
    )
    agent.name = "Zara"
    agent.llm_brain = llm_brain

    # Set some needs
    from engine.psychology import NeedType
    agent.needs.needs[NeedType.HUNGER].level = 0.7  # Moderately hungry
    agent.needs.needs[NeedType.CREATIVITY].level = 0.8  # High creativity need
    agent.needs.needs[NeedType.MEANING].level = 0.6

    # Add some items to inventory
    agent.inventory.add_item('wood', 3)
    agent.inventory.add_item('stone', 2)
    agent.wealth = 50

    print(f"✅ Created: {agent.name}")
    print(f"   Age: {agent.age}")
    print(f"   Personality: Ambitious {agent.personality.ambition:.1f}, Creative {agent.personality.creativity:.1f}")
    print(f"   Needs: Hunger {agent.needs.needs[NeedType.HUNGER].level:.1f}, Creativity {agent.needs.needs[NeedType.CREATIVITY].level:.1f}")
    print(f"   Inventory: {list(agent.inventory.items.keys())}")

    # Test perceptions (format expected by existing agent.py code)
    perceptions = {
        'nearby_agents': [
            {'id': 'marcus_001', 'name': 'Marcus', 'distance': 5},
            {'id': 'luna_001', 'name': 'Luna', 'distance': 3}
        ],
        'nearby_resources': [
            {'type': 'water', 'distance': 2},
            {'type': 'berries', 'distance': 4},
            {'type': 'metal_ore', 'distance': 6}
        ]
    }

    # Test decision-making
    print(f"\n🧠 {agent.name} is making a decision...")

    try:
        action = agent.autonomous_decide(
            perceptions=perceptions,
            current_tick=100,
            config=config
        )

        print(f"\n✅ Decision made!")
        print(f"   Action: {action.action_type.value}")
        print(f"   Priority: {action.priority:.2f}")

    except Exception as e:
        print(f"\n❌ Decision failed: {e}")
        import traceback
        traceback.print_exc()


def test_long_term_planning():
    """Test long-term goal planning"""

    print("\n" + "="*60)
    print("🎯 TESTING LONG-TERM GOAL PLANNING")
    print("="*60)

    config = load_config()

    if not config.use_llm_decisions:
        print("\n⚠️  LLM decisions are DISABLED in config")
        return

    llm_brain = MultiLLMBrain(api_keys=config.get_api_keys())

    # Create ambitious agent
    agent = TestAgent(
        age=30,
        gender=Gender.MALE,
        personality=PersonalityProfile(
            ambition=0.9,  # Very ambitious
            creativity=0.4,
            extraversion=0.7,
            openness=0.6
        )
    )
    agent.name = "Marcus"
    agent.llm_brain = llm_brain

    print(f"\n📝 Created: {agent.name}")
    print(f"   Personality: Very ambitious (0.9), social (0.7)")

    # Test long-term planning
    perceptions = {'nearby_agents': [], 'nearby_resources': []}

    print(f"\n🧠 {agent.name} is planning their future...")

    try:
        agent._do_long_term_planning(perceptions, current_tick=100)

        print(f"\n✅ Planning complete!")
        print(f"   Active goals: {len(agent.goals.active_goals)}")

        for goal in agent.goals.get_top_goals(5):
            print(f"   - {goal.goal_type.value}: {goal.description} (priority: {goal.priority:.2f})")

    except Exception as e:
        print(f"\n❌ Planning failed: {e}")
        import traceback
        traceback.print_exc()


def test_memory_system():
    """Test memory and learning"""

    print("\n" + "="*60)
    print("💾 TESTING MEMORY SYSTEM")
    print("="*60)

    agent = TestAgent(
        age=20,
        gender=Gender.FEMALE
    )
    agent.name = "Luna"

    print(f"\n📝 Created: {agent.name}")

    # Add some memories
    print(f"\n📝 Adding memories...")

    agent.remember_event(
        tick=100,
        event_type="discovery",
        description="I discovered how to make fire!",
        emotional_intensity=0.9,
        importance=0.9
    )

    agent.remember_event(
        tick=150,
        event_type="social",
        description="I made a new friend named Zara",
        emotional_intensity=0.7,
        importance=0.6,
        participants=["zara_id"]
    )

    agent.remember_event(
        tick=200,
        event_type="failure",
        description="My experiment failed and caused a small fire",
        emotional_intensity=0.6,
        importance=0.5
    )

    print(f"\n✅ Added {len(agent.memory.episodic_memory)} memories")

    # Retrieve memories
    print(f"\n🔍 Recent memories:")
    for memory in agent.memory.get_recent_memories(3):
        print(f"   [{memory.event_type}] {memory.description}")
        print(f"      Emotional: {memory.emotional_intensity:.1f}, Important: {memory.importance:.1f}")

    print(f"\n🔍 Significant life events:")
    for memory in agent.memory.get_significant_memories(min_importance=0.6):
        print(f"   [{memory.event_type}] {memory.description}")


def main():
    """Run all tests"""

    print("\n" + "="*60)
    print("🧪 AUTONOMOUS AGENT SYSTEM - TEST SUITE")
    print("="*60)

    # Load and display config
    config = load_config()
    config.print_status()

    # Run tests
    tests = [
        ("LLM Providers", test_llm_providers),
        ("Agent Decision", test_agent_decision),
        ("Long-term Planning", test_long_term_planning),
        ("Memory System", test_memory_system)
    ]

    for test_name, test_func in tests:
        try:
            test_func()
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Summary
    print("\n" + "="*60)
    print("✅ TESTING COMPLETE")
    print("="*60)
    print("\nIf all tests passed, you're ready to run the full simulation!")
    print("Run: python main.py")
    print("="*60)
    print()


if __name__ == "__main__":
    main()
