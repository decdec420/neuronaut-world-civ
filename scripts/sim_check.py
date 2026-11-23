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
  - at most NUM_AGENTS - MIN_ALIVE (2) deaths the agents could have prevented
    (hunger, thirst, exhaustion, illness, fights...), and somebody still alive.
    Natural disasters and old age are printed with every death but don't
    count: a catastrophic earthquake (5% of quakes) kills ~17% of a village
    whatever the code does (tests/test_disasters.py checks that shelter works)
  - average health of living agents >= MIN_HEALTH
  - at least one finished building

It also reports what the agents created (governments, religions, couples,
births, trades, distinct actions chosen...). Those are measurements only: zero
is a valid result and they never affect PASS/FAIL.

The same seed should give the same numbers every run, so a before/after
comparison measures the change and not luck. Parts of the sim walk sets
and sorted lists of ids, so two things the world's dice don't cover would
otherwise change the order things happen in:
  - Python's hash seed: the script pins PYTHONHASHSEED (0 unless you set
    one) by restarting itself;
  - ids from uuid.uuid4(), which uses the OS's randomness: during a check
    they come from a generator seeded with the run's seed (separate from
    the world's dice, so the world rolls exactly the same dice).
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


def natural_causes() -> set:
    """Causes of death no way of living prevents (old age, natural disasters,
    whose death_cause is the disaster type): reported, never a survival failure."""
    from world.disasters import DisasterType
    return {"old age"} | {d.value for d in DisasterType}
MIN_HEALTH = 70.0
NUM_AGENTS = 12


def max_rss_mb() -> float:
    """Peak resident memory of this process so far, in MB."""
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024  # bytes on macOS, KB on Linux


def emergence_metrics(sim, initial_ids, actions, successes) -> dict:
    """What the society created. Reported only; never part of PASS/FAIL."""
    from engine.simulation import UNHANDLED_ACTION_FALLBACKS

    agents = list(sim.world.agents)
    alive = [a for a in agents if a.alive]
    religion_stats = sim.religion.get_statistics()
    # Partnerships both agents chose (life/family.py), living ones now
    couples = sum(1 for a in alive if a.partner_id and any(b.id == a.partner_id for b in alive)) // 2
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
        "partnerships_formed": sim.life_events["partnered"],
        "separations": sim.life_events["separated"],
        "conceptions": sim.life_events["conceived"],
        "births": sum(1 for a in agents if a.id not in initial_ids),
        "children_alive": sum(1 for a in alive if a.life_stage in ("baby", "child")),
        "came_of_age": sim.life_events["became_adult"],
        "deaths_by_cause": dict(collections.Counter(a.death_cause for a in agents if not a.alive)),
        "glass_made": sim.products.get("glass", 0),
        "road_tiles": len(sim.infrastructure.roads),
        "wells": len(sim.infrastructure.wells),
        "street_lights": len(sim.infrastructure.lights),
        "tiles_saved_on_roads": sim.infrastructure.road_steps,
        "with_a_home": sum(1 for a in alive if getattr(a, "home_id", None)),
        "nights_slept_at_home": (f"{sim.life_events['slept_home'] / (sim.life_events['slept_home'] + sim.life_events['slept_out']):.0%}"
                                 if sim.life_events['slept_home'] + sim.life_events['slept_out'] else None),
        "kinds_of_things_made": len(sim.products),
        "money": round(sum(a.wealth for a in alive), 1),
        "trades_ok": trades_ok,
        "distinct_actions": len(actions),
        **news_metrics(sim),
    }


def news_metrics(sim) -> dict:
    """How news travels (Smallville measured this): conversations held, things
    passed on, and how far the important news got (share of the living who
    know each major item at least a day old)."""
    news = sim.news
    alive = [a.id for a in sim.world.agents if a.alive]
    now = sim.world.time.current_tick
    major = [n for n in news.items.values() if n.importance >= 0.8 and now - n.tick >= 144]
    reach = sorted(((news.reach(n.id, alive), n.text) for n in major), reverse=True)
    held = sim.gatherings.history
    return {
        "gatherings_held": len(held),
        "gathering_heard_vs_came": f"{sum(g.heard_before_start for g in held)}/{sum(len(g.attendees) for g in held)}"
                                   if held else None,
        "conversations": news.conversations,
        "news_passed_on": news.told,
        "major_news_reach": round(sum(r for r, _ in reach) / len(reach), 2) if reach else None,
        "widest_news": f"{reach[0][0]:.0%}: {reach[0][1][:60]}" if reach else None,
    }


