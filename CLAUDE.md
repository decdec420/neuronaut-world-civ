# Neuronaut World — instructions for Claude Code

An autonomous AI civilization sim: a band of 25 agents (12 in a settlers'
world) with needs, memory, personalities,
an economy, buildings, culture and (optionally) LLM-driven decisions, shown live
in a browser dashboard. The goal is a society you can sit back and watch grow.

## Design philosophy: the agents are in charge

The point of this sim is to see what agents create when they're fully in
charge. The world provides capabilities; what happens is up to them.

- **Never script outcomes.** No "if X then found a religion", no guaranteed
  governments, no forced jobs or marriages. Don't add rules whose purpose is to
  make a particular feature happen.
- **Every capability must be reachable.** If agents can never choose an action
  (it's missing from the AI brain's menu, or no rule-based option produces it),
  it doesn't count as built. Fixing that is opening a door, not pushing.
- **Make things possible, not inevitable.** Remove artificial blockers (e.g. a
  world with no money supply plus money-only trade) instead of adding pushes.
- **Choices come from the agent's own state:** needs, personality, memories,
  relationships, what it perceives. Use weights, not scripts.
- **The LLM brain is where real autonomy lives.** The rule-based brain is a
  fallback. Prefer changes that give the LLM brain the full menu and better
  information about its world.
- **Measure emergence, don't target it.** `sim_check.py` may count governments,
  religions, inventions, births, etc. Zero is a valid result, as long as
  those things were possible and nobody chose them.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-minimal.txt
