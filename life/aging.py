"""
Aging: life stages and natural death.

Life years are compressed. By default one year of life passes per simulated
day (TICKS_PER_LIFE_YEAR = 144 ticks; set it in .env), so a lifetime is a
few months of sim time and generations turn over in a run you can watch.
Calendar time (hours, days, seasons) is unchanged.

Stages: baby (0-1), child (2-15), adult (16-59), elder (60+).

Old age: from 50 the yearly chance of dying of old age follows a Gompertz
curve: 0.4% at 50, doubling about every 8 years (2.2% at 70, 5% at 80, 12% at
90). Of those who reach 50, about half live past 82. Hunger, illness,
disasters and fights can of course end a life sooner.
"""

import math

from life.family import ADULT_AGE

BABY_UNTIL = 2
ELDER_FROM = 60
OLD_AGE_FROM = 50
BASE_YEARLY_RISK = 0.004
RISK_GROWTH = 0.085


def life_stage(age: int) -> str:
    if age < BABY_UNTIL:
        return "baby"
    if age < ADULT_AGE:
        return "child"
    if age < ELDER_FROM:
        return "adult"
    return "elder"


def yearly_old_age_risk(age: int) -> float:
    """Chance (0-1) of dying of old age within the year, at this age."""
    if age < OLD_AGE_FROM:
        return 0.0
    return min(1.0, BASE_YEARLY_RISK * math.exp(RISK_GROWTH * (age - OLD_AGE_FROM)))
