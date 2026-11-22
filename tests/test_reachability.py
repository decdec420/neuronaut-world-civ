"""
Reachability map: can agents actually do every action the world offers?

The sim exists to see what agents create when they're in charge (CLAUDE.md,
"Design philosophy"). A capability that agents can never choose, or that never
works when they do, doesn't count as built. For every ActionType this checks:

  (a) handled     - a handler runs it, directly or via UNHANDLED_ACTION_FALLBACKS
  (b) rule brain  - the rule-based brain can ever propose it
  (c) LLM menu    - it is on the LLM brain's menu, and the LLM's answer
                    "ACTION: <name>" parses back to it
  (d) can succeed - its handler succeeds in at least one reasonable world
                    state, which this test builds and then executes

Names in UNHANDLED_ACTION_FALLBACKS are aliases ("gossip" runs `socialize`).
An alias inherits (b) and (d) from the action it runs; it still has to be on
the menu and parse correctly, so the LLM can use the word.

A test may set up the world so an action can work ("A and B courted each
other", "C is sick"). The sim itself never forces anything.

    python3 -m pytest tests/test_reachability.py -s   # assert + failure table
    python3 tests/test_reachability.py                 # full table
"""

import contextlib
import io
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ENABLE_SEMANTIC_MEMORY", "false")

# Deliberately not chosen by agents. Keep this short and say why.
INTERNAL_ACTIONS = {
    "idle": "what an agent does when nothing else is wanted; not a choice to offer",
    "wait": "same as idle",
    "give_birth": "happens at the end of a pregnancy, not something an agent picks",
}

ATTEMPTS = 25        # fresh worlds per action for (d)
TRIES_PER_WORLD = 8  # several outcomes are random (discoveries succeed 3-5% of the time)

# What an agent would do first so the action has something to work with.
# Each step is a real agent action, run until it succeeds (up to PREP_TRIES),
# so a failure here means agents can't get there either.
PREPARE = {
    "tend_crops": ["plant_crops"],
    "harvest": ["plant_crops", "<let crops grow>"],
    "build_temple": ["worship"], "perform_ritual": ["worship"],
    "make_law": ["govern"],
    "vote": ["govern", "make_law"],
    "guard": ["claim_territory"], "patrol": ["claim_territory"],
    "apply_for_loan": ["open_bank"],
    "operate_power_plant": ["build_power_plant"],
    "teach": ["experiment"],
    "write": ["experiment"],
    "create_alloy": ["refine_material"],
    "join_tax_revolt": ["<taxed by own government>"],
    "try_for_child": ["<partner wants a child>"],
    "care_for_child": ["<a baby is born>"],
    "build_road": ["<walks to the same place a few times>"],
    "build_streetlight": ["<makes glass>"],
    "attend_event": ["<a gathering is announced nearby>"],
}
PREP_TRIES = 60


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        yield


def _imports():
    with quiet():
        from engine import simulation as engine_simulation
        from agents import agent as agent_module
    return engine_simulation, agent_module


def canonical(name: str) -> str:
    engine_simulation, _ = _imports()
    return engine_simulation.UNHANDLED_ACTION_FALLBACKS.get(name, name)


# ---------------------------------------------------------------------------
# World states
# ---------------------------------------------------------------------------

