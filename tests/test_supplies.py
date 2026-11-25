"""
Food and water: agents use what they carry and what's close by.

- Urgently thirsty with water in the pack: drink it (engine/agent_updates/
  agent_updater.py _survival_override). It used to fetch water every time: a
  walk to the lake, several turns of being thirsty, with water in the pack.
- Gathering takes food or water within NEAR_SOURCE tiles before walking to a
  remembered place, and of remembered places the closest
  (engine/agent_updates/action_handlers.py _close_or_remembered,
  agents/pathfinding.py recall_resource). It used to walk to the most visited
  place, wherever it was.

    python3 -m pytest tests/test_supplies.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world  # noqa: E402


def test_thirsty_agents_drink_what_they_carry_and_fetch_only_without():
    from agents.agent import ActionType, NeedType
    sim, roles = make_world()
    agent = roles["actor"]
    agent.needs.needs[NeedType.THIRST].level = 0.9
    agent.needs.needs[NeedType.HUNGER].level = 0.1
    agent.inventory.items = {"water": 3}
    assert sim._agent_updater._survival_override(agent).action_type == ActionType.DRINK
    agent.inventory.items = {}
    assert sim._agent_updater._survival_override(agent).action_type == ActionType.GATHER_WATER


def test_the_closest_remembered_place_is_recalled():
    from agents.agent import Position
    sim, roles = make_world()
    agent, memory, tick = roles["actor"], sim.resource_memory, sim.world.time.current_tick
    for _ in range(5):                                    # an old favourite, far away
        memory.remember_resource(agent.id, "food", 90.0, 90.0, 30.0, tick)
    memory.remember_resource(agent.id, "food", 55.0, 52.0, 30.0, tick)
    near = memory.recall_resource(agent.id, "food", tick, near=Position(50.0, 50.0))
    assert (near["x"], near["y"]) == (55.0, 52.0)
    assert memory.recall_resource(agent.id, "food", tick)["x"] == 90.0   # without a place: most visited


def test_food_close_by_is_gathered_before_walking_to_a_remembered_place():
    from agents.agent import Position
    from world.simulation import Resource, ResourceType
    sim, roles = make_world()
    agent, tick = roles["actor"], sim.world.time.current_tick
    for (x, y), tile in sim.world.map.tiles.items():      # no food anywhere but where we put it
        tile.resources = [r for r in tile.resources if r.resource_type != ResourceType.FOOD]
    far = next((x, y) for (x, y) in sorted(sim.world.map.land_component)
               if ((x - 50) ** 2 + (y - 50) ** 2) ** 0.5 > 30)
    for _ in range(5):
        sim.resource_memory.remember_resource(agent.id, "food", float(far[0]), float(far[1]), 30.0, tick)
    sim.world.map.tiles[(51, 50)].resources.append(
        Resource(id="food_test", resource_type=ResourceType.FOOD, location=Position(51.0, 50.0), quantity=40.0))
    agent.location = Position(50.0, 50.0)
    before = agent.inventory.items.get("food", 0)
    result = sim.interaction_handler.handle_gather_food(agent, agent.location, tick)
    assert result["success"] and "Gathered" in result["message"], result
    assert agent.inventory.items.get("food", 0) > before
    assert (agent.location.x, agent.location.y) == (50.0, 50.0)   # it didn't set off for the old place
