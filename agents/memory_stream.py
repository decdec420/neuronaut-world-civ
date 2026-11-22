"""
An agent's memory stream, in the style of Generative Agents (Park et al.,
2023, "Smallville").

Everything an agent does or is part of goes in as a short first-person
record with an importance (0-1). When it decides, the most useful memories
are retrieved by three scores, each 0-1, added up:

- recency:    0.995 per game hour since the memory was last recalled
              (the paper's decay; 6 ticks = 1 game hour)
- importance: how much it mattered when it happened
- relevance:  how many words it shares with what the agent is thinking about
              (the paper uses embeddings; word overlap needs no model)

Reflections: once enough has happened (summed importance since the last
reflection reaches REFLECT_AT), an agent with a model is asked what it makes
of its recent memories; its insights go back into the stream as important
memories. Day plans: on waking, it is asked to plan its day. Both are kept
here, so the stream is the agent's own record of its life.

Bounded: at most MAX_RECORDS memories (the least important, least recent go
first), and a repeated action is one memory with a count.
"""

import re
from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, List, Optional, Tuple

TICKS_PER_HOUR = 6
DECAY_PER_HOUR = 0.995
MAX_RECORDS = 200
REFLECT_AT = 8.0          # summed importance of new memories that prompts a reflection
REPEAT_WINDOW = 12        # ticks within which the same thing again is one memory

_STOPWORDS = frozenset("""a an and are as at be but by for from had has have i i'm in is it its
me my of on or so that the their them they this to was we were with you your not no yes
did do does done just more some than then there what when where which who will would""".split())


def keywords(text: str) -> FrozenSet[str]:
    return frozenset(w for w in re.findall(r"[a-z][a-z_']+", text.lower())
                     if len(w) > 2 and w not in _STOPWORDS)


@dataclass
class MemoryRecord:
    tick: int
    text: str
    importance: float
    kind: str = "observation"       # observation | reflection | plan
    count: int = 1
    last_access: int = 0
    words: FrozenSet[str] = field(default_factory=frozenset)

    def to_dict(self) -> dict:
        return {"tick": self.tick, "text": self.text if self.count == 1 else f"{self.text} (x{self.count})",
                "importance": round(self.importance, 2), "kind": self.kind}


class MemoryStream:
    def __init__(self, max_records: int = MAX_RECORDS):
        self.max_records = max_records
        self.records: List[MemoryRecord] = []
        self.importance_since_reflection = 0.0
        self.day_plan: List[Tuple[int, str, str]] = []  # (hour, action, why)
        self.plan_day: Optional[int] = None

    # -- writing -----------------------------------------------------------------

    def add(self, tick: int, text: str, importance: float, kind: str = "observation") -> MemoryRecord:
        importance = max(0.0, min(1.0, importance))
        last = self.records[-1] if self.records else None
        if last is not None and last.text == text and last.kind == kind and tick - last.tick <= REPEAT_WINDOW:
            last.count += 1
            last.tick = last.last_access = tick
            last.importance = max(last.importance, importance)
            return last
        record = MemoryRecord(tick, text, importance, kind, last_access=tick, words=keywords(text))
        self.records.append(record)
        if kind == "observation":
            self.importance_since_reflection += importance
        if len(self.records) > self.max_records * 1.25:
            self._forget(tick)
        return record

    def _forget(self, now: int) -> None:
        """Keep the max_records memories with the best importance + recency."""
        keep = sorted(self.records, key=lambda r: -(r.importance + self._recency(r, now)))[:self.max_records]
        kept = set(map(id, keep))
        self.records = [r for r in self.records if id(r) in kept]

    # -- reading -----------------------------------------------------------------

    @staticmethod
    def _recency(record: MemoryRecord, now: int) -> float:
        return DECAY_PER_HOUR ** (max(0, now - record.last_access) / TICKS_PER_HOUR)

    def retrieve(self, about: str | Iterable[str], now: int, k: int = 5) -> List[MemoryRecord]:
        """The k memories that score best for this query; recalling them makes
        them recent again."""
        query = keywords(about) if isinstance(about, str) else frozenset(w.lower() for w in about)
        if not self.records:
            return []

        def score(r: MemoryRecord) -> float:
            relevance = len(r.words & query) / len(query) if query else 0.0
            return self._recency(r, now) + r.importance + min(1.0, relevance)

        best = sorted(self.records, key=score, reverse=True)[:k]
        for r in best:
            r.last_access = now
        return sorted(best, key=lambda r: r.tick)

    def recent(self, n: int = 20) -> List[MemoryRecord]:
        return self.records[-n:]

    def wants_reflection(self) -> bool:
        return self.importance_since_reflection >= REFLECT_AT

    def reflected(self, tick: int, insights: Iterable[str]) -> int:
        added = 0
        for insight in insights:
            insight = insight.strip(" -•*\t")
            if insight:
                self.add(tick, insight, 0.8, kind="reflection")
                added += 1
        self.importance_since_reflection = 0.0
        return added

    def set_plan(self, day: int, tick: int, items: List[Tuple[int, str, str]]) -> None:
        self.day_plan = sorted(items)[:6]
        self.plan_day = day
        if self.day_plan:
            self.add(tick, "My plan for today: " + "; ".join(f"{h:02d}:00 {a}" for h, a, _ in self.day_plan),
                     0.4, kind="plan")

    def planned_action(self, hour: int) -> Optional[str]:
        """The plan's step for this hour (the latest one at or before it)."""
        step = None
        for h, action, _ in self.day_plan:
            if h <= hour:
                step = action
        return step
