"""
News travels by word of mouth (world/news.py), Smallville-style.

    python3 -m pytest tests/test_news.py -q
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world, quiet  # noqa: E402


def _major(sim, title, who, tick=5):
    from engine.events import EventCategory, EventImportance
    sim.event_logger.log_event(EventCategory.POLITICAL, EventImportance.MAJOR, title, "", tick,
                               [a.id for a in who], {'x': who[0].location.x, 'y': who[0].location.y})
    return next(n for n in sim.news.items.values() if n.text == title)


def test_those_involved_and_nearby_know_others_do_not():
    from agents.agent import Position
    sim, roles = make_world()
    a, b, c, d = roles["actor"], roles["partner"], roles["sick"], roles["neighbour"]
    d.location = Position(5, 5)  # far away
    news = _major(sim, "Ann founded the Free Council", [a])
    assert sim.news.knows(a.id, news.id) and sim.news.knows(b.id, news.id)  # b stood beside a
    assert not sim.news.knows(d.id, news.id)
    minor_before = len(sim.news.items)
    from engine.events import EventCategory, EventImportance
    sim.event_logger.log_event(EventCategory.SOCIAL, EventImportance.MINOR, "small talk", "", 6, [a.id])
    assert len(sim.news.items) == minor_before  # trivia isn't news


def test_talking_passes_news_on_and_it_spreads_along_a_chain():
    from agents.agent import Position
    sim, roles = make_world()
    a, c, d = roles["actor"], roles["sick"], roles["neighbour"]
    c.location, d.location = Position(5, 5), Position(95, 95)
    news = _major(sim, "A street light was lit for the first time", [a])
    assert not sim.news.knows(c.id, news.id) and not sim.news.knows(d.id, news.id)

    passed = sim.news.converse(a, c, now=10)  # a tells c
    assert sim.news.knows(c.id, news.id) and passed[0][2] is news
    assert any(f"{a.name} told me" in r.text for r in c.memory_stream.records)
    sim.news.converse(c, d, now=20, both_ways=False)  # a story: c tells d
    assert sim.news.knows(d.id, news.id)
    alive = [x.id for x in sim.world.agents if x.alive]
    assert sim.news.reach(news.id, alive) == 1.0
    # Nothing left to tell: a conversation passes nothing on
    assert sim.news.converse(c, d, now=30) == [] or all(n is not news for _, _, n in sim.news.converse(c, d, now=31))


def test_the_freshest_most_important_news_is_told_first():
    sim, roles = make_world()
    a, c = roles["actor"], roles["sick"]
    old = sim.news.publish(0, "Old gossip", 0.9, [a.id])
    new = sim.news.publish(400, "Big news today", 0.9, [a.id])
    small = sim.news.publish(400, "Small news today", 0.3, [a.id])
    assert sim.news.worth_telling(a.id, c.id, now=410) is new


def test_a_socialize_action_carries_news_in_a_real_tick_path():
    from agents.agent import Action, ActionType
    sim, roles = make_world()
    a, d = roles["actor"], roles["neighbour"]
    d.location = a.location
    news = sim.news.publish(1, "Ann's well has water", 0.8, [a.id])
    d_known_before = sim.news.knows(d.id, news.id)
    sim._agent_updater._converse(a, Action(ActionType.SOCIALIZE, target_agent=d.id), 3)
    assert not d_known_before and sim.news.knows(d.id, news.id)
    assert sim.news.conversations == 1


def test_a_model_written_dialogue_is_remembered_by_both():
    from test_llm_brain import make_world as llm_world
    sim = llm_world()
    a, b = sim.world.agents[0], sim.world.agents[1]
    prompt, schema = sim.llm_brain.dialogue_prompt(a, b, [], 5)
    assert a.name in prompt and set(schema["properties"]["lines"]["items"]["properties"]["speaker"]["enum"]) == {a.name, b.name}
    answer = json.dumps({"lines": [{"speaker": a.name, "text": "Did you hear about the new well?"},
                                   {"speaker": b.name, "text": "I did, the water is sweet."},
                                   {"speaker": "Stranger", "text": "ignored"}]})
    with quiet():
        sim._agent_updater._apply_dialogue(a, b.id, answer, 6)
    for who in (a, b):
        assert any("Did you hear about the new well?" in r.text for r in who.memory_stream.records)
    assert sim.chronicle.voices[-1].text == "Did you hear about the new well?"
    assert "Stranger" not in sim.event_logger.events[-1].description


def test_news_is_bounded():
    from world import news as news_module
    from world.news import NewsNetwork
    network = NewsNetwork()
    for i in range(1000):
        network.publish(i, f"thing {i}", 0.5, ["a"])
    assert len(network.items) <= news_module.MAX_NEWS * 1.2
    assert len(network.known["a"]) <= news_module.MAX_KNOWN * 1.2
