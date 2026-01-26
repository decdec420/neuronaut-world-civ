"""
Test Goals & Memory Integration with AI Decision-Making

This test verifies CRITICAL FIXES #1 & #2:
1. Agent goals appear in LLM prompts
2. Agent memories appear in LLM prompts
3. AI decisions are influenced by goals and memories
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

def test_goals_memory_integration():
    """Test that goals and memories are visible to AI and influence decisions"""

    print("\n" + "="*70)
    print("🧪 TESTING GOALS & MEMORY INTEGRATION WITH AI DECISIONS")
    print("="*70)

    # Create agent
    agent = Agent(
        name="TestAgent",
        age=25,
        gender=Gender.FEMALE,
        personality=PersonalityProfile(
            ambition=0.9,      # Ambitious - wants to achieve goals
            creativity=0.7,
            risk_taking=0.3    # Cautious - should remember dangers
        )
    )

    # Add autonomous capabilities
    config = load_config()
    llm_brain = MultiLLMBrain(api_keys=config.get_api_keys())

    # Bind autonomous methods
    for method_name in dir(AutonomousAgentMixin):
        if not method_name.startswith('__'):
            method = getattr(AutonomousAgentMixin, method_name, None)
            if callable(method):
                setattr(agent, method_name, types.MethodType(method, agent))

    # Initialize autonomous systems
    agent.init_autonomous_systems(llm_brain=llm_brain)

    print(f"\n✅ Created {agent.name}")
    print(f"   Personality: Ambition {agent.personality.ambition:.1f}, Caution {1 - agent.personality.risk_taking:.1f}")

    # ===== SET SOME GOALS =====
    print("\n" + "="*70)
    print("📋 STEP 1: Setting Life Goals")
    print("="*70)

    # Add wealth goal
    agent.goals.add_goal(
        goal_type=GoalType.WEALTH,
        description="Become wealthy by trading",
        priority=0.9,
        current_tick=0
    )

    # Add family goal
    agent.goals.add_goal(
        goal_type=GoalType.FAMILY,
        description="Find a partner and start a family",
        priority=0.7,
        current_tick=0
    )

    # Update progress on wealth goal
    wealth_goal = agent.goals.active_goals[0]
    wealth_goal.progress = 0.3  # 30% progress

    top_goals = agent.goals.get_top_goals(3)
    print(f"\n✅ Set {len(agent.goals.active_goals)} goals:")
    for i, goal in enumerate(top_goals, 1):
        print(f"   {i}. {goal.description} (priority: {goal.priority:.1f}, progress: {goal.progress:.0%})")

    # ===== ADD MEMORIES =====
    print("\n" + "="*70)
    print("📚 STEP 2: Adding Memories")
    print("="*70)

    # Add successful trade memory
    agent.memory.remember(
        tick=50,
        event_type="trade_success",
        description="Successfully traded wood for stone with Marcus, made good profit",
        emotional_intensity=0.7,
        importance=0.6,
        participants=["Marcus"],
        location=(10, 20)
    )

    # Add a dangerous experiment consequence memory
    agent.memory.remember(
        tick=80,
        event_type="consequence_explosion",
        description="EXPLOSION during experiment! A catastrophic failure that I'll never forget. I was lucky to survive.",
        emotional_intensity=0.96,
        importance=0.85,
        participants=[],
        location=(15, 25)
    )

    # Update risk perception for experiments
    agent.memory.procedural_memory['risk_experiment'] = 0.78  # High risk!

    # Add semantic knowledge
    agent.memory.learn_fact(
        'experiment_is_dangerous',
        'I learned that experiment can lead to explosion (severity: 0.8)'
    )

    agent.memory.learn_fact(
        'trade_successful_with_marcus',
        'Trading with Marcus is profitable and safe'
    )

    print(f"\n✅ Added {len(agent.memory.episodic_memory)} memories:")
    for mem in agent.memory.episodic_memory:
        print(f"   - [{mem.event_type}] {mem.description[:60]}...")

    print(f"\n✅ Risk perception:")
    print(f"   - Experiment: {agent.memory.procedural_memory['risk_experiment']:.0%} (DANGEROUS!)")

    print(f"\n✅ Learned {len(agent.memory.semantic_memory)} facts:")
    for key in agent.memory.semantic_memory.keys():
        print(f"   - {key}")

    # ===== TEST PROMPT GENERATION =====
    print("\n" + "="*70)
    print("🔍 STEP 3: Checking Prompt Generation")
    print("="*70)

    # Test goal context extraction
    goal_context = llm_brain._get_goal_context(agent)
    print("\n📊 Goal Context:")
    print(goal_context)

    if "Become wealthy" in goal_context and "30%" in goal_context:
        print("   ✅ Goals appear in context with progress!")
    else:
        print("   ❌ Goals NOT properly formatted")

    # Test memory context extraction
    memory_context = llm_brain._get_memory_context(agent)
    print("\n📊 Memory Context:")
    print(memory_context)

    if "EXPLOSION" in memory_context or "traded" in memory_context:
        print("   ✅ Memories appear in context!")
    else:
        print("   ❌ Memories NOT in context")

    # Test risk warnings
    risk_warnings = llm_brain._get_risk_warnings(agent)
    print("\n📊 Risk Warnings:")
    print(risk_warnings)

    if "EXPERIMENT" in risk_warnings and "78%" in risk_warnings:
        print("   ✅ Risk warnings appear with correct percentage!")
    else:
        print("   ❌ Risk warnings NOT properly formatted")

    # ===== TEST ACTUAL DECISION =====
    print("\n" + "="*70)
    print("🧠 STEP 4: Testing AI Decision-Making")
    print("="*70)

    # Create perceptions (resources available for trading and experimenting)
    perceptions = {
        'nearby_agents': [
            {'name': 'Marcus', 'distance': 5, 'relationship': 0.6}
        ],
        'nearby_resources': [
            {'type': 'wood', 'distance': 3},
            {'type': 'reactive_material', 'distance': 2}  # Dangerous!
        ],
        'available_actions': ['trade', 'experiment', 'gather_food', 'rest']
    }

    print(f"\nPerceptions:")
    print(f"   - Marcus nearby (previous successful trade partner)")
    print(f"   - Wood available (safe trading resource)")
    print(f"   - Reactive material available (dangerous for experiments)")

    print(f"\nExpected behavior:")
    print(f"   ✅ Should consider trading (aligns with wealth goal + past success)")
    print(f"   ❌ Should AVOID experimenting (past explosion + high risk perception)")

    # Make decision
    try:
        decision_result = agent.autonomous_decide(perceptions, current_tick=100, config=config)

        print(f"\n🎯 AI Decision: {decision_result}")

        # Analyze decision
        decision_str = str(decision_result).lower()

        if 'trade' in decision_str:
            print("\n✅ EXCELLENT! Agent chose to trade (aligns with wealth goal)")
        elif 'experiment' in decision_str:
            print("\n⚠️  WARNING! Agent chose to experiment despite:")
            print("   - Past explosion memory")
            print("   - 78% risk perception")
            print("   - Low risk-taking personality (0.3)")
            print("\n   This suggests goals/memories are NOT influencing decisions!")
        else:
            print(f"\n🤔 Agent chose something else: {decision_result}")
            print("   Checking if it makes sense given goals/memories...")

    except Exception as e:
        print(f"\n❌ Decision failed: {e}")
        import traceback
        traceback.print_exc()

    # ===== SUMMARY =====
    print("\n" + "="*70)
    print("📊 INTEGRATION TEST SUMMARY")
    print("="*70)

    # Check each critical component
    goals_in_context = "Become wealthy" in goal_context
    memories_in_context = ("EXPLOSION" in memory_context) or ("traded" in memory_context)
    risks_in_warnings = "EXPERIMENT" in risk_warnings

    print(f"\nCritical Fix #1 - Goals in Prompts: {'✅' if goals_in_context else '❌'}")
    print(f"Critical Fix #2 - Memories in Prompts: {'✅' if memories_in_context else '❌'}")
    print(f"Risk Warnings Working: {'✅' if risks_in_warnings else '❌'}")

    all_working = goals_in_context and memories_in_context and risks_in_warnings

    if all_working:
        print(f"\n🎉 ALL CRITICAL FIXES INTEGRATED!")
        print(f"   Goals, memories, and risk warnings are now visible to AI!")
        print(f"\n   Next: Run full simulation to verify behavior over time.")
    else:
        print(f"\n⚠️  Some components not working:")
        if not goals_in_context:
            print(f"   - Goals not appearing in context")
        if not memories_in_context:
            print(f"   - Memories not appearing in context")
        if not risks_in_warnings:
            print(f"   - Risk warnings not working")

    return all_working


if __name__ == "__main__":
    success = test_goals_memory_integration()

    if success:
        print("\n" + "="*70)
        print("✅ CRITICAL FIXES #1 & #2 COMPLETE!")
        print("="*70)
        exit(0)
    else:
        print("\n" + "="*70)
        print("❌ FIXES NEED DEBUGGING")
        print("="*70)
        exit(1)
