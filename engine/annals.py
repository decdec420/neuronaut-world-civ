"""
The annals: the village's history, day by day, for as long as the world lasts.

The chronicle (engine/chronicle.py) writes down firsts. The annals write down
everything that changed the village each day: who was born and to whom, who
died, of what and at what age, who paired up or parted, who came of age;
what people worked out, picked up and taught, and what was lost; governments
founded and fallen, laws, elections, revolutions; faiths founded, spread and
temples built; buildings finished and fallen; disasters and what they cost;
gatherings, celebrations, inventions and wars; and, at the end of each day,
the village as it was (people, couples, homes, what they knew, the age).

It looks at the world once an hour of sim time and writes down what changed.
It never changes anything and never rolls the world's dice, so a world runs
the same with it as without it. A world saved before the annals existed has
its earlier days pieced together from the records that kept their time
(know-how, governments, faiths, disasters, gatherings, inventions, births of
the living); those days are marked as pieced together.

Served at GET /annals (engine/annals.py annals_view) for the Chronicle tab.
"""

from collections import Counter
from typing import Dict, List, Optional, Tuple

TICKS_PER_DAY = 144
TICKS_PER_HOUR = 6
MAX_PER_DAY = 400        # happenings kept for one day; beyond that they are only counted
DAYS_PER_CHAPTER = 10

# How much a kind of happening matters, for headlines and for what a short
# view shows (0: counted only, 5: changes the village)
WEIGHT = {
    'began': 5, 'age': 5, 'war': 5,
    'first_knowhow': 4, 'lost': 4, 'disaster': 4, 'government': 4, 'revolution': 4, 'fell': 4,
    'faith': 4, 'war_end': 4, 'first': 4,
    'born': 3, 'died': 3, 'coupled': 3, 'parted': 3, 'elected': 3, 'temple': 3, 'collapsed': 3,
    'revolt': 3, 'revolt_end': 3,
    'came_of_age': 2, 'law': 2, 'repealed': 2, 'built': 2, 'insight': 2, 'gathering': 2, 'arrived': 2,
    'tax': 2, 'tax_repealed': 2,
    'invention': 1, 'taught': 1, 'watched': 1, 'converted': 1, 'joined_faith': 1, 'lapsed': 1,
    'celebration': 1, 'election': 1, 'taxes': 1, 'role': 1,
}
# Chronicle firsts the annals already tell in their own words (they mark that happening as a first)
FIRST_OF = {'first_couple': 'coupled', 'first_birth': 'born', 'first_government': 'government',
            'first_religion': 'faith', 'first_law': 'law', 'first_death': 'died', 'first_death_old_age': 'died',
            'first_coming_of_age': 'came_of_age', 'first_home': 'built', 'first_invention': 'invention',
            'first_war': 'war', 'first_separation': 'parted', 'first_gathering': 'gathering',
            'first_temple': 'temple'}
DEATH_WORDS = {'old age': 'of old age', 'starvation': 'of hunger', 'dehydration': 'of thirst',
               'exhaustion': 'of exhaustion', 'disease': 'of illness', 'combat': 'in a fight', 'fight': 'in a fight'}


def _day(tick: int) -> int:
    return tick // TICKS_PER_DAY + 1


def _a(word: str) -> str:
    word = str(word).replace('_', ' ')
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word


def _and(names: List[str]) -> str:
    names = [n for n in names if n]
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def death_words(cause: Optional[str]) -> str:
    cause = str(cause or 'unknown causes')
    if cause in DEATH_WORDS:
        return DEATH_WORDS[cause]
    from world.disasters import DisasterType
    if cause in {d.value for d in DisasterType}:
        return f"in {_a(cause)}"
    return f"of {cause.replace('_', ' ')}"


def _newer(entries, after: int, tick_of=lambda e: e[0]) -> list:
    """The entries of an append-only list kept in time order whose tick is
    after `after`, found from the end (histories are long; the news is short)."""
    entries = list(entries)
    start = len(entries)
    while start > 0:
        t = tick_of(entries[start - 1])
        if t is not None and t <= after:
            break
        start -= 1
    return entries[start:]


