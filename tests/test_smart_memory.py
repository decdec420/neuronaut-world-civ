"""
Smart memory runs on sim time (engine/smart_memory.py): a memory fades with
the hours an agent lives, not with how long the server has been up.

    python3 -m pytest tests/test_smart_memory.py -q
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.smart_memory import EventImportance, SmartMemorySystem, TICKS_PER_HOUR  # noqa: E402


def test_a_minor_memory_fades_after_enough_sim_hours_however_fast_the_server_runs():
    m = SmartMemorySystem("a1")
    m.add_memory("traded a fish", EventImportance.MINOR)
    m.add_memory("built a hut", EventImportance.MAJOR)
    m.clock = 200 * TICKS_PER_HOUR            # 200 sim hours later: still there
    m.decay_memories()
    assert [x.content for x in m.episodic_memory] == ["traded a fish"]
    m.clock = 400 * TICKS_PER_HOUR            # 400 hours: 0.995^400 * 0.4 < 0.1, gone
    m.decay_memories()
    assert m.episodic_memory == [] and m.total_memories_decayed == 1
    assert [x.content for x in m.persistent_memories] == ["built a hut"]   # major ones stay


def test_decay_runs_once_a_sim_hour():
    m = SmartMemorySystem("a1")
    m.add_memory("x", EventImportance.MINOR)
    m.clock = 10_000
    m.decay_memories()
    m.add_memory("y", EventImportance.MINOR)   # stamped at 10_000
    m.clock = 10_000 + TICKS_PER_HOUR - 1
    before = m.total_memories_decayed
    m.decay_memories()                         # too soon: nothing happens
    assert m.total_memories_decayed == before


def test_a_save_from_the_wall_clock_days_starts_counting_from_now():
    m = SmartMemorySystem("a1")
    m.add_memory("old", EventImportance.MINOR)
    m.episodic_memory[0].timestamp = time.time()   # how saves stored it
    m.last_cleanup_time = time.time()
    m.clock = 50
    m.decay_memories()
    assert m.episodic_memory[0].timestamp == 50 and m.last_cleanup_time == 50
    m.clock = 50 + 400 * TICKS_PER_HOUR
    m.decay_memories()
    assert m.episodic_memory == []


def test_an_agent_sets_its_memory_clock():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_reachability import make_world
    sim, roles = make_world()
    agent = roles["actor"]
    for _ in range(7):
        agent.update()
    assert agent.memory.clock == agent.ticks_lived > 0
