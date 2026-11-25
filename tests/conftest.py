"""
Most tests exercise one mechanic in a small settled village, so they run in
a settlers' world (everything known) unless they ask for the dawn
(tests/test_knowhow.py). Worlds themselves start at the dawn by default
(config.py WORLD_START).
"""

import os

os.environ.setdefault("WORLD_START", "settlers")