class Annals:
    """The record (sim.annals); observe() once a tick, read with annals_view()."""

    def __init__(self):
        self.days: Dict[int, Dict] = {}       # day number -> its record
        self.started_tick: Optional[int] = None
        self.read_to = -1                       # records with tick <= read_to have been read
        self._people: Dict[str, Dict] = {}      # agent id -> what it was at the last look
        self._buildings: Dict[str, str] = {}    # building id -> up | done | fallen
        self._repairs: Dict[str, int] = {}
        self._wars: Dict[str, str] = {}         # war id -> what it was called
        self._celebrations: set = set()
        self._age: Optional[str] = None
        self._actions_at_dawn: Counter = Counter()

    # -- writing -------------------------------------------------------------------

    def _record(self, day: int) -> Dict:
        rec = self.days.get(day)
        if rec is None:
            rec = self.days[day] = {"day": day, "happenings": [], "counts": Counter(), "weather": Counter(),
                                    "actions": {}, "end": None}
        return rec

    def add(self, tick: int, kind: str, text: str, people=(), ref: Optional[Dict] = None,
            weight: Optional[int] = None, count_as: Optional[str] = None) -> Optional[Dict]:
        """Write down that something happened. people: agents (or (id, name))
        it is about, to link them; ref: what the dashboard opens."""
        rec = self._record(_day(tick))
        rec["counts"][count_as or kind] += 1
        w = WEIGHT.get(kind, 1) if weight is None else weight
        if w <= 0:
            return None
        if len(rec["happenings"]) >= MAX_PER_DAY:
            rec["counts"]["unwritten"] += 1
            return None
        named = []
        for p in people:
            if p is None:
                continue
            pid, name = (p.id, p.name) if hasattr(p, 'id') else p
            if pid and name and (pid, name) not in named:
                named.append((pid, name))
        h = {"tick": tick, "kind": kind, "w": w, "text": text, "people": named, "ref": ref}
        rec["happenings"].append(h)
        return h

    # -- looking at the world ---------------------------------------------------------

    def observe(self, sim, tick: int) -> None:
        """Once an hour (its last tick), write down what changed; close the day at its end."""
        if (tick + 1) % TICKS_PER_HOUR:
            return
        if self.started_tick is None:
            self._begin(sim, tick)
        else:
            self._read(sim, self.read_to, tick)
        self.read_to = tick
        weather = getattr(getattr(sim, 'weather', None), 'current_weather', None)
        if weather is not None:
            self._record(_day(tick))["weather"][getattr(weather, 'value', str(weather))] += 1
        if (tick + 1) % TICKS_PER_DAY == 0:
            self._close_day(sim, tick)

    def _begin(self, sim, tick: int) -> None:
        """The first look. A new world: its first people. A world older than
        its annals: piece together its past from what kept its time."""
        self.started_tick = tick
        self._actions_at_dawn = Counter(getattr(sim, 'action_successes', {}))
        founders = [a for a in sim.world.agents if not (a.mother_id or a.father_id)]
        if tick < TICKS_PER_DAY:
            dawn = getattr(getattr(sim, 'knowhow', None), 'active', False)
            self.add(0, 'began', (f"{len(founders)} people woke at the dawn of time, knowing only what comes "
                                  f"with being human" if dawn else
                                  f"{len(founders)} settlers arrived, knowing all they would need"), founders)
        for a in sim.world.agents:
            self._people[a.id] = self._person_now(a)
            if (a.mother_id or a.father_id) and a.alive:
                self._born(sim, a, max(0, tick - int(getattr(a, 'ticks_lived', 0))))
            died = getattr(a, 'death_tick', None)
            if not a.alive and died is not None and 0 <= died <= tick:
                self._died(sim, a, died)
        self._read(sim, -1, tick, people=False)
        self._age = self._age_now(sim)

    def _person_now(self, a) -> Dict:
        from life import family
        return {"alive": a.alive, "partner": a.partner_id, "adult": family.is_adult(a)}

    def _name(self, sim, agent_id) -> Tuple[Optional[str], Optional[str]]:
        a = sim._get_agent_by_id(agent_id) if agent_id else None
        return (a.id, a.name) if a is not None else (None, None)

    def _born(self, sim, child, tick: int) -> None:
        parents = [self._name(sim, child.mother_id), self._name(sim, child.father_id)]
        parents = [p for p in parents if p[0]]
        text = f"{child.name} was born" + (f" to {_and([p[1] for p in parents])}" if parents else "")
        self.add(tick, 'born', text, [child] + parents, ref={"kind": "agent", "id": child.id})

    def _read(self, sim, after: int, now: int, people: bool = True) -> None:
        """Write down what happened after `after` up to `now`. people=False:
        the first look, which only remembers who is there."""
        def fresh(t) -> bool:
            return t is not None and after < t <= now
        if people:
            self._read_people(sim, now)
        self._read_knowhow(sim, after, fresh)
        self._read_governments(sim, after, fresh)
        self._read_faiths(sim, after, fresh)
        self._read_buildings(sim, now, quiet=not people)
        self._read_disasters(sim, fresh)
        self._read_gatherings(sim, after, fresh)
        self._read_celebrations(sim, fresh)
        self._read_inventions(sim, fresh)
        self._read_wars(sim, now, quiet=not people)
        self._read_taxes(sim, now, fresh, quiet=not people)
        self._read_roles(sim, fresh)
        self._read_firsts(sim, after, fresh)

    def _read_people(self, sim, now: int) -> None:
        from life import family
        coupled, parted = set(), set()
        for a in sim.world.agents:
            was = self._people.get(a.id)
            if was is None:
                # Someone new: born in the last hour, or arrived (the dashboard can add people)
                if a.mother_id or a.father_id:
                    self._born(sim, a, max(now - TICKS_PER_HOUR + 1, now - int(getattr(a, 'ticks_lived', 0))))
                else:
                    self.add(now, 'arrived', f"{a.name} arrived in the village", [a],
                             ref={"kind": "agent", "id": a.id})
                was = dict(self._person_now(a), alive=True)
            if was["alive"] and not a.alive:
                died = getattr(a, 'death_tick', None)
                self._died(sim, a, died if died is not None and now - TICKS_PER_HOUR < died <= now else now)
            elif a.alive:
                partner = a.partner_id
                if partner and partner != was["partner"]:
                    pair = tuple(sorted((a.id, partner)))
                    if pair not in coupled:
                        coupled.add(pair)
                        other = sim._get_agent_by_id(partner)
                        self.add(now, 'coupled', f"{a.name} and {other.name if other else 'someone'} became a couple",
                                 [a, other], ref={"kind": "agent", "id": a.id})
                elif was["partner"] and not partner:
                    other = sim._get_agent_by_id(was["partner"])
                    pair = tuple(sorted((a.id, was["partner"])))
                    if other is not None and other.alive and pair not in parted:
                        parted.add(pair)
                        self.add(now, 'parted', f"{a.name} and {other.name} parted ways", [a, other],
                                 ref={"kind": "agent", "id": a.id})
                if not was["adult"] and family.is_adult(a):
                    self.add(now, 'came_of_age', f"{a.name} came of age", [a], ref={"kind": "agent", "id": a.id})
            self._people[a.id] = self._person_now(a)

    def _died(self, sim, a, now: int) -> None:
        children = [sim._get_agent_by_id(c) for c in getattr(a, 'children_ids', [])]
        living = [c for c in children if c is not None and c.alive]
        # (a death clears the partner, so take the one it had at the last look)
        partner = sim._get_agent_by_id(a.partner_id or self._people.get(a.id, {}).get("partner"))
        partner = partner if partner is not None and partner.alive else None
        left = ([partner.name] if partner else []) + \
               ([f"{len(living)} {'child' if len(living) == 1 else 'children'}"] if living else [])
        text = f"{a.name} died {death_words(a.death_cause)} at {int(a.age)}"
        if left:
            text += f", leaving {_and(left)}"
        violent = a.death_cause not in (None, 'old age')
        self.add(now, 'died', text, [a, partner], ref={"kind": "agent", "id": a.id}, weight=4 if violent else 3)

    def _read_knowhow(self, sim, after: int, fresh) -> None:
        ledger = getattr(sim, 'knowhow', None)
        if ledger is None or not getattr(ledger, 'active', False):
            return
        from world.knowhow import KNOWHOW
        for tick, name, who, how, teacher in _newer(getattr(ledger, 'log', []), after):
            if not fresh(tick):
                continue
            label = KNOWHOW[name].label if name in KNOWHOW else name.replace('_', ' ')
            person = self._name(sim, who)
            ref = {"kind": "knowhow", "id": name}
            first = ledger.firsts.get(name)
            if how == 'insight' and first and first.get('tick') == tick and first.get('agent_id') == who:
                self.add(tick, 'first_knowhow', f"{person[1]} worked out {label}, the first in the world",
                         [person], ref)
            elif how == 'insight':
                self.add(tick, 'insight', f"{person[1]} worked out {label}", [person], ref)
            elif how == 'taught':
                t = self._name(sim, teacher)
                self.add(tick, 'taught', f"{t[1] or 'Someone'} taught {person[1]} {label}", [t, person], ref)
            else:
                self.add(tick, 'watched', f"{person[1]} picked up {label} by watching", [person], ref)
        for lost in getattr(ledger, 'lost', []):
            if fresh(lost.get('tick')):
                self.add(lost['tick'], 'lost', f"The knowledge of {lost.get('label')} was lost: nobody alive knew it",
                         [], {"kind": "knowhow", "id": lost.get('knowhow')})

    def _read_governments(self, sim, after: int, fresh) -> None:
        gm = getattr(sim, 'governance_manager', None)
        if gm is None:
            return
        for gov in sorted(gm.governments.values(), key=lambda g: g.id):
            ref = {"kind": "government", "id": gov.id}
            for tick, kind, d in _newer(getattr(gov, 'history', []), after):
                if not fresh(tick):
                    continue
                n = lambda key: self._name(sim, d.get(key))  # noqa: E731
                law = gm.laws.get(d.get('law')) if d.get('law') else None
                law_ref = {"kind": "law", "id": law.id} if law else ref
                if kind == 'founded':
                    by = n('by')
                    self.add(tick, 'government', f"{by[1] or 'Someone'} founded {gov.name}, {_a(d.get('type'))}", [by], ref)
                elif kind == 'law':
                    by = n('by')
                    self.add(tick, 'law', f"{by[1] or 'Someone'} proposed a law in {gov.name}: "
                                          f"{law.name if law else 'a law'}", [by], law_ref)
                elif kind == 'repealed':
                    self.add(tick, 'repealed', f"{gov.name} repealed {law.name if law else 'a law'}", [], law_ref)
                elif kind == 'election':
                    self.add(tick, 'election', f"{gov.name} opened an election for {d.get('position')}", [], ref)
                elif kind == 'elected':
                    w = n('winner')
                    if d.get('votes'):
                        self.add(tick, 'elected', f"{w[1]} won the election for {d.get('position')} of {gov.name} "
                                                  f"with {d.get('votes')} of the votes, among {d.get('candidates')} "
                                                  f"candidates", [w], ref)
                    else:   # nobody voted: the office went to the only one who stood, or stayed put
                        self.add(tick, 'elected', f"{w[1]} became {d.get('position')} of {gov.name}, "
                                                  f"with nobody voting", [w], ref, weight=1)
                elif kind == 'revolution':
                    leader, old = n('leader'), n('old_leader')
                    text = (f"{leader[1]} overthrew {old[1]} in {gov.name}, with {d.get('supporters')} behind them"
                            if d.get('won') else f"{leader[1]}'s revolt in {gov.name} failed")
                    self.add(tick, 'revolution', text, [leader, old], ref)
                elif kind == 'collapsed':
                    self.add(tick, 'fell', f"{gov.name} fell", [], ref)
                elif kind == 'taxes':
                    by = n('by')
                    self.add(tick, 'taxes', f"{by[1]} collected {d.get('amount')} coins in taxes for {gov.name}", [by], ref)
                elif kind == 'joined':
                    self.add(tick, 'joined_government', '', weight=0)
                else:
                    self.add(tick, kind, '', weight=0)

    def _read_faiths(self, sim, after: int, fresh) -> None:
        religion = getattr(sim, 'religion', None)
        if religion is None:
            return
        for faith in sorted(religion.religions.values(), key=lambda f: f.id):
            ref = {"kind": "faith", "id": faith.id}
            for tick, kind, d in _newer(getattr(faith, 'history', []), after):
                if not fresh(tick):
                    continue
                n = lambda key: self._name(sim, d.get(key))  # noqa: E731
                if kind == 'founded':
                    by = n('by')
                    self.add(tick, 'faith', f"{by[1] or faith.founder_name or 'Someone'} founded a faith: {faith.name}",
                             [by], ref)
                elif kind == 'converted':
                    by, who = n('by'), n('who')
                    self.add(tick, 'converted', f"{by[1]} told {who[1]} of {faith.name}, and they took it up", [by, who], ref)
                elif kind == 'joined':
                    who = n('who')
                    self.add(tick, 'joined_faith', f"{who[1]} joined {faith.name}", [who], ref)
                elif kind == 'lapsed':
                    who = n('who')
                    self.add(tick, 'lapsed', f"{who[1]} drifted away from {faith.name}", [who], ref)
                elif kind == 'temple':
                    by = n('by')
                    self.add(tick, 'temple', f"{by[1]} built a temple for {faith.name}", [by], ref)

    def _read_buildings(self, sim, now: int, quiet: bool) -> None:
        dbs = getattr(sim, 'dynamic_building_system', None)
        if dbs is None:
            return
        for b in sorted(dbs.buildings.values(), key=lambda b: b.id):
            state = 'fallen' if getattr(b, 'collapsed', False) else 'done' if b.is_complete else 'up'
            was = self._buildings.get(b.id)
            repairs = getattr(b, 'repairs', 0)
            if not quiet and repairs > self._repairs.get(b.id, 0):
                self._record(_day(now))["counts"]["mended"] += repairs - self._repairs.get(b.id, 0)
            self._repairs[b.id] = repairs
            if state == was:
                continue
            self._buildings[b.id] = state
            ref = {"kind": "building", "id": b.id}
            builders = [self._name(sim, i) for i in sorted(getattr(b, 'builder_ids', []))]
            if state == 'done':
                tick = getattr(b, 'built_tick', None)
                if quiet and tick is None:
                    continue
                self.add(tick if tick is not None else now, 'built',
                         f"{_and([n for _, n in builders if n]) or 'Someone'} finished {b.name}", builders, ref)
            elif state == 'fallen' and was is not None and not quiet:
                self.add(now, 'collapsed', f"{b.name} fell", [], ref)
            elif state == 'up' and was is None and not quiet:
                self._record(_day(now))["counts"]["started_building"] += 1

    def _read_disasters(self, sim, fresh) -> None:
        disasters = getattr(sim, 'disasters', None)
        for d in list(getattr(disasters, 'disaster_history', []) or []):
            if not fresh(d.tick):
                continue
            kind = d.disaster_type.value.replace('_', ' ')
            severity = getattr(d.severity, 'value', str(d.severity))
            text = f"{_a(severity + ' ' + kind).capitalize()} struck near ({d.location_x:.0f}, {d.location_y:.0f})"
            # Who it killed: deaths of its kind at its tick (each also has its own line)
            toll = [a for a in sim.world.agents if not a.alive and a.death_cause == d.disaster_type.value
                    and getattr(a, 'death_tick', None) == d.tick]
            hurt = [f"{len(toll)} died"] if toll else []
            if d.buildings_destroyed:
                hurt.append(f"{d.buildings_destroyed} buildings destroyed")
            if d.buildings_damaged:
                hurt.append(f"{d.buildings_damaged} damaged")
            if hurt:
                text += ": " + ", ".join(hurt)
            h = self.add(d.tick, 'disaster', text, [], None, weight=5 if toll else 4)
            if h is not None:
                h["toll"] = len(toll)

    def _read_gatherings(self, sim, after: int, fresh) -> None:
        gatherings = getattr(sim, 'gatherings', None)
        for g in _newer(getattr(gatherings, 'history', []) or [], after, lambda g: g.end):
            if not fresh(g.end):
                continue
            came = len(g.attendees)
            host = self._name(sim, g.organizer)
            self.add(g.end, 'gathering', f"{g.organizer_name}'s {g.kind} at {g.place}: {came} came",
                     [host], {"kind": "gathering", "id": g.id}, weight=2 if came >= 5 else 1)

    def _read_celebrations(self, sim, fresh) -> None:
        fun = getattr(sim, 'fun_system', None)
        if fun is None:
            return
        for c in list(fun.active_celebrations.values()) + list(fun.celebration_history[-50:]):
            if c.id in self._celebrations or not fresh(getattr(c, 'start_tick', None)):
                continue
            self._celebrations.add(c.id)
            host = self._name(sim, c.organizer_id)
            why = f" ({c.trigger_event})" if getattr(c, 'trigger_event', None) else ""
            self.add(c.start_tick, 'celebration', f"{host[1] or 'Someone'} threw a celebration{why}", [host])

    def _read_inventions(self, sim, fresh) -> None:
        inventions = getattr(getattr(sim, 'innovation_manager', None), 'innovations', {}) or {}
        new = [i for i in inventions.values() if fresh(getattr(i, 'discovered_tick', None))]
        for inv in sorted(new, key=lambda i: (i.discovered_tick, i.id)):
            tick = inv.discovered_tick
            who = self._name(sim, inv.discoverer_id)
            self.add(tick, 'invention', f"{who[1] or 'Someone'} invented {inv.name}", [who],
                     {"kind": "invention", "id": inv.id})

    def _read_wars(self, sim, now: int, quiet: bool) -> None:
        wars = getattr(getattr(sim, 'warfare_manager', None), 'active_conflicts', {}) or {}
        for war_id in sorted(wars):
            if war_id in self._wars:
                continue
            war = wars[war_id]
            leaders = [self._name(sim, getattr(war, 'leader_a', None)), self._name(sim, getattr(war, 'leader_b', None))]
            title = f"war between {_and([n for _, n in leaders if n]) or 'two sides'}"
            self._wars[war_id] = title
            if not quiet:
                reason = getattr(getattr(war, 'reason', None), 'value', getattr(war, 'reason', None))
                self.add(now, 'war', f"A {title} began" + (f", over {reason}" if reason else ""), leaders)
        for war_id in sorted(set(self._wars) - set(wars)):
            if not quiet:
                self.add(now, 'war_end', f"The {self._wars[war_id]} ended")
            del self._wars[war_id]

    def _read_taxes(self, sim, now: int, fresh, quiet: bool) -> None:
        taxation = getattr(getattr(sim, 'economy', None), 'taxation', None)
        if taxation is None:
            return
        for policy in sorted(taxation.tax_policies.values(), key=lambda p: p.id):
            kind = getattr(policy.tax_type, 'value', str(policy.tax_type)).replace('_', ' ')
            kind = kind[:-4] if kind.endswith(' tax') else kind
            who = self._name(sim, policy.collector_id)
            if fresh(policy.enacted_tick):
                self.add(policy.enacted_tick, 'tax', f"{who[1] or 'A government'} imposed {_a(kind)} tax of "
                                                     f"{round(policy.rate * 100)}%", [who])
            if policy.repealed_tick and fresh(policy.repealed_tick):
                self.add(policy.repealed_tick, 'tax_repealed', f"The {kind} tax was repealed", [who])
        joined = self.__dict__.setdefault('_revolt_sizes', {})
        for revolt in sorted(taxation.revolts.values(), key=lambda r: r.id):
            leader = self._name(sim, revolt.leader_id)
            if fresh(revolt.started_tick):
                why = f" ({revolt.grievance})" if getattr(revolt, 'grievance', None) else ""
                self.add(revolt.started_tick, 'revolt', f"{leader[1] or 'Someone'} started a tax revolt{why}", [leader])
            if revolt.ended_tick and fresh(revolt.ended_tick):
                self.add(revolt.ended_tick, 'revolt_end',
                         f"{leader[1] or 'A'}'s tax revolt {'won' if revolt.succeeded else 'ended without winning'}, "
                         f"{len(revolt.participants)} strong", [leader])
            size = len(revolt.participants)
            if not quiet and size > joined.get(revolt.id, 1):
                self._record(_day(now))["counts"]["joined_revolt"] += size - joined.get(revolt.id, 1)
            joined[revolt.id] = size

    def _read_roles(self, sim, fresh) -> None:
        roles = getattr(getattr(sim, 'role_emergence', None), 'agent_roles', {}) or {}
        for agent_id in sorted(roles):
            for role in roles[agent_id]:
                if role.custom_role_name and fresh(getattr(role, 'started_tick', None)):
                    who = self._name(sim, agent_id)
                    if who[0]:
                        self.add(role.started_tick, 'role', f"{who[1]} came to be known as {role.custom_role_name}",
                                 [who], {"kind": "agent", "id": who[0]})

    def _read_firsts(self, sim, after: int, fresh) -> None:
        chronicle = getattr(sim, 'chronicle', None)
        news = [e for e in _newer(getattr(chronicle, 'entries', []), after, lambda e: e.tick)
                if e.kind == 'first' and fresh(e.tick)]
        if not news:
            return
        names = {a.name: a.id for a in sorted(sim.world.agents, key=lambda a: (a.alive, a.id))}
        for e in news:
            kind = FIRST_OF.get(e.key)
            if kind is not None:
                # Already told in the annals' own words: mark it as the first
                for h in reversed(self._record(_day(e.tick))["happenings"]):
                    if h["kind"] == kind and (not e.agents or any(n == e.agents[0] for _, n in h["people"])):
                        h["first"] = True
                        h["w"] = max(h["w"], 4)
                        break
                continue
            people = [(names[n], n) for n in e.agents if n in names]
            self.add(e.tick, 'first', e.title + (f": {e.text}" if e.text else ""), people, e.ref)

    # -- the end of a day ------------------------------------------------------------

    def _age_now(self, sim) -> Optional[str]:
        ledger = getattr(sim, 'knowhow', None)
        if ledger is None or not getattr(ledger, 'active', False):
            return None
        from world.knowhow import age_of
        return age_of(ledger._known_now())

    def _close_day(self, sim, tick: int) -> None:
        rec = self._record(_day(tick))
        age = self._age_now(sim)
        if age and self._age and age != self._age:
            self.add(tick, 'age', f"The village entered the {age}" if age != "Before tools"
                     else "The village fell back to before tools: what marked its age was lost")
        if age:
            self._age = age
        rec["end"] = village_now(sim, age)
        done = Counter(getattr(sim, 'action_successes', {}))
        today = done - self._actions_at_dawn
        rec["actions"] = dict(today.most_common(8))
        self._actions_at_dawn = done


