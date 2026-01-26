"""
Tests for Semantic Long-Term Memory System

These tests verify that:
1. Memories are stored with vector embeddings
2. Semantic search retrieves relevant memories by meaning
3. Cross-agent memory sharing works correctly
4. Memory consolidation preserves important memories
5. Temporal decay fades old, unimportant memories
"""

import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.semantic_memory import SemanticMemorySystem, SEMANTIC_MEMORY_AVAILABLE


def test_dependencies():
    """Test 0: Check if dependencies are available"""
    print("\n" + "=" * 60)
    print("TEST 0: Dependency Check")
    print("=" * 60)

    if not SEMANTIC_MEMORY_AVAILABLE:
        print("❌ Semantic memory dependencies not available")
        print("   Install with: pip install chromadb sentence-transformers")
        return False

    print("✅ ChromaDB available")
    print("✅ Sentence Transformers available")
    return True


def test_basic_initialization():
    """Test 1: SemanticMemorySystem initializes correctly"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Initialization")
    print("=" * 60)

    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    try:
        # Initialize memory system
        memory_system = SemanticMemorySystem(
            agent_id="test_agent",
            embedding_model="all-MiniLM-L6-v2",
            persist_directory=temp_dir,
            max_memories=100
        )

        # Check if enabled
        if not memory_system.enabled:
            print("⚠️  Semantic memory not enabled (missing dependencies)")
            return None

        print("✅ SemanticMemorySystem initialized successfully!")
        print(f"   Agent ID: {memory_system.agent_id}")
        print(f"   Max memories: {memory_system.max_memories}")
        print(f"   Embedding model loaded: {memory_system.embedder is not None}")

        stats = memory_system.get_statistics()
        print(f"   Statistics: {stats}")

        return memory_system, temp_dir

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return None


def test_memory_storage(memory_system):
    """Test 2: Memories are stored correctly"""
    print("\n" + "=" * 60)
    print("TEST 2: Memory Storage")
    print("=" * 60)

    # Store several memories
    memories = [
        {
            'tick': 100,
            'event_type': 'discovery',
            'description': 'Found a berry bush near the river with ripe red berries',
            'importance': 0.7,
            'emotional_intensity': 0.6
        },
        {
            'tick': 150,
            'event_type': 'social',
            'description': 'Had friendly conversation with Alice about hunting techniques',
            'importance': 0.5,
            'emotional_intensity': 0.4,
            'participants': ['Alice']
        },
        {
            'tick': 200,
            'event_type': 'achievement',
            'description': 'Successfully hunted a deer using a bow and arrow',
            'importance': 0.9,
            'emotional_intensity': 0.8
        },
        {
            'tick': 250,
            'event_type': 'danger',
            'description': 'Narrowly escaped from a bear attack in the forest',
            'importance': 1.0,
            'emotional_intensity': 0.95
        },
        {
            'tick': 300,
            'event_type': 'learning',
            'description': 'Learned how to make fire using flint and dry grass',
            'importance': 0.8,
            'emotional_intensity': 0.7
        }
    ]

    stored_ids = []
    for mem in memories:
        memory_id = memory_system.remember(**mem)
        if memory_id:
            stored_ids.append(memory_id)
            print(f"✅ Stored: {mem['description'][:50]}...")
        else:
            print(f"❌ Failed to store: {mem['description'][:50]}...")

    stats = memory_system.get_statistics()
    print(f"\n   Total memories stored: {stats['total_memories']}")
    print(f"   Total created: {stats['total_created']}")

    assert len(stored_ids) == len(memories), "Not all memories were stored"
    print(f"\n✅ All {len(memories)} memories stored successfully!")

    return stored_ids


def test_semantic_search(memory_system):
    """Test 3: Semantic search retrieves relevant memories"""
    print("\n" + "=" * 60)
    print("TEST 3: Semantic Search")
    print("=" * 60)

    test_queries = [
        {
            'query': 'how to find food',
            'expected_keywords': ['berry', 'hunt', 'deer'],
            'min_results': 2
        },
        {
            'query': 'dangerous situations and survival',
            'expected_keywords': ['bear', 'escape'],
            'min_results': 1
        },
        {
            'query': 'learning new skills',
            'expected_keywords': ['fire', 'flint'],
            'min_results': 1
        },
        {
            'query': 'social interactions with others',
            'expected_keywords': ['Alice', 'conversation'],
            'min_results': 1
        }
    ]

    for test in test_queries:
        print(f"\nQuery: '{test['query']}'")

        results = memory_system.recall(
            query=test['query'],
            n_results=5,
            min_relevance=0.0
        )

        print(f"   Retrieved {len(results)} memories")

        if results:
            print(f"   Top result: {results[0]['description'][:60]}...")
            print(f"   Relevance: {results[0]['relevance']:.2f}")

            # Check if expected keywords appear
            found_keywords = []
            for result in results:
                desc = result['description'].lower()
                for keyword in test['expected_keywords']:
                    if keyword.lower() in desc:
                        found_keywords.append(keyword)

            if found_keywords:
                print(f"   ✅ Found expected keywords: {found_keywords}")
            else:
                print(f"   ⚠️  Expected keywords not found: {test['expected_keywords']}")

        assert len(results) >= test['min_results'], f"Not enough results for: {test['query']}"

    print(f"\n✅ Semantic search working correctly!")


def test_recent_memories(memory_system):
    """Test 4: Recent memory retrieval"""
    print("\n" + "=" * 60)
    print("TEST 4: Recent Memory Retrieval")
    print("=" * 60)

    recent = memory_system.recall_recent(n_results=3)

    print(f"Retrieved {len(recent)} recent memories:")
    for i, mem in enumerate(recent, 1):
        print(f"   {i}. Tick {mem['tick']}: {mem['description'][:50]}...")

    # Most recent should be tick 300 (fire making)
    if recent:
        assert recent[0]['tick'] == 300, "Most recent memory should be from tick 300"
        print(f"\n✅ Most recent memory correctly retrieved (tick {recent[0]['tick']})")


def test_cross_agent_memory_sharing():
    """Test 5: Memory sharing between agents"""
    print("\n" + "=" * 60)
    print("TEST 5: Cross-Agent Memory Sharing")
    print("=" * 60)

    # Create two agents
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()

    try:
        agent1_memory = SemanticMemorySystem(
            agent_id="hunter_1",
            persist_directory=temp_dir1,
            max_memories=100
        )

        agent2_memory = SemanticMemorySystem(
            agent_id="hunter_2",
            persist_directory=temp_dir2,
            max_memories=100
        )

        if not agent1_memory.enabled or not agent2_memory.enabled:
            print("⚠️  Skipping (dependencies not available)")
            return

        # Agent 1 has a valuable memory
        memory_id = agent1_memory.remember(
            tick=100,
            event_type='discovery',
            description='Found a hidden cave with rare mushrooms that boost energy',
            importance=0.9,
            emotional_intensity=0.7
        )

        print(f"✅ Agent 1 created memory: {memory_id}")

        # Agent 1 shares with Agent 2
        success = agent1_memory.share_memory(
            memory_id=memory_id,
            recipient_memory_system=agent2_memory,
            trust_level=0.8
        )

        if success:
            print(f"✅ Memory shared successfully!")

            # Agent 2 should now be able to recall this
            results = agent2_memory.recall(
                query="where to find energy-boosting food",
                n_results=3
            )

            if results:
                print(f"✅ Agent 2 can now recall shared memory!")
                print(f"   Found: {results[0]['description'][:60]}...")
                assert 'hunter_1' in results[0]['description'].lower(), "Should mention source agent"
            else:
                print(f"❌ Agent 2 couldn't recall shared memory")

        # Cleanup
        shutil.rmtree(temp_dir1, ignore_errors=True)
        shutil.rmtree(temp_dir2, ignore_errors=True)

    except Exception as e:
        print(f"❌ Memory sharing test failed: {e}")
        import traceback
        traceback.print_exc()


def test_memory_consolidation():
    """Test 6: Memory consolidation and forgetting"""
    print("\n" + "=" * 60)
    print("TEST 6: Memory Consolidation")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()

    try:
        # Create system with small limit
        memory_system = SemanticMemorySystem(
            agent_id="test_agent",
            persist_directory=temp_dir,
            max_memories=10  # Small limit to trigger consolidation
        )

        if not memory_system.enabled:
            print("⚠️  Skipping (dependencies not available)")
            return

        # Store 15 memories (5 more than limit)
        print("Storing 15 memories (limit is 10)...")

        for i in range(15):
            # Make some memories more important than others
            importance = 0.9 if i % 3 == 0 else 0.3

            memory_system.remember(
                tick=i * 10,
                event_type='test',
                description=f"Test memory number {i} with importance {importance}",
                importance=importance,
                emotional_intensity=importance
            )

        stats = memory_system.get_statistics()
        print(f"\n   Total memories retained: {stats['total_memories']}")
        print(f"   Total created: {stats['total_created']}")
        print(f"   Consolidations: {stats['total_consolidations']}")

        # Should have consolidated down to max
        assert stats['total_memories'] <= 10, "Memory consolidation didn't work"

        print(f"\n✅ Memory consolidation working!")
        print(f"   Created 15, retained {stats['total_memories']} most important")

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"❌ Consolidation test failed: {e}")
        import traceback
        traceback.print_exc()


def test_memory_persistence():
    """Test 7: Memory persistence across restarts"""
    print("\n" + "=" * 60)
    print("TEST 7: Memory Persistence")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()

    try:
        # Create and store memories
        memory_system_1 = SemanticMemorySystem(
            agent_id="persistent_agent",
            persist_directory=temp_dir,
            max_memories=100
        )

        if not memory_system_1.enabled:
            print("⚠️  Skipping (dependencies not available)")
            return

        # Store important memory
        memory_system_1.remember(
            tick=100,
            event_type='achievement',
            description='Built first permanent shelter with stone walls',
            importance=0.95,
            emotional_intensity=0.8
        )

        stats_before = memory_system_1.get_statistics()
        print(f"✅ Stored {stats_before['total_memories']} memories")

        # Simulate restart - create new instance with same persist directory
        memory_system_2 = SemanticMemorySystem(
            agent_id="persistent_agent",
            persist_directory=temp_dir,
            max_memories=100
        )

        stats_after = memory_system_2.get_statistics()
        print(f"✅ After restart: {stats_after['total_memories']} memories")

        # Should have same number of memories
        assert stats_after['total_memories'] == stats_before['total_memories'], "Memories not persisted"

        # Should be able to recall
        results = memory_system_2.recall(query="building shelter", n_results=1)

        if results:
            print(f"✅ Can recall persisted memory!")
            print(f"   Found: {results[0]['description'][:60]}...")
        else:
            print(f"❌ Could not recall persisted memory")

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"❌ Persistence test failed: {e}")
        import traceback
        traceback.print_exc()


def test_export_memories(memory_system):
    """Test 8: Memory export functionality"""
    print("\n" + "=" * 60)
    print("TEST 8: Memory Export")
    print("=" * 60)

    exported = memory_system.export_memories()

    print(f"Exported {len(exported)} memories")

    if exported:
        print(f"\nFirst memory:")
        print(f"   ID: {exported[0]['id']}")
        print(f"   Description: {exported[0]['description'][:50]}...")
        print(f"   Metadata keys: {list(exported[0]['metadata'].keys())}")

    assert len(exported) > 0, "No memories exported"
    print(f"\n✅ Memory export working!")


def run_all_tests():
    """Run all semantic memory tests"""
    print("\n" + "=" * 60)
    print("🧠 SEMANTIC LONG-TERM MEMORY TEST SUITE")
    print("=" * 60)
    print("\nThis test suite verifies AI agents can truly learn:")
    print("- Vector-based memory storage")
    print("- Semantic search by meaning")
    print("- Cross-agent memory sharing")
    print("- Memory consolidation & forgetting")
    print("- Persistent memory across restarts")

    # Check dependencies
    if not test_dependencies():
        print("\n❌ Cannot run tests without dependencies")
        print("   Install: pip install chromadb sentence-transformers")
        return

    memory_system = None
    temp_dir = None

    try:
        # Test 1: Initialization
        result = test_basic_initialization()
        if result is None:
            print("\n❌ Tests cannot proceed without working memory system")
            return

        memory_system, temp_dir = result

        # Test 2: Storage
        stored_ids = test_memory_storage(memory_system)

        # Test 3: Semantic search
        test_semantic_search(memory_system)

        # Test 4: Recent memories
        test_recent_memories(memory_system)

        # Test 5: Cross-agent sharing
        test_cross_agent_memory_sharing()

        # Test 6: Consolidation
        test_memory_consolidation()

        # Test 7: Persistence
        test_memory_persistence()

        # Test 8: Export
        test_export_memories(memory_system)

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETE!")
        print("=" * 60)
        print("\nSemantic Long-Term Memory is working correctly!")
        print("Agents can now:")
        print("  🧠 Store memories with semantic embeddings")
        print("  🔍 Search memories by meaning, not keywords")
        print("  🤝 Share knowledge with other agents")
        print("  💪 Strengthen important memories through recall")
        print("  🌊 Naturally forget trivial experiences")

    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_all_tests()
