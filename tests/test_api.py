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