def village_now(sim, age: Optional[str] = None) -> Dict:
    """The village as it is: people, couples, homes, what is known, the age."""
    alive = [a for a in sim.world.agents if a.alive]
    from life import family
    adults = sum(1 for a in alive if family.is_adult(a))
    couples = len({tuple(sorted((a.id, a.partner_id))) for a in alive if a.partner_id})
    dbs = getattr(sim, 'dynamic_building_system', None)
    standing = sum(1 for b in dbs.buildings.values() if b.is_complete and not getattr(b, 'collapsed', False)) if dbs else 0
    ledger = getattr(sim, 'knowhow', None)
    dawn = ledger is not None and getattr(ledger, 'active', False)
    if dawn and age is None:
        from world.knowhow import age_of
        age = age_of(ledger._known_now())
    gm = getattr(sim, 'governance_manager', None)
    religion = getattr(sim, 'religion', None)
    return {
        "people": len(alive), "adults": adults, "children": len(alive) - adults, "couples": couples,
        "homes": sum(1 for a in alive if getattr(a, 'home_id', None)), "buildings": standing,
        "knows": len(ledger._known_now()) if dawn else None, "age": age,
        "governments": sum(1 for g in gm.governments.values() if getattr(g, 'active', True)) if gm else 0,
        "faiths": sum(1 for f in religion.religions.values() if f.followers) if religion else 0,
        "season": getattr(sim.world.time, 'season', None),
    }


