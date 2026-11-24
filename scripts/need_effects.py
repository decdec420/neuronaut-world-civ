"""
Which needs each action really meets, measured: runs every action the rule-based
brain can choose in a small test village and diffs the agent's needs. Prints
what the brain credits next to what happened, and any mismatch.

    python3 scripts/need_effects.py

Keep agents/utility_brain.py ACTION_NEEDS in step with this when you change what
an action does (tests/test_need_effects.py fails until you do).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, ROOT)

from test_need_effects import measure  # noqa: E402
from agents.utility_brain import ACTION_NEEDS, EFFECT_LATER  # noqa: E402

bad = 0
for name, credited in sorted(ACTION_NEEDS.items()):
    ok, relieved = measure(name)
    claim = {n.value: w for n, w in credited.items()}
    later = name in EFFECT_LATER
    missing = [] if later else [n for n in claim if n not in relieved]
    flag = "later" if later else ("MISMATCH" if missing or (not claim and relieved) else "ok")
    bad += flag == "MISMATCH"
    print(f"{name:22s} {flag:8s} ran={'yes' if ok else 'no ':3s} credited {claim}  relieved {relieved}")
print(f"\n{bad} mismatches")
sys.exit(1 if bad else 0)
