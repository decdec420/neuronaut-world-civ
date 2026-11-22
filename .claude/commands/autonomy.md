---
description: Build Neuronaut World out for full agent autonomy. Open every capability, give agents real minds, let life continue, and record what they create
argument-hint: "[optional: phase number to start from, e.g. '4']"
---

# Goal

Neuronaut World exists to answer one question: **what do agents create when
they're fully in charge?** The world supplies capabilities; the agents decide.
Today most capabilities exist in code but can't be chosen, so the answer is
meaningless. Your job is to make every capability *reachable*, give the agents
real minds and a continuing life, and make what they create *visible*,
**without scripting any outcome.**

Start phase: $ARGUMENTS (default: phase 0). Read CLAUDE.md first, especially
"Design philosophy: the agents are in charge"; it overrides anything here.

# Rules for the whole job

- **Never script outcomes.** No rule exists to make a feature happen ("agents
  with high X found a religion", "after day 3 form a government", forced
  marriages or jobs). Agents choose from their own state: needs, personality,
  memories, relationships, perceptions. Use weights and sampling, not if-then.
- **Prove capabilities in tests, not in the sim.** A test may directly invoke
  "agent A founds a religion" to prove the path works end-to-end. The sim never
  forces it. Zero religions in a run is a valid result if founding one was possible.
- **Remove blockers, don't add pushes.** If something can't happen because the
  world makes it impossible (no money supply, an unreachable action, a missing
  target), fix the world, not the agent's motivation.
- **Measure everything.** Baseline first; after every step, run
  `python3 scripts/sim_check.py --verbose` and compare. One commit per step,
  with before/after numbers in the message. Don't change balance numbers
  without showing their effect.
- **Keep agents sandboxed.** In-sim agents get no real network, filesystem,
  shell or credentials. The only outside call allowed is the LLM provider
  used by the decision brain itself.
- **Don't break survival.** `sim_check.py` must stay PASS after every phase.
  If a phase breaks it and two attempts don't fix it, revert that step, note
  why in the PR, and move on.
- No "COMPLETE"/"100%" status docs. Work on branch `autonomy/<phase-topic>`
  (or one branch `autonomy/full-build` with a commit per step). Push and open a
  PR when done; never push to `main`.

# Phase 0: Baseline and emergence metrics

1. Run `scripts/sim_check.py --verbose` and `--llm`; save the output.
2. Extend `sim_check.py` to also report, per seed: governments, laws, religions,
   followers, rituals, innovations/discoveries, couples, births, deaths by
   cause, total money in circulation, successful trades, and **distinct action
   types actually chosen**. Report them only; emergence counts must not affect PASS/FAIL.
3. Add `--long` (e.g. 6000 ticks, 1 seed) and print average tick time at the
   start vs the end, to spot slowdowns.

# Phase 1: Reachability map (the test that keeps this honest)

1. Write `tests/test_reachability.py`. For every `ActionType`, determine:
   (a) has a handler or fallback, (b) the rule-based brain can ever produce it,
   (c) it's on the LLM brain's menu, (d) its handler can succeed in at least one
   reasonable world state (build that state in the test and execute it).
2. Keep a small, documented allowlist for actions that are deliberately
   internal (e.g. `idle`). Everything else must pass (a)–(d). The test should
   print a table of failures. It will fail now; that's the to-do list for
   phases 2–4.

# Phase 2: The AI brain gets the full menu

1. Generate the LLM's action menu from the same registry the engine uses
   (ActionType + handlers + fallbacks), so it can never drift again. Group by
   category (survival, building, crafting, social, romance and family, economy,
   politics, religion, knowledge and invention, culture, conflict), with a few
   words per action. Keep the prompt compact; group or abbreviate rather than drop.
2. Make the output format strict (exact action name + optional target agent,
   position or parameters) and make parsing robust. Log and count parse
   failures; fall back to the rule-based brain on failure.
3. Give the brain what it needs to choose: its needs, inventory, money,
   relationships and nearby agents (by name), local buildings, current laws and
   governments, known religions, recent memories and reflections, current goal.
4. Unit-test prompt building and parsing with a fake LLM client (no network).

# Phase 3: The rule-based brain considers everything