# -- reading ----------------------------------------------------------------------------

def _happening_view(h: Dict) -> Dict:
    return {"tick": h["tick"], "day": _day(h["tick"]), "hour": h["tick"] // TICKS_PER_HOUR % 24, "kind": h["kind"],
            "weight": h["w"], "text": h["text"], "first": bool(h.get("first")),
            "people": [{"id": i, "name": n} for i, n in h["people"]], "ref": h["ref"]}


GROUP_NOUNS = {'coupled': 'couples', 'died': 'deaths', 'government': 'governments founded',
               'faith': 'faiths founded', 'elected': 'elections won', 'first': 'firsts', 'disaster': 'disasters',
               'parted': 'partings', 'revolt': 'revolts', 'tax': 'taxes', 'first_knowhow': 'firsts',
               'collapsed': 'buildings fallen', 'temple': 'temples'}

COUNT_WORDS = {
    'law': ('law proposed', 'laws proposed'), 'joined_revolt': ('joined a tax revolt', 'joined tax revolts'),
    'role': ('new name for what someone does', 'new names for what people do'),
    'came_of_age': ('came of age', 'came of age'),
    'taught': ('lesson', 'lessons'), 'watched': ('thing picked up by watching', 'things picked up by watching'),
    'converted': ('conversion', 'conversions'), 'joined_faith': ('joined a faith', 'joined a faith'),
    'lapsed': ('drifted from a faith', 'drifted from a faith'), 'invention': ('invention', 'inventions'),
    'joined_government': ('became a citizen', 'became citizens'), 'mended': ('repair', 'repairs'),
    'started_building': ('building begun', 'buildings begun'), 'celebration': ('celebration', 'celebrations'),
    'gathering': ('gathering', 'gatherings'), 'insight': ('thing worked out again', 'things worked out again'),
}


