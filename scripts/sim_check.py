"""
Headless health check for Neuronaut World.

Runs the simulation without the web server, fast, across several random seeds,
and reports whether the society is healthy. Exits non-zero if it isn't, so it
can gate any change.

    python3 scripts/sim_check.py                 # 1200 ticks x 3 seeds, rule-based
    python3 scripts/sim_check.py --ticks 600 --seeds 1
    python3 scripts/sim_check.py --llm           # LLM decision path (falls back if no model)

    python3 scripts/sim_check.py --long          # 6000 ticks x 1 seed, tick time start vs end

PASS means, for every seed:
  - zero exceptions raised from tick()
  - at least MIN_ALIVE of 12 agents alive (earthquakes can legitimately kill one)
  - average health of living agents >= MIN_HEALTH
  - at least one finished building

It also reports what the agents created (governments, religions, couples,
births, trades, distinct actions chosen...). Those are measurements only: zero
is a valid result and they never affect PASS/FAIL.
"""
import argparse
import asyncio
import collections
import contextlib
import io
import logging
import os
import random
import resource
import sys
import time

MIN_ALIVE = 10
MIN_HEALTH = 70.0
NUM_AGENTS = 12


def max_rss_mb() -> float:
    """Peak resident memory of this process so far, in MB."""
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024  # bytes on macOS, KB on Linux


def emergence_metrics(sim, initial_ids, actions, successes) -> dict:
    """What the society created. Reported only; never part of PASS/FAIL."""
    from engine.simulation import UNHANDLED_ACTION_FALLBACKS
    from social.relationships import RelationshipType

    agents = list(sim.world.agents)
    alive = [a for a in agents if a.alive]
    religion_stats = sim.religion.get_statistics()
    couples = sum(1 for r in sim.relationship_manager.relationships.values()
                  if r.relationship_type == RelationshipType.ROMANCE)
    trades_ok = sum(n for action, n in successes.items()
                    if UNHANDLED_ACTION_FALLBACKS.get(action, action) == "trade")
    return {
        "governments": len(sim.governance_manager.governments),
        "laws": len(sim.governance_manager.laws),
        "religions": religion_stats["total_religions"],
        "followers": religion_stats["total_followers"],
        "rituals": religion_stats["rituals_performed"],
        "innovations": len(sim.innovation_manager.innovations),
        "discoveries": len(sim.experimentation_engine.discoveries),
        "couples": couples,
        "births": sum(1 for a in agents if a.id not in initial_ids),
        "deaths_by_cause": dict(collections.Counter(a.death_cause for a in agents if not a.alive)),
        "money": round(sum(a.wealth for a in alive), 1),
        "trades_ok": trades_ok,
        "distinct_actions": len(actions),
    }


def run_seed(ticks: int, seed: int, use_llm: bool) -> dict:
    os.environ["USE_LLM_DECISIONS"] = "true" if use_llm else "false"
    os.environ.setdefault("ENABLE_SEMANTIC_MEMORY", "false")
    random.seed(seed)

    with contextlib.redirect_stdout(io.StringIO()):
        from engine.simulation import SimulationEngine
        from agents.agent import NeedType
        sim = SimulationEngine(world_width=100, world_height=100)
        sim.initialize_world(num_agents=NUM_AGENTS)
    initial_ids = {a.id for a in sim.world.agents}

    actions, failures, errors = collections.Counter(), collections.Counter(), collections.Counter()
    successes = collections.Counter()
    original = sim.execute_action

    async def counted(agent, action):
        result = await original(agent, action)
        actions[action.action_type.value] += 1
        if isinstance(result, dict) and not result.get("success", True):
            failures[(action.action_type.value, str(result.get("message", ""))[:60])] += 1
        elif isinstance(result, dict):
            successes[action.action_type.value] += 1
        return result

    sim.execute_action = counted

    tick_seconds = []

    async def loop():
        for _ in range(ticks):
            t0 = time.perf_counter()
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    await sim.tick()
            except Exception as e:  # noqa: BLE001 - we want every failure counted
                errors[f"{type(e).__name__}: {e}"[:140]] += 1
            tick_seconds.append(time.perf_counter() - t0)

    start = time.time()
    asyncio.run(loop())

    agents = list(sim.world.agents)
    alive = [a for a in agents if a.alive]

    def avg(values):
        values = list(values)
        return sum(values) / len(values) if values else 0.0

    def need(agent, kind):
        n = agent.needs.needs.get(kind)
        return n.level if n else 0.0

    dbs = getattr(sim, "dynamic_building_system", None)
    buildings = list(dbs.buildings.values()) if dbs else []

    return {
        "seed": seed,
        "seconds": time.time() - start,
        "alive": len(alive),
        "health": avg(a.health for a in alive),
        "hunger": avg(need(a, NeedType.HUNGER) for a in alive),
        "thirst": avg(need(a, NeedType.THIRST) for a in alive),
        "buildings": sum(b.is_complete for b in buildings),
        # Agents record why they died in `death_cause` (this used to read a field
        # that doesn't exist, so every cause printed as None)
        "deaths": [(a.name, getattr(a, "death_cause", None)) for a in agents if not a.alive],
        "actions": actions,
        "failures": failures,
        "errors": errors,
        "emergence": emergence_metrics(sim, initial_ids, actions, successes),
        "tick_ms_start": 1000 * avg(tick_seconds[: max(1, ticks // 10)]),
        "tick_ms_end": 1000 * avg(tick_seconds[-max(1, ticks // 10):]),
        "max_rss_mb": max_rss_mb(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ticks", type=int, default=1200)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--llm", action="store_true", help="use the LLM decision path")
    parser.add_argument("--verbose", action="store_true", help="show top actions and failures")
    parser.add_argument("--long", action="store_true",
                        help="one long run (6000 ticks, 1 seed) to spot slowdowns and memory growth")
    args = parser.parse_args()
    if args.long:
        args.ticks, args.seeds = 6000, 1

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logging.disable(logging.WARNING)

    all_ok = True
    for seed in range(1, args.seeds + 1):
        r = run_seed(args.ticks, seed, args.llm)
        problems = []
        if r["errors"]:
            problems.append(f"{sum(r['errors'].values())} exceptions")
        if r["alive"] < MIN_ALIVE:
            problems.append(f"only {r['alive']}/{NUM_AGENTS} alive")
        if r["health"] < MIN_HEALTH:
            problems.append(f"avg health {r['health']:.0f} < {MIN_HEALTH:.0f}")
        if r["buildings"] < 1:
            problems.append("no finished buildings")
        ok = not problems
        all_ok &= ok

        print(f"[{'PASS' if ok else 'FAIL'}] seed {seed}: {args.ticks} ticks in {r['seconds']:.0f}s | "
              f"alive {r['alive']}/{NUM_AGENTS} | health {r['health']:.0f} | "
              f"hunger {r['hunger']:.2f} thirst {r['thirst']:.2f} | buildings {r['buildings']}"
              + (f" | {'; '.join(problems)}" if problems else ""))
        if r["deaths"]:
            print(f"    deaths: {r['deaths']}")
        print(f"    emergence: {r['emergence']}")
        if args.long:
            print(f"    tick time: first 10% {r['tick_ms_start']:.1f} ms, last 10% {r['tick_ms_end']:.1f} ms"
                  f" | peak memory {r['max_rss_mb']:.0f} MB")
        for msg, n in r["errors"].most_common(5):
            print(f"    error x{n}: {msg}")
        if args.verbose:
            print(f"    top actions: {r['actions'].most_common(12)}")
            print(f"    top failures: {r['failures'].most_common(8)}")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
