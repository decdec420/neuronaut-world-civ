"""
Test Goal-Driven Behavior Over Time

Verifies that agents with specific goals make decisions that align with
those goals over multiple simulation ticks.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.agent import Agent, Gender
from agents.autonomous_agent import AutonomousAgentMixin, GoalType
from engine.psychology import PersonalityProfile
from config import load_config
from agents.llm_brain import MultiLLMBrain
import types

def test_goal_pursuit_over_time():
    """Test that agents pursue their goals consistently"""

    print("\n" + "="*70)
    print("🎯 TESTING GOAL-DRIVEN BEHAVIOR OVER TIME")
    print("="*70)

    # Create ambitious agent focused on WEALTH
    agent = Agent(
        name="Entrepreneur",
        age=30,
        gender=Gender.MALE,
        personality=PersonalityProfile(
            ambition=0.95,      # Very ambitious!
            creativity=0.6,
            risk_taking=0.4,    # Moderate risk
            extraversion=0.7
        )
    )

    # Add autonomous capabilities
    config = load_config()
    llm_brain = MultiLLMBrain(api_keys=config.get_api_keys())

    for method_name in dir(AutonomousAgentMixin):
        if not method_name.startswith('__'):
            method = getattr(AutonomousAgentMixin, method_name, None)
            if callable(method):
                setattr(agent, method_name, types.MethodType(method, agent))

    agent.init_autonomous_systems(llm_brain=llm_brain)

    print(f"\n✅ Created {agent.name}")
    print(f"   Ambition: {agent.personality.ambition:.0%}")
    print(f"   Risk-taking: {agent.personality.risk_taking:.0%}")

    # Set WEALTH goal
    agent.goals.add_goal(
        goal_type=GoalType.WEALTH,
        description="Become the wealthiest agent in the world",
        priority=1.0,  # Maximum priority!
        current_tick=0
    )

    print(f"\n🎯 Goal Set: {agent.goals.active_goals[0].description}")

    # Add some relevant memories
    agent.memory.remember(
        tick=10,
        event_type="trade_success",
        description="I traded wood for stone and made a good profit. Trading seems profitable!",
        emotional_intensity=0.6,
        importance=0.5,
        participants=["Trader1"],
        location=(10, 10)
    )

    agent.memory.learn_fact(
        'trading_is_profitable',
        'Trading resources can increase my wealth quickly'
    )

    print(f"📚 Added memory: Trading is profitable")

    # Run multiple decision cycles
    print(f"\n" + "="*70)
    print("🔄 Running 5 Decision Cycles")
    print("="*70)

    wealth_related_actions = ['trade', 'gather_food', 'gather_water', 'gather_materials',
                              'craft', 'build']
    non_wealth_actions = ['rest', 'play_game', 'celebrate', 'socialize']

    decisions = []

    for i in range(5):
        print(f"\n--- Cycle {i+1} ---")

        # Perceptions with trading opportunities
        perceptions = {
            'nearby_agents': [
                {'name': 'Trader1', 'distance': 3, 'relationship': 0.5}
            ],
            'nearby_resources': [
                {'type': 'wood', 'distance': 2},
                {'type': 'stone', 'distance': 4}
            ],
            'available_actions': wealth_related_actions + non_wealth_actions
        }

        try:
            decision = agent.autonomous_decide(perceptions, current_tick=i*10, config=config)
            action_str = str(decision).lower()

            # Extract action type
            if 'trade' in action_str:
                action_type = 'trade'
            elif 'gather' in action_str:
                action_type = 'gather'
            elif 'craft' in action_str:
                action_type = 'craft'
            elif 'build' in action_str:
                action_type = 'build'
            elif 'rest' in action_str:
                action_type = 'rest'
            elif 'play' in action_str:
                action_type = 'play'
            elif 'celebrate' in action_str:
                action_type = 'celebrate'
            else:
                action_type = 'other'

            decisions.append(action_type)

            # Check if aligned with wealth goal
            is_wealth_aligned = action_type in ['trade', 'gather', 'craft', 'build']
            alignment_emoji = "✅" if is_wealth_aligned else "⚠️"

            print(f"   Decision: {action_type} {alignment_emoji}")
            print(f"   Aligns with WEALTH goal: {is_wealth_aligned}")

        except Exception as e:
            print(f"   ❌ Decision failed: {e}")
            decisions.append('error')

    # Analyze results
    print(f"\n" + "="*70)
    print("📊 ANALYSIS")
    print("="*70)

    wealth_aligned_count = sum(1 for d in decisions if d in wealth_related_actions)
    total_decisions = len([d for d in decisions if d != 'error'])

    if total_decisions > 0:
        alignment_rate = wealth_aligned_count / total_decisions

        print(f"\nDecisions made: {decisions}")
        print(f"Wealth-aligned: {wealth_aligned_count}/{total_decisions} ({alignment_rate:.0%})")

        if alignment_rate >= 0.8:
            print(f"\n✅ EXCELLENT! Agent consistently pursued wealth goal ({alignment_rate:.0%})")
            return True
        elif alignment_rate >= 0.6:
            print(f"\n⚠️  GOOD: Agent mostly pursued wealth goal ({alignment_rate:.0%})")
            print(f"   Some deviation is realistic - agents have other needs too")
            return True
        else:
            print(f"\n❌ POOR: Agent not consistently pursuing goal ({alignment_rate:.0%})")
            print(f"   Goals may not be influencing decisions enough")
            return False
    else:
        print(f"\n❌ All decisions failed - cannot assess goal pursuit")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 GOAL PURSUIT TEST")
    print("   Verifying agents pursue their goals over time")
    print("="*70)

    success = test_goal_pursuit_over_time()

    if success:
        print("\n" + "="*70)
        print("✅ GOAL-DRIVEN BEHAVIOR VERIFIED!")
        print("   Agents make decisions aligned with their life goals")
        print("="*70)
        exit(0)
    else:
        print("\n" + "="*70)
        print("⚠️  Goal influence needs improvement")
        print("="*70)
        exit(1)