USE_LLM_DECISIONS=false python main.py       # then open http://localhost:8000/app
```

Python 3.9 or newer. The requirements pin current versions for 3.10+ and the
last versions that support 3.9 (macOS's own Python) for 3.9; CI tests both.
Don't use syntax newer than 3.9 (`X | Y` in annotations evaluated at run time,
`match`, `zip(strict=)`); CI on 3.9 will fail.

`USE_LLM_DECISIONS=true` needs Ollama running locally or an API key in `.env`
(see `.env.example`). Without a model, the LLM path falls back to the rule-based brain.

## Verify every change (non-negotiable)

```bash
pip3 install -r requirements-dev.txt          # once: pytest + httpx
pytest                                        # the test suite (tests/), must pass
python3 scripts/sim_check.py                  # 1200 ticks x 3 seeds, must print OVERALL: PASS
python3 scripts/sim_check.py --verbose        # also shows top actions and top failures
python3 scripts/sim_check.py --llm            # LLM decision path
python3 scripts/sim_check.py --seeds 8        # for changes to the world itself: 3 seeds is too few
python3 scripts/sim_check.py --start settlers # the other kind of world (default: WORLD_START, dawn)
```

- `sim_check.py` is reproducible: the same code and seed give the same numbers
  (it pins the hash seed and seeds uuid4), so a difference is your change.
  A change to the world's shape or the order choices are made in moves every
  number; compare medians over 8 seeds then, not seed by seed.
- CI (`.github/workflows/ci.yml`) runs pytest, sim_check and a Docker smoke test
  on every push.

- Run `sim_check.py` before you change anything (baseline) and after every fix.
- A change is done only when it passes AND you've compared the numbers to the
  baseline (alive, health, buildings, top failures). Say what changed.
- If you touch `api/` or `web/`, also start the server and load `/app`; check the
  browser console has no errors and the tick counter / activity stream update.
- Never claim something works without running it. Do not write "COMPLETE",
  "A+", "100%" or similar status reports. `docs/archive/` holds ~100 of them,
  and several described systems that were broken. Report measured results,
  and don't add status `.md` files.

## Architecture map

| Area | Where |
|---|---|
| Entry point / server | `main.py`, `api/server.py` (FastAPI, websocket `/ws`) |
| Tick loop | `engine/simulation.py` → `SimulationEngine.tick()` |
| Per-agent update + decisions | `engine/agent_updates/agent_updater.py` (`_survival_override`, `_can_run`) |
| Action handlers (modular) | `engine/handlers/*.py`, registered in `SimulationEngine._register_action_handlers` |
| Legacy action implementations | `engine/agent_updates/action_handlers.py` (reached via `sim.interaction_handler`) |
| Unimplemented actions | `UNHANDLED_ACTION_FALLBACKS` in `engine/simulation.py` routes them to the closest real action |
| Agents, needs, inventory | `agents/agent.py`, `engine/psychology.py` |
| Goals / plans | `agents/strategy.py` (`evaluate_goal_action` maps plan steps to real actions) |
| Commitments (carrying on with a walk) | `agents/commitment.py`, noted in `SimulationEngine.execute_action` |
| Know-how (the beginning of time) | `world/knowhow.py`: what each agent knows how to do, insight, watching, teaching, loss; gated in `execute_action` and `_can_run` |
| Buildings | `engine/handlers/construction.py`, `world/dynamic_buildings.py` |
| World, resources, regrowth | `world/simulation.py` (`resource_pools`, `pool_regeneration`) |
| Dashboard | `web/enhanced.html` (served at `/app`) |

## Gotchas (each one caused real bugs)

- **Need levels run 0 = satisfied → 1 = desperate.** High hunger is bad. Building
  purpose logic once had this inverted.
- **Action energy uses `agent.energy` (0–100).** Deriving it from hunger created
  a starvation death spiral. Food/water gathering must never be energy-blocked.
- **Validate before acting.** If an action can't run (no seeds, no materials, no
  need), reject it in the handler's `validate()` so the agent picks something
  else, rather than failing in `execute()` every tick.
- **Websocket messages**: first message is a bare snapshot, later ones are
  `{type: "simulation_update", data: {...}}`. The viewer must unwrap `data`.
- **The dashboard references elements that may not exist.** Use `$safe(id)` /
  `setTextSafe(id, value)` in `web/enhanced.html`, never a bare `getElementById(...).x`.
- **Survival before goals.** Urgent needs are handled in `_survival_override`
  for both the rule-based and LLM paths. Keep it that way.
- Default agent inventory capacity is 150; a basic shelter needs ~55 materials.
- **Never let a choice depend on a set's order.** Sets of ids come back from a save
  in a different order, so a loaded world chose differently from the one saved.
  Iterate `sorted(...)` wherever order can change an outcome.
- **Water isn't walkable.** Move agents with `infrastructure.step_toward` (paths)
  or `world.map.walk_line` (straight, stops at the shore), never by setting
  `agent.location` directly. A step toward somewhere also starts the agent's
  commitment (`agent.stepped_toward`); a handler that walks with `walk_line`
  must set it too, and one that waits in place returns `underway: True`.
- **Worlds start at the dawn of time** (`WORLD_START=dawn`, the default): agents
  can't do what they don't know how to (`world/knowhow.py`), so a new action
  that needs know-how goes in a `KnowHow.unlocks`, and one that doesn't is
  innate. `agent.knowhow is None` means "knows everything" (settlers, older
  saves). Tests run as settlers unless they ask for the dawn (`tests/conftest.py`).
- **Relationships grow with time together** (`social/relationships.py`
  BOND_SPACING): repeating an interaction in the same hour adds almost
  nothing. Don't add 0.1 per interaction elsewhere.
- **Requests that change the world** need the `X-Neuronaut-Control: 1` header
  (and the admin token if `NEURONAUT_ADMIN_TOKEN` is set). In the dashboard use
  `controlFetch()`.

## Known open issues (good places to start)

Measured after Round 8 (PR #7): 100-day dawn runs, seeds 1-4. Fixed in that
round: each person has an orientation, roughly as in human populations
(attraction ignored gender, so half of all couples could never have
children); the dawn begins with a band of 25; water comes from its lake or
well, not a global pool sized for 12 (with 40 people it ran dry and people
died beside full lakes); courting someone who hasn't answered is refused;
perception looks only at nearby tiles (a third less CPU per tick); the
Chronicle shows the living by generation. Alive on day 100: 25, 19, 17, 40
(baseline 8, 2, 3, 2), up to 6 generations, every death old age but one
wildfire. Round 7 started worlds at the dawn of time (`world/knowhow.py`).

1. **Births don't quite replace old age.** Seeds 1-3 shrink slowly from day
   40 (100 days: born 36/35/26, died 36/41/34); seed 4 grows (59 born).
   Couples who could have children are 1-7 at a time; about a quarter of
   people don't want children (life profile: agreeableness > 0.4), and
   try_for_child seldom wins against time with a partner (utility_brain:
   FAMILY_WEIGHT x family_priority ~0.5 vs ROMANCE_WEIGHT x liking ~0.8).
   A year of life per sim day leaves a short fertile window. Measure on
   100-day runs before changing any of it.
2. **Couples never separate** (0 in every run) and **liking ignores
   personality** (every bond reaches 1.0 with enough contact). Tried in
   Round 8 and reverted: exchanges that go badly by fit and stress, couples'
   quarrels, bonds that fade without contact: births 37 -> 19 over 8 dawn
   seeds, still no separations (the diff is described in PR #7).
3. **Content agents have little to do:** rest is ~40% of actions (night
   sleep is about 30%); much of the day goes to patrol and gatherings.
4. **Resources have no maximum** (`world/simulation.py` Resource.regenerate):
   food tiles grow +0.5 a tick forever; and since water stopped drawing on
   the global pool, droughts no longer affect water (they only lowered that
   pool's refill). Measure before changing.
5. **Dawn pacing is a first calibration** (`KnowHow.chance`): with 25, most
   worlds have stone tools, fire and shelter in the first 1-2 weeks, farming
   by day 13-53, writing by day 15-64; knowledge is still lost sometimes
   (writing on day 85 in seed 1).
6. **Far guests can't reach a gathering** (LEAD_TICKS): anyone more than
   ~20 tiles away arrives after the end. Letting them set off in time
   lowered attendance in every test. Measure before trying again.
7. A tick costs ~80 ms of CPU with 30-40 people (profile: the rule brain
   weighing ~65 options per agent is the largest part). Faiths stay small;
   disasters are large; the PDFs in `docs/references/` predate most of this.

## How to work

- Small, focused changes; one commit per fix with a message saying what was
  broken and how you know it's fixed.
- Fix root causes, not symptoms. Don't silence errors, widen try/excepts, or
  delete failing features to make the check pass.
- Don't change world-balance numbers (rates, capacities, thresholds) without
  showing before/after `sim_check.py` results.
- Keep the agents sandboxed: no real network access, credentials or shell for
  in-sim agents. Log agent-to-agent messages.
- Work on a branch and open a PR; don't push to `main`.