_IDS = random.Random()


def _seed_ids(seed: int) -> None:
    """uuid4 ids from a generator seeded per run (see the docstring). One
    patched function, reseeded each run, so a module that kept a reference
    to uuid4 gets the same ids as one that looks it up each time."""
    import uuid
    if getattr(uuid.uuid4, "__name__", "") != "_seeded_uuid4":
        def _seeded_uuid4():
            return uuid.UUID(int=_IDS.getrandbits(128), version=4)
        uuid.uuid4 = _seeded_uuid4
    _IDS.seed(f"ids-{seed}")


def run_seed(ticks: int, seed: int, use_llm: bool) -> dict:
    os.environ["USE_LLM_DECISIONS"] = "true" if use_llm else "false"
    os.environ.setdefault("ENABLE_SEMANTIC_MEMORY", "false")
    os.environ.setdefault("AUTOSAVE_EVERY", "0")  # a check run leaves no save files behind
    random.seed(seed)
    _seed_ids(seed)

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
        "preventable_deaths": sum(1 for a in agents if not a.alive and a.death_cause not in natural_causes()),
        "actions": actions,
        "failures": failures,
        "errors": errors,
        "emergence": emergence_metrics(sim, initial_ids, actions, successes),
        "tick_ms_start": 1000 * avg(tick_seconds[: max(1, ticks // 10)]),
        "tick_ms_end": 1000 * avg(tick_seconds[-max(1, ticks // 10):]),
        "max_rss_mb": max_rss_mb(),
        "ai": ai_stats(sim) if use_llm else None,
    }


def ai_stats(sim) -> dict:
    """How the AI brain did: model calls, latency, readable answers, and how
    many decisions its answers made (agents/thinking.py)."""
    brain = getattr(sim, "llm_brain", None)
    thinking = getattr(sim._agent_updater, "thinking", None)
    if brain is None or thinking is None:
        return {"model": "none"}
    stats = brain.get_stats()
    out = {k: stats[k] for k in ("calls", "call_failures", "average_latency_s", "decisions_parsed", "parse_failures")}
    out.update(dict(thinking.stats))
    out["tick_wait_s"] = round(thinking.wait_seconds, 1)
    thinking.close()
    return out


def main() -> int:
    if "PYTHONHASHSEED" not in os.environ:
        # Restart with a fixed hash seed so a seed means the same run every time
        os.environ["PYTHONHASHSEED"] = "0"
        os.execv(sys.executable, [sys.executable] + sys.argv)
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
        if r["preventable_deaths"] > NUM_AGENTS - MIN_ALIVE:
            problems.append(f"{r['preventable_deaths']} preventable deaths")
        if r["alive"] == 0:
            problems.append("nobody alive")
        if r["health"] < MIN_HEALTH:
            problems.append(f"avg health {r['health']:.0f} < {MIN_HEALTH:.0f}")
        if r["buildings"] < 1:
            problems.append("no finished buildings")
        ok = not problems
        all_ok &= ok

        print(f"[{'PASS' if ok else 'FAIL'}] seed {seed}: {args.ticks} ticks in {r['seconds']:.0f}s | "
              f"alive {r['alive']}/{NUM_AGENTS} | preventable deaths {r['preventable_deaths']} | health {r['health']:.0f} | "
              f"hunger {r['hunger']:.2f} thirst {r['thirst']:.2f} | buildings {r['buildings']}"
              + (f" | {'; '.join(problems)}" if problems else ""))
        if r["deaths"]:
            print(f"    deaths: {r['deaths']}")
        print(f"    emergence: {r['emergence']}")
        if r["ai"] is not None:
            print(f"    ai: {r['ai']}")
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
