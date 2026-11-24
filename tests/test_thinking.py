"""
Agents think in parallel, within a time budget (agents/thinking.py). No
network: the "model" here is a function that sleeps and answers.

    python3 -m pytest tests/test_thinking.py -q
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Agent:
    def __init__(self, i):
        self.id = f"a{i}"


def slow_model(seconds, answer="ACTION: rest"):
    def complete(prompt, schema=None):
        time.sleep(seconds)
        return f"{answer} ({prompt})"
    return complete


def test_calls_run_in_parallel_and_answers_arrive_within_the_budget():
    from agents.thinking import ThinkingScheduler
    t = ThinkingScheduler(slow_model(0.3), workers=3, think_every=5, tick_budget=2.0)
    agents = [Agent(i) for i in range(3)]
    start = time.perf_counter()
    assert t.start(agents, tick=0, build_prompt=lambda a: ("decide", a.id, None)) == 3
    t.wait()
    assert time.perf_counter() - start < 0.6  # three 0.3 s calls, not 0.9 s
    assert [t.take(a.id, 0) for a in agents] == [("decide", f"ACTION: rest ({a.id})") for a in agents]
    assert t.stats["on_time"] == 3
    t.close()


def test_a_slow_model_never_holds_the_tick_longer_than_the_budget():
    from agents.thinking import ThinkingScheduler
    t = ThinkingScheduler(slow_model(0.5), workers=2, think_every=1, tick_budget=0.1)
    agents = [Agent(i) for i in range(4)]
    assert t.start(agents, tick=0, build_prompt=lambda a: ("decide", a.id, None)) == 2  # only as many as workers
    start = time.perf_counter()
    t.wait()
    assert time.perf_counter() - start < 0.3
    assert t.take("a0", 0) is None  # not ready: the rule brain decides this tick
    # The others wait their turn rather than queueing behind a slow model
    assert t.start(agents, tick=1, build_prompt=lambda a: ("decide", a.id, None)) == 0
    time.sleep(0.6)
    assert t.take("a0", 2) == ("decide", "ACTION: rest (a0)") and t.stats["late"] == 1  # used on a later turn
    # Longest-waiting agents go next
    assert t.start(agents, tick=2, build_prompt=lambda a: ("decide", a.id, None)) == 2
    assert set(t.pending) == {"a2", "a3"}
    t.close()


def test_stale_answers_and_thinking_too_often():
    from agents.thinking import ThinkingScheduler
    t = ThinkingScheduler(slow_model(0.0), workers=1, think_every=6, tick_budget=1.0, max_age=10)
    agent = Agent(0)
    t.start([agent], tick=0, build_prompt=lambda a: ("decide", "p", None))
    t.wait()
    assert not t.is_due(agent.id, 3)  # an answer is waiting
    assert t.take(agent.id, 11) is None and t.stats["stale"] == 1  # too old to act on
    assert not t.is_due(agent.id, 5) and t.is_due(agent.id, 6)  # thinks every 6 ticks
    t.close()


def test_a_tick_with_a_slow_model_uses_late_answers_on_later_turns():
    """A whole tick: the model takes longer than the budget, so agents use the
    rule-based brain, and the answers are acted on when they arrive."""
    import asyncio
    from test_llm_brain import make_world, quiet
    os.environ["LLM_TICK_BUDGET"] = "0.05"
    os.environ["LLM_WORKERS"] = "4"
    os.environ["LLM_THINK_EVERY"] = "1"
    try:
        sim = make_world()
    finally:
        for key in ("LLM_TICK_BUDGET", "LLM_WORKERS", "LLM_THINK_EVERY"):
            os.environ.pop(key, None)
    thinking = sim._agent_updater.thinking
    assert thinking is not None and thinking.tick_budget == 0.05

    def complete(prompt, **kwargs):
        time.sleep(0.3)
        return '{"action": "create_art", "target": "none", "reason": "inspired"}'
    sim.llm_brain.complete = complete

    start = time.perf_counter()
    with quiet():
        asyncio.run(sim.tick())
    assert time.perf_counter() - start < 0.3 + 0.25  # didn't wait for 4 x 0.3 s
    assert thinking.stats["asked"] == 4 and thinking.stats["used"] == 0
    time.sleep(0.4)
    with quiet():
        asyncio.run(sim.tick())
    assert thinking.stats["late"] >= 1 and thinking.stats["used"] >= 1
    assert any(getattr(a, "ai_intent", (None,))[0] == "create_art" for a in sim.world.agents)
    thinking.close()


def test_smoke_script_runs_end_to_end_with_the_fake_model():
    import subprocess
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "llm_smoke.py")
    run = subprocess.run([sys.executable, script, "--fake", "--ticks", "15", "--agents", "3"],
                         capture_output=True, text=True, timeout=300)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "parse failures 0%" in run.stdout and "RESULT: OK" in run.stdout
