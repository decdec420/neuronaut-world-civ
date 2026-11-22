# Neuronaut World audit

Scope: the whole sim. Read-only review at commit `74fab84` (2026-11-22). No code changed.

## How this was measured

| Step | Command / method |
|---|---|
| Health check | `python3 scripts/sim_check.py --verbose` and `--verbose --llm` (1200 ticks x 3 seeds, 12 agents) |
| Live server | `USE_LLM_DECISIONS=false python3 main.py`, then `curl` on every GET route in `api/server.py` |
| Dashboard | headless Chromium on `/app` for 20 s, then clicked all 15 tabs; console errors, websocket frames and header values recorded |
| Instrumented runs | one-off scripts outside the repo that wrap `start_construction`, `agent_designs_building`, `harvest_from_pool`, `harvest_resource` and `execute_action` and count what happens (seed 1 unless noted) |

The rule-based path is deterministic per seed: an instrumented seed-1 run reproduced the
baseline's seed-1 action counts exactly (`gather_materials` 8426). The `--llm` path is not:
two runs of the same seeds gave different deaths (see finding 7).

### Baseline numbers

Rule-based (`sim_check.py --verbose`): **OVERALL: PASS**

| Seed | Alive | Health | Buildings | Top failure | Share of all agent-ticks |
|---|---|---|---|---|---|
| 1 | 12/12 | 80 | 32 | `gather_materials` "No materials available to gather" x7979 | 55% |
| 2 | 12/12 | 88 | 11 | `build_house` "Construction failed to start" x7633 | 53% |
| 3 | 10/12 | 95 | 11 | `build_house` "Construction failed to start" x7408 | 51% |

Other failures: `gather_food` "Failed to gather food" x1403 / x1078 / x559.
There were no exceptions from `tick()`.

LLM path, no model available, so it falls back (`sim_check.py --verbose --llm`): **OVERALL: FAIL**

| Seed | Alive | Health | Buildings | Top failure |
|---|---|---|---|---|
| 1 | 11/12 | 75 | 29 | `gather_materials` "No materials available to gather" x6305 |
| 2 | 8/12 | 100 | 10 | same x5603, `build` "Construction failed to start" x1120 |
| 3 | 9/12 | 99 | 12 | same x5736, `build` "Construction failed to start" x1328 |

`sim_check` printed every death cause as `None` (finding 12). With the field name corrected, all
LLM-path FAIL deaths were **earthquakes** (finding 7).

### Server and dashboard

- All 38 GET routes return 200. `/materials/{category}` returns 404 only for an unknown category, which is expected.
- No ERROR lines or tracebacks in the server log. The log runs at DEBUG for `agents.agent` (`main.py:29`): 2,650 lines in about 2 minutes.
- `/app` showed 0 console errors and 0 failed requests across all 15 tabs. It received 18 websocket frames in 20 s; the header buildings count rose 6 → 14 and the activity feed rose 1 → 25 items.
- `/app` bug: the live activity counters stay at 0 while agents work (finding 10).

---

## Findings, ranked by impact

Findings 1–3 compound into one loop. After its first few buildings an agent spends most of its
remaining ticks on a build or gather action that can never succeed. They are listed separately
because each has its own root cause and fix.

### 1. The `defense` building can never be built, and the up-front check that should catch it is silently disabled

**What's wrong.**
- `ConstructionHandler._determine_building_purpose` returns `'defense'` once SECURITY > 0.7 (`engine/handlers/construction.py:571-572`).
- `DynamicBuildingSystem._estimate_materials` has no `'defense'` recipe. Its table uses `'protection'` (`world/dynamic_buildings.py:385-397`). The total is therefore 0, below the minimum, so it returns `None` (`world/dynamic_buildings.py:469-472`).
- `agent_designs_building` doesn't check for `None`. It stores a `BuildingDesign` with `materials_needed=None` (`world/dynamic_buildings.py:262-289`).
- `start_construction` then rejects that design (`:541-543`), and the handler reports "Construction failed to start" (`construction.py:361-367`).
- The up-front material check in `validate()` calls `needed.items()` on that `None`. The resulting `AttributeError` is swallowed by `except Exception: pass` (`construction.py:146-155`), so validation passes and the agent retries every tick.
- The goal path keeps it going. A `find_shelter` goal's `build_shelter` step maps to `build_house` (`agents/strategy.py:429`). That step is validated with the same broken check (`engine/agent_updates/agent_updater.py:397-400`), and goals are never abandoned (finding 3).

