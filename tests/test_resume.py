"""
The world carries on across restarts (api/server.py _start_world, _save_on_stop):
the server saves the world when it stops and, with RESUME=last (the default),
carries on the newest playable save when it starts. Before, every start began
a new world.
"""

import asyncio
import contextlib
import gzip
import io

import pytest
from fastapi.testclient import TestClient

import config
from api import server


@pytest.fixture()
def saves(tmp_path, monkeypatch):
    """A save folder of its own, saves on, carrying on at start."""
    monkeypatch.setenv("SAVE_DIR", str(tmp_path))
    monkeypatch.setenv("AUTOSAVE_EVERY", "1000")
    monkeypatch.setenv("RESUME", "last")
    monkeypatch.setattr(server, "BROADCAST_INTERVAL", 0.05)
    config.reset_config()
    yield tmp_path
    config.reset_config()


def _run_ticks(sim, n):
    async def go():
        for _ in range(n):
            with contextlib.redirect_stdout(io.StringIO()):
                await sim.tick()
    asyncio.run(go())


def _save(sim, name):
    from engine.save_manager import SaveManager
    manager = SaveManager()
    with contextlib.redirect_stdout(io.StringIO()):
        assert manager.create_save(name, sim.persistence.create_snapshot(), simulation=sim)
    return manager.last_save_id


def test_stopping_saves_the_world_and_starting_carries_it_on(saves):
    with TestClient(server.app) as client:
        server.simulation.paused = True
        _run_ticks(server.simulation, 30)
        tick = server.simulation.world.time.current_tick
        names = sorted(a.name for a in server.simulation.world.agents)
        assert client.get("/health").json()["world"]["kind"] == "new"
    from engine.save_manager import SaveManager
    stopped = [s for s in SaveManager().list_saves() if s["name"].startswith("Stopped on day")]
    assert len(stopped) == 1 and stopped[0]["state_filename"]

    with TestClient(server.app) as client:
        world = client.get("/health").json()["world"]
        assert world["kind"] == "resumed" and world["save"] == stopped[0]["name"]
        assert server.simulation.world.time.current_tick >= tick
        assert sorted(a.name for a in server.simulation.world.agents) == names


def test_resume_new_begins_a_new_world(saves, monkeypatch):
    with TestClient(server.app):
        server.simulation.paused = True
        _run_ticks(server.simulation, 20)
    monkeypatch.setenv("RESUME", "new")
    config.reset_config()
    with TestClient(server.app) as client:
        assert client.get("/health").json()["world"]["kind"] == "new"
        assert server.simulation.world.time.current_tick < 20


def test_the_newest_playable_save_is_carried_on(saves):
    """Not a save where everyone had died, and not one that won't load."""
    from engine.save_manager import SaveManager
    from engine.simulation import SimulationEngine
    with contextlib.redirect_stdout(io.StringIO()):
        sim = SimulationEngine(world_width=100, world_height=100)
        sim.initialize_world(num_agents=12)
    _run_ticks(sim, 12)
    good = _save(sim, "The living village")

    for a in sim.world.agents:
        a.alive = False
    _save(sim, "Everyone gone")
    newest = SaveManager().newest_first()[0]      # made in the same second as the other: still the newest
    assert newest["name"] == "Everyone gone" and newest["stats"]["alive_agents"] == 0

    found = server._newest_playable_save()
    assert found is not None and found[0]["id"] == good


def test_a_save_that_wont_load_begins_a_new_world(saves):
    from engine.simulation import SimulationEngine
    with contextlib.redirect_stdout(io.StringIO()):
        sim = SimulationEngine(world_width=100, world_height=100)
        sim.initialize_world(num_agents=12)
    save_id = _save(sim, "Damaged")
    from engine.save_manager import SaveManager
    path = SaveManager().state_path(save_id)
    with gzip.open(path, "wb") as f:
        f.write(b"not a world")
    with TestClient(server.app) as client:
        assert client.get("/health").json()["world"]["kind"] == "new"
        assert client.get("/health").status_code == 200


def test_nothing_is_saved_when_saves_are_off(saves, monkeypatch):
    monkeypatch.setenv("AUTOSAVE_EVERY", "0")
    config.reset_config()
    with TestClient(server.app):
        pass
    from engine.save_manager import SaveManager
    assert SaveManager().list_saves() == []
