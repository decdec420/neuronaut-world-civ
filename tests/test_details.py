"""
Everything the dashboard can open is told in full (engine/details.py,
GET /details/{kind}/{id}), and the things that have a history keep one:
governments (founded, joined, laws, elections, taxes...), faiths (founded,
who told whom), know-how (who learned it, how, from whom).

    python3 -m pytest tests/test_details.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act  # noqa: E402
from test_reachability import make_world, quiet  # noqa: E402


def check_shape(d, kind):
    assert d["kind"] == kind and d["id"] and d["title"] and isinstance(d["facts"], list)
    for f in d["facts"]:
        assert set(f) >= {"label", "value"}
    for s in d["sections"]:
        assert s["title"] and ("text" in s or "items" in s or "timeline" in s)
        for item in s.get("items") or []:
            assert "text" in item
            if item.get("link"):
                assert set(item["link"]) == {"kind", "id", "label"}
    return d


def links(d):
    found = [f["link"] for f in d["facts"] if f.get("link")]
    for s in d["sections"]:
        found += [i["link"] for i in s.get("items") or [] if i.get("link")]
        for line in s.get("timeline") or []:
            found += line["links"]
    return found


def test_a_government_tells_how_it_is_run_who_is_in_it_and_what_happened():
    from engine.details import describe
    sim, roles = make_world()
    a, d = roles["actor"], roles["neighbour"]
    sim.world.time.current_tick = 300
    founded = act(sim, a, "govern")
    gov = sim.governance_manager.governments[founded.metadata["government_id"]]
    sim.world.time.current_tick = 320
    act(sim, d, "govern")                                         # joins
    law = act(sim, a, "make_law", prohibition="gamble")
    act(sim, d, "vote")
    g = check_shape(describe(sim, "government", gov.id), "government")
    assert gov.founded_tick == 300 and "founded on day 3" in g["subtitle"]
    assert "How it's run" in [s["title"] for s in g["sections"]]
    history = next(s for s in g["sections"] if s["title"] == "What has happened in it")["timeline"]
    texts = [line["text"] for line in history]
    assert any("founded it" in t for t in texts) and any("became a citizen" in t for t in texts)
    assert any("proposed a law" in t for t in texts)
    assert {"agent", "law"} <= {l["kind"] for l in links(g)}
    l = check_shape(describe(sim, "law", law.metadata["law_id"]), "law")
    votes = next(s for s in l["sections"] if s["title"].startswith("Votes"))["items"]
    assert len(votes) == 2 and all(v.get("link") for v in votes)


def test_a_faith_tells_its_beliefs_followers_and_who_told_whom(monkeypatch):
    from engine.details import describe
    from world.religion import ReligionType
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    faith = sim.religion.found_religion(a.id, a.name, ReligionType.ANIMISM, 10)
    sim.religion.convert_agent(a.id, faith.id)
    sim.religion.convert_agent(b.id, faith.id, by=a.id)
    f = check_shape(describe(sim, "faith", faith.id), "faith")
    titles = [s["title"] for s in f["sections"]]
    assert "What they believe" in titles and any(t.startswith("Followers") for t in titles)
    history = next(s for s in f["sections"] if s["title"] == "What has happened in it")["timeline"]
    assert any(f"{a.name} told {b.name}" in line["text"] for line in history)


def test_a_person_a_building_a_gathering_and_an_event_can_be_opened():
    from engine.details import describe
    from world.dynamic_buildings import Building
    sim, roles = make_world()
    a = roles["actor"]
    p = check_shape(describe(sim, "agent", a.id), "agent")
    assert any(f["label"] == "Partner" for f in p["facts"])
    hut = Building(id="hut", name="A's Hut", design_id="none", location=(50, 50), is_complete=True,
                   builder_ids={a.id}, shelter_value=0.8)
    sim.dynamic_building_system.buildings[hut.id] = hut
    check_shape(describe(sim, "building", "hut"), "building")
    sim.world.time.current_tick = 12 * 6
    gid = act(sim, a, "organize_event", details="a feast at 18:00").metadata["gathering_id"]
    g = check_shape(describe(sim, "gathering", gid), "gathering")
    assert g["title"].endswith("feast")
    event = sim.event_logger.events[-1]
    check_shape(describe(sim, "event", event.id), "event")


def test_knowhow_tells_how_it_spread_from_whom():
    from engine.details import describe
    from test_knowhow import dawn_world
    sim, roles = dawn_world()
    a, b = roles["actor"], roles["partner"]
    with quiet():
        sim.knowhow.learn(a, "stone_tools", "insight", 30)
        sim.knowhow.learn(b, "stone_tools", "taught", 40, teacher=a)
    k = check_shape(describe(sim, "knowhow", "stone_tools"), "knowhow")
    assert f"by {a.name}" in k["subtitle"]
    spread = next(s for s in k["sections"] if s["title"] == "How it spread")["timeline"]
    assert [line["text"] for line in spread] == [f"{a.name} taught {b.name}", f"{a.name} worked it out"]
    assert any(s["title"] == "Opens the way to" for s in k["sections"])


def test_the_endpoint_serves_details_and_404s_what_is_not_there():
    from fastapi.testclient import TestClient
    from api import server
    with TestClient(server.app) as client:
        agent = next(a for a in server.simulation.world.agents if a.alive)
        ok = client.get(f"/details/agent/{agent.id}")
        assert ok.status_code == 200 and ok.json()["title"] == agent.name
        assert client.get("/details/agent/nobody").status_code == 404
        assert client.get("/details/dragon/1").status_code == 404
        assert client.get("/details/knowhow/fire").status_code == 200
