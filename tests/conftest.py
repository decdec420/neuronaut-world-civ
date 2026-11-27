"""
Most tests exercise one mechanic in a small settled village, so they run in
a settlers' world (everything known) unless they ask for the dawn
(tests/test_knowhow.py). Worlds themselves start at the dawn by default
(config.py WORLD_START).

A test server begins a new world and saves nothing when it stops, in a save
folder of its own: it must never carry on, or write over, the worlds of
whoever runs the tests (tests/test_resume.py turns these on where it means to).
"""

import os
import tempfile

os.environ.setdefault("WORLD_START", "settlers")
os.environ.setdefault("RESUME", "new")
os.environ.setdefault("AUTOSAVE_EVERY", "0")
os.environ.setdefault("SAVE_DIR", tempfile.mkdtemp(prefix="neuronaut-test-saves-"))
