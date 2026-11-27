"""
Needs stay within 0-1, and the dead let go of land and guard duty
(engine/psychology.py Need.satisfy, world/territory.py forget_the_dead).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world  # noqa: E402


def test_a_need_made_more_pressing_stops_at_one():
    from engine.psychology import Need, NeedType
    need = Need(NeedType.SECURITY, level=0.95, decay_rate=0.0, priority=2)
    need.satisfy(-0.1)
    assert need.level == 1.0
    need.satisfy(0.3)
    assert abs(need.level - 0.7) < 1e-9


def test_trespassing_can_not_push_security_past_one():
    sim, roles = make_world()
    a, d = roles["actor"], roles["neighbour"]
    from world.territory import TerritoryType
    from engine.psychology import NeedType
    land = sim.territory.claim_territory(d.id, d.name, (a.location.x, a.location.y), 15.0, TerritoryType.PERSONAL, 0)
    sim.territory.add_guard(land.id, d.id)
    a.needs.needs[NeedType.SECURITY].level = 0.98
    import random
    random.seed(1)
    for tick in range(5):                 # standing in d's defended land, hour after hour
        sim._agent_updater._check_trespassing(a, tick)
    assert a.needs.needs[NeedType.SECURITY].level == 1.0


def test_the_dead_let_go_of_land_and_guard_duty():
    sim, roles = make_world()
    a, b, d = roles["actor"], roles["partner"], roles["neighbour"]
    from world.territory import TerritoryType
    owned = sim.territory.claim_territory(d.id, d.name, (10, 10), 15.0, TerritoryType.PERSONAL, 0)
    guarded = sim.territory.claim_territory(a.id, a.name, (80, 80), 15.0, TerritoryType.PERSONAL, 0)
    sim.territory.add_guard(guarded.id, b.id)
    assert guarded.defended

    b.alive = False                       # the guard dies
    d.alive = False                       # the owner dies
    sim.lifecycle_manager.handle_deaths()
    assert owned.id not in sim.territory.territories          # no one's now: free to claim
    assert sim.territory.get_territory_at_location((10, 10)) is None
    assert not guarded.defended and b.id not in guarded.guards
    assert guarded.id in sim.territory.territories             # its owner lives


def test_a_world_saved_before_this_lets_go_when_loaded():
    sim, roles = make_world()
    d = roles["neighbour"]
    from world.territory import TerritoryType
    land = sim.territory.claim_territory(d.id, d.name, (10, 10), 15.0, TerritoryType.PERSONAL, 0)
    d.alive = False
    d.death_recorded = True               # died before the release existed
    sim.ensure_newer_systems()
    assert land.id not in sim.territory.territories
