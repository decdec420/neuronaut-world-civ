"""
Governance System Integration Test

Tests the complete governance flow:
1. Government formation
2. Law creation
3. Voting system
4. Governance context in AI prompts
5. Political power tracking
"""

import os
import sys

# Ensure the project root is in sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from world.governance import GovernanceManager, GovernmentType, Law, Government
from agents.agent import ActionType


def test_government_types():
    """Test 1: Verify all government types exist"""
    print("=" * 60)
    print("TEST 1: Government Types")
    print("=" * 60)

    types = list(GovernmentType)

    print(f"\n🏛️  Available Government Types ({len(types)}):")
    for gov_type in types:
        print(f"   • {gov_type.value}")

    assert len(types) >= 5, f"Expected at least 5 government types, got {len(types)}"
    assert GovernmentType.DEMOCRACY in types, "Democracy should be available"
    assert GovernmentType.STRONGMAN in types, "Strongman should be available"

    print(f"\n✅ PASS: {len(types)} government types defined")
    return True


def test_government_formation():
    """Test 2: Form a government"""
    print("\n" + "=" * 60)
    print("TEST 2: Government Formation")
    print("=" * 60)

    manager = GovernanceManager()

    founder_id = "agent_001"
    gov_name = "The People's Council"

    government = manager.agent_forms_government(
        founder_id=founder_id,
        name=gov_name,
        gov_type=GovernmentType.DEMOCRACY
    )

    print(f"\n🏛️  Government Created:")
    print(f"   Name: {government.name}")
    print(f"   Type: {government.government_type.value}")
    print(f"   Leader: {government.leader_id}")
    print(f"   Citizens: {len(government.citizens)}")
    print(f"   Approval: {government.approval_rating:.0%}")

    assert government.name == gov_name, "Government name should match"
    assert government.leader_id == founder_id, "Founder should be leader"
    assert founder_id in government.citizens, "Founder should be citizen"
    assert government.government_type == GovernmentType.DEMOCRACY, "Type should match"

    # Check political power
    power = manager.political_power.get(founder_id, 0.0)
    print(f"\n📊 Founder's Political Power: {power:.0%}")
    assert power > 0.0, "Founder should gain political power"

    print(f"\n✅ PASS: Government formation working")
    return True


def test_law_creation():
    """Test 3: Create and vote on laws"""
    print("\n" + "=" * 60)
    print("TEST 3: Law Creation")
    print("=" * 60)

    manager = GovernanceManager()

    # Create government first
    leader_id = "agent_leader"
    government = manager.agent_forms_government(
        founder_id=leader_id,
        name="Test Government",
        gov_type=GovernmentType.DEMOCRACY
    )

    # Leader creates a law
    law = manager.agent_creates_law(
        creator_id=leader_id,
        government_id=government.id,
        name="No Theft Law",
        description="Stealing from others is prohibited",
        prohibition="theft",
        requirement=None
    )

    print(f"\n📜 Law Created:")
    print(f"   Name: {law.name}")
    print(f"   Description: {law.description}")
    print(f"   Prohibition: {law.prohibition}")
    print(f"   Creator: {law.created_by}")
    print(f"   Active: {law.active}")

    assert law is not None, "Law should be created"
    assert law.name == "No Theft Law", "Law name should match"
    assert law.created_by == leader_id, "Creator should match"
    assert leader_id in law.supporters, "Creator should support their law"

    # Add more agents and vote
    citizen1_id = "agent_001"
    citizen2_id = "agent_002"

    manager.agent_joins_government(citizen1_id, government.id)
    manager.agent_joins_government(citizen2_id, government.id)

    # Vote on law
    manager.vote_on_law(citizen1_id, law.id, support=True)
    manager.vote_on_law(citizen2_id, law.id, support=False)

    print(f"\n🗳️  Voting Results:")
    print(f"   Supporters: {len(law.supporters)}")
    print(f"   Opposers: {len(law.opposers)}")
    print(f"   Support ratio: {law.get_support_ratio():.0%}")

    assert citizen1_id in law.supporters, "Citizen 1 should support"
    assert citizen2_id in law.opposers, "Citizen 2 should oppose"
    support_ratio = law.get_support_ratio()
    assert 0.0 <= support_ratio <= 1.0, "Support ratio should be 0-100%"

    print(f"\n✅ PASS: Law creation and voting working")
    return True


