"""
Gatherings: an invitation spreads by word of mouth; people choose to come
(world/gatherings.py). The Smallville party, without a script.

    python3 -m pytest tests/test_gatherings.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_capabilities import act  # noqa: E402
from test_reachability import make_world  # noqa: E402


def test_when_and_what_come_from_the_invitation():
    from world.gatherings import parse_when_and_what
    noon = 12 * 6
    assert parse_when_and_what("a feast at 19:00", noon) == (19 * 6, "feast")
    assert parse_when_and_what("a dance at 8pm", noon) == (20 * 6, "dance")
    assert parse_when_and_what("", noon) == (18 * 6, "gathering")       # this evening
    assert parse_when_and_what("a meeting at 9", noon)[0] == (24 + 9) * 6  # 9:00 has passed: tomorrow


def test_an_invitation_spreads_by_word_of_mouth_and_people_come():
    from agents.agent import Action, ActionType, Position
    sim, roles = make_world()
    host, near, far, other = roles["actor"], roles["partner"], roles["sick"], roles["neighbour"]
    far.location, other.location = Position(90, 90), Position(10, 90)
    sim.world.time.current_tick = 17 * 6  # 17:00
    attend = sim._handler_registry.get_handler(ActionType.ATTEND_EVENT)

    invite = act(sim, host, "organize_event", details="a feast at 18:00")
    g = sim.gatherings.upcoming[invite.metadata["gathering_id"]]
    assert g.kind == "feast" and g.start == 18 * 6
    news = sim.news.items[g.news_id]
    assert "feast" in news.text and "18:00" in news.text
    assert sim.news.knows(near.id, news.id) and not sim.news.knows(far.id, news.id)
    assert not attend.validate(far, Action(ActionType.ATTEND_EVENT))[0]  # never heard of it

    # Word of mouth: near tells far; now far can choose to go
    sim.news.converse(near, far, now=sim.world.time.current_tick)
    assert attend.validate(far, Action(ActionType.ATTEND_EVENT))[0]
    assert not attend.validate(other, Action(ActionType.ATTEND_EVENT))[0]

    # far walks over, then joins once it's on
    start = far.location
    assert "On the way" in act(sim, far, "attend_event").message
    assert far.location.distance_to(Position(g.x, g.y)) < start.distance_to(Position(g.x, g.y))
    far.location = Position(g.x + 1, g.y)
    assert "Waiting" in act(sim, far, "attend_event").message
    sim.world.time.current_tick = g.start
    sim.gatherings.update(g.start)
    assert act(sim, far, "attend_event").metadata["joined"]
    assert g.heard_before_start == 3  # host, near, far (other never heard)

    # It ends: logged with who came, and it's a first in the chronicle
    sim.gatherings.update(g.end)
    assert not sim.gatherings.upcoming and sim.gatherings.history[-1] is g
    assert any("feast" in e.title and "came" in e.title for e in sim.event_logger.events)
    sim.chronicle.observe(sim, g.end)
    assert "first_gathering" in sim.chronicle.done


def test_one_gathering_per_host_at_a_time():
    from agents.agent import Action, ActionType
    sim, roles = make_world()
    host = roles["actor"]
    act(sim, host, "organize_event")
    ok, why = sim._handler_registry.get_handler(ActionType.ORGANIZE_EVENT).validate(host, Action(ActionType.ORGANIZE_EVENT))
    assert not ok and "already hosting" in why


def test_a_host_who_names_no_time_avoids_one_it_has_heard_of():
    from agents.daily_life import DailyRoutine
    from world.gatherings import parse_when_and_what, free_evening_hours
    noon = 12 * 6
    night_owl = DailyRoutine(wake_hour=8, work_start=9, work_end=17, sleep_hour=23)
    assert free_evening_hours(night_owl) == [18, 19, 20, 21, 17]
    assert parse_when_and_what("", noon, busy=[], routine=night_owl)[0] == 18 * 6
    # it heard of one at 18:00; 19:00 would overlap it (two hours), so 20:00
    assert parse_when_and_what("", noon, busy=[18 * 6], routine=night_owl)[0] == 20 * 6
    # a time it names is kept, clash or not
    assert parse_when_and_what("a dance at 18:00", noon, busy=[18 * 6], routine=night_owl)[0] == 18 * 6
    # every evening hour taken today: tomorrow
    early_bird = DailyRoutine(wake_hour=6, work_start=7, work_end=15, sleep_hour=21)
    busy = [15 * 6, 17 * 6, 19 * 6]
    assert parse_when_and_what("", noon, busy=busy, routine=early_bird)[0] == (24 + 18) * 6

    # in the world: the second host had heard of the first's gathering
    sim, roles = make_world()
    first, second = roles["actor"], roles["partner"]
    sim.world.time.current_tick = noon
    g1 = sim.gatherings.upcoming[act(sim, first, "organize_event").metadata["gathering_id"]]
    assert sim.news.knows(second.id, g1.news_id)
    g2 = sim.gatherings.upcoming[act(sim, second, "organize_event").metadata["gathering_id"]]
    assert abs(g2.start - g1.start) >= 12

