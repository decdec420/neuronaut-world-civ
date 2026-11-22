---
description: Read-only review of Neuronaut World. Finds what's broken or not working as intended and ranks it; changes nothing
argument-hint: "[optional area, e.g. 'economy' or 'web viewer']"
---

Audit Neuronaut World without changing any code. Area: $ARGUMENTS
(If no area was given, cover the whole sim.)

1. Run `python3 scripts/sim_check.py --verbose` (and `--llm`) and record the results.
2. Start the server (`USE_LLM_DECISIONS=false python3 main.py`), hit the API
   endpoints in `api/server.py`, and load `/app`. Note anything erroring or not updating.
3. For the area in scope, trace the main code paths end to end. Look for:
   - features that exist in code but can never trigger (unreachable conditions,
     handlers never registered, events nobody listens to)
   - actions that fail every tick, or succeed but change nothing
   - inverted or mis-scaled logic (need levels run 0 = satisfied → 1 = desperate)
   - fields read under a different name than they're written
   - docs/status files claiming things the code doesn't do
4. Write the findings to `AUDIT.md`, ranked by impact. For each: what's wrong,
   evidence (file:line plus a log line or number from step 1–2), why it matters
   for the society, and a suggested fix with rough size (S/M/L).
5. End with the top 3 you'd fix first. Don't edit any other file.