**Evidence.**
- Seed 2, 600 instrumented ticks: 693 failed construction starts. 684 had purpose `defense` and 9 had `shelter`. All 693 had `materials_needed is None`.
- Baseline seeds 2 and 3: `build_house` failed 7633 of 7651 and 7408 of 7420 times.
- Seed 1 ended with 834 stored designs for 32 completed buildings. Each failed attempt leaves a junk design behind, which also skews `get_statistics()["success_rate"]`.

**Why it matters.** In 2 of 3 seeds, half of all agent-ticks for the whole run produce nothing.
Agents never build defenses, so SECURITY is never satisfied (finding 3). This is CLAUDE.md
known issue #1: the handler's purposes and the design system's recipes don't agree.

**Fix (S).**
- Give every purpose `_determine_building_purpose` can return a recipe, e.g. map `defense` to the `protection` recipe.
- Have `agent_designs_building` return `None` when the estimate is `None`, and don't store the design.
- In `validate()`, treat a `None` estimate as "can't build this yet" instead of swallowing the exception.
- Pass the current era to the validate-time estimate. Today it uses the default `"Stone Age"` (`construction.py:147`), while execute uses `civilization.current_era` (`:331`).

### 2. Inventories fill with stone, after which `gather_materials` fails every tick with a misleading message

**What's wrong.**
- `handle_gather_materials` always takes the first material in a fixed priority list, stone first (`engine/agent_updates/action_handlers.py:483`). It does this whatever the agent's next building needs, as long as the pool holds more than 10.
- Agents therefore fill the 150-slot inventory with stone.
- Once the inventory is full, the loop `break`s at `space <= 0` (`:514-516`) and returns "No materials available to gather" (`:573-578`).
- `ResourceGatheringHandler.validate` only checks alive and energy (`engine/handlers/resource_gathering.py`, `validate`), so the action is never rejected.
- Several paths keep choosing it:
  - `agent.decide` adds it whenever `len(self.inventory.items) < 15`. That counts distinct item types, not quantity, so a full inventory still qualifies (`agents/agent.py:948`).
  - The goal path converts a rejected build into `GATHER_MATERIALS` (`agent_updater.py:401-403`).
  - `find_shelter`'s first step is `gather_materials`.
- A stone-only inventory also can't produce a viable design. Shelter needs wood, fiber and clay, so this feeds finding 1.

**Evidence.**
- Seed 1 at tick 400: every inspected agent held 149–150 items, 111–145 of them stone, with 1–3 wood.
- Seed 1 world pools at tick 1200: wood 3000 (full), plant_fiber 2000 (full), clay 1560, stone 1161.
- Baseline seed 1: 7979 of 8426 `gather_materials` attempts failed.
- **CLAUDE.md known issue #2 has the cause wrong.** The pools are not drained. The agents' inventories are full.

**Why it matters.** This wastes 55% of agent-ticks in seed 1 and 40–48% on the LLM path. It
also starves construction of wood, fiber and clay, and freezes material diversity, so
experimentation keeps reusing stone.

**Fix (S–M).**
- Gather what the agent lacks for its next building: the shortfall from finding 1's estimate, or else the material it holds least of.
- Reject `gather_materials` in `validate()` when the inventory is full, with an honest reason, so the agent picks something else.
- Make the `agent.decide` capacity check use total quantity.

### 3. SHELTER and SECURITY needs are never satisfied by existing buildings, and goals are never abandoned

