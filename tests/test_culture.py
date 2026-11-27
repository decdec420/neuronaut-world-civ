"""
Celebrations are chosen, not thrown by the world (engine/handlers/
entertainment.py, construction.py, knowledge.py).

Every finished building and every discovery used to throw a party by
itself, adding about 70% of everyone near as guests who then got belonging,
meaning and joy without choosing anything: about 35 parties a day in a
20-day world. Now a celebration happens when someone chooses to celebrate;
it records who threw it, why (in their words, if they gave any), when, and
who joined. GET /culture tells it with ids.

    python3 -m pytest tests/test_culture.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act  # noqa: E402
from test_reachability import make_world  # noqa: E402


def test_a_celebration_is_someones_choice_and_says_who_why_and_when():
    from engine.society import culture_snapshot
    sim, roles = make_world()
    a = roles["actor"]
    sim.world.time.current_tick = 144 * 2 + 6 * 19
    act(sim, a, "celebrate", details="the first harvest")
    c = culture_snapshot(sim)["celebrations"][0]
    assert c["host"] == {"id": a.id, "name": a.name} and c["why"] == "the first harvest"
    assert c["when"] == "day 3, 19:00" and c["live"] and a.id not in [g["id"] for g in c["guests"]]


def test_finishing_a_building_or_a_discovery_throws_no_party_by_itself():
    """Only the celebrate action starts a celebration."""
    import inspect
    from engine.handlers import construction, entertainment, knowledge
    for module in (construction, knowledge):
        assert "trigger_celebration(" not in inspect.getsource(module), module.__name__
    assert "trigger_celebration(" in inspect.getsource(entertainment)


def test_the_culture_endpoint_serves_people_with_ids():
    from fastapi.testclient import TestClient
    from api import server
    with TestClient(server.app) as client:
        data = client.get("/culture").json()
        assert {"counts", "celebrations", "gatherings", "art", "games"} <= set(data)


def test_the_lab_tells_what_was_made_by_whom_and_what_keeps_failing():
    from engine.society import lab_snapshot
    sim, roles = make_world()
    a = roles["actor"]
    sim.world.time.current_tick = 300
    for _ in range(12):
        act(sim, a, "experiment")
    lab = lab_snapshot(sim)
    assert lab["counts"]["tried"] == 12 and lab["counts"]["made"] + lab["counts"]["failed"] == 12
    assert lab["experimenters"][0]["id"] == a.id
    if lab["most_made"]:
        first = lab["most_made"][0]
        assert first["by"]["id"] == a.id and first["when"] == "day 3, 02:00" and first["from"]
        assert first["times"] >= 1 and first["makers"] == 1
        assert sum(m["times"] for m in lab["most_made"]) <= lab["counts"]["made"]
    if lab["counts"]["failed"]:
        assert lab["failures_by_reason"] and lab["failing_combinations"]
