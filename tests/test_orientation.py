"""
Whom people are drawn to (life/family.py ORIENTATIONS, drawn_to): each person
has an orientation, drawn once, roughly as population surveys report. It
shapes attraction and whom the rule-based brain courts; nobody is made to pair
with anyone. Attraction used to ignore gender for everyone.

    python3 -m pytest tests/test_orientation.py -q
"""

import os
import random
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world, quiet  # noqa: E402


def person(gender, orientation):
    return SimpleNamespace(gender=SimpleNamespace(value=gender), orientation=orientation)


def test_orientations_are_drawn_roughly_as_in_human_populations():
    from life import family
    random.seed(5)
    draws = [family.draw_orientation() for _ in range(20000)]
    share = {o: draws.count(o) / len(draws) for o, _ in family.ORIENTATIONS}
    for name, expected in family.ORIENTATIONS:
        assert abs(share[name] - expected) < 0.01, (name, share[name])


def test_whom_people_are_drawn_to():
    from life import family
    man, woman = "male", "female"
    assert family.drawn_to(person(man, "other"), person(woman, "other"))
    assert not family.drawn_to(person(man, "other"), person(man, "other"))
    assert family.drawn_to(person(woman, "same"), person(woman, "other"))
    assert not family.drawn_to(person(woman, "same"), person(man, "other"))
    assert family.drawn_to(person(man, "both"), person(man, "other"))
    assert family.drawn_to(person(man, None), person(man, "other"))       # saved before orientations
    assert family.drawn_to(person("non_binary", "other"), person(man, "other"))


def test_the_rule_brain_courts_only_those_it_is_drawn_to():
    from agents.agent import Gender
    from social.relationships import RelationshipType
    sim, roles = make_world()
    seeker = roles["neighbour"]
    seeker.partner_id = None
    seeker.orientation = "other"
    others = [a for a in sim.world.agents if a is not seeker]
    for other in others:
        other.partner_id = None
        with quiet():
            sim.relationship_manager.create_relationship(seeker.id, other.id, RelationshipType.FRIENDSHIP, 0.5)
    for other in others:
        other.gender = seeker.gender                                       # nobody of the other sex
    brain = sim._agent_updater.utility_brain
    assert brain._romance_target(seeker, "seek_romance") == (None, 0.0)
    others[0].gender = Gender.FEMALE if seeker.gender == Gender.MALE else Gender.MALE
    for _ in range(20):
        assert brain._romance_target(seeker, "seek_romance")[0] == others[0].id


def test_the_ai_brain_is_told_whom_its_agent_is_drawn_to():
    from test_llm_brain import make_world as make_ai_world
    sim = make_ai_world()
    agent = sim.world.agents[0]
    agent.partner_id = None
    agent.orientation = "same"
    perceptions = sim._perception_builder.build_perceptions(agent, sim.world.get_state())
    with quiet():
        prompt = sim.llm_brain._build_thinking_prompt(agent, perceptions, "decide_action")
    assert "you are drawn to your own sex" in prompt
