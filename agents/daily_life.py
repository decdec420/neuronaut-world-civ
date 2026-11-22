"""
Daily life: a day plan and jobs.

Loosely modelled on Stanford's Generative Agents ("Smallville", Park et al.
2023), where every agent follows a plan for the day (sleep, work, free time)
and has an occupation. There is no language model in this loop, so:

- the plan is a simple schedule shaped by personality (early risers,
  night owls), and
- jobs are not handed out. The rule-based brain (agents/utility_brain.py)
  leans toward work in work hours and toward the agent's own job most; the
  work an agent ends up doing most in work hours becomes its job. Jobs can
  drift if the agent keeps doing other work.

Survival always comes first: the agent updater handles urgent hunger, thirst
and exhaustion before it consults the plan.
"""

from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Day plan
# ---------------------------------------------------------------------------

SLEEP, MORNING, WORK, FREE_TIME = 'sleep', 'morning', 'work', 'free_time'


@dataclass
class DailyRoutine:
    """When an agent gets up, works, and goes to bed (hours 0-23)."""
    wake_hour: int = 7
    work_start: int = 8
    work_end: int = 16
    sleep_hour: int = 22

    @classmethod
    def for_personality(cls, personality) -> 'DailyRoutine':
        """Disciplined agents rise early; sociable agents stay up later."""
        wake = 6 + round((1.0 - personality.conscientiousness) * 2)   # 6-8
        work_start = wake + 1                                          # 7-9
        work_end = work_start + 8                                      # 15-17
        sleep = 21 + round(personality.extraversion * 2)               # 21-23
        return cls(wake, work_start, work_end, sleep)

    def block(self, hour: int) -> str:
        """Which part of the day this hour falls in."""
        if hour >= self.sleep_hour or hour < self.wake_hour:
            return SLEEP
        if self.work_start <= hour < self.work_end:
            return WORK
        if hour < self.work_start:
            return MORNING
        return FREE_TIME

    def to_dict(self) -> Dict:
        return {'wake_hour': self.wake_hour, 'work_start': self.work_start,
                'work_end': self.work_end, 'sleep_hour': self.sleep_hour}


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Job:
    title: str
    actions: Tuple[str, ...]  # tried in order; the first one that can run is done
    traits: Tuple[str, ...]   # personality traits that draw an agent to this work


# Only work whose actions actually succeed today. Farming needs seeds that no
# one can get yet, and trading needs money that no one has (AUDIT.md finding
# 6), so neither is a job until those work.
JOBS: Dict[str, Job] = {
    'builder': Job('Builder', ('build', 'gather_materials'), ('conscientiousness', 'ambition')),
    'gatherer': Job('Gatherer', ('gather_materials', 'chop_wood', 'mine'), ('conscientiousness', 'risk_taking')),
    'forager': Job('Forager', ('gather_food', 'hunt'), ('risk_taking', 'agreeableness')),
    'inventor': Job('Inventor', ('experiment',), ('openness', 'creativity')),
    'teacher': Job('Teacher', ('teach', 'write'), ('agreeableness', 'empathy')),
    'storyteller': Job('Storyteller', ('tell_story', 'create_art', 'play_game'), ('extraversion', 'creativity')),
    'healer': Job('Healer', ('heal',), ('empathy', 'agreeableness')),
}

# Work shifts (ticks of work) an agent puts in before it settles into a job,
# and how many recent shifts count when deciding what its job is. A work day
# is 8 hours = 48 ticks, so a job emerges after about two days of work.
SHIFTS_BEFORE_JOB = 96
SHIFTS_REMEMBERED = 144


@dataclass
class WorkLife:
    """An agent's job and the recent work it has done."""
    job: Optional[str] = None
    recent_shifts: Deque[str] = field(default_factory=lambda: deque(maxlen=SHIFTS_REMEMBERED))

    def record_shift(self, job_key: str) -> Optional[str]:
        """Count a shift of work. Returns the new job if it changed.

        Every shift counts, not just successful ones: a failed experiment is
        still a day at the bench. Counting only successes pushed everyone into
        work that never fails (teaching, storytelling).
        """
        self.recent_shifts.append(job_key)
        if len(self.recent_shifts) < SHIFTS_BEFORE_JOB:
            return None
        most_done = Counter(self.recent_shifts).most_common(1)[0][0]
        if most_done != self.job:
            self.job = most_done
            return most_done
        return None

    def to_dict(self) -> Dict:
        counts = Counter(self.recent_shifts)
        return {
            'job': self.job,
            'job_title': JOBS[self.job].title if self.job else None,
            'work_experience': {JOBS[k].title: n for k, n in counts.most_common()},
        }


def job_for(action: str, current_job: Optional[str] = None) -> Optional[str]:
    """Which job a piece of work counts toward: the agent's own job if the
    action is part of it, otherwise the first job that does this work."""
    if current_job and action in JOBS[current_job].actions:
        return current_job
    return next((key for key, job in JOBS.items() if action in job.actions), None)