def make_world(seed: int = 0, use_llm: bool = False):
    """A small, well-supplied village: actor A, partner B, sick C, neighbour D.

    Returns (sim, roles) where roles maps role name -> agent.
    """
    os.environ["USE_LLM_DECISIONS"] = "true" if use_llm else "false"
    random.seed(seed)
    import logging
    logging.disable(logging.WARNING)
    import config
    config.reset_config()  # the config is cached per process; re-read USE_LLM_DECISIONS
    with quiet():
        from engine.simulation import SimulationEngine
        from agents.agent import Position, Gender
        from social.relationships import RelationshipType
        sim = SimulationEngine(world_width=100, world_height=100)
        sim.initialize_world(num_agents=4)
    a, b, c, d = sim.world.agents[:4]
    for i, agent in enumerate((a, b, c, d)):
        agent.location = Position(50 + i, 50)
        agent.age = 25
        agent.energy = 100.0
        agent.health = 100.0
        agent.wealth = 500.0
        agent.inventory.capacity = 1000
    b.gender = Gender.FEMALE if a.gender == Gender.MALE else Gender.MALE
    # A and B are drawn to each other (some agents are; personalities vary)
    for agent in (a, b):
        agent.personality.sexuality = 0.9
        agent.personality.agreeableness = 0.8
        agent.personality.extraversion = 0.8
    from engine.psychology import NeedType
    a.needs.needs[NeedType.SEX].level = 0.9

    supplies = {"wood": 60, "stone": 60, "clay": 30, "plant_fiber": 30, "metal_ore": 40,
                "iron_ore": 30, "food": 20, "water": 20, "seeds": 10, "herbs": 10,
                "medicine": 5, "hide": 10, "sand": 10, "coal": 20}
    for agent in (a, b, d):
        for item, qty in supplies.items():
            agent.inventory.items[item] = qty
    for skill in ("construction", "gathering", "hunting", "literacy", "medicine",
                  "farming", "crafting", "chemistry", "teaching", "art", "trading"):
        a.skills.learn_skill(skill, 1.0)

    rel_mgr = sim.relationship_manager
    with quiet():
        rel_mgr.create_relationship(a.id, b.id, RelationshipType.ROMANCE, 0.9)
        rel_mgr.create_relationship(a.id, d.id, RelationshipType.FRIENDSHIP, 0.8)
        rel_mgr.create_relationship(a.id, c.id, RelationshipType.FRIENDSHIP, 0.8)

    # A and B court each other, so they are partners: both chose it
    from agents.agent import Action, ActionType
    romance = sim._handler_registry.get_handler(ActionType.SEEK_ROMANCE)
    with quiet():
        for who, other in ((a, b), (b, a)):
            romance.execute(who, Action(ActionType.SEEK_ROMANCE, target_agent=other.id))
    assert a.partner_id == b.id

    # C is ill, so there's someone to heal
    with quiet():
        from world.health import DiseaseType, Severity
        sim.health.infect_agent(c.id, DiseaseType.FLU, Severity.MODERATE, 0)

    return sim, {"actor": a, "partner": b, "sick": c, "neighbour": d}


# Targets/parameters that give each action something to act on. Actions not
# listed get the nearest other agent as target if they need one (the engine
# fills that in itself).
TARGETS = {
    "heal": "sick", "cure": "sick", "diagnose": "sick",
    "seek_romance": "partner", "separate": "partner", "try_for_child": "partner",
    "trade": "neighbour", "teach": "neighbour", "socialize": "neighbour",
    "tell_story": "neighbour", "play_game": "neighbour", "gamble": "neighbour",
    "fight": "neighbour",
}


def build_action(sim, roles, name: str):
    from agents.agent import Action, ActionType, Position
    actor = roles["actor"]
    target_role = TARGETS.get(name)
    target = roles[target_role].id if target_role else None
    position = Position(actor.location.x + 3, actor.location.y + 3)
    params = {}
    if name == "refine_material":
        params = {"details": "iron ore"}  # what create_alloy's preparation needs
    if name == "vote":
        laws = list(sim.governance_manager.laws)
        if laws:
            params = {"vote_target": laws[0], "choice": "yes"}
    return Action(ActionType(name), target_agent=target, target_position=position, parameters=params)


def attempt(sim, roles, name: str):
    """Validate and execute one action as the actor. Returns (success, why)."""
    from agents.agent import ActionType
    handler = sim._handler_registry.get_handler(ActionType(name))
    if handler is None:
        return False, "no handler"
    action = build_action(sim, roles, name)
    with quiet():
        ok, reason = handler.validate(roles["actor"], action)
        if not ok:
            return False, f"validate: {reason}"
        try:
            result = handler.execute(roles["actor"], action)
        except Exception as e:  # report, don't hide: this is a broken capability
            return False, f"execute raised {type(e).__name__}: {e}"
    return result.success, "" if result.success else f"execute: {result.message}"


def attempt_as(sim, agent, name: str, params: dict):
    """Validate and execute an action as any agent, with parameters."""
    from agents.agent import Action, ActionType
    handler = sim._handler_registry.get_handler(ActionType(name))
    action = Action(ActionType(name), parameters=params)
    with quiet():
        ok, reason = handler.validate(agent, action)
        if not ok:
            return False, f"validate: {reason}"
        result = handler.execute(agent, action)
    return result.success, "" if result.success else f"execute: {result.message}"


