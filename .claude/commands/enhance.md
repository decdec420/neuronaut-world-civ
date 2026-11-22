---
description: Find the most valuable improvements to Neuronaut World, implement them, prove they work, and open a PR
argument-hint: "[optional focus, e.g. 'buildings' or 'make religion emerge']"
---

Improve Neuronaut World. Focus: $ARGUMENTS
(If no focus was given, pick the highest-impact problems yourself.)

Follow CLAUDE.md throughout. Work in this order and don't skip steps.

1. **Baseline.** Create a branch `enhance/<short-topic>`. Run
   `python3 scripts/sim_check.py --verbose` and save the output. These are the
   numbers you must beat.

2. **Investigate.** Using the baseline (top failures, deaths, missing buildings)
   plus "Known open issues" in CLAUDE.md and your own reading of the code, list
   candidate problems. For each one, find the root cause in the code; quote the
   file and line. Read the code path end to end. Don't guess from names.

3. **Choose.** Pick the 3 changes with the best value for the risk. Prefer:
   things that are broken > things that are wasteful (failing actions every tick)
   > missing behaviors that are already half-built > new features.
   Write the plan as a short checklist before coding.

4. **Implement one at a time.** For each change:
   - make the smallest change that fixes the root cause
   - run `python3 scripts/sim_check.py --verbose` and compare to the baseline
   - if it got worse or fails, fix or revert before moving on
   - commit with a message saying what was broken, the fix, and the measured effect

5. **Check the rest.** If you touched `api/` or `web/`, start the server, load
   `http://localhost:8000/app`, and confirm no console errors and that ticks,
   header counts and the activity stream update. Run `--llm` if you touched
   decision code.

6. **Report and PR.** Push the branch and open a PR. The description must include:
   - a table of baseline vs after (alive, health, buildings, top 3 failures, errors)
   - each change: what was wrong (file:line), what you changed, how you verified
   - what you looked at but didn't change, and why
   - remaining problems, ranked

Rules: no status/"COMPLETE" docs, no silencing errors to pass the check, no
balance-number changes without before/after numbers, no pushing to `main`.
