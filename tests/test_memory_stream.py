"""
Memory, reflection and day plans, Smallville-style (agents/memory_stream.py).
No network: model answers are canned.

    python3 -m pytest tests/test_memory_stream.py -q
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_retrieval_weighs_recency_importance_and_relevance():
    from agents.memory_stream import MemoryStream
    stream = MemoryStream()
    stream.add(0, "Mary and I became partners by the river", 0.8)
    for t in range(1, 40):
        stream.add(t, f"Gathered water at the well, trip {t}", 0.1)
    stream.add(40, "Found iron ore in the hills", 0.3)
    best = stream.retrieve("Mary", now=41, k=3)
    assert any("Mary" in r.text for r in best)            # relevant and important beats recent chores
    assert any("iron" in r.text for r in best)            # recent and moderately important
    # Recency fades: 0.995 per game hour
    old = stream.retrieve("nothing in common", now=6 * 24 * 200, k=1)[0]
    assert old.importance == 0.8


def test_the_stream_is_bounded_and_repeats_are_one_memory():
    from agents.memory_stream import MemoryStream
    stream = MemoryStream(max_records=50)
    for t in range(5):
        stream.add(t, "Rested", 0.1)
    assert len(stream.records) == 1 and stream.records[0].count == 5
    stream.add(10, "Built a stone house", 0.9)
    for t in range(20, 400):
        stream.add(t, f"Walked to spot {t}", 0.1)
    assert len(stream.records) <= 50 * 1.25
    assert any("stone house" in r.text for r in stream.records)  # important memories outlast chores


def test_events_and_own_actions_become_memories():
    from test_reachability import make_world, quiet
    from test_capabilities import act
    sim, roles = make_world()
    c, d = roles["sick"], roles["neighbour"]
    act(sim, d, "seek_romance", target=c)
    act(sim, c, "seek_romance", target=d)  # they become partners: an event both remember
    assert any("partners" in r.text for r in c.memory_stream.records)
    assert any("partners" in r.text for r in d.memory_stream.records)

    from agents.agent import Action, ActionType
    with quiet():
        sim._agent_updater._remember_action(d, Action(ActionType.TELL_STORY, target_agent=c.id),
                                            {"success": True, "message": "A tale of the river", "emotional_impact": 0.5}, 5)
    assert d.memory_stream.records[-1].text == f"Tell story with {c.name}: A tale of the river"


def _llm_world():
    from test_llm_brain import make_world
    sim = make_world()
    sim.world.time.current_tick = 6 * 9  # 09:00 on day 1: everyone is awake
    sim.world.time.hour, sim.world.time.day = 9, 1
    return sim


def test_an_awake_agent_without_a_plan_plans_its_day_and_follows_it():
    sim = _llm_world()
    agent = sim.world.agents[0]
    updater = sim._agent_updater
    kind, prompt, schema = updater._next_thought(agent, sim.world.get_state(), 54)
    assert kind == "plan" and "Plan your day" in prompt
    assert schema["properties"]["plan"]["items"]["properties"]["action"]["enum"]

    answer = json.dumps({"plan": [{"hour": 9, "action": "gather_food", "why": "the larder is empty"},
                                  {"hour": 14, "action": "build", "why": "a roof before winter"},
                                  {"hour": 15, "action": "daydream", "why": "not on the menu"}]})
    updater._apply_thought(agent, "plan", answer, 54)
    stream = agent.memory_stream
    assert stream.plan_day == 1 and [a for _, a, _ in stream.day_plan] == ["gather_food", "build"]
    assert stream.planned_action(10) == "gather_food" and stream.planned_action(16) == "build"
    # Planned for today: next it decides, and the plan is in what it remembers
    kind, prompt, _ = updater._next_thought(agent, sim.world.get_state(), 55)
    assert kind == "decide" and "Your plan for today: 09:00 gather_food" in prompt


def test_enough_happening_prompts_a_reflection_that_is_remembered():
    sim = _llm_world()
    agent = sim.world.agents[0]
    updater = sim._agent_updater
    agent.memory_stream.plan_day = 1  # already planned today
    for t in range(30):
        agent.memory_stream.add(t, f"Argued with Kenneth about the well, time {t}", 0.4)
    kind, prompt, _ = updater._next_thought(agent, sim.world.get_state(), 54)
    assert kind == "reflect" and "Argued with Kenneth" in prompt
    updater._apply_thought(agent, "reflect", json.dumps({"insights": [
        "Kenneth and I keep clashing over water", "The village needs a second well"]}), 54)
    reflections = [r for r in agent.memory_stream.records if r.kind == "reflection"]
    assert [r.text for r in reflections] == ["Kenneth and I keep clashing over water",
                                             "The village needs a second well"]
    assert not agent.memory_stream.wants_reflection()
    assert updater._next_thought(agent, sim.world.get_state(), 55)[0] == "decide"
