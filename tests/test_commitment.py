"""
Agents carry on with what they set out to do (agents/commitment.py): a walk
toward somewhere starts a commitment, arriving ends it, and the rule-based
brain feels a pull to carry on (agents/utility_brain.py COMMIT_PULL).

    python3 -m pytest tests/test_commitment.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act  # noqa: E402
from test_reachability import make_world  # noqa: E402


def _far_spot(sim, x, y, lo, hi):
    """A dry tile on the same land as (x, y), between lo and hi tiles away."""
    m = sim.world.map
    here = m.land_component.get((int(x), int(y)))
    return next((cx, cy) for (cx, cy), comp in sorted(m.land_component.items())
                if comp == here and lo <= ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5 <= hi)


def _gathering_far_from(sim, host, guest, lo=25, hi=35):
    from agents.agent import Position
    sim.world.time.current_tick = 12 * 6
    g = sim.gatherings.upcoming[act(sim, host, "organize_event", details="a feast at 18:00").metadata["gathering_id"]]
    assert sim.news.knows(guest.id, g.news_id)
    guest.location = Position(*_far_spot(sim, g.x, g.y, lo, hi))
    return g


def _do(sim, agent, name):
    """Run an action the way the tick does (sim.execute_action notes commitments)."""
    import asyncio
    from agents.agent import Action, ActionType
    from test_reachability import quiet
    with quiet():
        return asyncio.run(sim.execute_action(agent, Action(ActionType(name))))


def test_walking_somewhere_is_a_commitment_and_arriving_ends_it():
    from agents import commitment
    from world.gatherings import JOIN_RADIUS, LEAD_TICKS
    sim, roles = make_world()
    host, guest = roles["actor"], roles["partner"]
    g = _gathering_far_from(sim, host, guest, lo=7, hi=9)
    sim.world.time.current_tick = g.start - LEAD_TICKS     # as early as one may set off
    first = _do(sim, guest, "attend_event")
    assert first["success"] and "On the way" in first["message"], first
    c = commitment.current(guest, sim.world.time.current_tick)
    assert c is not None and c.action == "attend_event" and (c.x, c.y) == (g.x, g.y)
    since = c.since
    for _ in range(LEAD_TICKS):                       # keep walking; it's the same commitment
        sim.world.time.current_tick += 1
        result = _do(sim, guest, "attend_event")
        if "Waiting" in result["message"]:
            break
    assert "Waiting" in result["message"]
    assert ((guest.location.x - g.x) ** 2 + (guest.location.y - g.y) ** 2) ** 0.5 <= JOIN_RADIUS
    assert commitment.current(guest, sim.world.time.current_tick).since == since   # waiting: still under way
    sim.world.time.current_tick = g.start
    sim.gatherings.update(g.start)
    assert _do(sim, guest, "attend_event")["joined"]
    assert commitment.current(guest, sim.world.time.current_tick) is None          # arrived and done


def test_the_rule_brain_feels_the_pull_to_carry_on_more_if_conscientious():
    from agents import commitment
    from agents.utility_brain import UtilityBrain, COMMIT_PULL
    sim, roles = make_world()
    agent = roles["actor"]
    brain = UtilityBrain(sim, ["attend_event", "rest"])
    tick = sim.world.time.current_tick
    without = brain.utility(agent, "attend_event")
    agent.commitment = commitment.Commitment("attend_event", 10.0, 10.0, tick, tick)
    agent.personality.conscientiousness = 0.9
    keen = brain.utility(agent, "attend_event") - without
    agent.personality.conscientiousness = 0.1
    lax = brain.utility(agent, "attend_event") - without
    assert abs(keen - COMMIT_PULL * 1.4) < 1e-6 and abs(lax - COMMIT_PULL * 0.6) < 1e-6
    assert brain.utility(agent, "rest") == brain.utility(agent, "rest")   # other actions untouched
    # it runs out
    sim.world.time.current_tick = tick + commitment.MAX_TICKS + 1
    assert abs(brain.utility(agent, "attend_event") - without) < 1e-6
    assert agent.commitment is None


def test_something_that_cannot_be_done_ends_the_commitment():
    from agents import commitment
    from agents.agent import Action, ActionType
    import asyncio
    sim, roles = make_world()
    agent = roles["actor"]
    tick = sim.world.time.current_tick
    agent.commitment = commitment.Commitment("attend_event", 10.0, 10.0, tick, tick)
    result = asyncio.run(sim.execute_action(agent, Action(ActionType.ATTEND_EVENT)))   # heard of none
    assert not result["success"] and agent.commitment is None


def test_the_ai_brain_is_told_what_it_set_out_to_do():
    from agents import commitment
    from test_llm_brain import make_world as make_ai_world, quiet
    sim = make_ai_world()
    agent = sim.world.agents[0]
    tick = sim.world.time.current_tick
    agent.commitment = commitment.Commitment("attend_event", 40.0, 33.0, tick - 12, tick)
    perceptions = sim._perception_builder.build_perceptions(agent, sim.world.get_state())
    with quiet():
        prompt = sim.llm_brain._build_thinking_prompt(agent, perceptions, "decide_action")
    assert "You set out 2 hours ago to attend event, heading for (40, 33)" in prompt
