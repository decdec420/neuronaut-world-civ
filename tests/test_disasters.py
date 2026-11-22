"""
Disasters: shelter has to matter.

sim_check doesn't fail a run for disaster deaths (a catastrophic quake is a
roll of the dice, 5% of quakes), so this checks the mechanism directly: the
same catastrophic earthquake, with half the village inside sturdy buildings
and half out in the open.

    python3 -m pytest tests/test_disasters.py -q
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import quiet  # noqa: E402


def test_sturdy_shelter_saves_lives_in_a_catastrophic_quake():
    os.environ["USE_LLM_DECISIONS"] = "false"
    random.seed(7)
    with quiet():
        import config
        config.reset_config()
        from engine.simulation import SimulationEngine
        from agents.agent import Position
        from world.dynamic_buildings import Building
        from world.disasters import Disaster, DisasterType, DisasterSeverity
        sim = SimulationEngine(world_width=100, world_height=100)
        sim.initialize_world(num_agents=40)
    dbs = sim.dynamic_building_system
    dbs.buildings.clear()
    sheltered, exposed = sim.world.agents[:20], sim.world.agents[20:]
    for i, agent in enumerate(sheltered):
        x, y = 10 + 4 * (i % 5), 10 + 4 * (i // 5)
        dbs.buildings[f"house{i}"] = Building(id=f"house{i}", name=f"House {i}", design_id="test",
                                              location=(x, y), is_complete=True, durability=1.0)
        agent.location = Position(x + 1, y)
    for i, agent in enumerate(exposed):
        agent.location = Position(70 + i % 5, 70 + i // 5)

    quake = Disaster(DisasterType.EARTHQUAKE, DisasterSeverity.CATASTROPHIC, 50.0, 50.0, 200.0, 0)
    with quiet():
        sim.system_coordinator.apply_disaster_to_world(quake)

    dead_inside = sum(not a.alive for a in sheltered)
    dead_outside = sum(not a.alive for a in exposed)
    # Full-strength buildings stand and protect fully; in the open, 40% die
    assert dead_inside == 0, dead_inside
    assert dead_outside >= 3, dead_outside