def narrate(rec: Dict) -> str:
    """A day in a few plain sentences, from its happenings."""
    by_kind: Dict[str, List[Dict]] = {}
    for h in rec["happenings"]:
        by_kind.setdefault(h["kind"], []).append(h)
    parts = []

    def texts(kind, most=4):
        hs = by_kind.get(kind, [])
        shown = [h["text"] for h in hs[:most]]
        more = len(hs) - len(shown)
        return shown, more

    def group(kind, most=3):
        shown, more = texts(kind, most)
        if shown:
            parts.append("; ".join(shown) + (f"; and {more} more {GROUP_NOUNS.get(kind, 'like it')}" if more > 0 else ""))

    for kind in ('began', 'age', 'war', 'disaster', 'first_knowhow', 'lost', 'government', 'revolution', 'fell',
                 'faith', 'war_end'):
        group(kind)
    born = by_kind.get('born', [])
    if born:
        parts.append(f"{'A child was' if len(born) == 1 else f'{len(born)} children were'} born: "
                     + "; ".join(h["text"].replace(" was born", "") for h in born[:5])
                     + (f"; and {len(born) - 5} more" if len(born) > 5 else ""))
    for kind in ('died', 'coupled', 'parted', 'revolt', 'revolt_end', 'tax', 'elected', 'temple', 'collapsed', 'first'):
        group(kind, 4)
    sentences = [p if p.endswith('.') else p + '.' for p in parts]
    counts = rec["counts"]
    small = []
    for key in ('law', 'taught', 'insight', 'watched', 'invention', 'converted', 'joined_revolt', 'role',
                'gathering', 'celebration', 'mended', 'came_of_age'):
        n = counts.get(key, 0)
        if n:
            one, many = COUNT_WORDS[key]
            small.append(f"{n} {one if n == 1 else many}")
    if small:
        sentences.append("Also: " + ", ".join(small) + ".")
    if not sentences:
        sentences.append("A quiet day.")
    return " ".join(sentences)


