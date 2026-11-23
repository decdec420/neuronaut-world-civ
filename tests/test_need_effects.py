"""
The rule-based brain believes what the world does: every action it credits
with meeting a need really meets that need when it runs
(agents/utility_brain.py ACTION_NEEDS).

    python3 -m pytest tests/test_need_effects.py -q
    python3 scripts/need_effects.py            # the measured table, and any mismatch

The table used to be written by hand, and 52 of 61 actions were credited with
needs they never relieve. Needs that nothing relieved (recognition, creativity)
stayed urgent forever and kept pulling agents to the actions credited with
them: tell_story became 22% of everything agents did.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import build_action, make_world, prepare, quiet  # noqa: E402


def measure(name: str):
    """Run one action as a fairly needy agent; return (succeeded, {need: relief})."""
    sim, roles = make_world()
    prepare(sim, roles, name)
    actor = roles["actor"]
    for need in actor.needs.needs.values():
        need.level = 0.7
    action = build_action(sim, roles, name)
    before = {k.value: v.level for k, v in actor.needs.needs.items()}
    with quiet():
        result = asyncio.run(sim.execute_action(actor, action))
    ok = result.get("success") if isinstance(result, dict) else getattr(result, "success", False)
    after = {k.value: v.level for k, v in actor.needs.needs.items()}
    return bool(ok), {k: round(before[k] - after[k], 3) for k in before if before[k] - after[k] > 0.005}


def test_every_credited_need_is_really_met():
    from agents.utility_brain import ACTION_NEEDS, EFFECT_LATER
    wrong = []
    for name, credited in sorted(ACTION_NEEDS.items()):
        if name in EFFECT_LATER or not credited:
            continue
        ok, relieved = measure(name)
        assert ok, f"{name} didn't run in the test village"
        missing = [n.value for n in credited if n.value not in relieved]
        if missing:
            wrong.append(f"{name}: credited with {missing}, relieves {relieved}")
    assert not wrong, "the brain credits needs the world doesn't meet:\n" + "\n".join(wrong)


def test_actions_credited_with_nothing_really_meet_nothing():
    from agents.utility_brain import ACTION_NEEDS, EFFECT_LATER
    for name, credited in sorted(ACTION_NEEDS.items()):
        if credited or name in EFFECT_LATER:
            continue
        ok, relieved = measure(name)
        assert not relieved, f"{name} meets {relieved}: credit it in ACTION_NEEDS"


def test_a_successful_experiment_meets_what_the_brain_credits():
    from agents.utility_brain import ACTION_NEEDS
    from test_capabilities import act
    sim, roles = make_world()
    prepare(sim, roles, "experiment")
    actor = roles["actor"]
    for _ in range(200):
        for need in actor.needs.needs.values():
            need.level = 0.7
        result = act(sim, actor, "experiment")
        if result.success:
            break
        prepare(sim, roles, "experiment")
    assert result.success
    for need in ACTION_NEEDS["experiment"]:
        assert actor.needs.needs[need].level < 0.7, f"a successful experiment didn't meet {need.value}"