**What's wrong.**
- SHELTER rises 0.002/tick and SECURITY 0.001/tick (`engine/psychology.py:105,107`).
- The only code that ever lowers them is completing a shelter or defense (`construction.py:464-479`). Standing in or near your own home does nothing. `DynamicBuildingSystem.use_building` exists but has no callers.
- Each agent may build one of each purpose (`construction.py:316-320`). Once its shelter is built, SHELTER climbs back to 1.0 and stays there.
- `_determine_building_purpose` keeps returning `'shelter'`, which is then nulled as already built, giving "No building need". Or it returns `'defense'` (finding 1).
- `StrategicPlanner.choose_goal` keeps creating `find_shelter` goals because SHELTER urgency is above 0.7 (`agents/strategy.py:129-130`).
- `StrategyManager.update_goal_progress` records obstacles but never abandons a goal (`agents/strategy.py:339-363`). `abandon_goal` has no callers.
- Goal progress also advances on the success of *any* action that tick, including survival overrides (`agent_updater.py:583-588`), not just the goal's own step.

**Evidence.**
- Seed 1 at tick 1200: 26 of 30 active goals were `find_shelter`, and 415 obstacle strings had accumulated on live goals. That list grows without bound.
- Every agent's `built_purposes` held `shelter` within the first 400 ticks.

**Why it matters.** This is what feeds the loops in findings 1 and 2. Homes don't function as
homes, and the agents' strongest long-term drive points at something they can never do again.

**Fix (M).**
- Satisfy SHELTER (and some SECURITY) while an agent rests at or near a completed building it built or occupies. Wire up `use_building`.
- Abandon a goal after N consecutive failures of its current step.
- Only credit goal progress when the executed action came from the goal.

### 4. The food pool is empty from tick ~200 on: a third of it leaks, and half of gathering is stockpiling

**What's wrong.**
- `WorldSimulation.harvest_resource` debits the *requested* amount (12) from the global pool (`world/simulation.py:423`). It then takes what the tile actually has (`:426`), which is often less.
- Only the tile is refunded when the two disagree (`:429-431`), never the pool.
- Gathering is also driven by goals when agents aren't hungry: `secure_food` maps `find_food_source` to `forage` and then to `gather_food`, and `stockpile_food` maps to `gather_food`.
- On top of that, each harvest both stores the food *and* satisfies hunger immediately (`engine/agent_updates/action_handlers.py:427-436`).

**Evidence (seed 1, 1200 ticks).**
- The pool was debited 10,201 food, but agents received 6,705. 34% leaked.
- 1,367 of 2,827 `gather_food`/`forage` attempts (48%) came from agents with hunger < 0.3.
- Food pool by tick: 2000 at t0, 1124 at t100, 0 at t200, and between 0 and 58 from then to t1200.
- Baseline: "Failed to gather food" x1403 / x1078 / x559. This is CLAUDE.md known issue #3: the pool is empty, and regen of 6/tick is split among competing gatherers.
- On the LLM path, which ignores goals, the pool stayed near 2000 all run.

**Why it matters.** Hunger averages 0.38–0.48 in the rule-based runs. It's survivable, but
it's the main reason food actions fail, and it would kill a larger population.

**Fix (S).**
- Debit the pool by what the tile actually yields, or refund the pool.
- Skip stockpiling steps when hunger is low and the agent holds food.
- Have `validate()` reject `gather_food` when the global pool is empty.

### 5. Governance and religion can't emerge on the rule-based path, and innovations are never recorded

**What's wrong.**
- No rule-based option ever produces `govern`, `make_law`, `pray`, `worship` or `perform_ritual`.
  - `agent.decide` / `_generate_possible_actions` never generates them (`agents/agent.py:780-1155`).
  - Every goal plan was resolved to its executed action (table generated from `StrategicPlanner._generate_plan` + `evaluate_goal_action` + `UNHANDLED_ACTION_FALLBACKS`). None reach them.
- `become_leader` maps to `campaign` and then `vote` (`agents/strategy.py:445,447`; `engine/simulation.py:127`). `vote` is built with no `vote_target`, so it always returns "No vote target specified" (`engine/handlers/governance.py:139-140`). `validate()` doesn't reject it first.
- Religions are only founded inside `PRAY`, at 10% per prayer (`engine/handlers/religion.py:47-52`). `PRAY` is only reachable through the LLM keyword parser or the `meditate`/`contemplate` aliases, which nothing in the rule path emits.
- `InnovationManager.agent_discovers`, `record_experiment` and `agent_invents_building` have no callers anywhere outside `world/innovations.py`. `/innovations` is therefore always empty.

