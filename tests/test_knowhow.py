"""
The beginning of time (world/knowhow.py): in a dawn world people know only
what comes with being human; everything else is worked out, seen, taught, and
lost when the last one who knew it dies.

    python3 -m pytest tests/test_knowhow.py -q
"""

import os
import sys
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act  # noqa: E402
from test_reachability import make_world, quiet  # noqa: E402


@contextmanager
def dawn():
    before = os.environ.get("WORLD_START")
    os.environ["WORLD_START"] = "dawn"
    try:
        yield
    finally:
        if before is None:
            os.environ.pop("WORLD_START", None)
        else:
            os.environ["WORLD_START"] = before
        import config
        config.reset_config()


def dawn_world():
    with dawn():
        return make_world()


def run(sim, agent, name, target=None):
    """Run an action the way the tick does (gates, then the handler, then ideas and onlookers)."""
    import asyncio
    from agents.agent import Action, ActionType
    with quiet():
        return asyncio.run(sim.execute_action(agent, Action(ActionType(name), target_agent=target.id if target else None)))


def test_a_dawn_world_starts_with_nothing_but_being_human():
    sim, roles = dawn_world()
    assert sim.knowhow.active
    assert all(a.knowhow == set() for a in sim.world.agents)
    settlers, _ = make_world()
    assert not settlers.knowhow.active and all(a.knowhow is None for a in settlers.world.agents)


def test_founders_at_the_dawn_carry_only_a_little_food_and_water():
    with dawn():
        import config, random
        config.reset_config()
        random.seed(3)
        with quiet():
            from engine.simulation import SimulationEngine
            sim = SimulationEngine(world_width=100, world_height=100)
            sim.initialize_world(num_agents=6)
    for agent in sim.world.agents:
        assert set(agent.inventory.items) <= {"food", "water"} and agent.knowhow == set()


def test_you_cannot_do_what_you_dont_know_how_to_until_you_learn_it():
    sim, roles = dawn_world()
    agent = roles["actor"]
    from agents.agent import Action, ActionType
    result = run(sim, agent, "build")
    assert not result["success"] and "don't know how" in result["message"] and "building shelters" in result["message"]
    assert not sim._agent_updater._can_run(agent, Action(ActionType.BUILD))       # the brain won't pick it
    assert sim._agent_updater._can_run(agent, Action(ActionType.GATHER_FOOD))     # innate
    with quiet():
        sim.knowhow.learn(agent, "stone_tools", "insight", 10)
        sim.knowhow.learn(agent, "shelter", "insight", 11)
    assert sim._agent_updater._can_run(agent, Action(ActionType.BUILD))


def test_doing_something_related_can_give_the_idea_and_the_first_is_recorded(monkeypatch):
    from world import knowhow
    sim, roles = dawn_world()
    agent = roles["actor"]
    monkeypatch.setattr(knowhow.random, "random", lambda: 0.0)   # the idea comes
    with quiet():
        sim.knowhow.after_action(agent, "gather_materials", {"success": True}, 300)
    assert agent.knowhow                                           # it worked something out
    first = sim.knowhow.firsts[next(iter(agent.knowhow))]
    assert first["who"] == agent.name and first["day"] == 3 and first["generation"] == 1 and first["humans"]
    farming = knowhow.KNOWHOW["farming"]
    assert not knowhow.can_learn(roles["partner"], "farming")         # it needs stone tools first
    assert farming.needs == ("stone_tools",)


def test_onlookers_can_pick_it_up_by_watching(monkeypatch):
    from world import knowhow
    sim, roles = dawn_world()
    agent, near = roles["actor"], roles["partner"]
    with quiet():
        sim.knowhow.learn(agent, "stone_tools", "insight", 5)
    monkeypatch.setattr(knowhow, "WATCH_CHANCE", 1.0)
    with quiet():
        sim.knowhow.after_action(agent, "chop_wood", {"success": True}, 6)   # chopping takes stone tools
    assert "stone_tools" in near.knowhow and sim.knowhow.counts["watched"] >= 1


