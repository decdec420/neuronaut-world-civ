"""
What an agent has set out to do and is part-way through.

Agents decide afresh every tick. Without some memory of what they were in the
middle of, a walk of fifty tiles (to a gathering, to shelter, to a water
source) was given up a few steps in whenever anything else looked as good,
and so it rarely got anywhere. People finish what they set out to do, more or
less, depending on who they are.

A commitment starts when an action takes the agent a step toward somewhere
(every walk goes through infrastructure.step_toward, which notes where the
step was headed), or when a handler says the action is under way without a
step (waiting at a gathering for it to begin). It ends when the action runs
without taking a step and without saying it's still under way (the agent has
arrived and done it), when the action fails, or after MAX_TICKS.

Something else can come first: thirst on the way to a party (survival is
handled before any choice), or a walk home at nightfall. That detour is a
commitment of its own, and the one it interrupted is set aside (one level
deep) and taken up again once the detour is done. With a single slot, the
detour used to replace it: on seed 1, 99 of 186 walks to a gathering were
forgotten after a stop for water or food.

What it changes is a weight: the rule-based brain feels a pull to carry on
(agents/utility_brain.py COMMIT_PULL, stronger the more conscientious the
agent), and the AI brain is told what it set out to do. Neither has to.
"""

import collections
from dataclasses import dataclass
from typing import Optional

MAX_TICKS = 72   # half a day: past that, whatever it set out to do is forgotten


@dataclass
class Commitment:
    action: str          # the action it set out to do
    x: float             # where it was heading
    y: float
    since: int           # the tick it set out
    last: int            # the tick it last made progress
    then: Optional['Commitment'] = None   # what it set aside for this, to take up after


def _ended(agent, how: str) -> None:
    """Keep count of how the agent's commitments end (sim_check reports it)."""
    if not hasattr(agent, 'commitments_ended'):
        agent.commitments_ended = collections.Counter()
    agent.commitments_ended[how] += 1


def current(agent, tick: int) -> Optional[Commitment]:
    """The agent's commitment, unless it has run out (then whatever it had set
    aside for it, unless that has run out too)."""
    c = getattr(agent, 'commitment', None)
    while c is not None and tick - c.since > MAX_TICKS:
        _ended(agent, 'ran out')
        c = c.then
        agent.commitment = c
    return c


def note(agent, action_name: str, result: dict, tick: int) -> None:
    """After an action ran: start, carry on or end the agent's commitment."""
    step = getattr(agent, 'stepped_toward', None)
    agent.stepped_toward = None
    ok = bool(result.get('success'))
    underway = bool(result.get('underway'))   # an ActionResult's metadata is merged into the dict
    c = current(agent, tick)
    if ok and (step is not None or underway):
        x, y = step if step is not None else (agent.location.x, agent.location.y)
        if c is not None and c.action == action_name:
            c.x, c.y, c.last = x, y, tick
        else:
            # Something else first: set out on it, and keep this one for after
            if c is not None and c.then is not None:
                _ended(agent, 'dropped')            # only one thing is kept for later
                c.then = None
            agent.commitment = Commitment(action_name, x, y, tick, tick, then=c)
    elif c is not None and c.action == action_name:
        agent.commitment = c.then                   # back to what it set aside, if anything
        _ended(agent, 'done' if ok else 'could not')   # arrived and did it, or it can't be done
