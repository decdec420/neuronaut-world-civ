"""
The same seed gives the same world (engine/ids.py): run a world twice, in
two fresh processes as a server restart would, and get the same people, ids,
relationships, buildings and events.

    python3 -m pytest tests/test_reproducible.py -q
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCRIPT = r"""
import asyncio, contextlib, io, json, logging, os, random, sys
sys.path.insert(0, ".")
logging.disable(logging.WARNING)
os.environ.update(USE_LLM_DECISIONS="false", ENABLE_SEMANTIC_MEMORY="false", AUTOSAVE_EVERY="0")
random.seed(int(sys.argv[1]))
with contextlib.redirect_stdout(io.StringIO()):
    from engine.simulation import SimulationEngine
    sim = SimulationEngine(world_width=100, world_height=100)
    sim.initialize_world(num_agents=8)
    async def go():
        for _ in range(int(sys.argv[2])):
            await sim.tick()
    asyncio.run(go())
print(json.dumps({
    "agents": sorted([a.id, a.name, round(a.location.x, 6), round(a.location.y, 6), a.alive, round(a.health, 6)]
                     for a in sim.world.agents),
    "relationships": sorted([r.id, r.agent_a, r.agent_b, round(r.strength, 6)]
                            for r in sim.relationship_manager.relationships.values()),
    "buildings": sorted([b.id, b.name, list(b.location)] for b in sim.dynamic_building_system.buildings.values()),
    "events": [[e.id, e.tick, e.title] for e in sim.event_logger.events][-50:],
}))
"""


def _world(seed: int, ticks: int) -> dict:
    env = dict(os.environ, PYTHONHASHSEED="0")
    out = subprocess.run([sys.executable, "-c", SCRIPT, str(seed), str(ticks)], cwd=ROOT, env=env,
                         capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr[-2000:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_the_same_seed_gives_the_same_world_with_the_same_ids():
    a, b = _world(5, 60), _world(5, 60)
    assert a["agents"] and a["events"]
    assert a == b


def test_another_seed_gives_another_world():
    a, b = _world(5, 10), _world(6, 10)
    assert [x[0] for x in a["agents"]] != [x[0] for x in b["agents"]]
