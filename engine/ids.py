"""
Ids for things in the world, made from the world's own dice.

Agents, buildings, faiths, laws, events... used to get ids from uuid.uuid4(),
which draws on the operating system's randomness. So the same seed never gave
the same world twice: ids differ, and anything sorted or compared by id (and
everything downstream of that) differed with them.

new_uuid() returns a version-4 UUID like uuid4() does, but drawn from a
generator the simulation seeds from its own dice when it starts, and that is
saved and restored with the world (engine/persistence.py). One generator per
process, like `random`.
"""

import random
import uuid

_rng = random.Random()


def new_uuid() -> uuid.UUID:
    """A random-looking version-4 UUID from the world's id generator."""
    return uuid.UUID(int=_rng.getrandbits(128), version=4)


def seed(value) -> None:
    _rng.seed(value)


def get_state():
    return _rng.getstate()


def set_state(state) -> None:
    _rng.setstate(state)
