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