def test_teaching_is_done_in_person_and_passes_it_on(monkeypatch):
    from agents.agent import Position
    from world import knowhow
    sim, roles = dawn_world()
    teacher, pupil = roles["actor"], roles["neighbour"]
    with quiet():
        sim.knowhow.learn(teacher, "stone_tools", "insight", 5)
    monkeypatch.setattr(knowhow.random, "random", lambda: 0.0)        # the lesson takes
    pupil.location = Position(*next((x, y) for (x, y) in sorted(sim.world.map.land_component)
                                    if 12 <= ((x - teacher.location.x) ** 2 + (y - teacher.location.y) ** 2) ** 0.5 <= 14))
    far = teacher.location.distance_to(pupil.location)
    walking = act(sim, teacher, "teach", target=pupil)
    assert walking.metadata.get("underway") and teacher.location.distance_to(pupil.location) < far
    pupil.location = Position(teacher.location.x + 1, teacher.location.y)
    taught = act(sim, teacher, "teach", target=pupil)
    assert taught.success and "stone tools" in taught.message and "stone_tools" in pupil.knowhow


def test_knowhow_dies_with_the_last_who_knew_it_and_can_be_found_again():
    sim, roles = dawn_world()
    agent = roles["actor"]
    with quiet():
        sim.knowhow.learn(agent, "fire", "insight", 12)
        sim.knowhow.update(12)
        agent.alive = False
        sim.knowhow.update(24)
    assert [l["knowhow"] for l in sim.knowhow.lost] == ["fire"]
    titles = [e.title for e in sim.event_logger.get_recent_events(10)]
    assert any("has been lost" in t for t in titles)
    with quiet():
        assert sim.knowhow.learn(roles["partner"], "fire", "insight", 40)
    assert any("again" in e.title for e in sim.event_logger.get_recent_events(5))
    assert sim.knowhow.firsts["fire"]["who"] == agent.name     # the first stays the first


def test_children_at_the_dawn_are_born_knowing_nothing_and_are_a_generation_on():
    sim, roles = dawn_world()
    mother, father = roles["partner"], roles["actor"]
    from agents.agent import Gender
    mother.gender, father.gender = Gender.FEMALE, Gender.MALE
    with quiet():
        sim.knowhow.learn(mother, "fire", "insight", 1)
    mother.is_pregnant, mother.pregnancy_partner_id = True, father.id
    with quiet():
        child = sim.lifecycle_manager.deliver_baby(mother, 100)
    assert child.knowhow == set() and child.generation == 2


def test_the_ai_brain_is_told_what_it_knows_and_what_it_could_teach():
    from test_llm_brain import make_world as make_ai_world
    with dawn():
        sim = make_ai_world()
    agent, other = sim.world.agents[0], sim.world.agents[1]
    other.location = agent.location
    with quiet():
        sim.knowhow.learn(agent, "fire", "insight", 3)
    perceptions = sim._perception_builder.build_perceptions(agent, sim.world.get_state())
    with quiet():
        prompt = sim.llm_brain._build_thinking_prompt(agent, perceptions, "decide_action")
    assert "You know how to do: making fire." in prompt
    assert "You could teach " in prompt and f"{other.name} making fire" in prompt


def test_worlds_start_at_the_dawn_unless_told_otherwise(monkeypatch):
    import config
    monkeypatch.delenv("WORLD_START", raising=False)
    config.reset_config()
    try:
        assert config.load_config().world_start == "dawn"
        monkeypatch.setenv("WORLD_START", "settlers")
        config.reset_config()
        assert config.load_config().world_start == "settlers"
    finally:
        config.reset_config()


def test_a_dawn_world_starts_with_a_band_of_25_and_settlers_with_12(monkeypatch):
    import config
    monkeypatch.delenv("NUM_AGENTS", raising=False)
    try:
        monkeypatch.setenv("WORLD_START", "dawn")
        config.reset_config()
        assert config.load_config().num_agents == 25
        monkeypatch.setenv("WORLD_START", "settlers")
        config.reset_config()
        assert config.load_config().num_agents == 12
        monkeypatch.setenv("NUM_AGENTS", "40")
        config.reset_config()
        assert config.load_config().num_agents == 40
    finally:
        config.reset_config()
