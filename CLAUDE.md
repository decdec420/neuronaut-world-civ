# Neuronaut World — instructions for Claude Code

An autonomous AI civilization sim: ~12 agents with needs, memory, personalities,
an economy, buildings, culture and (optionally) LLM-driven decisions, shown live
in a browser dashboard. The goal is a society you can sit back and watch grow.

## Run it

```bash
pip3 install -r requirements-minimal.txt
USE_LLM_DECISIONS=false python3 main.py      # then open http://localhost:8000/app
```

`USE_LLM_DECISIONS=true` needs Ollama running locally or an API key in `.env`
(see `.env.example`). Without a model, the LLM path falls back to the rule-based brain.

## Verify every change (non-negotiable)

```bash
python3 scripts/sim_check.py                  # 1200 ticks x 3 seeds, must print OVERALL: PASS
python3 scripts/sim_check.py --verbose        # also shows top actions and top failures
python3 scripts/sim_check.py --llm            # LLM decision path
```

- Run `sim_check.py` before you change anything (baseline) and after every fix.
- A change is done only when it passes AND you've compared the numbers to the
  baseline (alive, health, buildings, top failures). Say what changed.
- If you touch `api/` or `web/`, also start the server and load `/app`; check the
  browser console has no errors and the tick counter / activity stream update.
- Never claim something works without running it. Do not write "COMPLETE",
  "A+", "100%" or similar status reports. This repo already has ~100 of them,
  and several described systems that were broken. Report measured results.

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

## Known open issues (good places to start)

1. `build_house` / `build` still fail a lot with "Construction failed to start".
   The up-front material check in `construction.py` doesn't match the design that
   `world/dynamic_buildings.py` actually produces. Make them agree.
2. Stone/clay pools drain with 12 builders → thousands of
   "No materials available to gather". Rebalance or make agents stop trying.
3. `gather_food` "Failed to gather food" ~500 per 600 ticks. Find out why.
4. Governance, religion and inventions haven't been seen to emerge. Trace
   whether their triggers are reachable.
5. LLM path untested against a real model (Ollama). Test and tune prompts.
6. Roughly 100 status `.md` files in the repo root and `docs/` are stale; leave
   them unless asked, and never add more.

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
