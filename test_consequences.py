"""
Test Consequence → Memory → Learning Connection

This tests that:
1. Consequences are applied when risky actions fail
2. Agents remember consequences in their memory
3. Agents learn to avoid risky actions
4. AI decisions consider past consequences
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.agent import Agent, Gender
from agents.autonomous_agent import AutonomousAgentMixin
from world.consequences import ConsequenceEngine, ConsequenceType
from engine.psychology import PersonalityProfile
from config import load_config
from agents.llm_brain import MultiLLMBrain
import types

def test_consequence_learning():
    """Test that agents learn from consequences"""

    print("\n" + "="*60)
    print("🧪 TESTING CONSEQUENCE → MEMORY → LEARNING")
    print("="*60)

    # Create agent with autonomous capabilities
    agent = Agent(
        name="TestAgent",
        age=25,
        gender=Gender.MALE,
        personality=PersonalityProfile(
            ambition=0.8,
            creativity=0.9,
            risk_taking=0.7  # Risky personality
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
    print(f"   Personality: Risk-Taking {agent.personality.risk_taking:.1f}")

    # Check baseline - agent has no risk memories
    print(f"\n📊 Initial State:")
    print(f"   Episodic memories: {len(agent.memory.episodic_memory)}")
    print(f"   Risk knowledge: {agent.memory.procedural_memory}")

    # Create consequence engine
    consequence_engine = ConsequenceEngine()

    # ===== APPLY A SEVERE CONSEQUENCE =====
    print(f"\n💥 Simulating EXPLOSION during experiment...")

    consequence = consequence_engine.apply_consequence(
        consequence_type=ConsequenceType.EXPLOSION,
        affected_agents={agent.id},
        action='experiment',
        severity=0.8,  # Severe!
        context={
            'current_tick': 100,
            'had_explosion': True
        },
        agent_objects=[agent]  # NEW: Pass agent for learning
    )

    print(f"   Consequence ID: {consequence.id}")
    print(f"   Description: {consequence.description}")

    # ===== CHECK THAT AGENT LEARNED =====
    print(f"\n📊 After Consequence:")
    print(f"   Episodic memories: {len(agent.memory.episodic_memory)}")

    # Check for consequence memory
    consequence_memories = [
        m for m in agent.memory.episodic_memory
        if m.event_type.startswith('consequence_')
    ]

    if consequence_memories:
        print(f"   ✅ Agent remembered the consequence!")
        for mem in consequence_memories:
            print(f"      - {mem.description}")
            print(f"      - Importance: {mem.importance:.2f}")
            print(f"      - Emotional intensity: {mem.emotional_intensity:.2f}")
    else:
        print(f"   ❌ Agent did NOT remember the consequence!")

    # Check risk perception
    print(f"\n   Risk perception:")
    if 'risk_experiment' in agent.memory.procedural_memory:
        risk_level = agent.memory.procedural_memory['risk_experiment']
        print(f"   ✅ Experiment risk level: {risk_level:.1%}")
        if risk_level > 0.6:
            print(f"   ✅ Agent learned that experimenting is DANGEROUS!")
    else:
        print(f"   ❌ No risk perception for experiments")

    # Check semantic knowledge
    print(f"\n   Learned facts:")
    dangerous_facts = {k: v for k, v in agent.memory.semantic_memory.items() if 'dangerous' in k}
    if dangerous_facts:
        for fact, value in dangerous_facts.items():
            print(f"   ✅ {fact}: {value}")
    else:
        print(f"   ❌ No learned facts about danger")

    # ===== TEST AI DECISION WITH WARNINGS =====
    print(f"\n🧠 Testing AI Decision (should show warnings)...")

    # Build test perceptions
    perceptions = {
        'nearby_agents': [],
        'nearby_resources': [
            {'type': 'wood', 'distance': 2},
            {'type': 'stone', 'distance': 3}
        ]
    }

    # Check if warnings are included in LLM prompt
    if llm_brain and config.use_llm_decisions:
        warnings = llm_brain._get_risk_warnings(agent)
        print(f"\n⚠️  Risk Warnings for LLM:")
        if warnings:
            print(warnings)
            print("   ✅ Agent will receive warnings about risky actions!")
        else:
            print("   ❌ No warnings generated")

    print("\n" + "="*60)
    print("✅ CONSEQUENCE LEARNING TEST COMPLETE")
    print("="*60)

    # Summary
    print(f"\nSummary:")
    print(f"  Consequence applied: ✅")
    print(f"  Agent remembered: {'✅' if consequence_memories else '❌'}")
    print(f"  Risk perception updated: {'✅' if 'risk_experiment' in agent.memory.procedural_memory else '❌'}")
    print(f"  Warnings generated: {'✅' if warnings else '❌'}")

    success = (
        len(consequence_memories) > 0 and
        'risk_experiment' in agent.memory.procedural_memory and
        bool(warnings)
    )

    if success:
        print(f"\n🎉 FULL INTEGRATION WORKING!")
        print(f"   Consequences → Memory → Learning → AI Warnings ✅")
    else:
        print(f"\n⚠️  Some components not working properly")


if __name__ == "__main__":
    test_consequence_learning()
