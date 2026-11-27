"""
The annals write down, hour by hour, what changed the village (engine/annals.py),
without changing anything; GET /annals reads them for the Chronicle tab.

    python3 -m pytest tests/test_annals.py -q
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world, quiet  # noqa: E402

HOUR = 6


def _hour_end(n):
    """The last tick of hour n (when the annals look)."""
    return n * HOUR + HOUR - 1


def _kinds(sim, day=1):
    return [h["kind"] for h in sim.annals.days[day]["happenings"]]


def _child(sim, mother, father, name="Wren"):
    from agents.agent import Agent, Gender
    with quiet():
        child = Agent(gender=Gender.FEMALE)
    child.name, child.age = name, 0
    child.mother_id, child.father_id = mother.id, father.id
    mother.children_ids.append(child.id)
    father.children_ids.append(child.id)
    sim.world.agents.append(child)
    return child


def test_births_deaths_and_couples_are_written_down_with_who():
    sim, roles = make_world()
    a, b, c, d = roles["actor"], roles["partner"], roles["sick"], roles["neighbour"]
    annals = sim.annals
    annals.observe(sim, _hour_end(0))          # the first look: who is there
    assert annals.started_tick == _hour_end(0)

    a.partner_id, b.partner_id = None, None
    annals.observe(sim, _hour_end(1))
    a.partner_id, b.partner_id = b.id, a.id
    child = _child(sim, b, a)
    c.alive, c.death_cause, c.death_tick = False, "old age", _hour_end(2) - 2
    annals.observe(sim, _hour_end(2))

    day = annals.days[1]["happenings"]
    born = next(h for h in day if h["kind"] == "born")
    assert born["text"] == f"{child.name} was born to {b.name} and {a.name}"
    assert {p for p, _ in born["people"]} == {child.id, a.id, b.id}
    died = next(h for h in day if h["kind"] == "died")
    assert died["text"].startswith(f"{c.name} died of old age at {int(c.age)}") and died["tick"] == c.death_tick
    coupled = [h for h in day if h["kind"] == "coupled"]
    assert len(coupled) == 1 and {a.name, b.name} <= set(n for _, n in coupled[0]["people"])
    kinds = _kinds(sim)                             # they parted in hour 1 and paired again in hour 2
    assert kinds.index("parted") < kinds.index("coupled")
    del d


def test_a_death_names_the_partner_it_leaves():
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    a.partner_id, b.partner_id = b.id, a.id
    sim.annals.observe(sim, _hour_end(0))
    a.alive, a.death_cause = False, "flood"
    a.partner_id = b.partner_id = None            # a death clears the partner
    sim.annals.observe(sim, _hour_end(1))
    died = next(h for h in sim.annals.days[1]["happenings"] if h["kind"] == "died")
    assert died["text"] == f"{a.name} died in a flood at {int(a.age)}, leaving {b.name}"
    assert died["w"] == 4                         # not of old age


def test_looking_never_rolls_the_worlds_dice():
    sim, roles = make_world()
    random.seed(7)
    before = random.getstate()
    for hour in range(30):
        sim.annals.observe(sim, _hour_end(hour))
    assert random.getstate() == before


def test_a_day_closes_with_the_village_as_it_was():
    sim, roles = make_world()
    for hour in range(24):
        sim.annals.observe(sim, _hour_end(hour))
    end = sim.annals.days[1]["end"]
    alive = [a for a in sim.world.agents if a.alive]
    assert end["people"] == len(alive) and end["adults"] + end["children"] == len(alive)
    from engine.annals import annals_view
    view = annals_view(sim)
    assert view["days"][0]["day"] == 1 and view["days"][0]["summary"]
    assert view["population"][0] == {"day": 1, "people": len(alive), "born": 0, "died": 0}
    assert view["chapters"][0]["from"] == 1


def test_a_world_saved_before_the_annals_pieces_its_past_together():
    sim, roles = make_world()
    a, b, d = roles["actor"], roles["partner"], roles["neighbour"]
    a.personality.aggression = 0.1
    from test_capabilities import act
    act(sim, a, "govern")                           # a government founded at tick 0
    sim.world.time.current_tick = 3 * 144 + 10      # three days later
    child = _child(sim, b, a)
    child.ticks_lived = 2 * 144                     # born on day 2
    del sim.annals
    sim.ensure_newer_systems()                      # what loading an old save does
    sim.annals.observe(sim, _hour_end(3 * 24 + 1))
    assert "government" in _kinds(sim, 1)
    born = next(h for h in sim.annals.days[2]["happenings"] if h["kind"] == "born")
    assert child.name in born["text"]
    from engine.annals import annals_view
    view = annals_view(sim)
    assert view["began"]["pieced_before"] == 4
    assert all(d["pieced"] for d in view["days"] if d["day"] < 4)
    del d


def test_since_you_were_last_here_counts_what_happened():
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    sim.annals.observe(sim, _hour_end(0))
    sim.world.time.current_tick = 144 * 2
    _child(sim, b, a, "Ash")
    sim.annals.observe(sim, 144 * 2 + 5)
    from engine.annals import annals_view
    since = annals_view(sim, since_day=2)["since"]
    assert since["born"] == 1 and since["from_day"] == 2
    assert any("Ash" in h["text"] for h in since["notable"])
    assert annals_view(sim, since_day=1)["since"]["born"] == 1


def test_many_of_a_kind_are_told_together():
    from engine.annals import Annals, narrate
    annals = Annals()
    for i in range(7):
        annals.add(10 + i, 'coupled', f"P{i} and Q{i} became a couple", [(f"p{i}", f"P{i}"), (f"q{i}", f"Q{i}")])
    annals.add(20, 'taught', "T taught U fire", [("t", "T"), ("u", "U")])
    text = narrate(annals.days[1])
    assert "P0 and Q0 became a couple" in text and "and 3 more couples" in text
    assert "1 lesson" in text


def test_a_persons_panel_tells_their_life_from_the_annals():
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    sim.annals.observe(sim, _hour_end(0))
    _child(sim, b, a, "Rowan")
    sim.annals.observe(sim, _hour_end(1))
    from engine.details import describe
    detail = describe(sim, "agent", a.id)
    life = next(s for s in detail["sections"] if s["title"] == "Their life")
    assert any("Rowan was born" in row["text"] for row in life["timeline"])


def test_the_annals_endpoint(monkeypatch):
    from fastapi.testclient import TestClient
    from api import server
    monkeypatch.setattr(server, "BROADCAST_INTERVAL", 0.05)
    with TestClient(server.app) as client:
        server.simulation.paused = True
        for hour in range(3):
            server.simulation.annals.observe(server.simulation, _hour_end(hour))
        body = client.get("/annals?days=5&since_day=1").json()
        assert {"today", "population", "chapters", "days", "houses", "lives", "since", "began"} <= set(body)
        assert body["days"][0]["happenings"][0]["kind"] == "began"
        founders = body["days"][0]["happenings"][0]["people"]
        assert founders and all({"id", "name"} <= set(p) for p in founders)