def _day_view(rec: Dict, pieced_before: Optional[int], people: Optional[int] = None, full: bool = True) -> Dict:
    happenings = sorted(rec["happenings"], key=lambda h: (h["tick"], -h["w"]))
    weather = rec.get("weather") or {}
    view = {
        "day": rec["day"], "summary": narrate(rec), "end": rec.get("end"), "people": people,
        "counts": {k: v for k, v in rec["counts"].items() if v},
        "weather": max(weather, key=weather.get) if weather else None,
        "actions": rec.get("actions") or {},
        "pieced": pieced_before is not None and rec["day"] < pieced_before,
        "notable": sum(1 for h in happenings if h["w"] >= 3),
    }
    if full:
        view["happenings"] = [_happening_view(h) for h in happenings]
    return view


def _chapter(days: List[Dict], start: int, end: int, people_of: Dict[int, Optional[int]]) -> Dict:
    happenings = [h for rec in days for h in rec["happenings"]]
    # A first counts a little extra; a disaster counts by how many it killed
    top = max(happenings, key=lambda h: (h["w"] + (0.5 if h.get("first") else 0) + h.get("toll", 0) / 100, -h["tick"]),
              default=None)
    struck = {h["tick"] for h in happenings if h["kind"] == 'disaster' and h.get("toll")}
    counts = Counter()
    for rec in days:
        counts.update(rec["counts"])
    counted = [rec for rec in days if people_of.get(rec["day"]) is not None]
    last_end = next((rec["end"] for rec in reversed(days) if rec.get("end")), None)
    highlights = sorted((h for h in happenings if (h["w"] >= 4 or h.get("first"))
                         and not (h["kind"] == 'died' and h["tick"] in struck)),   # told in the disaster's line
                        key=lambda h: (-h["w"], h["tick"]))[:8]
    return {
        "from": start, "to": end,
        "title": top["text"] if top else "Quiet days",
        "born": counts.get('born', 0), "died": counts.get('died', 0), "couples": counts.get('coupled', 0),
        "people_start": people_of[counted[0]["day"]] if counted else None,
        "people_end": people_of[counted[-1]["day"]] if counted else None,
        "age": last_end.get("age") if last_end else None,
        "taught": counts.get('taught', 0), "inventions": counts.get('invention', 0),
        "highlights": [_happening_view(h) for h in sorted(highlights, key=lambda h: h["tick"])],
    }


