"""
Save, load, carry on: a saved world comes back exactly as it was.

    python3 -m pytest tests/test_persistence.py -q
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act, befriend  # noqa: E402
from test_reachability import quiet  # noqa: E402


def run(sim, ticks):
    async def go():
        for _ in range(ticks):
            await sim.tick()
    with quiet():
        asyncio.run(go())


def fingerprint(sim) -> dict:
    """What a save must keep: agents, relationships, buildings, governments,
    religions, money, time."""
    gm, rel = sim.governance_manager, sim.religion
    return {
        "tick": sim.world.time.current_tick,
        "agents": sorted((a.id, a.name, a.alive, round(a.health, 6), round(a.location.x, 6), round(a.location.y, 6),
                          round(a.wealth, 6), a.age, a.partner_id, a.life_stage, a.death_cause,
                          tuple(sorted(a.inventory.items.items())), len(a.memory_stream.records))
                         for a in sim.world.agents),
        "relationships": sorted((r.agent_a, r.agent_b, r.relationship_type.value, round(r.strength, 6))
                                for r in sim.relationship_manager.relationships.values()),
        # By name and place: ids of buildings started after a save come from
        # uuid4 (not the world's dice), so they differ between two runs
        "buildings": sorted((b.name, round(b.location[0], 6), round(b.location[1], 6), b.is_complete,
                             b.collapsed, round(b.durability, 6))
                            for b in sim.dynamic_building_system.buildings.values()),
        "governments": sorted((g.id, g.leader_id, tuple(sorted(g.citizens))) for g in gm.governments.values()),
        "laws": sorted((law.id, law.active) for law in gm.laws.values()),
        "religions": sorted((r.id, tuple(sorted(r.followers))) for r in rel.religions.values()),
        "money": round(sum(a.wealth for a in sim.world.agents), 6),
        "life_events": dict(sim.life_events),
    }


def test_save_load_and_carry_on(tmp_path):
    from test_reachability import make_world
    from engine.persistence import save_full_state, load_full_state
    sim, roles = make_world()
    a, b, c = roles["actor"], roles["neighbour"], roles["sick"]
    # Something of everything: a government with a law, a faith, money
    a.personality.aggression = 0.1
    act(sim, a, "govern")
    befriend(sim, b, a)
    act(sim, b, "govern")
    act(sim, a, "make_law", details="no fighting")
    act(sim, c, "worship")
    run(sim, 40)

    path = str(tmp_path / "world.state.gz")
    save_full_state(sim, path)
    saved = fingerprint(sim)
    saved_building_ids = set(sim.dynamic_building_system.buildings)
    assert saved["governments"] and saved["laws"] and saved["religions"] and saved["relationships"]

    # The original carries on...
    run(sim, 30)
    carried_on = fingerprint(sim)

    # ...and so does the loaded copy, from the same point
    loaded = load_full_state(path)
    assert fingerprint(loaded) == saved
    assert set(loaded.dynamic_building_system.buildings) == saved_building_ids
    run(loaded, 30)
    after = fingerprint(loaded)
    differ = {k: (carried_on[k], after[k]) for k in after if after[k] != carried_on[k]}
    assert not differ, f"diverged after loading: {list(differ)}"  # same world, same dice: same 30 ticks


def test_a_world_with_ai_minds_saves_and_thinks_after_loading(tmp_path):
    import json
    from test_llm_brain import make_world
    from engine.persistence import save_full_state, load_full_state
    sim = make_world(use_llm=True)
    sim.llm_brain.complete = lambda prompt, **kw: json.dumps({"action": "rest", "target": "none", "reason": "tired"})
    run(sim, 3)
    del sim.llm_brain.complete  # a test stand-in, not part of the world
    path = str(tmp_path / "ai.state.gz")
    save_full_state(sim, path)

    loaded = load_full_state(path)
    agent = loaded.world.agents[0]
    assert agent.autonomous_decide.__self__ is agent  # its AI methods are its own again
    assert loaded._agent_updater.thinking.executor is not None
    loaded.llm_brain.complete = lambda prompt, **kw: json.dumps({"action": "create_art", "target": "none", "reason": "x"})
    run(loaded, 8)
    assert loaded._agent_updater.thinking.stats["used"] > 0
    loaded._agent_updater.thinking.close()
    sim._agent_updater.thinking.close()


def test_saves_list_load_and_delete_through_the_save_manager(tmp_path):
    from test_reachability import make_world
    from engine.save_manager import SaveManager
    from engine.persistence import load_full_state
    sim, _ = make_world()
    sim.persistence.simulation = sim
    manager = SaveManager(saves_dir=str(tmp_path))
    assert manager.create_save("My World", sim.persistence.create_snapshot(), simulation=sim)
    save_id = manager.list_saves()[0]["id"]
    path = manager.state_path(save_id)
    assert path is not None
    assert fingerprint(load_full_state(str(path))) == fingerprint(sim)
    assert manager.delete_save(save_id) and not path.exists()
