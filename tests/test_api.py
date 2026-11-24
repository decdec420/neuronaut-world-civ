"""
The server as a viewer sees it: pages, the live websocket, and that live
updates survive errors (api/server.py).

    python3 -m pytest tests/test_api.py -q

Uses FastAPI's TestClient (needs httpx), which runs the app's startup: a
real world of 12 agents ticking in the background.
"""

import concurrent.futures
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from api import server  # noqa: E402

WAIT = 15  # seconds; a broken loop would otherwise hang the test forever


def _receive(ws, timeout=WAIT):
    with concurrent.futures.ThreadPoolExecutor(1) as pool:
        return pool.submit(ws.receive_json).result(timeout=timeout)


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(server, "BROADCAST_INTERVAL", 0.05)
    with TestClient(server.app) as c:
        yield c


def test_pages_are_served_from_any_working_directory(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    page = client.get("/app")
    assert page.status_code == 200 and "world-canvas" in page.text
    js = client.get("/app/town_map.js")
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]


def test_only_the_dashboard_is_served(client):
    """/game is the dashboard's old address; the old pages (a "classic" view,
    a crafting page whose button only showed an alert, a materials demo) are
    gone."""
    moved = client.get("/game", follow_redirects=False)
    assert moved.status_code in (302, 307) and moved.headers["location"] == "/app"
    for gone in ("/app/classic", "/inventory", "/materials_example"):
        assert client.get(gone).status_code == 404, gone


def test_politics_names_leaders_and_economy_counts_what_was_made(client):
    sim = server.simulation
    founder = sim.world.agents[0]
    from world.governance import GovernmentType
    gov = sim.governance_manager.agent_forms_government(founder.id, "Test Council", GovernmentType.DEMOCRACY)
    politics = client.get("/politics").json()
    mine = next(g for g in politics["governments"] if g["id"] == gov.id)
    assert mine["leader"] == founder.name and mine["leader_id"] == founder.id
    listed = next(g for g in client.get("/governments").json()["governments"] if g["id"] == gov.id)
    assert listed["leader"] == founder.name      # the Politics tab shows this one
    sim.action_successes["mint_coins"] += 1
    made = client.get("/economy").json()["made"]
    assert made["mint_coins"] >= 1 and "smelt_ore" in made


def test_the_websocket_sends_a_snapshot_then_updates(client):
    with client.websocket_connect("/ws") as ws:
        first = _receive(ws)
        assert "agents" in first and "town" in first
        update = _receive(ws)
        assert update["type"] == "simulation_update" and "agents" in update["data"]


def test_updates_carry_on_after_a_snapshot_fails(client):
    sim = server.simulation
    real = sim.get_state_snapshot
    failures = {"left": 2}

    def flaky():
        if failures["left"] > 0:
            failures["left"] -= 1
            raise RuntimeError("snapshot failed")
        return real()

    with client.websocket_connect("/ws") as ws:
        _receive(ws)                       # the first snapshot
        sim.get_state_snapshot = flaky
        update = _receive(ws)              # before the fix: the loop died, this never came
        assert update["type"] == "simulation_update"
        assert failures["left"] == 0


def test_a_closed_viewer_is_forgotten(client):
    with client.websocket_connect("/ws") as ws:
        _receive(ws)
        assert len(server.active_websockets) == 1
    # the endpoint's cleanup ran (and a second removal by the broadcast loop is harmless)
    for _ in range(100):
        if not server.active_websockets:
            break
        import time
        time.sleep(0.05)
    assert server.active_websockets == []
    server._drop_websocket(ws)  # already gone: no error


# ---------------------------------------------------------------- controls

def test_another_site_cannot_change_the_world(client):
    sim = server.simulation
    paused = sim.paused
    # a bare POST, as any web page could send it: refused, nothing changes
    r = client.post("/simulation/pause", headers={"Origin": "https://elsewhere.example"})
    assert r.status_code == 403 and sim.paused == paused
    # and the browser's preflight for the header is not granted to other sites
    pre = client.options("/simulation/pause", headers={
        "Origin": "https://elsewhere.example", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "x-neuronaut-control"})
    assert "access-control-allow-origin" not in {k.lower() for k in pre.headers}
    # reading the world stays open
    assert client.get("/simulation/status").status_code == 200


def test_the_dashboard_can_change_the_world(client):
    sim = server.simulation
    paused = sim.paused
    r = client.post("/simulation/pause", headers={"X-Neuronaut-Control": "1"})
    assert r.status_code == 200 and sim.paused != paused
    r = client.post("/simulation/speed", json={"speed": "fast"}, headers={"X-Neuronaut-Control": "1"})
    assert r.status_code == 200 and sim.tick_rate == 0.5


def test_an_admin_token_when_the_server_has_one(client, monkeypatch):
    monkeypatch.setenv("NEURONAUT_ADMIN_TOKEN", "s3cret-token")
    control = {"X-Neuronaut-Control": "1"}
    assert client.post("/simulation/pause", headers=control).status_code == 401
    wrong = dict(control, Authorization="Bearer nope")
    assert client.post("/simulation/pause", headers=wrong).status_code == 401
    right = dict(control, Authorization="Bearer s3cret-token")
    assert client.post("/simulation/pause", headers=right).status_code == 200
    assert client.get("/simulation/status").status_code == 200   # reading needs no token


# ------------------------------------------------------------------ health

def test_health_reports_whether_the_world_is_running(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok" and r.json()["alive_agents"] > 0
    server.simulation_task.cancel()             # the world's loop stops
    for _ in range(100):
        if server.simulation_task.done():
            break
        import time
        time.sleep(0.02)
    r = client.get("/health")
    assert r.status_code == 503 and r.json()["status"] == "down"


def test_settings_come_from_the_environment(monkeypatch):
    import config
    monkeypatch.setenv("NUM_AGENTS", "7")
    monkeypatch.setenv("PORT", "not-a-port")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("SAVE_DIR", "my_saves")
    config.reset_config()
    try:
        cfg = config.load_config()
        assert cfg.num_agents == 7 and cfg.port == 8000 and cfg.log_level == "DEBUG"
        assert cfg.host == "127.0.0.1"                       # this machine only, by default
        assert cfg.save_dir == config.REPO_DIR / "my_saves"  # not the working directory
    finally:
        config.reset_config()


# ------------------------------------------------------------------- saves

def test_saving_through_the_api(client, tmp_path, monkeypatch):
    from engine.save_manager import SaveManager
    monkeypatch.setattr(server, "save_manager", SaveManager(tmp_path))
    control = {"X-Neuronaut-Control": "1"}
    assert client.post("/saves", json={"name": "x" * 81}, headers=control).status_code == 422
    r = client.post("/saves", json={"name": "Harvest festival"}, headers=control)
    assert r.status_code == 200 and r.json()["id"]
    listed = client.get("/saves").json()["saves"]
    assert [s["name"] for s in listed] == ["Harvest festival"] and listed[0]["state_filename"]


def test_a_profile_tells_the_agents_story_and_has_real_mood(client):
    from api import server
    agent = next(a for a in server.simulation.world.agents if a.alive)
    profile = client.get(f"/agents/{agent.id}/profile").json()
    story = profile["story"]
    assert {"doing", "set_out", "life_stage", "generation", "partner", "parents", "children",
            "home", "faith", "knows", "memories"} <= set(story)
    assert story["generation"] == 1 and isinstance(story["memories"], list)
    # the dashboard reads mood, stress and satisfaction from here (they showed NaN)
    assert all(isinstance(profile["psychology"][k], (int, float)) for k in ("mood", "stress", "life_satisfaction"))
