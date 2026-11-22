"""
End-to-end proofs that the world's capabilities work when agents choose them.

Each test sets up a small village and has agents take actions directly
("A founds a government", "B joins"), to prove the path works. The sim itself
never forces any of this; whether it happens is up to the agents.

    python3 -m pytest tests/test_capabilities.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world, quiet  # noqa: E402


def act(sim, agent, name, target=None, **params):
    """Have an agent validate and execute an action. Returns the ActionResult."""
    from agents.agent import Action, ActionType
    action = Action(ActionType(name), target_agent=target.id if target else None, parameters=params)
    handler = sim._handler_registry.get_handler(action.action_type)
    with quiet():
        ok, reason = handler.validate(agent, action)
        assert ok, f"{name} rejected: {reason}"
        return handler.execute(agent, action)


def befriend(sim, a, b, strength=0.9):
    from social.relationships import RelationshipType
    with quiet():
        rel = sim.relationship_manager.get_relationship(a.id, b.id)
        if rel is None:
            rel = sim.relationship_manager.create_relationship(a.id, b.id, RelationshipType.FRIENDSHIP, strength)
        rel.strength = strength


def test_governance_found_join_law_vote_elect_enforce_repeal():
    from world.governance import GovernmentType
    sim, roles = make_world()
    a, b, c = roles["actor"], roles["neighbour"], roles["sick"]
    gm = sim.governance_manager
    a.personality.openness, a.personality.conscientiousness, a.personality.aggression = 0.9, 0.5, 0.1

    # A founds a democracy; B, who likes A, joins it rather than founding another
    assert act(sim, a, "govern").metadata.get("founded")
    gov = gm.get_agent_government(a.id)
    assert gov.government_type == GovernmentType.DEMOCRACY and gov.leader_id == a.id
    befriend(sim, b, a)
    assert act(sim, b, "govern").metadata.get("joined")
    assert b.id in gov.citizens and len(gm.governments) == 1

    # A proposes a law; B votes on it (a real target, found by the handler)
    law_result = act(sim, a, "make_law", details="no fighting in the village")
    law = gm.laws[law_result.metadata["law_id"]]
    assert law.prohibition == "fight" and law.active
    assert act(sim, b, "vote").metadata["vote_type"] == "law"
    assert b.id in law.supporters | law.opposers

    # The democracy holds an election; B stands, A votes, the count makes a leader
    gm.update_governments(current_tick=gm.ELECTION_EVERY + 1)
    election = gm.open_election(gov.id)
    assert election is not None
    assert act(sim, b, "govern").metadata.get("candidate")
    assert act(sim, a, "vote").metadata["vote_type"] == "election"
    gm.update_governments(current_tick=election.ends_tick)
    assert election.complete and gov.leader_id == election.winner

    # B fights within sight of A: the law is broken and noticed
    sim._agent_updater._observe_laws(b, "fight", current_tick=1)
    assert law.times_broken == 1 and law.times_enforced == 1

    # C joins; with B and C against it, the law is repealed
    befriend(sim, c, a)
    act(sim, c, "govern")
    gm.vote_on_law(b.id, law.id, False)
    gm.vote_on_law(c.id, law.id, False)
    gm.update_governments(current_tick=election.ends_tick + 1)
    assert not law.active


def test_nothing_to_vote_on_is_rejected_up_front():
    from agents.agent import Action, ActionType
    sim, roles = make_world()
    handler = sim._handler_registry.get_handler(ActionType.VOTE)
    ok, reason = handler.validate(roles["actor"], Action(ActionType.VOTE))
    assert not ok and reason == "Nothing to vote on"


def test_religion_found_join_ritual_temple_convert_lapse():
    sim, roles = make_world()
    a, b, d = roles["actor"], roles["neighbour"], roles["partner"]
    rel = sim.religion

    # Nobody A cares about has a faith, so worshipping founds one
    founded = act(sim, a, "worship")
    assert founded.metadata.get("founded")
    faith = rel.get_agent_religion(a.id)

    # B likes A, so B's worship joins A's faith instead of founding another
    befriend(sim, b, a)
    assert act(sim, b, "worship").metadata.get("joined")
    assert b.id in faith.followers and len(rel.religions) == 1

    # A leads a ritual (B is nearby and takes part) and builds a temple
    assert act(sim, a, "perform_ritual").metadata["participants"] >= 2
    assert act(sim, a, "build_temple").success

    # D, who cares for nobody in A's faith, founds a second one; B comes to
    # like D far more than A and converts
    befriend(sim, d, a, 0.0)
    befriend(sim, d, b, 0.0)
    assert act(sim, d, "worship").metadata.get("founded")
    befriend(sim, b, a, 0.1)
    befriend(sim, b, d, 0.95)
    assert act(sim, b, "worship").metadata.get("joined")
    assert b.id not in faith.followers and b.id in rel.get_agent_religion(d.id).followers

    # A faith nobody practises fades: A lapses after LAPSE_TICKS without practice
    rel.record_practice(a.id, 0)
    lapsed = rel.lapse_inactive_followers(rel.LAPSE_TICKS)
    assert a.id in lapsed and rel.get_agent_religion(a.id) is None


def test_inventions_are_recorded_once_and_spread_by_teaching():
    sim, roles = make_world()
    a, b = roles["actor"], roles["neighbour"]
    innovations = sim.innovation_manager
    updater = sim._agent_updater

    # A succeeds at an experiment; whatever it made is A's invention
    for _ in range(200):
        result = act(sim, a, "experiment")
        updater._record_invention(a, "experiment", result.to_dict(), current_tick=1)
        if result.success:
            break
    assert result.success and len(innovations.innovations) == 1
    invention = next(iter(innovations.innovations.values()))
    assert invention.discoverer_id == a.id
    assert invention.name == result.metadata["discovered_material"].replace("_", " ")
    assert innovations.experiment_log

    # Making the same thing again is not a new invention
    updater._record_invention(b, "experiment", {"success": True, "discovered_material": invention.name.replace(" ", "_")}, 2)
    assert len(innovations.innovations) == 1 and innovations.agent_knows(b.id, invention.id)

    # Teaching passes an invention on
    c = roles["partner"]
    assert not innovations.agent_knows(c.id, invention.id)
    for _ in range(50):
        if act(sim, a, "teach", target=c).success:
            break
    assert innovations.agent_knows(c.id, invention.id)