def houses(sim, limit: int = 8) -> List[Dict]:
    """Families by founder: everyone descended from each of the first people
    (no parents in the village), the living among them and how many generations."""
    by_id = {a.id: a for a in sim.world.agents}
    out = []
    for founder in sim.world.agents:
        if founder.mother_id in by_id or founder.father_id in by_id or not founder.children_ids:
            continue
        seen, frontier, depth = set(), [founder.id], 0
        while frontier:
            nxt = []
            for pid in frontier:
                for c in getattr(by_id.get(pid), 'children_ids', []) or []:
                    if c in by_id and c not in seen:
                        seen.add(c)
                        nxt.append(c)
            if nxt:
                depth += 1
            frontier = nxt
        partner = by_id.get(founder.partner_id) if founder.partner_id else None
        out.append({"id": founder.id, "name": founder.name, "alive": founder.alive,
                    "partner": partner.name if partner else None, "partner_id": partner.id if partner else None,
                    "descendants": len(seen), "living": sum(1 for i in seen if by_id[i].alive),
                    "generations": depth + 1})
    out.sort(key=lambda h: (-h["living"], -h["descendants"], h["name"]))
    return out[:limit]


def lives(sim) -> List[Dict]:
    """People worth remembering, each for a reason taken from the record."""
    agents = list(sim.world.agents)
    alive = [a for a in agents if a.alive]
    dead = [a for a in agents if not a.alive]
    rows = []

    def person(a, why, value=None):
        rows.append({"id": a.id, "name": a.name, "alive": a.alive, "why": why, "value": value})

    if alive:
        a = max(alive, key=lambda a: (a.age, a.id))
        person(a, f"the oldest alive, at {int(a.age)}", int(a.age))
    if dead:
        a = max(dead, key=lambda a: (a.age, a.id))
        person(a, f"the longest life, {int(a.age)} years ({a.death_cause})", int(a.age))
    with_children = [a for a in agents if a.children_ids]
    if with_children:
        a = max(with_children, key=lambda a: (len(a.children_ids), a.id))
        person(a, f"the most children: {len(a.children_ids)}", len(a.children_ids))
    ledger = getattr(sim, 'knowhow', None)
    if ledger is not None and getattr(ledger, 'active', False):
        teachers = Counter(t for _, _, _, how, t in getattr(ledger, 'log', []) if how == 'taught' and t)
        if teachers:
            tid, n = max(teachers.items(), key=lambda kv: (kv[1], kv[0]))
            a = sim._get_agent_by_id(tid)
            if a is not None:
                person(a, f"taught the most: {n} lessons", n)
        firsts = Counter(f.get('agent_id') for f in ledger.firsts.values() if f.get('agent_id'))
        if firsts:
            fid, n = max(firsts.items(), key=lambda kv: (kv[1], kv[0]))
            a = sim._get_agent_by_id(fid)
            if a is not None:
                from world.knowhow import KNOWHOW
                what = [KNOWHOW[k].label for k, f in ledger.firsts.items() if f.get('agent_id') == fid and k in KNOWHOW]
                person(a, f"worked out {_and(what[:4])}{' and more' if len(what) > 4 else ''} before anyone", n)
    gm = getattr(sim, 'governance_manager', None)
    for gov in sorted(getattr(gm, 'governments', {}).values(), key=lambda g: (g.founded_tick or 0, g.id))[:1]:
        founded = next((d for _, kind, d in getattr(gov, 'history', []) if kind == 'founded'), None)
        a = sim._get_agent_by_id(founded.get('by')) if founded else None
        if a is not None:
            person(a, f"founded the first government, {gov.name}")
    religion = getattr(sim, 'religion', None)
    for faith in sorted(getattr(religion, 'religions', {}).values(), key=lambda f: (f.founded_tick, f.id))[:1]:
        a = sim._get_agent_by_id(faith.founder_id) if faith.founder_id else None
        if a is not None:
            person(a, f"founded the first faith, {faith.name}")
    born = [a for a in agents if a.mother_id]
    if born:
        # world.agents keeps the order people came into the world
        person(born[0], "the first child born in the village")
    return rows