def prepare(sim, roles, name: str):
    """Run the actions an agent would do first. Returns None, or why it failed."""
    for step in PREPARE.get(name, []):
        if step == "<let crops grow>":
            for tick in range(1, 3000, 10):
                sim.world.time.current_tick = tick
                with quiet():
                    sim.agriculture.update_crops(tick)
            continue
        if step == "<taxed by own government>":
            # The neighbour founds a government, the actor (who likes them)
            # joins, and the neighbour proposes a tax: all agent actions
            neighbour, actor = roles["neighbour"], roles["actor"]
            neighbour.personality.aggression = 0.1
            for who, name, params in ((neighbour, "govern", {}), (actor, "govern", {}),
                                      (neighbour, "make_law", {"details": "a tax for the common good"})):
                ok, why = attempt_as(sim, who, name, params)
                if not ok:
                    return f"first needs {who.name} to {name}, which failed ({why})"
            continue
        if step == "<walks to the same place a few times>":
            actor = roles["actor"]
            for tick in range(8):
                sim.infrastructure.step_toward(actor, sim.pathfinder, 80, 80, tick)
            continue
        if step == "<a gathering is announced nearby>":
            hour = (sim.world.time.current_tick // 6 + 1) % 24  # the clock as ticks count it
            ok, why = attempt_as(sim, roles["neighbour"], "organize_event", {"details": f"a feast at {hour}:00"})
            if not ok:
                return f"first needs someone to organize a gathering, which failed ({why})"
            continue
        if step == "<makes glass>":
            ok, why = attempt_as(sim, roles["actor"], "refine_material", {"details": "sand into glass"})
            if not ok:
                return f"first needs glass, which failed ({why})"
            continue
        if step == "<partner wants a child>":
            ok, why = attempt_as(sim, roles["partner"], "try_for_child", {})
            if not ok:
                return f"first needs the partner to want a child, which failed ({why})"
            continue
        if step == "<a baby is born>":
            # The partners both choose to try for a child until one is on the
            # way, then the pregnancy runs its course
            actor, partner = roles["actor"], roles["partner"]
            for _ in range(PREP_TRIES):
                for who in (partner, actor):
                    attempt_as(sim, who, "try_for_child", {})
                if actor.is_pregnant or partner.is_pregnant:
                    break
            mother = actor if actor.is_pregnant else partner
            if not mother.is_pregnant:
                return "first needs a child, but no pregnancy came"
            with quiet():
                sim.lifecycle_manager.deliver_baby(mother, mother.pregnancy_start_tick + mother.pregnancy_duration_ticks)
            continue
        why = "never tried"
        for _ in range(PREP_TRIES):
            ok, why = attempt(sim, roles, step)
            if ok:
                break
        else:
            return f"first needs {step}, which failed ({why})"
    return None


def try_to_succeed(name: str):
    """(d): does the handler succeed in at least one fresh, well-supplied world?"""
    last = "never attempted"
    for seed in range(ATTEMPTS):
        sim, roles = make_world(seed=seed)
        blocked = prepare(sim, roles, name)
        if blocked:
            last = blocked
            continue
        for _ in range(TRIES_PER_WORLD):
            ok, why = attempt(sim, roles, name)
            if ok:
                return True, ""
            last = why
    return False, last


# ---------------------------------------------------------------------------
# (b) What the rule-based brain can produce
# ---------------------------------------------------------------------------

def rule_brain_actions(samples: int = 40):
    """Every action the rule-based decision path can come up with.

    The rule-based brain (agents/utility_brain.py) weighs every action it
    considers and samples among the ones that can run, so any considered
    action has a chance whenever it's possible. This also samples its
    choices over random agents to check that it really returns them, and
    adds the survival override that runs before it."""
    from agents.agent import NeedType
    produced = set()
    sim, roles = make_world()
    agent = roles["actor"]
    brain = sim._agent_updater.utility_brain
    produced |= set(brain.considered_actions())

    perceptions = sim._perception_builder.build_perceptions(agent, sim.world.get_state())
    rng = random.Random(1)
    traits = [t for t in vars(agent.personality) if isinstance(getattr(agent.personality, t), float)]
    sampled = set()
    for _ in range(samples):
        for t in traits:
            setattr(agent.personality, t, rng.random())
        for need in agent.needs.needs.values():
            need.level = rng.random()
        with quiet():
            choice = brain.choose(agent, perceptions, lambda a: sim._agent_updater._can_run(agent, a))
        sampled.add(choice.action_type.value)
    assert sampled <= produced, sampled - produced  # it only picks what it considers

    updater = sim._agent_updater
    for thirst, hunger, energy, food in [(0.9, 0.1, 80, 0), (0.1, 0.9, 80, 0), (0.1, 0.9, 80, 5),
                                         (0.1, 0.1, 5, 0), (0.1, 0.1, 80, 0)]:
        agent.needs.needs[NeedType.THIRST].level = thirst
        agent.needs.needs[NeedType.HUNGER].level = hunger
        agent.energy = energy
        agent.inventory.items = {"food": food} if food else {}
        override = updater._survival_override(agent)
        if override is not None:
            produced.add(override.action_type.value)
    return produced


# ---------------------------------------------------------------------------
# (c) The LLM brain's menu and parser
# ---------------------------------------------------------------------------

def llm_menu_and_parser():
    """Return (menu_names, parse) where parse(name) -> ActionType value or None."""
    sim, roles = make_world(use_llm=True)
    agent = roles["actor"]
    perceptions = sim._perception_builder.build_perceptions(agent, sim.world.get_state())
    brain = sim.llm_brain
    if brain is None:
        return set(), (lambda name: None)
    agent.last_perception = perceptions
    with quiet():
        prompt = brain._build_thinking_prompt(agent, perceptions, "decide_action")
    # A name counts as on the menu only if the prompt the model sees contains it
    # as a whole word
    from agents.agent import ActionType
    menu = {a.value for a in ActionType
            if re.search(rf"(?<![a-z_]){re.escape(a.value)}(?![a-z_])", prompt)}

    def parse(name: str):
        with quiet():
            action = agent._parse_action_from_llm(f"ACTION: {name}\nREASON: it fits my plans", perceptions)
        return action.action_type.value if action is not None else None
    return menu, parse


# ---------------------------------------------------------------------------
# The map
# ---------------------------------------------------------------------------

def reachability_rows():
    engine_simulation, agent_module = _imports()
    fallbacks = engine_simulation.UNHANDLED_ACTION_FALLBACKS
    sim, _ = make_world()
    registry = sim._handler_registry

    brain_canonical = {canonical(n) for n in rule_brain_actions()}
    menu, parse = llm_menu_and_parser()

    succeeds = {}
    rows = []
    for action_type in agent_module.ActionType:
        name = action_type.value
        if name in INTERNAL_ACTIONS:
            continue
        direct = registry.get_handler(action_type) is not None
        target = name if direct else fallbacks.get(name)
        a_ok = direct or (target is not None and registry.get_handler(agent_module.ActionType(target)) is not None)
        b_ok = canonical(name) in brain_canonical
        parsed = parse(name)
        c_ok = name in menu and parsed is not None and canonical(parsed) == canonical(name)
        if target not in succeeds and a_ok:
            succeeds[target] = try_to_succeed(target)
        d_ok, d_why = succeeds.get(target, (False, "no handler"))
        notes = []
        if not a_ok:
            notes.append("no handler or fallback")
        if not c_ok:
            notes.append("not on LLM menu" if name not in menu else f"LLM answer parses as {parsed!r}")
        if not d_ok:
            notes.append(f"never succeeds ({d_why})")
        rows.append({"action": name, "runs": target or "-", "a": a_ok, "b": b_ok, "c": c_ok, "d": d_ok,
                     "note": "; ".join(notes)})
    return rows


def format_table(rows, only_failures=True):
    mark = lambda ok: "ok" if ok else "NO"
    shown = [r for r in rows if not (r["a"] and r["b"] and r["c"] and r["d"])] if only_failures else rows
    lines = [f"{'action':<22} {'runs':<18} a   b   c   d   note"]
    for r in shown:
        lines.append(f"{r['action']:<22} {r['runs']:<18} {mark(r['a']):<3} {mark(r['b']):<3} "
                     f"{mark(r['c']):<3} {mark(r['d']):<3} {r['note']}")
    total = len(rows)
    lines.append("")
    lines.append(f"{total} actions checked ({len(INTERNAL_ACTIONS)} internal skipped): "
                 f"handled {sum(r['a'] for r in rows)}, rule brain {sum(r['b'] for r in rows)}, "
                 f"LLM menu {sum(r['c'] for r in rows)}, can succeed {sum(r['d'] for r in rows)}, "
                 f"all four {sum(r['a'] and r['b'] and r['c'] and r['d'] for r in rows)}")
    return "\n".join(lines)


def test_every_action_is_reachable():
    rows = reachability_rows()
    failures = [r for r in rows if not (r["a"] and r["b"] and r["c"] and r["d"])]
    print("\n" + format_table(rows))
    assert not failures, f"{len(failures)} actions are not fully reachable (table above)"


if __name__ == "__main__":
    print(format_table(reachability_rows(), only_failures="--all" not in sys.argv))