**Evidence.**
- 1200 ticks, rule seed 1 and LLM-fallback seed 2: 0 governments, 0 laws, 0 religions, 0 rituals, 0 innovations.
- `docs/refactoring/PHASE_1.2_GOVERNANCE_COMPLETE.md` claims "✅ Forms government via `governance_manager.agent_forms_government()`".
- `engine/simulation.py:347` prints "✅ 100% ACTION COVERAGE ACHIEVED!". Coverage means a handler is registered, not that the action can be chosen.

**Why it matters.** Three headline society features (politics, religion, invention) are
dead code without a working LLM. This is CLAUDE.md known issue #4.

**Fix (M).**
- Add need-driven options in `_generate_possible_actions`: MEANING leads to `pray`; STATUS plus charisma or ambition leads to `govern`.
- Give `vote` a target (the open election or law), or validate it away.
- Call `innovation_manager.record_experiment` / `agent_discovers` from the experiment handler when a discovery succeeds.

### 6. There is no money supply, so currency trade can't happen

**What's wrong.**
- Every agent starts with `wealth = 0.0` (`engine/world_initializer.py:82`, `agents/agent.py:459`).
- Money only enters through `mint_coins`, which needs metal ore (finding 11), loans, gambling pots or knowledge sales. The rule-based brain never chooses `mint_coins`.
- `handle_trade` is money-only (`economy/market.py:357` returns "Insufficient funds").
- Several trade failures put their text under `'reason'` instead of `'message'` (`engine/agent_updates/action_handlers.py:65,72,80,106`), so they log as an empty string.

**Evidence.**
- All 12 agents had wealth 0.0 at tick 1200 (rule seed 1 and LLM seed 2). `/economy` reports `total_wealth: 0.0`.
- LLM baseline seed 2: `trade` failed with "Insufficient funds" x157 and `''` x255.

**Why it matters.** "Economy emerges from trade" (README) can't happen. Trade attempts are
wasted ticks.

**Fix (M).**
- Allow barter (goods for goods) when the buyer has no money, or seed a small starting purse.
- Rename the result key to `message`.

### 7. Catastrophic earthquakes kill about 40% of the town with no protection, which makes `--llm` FAIL at random

**What's wrong.**
- A catastrophic earthquake has `agent_death_chance=0.40` (`world/disasters.py:128`) over a radius of 60 on a 100x100 map (`:439-444`). Agents cluster, so one event covers most of them.
- Shelter gives no protection.
- `SystemCoordinator.apply_disaster_to_world` damages only the legacy `building_manager.buildings` (`engine/system_coordinator.py:65`), never the dynamic buildings agents actually build.
- The LLM path is non-deterministic across runs, so the same seed can PASS or FAIL.

**Evidence.**
- `--llm` run 1: seed 2 lost 4 agents to one earthquake and seed 3 lost 5.
- `--llm` run 2: seed 2 lost no one, and seed 3 lost 3 (all earthquake).
- `sim_check` assumes "earthquakes can legitimately kill one" (`scripts/sim_check.py:12`).

**Why it matters.** A single roll can wipe out a third of a 12-agent society. The health check
fails for reasons unrelated to the change under test. Buildings have no protective value.

**Fix (S–M).**
- Scale `agent_death_chance` down for agents inside or near a completed, non-collapsed dynamic building.
- Apply building damage and collapse to `dynamic_building_system.buildings`.
- Optionally cap casualties per event.
- These are balance changes, so they need before/after numbers.

### 8. Action-outcome learning is dead code

**What's wrong.**
- `agent_updater.py:552` calls `self.sim._calculate_success_score`, which doesn't exist on `SimulationEngine`. The `AttributeError` is swallowed by `except Exception: pass` (`:570-572`).
- `needs_before = agent.needs` (`:483`) is the same object as `needs_after` (`:524`), so measured need changes are always 0 anyway.
- `outcome.get('reason')` (`:537`) reads a key that results don't set. They use `message`.

**Evidence.** After 1200 ticks, `len(agent.recent_action_outcomes)` was 0 for all 12 agents.
`life_satisfaction_history` and `decision_quality_scores` are never written either. The profile's
`decision_quality` is always the default 50.0 (`agents/agent.py:1339`).