LIFE_KINDS = {'born', 'died', 'coupled', 'parted', 'came_of_age', 'arrived', 'first_knowhow', 'insight', 'taught',
              'watched', 'government', 'law', 'elected', 'revolution', 'faith', 'converted', 'joined_faith', 'lapsed',
              'temple', 'built', 'gathering', 'celebration', 'invention', 'revolt', 'revolt_end', 'tax', 'role',
              'first', 'war'}


def life_of(sim, agent_id: str, limit: int = 60) -> List[Dict]:
    """One person's life from the annals, oldest first: what they were part of."""
    annals = getattr(sim, 'annals', None)
    if annals is None:
        return []
    rows = []
    for day in sorted(annals.days):
        for h in annals.days[day]["happenings"]:
            if h["kind"] in LIFE_KINDS and any(pid == agent_id for pid, _ in h["people"]):
                rows.append(h)
    rows.sort(key=lambda h: h["tick"])
    if len(rows) > limit:
        # Keep what matters most, then the latest
        keep = sorted(rows, key=lambda h: (-h["w"], -h["tick"]))[:limit]
        rows = sorted(keep, key=lambda h: h["tick"])
    return [_happening_view(h) for h in rows]


def annals_view(sim, since_day: Optional[int] = None, before_day: Optional[int] = None, days: int = 10) -> Dict:
    """GET /annals: the record for the Chronicle tab. The most recent `days`
    days in full (or those before `before_day`), every day's population,
    chapters of DAYS_PER_CHAPTER days, and, with since_day, what happened
    since then."""
    annals = getattr(sim, 'annals', None)
    now = sim.world.time.current_tick
    today = _day(now)
    records = [annals.days[d] for d in sorted(annals.days)] if annals else []
    pieced_before = _day(annals.started_tick) if annals and annals.started_tick and annals.started_tick >= TICKS_PER_DAY else None

    # People at the end of each day: the annals' own count, else the daily
    # count the engine keeps (taken as each day begins, so it is the day before's)
    kept = {e.get('day', 0) - 1: e.get('alive') for e in getattr(sim, 'population_history', []) or []}
    people_of = {r["day"]: r["end"]["people"] if r.get("end") else kept.get(r["day"]) if r["day"] < today else None
                 for r in records}
    population = [{"day": r["day"], "people": people_of[r["day"]],
                   "born": r["counts"].get('born', 0), "died": r["counts"].get('died', 0)} for r in records]
    if not records or records[-1].get("end") is None:
        # today is still going: count who's alive now
        alive = sum(1 for a in sim.world.agents if a.alive)
        if population and population[-1]["day"] == today:
            population[-1]["people"] = alive
        else:
            population.append({"day": today, "people": alive, "born": 0, "died": 0})

    chapters = []
    for start in range(1, today + 1, DAYS_PER_CHAPTER):
        end = min(start + DAYS_PER_CHAPTER - 1, today)
        inside = [r for r in records if start <= r["day"] <= end]
        if inside:
            chapters.append(_chapter(inside, start, end, people_of))

    shown = [r for r in records if before_day is None or r["day"] < before_day]
    shown = shown[-max(1, min(days, 60)):]
    out = {
        "tick": now, "today": today,
        "began": {"tick": annals.started_tick if annals else None, "pieced_before": pieced_before},
        "population": population,
        "chapters": chapters,
        "days": [_day_view(r, pieced_before, people_of.get(r["day"])) for r in reversed(shown)],
        "earliest_day": records[0]["day"] if records else None,
        "now": village_now(sim),
        "houses": houses(sim),
        "lives": lives(sim),
    }
    if since_day is not None:
        out["since"] = since_view(records, since_day, pieced_before)
    return out


def since_view(records: List[Dict], since_day: int, pieced_before: Optional[int] = None) -> Dict:
    """What happened from since_day on, for someone coming back."""
    inside = [r for r in records if r["day"] >= since_day]
    counts = Counter()
    for r in inside:
        counts.update(r["counts"])
    happenings = [h for r in inside for h in r["happenings"]]
    notable = sorted((h for h in happenings if h["w"] >= 3 or h.get("first")), key=lambda h: (-h["w"], h["tick"]))[:40]
    first = next((r["end"] for r in inside if r.get("end")), None)
    last = next((r["end"] for r in reversed(inside) if r.get("end")), None)
    return {
        "from_day": since_day, "days": len(inside),
        "born": counts.get('born', 0), "died": counts.get('died', 0), "couples": counts.get('coupled', 0),
        "parted": counts.get('parted', 0), "taught": counts.get('taught', 0),
        "inventions": counts.get('invention', 0), "firsts": sum(1 for h in happenings if h["kind"] in ('first', 'first_knowhow') or h.get("first")),
        "people_then": first["people"] if first else None, "people_now": last["people"] if last else None,
        "notable": [_happening_view(h) for h in sorted(notable, key=lambda h: h["tick"])],
    }
