"""
Semantic long-term memory (agents/semantic_memory.py): memories stored as
embeddings and recalled by meaning.

    python3 -m pytest tests/test_semantic_memory.py -q

It needs chromadb and sentence-transformers (not in requirements-minimal.txt).
Without them the system switches itself off, and that path is always tested
here. The tests that need the packages are skipped when they aren't
installed. (This file used to be a script: its tests needed a
`memory_system` fixture that didn't exist, so pytest errored on them.)
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import semantic_memory  # noqa: E402
from agents.semantic_memory import SemanticMemorySystem, SEMANTIC_MEMORY_AVAILABLE  # noqa: E402

needs_packages = pytest.mark.skipif(not SEMANTIC_MEMORY_AVAILABLE,
                                    reason="needs chromadb and sentence-transformers")

MEMORIES = [
    dict(tick=100, event_type='discovery', description='Found a berry bush near the river with ripe red berries',
         importance=0.7, emotional_intensity=0.6),
    dict(tick=150, event_type='social', description='Had friendly conversation with Alice about hunting techniques',
         importance=0.5, emotional_intensity=0.4, participants=['Alice']),
    dict(tick=200, event_type='achievement', description='Successfully hunted a deer using a bow and arrow',
         importance=0.9, emotional_intensity=0.8),
    dict(tick=250, event_type='danger', description='Narrowly escaped from a bear attack in the forest',
         importance=1.0, emotional_intensity=0.95),
    dict(tick=300, event_type='learning', description='Learned how to make fire using flint and dry grass',
         importance=0.8, emotional_intensity=0.7),
]


def test_without_its_packages_it_switches_off_and_does_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(semantic_memory, "SEMANTIC_MEMORY_AVAILABLE", False)
    m = SemanticMemorySystem(agent_id="a1", persist_directory=str(tmp_path), max_memories=100)
    other = SemanticMemorySystem(agent_id="a2", persist_directory=str(tmp_path), max_memories=100)
    assert m.enabled is False
    assert m.remember(**MEMORIES[0]) is None
    assert m.recall("food") == [] and m.recall_recent(3) == [] and m.export_memories() == []
    assert not m.share_memory("x", other)
    assert m.get_statistics()["enabled"] is False
    m.clear_all_memories()                    # a no-op, not an error
    assert list(tmp_path.iterdir()) == []     # and it wrote nothing


@pytest.fixture()
def memory_system(tmp_path):
    m = SemanticMemorySystem(agent_id="test_agent", embedding_model="all-MiniLM-L6-v2",
                             persist_directory=str(tmp_path), max_memories=100)
    assert m.enabled
    for mem in MEMORIES:
        assert m.remember(**mem)
    return m


@needs_packages
@pytest.mark.parametrize("query, keywords", [
    ("how to find food", ["berry", "hunt", "deer"]),
    ("dangerous situations and survival", ["bear", "escape"]),
    ("learning new skills", ["fire", "flint"]),
    ("social interactions with others", ["alice", "conversation"]),
])
def test_recall_finds_memories_by_meaning(memory_system, query, keywords):
    results = memory_system.recall(query=query, n_results=5, min_relevance=0.0)
    assert results
    top = results[0]["description"].lower()
    assert any(k in top for k in keywords), f"{query!r} recalled {top!r} first"


@needs_packages
def test_recent_memories_come_newest_first(memory_system):
    recent = memory_system.recall_recent(n_results=3)
    assert [r["tick"] for r in recent][:1] == [300]


@needs_packages
def test_memories_can_be_exported(memory_system):
    assert len(memory_system.export_memories()) == len(MEMORIES)
