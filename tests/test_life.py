"""
Life goes on: aging, life stages and natural death.

    python3 -m pytest tests/test_life.py -q
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world, quiet  # noqa: E402


def test_birthdays_and_coming_of_age():
    sim, roles = make_world()
    teen = roles["neighbour"]
    year = sim.config.ticks_per_life_year
    teen.age, teen.life_stage, teen.age_ticks = 15, "child", year - 1
    with quiet():
        sim.lifecycle_manager.update_aging(current_tick=1)
    assert teen.age == 16 and teen.age_ticks == 0 and teen.life_stage == "adult"
    assert sim.life_events["became_adult"] == 1
    assert any("come of age" in e.title for e in sim.event_logger.events)


def test_old_age_ends_a_life_once():
    from life.aging import yearly_old_age_risk
    assert yearly_old_age_risk(40) == 0.0
    assert 0.0 < yearly_old_age_risk(60) < yearly_old_age_risk(80) < yearly_old_age_risk(95)

    sim, roles = make_world()
    elder = roles["neighbour"]
    elder.age = 105
    random.seed(3)
    with quiet():
        for tick in range(1, 20 * sim.config.ticks_per_life_year):
            sim.lifecycle_manager.update_aging(tick)
            if not elder.alive:
                break
    assert not elder.alive and elder.death_cause == "old age"
    with quiet():
        sim.lifecycle_manager.handle_deaths()
        sim.lifecycle_manager.handle_deaths()
    assert sim.death_causes == {"old age": 1}  # counted once, however many ticks pass


def test_the_young_are_not_at_risk_of_old_age():
    sim, roles = make_world()
    random.seed(4)
    with quiet():
        for tick in range(1, 3 * sim.config.ticks_per_life_year):
            sim.lifecycle_manager.update_aging(tick)
    assert all(a.alive for a in roles.values())