**Why it matters.** The "learns from outcomes" loop and the UI fields built on it show nothing.

**Fix (S).** Implement the score from `action_outcome`, snapshot need levels before acting, and
read `message`.

### 9. Random disease selection is inverted

**What's wrong.** `_check_random_disease_infection` gives MALNUTRITION when `HUNGER.level < 0.3`
and DEHYDRATION when `THIRST.level < 0.3` (`engine/agent_updates/agent_updater.py:217,220`).
Need levels run 0 = satisfied, so well-fed agents get malnutrition and starving agents get the
generic flu.

**Why it matters.** Small: about 7 infections per run. But it's the exact inversion CLAUDE.md
warns about, and it puts MODERATE illness on healthy agents.

**Fix (S).** Use `> 0.7`.

### 10. Dashboard activity counters and map colours undercount

**What's wrong.**
- `/app` counts `agent.current_action === 'build'`, `'explore'`, and so on (`web/enhanced.html:7036-7044`, colours at `:6911-6935`).
- The API reports the agent's chosen alias instead, e.g. `build_house`, `forage`, `survey_land` or `learn_skill`. `agent.current_action` is the pre-fallback action, set at `agent_updater.py:414`.

**Evidence.** The live page showed "0 BUILDING" and "0 EXPLORING" while `/agents` listed `build_house`, and the header building count was rising.

**Fix (S).** Either report the resolved action, using `UNHANDLED_ACTION_FALLBACKS`, alongside the
chosen one in the snapshot, or normalise in the viewer.

### 11. Metal and iron ore pools are never unlocked

**What's wrong.** `metal_ore` and `iron_ore` pools start at 0 (`world/simulation.py:262-263`).
`WorldSimulation.unlock_resource` (`:342`) has no callers. The era still advances to Iron Age
through discoveries.

**Evidence.** Seed 1 ended in the "Iron Age" with both ore pools at 0.

**Why it matters.** `gather_materials` and `mine` can never gather ore. Metal-requiring
buildings and `mint_coins` are only reachable through stray inventory.

**Fix (S).** Call `unlock_resource` from the era/milestone advance (`world/civilization_progression.py:_advance_to_era`).

### 12. `sim_check` hides death causes

**What's wrong.** `scripts/sim_check.py:90` reads `cause_of_death`, but agents write `death_cause`
(`agents/agent.py:500,735`; `engine/system_coordinator.py:91`).

**Evidence.** Every death printed `None`. With the field fixed, the causes were "earthquake"
and "unknown causes".

**Fix (S).** One-word change.

### 13. Smaller problems

- `validate_agent_inventory` reads `agent.inventory.resources`, which doesn't exist; the field is `items` (`engine/action_handlers.py:468`). It's currently unused.
- `/app` hard-codes `ws://localhost:8000/ws` (`web/enhanced.html:2766`), so the viewer breaks on any other host or port.
- `agents.agent` logs at DEBUG under `main.py` (`main.py:29`), which is noisy.
- "unknown causes" deaths (LLM seed 1, both runs) aren't attributed. Weather damage, disease damage (`agent_updater.py:166-170`) and the random 5–20 hit in `Agent.update` all lower health without setting a cause.
- No births were observed in any 1200-tick run. I didn't trace the reproduction path, so this may simply be too few ticks.

---

## Top 3 to fix first

1. **Finding 1: the `defense` recipe mismatch and the silently disabled build validation.** Size S. It accounts for about 51–53% of all agent-ticks in two of three seeds, and it is known issue #1.
2. **Finding 2: stone hoarding into a full inventory, with gathering that ignores what's needed.** Size S–M. It accounts for 55% of agent-ticks in seed 1 and about 45% on the LLM path. It also starves construction of the materials it needs, and corrects the diagnosis in known issue #2.
3. **Finding 3: SHELTER and SECURITY are never satisfied by existing buildings, and goals are never abandoned.** Size M. This drives agents back into loops 1 and 2. Without it, fixing 1 and 2 still leaves agents re-planning shelters they can't build.

Next after these: finding 4 (the food leak, S) and finding 7 (earthquake lethality, which makes the `--llm` check flaky).