1. Replace hand-picked option lists with utility over **all** reachable
   actions: each action scores from the agent's needs, personality traits,
   memories and relationships, then sample (softmax with a temperature) rather
   than always taking the max. Rare actions should be rare, not impossible.
2. Keep `_survival_override` exactly as the first gate.
3. Verify with phase-0 metrics: distinct action types chosen should rise a lot
   while survival stays PASS.

# Phase 4: Open the locked doors (see AUDIT.md)

Fix the world so these are possible. Don't make them likely.

- **Governance:** `vote` needs a real target (open election or proposed law);
  forming a government, proposing laws and enforcing them must work end-to-end.
- **Religion:** `pray`/`worship`/`perform_ritual` reachable; founding a religion
  is something an agent can choose, followers can join or leave.
- **Invention:** successful experiments and discoveries call
  `InnovationManager` (`agent_discovers`, `record_experiment`,
  `agent_invents_building`) so inventions are recorded and spread.
- **Economy:** allow barter (goods for goods) when the buyer has no money, and
  make minting reachable (unlock metal/iron ore, AUDIT #11). Fix trade results
  that put text under `reason` instead of `message` (AUDIT #6).
- **Learning:** wire up the dead action-outcome learning (AUDIT #8) so agents'
  future choices are shaped by what worked for them.
- **Disease:** fix the inverted random disease selection (AUDIT #9).
- Re-run `tests/test_reachability.py`; it should now pass.

# Phase 5: Life continues

1. **Relationships to partnership:** courtship and partnership require both
   agents' consent (each decides on its own turn). Partners can separate.
2. **Children:** partners may choose to have a child. A new agent inherits a
   blend of both parents' personalities plus variation, starts as a child (with
   needs cared for by parents/others; limited actions), grows up, then acts
   fully. Name generation must avoid duplicates.
3. **Aging and natural death:** life stages and old age, so generations turn over.
4. Add a configurable population cap (default ~60) for performance only,
   documented as a technical limit, not a design rule.
5. Phase-0 metrics: couples, births and deaths by cause over a `--long` run.

# Phase 6: Real minds (Ollama)

1. Support a local Ollama model via `.env` (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`).
   Default to a small instruct model that runs on an Intel Mac; document RAM needs.
2. Per-tick time budget: run agents' LLM calls concurrently with a timeout;
   agents whose call times out use the rule-based brain that tick. Optionally
   let each agent think every N ticks and follow its plan in between.
3. Memory, reflection and planning in the Smallville style: a memory stream
   scored by recency/importance/relevance, periodic reflections, and day
   plans, all bounded in size.
4. Add `scripts/llm_smoke.py`: runs ~50 ticks against the configured model and
   reports calls, average latency, parse-failure rate, distinct actions chosen
   and a few sample decisions with the agent's stated reasoning. If no model is
   reachable in your environment, test with the fake client, then write exact
   steps in the PR for running it on Tommy's Intel MacBook.

# Phase 7: It runs for a long time

1. Save/load round-trip test: save mid-run, load, continue, and check state
   matches (agents, relationships, buildings, governments, religions, money).
2. `--long` run: no exceptions, and tick time and memory don't grow without
   bound. Cap memory streams, event logs and history lists.

# Phase 8: See what they created

1. **Chronicle:** record "firsts" and milestones as they happen (first home,
   first couple, first birth, first government and its founder, first law,
   first religion and its prophet, first invention, first trade, first war,
   first death of old age), plus notable reflections or speeches from LLM
   agents. Expose `GET /chronicle` and show it as a dashboard panel/tab.
2. Dashboard panels for governments, laws, religions, families (simple family
   tree), economy (money, trades), and inventions. Use `$safe` / `setTextSafe`.
3. Start the server, load `/app`, and confirm no console errors and that the
   new panels update live.

# Finish

Run `sim_check.py` (default, `--llm`, `--long`), `tests/test_reachability.py`
and the server/viewer check. Open a PR whose description has:
- a baseline vs final table: survival numbers, distinct actions chosen, and
  every emergence metric
- per phase: what was locked or broken (file:line), what you changed, and how
  you verified it
- anything skipped or reverted, and why
- exact steps for Tommy to run it with Ollama on his Mac and watch `/app`
- what you'd do next, ranked
