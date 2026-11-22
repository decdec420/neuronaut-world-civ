"""
News and how it spreads: who knows what, and conversations that pass it on.

In Generative Agents (Park et al., 2023) information travels the way it does
in a real town: Isabella tells a few people about her party, they tell
others, and by the day half the town knows. Here:

- Something that matters happens (a logged event of moderate importance or
  more: a couple forms, a law is proposed, a child is born, someone puts up
  a street light...). It becomes a piece of news. Those involved know it,
  and so does anyone within WITNESS_RADIUS who saw it.
- When two agents talk (socialize; tell_story, one way), each passes on the
  most important, most recent thing it knows that the other doesn't. The
  listener remembers who told it; the teller remembers telling.
- Agents with an AI mind see the news they've heard in their prompt, and
  can act on it (e.g. go to a gathering they heard about).

Nothing decides who talks to whom: agents choose to socialize. This only
carries what they know along with them. Bounded: MAX_NEWS items, and each
agent remembers MAX_KNOWN of them.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

WITNESS_RADIUS = 10.0
MAX_NEWS = 300
MAX_KNOWN = 60
RECENCY_TICKS = 144 * 3   # news fades from "worth telling" over about three days


@dataclass
class News:
    id: str
    tick: int
    text: str
    importance: float                 # 0-1
    about: List[str] = field(default_factory=list)   # agent ids it concerns
    kind: str = "event"               # event | gathering
    data: Dict = field(default_factory=dict)

    def worth(self, now: int) -> float:
        """How worth telling it is now: importance, fading with age."""
        return self.importance * max(0.1, 1.0 - (now - self.tick) / RECENCY_TICKS)


class NewsNetwork:
    def __init__(self):
        self.items: Dict[str, News] = {}
        self.known: Dict[str, Dict[str, int]] = {}   # agent id -> news id -> tick learned
        self.conversations = 0
        self.told = 0
        self._next = 0

    # -- what happens ----------------------------------------------------------

    def publish(self, tick: int, text: str, importance: float, knowers: Iterable[str],
                kind: str = "event", about: Iterable[str] = (), data: Optional[Dict] = None) -> News:
        self._next += 1
        news = News(f"news_{self._next}", tick, text, importance, list(about), kind, data or {})
        self.items[news.id] = news
        for agent_id in set(knowers):
            self.learn(agent_id, news.id, tick)
        if len(self.items) > MAX_NEWS * 1.2:
            keep = sorted(self.items.values(), key=lambda n: (n.importance, n.tick))[-MAX_NEWS:]
            self.items = {n.id: n for n in sorted(keep, key=lambda n: n.tick)}
        return news

    def learn(self, agent_id: str, news_id: str, tick: int) -> bool:
        known = self.known.setdefault(agent_id, {})
        if news_id in known:
            return False
        known[news_id] = tick
        if len(known) > MAX_KNOWN * 1.2:
            for old in sorted(known, key=known.get)[:len(known) - MAX_KNOWN]:
                del known[old]
        return True

    def knows(self, agent_id: str, news_id: str) -> bool:
        return news_id in self.known.get(agent_id, {})

    @staticmethod
    def witnesses(agents, x: float, y: float) -> List[str]:
        return [a.id for a in agents if a.alive and math.hypot(a.location.x - x, a.location.y - y) <= WITNESS_RADIUS]

    # -- talking -----------------------------------------------------------------

    def worth_telling(self, teller_id: str, listener_id: str, now: int) -> Optional[News]:
        """The most important, freshest thing the teller knows and the listener doesn't."""
        best, best_worth = None, 0.0
        for news_id in self.known.get(teller_id, {}):
            news = self.items.get(news_id)
            if news is None or self.knows(listener_id, news_id):
                continue
            worth = news.worth(now)
            if worth > best_worth:
                best, best_worth = news, worth
        return best

    def converse(self, teller, listener, now: int, both_ways: bool = True) -> List[Tuple[object, object, News]]:
        """A conversation: each passes on one thing the other hasn't heard.
        Returns [(teller, listener, news)] for what was passed on."""
        self.conversations += 1
        passed = []
        pairs = [(teller, listener), (listener, teller)] if both_ways else [(teller, listener)]
        for speaker, hearer in pairs:
            news = self.worth_telling(speaker.id, hearer.id, now)
            if news is None:
                continue
            self.learn(hearer.id, news.id, now)
            self.told += 1
            passed.append((speaker, hearer, news))
            stream = getattr(hearer, "memory_stream", None)
            if stream is not None:
                stream.add(now, f"{speaker.name} told me: {news.text}", 0.2 + 0.6 * news.importance)
            stream = getattr(speaker, "memory_stream", None)
            if stream is not None:
                stream.add(now, f"I told {hearer.name}: {news.text}", 0.1)
        return passed

    # -- reading -----------------------------------------------------------------

    def heard_by(self, agent_id: str, now: int, n: int = 3) -> List[News]:
        """What this agent knows that's most worth thinking about now."""
        items = [self.items[i] for i in self.known.get(agent_id, {}) if i in self.items]
        return sorted(items, key=lambda news: -news.worth(now))[:n]

    def reach(self, news_id: str, alive_ids: Iterable[str]) -> float:
        alive = list(alive_ids)
        if not alive:
            return 0.0
        return sum(1 for a in alive if self.knows(a, news_id)) / len(alive)
