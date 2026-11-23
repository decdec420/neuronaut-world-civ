"""
Saves (engine/save_manager.py): unique ids, one index shared safely, a
damaged index doesn't stop the server, and autosaves are loadable and kept
to AUTOSAVE_KEEP.

    python3 -m pytest tests/test_saves.py -q
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world, quiet  # noqa: E402

SUMMARY = {"world": {"time": {"current_day": 3}, "total_agents": 2, "alive_agents": 2}}


def test_two_saves_in_the_same_second_are_two_saves(tmp_path):
    from engine.save_manager import SaveManager
    m = SaveManager(tmp_path)
    m.create_save("Same", SUMMARY)
    m.create_save("Same", SUMMARY)
    saves = m.list_saves()
    assert len(saves) == 2 and saves[0]["id"] != saves[1]["id"]
    assert saves[0]["filename"] != saves[1]["filename"]
    assert m.delete_save(saves[0]["id"]) and len(m.list_saves()) == 1


def test_two_managers_share_one_index(tmp_path):
    # the server and the engine's autosave each hold a SaveManager
    from engine.save_manager import SaveManager
    server, engine = SaveManager(tmp_path), SaveManager(tmp_path)
    server.create_save("Mine", SUMMARY)
    engine.create_save("Autosave", SUMMARY, autosave=True)
    server.create_save("Mine again", SUMMARY)       # used to drop the autosave's entry
    names = sorted(s["name"] for s in SaveManager(tmp_path).list_saves())
    assert names == ["Autosave", "Mine", "Mine again"]


def test_a_damaged_index_is_set_aside(tmp_path):
    from engine.save_manager import SaveManager
    (tmp_path / "saves_metadata.json").write_text("{ not json")
    m = SaveManager(tmp_path)
    assert m.list_saves() == []
    assert m.create_save("Fresh", SUMMARY)
    assert [s["name"] for s in m.list_saves()] == ["Fresh"]
    assert any(p.name.startswith("saves_metadata.corrupt-") for p in tmp_path.iterdir())


def test_autosaves_are_loadable_and_only_the_newest_are_kept(tmp_path):
    from engine.save_manager import SaveManager
    from engine.persistence import load_full_state
    sim, _ = make_world()
    m = SaveManager(tmp_path)
    m.create_save("My world", SUMMARY)                              # a save you made
    m.metadata["saves"].append({"id": "old", "name": "AutoSave - Day 2 10:00:00", "filename": "gone.json.gz",
                                "created_at": "20000101_000000", "last_played": "20000101_000000"})
    m._save_metadata()                                              # an old dashboard autosave
    for _ in range(4):
        m.auto_save(sim.persistence.create_snapshot(), simulation=sim, keep=2)
    saves = m.list_saves()
    autos = [s for s in saves if m._is_autosave(s)]
    assert len(autos) == 2 and all(s["autosave"] for s in autos)   # the old one went too
    assert any(s["name"] == "My world" for s in saves)               # yours stays
    loaded = load_full_state(str(m.state_path(autos[0]["id"])))
    assert len(loaded.world.agents) == len(sim.world.agents)
    files = {p.name for p in tmp_path.iterdir()}
    assert sum(1 for f in files if f.endswith(".state.gz")) == 2     # no files left behind


def test_the_running_world_autosaves_where_saves_go(tmp_path):
    from engine.save_manager import SaveManager
    sim, _ = make_world()
    sim.config.autosave_every, sim.config.autosave_keep, sim.config.save_dir = 5, 2, tmp_path

    async def go():
        for _ in range(16):
            await sim.tick()
    with quiet():
        asyncio.run(go())
    autos = SaveManager(tmp_path).list_saves()
    assert len(autos) == 2 and all(a["autosave"] and a["state_filename"] for a in autos)
