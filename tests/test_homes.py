"""
Homes: agents live somewhere and go home to sleep (life/homes.py).

    python3 -m pytest tests/test_homes.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act  # noqa: E402
from test_reachability import make_world, quiet  # noqa: E402


def _hut(sim, builder, x=50, y=50, bid="hut"):
    from world.dynamic_buildings import Building
    b = Building(id=bid, name=f"{builder.name}'s Hut", design_id="none", location=(x, y),
                 is_complete=True, builder_ids={builder.id}, shelter_value=0.8)
    sim.dynamic_building_system.buildings[b.id] = b
    return b


def _night(sim):
    sim.world.time.current_tick, sim.world.time.hour = 22 * 6, 22


def test_a_finished_shelter_is_home_to_its_builder_and_household():
    sim, roles = make_world()
    a, b, d = roles["actor"], roles["partner"], roles["neighbour"]  # a and b are partners
    hut = _hut(sim, a)
    sim._agent_updater._move_into(a, hut.id, 5)
    assert a.home_id == hut.id and b.home_id == hut.id and d.home_id is None
    assert any("is my home now" in r.text for r in a.memory_stream.records)


def test_at_night_an_agent_walks_home_and_sleeps_better_there():
    from agents.agent import Position
    from engine.psychology import NeedType
    sim, roles = make_world()
    a = roles["actor"]
    hut = _hut(sim, a, 50, 50)
    a.home_id = hut.id
    _night(sim)
    a.location, a.energy = Position(60, 50), 50.0
    result = act(sim, a, "rest")
    assert "Heading home" in result.message and a.location.x < 60 and a.energy == 50.0
    a.location = Position(50, 50)
    a.needs.needs[NeedType.SHELTER].level = 0.8
    act(sim, a, "rest")
    assert a.energy == 80.0 and a.needs.needs[NeedType.SHELTER].level < 0.8  # +30 at home
    assert sim.life_events["slept_home"] == 1

    # Exhausted: sleeps where it drops
    a.location, a.energy = Position(70, 50), 10.0
    act(sim, a, "rest")
    assert a.location.x == 70 and a.energy == 30.0 and sim.life_events["slept_out"] == 1

    # By day, rest is rest wherever you are
    sim.world.time.hour = 12
    a.energy = 50.0
    act(sim, a, "rest")
    assert a.location.x == 70 and a.energy == 70.0


def test_partners_share_a_home_and_a_collapsed_home_is_gone():
    sim, roles = make_world()
    c, d = roles["sick"], roles["neighbour"]
    hut = _hut(sim, c)
    c.home_id = hut.id
    act(sim, d, "seek_romance", target=c)
    act(sim, c, "seek_romance", target=d)
    assert d.home_id == hut.id  # moved in with c
    hut.collapsed = True
    from life import homes
    assert homes.home_of(sim.dynamic_building_system, c) is None and c.home_id is None


def test_a_newborn_lives_with_its_mother():
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    mother = a if a.gender.value == "female" else b
    hut = _hut(sim, mother)
    mother.home_id = hut.id
    mother.is_pregnant, mother.pregnancy_partner_id = True, (b if mother is a else a).id
    with quiet():
        child = sim.lifecycle_manager.deliver_baby(mother, 10)
    assert child.home_id == hut.id
