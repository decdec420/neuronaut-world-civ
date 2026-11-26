"""
Roles (world/roles.py) say what people do now, in words that fit:

- Work with no vocabulary of its own used to take the food-gathering words,
  so someone always courting was a "Harvester" and someone always at
  gatherings a "Plant-Knower". Now it has words of its own, or a plain name
  ("One-Who-Dances-Wildly").
- Roles never ended, so each person piled up five and the Roles tab counted
  126 "specialists" among 42 people. Now a role lapses when the agent mostly
  stops (below ROLE_LAPSES_BELOW) and comes back, name and all, if they take
  it up again.
- Naming uses the agent's own dice, not the world's: it doesn't change what
  happens next.

    python3 -m pytest tests/test_roles.py -q
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.roles import BehaviorPattern, RoleEmergence, LIFE_VOCABULARIES, one_who  # noqa: E402


FOOD_WORDS = {"Gatherer", "Forager", "Harvester", "Collector", "Provider", "Finder", "Plant-Knower",
              "Food-Bringer", "Forest-Walker", "Field-Tender", "Wild-Harvester"}


def pattern(action, share=0.4):
    return BehaviorPattern(f"specialized_{action}", [action], {}, share)


def test_names_fit_what_people_do():
    roles = RoleEmergence()
    for action in ("seek_romance", "attend_event", "care_for_child", "play_game", "patrol"):
        for seed in ("a", "b", "c", "d"):
            name = roles.generate_agent_role_name(pattern(action), agent_seed=seed)
            words = set(name.replace(" ", "-").split("-")) | {name}
            assert not words & FOOD_WORDS, (action, name)
            vocab = LIFE_VOCABULARIES[action]
            assert any(w in name for w in vocab["nouns"] + vocab["compounds"] + vocab["materials"]), (action, name)
    assert roles.generate_agent_role_name(pattern("dance_wildly"), agent_seed="a") == "One-Who-Dances-Wildly"
    assert one_who("try_for_child") == "One-Who-Tries-For-Child"


def test_naming_uses_the_agents_own_dice():
    roles = RoleEmergence()
    random.seed(7)
    before = random.random()
    random.seed(7)
    first = roles.generate_agent_role_name(pattern("gather_food"), agent_seed="agent-1")
    assert random.random() == before                       # the world's dice weren't touched
    assert roles.generate_agent_role_name(pattern("gather_food"), agent_seed="agent-1") == first


def test_roles_lapse_when_people_stop_and_return_when_they_start_again():
    roles = RoleEmergence()
    for _ in range(40):
        roles.record_action("x", "patrol")
    for _ in range(20):
        roles.record_action("x", "gather_food")
    found = {p.pattern_type: p for p in roles.detect_behavior_patterns("x")}
    role = roles.agent_discovers_role("x", "X", found["specialized_patrol"], agent_generated_name="Watcher")
    roles.record_action("x", "patrol")
    assert role.times_acted_in_role == 1
    for _ in range(95):                                     # they mostly stop patrolling
        roles.record_action("x", "gather_food")
    assert roles.review_roles("x", 500) == [role]
    assert not role.active and role.ended_tick == 500
    roles.record_action("x", "patrol")
    assert role.times_acted_in_role == 1                    # a lapsed role isn't counted
    for _ in range(40):                                     # and take it up again
        roles.record_action("x", "patrol")
    roles.review_roles("x", 900)
    assert role.active and role.ended_tick is None and role.custom_role_name == "Watcher"


def test_the_roles_view_puts_jobs_first_and_counts_each_role_once():
    from engine.society import roles_snapshot
    from test_reachability import make_world
    sim, roles = make_world()
    a = roles["actor"]
    a.work_life.job = "forager"
    a.work_life.recent_shifts.extend(["forager"] * 3 + ["builder"])
    sim.role_emergence.agent_roles[a.id] = []
    for _ in range(40):
        sim.role_emergence.record_action(a.id, "seek_romance")
    sim._update_role_emergence(300)
    view = roles_snapshot(sim)
    forager = next(j for j in view["jobs"] if j["key"] == "forager")
    assert {"id": a.id, "name": a.name, "share": 0.75} in forager["people"]
    mine = [r for r in view["current"] if r["agent_id"] == a.id]
    assert len(mine) == 1 and mine[0]["activity"] == "seek romance" and mine[0]["since_day"] == 3
    assert mine[0]["name"] not in FOOD_WORDS
