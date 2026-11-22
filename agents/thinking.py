"""
Agents think in parallel, and the world doesn't wait for slow minds.

A model call can take a second (a cloud provider) or twenty (a 3B model on a
laptop CPU). Asking twelve agents one after another would stall every tick, so
each tick (AgentUpdater.update_all_agents):

1. start(): agents due to think get a prompt built now, from what they see,
   and their call runs in a worker thread. An agent is due when it has no
   call in flight, hasn't thought for `think_every` ticks, isn't a baby and
   isn't in urgent need (survival comes first, without the model). Only as
   many calls as there are workers are in flight at once, longest-waiting
   agents first, so a slow model never builds a backlog.
2. wait(): the tick waits up to `tick_budget` seconds for those calls.
3. On its turn, take() hands an agent its answer if one is ready. If not, the
   rule-based brain decides this tick (AgentUpdater), drawn toward what the
   agent last decided with its model (its intent) until it thinks again.
   An answer that comes back late is used on a later turn, unless it is older
   than `max_age` ticks.

Settings (.env): LLM_WORKERS, LLM_THINK_EVERY, LLM_TICK_BUDGET.
"""

import collections
import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor, wait as wait_futures
from typing import Callable, Dict, Iterable, Optional, Tuple

logger = logging.getLogger(__name__)


class ThinkingScheduler:
    def __init__(self, complete: Callable[[str], Optional[str]], workers: int = 2,
                 think_every: int = 6, tick_budget: float = 2.0, max_age: Optional[int] = None):
        """complete: prompt -> answer text or None (MultiLLMBrain.complete)."""
        self.complete = complete
        self.workers = max(1, workers)
        self.think_every = max(1, think_every)
        self.tick_budget = max(0.0, tick_budget)
        self.max_age = max_age if max_age is not None else 3 * self.think_every
        self.executor = ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="agent-mind")
        self.pending: Dict[str, Tuple[int, Future]] = {}   # agent id -> (tick asked, call)
        self.ready: Dict[str, Tuple[int, Optional[str]]] = {}  # agent id -> (tick asked, answer)
        self.last_asked: Dict[str, int] = {}
        self.stats = collections.Counter()
        self.wait_seconds = 0.0

    # -- each tick ---------------------------------------------------------------

    def is_due(self, agent_id: str, tick: int) -> bool:
        if agent_id in self.pending or agent_id in self.ready:
            return False
        last = self.last_asked.get(agent_id)
        return last is None or tick - last >= self.think_every

    def start(self, candidates: Iterable, tick: int, build_prompt: Callable[[object], Optional[str]]) -> int:
        """Start calls for due agents, longest-waiting first, up to the free
        workers. build_prompt(agent) -> prompt, or None to skip the agent.
        Returns how many calls started."""
        self._collect()
        free = self.workers - len(self.pending)
        if free <= 0:
            return 0
        due = [a for a in candidates if self.is_due(a.id, tick)]
        due.sort(key=lambda a: self.last_asked.get(a.id, -10 ** 9))
        started = 0
        for agent in due:
            if started >= free:
                break
            prompt = build_prompt(agent)
            if prompt is None:
                continue
            self.submit(agent.id, prompt, tick)
            started += 1
        return started

    def submit(self, agent_id: str, prompt: str, tick: int) -> None:
        self.pending[agent_id] = (tick, self.executor.submit(self.complete, prompt))
        self.last_asked[agent_id] = tick
        self.stats["asked"] += 1

    def wait(self, budget: Optional[float] = None) -> None:
        """Wait up to budget seconds (default tick_budget) for calls in flight."""
        budget = self.tick_budget if budget is None else budget
        if self.pending and budget > 0:
            start = time.perf_counter()
            wait_futures([f for _, f in self.pending.values()], timeout=budget)
            self.wait_seconds += time.perf_counter() - start
        self._collect()

    def take(self, agent_id: str, tick: int) -> Optional[str]:
        """The agent's answer, if one is ready and fresh enough."""
        self._collect()
        asked_and_answer = self.ready.pop(agent_id, None)
        if asked_and_answer is None:
            return None
        asked, answer = asked_and_answer
        if answer is None:
            self.stats["no_answer"] += 1
            return None
        if tick - asked > self.max_age:
            self.stats["stale"] += 1
            return None
        self.stats["late" if tick > asked else "on_time"] += 1
        return answer

    def _collect(self) -> None:
        for agent_id, (asked, future) in list(self.pending.items()):
            if future.done():
                del self.pending[agent_id]
                try:
                    self.ready[agent_id] = (asked, future.result())
                except Exception as e:  # a failed call is a missing answer, logged
                    logger.warning(f"Model call for agent {agent_id} failed: {e}")
                    self.ready[agent_id] = (asked, None)

    def forget(self, agent_id: str) -> None:
        """Drop an agent (it died): its answer, if any, is no longer wanted."""
        self.ready.pop(agent_id, None)
        self.last_asked.pop(agent_id, None)

    def close(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)
