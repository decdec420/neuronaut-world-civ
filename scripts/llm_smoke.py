"""
Smoke test for the AI brain against a real model (or a fake one).

Runs a small village for ~50 ticks with USE_LLM_DECISIONS=true and reports:
model calls, latency, the share of answers that couldn't be read, distinct
actions chosen (by the model and overall), and sample decisions with the
agent's own stated reason, plus any day plans and reflections.

    python3 scripts/llm_smoke.py                # the model in .env (Ollama by default)
    python3 scripts/llm_smoke.py --ticks 100 --agents 6 --budget 2
    python3 scripts/llm_smoke.py --fake         # no model needed: canned answers

The village starts at 08:00 so agents are awake and plan their day. Each
tick waits up to --budget seconds for answers (default 10, so a CPU model
keeps up: expect ~5-10 minutes with llama3.2:3b on a laptop CPU).
Exit code: 0 if the model answered and its answers were read, 1 if not,
2 if no model is reachable (with steps to start one).
"""
import argparse
import asyncio
import collections
import contextlib
import io
import json
import logging
import os
import random
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def model_reachable(cfg) -> str:
    """'' if a model can be asked, else why not."""
    if cfg.get_api_keys():
        return ""
    import requests
    try:
        tags = requests.get(f"{cfg.ollama_host.rstrip('/')}/api/tags", timeout=5).json()
    except Exception as e:  # report, don't hide
        return f"Ollama isn't answering at {cfg.ollama_host} ({type(e).__name__})"
    names = {m.get("name") for m in tags.get("models", [])}
    if cfg.ollama_model not in names and f"{cfg.ollama_model}:latest" not in names:
        return f"Ollama is running but {cfg.ollama_model} isn't pulled (have: {', '.join(sorted(names)) or 'none'})"
    return ""