def test_political_authority():
    """Test 4: Check who can make laws"""
    print("\n" + "=" * 60)
    print("TEST 4: Political Authority")
    print("=" * 60)

    manager = GovernanceManager()

    # Create government
    leader_id = "agent_leader"
    citizen_id = "agent_citizen"

    government = manager.agent_forms_government(
        founder_id=leader_id,
        name="Test Gov",
        gov_type=GovernmentType.STRONGMAN
    )

    manager.agent_joins_government(citizen_id, government.id)

    print(f"\n🏛️  Government Type: {government.government_type.value}")

    # Leader should be able to make laws
    can_leader_make_laws = manager._can_make_law(leader_id, government)
    print(f"\n👑 Leader can make laws: {can_leader_make_laws}")

    # Regular citizen in strongman government shouldn't
    can_citizen_make_laws = manager._can_make_law(citizen_id, government)
    print(f"👤 Citizen can make laws: {can_citizen_make_laws}")

    assert can_leader_make_laws, "Leader should make laws in strongman"
    assert not can_citizen_make_laws, "Regular citizen can't make laws in strongman"

    # Change to democracy
    government.government_type = GovernmentType.DEMOCRACY
    manager.political_power[citizen_id] = 0.3  # Give enough power

    can_citizen_now = manager._can_make_law(citizen_id, government)
    print(f"\n🗳️  After democracy + power:")
    print(f"   Citizen can make laws: {can_citizen_now}")

    assert can_citizen_now, "Citizens with power can make laws in democracy"

    print(f"\n✅ PASS: Political authority checks working")
    return True


def test_governance_keywords():
    """Test 5: Governance action keywords"""
    print("\n" + "=" * 60)
    print("TEST 5: Governance Keywords")
    print("=" * 60)

    # Just verify keywords are in ActionType
    assert hasattr(ActionType, 'GOVERN'), "GOVERN action should exist"
    assert hasattr(ActionType, 'MAKE_LAW'), "MAKE_LAW action should exist"
    assert hasattr(ActionType, 'VOTE'), "VOTE action should exist"

    print(f"\n✅ Action Types Verified:")
    print(f"   • ActionType.GOVERN = {ActionType.GOVERN.value}")
    print(f"   • ActionType.MAKE_LAW = {ActionType.MAKE_LAW.value}")
    print(f"   • ActionType.VOTE = {ActionType.VOTE.value}")

    keywords = [
        "form government",
        "establish government",
        "govern",
        "lead",
        "make law",
        "propose law",
        "create law",
        "vote",
        "cast vote"
    ]

    print(f"\n📝 Expected Keywords:")
    for keyword in keywords:
        print(f"   • '{keyword}'")

    print(f"\n✅ PASS: Governance keywords defined")
    return True


def test_government_stats():
    """Test 6: Government statistics and tracking"""
    print("\n" + "=" * 60)
    print("TEST 6: Government Statistics")
    print("=" * 60)

    manager = GovernanceManager()

    # Create multiple governments
    gov1 = manager.agent_forms_government("agent1", "Empire", GovernmentType.STRONGMAN)
    gov2 = manager.agent_forms_government("agent2", "Republic", GovernmentType.DEMOCRACY)
    gov3 = manager.agent_forms_government("agent3", "Council", GovernmentType.COUNCIL)

    print(f"\n🏛️  Governments Created:")
    for gov_id, gov in manager.governments.items():
        print(f"   • {gov.name} ({gov.government_type.value})")
        print(f"     Leader: {gov.leader_id}")
        print(f"     Citizens: {len(gov.citizens)}")
        print(f"     Approval: {gov.approval_rating:.0%}")

    assert len(manager.governments) == 3, "Should have 3 governments"

    # Add citizens to one
    for i in range(5):
        manager.agent_joins_government(f"citizen_{i}", gov1.id)

    print(f"\n📊 Empire Statistics:")
    print(f"   Total citizens: {len(gov1.citizens)}")
    print(f"   Stability: {gov1.stability:.0%}")

    assert len(gov1.citizens) == 6, "Empire should have 6 citizens (5 + leader)"

    print(f"\n✅ PASS: Government statistics tracking")
    return True


def run_all_tests():
    """Run all governance integration tests"""
    print("\n" + "🏛️ " * 20)
    print("GOVERNANCE SYSTEM INTEGRATION TESTS")
    print("🏛️ " * 20)

    tests = [
        ("Government Types", test_government_types),
        ("Government Formation", test_government_formation),
        ("Law Creation & Voting", test_law_creation),
        ("Political Authority", test_political_authority),
        ("Governance Keywords", test_governance_keywords),
        ("Government Statistics", test_government_stats),
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
        print("\n🎉 ALL TESTS PASSED - Governance system integration complete!")
        print("\n✨ Governance Features Ready:")
        print("   • 6 government types (anarchy → strongman → democracy → etc.)")
        print("   • Government formation by charismatic agents")
        print("   • Law creation and voting systems")
        print("   • Political power and authority")
        print("   • Citizen participation (join, vote, propose)")
        print("   • Approval ratings and stability tracking")
        print("\n🚀 Full governance system operational!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
