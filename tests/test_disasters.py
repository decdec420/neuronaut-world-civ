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


def _world(n=12, seed=3):
    os.environ["USE_LLM_DECISIONS"] = "false"
    random.seed(seed)
    with quiet():
        import config
        config.reset_config()
        from engine.simulation import SimulationEngine
        sim = SimulationEngine(world_width=100, world_height=100)
        sim.initialize_world(num_agents=n)
    return sim


def _tick(sim, n):
    import asyncio

    async def go():
        for _ in range(n):
            await sim.tick()
    with quiet():
        asyncio.run(go())


def test_a_warned_flood_comes_and_does_harm():
    """Floods, fires, tornadoes... come with a warning. They used to keep the
    tick of their warning, and the engine only applies a disaster on its own
    tick, so none of them ever did anything."""
    from world.disasters import DisasterType, DisasterSeverity
    sim = _world()
    disasters = sim.disasters
    disasters.min_disaster_cooldown = 10 ** 9          # only the one we force
    alive = [a for a in sim.world.agents if a.alive]
    disasters.force_disaster(DisasterType.FLOOD, DisasterSeverity.MAJOR, sim.world.time.current_tick)
    warning = disasters.pending_warnings[-1]
    flood = warning["disaster"]
    flood.location_x, flood.location_y, flood.radius = alive[0].location.x, alive[0].location.y, 200.0
    before = {a.id: a.needs.needs[next(k for k in a.needs.needs if k.value == "security")].level for a in alive}
    _tick(sim, warning["impact_tick"] - sim.world.time.current_tick + 1)
    assert not disasters.pending_warnings
    assert flood in disasters.disaster_history and flood.tick == warning["impact_tick"]
    hurt = flood.agents_injured + flood.casualties
    assert hurt > 0, "the flood reached everyone and harmed nobody"


def test_a_disaster_is_active_for_an_hour_then_history():
    from world.disasters import DisasterType, DisasterSeverity
    sim = _world()
    disasters = sim.disasters
    disasters.min_disaster_cooldown = 10 ** 9
    disasters.force_disaster(DisasterType.EARTHQUAKE, DisasterSeverity.MINOR, sim.world.time.current_tick)
    quake = disasters.active_disasters[-1]
    _tick(sim, disasters.ACTIVE_TICKS + 1)
    assert quake not in disasters.active_disasters and quake in disasters.disaster_history


def test_agents_hear_of_a_coming_disaster_and_whether_it_reaches_them():
    from world.disasters import DisasterType, DisasterSeverity
    sim = _world()
    disasters = sim.disasters
    disasters.min_disaster_cooldown = 10 ** 9
    disasters.force_disaster(DisasterType.WILDFIRE, DisasterSeverity.MODERATE, sim.world.time.current_tick)
    fire = disasters.pending_warnings[-1]["disaster"]
    near, far = sim.world.agents[0], sim.world.agents[1]
    fire.location_x, fire.location_y, fire.radius = near.location.x, near.location.y, 5.0
    far.location.x, far.location.y = near.location.x + 30, near.location.y
    builder = sim._agent_updater.perception_builder if hasattr(sim._agent_updater, "perception_builder") else None
    from engine.agent_updates.perception_builder import PerceptionBuilder
    builder = builder or PerceptionBuilder(sim)
    seen_near = builder._add_disaster_info(near, {})["disaster_info"]["warnings"]
    seen_far = builder._add_disaster_info(far, {})["disaster_info"]["warnings"]
    assert seen_near[0]["type"] == "wildfire" and seen_near[0]["will_reach_you"] and seen_near[0]["ticks_until_impact"] > 0
    assert not seen_far[0]["will_reach_you"]
    assert builder._add_disaster_info(near, {})["disaster_info"]["active_disasters"] == []   # nothing has hit yet