def fake_complete(menu_names):
    """Plausible answers in the shapes the real model is asked for."""
    rng = random.Random(7)
    everyday = [a for a in ("gather_food", "gather_water", "build", "socialize", "tell_story", "explore",
                            "experiment", "trade", "rest", "create_art", "worship", "govern")
                if a in menu_names]

    def complete(prompt, schema=None):
        time.sleep(0.05)
        props = (schema or {}).get("properties", {})
        if "plan" in props:
            return json.dumps({"plan": [{"hour": h, "action": rng.choice(everyday), "why": "it needs doing"}
                                        for h in (9, 12, 16)]})
        if "insights" in props:
            return json.dumps({"insights": ["I work hard but I'm often thirsty"]})
        if "lines" in props:
            names = props["lines"]["items"]["properties"]["speaker"]["enum"]
            return json.dumps({"lines": [{"speaker": names[0], "text": "Good to see you."},
                                         {"speaker": names[-1], "text": "And you. Heard any news?"}]})
        return json.dumps({"action": rng.choice(everyday), "target": "none", "reason": "it seems sensible"})
    return complete


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ticks", type=int, default=50)
    parser.add_argument("--agents", type=int, default=4)
    parser.add_argument("--budget", type=float, default=10.0,
                        help="seconds each tick waits for answers (LLM_TICK_BUDGET); a smoke test "
                             "wants answers, so it waits longer than a normal run's 2 s")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--fake", action="store_true", help="canned answers instead of a model (no network)")
    args = parser.parse_args()

    os.environ["USE_LLM_DECISIONS"] = "true"
    os.environ["LLM_TICK_BUDGET"] = str(args.budget)
    os.environ.setdefault("ENABLE_SEMANTIC_MEMORY", "false")
    logging.disable(logging.WARNING)
    random.seed(args.seed)
    import config
    config.reset_config()
    cfg = config.load_config()

    why_not = "" if args.fake else model_reachable(cfg)
    if why_not:
        print(f"No model to talk to: {why_not}.\n"
              f"  1. Install Ollama from https://ollama.com (or: brew install ollama)\n"
              f"  2. ollama serve            (leave it running)\n"
              f"  3. ollama pull {cfg.ollama_model}\n"
              f"  4. python3 scripts/llm_smoke.py\n"
              f"Or run with --fake to check the plumbing without a model.")
        return 2

    with contextlib.redirect_stdout(io.StringIO()):
        from engine.simulation import SimulationEngine
        sim = SimulationEngine(world_width=100, world_height=100)
        sim.initialize_world(num_agents=args.agents)
    sim.world.time.advance(6 * 8)  # 08:00: awake, time to plan the day
    brain, thinking = sim.llm_brain, sim._agent_updater.thinking

    # Record every model call: what kind of thought, how long, what came back
    calls = []
    inner = brain.complete if not args.fake else None
    fake = fake_complete(brain.action_menu.names) if args.fake else None

    def recorded(prompt, schema=None):
        props = (schema or {}).get("properties", {})
        kind = "plan" if "plan" in props else "reflect" if "insights" in props else \
            "talk" if "lines" in props else "decide"
        start = time.perf_counter()
        answer = fake(prompt, schema) if fake else inner(prompt, label="smoke", json_schema=schema)
        calls.append({"kind": kind, "seconds": time.perf_counter() - start, "answer": answer})
        return answer
    thinking.complete = recorded

    # Which actions the AI chose (and why), and every action taken
    ai_choices = []
    original_parse = None
    actions = collections.Counter()
    execute = sim.execute_action

    async def counted(agent, action):
        actions[action.action_type.value] += 1
        return await execute(agent, action)
    sim.execute_action = counted
    for agent in sim.world.agents:
        original_parse = agent._parse_action_from_llm

        def parse(text, perceptions=None, _agent=agent, _orig=original_parse):
            action = _orig(text, perceptions)
            if action is not None:
                target = sim._get_agent_by_id(action.target_agent) if action.target_agent else None
                ai_choices.append((_agent.name, action.action_type.value, target.name if target else None,
                                   action.parameters.get("reason", "")))
            return action
        agent._parse_action_from_llm = parse

    model = "fake" if args.fake else (", ".join(cfg.get_api_keys()) or f"{cfg.ollama_model} at {cfg.ollama_host}")
    print(f"Model: {model} | {args.agents} agents, {args.ticks} ticks from 08:00 | "
          f"workers {thinking.workers}, think every {thinking.think_every} ticks, tick budget {thinking.tick_budget:.0f} s")
    errors = collections.Counter()
    start = time.time()

    async def run():
        for _ in range(args.ticks):
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    await sim.tick()
            except Exception as e:  # count, report
                errors[f"{type(e).__name__}: {e}"[:120]] += 1
    asyncio.run(run())
    elapsed = time.time() - start
    thinking.wait(budget=0)
    thinking.close()

    answered = [c for c in calls if c["answer"]]
    latencies = [c["seconds"] for c in answered]
    decisions = [c for c in answered if c["kind"] == "decide"]
    stats = brain.get_stats()
    unreadable = stats["parse_failures"]
    read = stats["decisions_parsed"]
    print(f"Ran {args.ticks} ticks in {elapsed:.0f} s ({elapsed / args.ticks:.1f} s per tick)")
    print(f"Model calls: {len(calls)} ({len(calls) - len(answered)} without an answer) | "
          + (f"latency avg {statistics.mean(latencies):.1f} s, median {statistics.median(latencies):.1f} s, "
             f"max {max(latencies):.1f} s" if latencies else "no latency data"))
    by_kind = collections.Counter(c["kind"] for c in answered)
    print(f"Thoughts: {by_kind.get('decide', 0)} decisions, {by_kind.get('plan', 0)} day plans, "
          f"{by_kind.get('reflect', 0)} reflections, {by_kind.get('talk', 0)} conversations written")
    if read + unreadable:
        print(f"Decisions read: {read}/{read + unreadable} (parse failures {100 * unreadable / (read + unreadable):.0f}%)")
    print(f"Scheduler: {dict(thinking.stats)}")
    ai_actions = collections.Counter(a for _, a, _, _ in ai_choices)
    print(f"Distinct actions: {len(ai_actions)} chosen by the model {dict(ai_actions.most_common(8))}; "
          f"{len(actions)} overall")
    for name, action, target, reason in ai_choices[:6]:
        print(f"  {name}: {action}" + (f" -> {target}" if target else "") + (f" | {reason}" if reason else ""))
    for agent in sim.world.agents[:3]:
        if agent.memory_stream.day_plan:
            print(f"  {agent.name}'s plan: " + "; ".join(f"{h:02d}:00 {a} ({w})" for h, a, w in agent.memory_stream.day_plan))
    reflections = [(a.name, r.text) for a in sim.world.agents for r in a.memory_stream.records if r.kind == "reflection"]
    for name, text in reflections[:3]:
        print(f"  {name} reflected: {text}")
    talks = [e for e in sim.event_logger.events if e.title.startswith("💬")]
    for e in talks[:2]:
        print(f"  {e.title}: {e.description[:200]}")
    works, news = sim.infrastructure, sim.news
    print(f"Village: {len(works.roads)} road tiles, {len(works.wells)} wells, {len(works.lights)} street lights; "
          f"{news.conversations} conversations passed news on {news.told} times; "
          f"{len(sim.gatherings.upcoming) + len(sim.gatherings.history)} gatherings announced")
    if errors:
        print(f"Exceptions from tick(): {dict(errors)}")
    ok = bool(decisions) and read > 0 and not errors
    print("RESULT:", "OK" if ok else "PROBLEM (see above)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
