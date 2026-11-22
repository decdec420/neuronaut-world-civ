"""
Long runs stay bounded: what grew every tick now has a cap.

Each cap here was found by measuring a 6,000-tick run (container sizes at
ticks 1,000 / 3,000 / 6,000). The memory stream's own bound is tested in
test_memory_stream.py.

    python3 -m pytest tests/test_bounded.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_finished_games_leave_the_active_list():
    from world.fun_system import FunSystem
    fun = FunSystem()
    for _ in range(5):
        game = fun.start_dice_game([("a", "Ann"), ("b", "Bob")], stakes=1.0)
        fun.resolve_dice_game(game)
    assert fun.active_games == {} and len(fun.game_history) == 5
    fun.HISTORY_LIMIT = 3
    fun.resolve_dice_game(fun.start_dice_game([("a", "Ann"), ("b", "Bob")], stakes=1.0))
    assert len(fun.game_history) == 3


def test_trespass_log_keeps_recent_incidents_and_counts_them_all():
    from world.territory import TerritoryManager, TerritoryType
    land = TerritoryManager()
    land.claim_territory("owner", "Ann", (50.0, 50.0), 10.0, list(TerritoryType)[0], 0)
    for tick in range(2000):
        land.check_trespassing("intruder", (50.0, 50.0), tick)
    assert len(land.trespass_events) <= land.MAX_TRESPASS_EVENTS * 1.2
    assert land.total_trespasses == 2000


def test_old_memory_system_is_capped():
    from engine.smart_memory import SmartMemorySystem, EventImportance
    memory = SmartMemorySystem("agent")
    for i in range(1000):
        memory.add_memory(f"minor thing {i}", EventImportance.MINOR)
        memory.add_memory(f"major thing {i}", EventImportance.MAJOR)
    assert len(memory.episodic_memory) <= memory.MAX_EPISODIC * 1.2
    assert len(memory.persistent_memories) == memory.MAX_PERSISTENT
    assert memory.persistent_memories[-1].content == "major thing 999"


def test_path_cache_is_capped():
    from agents.pathfinding import Pathfinder
    finder = Pathfinder(100, 100)
    finder.MAX_CACHED_PATHS = 10
    for i in range(30):
        finder.find_path(0, 0, 5 + i % 20, 3 + i // 20)
    assert 0 < len(finder.path_cache) <= 10


def test_autosaves_on_disk_are_pruned(tmp_path):
    from test_reachability import make_world
    from engine.persistence import PersistenceEngine
    sim, _ = make_world()
    persistence = PersistenceEngine(save_directory=str(tmp_path))
    persistence.keep_last_n_snapshots = 3
    for i in range(3):  # left over from an earlier run
        (tmp_path / f"snapshot_tick_{i}_old.json.gz").write_bytes(b"")
    for i in range(4):
        persistence.save_simulation_state(sim, snapshot_name=f"snapshot_tick_{1000 + i}")
    left = sorted(p.name for p in tmp_path.iterdir() if p.name.startswith("snapshot_tick_"))
    assert len(left) == 3 and all("_old" not in name for name in left)


def test_fun_stats_are_counted_as_they_happen():
    from world.fun_system import FunSystem
    fun = FunSystem()
    fun.HISTORY_LIMIT = 2
    for _ in range(4):
        game = fun.start_dice_game([("a", "Ann"), ("b", "Bob")], stakes=1.0)
        fun.resolve_dice_game(game)
    stats = fun.get_agent_fun_stats("a")
    assert stats["games_played"] == 4  # exact, though only 2 games are kept in the history
    assert fun.get_agent_fun_stats("a")["games_won"] + fun.get_agent_fun_stats("b")["games_won"] == 4
