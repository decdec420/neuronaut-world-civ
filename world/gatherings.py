"""
Gatherings: someone invites the village; word spreads; people choose to come.

Smallville's best-known moment: Isabella decides to throw a Valentine's
party, mentions it to a few people, they tell others, and on the day several
agents who heard about it turn up. Here:

- organize_event: an agent announces a gathering (a feast, a dance, a
  meeting... whatever it says, or "a gathering") at the place it stands, at
  an hour it names or else this evening (EVENING_HOUR). The announcement is
  news (world/news.py): the organizer and anyone nearby know it, and it
  spreads only by people telling each other.
- attend_event: possible only for someone who has heard of a gathering that
  is on, or starts within LEAD_TICKS. It walks there (roads help) and joins
  once within JOIN_RADIUS while it's on.
- When it ends, who came is logged (and so becomes news, and history).

Nobody is made to organize or attend; the world only lets invitations
travel and lets people act on them. Bounded: MAX_UPCOMING at a time, one
upcoming gathering per organizer, the last MAX_HISTORY finished ones kept.
"""

import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

TICKS_PER_HOUR = 6
DURATION_TICKS = 12          # two hours
EVENING_HOUR = 18
LEAD_TICKS = 12              # you can set off up to two hours early
JOIN_RADIUS = 4.0
MAX_UPCOMING = 6
MAX_HISTORY = 50
KINDS = ("feast", "dance", "party", "meeting", "festival", "wedding", "council", "market", "service",
         "concert", "game", "picnic", "vigil", "celebration")


@dataclass
class Gathering:
    id: str
    organizer: str
    organizer_name: str
    kind: str
    place: str
    x: float
    y: float
    start: int
    end: int
    news_id: Optional[str] = None
    attendees: Set[str] = field(default_factory=set)
    heard_before_start: int = 0     # how many living people knew of it when it began
    finished: bool = False

    def is_on(self, tick: int) -> bool:
        return self.start <= tick < self.end


def parse_when_and_what(details: str, now: int):
    """(start tick, kind) from free text like "a feast at 19:00" or "dance
    at 8pm"; else this evening (or tomorrow's, if it's too late today)."""
    text = (details or "").lower()
    kind = next((k for k in KINDS if k in text), "gathering")
    hour = None
    m = re.search(r"\b(\d{1,2})\s*(?::\s*\d{2})?\s*(am|pm)?\b", text)
    if m:
        h = int(m.group(1))
        if m.group(2) == "pm" and h < 12:
            h += 12
        if m.group(2) == "am" and h == 12:
            h = 0
        if 0 <= h <= 23:
            hour = h
    hour = EVENING_HOUR if hour is None else hour
    day_start = now - now % (24 * TICKS_PER_HOUR)
    start = day_start + hour * TICKS_PER_HOUR
    if start < now + TICKS_PER_HOUR:   # at least an hour's notice
        start += 24 * TICKS_PER_HOUR
    return start, kind


class Gatherings:
    def __init__(self, sim):
        self.sim = sim
        self.upcoming: Dict[str, Gathering] = {}
        self.history: List[Gathering] = []
        self._next = 0

    def place_name(self, x: float, y: float) -> str:
        """Somewhere people would recognise: a building, a well, a street light."""
        sim = self.sim
        dbs = getattr(sim, "dynamic_building_system", None)
        if dbs is not None:
            near = dbs.standing_building_near(x, y, 6.0)
            if near is not None:
                return near.name
        works = getattr(sim, "infrastructure", None)
        if works is not None:
            if works.light_near(x, y, 6.0) is not None:
                return "the street light"
            if works.well_near(x, y, 6.0) is not None:
                return "the well"
        return f"the clearing at ({int(x)}, {int(y)})"

    def organized_by(self, agent_id: str) -> Optional[Gathering]:
        return next((g for g in self.upcoming.values() if g.organizer == agent_id), None)

    def announce(self, agent, details: str, tick: int) -> Gathering:
        sim = self.sim
        start, kind = parse_when_and_what(details, tick)
        x, y = agent.location.x, agent.location.y
        self._next += 1
        g = Gathering(f"gathering_{self._next}", agent.id, agent.name, kind, self.place_name(x, y),
                      x, y, start, start + DURATION_TICKS)
        day = start // (24 * TICKS_PER_HOUR) + 1
        text = f"{agent.name} invites everyone to a {kind} at {g.place}, day {day} at {start // TICKS_PER_HOUR % 24:02d}:00"
        knowers = {agent.id} | set(sim.news.witnesses(sim.world.agents, x, y))
        g.news_id = sim.news.publish(tick, text, 0.9, knowers, kind="gathering", about=[agent.id],
                                     data={"gathering_id": g.id}).id
        self.upcoming[g.id] = g
        return g

    def known_to(self, agent_id: str, tick: int) -> List[Gathering]:
        """Gatherings this agent has heard of that are on or start soon."""
        sim = self.sim
        found = []
        for g in self.upcoming.values():
            if not (g.start - LEAD_TICKS <= tick < g.end):
                continue
            if g.organizer == agent_id or (g.news_id and sim.news.knows(agent_id, g.news_id)):
                found.append(g)
        return found

    def update(self, tick: int) -> None:
        """Start and finish gatherings; log how each one went."""
        sim = self.sim
        from engine.events import EventCategory, EventImportance
        alive = [a for a in sim.world.agents if a.alive]
        for g in list(self.upcoming.values()):
            if tick == g.start:
                g.heard_before_start = sum(1 for a in alive if g.news_id and sim.news.knows(a.id, g.news_id))
                organizer = sim._get_agent_by_id(g.organizer)
                if organizer is not None and organizer.alive and \
                        math.hypot(organizer.location.x - g.x, organizer.location.y - g.y) <= JOIN_RADIUS * 3:
                    g.attendees.add(organizer.id)
            if tick >= g.end:
                g.finished = True
                del self.upcoming[g.id]
                self.history.append(g)
                del self.history[:-MAX_HISTORY]
                came = [sim._get_agent_by_id(i) for i in sorted(g.attendees)]
                names = [a.name for a in came if a is not None]
                importance = EventImportance.MAJOR if len(names) >= 4 else EventImportance.MODERATE if names else EventImportance.MINOR
                sim.event_logger.log_event(
                    EventCategory.SOCIAL, importance,
                    f"🎉 {g.organizer_name}'s {g.kind} at {g.place}: {len(names)} came",
                    f"{g.heard_before_start} had heard of it. " + (f"There: {', '.join(names)}." if names else "Nobody came."),
                    tick, sorted(g.attendees) or [g.organizer], {"x": g.x, "y": g.y})
