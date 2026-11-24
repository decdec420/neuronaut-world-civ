"""
Taking shelter (engine/handlers/shelter.py): 'hide' walks to a standing
building and shelters there, and the rule-based brain weighs a warned
disaster coming its way (agents/utility_brain.py).

    python3 -m pytest tests/test_shelter.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act  # noqa: E402
from test_reachability import make_world  # noqa: E402


def _house(sim, x, y, bid="house", durability=0.9):
    from world.dynamic_buildings import Building
    b = Building(id=bid, name=f"House {bid}", design_id="test", location=(x, y),
                 is_complete=True, durability=durability)
    sim.dynamic_building_system.buildings[b.id] = b
    return b


def _dry_spot_near(sim, agent, dx):
    """A dry tile on the agent's own land about dx tiles away."""
    m, pf = sim.world.map, sim.pathfinder
    mine = pf.land_component.get((int(agent.location.x), int(agent.location.y)))
    for r in range(dx, dx + 15):
        for cx, cy in ((agent.location.x + r, agent.location.y), (agent.location.x - r, agent.location.y),
                       (agent.location.x, agent.location.y + r), (agent.location.x, agent.location.y - r)):
            if not m.is_water(cx, cy) and pf.land_component.get((int(cx), int(cy))) == mine:
                return int(cx), int(cy)
    raise AssertionError("no dry land nearby")


def test_hide_walks_to_a_house_then_shelters_there():
    from engine.system_coordinator import SHELTER_RADIUS
    sim, roles = make_world()
    agent = roles["actor"]
    x, y = _dry_spot_near(sim, agent, 12)
    house = _house(sim, x, y)
    first = act(sim, agent, "hide")
    assert "Heading for shelter" in first.message and not first.metadata["arrived"]
    for _ in range(30):
        result = act(sim, agent, "hide")
        if result.metadata.get("arrived"):
            break
    assert result.metadata["arrived"] and house.name in result.message
    assert sim.dynamic_building_system.standing_building_near(agent.location.x, agent.location.y, SHELTER_RADIUS) is house
    assert not sim.world.map.is_water(agent.location.x, agent.location.y)


def test_home_comes_first():
    from life import homes
    sim, roles = make_world()
    agent = roles["actor"]
    x, y = _dry_spot_near(sim, agent, 6)
    home = _house(sim, x, y, "home", durability=0.3)
    x2, y2 = _dry_spot_near(sim, agent, 3)
    _house(sim, x2, y2, "sturdier", durability=1.0)
    homes.move_in(sim.dynamic_building_system, agent, home, 0, "test")
    result = act(sim, agent, "hide")
    assert result.metadata["shelter_id"] == "home"


def test_no_building_no_hiding():
    from agents.agent import Action, ActionType
    sim, roles = make_world()
    sim.dynamic_building_system.buildings.clear()
    ok, why = sim._handler_registry.get_handler(ActionType.HIDE).validate(roles["actor"], Action(ActionType.HIDE))
    assert not ok and "no standing building" in why


def test_a_coming_disaster_pulls_toward_shelter_for_those_it_will_reach():
    from world.disasters import DisasterType, DisasterSeverity
    sim, roles = make_world()
    near, far = roles["actor"], roles["neighbour"]
    brain = sim._agent_updater.utility_brain if hasattr(sim._agent_updater, "utility_brain") else None
    if brain is None:
        from agents.utility_brain import UtilityBrain
        brain = UtilityBrain(sim)
    assert brain._warning_pull(near) == 0.0          # nothing coming
    sim.disasters.min_disaster_cooldown = 10 ** 9
    sim.disasters.force_disaster(DisasterType.FLOOD, DisasterSeverity.MAJOR, sim.world.time.current_tick)
    warning = sim.disasters.pending_warnings[-1]
    flood = warning["disaster"]
    flood.location_x, flood.location_y, flood.radius = near.location.x, near.location.y, 5.0
    far.location.x, far.location.y = near.location.x + 30, near.location.y
    pull_soon = brain._warning_pull(near)
    assert pull_soon > 0 and brain._warning_pull(far) == 0.0
    # a careful agent feels it more than a reckless one
    near.personality.risk_taking = 0.9
    reckless = brain._warning_pull(near)
    near.personality.risk_taking = 0.1
    careful = brain._warning_pull(near)
    assert careful > reckless
    # and further off in time, less
    warning["impact_tick"] = sim.world.time.current_tick + 30
    assert brain._warning_pull(near) < careful
