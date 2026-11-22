"""
The chronicle writes down firsts as agents make them (engine/chronicle.py).

    python3 -m pytest tests/test_chronicle.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act, befriend  # noqa: E402
from test_reachability import make_world, quiet  # noqa: E402


def _titles(sim):
    return {e.key: e for e in sim.chronicle.entries}


def test_firsts_are_written_down_once_with_who_did_them():
    sim, roles = make_world()
    a, b, c, d = roles["actor"], roles["partner"], roles["sick"], roles["neighbour"]
    chronicle = sim.chronicle
    chronicle.observe(sim, 1)
    assert set(_titles(sim)["first_couple"].agents) == {a.name, b.name}  # make_world's couple courted each other

    a.personality.aggression = 0.1
    act(sim, a, "govern")
    act(sim, a, "make_law", details="no fighting")
    act(sim, d, "worship")
    chronicle.observe(sim, 2)
    entries = _titles(sim)
    assert a.name in entries["first_government"].text and entries["first_government"].agents == [a.name]
    assert entries["first_law"].agents == [a.name]
    assert entries["first_religion"].text == f"Its prophet: {d.name}."

    # A trade that worked is the first trade; a second one isn't news
    chronicle.on_action(sim, a, "trade", {"success": True, "message": "Bartered herbs"}, 3)
    chronicle.on_action(sim, d, "trade", {"success": True, "message": "Bartered wood"}, 4)
    assert sum(e.key == "first_trade" for e in chronicle.entries) == 1
    chronicle.on_action(sim, a, "fight", {"success": False}, 5)
    assert "first_fight" not in chronicle.done  # failed actions aren't firsts

    # Deaths: the first, and the first of old age
    c.alive, c.death_cause, c.age = False, "old age", 88
    chronicle.observe(sim, 6)
    entries = _titles(sim)
    assert entries["first_death"].agents == [c.name] and entries["first_death_old_age"].text == f"{c.name} lived to 88."
    n = len(chronicle.entries)
    chronicle.observe(sim, 7)
    assert len(chronicle.entries) == n  # nothing new, nothing written


def test_agents_words_are_kept_and_bounded():
    from engine.chronicle import Chronicle
    chronicle = Chronicle()
    chronicle.MAX_VOICES = 5

    class Agent:
        name = "Yara"
    chronicle.on_choice(1, Agent(), "make_law", "Nobody should go thirsty")
    chronicle.on_choice(2, Agent(), "rest", "tired")  # everyday choices aren't kept
    for i in range(10):
        chronicle.voice(3 + i, "Yara", f"insight {i}")
    texts = [v.text for v in chronicle.voices]
    assert "tired" not in texts and len(texts) == 5 and texts[-1] == "insight 9"
