# Neuronaut World — instructions for Claude Code

An autonomous AI civilization sim: ~12 agents with needs, memory, personalities,
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
pip3 install -r requirements-minimal.txt
USE_LLM_DECISIONS=false python3 main.py      # then open http://localhost:8000/app
```

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
- **Requests that change the world** need the `X-Neuronaut-Control: 1` header
  (and the admin token if `NEURONAUT_ADMIN_TOKEN` is set). In the dashboard use
  `controlFetch()`.

## Known open issues (good places to start)

Measured on 8 seeds after the "make the sim work right" round (PR #4, Round 6).
Fixed in that round: agents now carry on with what they set out to do
(`agents/commitment.py`: 84-95% of commitments end with the agent arriving),
believers can tell others about their faith (`convert`), the dashboard serves
only `/app` (fake and stale pages removed) and shows names, not ids. Checked and
fine: `rest` is ~36% of actions, but 92% of it is sleep at night. Earlier rounds
fixed tell_story dominance, lapsing faiths, clashing gatherings, ids from the
seed, the disaster rate, unused modules and stale docs.

1. **Far guests can't reach a gathering.** One may set off only two hours
   early (LEAD_TICKS), and walking is a tile a tick, so anyone more than ~20
   tiles away arrives after the end. Letting them set off in time (walk time
   on top) lowered attendance in every test, with commitments too (seeds 1
   and 4, per person per day: 64%/58% without it, 60%/46% with it). Why is
   not known; long walks get set aside for water, food and sleep, and the
   pull of a far gathering may draw people from a near one. Measure before
   trying again.
2. Commitments cost some other things (8-seed medians): innovations 41.5 ->
   36, road tiles 55 -> 31.5, conversations 2192 -> 1828. Likely time spent
   finishing walks; not measured. COMMIT_PULL (0.8) is the knob.
3. Faiths stay small: followers at the end, median 2 per world. `convert` is
   rare; the listener's chance (LISTEN_* in engine/handlers/religion.py) is
   a sketch of persuasion, not tuned to any target.
4. Building fell when the need table was corrected (8-seed median 20 ->
   16.5-17.5 since, glass made 7 -> 1-2): it had been pulled by needs it
   doesn't meet. Whether agents build enough is an honest question about
   what building gives them.
5. Disasters come at their written rates (one every ~2-5 weeks, more in rain
   and spring), but each is large: radius 40-60 tiles on a 100x100 map for
   major ones, death chances up to 0.9. A balance call; measure on long runs
   (`--long`) before changing it.
6. The design PDFs in `docs/references/` predate most of this.

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
