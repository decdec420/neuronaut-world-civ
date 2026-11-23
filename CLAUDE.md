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
  `agent.location` directly.
- **Requests that change the world** need the `X-Neuronaut-Control: 1` header
  (and the admin token if `NEURONAUT_ADMIN_TOKEN` is set). In the dashboard use
  `controlFetch()`.

## Known open issues (good places to start)

Measured on 8 seeds after the open-issues round (see PR #4, "Round 5"). Fixed
in that round: tell_story dominance (the rule brain's need table credited needs
actions never meet; it is now measured, `scripts/need_effects.py`), faiths
lapsing, gathering hosts all picking 18:00, ids not coming from the seed,
disasters firing at ~27x their written rate, the unused swarm and
semantic-memory modules (removed), and the stale status docs (now in
`docs/archive/`). Top failures are research that finds nothing, territory
already claimed and failed hunts: legitimate outcomes.

1. **The rule brain doesn't stick with a plan.** It chooses afresh every tick,
   so a long walk (to a gathering 50 tiles away, to a far shelter) is usually
   given up halfway. Guests more than ~20 tiles from a gathering can't arrive:
   they may set off only two hours early. Letting them set off earlier made
   fewer people come (measured), because they abandoned the walk. A
   commitment term (keep doing what you set out to do, weighted by
   conscientiousness) is the thing to try; it touches every choice, so compare
   8-seed medians.
2. Most faiths have only their founder. Joining needs `worship` by someone who
   likes a follower; nobody preaches. Followers now practise and keep their
   faith.
3. `rest` is ~37% of rule-brain actions. Most of it is sleep at night
   (NIGHT_REST_PULL); worth checking how much is daytime idling.
4. Building fell when the need table was corrected (8-seed median 20 -> 16.5,
   glass made 7 -> 1): it had been pulled by needs it doesn't meet. Whether
   agents build enough is now an honest question about what building gives them.
5. Disasters now come at their written rates (one every ~2-5 weeks, more in
   rain and spring), but each is large: radius 40-60 tiles on a 100x100 map
   for major ones, death chances up to 0.9. Over 6000 ticks (42 days) x 2
   seeds the fix took disasters 29/29 -> 3/7, disaster deaths 3/6 -> 0/0 and
   alive at the end 8/18 -> 16/21; a single major one can still kill several.
   A balance call; measure on long runs (`--long`) before changing it.
6. The design PDFs in `docs/references/` and `.github/copilot-instructions.md`
   predate most of this; the latter links files that no longer exist.

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
