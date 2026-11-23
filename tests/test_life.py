"""
Life goes on: aging, life stages and natural death; children, by the
parents' own choice; growing up.

    python3 -m pytest tests/test_life.py -q
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world, quiet  # noqa: E402
from test_capabilities import act  # noqa: E402


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


def _try(sim, agent):
    from agents.agent import Action, ActionType
    handler = sim._handler_registry.get_handler(ActionType.TRY_FOR_CHILD)
    with quiet():
        ok, why = handler.validate(agent, Action(ActionType.TRY_FOR_CHILD))
        return (handler.execute(agent, Action(ActionType.TRY_FOR_CHILD)) if ok else None), why


def _have_baby(sim, a, b):
    """Both partners keep choosing to try until a child is on the way; then it's born."""
    random.seed(11)
    for _ in range(100):
        _try(sim, b)
        _try(sim, a)
        if a.is_pregnant or b.is_pregnant:
            break
    mother = a if a.is_pregnant else b
    assert mother.is_pregnant
    with quiet():
        return sim.lifecycle_manager.deliver_baby(mother, mother.pregnancy_start_tick + mother.pregnancy_duration_ticks)


def test_a_child_needs_both_partners_to_want_one():
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    random.seed(5)
    # A alone, however often: no pregnancy, and A learns B hasn't said yes
    first, _ = _try(sim, a)
    assert first.success and "like a child" in first.message
    again, _ = _try(sim, a)
    assert not again.success and not (a.is_pregnant or b.is_pregnant)
    # B says it too: now they can conceive (by chance, so they may try a few times)
    for _ in range(100):
        _try(sim, b)
        if a.is_pregnant or b.is_pregnant:
            break
        _try(sim, a)
    mother = a if a.is_pregnant else b
    assert mother.is_pregnant and mother.gender.value == "female"
    assert sim.life_events["conceived"] == 1


def test_a_couple_who_cannot_conceive_is_told_so():
    from agents.agent import Gender
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    b.gender = a.gender
    result, why = _try(sim, a)
    assert result is None and "can't conceive" in why


def test_birth_blends_both_parents_into_a_new_family_member():
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    for parent in (a, b):
        parent.personality.openness = 0.95
        parent.personality.aggression = 0.05
    names_before = {x.name for x in sim.world.agents}
    child = _have_baby(sim, a, b)
    assert child in sim.world.agents and child.age == 0 and child.life_stage == "baby"
    assert {child.mother_id, child.father_id} == {a.id, b.id}
    assert child.id in a.children_ids and child.id in b.children_ids
    assert child.name not in names_before
    # Inherited: both parents very open and gentle, so the child leans that way
    assert child.personality.openness > 0.6 and child.personality.aggression < 0.4
    rel = sim.relationship_manager.get_relationship(a.id, child.id)
    assert rel is not None and rel.relationship_type.value == "family"
    assert sim.life_events["born"] == 1 and not (a.is_pregnant or b.is_pregnant)


def test_the_young_can_only_do_some_things_and_cannot_be_courted():
    from agents.agent import Action, ActionType
    from life import family
    sim, roles = make_world()
    baby = _have_baby(sim, roles["actor"], roles["partner"])
    can_run = lambda who, name: sim._agent_updater._can_run(who, Action(ActionType(name)))
    assert can_run(baby, "rest") and not can_run(baby, "govern") and not can_run(baby, "gather_food")
    baby.age, baby.life_stage = 8, "child"
    assert can_run(baby, "pray") and not can_run(baby, "build") and not can_run(baby, "trade")
    ok, why = family.free_to_court(roles["neighbour"], baby)
    assert not ok and "child" in why
    # Coming of age opens everything
    baby.age_ticks, baby.age = sim.config.ticks_per_life_year - 1, 15
    with quiet():
        sim.lifecycle_manager.update_aging(1)
    assert baby.life_stage == "adult" and can_run(baby, "govern")


def test_looking_after_a_hungry_baby_feeds_it():
    from agents.agent import Action, ActionType
    from engine.psychology import NeedType
    sim, roles = make_world()
    a = roles["actor"]
    baby = _have_baby(sim, a, roles["partner"])
    baby.needs.needs[NeedType.HUNGER].level = 0.9
    food_before = a.inventory.items.get("food", 0)
    handler = sim._handler_registry.get_handler(ActionType.CARE_FOR_CHILD)
    with quiet():
        assert handler.validate(a, Action(ActionType.CARE_FOR_CHILD))[0]
        result = handler.execute(a, Action(ActionType.CARE_FOR_CHILD))
    assert result.success and result.metadata["fed"]
    assert baby.needs.needs[NeedType.HUNGER].level < 0.9 and a.inventory.items["food"] == food_before - 1
    # The rule brain feels that pull: a hungry child of one's own
    target, pull = sim._agent_updater.utility_brain._child_in_need(a)
    assert target == baby.id and pull > 0


def test_names_never_repeat_in_a_world():
    from agents.agent import Agent, Gender
    sim, roles = make_world()
    names = [a.name for a in sim.world.agents]
    for i in range(150):
        names.append(Agent(gender=Gender.MALE if i % 2 else Gender.FEMALE).name)
    assert len(names) == len(set(names))


def test_the_population_cap_stops_new_pregnancies_only():
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    sim.config.max_population = 4  # the 4 agents of make_world
    result, why = _try(sim, a)
    assert result is None and "population limit" in why
    sim.config.max_population = 5
    result, _ = _try(sim, a)
    assert result is not None and result.success


def test_a_wish_for_a_child_does_not_carry_over_to_a_new_partner():
    sim, roles = make_world()
    a, b, d = roles["actor"], roles["partner"], roles["neighbour"]
    from agents.agent import Gender
    d.gender = b.gender  # a and d could conceive together
    _try(sim, a)                                  # a tells b it wants a child
    b.alive = False
    sim.lifecycle_manager.handle_deaths()         # b dies; a is free
    sim.world.time.current_tick += 1
    act(sim, d, "seek_romance", target=a)
    act(sim, a, "seek_romance", target=d)         # a and d pair up
    assert a.partner_id == d.id
    result, _ = _try(sim, d)                       # d says it wants one...
    assert "like a child" in result.message        # ...which a never said to d
    assert not (a.is_pregnant or d.is_pregnant)
