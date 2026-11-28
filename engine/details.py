"""
Everything the dashboard can open (GET /details/{kind}/{id}): a person, a
government, a law, a faith, a piece of know-how, an invention, a gathering,
a building or an event, told in full, with links to everything it touches.

Every kind comes back in one shape, so one panel shows them all:

    {kind, id, icon, title, subtitle, summary,
     facts:    [{label, value, link?}],
     sections: [{title, text?, items?: [{text, note?, link?}],
                 timeline?: [{tick, when, text, links: [link]}]}]}

    link = {kind, id, label}

Read-only. Names are looked up when read, so they're current; someone who
has died is still named (and linked: their story stays readable).
"""

from typing import Callable, Dict, List, Optional

TICKS_PER_DAY = 144


# -- small helpers -----------------------------------------------------------------

def when(tick: Optional[int]) -> str:
    if tick is None:
        return "an unknown time"
    return f"day {tick // TICKS_PER_DAY + 1}, {tick // 6 % 24:02d}:00"


def day(tick: Optional[int]) -> str:
    return "an unknown day" if tick is None else f"day {tick // TICKS_PER_DAY + 1}"


def link(kind: str, item_id, label: str) -> Dict:
    return {"kind": kind, "id": str(item_id), "label": label}


class _Names:
    def __init__(self, sim):
        self.by_id = {a.id: a for a in sim.world.agents}

    def name(self, agent_id) -> str:
        agent = self.by_id.get(agent_id)
        return agent.name if agent is not None else "someone"

    def person(self, agent_id) -> Optional[Dict]:
        agent = self.by_id.get(agent_id)
        if agent is None:
            return None
        return link("agent", agent.id, agent.name + ("" if agent.alive else " †"))

    def people(self, ids, note: Callable = None) -> List[Dict]:
        rows = []
        for agent_id in sorted(ids, key=lambda i: self.name(i)):
            p = self.person(agent_id)
            if p is not None:
                rows.append({"text": p["label"], "link": p, **({"note": note(agent_id)} if note else {})})
        return rows


def _a(word: str) -> str:
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word


def _pct(x) -> str:
    return f"{round(100 * float(x))}%"


def _fact(label, value, link_to=None) -> Dict:
    fact = {"label": label, "value": str(value)}
    if link_to:
        fact["link"] = link_to
    return fact


# -- people ------------------------------------------------------------------------

def agent(sim, agent_id: str) -> Optional[Dict]:
    names = _Names(sim)
    a = names.by_id.get(agent_id)
    if a is None:
        return None
    from agents.profiles import agent_story
    from world.knowhow import KNOWHOW
    story = agent_story(sim, a)
    gov = sim.governance_manager.get_agent_government(a.id)
    faith = sim.religion.get_agent_religion(a.id)
    job = getattr(getattr(a, 'work_life', None), 'job', None)
    from life import homes
    home = homes.home_of(sim.dynamic_building_system, a)

    if a.alive:
        summary = f"{a.name} is {_doing(story['doing'])}."
        if story['set_out']:
            s = story['set_out']
            summary += f" They set out {s['hours_ago']} hours ago to {s['action'].replace('_', ' ')}, {s['distance']} tiles to go."
    else:
        from engine.annals import death_words
        summary = f"{a.name} died {death_words(getattr(a, 'death_cause', None))} at {a.age}."

    facts = [_fact("Age", f"{a.age}, {a.life_stage}"), _fact("Generation", getattr(a, 'generation', 1))]
    if a.alive:
        facts += [_fact("Health", f"{a.health:.0f}"), _fact("Energy", f"{a.energy:.0f}")]
    if story['partner']:
        facts.append(_fact("Partner", story['partner'], names.person(a.partner_id)))
    if home is not None:
        facts.append(_fact("Home", getattr(home, 'name', 'a home'), link("building", home.id, home.name)))
    if faith is not None:
        facts.append(_fact("Faith", faith.name, link("faith", faith.id, faith.name)))
    if gov is not None:
        role = "leader" if gov.leader_id == a.id else "council" if a.id in gov.council_ids else "citizen"
        facts.append(_fact("Government", f"{gov.name} ({role})", link("government", gov.id, gov.name)))
    if job:
        from agents.daily_life import JOBS
        facts.append(_fact("Work", JOBS[job].title if job in JOBS else job))
    facts.append(_fact("Wealth", f"{a.wealth:.0f}"))

    sections = []
    family = [{"text": names.name(p), "note": "parent", "link": names.person(p)}
              for p in (a.mother_id, a.father_id) if p and names.person(p)]
    family += [{"text": names.name(c), "note": "child", "link": names.person(c)}
               for c in a.children_ids if names.person(c)]
    if family:
        sections.append({"title": "Family", "items": family})

    if a.alive:
        needs = sorted(a.needs.needs.items(), key=lambda kv: -kv[1].get_urgency())[:6]
        sections.append({"title": "What presses on them now", "items": [
            {"text": n.value.replace('_', ' '), "note": f"{_pct(need.level)} unmet"} for n, need in needs]})

    traits = {t: v for t, v in vars(a.personality).items() if isinstance(v, float)}
    high = sorted(traits.items(), key=lambda kv: -kv[1])[:3]
    low = sorted(traits.items(), key=lambda kv: kv[1])[:2]
    sections.append({"title": "Who they are", "items":
                     [{"text": f"very {t.replace('_', ' ')}", "note": _pct(v)} for t, v in high]
                     + [{"text": f"little {t.replace('_', ' ')}", "note": _pct(v)} for t, v in low]})

    known = getattr(a, 'knowhow', None)
    if known is not None:
        sections.append({"title": "Knows how to", "items": [
            {"text": KNOWHOW[k].label, "link": link("knowhow", k, KNOWHOW[k].label)} for k in sorted(known)]
            or [{"text": "only what comes with being human"}]})

    rels = sim.relationship_manager.get_agent_relationships(a.id)
    rels = sorted(rels, key=lambda r: -r.strength)[:12]
    if rels:
        rows = []
        for r in rels:
            other = r.agent_b if r.agent_a == a.id else r.agent_a
            p = names.person(other)
            if p:
                rows.append({"text": p["label"], "link": p,
                             "note": f"{r.relationship_type.value}, {_pct(r.strength)}"})
        sections.append({"title": "People in their life", "items": rows})

    carrying = {k: v for k, v in sorted(a.inventory.items.items()) if v}
    if carrying:
        sections.append({"title": "Carrying", "items": [{"text": k.replace('_', ' '), "note": str(v)}
                                                        for k, v in carrying.items()]})
    skills = sorted(((n, s.level) for n, s in a.skills.skills.items()), key=lambda kv: -kv[1])[:6]
    if skills:
        sections.append({"title": "Skills", "items": [{"text": n.replace('_', ' '), "note": f"{lvl:.2f}"}
                                                      for n, lvl in skills]})
    if story['memories']:
        sections.append({"title": "Remembers", "items": [{"text": m['text'], "note": f"day {m['day']}"}
                                                         for m in story['memories']]})
    # Their life from the annals (engine/annals.py): born, came of age, paired up,
    # children, what they learned and taught, what they founded, how they died
    from engine.annals import life_of
    life = life_of(sim, a.id)
    if life:
        sections.append({"title": "Their life", "timeline": [_annal_line(names, h) for h in life]})
    events = sim.event_logger.get_events_involving_agent(a.id, 25)
    if events:
        sections.append({"title": "Lately", "timeline": [_event_line(names, e) for e in reversed(events)]})

    return {"kind": "agent", "id": a.id, "icon": "🧑", "title": a.name,
            "subtitle": f"{a.age}, {a.life_stage}, generation {getattr(a, 'generation', 1)}"
                        + ("" if a.alive else " · died"),
            "summary": summary, "facts": facts, "sections": sections}


def _annal_line(names, h) -> Dict:
    links = [p for p in (names.person(x["id"]) for x in h["people"]) if p]
    ref = h.get("ref")
    if ref and ref.get("kind") != "agent":
        links.append(link(ref["kind"], ref["id"], {"government": "the government", "faith": "the faith",
                                                    "law": "the law", "knowhow": "the know-how",
                                                    "invention": "the invention", "gathering": "the gathering",
                                                    "building": "the building"}.get(ref["kind"], "open")))
    return {"tick": h["tick"], "when": when(h["tick"]), "text": h["text"], "links": links}


# "socialize" -> "socializing", "gather_food" -> "gathering food" (it said "Laura is socialize")
_ING = {'sit': 'sitting', 'dig': 'digging', 'chat': 'chatting', 'plan': 'planning', 'run': 'running',
        'swim': 'swimming', 'set': 'setting', 'shop': 'shopping', 'be': 'being', 'see': 'seeing', 'flee': 'fleeing',
        'lie': 'lying', 'die': 'dying', 'tie': 'tying', 'begin': 'beginning', 'stop': 'stopping'}


def _doing(action: Optional[str]) -> str:
    if not action:
        return "doing nothing in particular yet"
    words = str(action).split('_')
    verb = words[0]
    if verb in _ING:
        ing = _ING[verb]
    elif verb.endswith('ie'):
        ing = verb[:-2] + 'ying'
    elif verb.endswith('e') and not verb.endswith('ee'):
        ing = verb[:-1] + 'ing'
    else:
        ing = verb + 'ing'
    return " ".join([ing] + words[1:])


def _event_line(names, e) -> Dict:
    links = [p for p in (names.person(i) for i in e.agents_involved) if p]
    return {"tick": e.tick, "when": when(e.tick), "text": e.title + (f": {e.description}" if e.description else ""),
            "links": links}


# -- governments and laws ----------------------------------------------------------------

HOW_RUN = {
    "strongman": "One person rules. Only the leader makes laws; there are no elections.",
    "oligarchy": "A few rule. The leader and the council make the laws; there are no elections.",
    "democracy": "Many rule. Anyone with enough standing may propose a law, and the leader is "
                 "chosen by election every 3 days (the vote stays open half a day).",
    "council": "A council rules with the leader. Leader and council members make the laws.",
    "theocracy": "Faith rules. The leader and council make the laws.",
    "anarchy": "Nobody rules any more: it has fallen.",
}
COMMON_RULES = ("Citizens vote on each law; once at least half of them (and at least two) have voted and "
                "more are against than for, it is repealed. Approval is how much the laws are supported, "
                "on average; low approval makes the government unstable, and it falls if stability runs out. "
                "A tax law lets the leader collect 5% of each citizen's wealth.")


def government(sim, gov_id: str) -> Optional[Dict]:
    gm = sim.governance_manager
    g = gm.governments.get(gov_id)
    if g is None:
        return None
    names = _Names(sim)
    kind = g.government_type.value
    laws = [gm.laws[l] for l in g.laws if l in gm.laws]
    in_force = [l for l in laws if l.active]
    founded = getattr(g, 'founded_tick', None)
    founder = next((d.get('by') for _, k, d in getattr(g, 'history', []) if k == 'founded'), g.leader_id)

    facts = [_fact("Form", kind)]
    if g.leader_id:
        facts.append(_fact("Leader", names.name(g.leader_id), names.person(g.leader_id)))
    if founded is not None:
        facts.append(_fact("Founded", f"{day(founded)} by {names.name(founder)}", names.person(founder)))
    facts += [_fact("Citizens", len(g.citizens)), _fact("Laws in force", len(in_force)),
              _fact("Approval", _pct(g.approval_rating)), _fact("Stability", _pct(g.stability)),
              _fact("Treasury", f"{g.treasury:.0f} coins")]
    taxing = [l for l in in_force if getattr(l, 'tax_policy_id', None)]
    if taxing:
        facts.append(_fact("Tax", "5% of each citizen's wealth, collected by the leader"))

    def role(agent_id):
        r = "leader" if agent_id == g.leader_id else "council" if agent_id in g.council_ids else "citizen"
        return f"{r}, standing {gm.political_power.get(agent_id, 0.0):.2f}"

    sections = [{"title": "How it's run", "text": HOW_RUN.get(kind, "") + " " + COMMON_RULES},
                {"title": f"Citizens ({len(g.citizens)})", "items": names.people(g.citizens, role)}]
    if laws:
        sections.append({"title": f"Laws ({len(in_force)} in force)", "items": [
            {"text": l.name, "link": link("law", l.id, l.name),
             "note": ("in force" if l.active else "repealed") + f" · {len(l.supporters)} for, "
                     f"{len(l.opposers)} against · broken {l.times_broken}×"} for l in laws]})
    elections = [e for e in gm.elections.values() if e.government_id == g.id]
    if elections:
        rows = []
        for e in sorted(elections, key=lambda e: e.ends_tick, reverse=True)[:10]:
            ranked = sorted(e.candidates.items(), key=lambda kv: -kv[1])
            field_text = ", ".join(f"{names.name(c)} {v}" for c, v in ranked) or "no candidates"
            status = (f"{names.name(e.winner)} won" if e.winner else "nobody stood") if e.complete \
                else f"open until {when(e.ends_tick)}"
            rows.append({"text": f"{e.position.title()}: {status}", "note": f"votes: {field_text}",
                         "link": names.person(e.winner) if e.winner else None})
        sections.append({"title": "Elections", "items": rows})
    timeline = [_gov_line(names, gm, t, k, d) for t, k, d in reversed(getattr(g, 'history', []))]
    sections.append({"title": "What has happened in it", "timeline": timeline} if timeline else
                    {"title": "What has happened in it", "text": "This government was founded before "
                     "governments kept a history; what happens from now on is recorded here."})

    status = "" if g.active else " (fallen)"
    return {"kind": "government", "id": g.id, "icon": "🏛️", "title": g.name + status,
            "subtitle": _a(kind).capitalize() + (f" founded on {day(founded)} by {names.name(founder)}" if founded is not None else ""),
            "summary": f"Led by {names.name(g.leader_id)} with {len(g.citizens)} citizens and "
                       f"{len(in_force)} law{'s' if len(in_force) != 1 else ''} in force.",
            "facts": facts, "sections": sections}


def government_cards(sim) -> List[Dict]:
    """What the Politics tab lists for each government, standing or fallen:
    enough to see at a glance how it's run, with ids to open the rest."""
    gm = sim.governance_manager
    names = _Names(sim)
    cards = []
    for g in gm.governments.values():
        kind = g.government_type.value
        laws = [gm.laws[l] for l in g.laws if l in gm.laws]
        founded = getattr(g, 'founded_tick', None)
        history = getattr(g, 'history', [])
        open_elections = [e for e in gm.elections.values() if e.government_id == g.id and not e.complete]
        cards.append({
            "id": g.id, "name": g.name, "type": kind, "active": g.active,
            "leader": names.name(g.leader_id) if g.leader_id else None, "leader_id": g.leader_id,
            "council": [names.person(c) for c in sorted(g.council_ids) if names.person(c)],
            "citizens": len(g.citizens), "approval": round(g.approval_rating, 2),
            "stability": round(g.stability, 2), "treasury": round(g.treasury, 1),
            "founded_day": founded // TICKS_PER_DAY + 1 if founded is not None else None,
            "how_run": HOW_RUN.get(kind, ""),
            "laws": [{"id": l.id, "name": l.name, "active": l.active, "for": len(l.supporters),
                      "against": len(l.opposers), "broken": l.times_broken} for l in laws],
            "elections_open": [{"position": e.position, "closes": when(e.ends_tick),
                                "candidates": [names.person(c) for c in sorted(e.candidates) if names.person(c)]}
                               for e in open_elections],
            "recent": [_gov_line(names, gm, t, k, d) for t, k, d in list(reversed(history))[:4]],
        })
    cards.sort(key=lambda c: (not c["active"], -(c["citizens"])))
    return cards


def _gov_line(names, gm, tick, kind, d) -> Dict:
    p = names.person
    law = gm.laws.get(d.get('law')) if d.get('law') else None
    law_link = link("law", law.id, law.name) if law else None
    texts = {
        'founded': (f"{names.name(d.get('by'))} founded it as {_a(str(d.get('type')))}", [p(d.get('by'))]),
        'joined': (f"{names.name(d.get('who'))} became a citizen", [p(d.get('who'))]),
        'law': (f"{names.name(d.get('by'))} proposed a law: {law.name if law else 'a law'}", [p(d.get('by')), law_link]),
        'repealed': (f"{law.name if law else 'A law'} was repealed: {d.get('against')} against, {d.get('support')} for",
                     [law_link]),
        'election': (f"An election for {d.get('position')} opened, closing {when(d.get('closes'))}", []),
        'candidate': (f"{names.name(d.get('who'))} stood for election", [p(d.get('who'))]),
        'elected': (f"{names.name(d.get('winner'))} won the election for {d.get('position')} "
                    f"with {d.get('votes')} votes among {d.get('candidates')} candidates", [p(d.get('winner'))]),
        'taxes': (f"{names.name(d.get('by'))} collected {d.get('amount')} coins in taxes", [p(d.get('by'))]),
        'revolution': ((f"{names.name(d.get('leader'))} overthrew {names.name(d.get('old_leader'))} with "
                        f"{d.get('supporters')} supporters") if d.get('won') else
                       f"{names.name(d.get('leader'))}'s revolt with {d.get('supporters')} supporters failed",
                       [p(d.get('leader'))]),
        'collapsed': (f"It fell: approval had sunk to {_pct(d.get('approval', 0))}", []),
    }
    text, links = texts.get(kind, (kind, []))
    return {"tick": tick, "when": when(tick), "text": text, "links": [l for l in links if l]}


def law(sim, law_id: str) -> Optional[Dict]:
    gm = sim.governance_manager
    l = gm.laws.get(law_id)
    if l is None:
        return None
    names = _Names(sim)
    gov = gm.governments.get(getattr(l, 'government_id', None)) or \
        next((g for g in gm.governments.values() if l.id in g.laws), None)
    facts = []
    if gov is not None:
        facts.append(_fact("Government", gov.name, link("government", gov.id, gov.name)))
    facts.append(_fact("Proposed by", names.name(l.created_by), names.person(l.created_by)))
    if getattr(l, 'proposed_tick', None) is not None:
        facts.append(_fact("Proposed", when(l.proposed_tick)))
    if l.prohibition:
        facts.append(_fact("Forbids", l.prohibition.replace('_', ' ')))
    if l.requirement:
        facts.append(_fact("Requires", l.requirement.replace('_', ' ')))
    facts += [_fact("Punishment", l.punishment.replace('_', ' ')),
              _fact("Status", "in force" if l.active else
                    f"repealed on {day(l.repealed_tick)}" if getattr(l, 'repealed_tick', None) is not None else "repealed"),
              _fact("Support", f"{len(l.supporters)} for, {len(l.opposers)} against ({_pct(l.get_support_ratio())})"),
              _fact("Broken", f"{l.times_broken} times"), _fact("Enforced", f"{l.times_enforced} times")]
    votes = getattr(l, 'votes', {}) or {}
    rows = []
    for voter in sorted(set(votes) | l.supporters | l.opposers, key=names.name):
        support, tick = votes.get(voter, (voter in l.supporters, None))
        p = names.person(voter)
        if p:
            rows.append({"text": p["label"], "link": p,
                         "note": ("for" if support else "against") + (f", {day(tick)}" if tick is not None else "")})
    sections = [{"title": "What it says", "text": l.description},
                {"title": "How it can end", "text": "Once at least half of the citizens (and at least two) have "
                 "voted and more are against than for, it is repealed."},
                {"title": f"Votes ({len(rows)})", "items": rows or [{"text": "nobody has voted yet"}]}]
    return {"kind": "law", "id": l.id, "icon": "📜", "title": l.name,
            "subtitle": f"A law of {gov.name}" if gov else "A law", "summary": l.description,
            "facts": facts, "sections": sections}


# -- faiths ------------------------------------------------------------------------

def faith(sim, faith_id: str) -> Optional[Dict]:
    rm = sim.religion
    r = rm.religions.get(faith_id)
    if r is None:
        return None
    names = _Names(sim)
    prophet = r.founder_id
    facts = [_fact("Kind", r.religion_type.value.replace('_', ' ')),
             _fact("Prophet", r.founder_name or names.name(prophet), names.person(prophet)),
             _fact("Founded", when(r.founded_tick)), _fact("Followers", len(r.followers)),
             _fact("Priests", len(r.priests)), _fact("Temples", len(r.temples))]
    sections = []
    if r.core_beliefs:
        sections.append({"title": "What they believe", "items": [{"text": b} for b in r.core_beliefs]})
    if r.moral_code:
        sections.append({"title": "How they should live", "items": [{"text": m} for m in r.moral_code]})
    deities = [rm.deities[d] for d in r.deities if d in rm.deities]
    if deities:
        sections.append({"title": "What they worship", "items": [
            {"text": d.name, "note": f"{d.domain.value.replace('_', ' ')}, "
                                     f"{'kind' if d.benevolent >= 0.5 else 'wrathful'}"} for d in deities]})
    if r.regular_rituals or r.holy_days:
        sections.append({"title": "Rituals and holy days", "items":
                         [{"text": rt.value.replace('_', ' '), "note": "ritual"} for rt in r.regular_rituals]
                         + [{"text": h, "note": "holy day"} for h in r.holy_days]})
    if r.sacred_texts:
        sections.append({"title": "Sacred texts", "items": [{"text": t} for t in r.sacred_texts]})
    sections.append({"title": f"Followers ({len(r.followers)})", "items":
                     names.people(r.followers, lambda i: "priest" if i in r.priests else "follower")
                     or [{"text": "nobody holds this faith now"}]})
    temples = [rm.temples[t] for t in r.temples if t in rm.temples]
    if temples:
        sections.append({"title": "Temples", "items": [
            {"text": t.name, "note": f"built {day(t.built_at)} by {names.name(t.builder_id)}, "
                                     f"at ({t.location[0]:.0f}, {t.location[1]:.0f})"} for t in temples]})
    timeline = [_faith_line(names, t, k, d) for t, k, d in reversed(getattr(r, 'history', []))]
    if timeline:
        sections.append({"title": "What has happened in it", "timeline": timeline})
    return {"kind": "faith", "id": r.id, "icon": "🙏", "title": r.name,
            "subtitle": f"Founded by {r.founder_name or names.name(prophet)} on {day(r.founded_tick)}",
            "summary": f"{len(r.followers)} follower{'s' if len(r.followers) != 1 else ''}. "
                       + (r.core_beliefs[0] if r.core_beliefs else ""),
            "facts": facts, "sections": sections}


def _faith_line(names, tick, kind, d) -> Dict:
    p = names.person
    texts = {
        'founded': (f"{names.name(d.get('by'))} founded it", [p(d.get('by'))]),
        'converted': (f"{names.name(d.get('by'))} told {names.name(d.get('who'))} of it, and they took it up",
                      [p(d.get('by')), p(d.get('who'))]),
        'joined': (f"{names.name(d.get('who'))} joined", [p(d.get('who'))]),
        'lapsed': (f"{names.name(d.get('who'))} drifted away (no practice for days)", [p(d.get('who'))]),
        'temple': (f"{names.name(d.get('by'))} built a temple", [p(d.get('by'))]),
    }
    text, links = texts.get(kind, (kind, []))
    return {"tick": tick, "when": when(tick), "text": text, "links": [l for l in links if l]}


# -- know-how and inventions ------------------------------------------------------------

HOW_WORDS = {'insight': 'worked it out', 'watched': 'picked it up watching', 'taught': 'was taught'}


def knowhow(sim, name: str) -> Optional[Dict]:
    from world.knowhow import KNOWHOW, NEEDED_FOR, knows
    k = KNOWHOW.get(name)
    if k is None:
        return None
    ledger = sim.knowhow
    names = _Names(sim)
    first = ledger.firsts.get(name)
    alive = [a for a in sim.world.agents if a.alive]
    knowers = [a.id for a in alive if knows(a, name)] if ledger.active else [a.id for a in alive]
    needs = [KNOWHOW[n] for n in k.needs]
    leads = [o for o in KNOWHOW.values() if name in o.needs]
    lets = [a.replace('_', ' ') for a in k.unlocks]
    facts = [_fact("Humans first", k.humans)]
    if first:
        facts += [_fact("First here", f"{first['who']}, {day(first['tick'])}, generation {first['generation']}",
                        names.person(first['agent_id'])),
                  _fact("How", HOW_WORDS.get(first['how'], first['how']))]
    facts.append(_fact("Know it now", f"{len(knowers)} of {len(alive)}"))
    sections = [{"title": "What it lets people do", "text": (", ".join(lets) if lets else
                 "Nothing on its own; it opens the way to what follows.")
                 + f" Doing {', '.join(s.replace('_', ' ') for s in k.sparks)} may give someone the idea;"
                   " tinkering (experiment) may too, once its groundwork is known."}]
    if needs:
        sections.append({"title": "Builds on", "items": [{"text": n.label, "link": link("knowhow", n.name, n.label)}
                                                          for n in needs]})
    if leads:
        sections.append({"title": "Opens the way to", "items": [{"text": o.label, "link": link("knowhow", o.name, o.label)}
                                                                 for o in leads]})
    sections.append({"title": f"Who knows it now ({len(knowers)})",
                     "items": names.people(knowers) or [{"text": "nobody alive"}]})
    log = [entry for entry in getattr(ledger, 'log', []) if entry[1] == name]
    lines = []
    for tick, _, who, how, teacher in log:
        if how == 'taught' and teacher:
            text, links = f"{names.name(teacher)} taught {names.name(who)}", [names.person(teacher), names.person(who)]
        else:
            text, links = f"{names.name(who)} {HOW_WORDS.get(how, how)}", [names.person(who)]
        lines.append({"tick": tick, "when": when(tick), "text": text, "links": [l for l in links if l]})
    for lost in ledger.lost:
        if lost['knowhow'] == name:
            lines.append({"tick": lost['tick'], "when": when(lost['tick']),
                          "text": "Lost: nobody alive knew it any more", "links": []})
    lines.sort(key=lambda x: -x['tick'])
    if lines:
        sections.append({"title": "How it spread", "timeline": lines[:80]})
    elif first:
        sections.append({"title": "How it spread", "text": "This world began before who learned what was "
                         "written down; everyone who learns it from now on is recorded here."})
    if not ledger.active:
        subtitle = "Known to everyone in a settlers' world"
    elif first:
        subtitle = f"First worked out on {day(first['tick'])} by {first['who']}"
    else:
        subtitle = "Not worked out yet in this world"
    return {"kind": "knowhow", "id": name, "icon": "💡", "title": k.label[:1].upper() + k.label[1:],
            "subtitle": subtitle, "summary": f"Humans first did this {k.humans}.", "facts": facts,
            "sections": sections}


def invention(sim, inv_id: str) -> Optional[Dict]:
    im = sim.innovation_manager
    inv = im.innovations.get(inv_id)
    if inv is None:
        return None
    names = _Names(sim)
    tick = getattr(inv, 'discovered_tick', None)
    facts = [_fact("Kind", inv.discovery_type.value.replace('_', ' ')),
             _fact("Inventor", names.name(inv.discoverer_id), names.person(inv.discoverer_id)),
             _fact("Made", when(tick) if tick is not None else "before the world kept dates"),
             _fact("Known by", len(inv.known_by)), _fact("Used", f"{inv.times_used} times"),
             _fact("Works", _pct(inv.success_rate) + " of the time")]
    sections = [{"title": "What it is", "text": " ".join(x for x in (inv.description, inv.effect_description) if x)}]
    if inv.requires_items or inv.produces_items or inv.applies_to_actions:
        sections.append({"title": "In use", "items":
                         [{"text": i.replace('_', ' '), "note": "needs"} for i in inv.requires_items]
                         + [{"text": i.replace('_', ' '), "note": "makes"} for i in inv.produces_items]
                         + [{"text": i.replace('_', ' '), "note": "helps with"} for i in inv.applies_to_actions]})
    sections.append({"title": f"Who knows it ({len(inv.known_by)})", "items": names.people(inv.known_by)})
    taught = getattr(inv, 'taught', [])
    if taught:
        sections.append({"title": "Who taught whom", "timeline": [
            {"tick": t, "when": when(t), "text": f"{names.name(a)} taught {names.name(b)}",
             "links": [x for x in (names.person(a), names.person(b)) if x]} for t, a, b in reversed(taught)]})
    return {"kind": "invention", "id": inv.id, "icon": "🔧", "title": inv.name,
            "subtitle": f"Made by {names.name(inv.discoverer_id)}" + (f" on {day(tick)}" if tick is not None else ""),
            "summary": inv.effect_description or inv.description, "facts": facts, "sections": sections}


# -- village life ------------------------------------------------------------------

def gathering(sim, gathering_id: str) -> Optional[Dict]:
    g = sim.gatherings.upcoming.get(gathering_id) or next(
        (h for h in sim.gatherings.history if h.id == gathering_id), None)
    if g is None:
        return None
    names = _Names(sim)
    now = sim.world.time.current_tick
    status = "on now" if g.is_on(now) else "over" if g.finished or now >= g.end else "coming up"
    heard = set(getattr(g, 'heard', set()))
    if not g.finished and g.news_id:
        heard |= {a.id for a in sim.world.agents if a.alive and sim.news.knows(a.id, g.news_id)}
    facts = [_fact("Host", g.organizer_name, names.person(g.organizer)), _fact("What", g.kind),
             _fact("Where", g.place), _fact("From", when(g.start)), _fact("Until", when(g.end)),
             _fact("Status", status), _fact("Heard of it", len(heard)), _fact("Came", len(g.attendees))]
    sections = [{"title": "How word spread", "text": "Only people who hear of a gathering can go: the host and "
                 "anyone nearby when it was announced, then whoever they tell, and so on."},
                {"title": f"Who came ({len(g.attendees)})", "items": names.people(g.attendees) or [{"text": "nobody yet"}]},
                {"title": f"Who heard of it ({len(heard)})", "items": names.people(heard)}]
    return {"kind": "gathering", "id": g.id, "icon": "🎉", "title": f"{g.organizer_name}'s {g.kind}",
            "subtitle": f"{g.place}, {when(g.start)}", "summary": f"{len(g.attendees)} came of {len(heard)} who heard.",
            "facts": facts, "sections": sections}


def building(sim, building_id: str) -> Optional[Dict]:
    dbs = sim.dynamic_building_system
    b = dbs.buildings.get(building_id)
    if b is None:
        return None
    names = _Names(sim)
    design = dbs.designs.get(b.design_id)
    residents = [a.id for a in sim.world.agents if a.alive and getattr(a, 'home_id', None) == b.id]
    state = "collapsed" if b.collapsed else "complete" if b.is_complete else f"{_pct(b.construction_progress)} built"
    facts = [_fact("State", state), _fact("Where", f"({b.location[0]:.0f}, {b.location[1]:.0f})"),
             _fact("Condition", _pct(min(1.0, b.durability)))]
    if getattr(b, 'built_tick', None) is not None:
        facts.append(_fact("Finished", when(b.built_tick)))
    if design is not None:
        facts.append(_fact("Kind", str(design.category).replace('_', ' ')))
        if design.intended_purposes:
            facts.append(_fact("Meant for", ", ".join(p.replace('_', ' ') for p in design.intended_purposes)))
    if getattr(b, 'quality', None) is not None and b.is_complete and not b.collapsed:
        facts.append(_fact("Built to", _pct(min(1.0, b.quality))))
    if getattr(b, 'repairs', 0):
        facts.append(_fact("Mended", f"{b.repairs}×"))
    for label, value in (("Shelter", b.shelter_value), ("Comfort", b.comfort_value), ("Defence", b.defense_value)):
        if value is not None:
            facts.append(_fact(label, _pct(min(1.0, value))))
    sections = [{"title": f"Built by ({len(b.builder_ids)})", "items": names.people(b.builder_ids)},
                {"title": f"Lives here ({len(residents)})", "items": names.people(residents) or [{"text": "nobody"}]}]
    if b.materials_used:
        sections.append({"title": "Made of", "items": [{"text": m.replace('_', ' '), "note": str(q)}
                                                       for m, q in sorted(b.materials_used.items())]})
    if b.events:
        def told(e):
            # older saves wrote the wall clock ("Completed on 2026-11-26 19:35:57"); a collapse named an id
            if e.startswith("Completed on 20") and getattr(b, 'built_tick', None) is not None:
                return f"Completed on {when(b.built_tick)}"
            for agent_id in names.by_id:
                if agent_id in e:
                    e = e.replace(agent_id, names.name(agent_id))
            return e
        sections.append({"title": "What has happened to it", "items": [{"text": told(e)} for e in b.events[-15:]]})
    return {"kind": "building", "id": b.id, "icon": "🏠", "title": b.name, "subtitle": state,
            "summary": f"Built by {', '.join(names.name(i) for i in sorted(b.builder_ids)) or 'someone'}.",
            "facts": facts, "sections": sections}


def event(sim, event_id: str) -> Optional[Dict]:
    e = next((e for e in sim.event_logger.events if e.id == event_id), None)
    if e is None:
        return None
    names = _Names(sim)
    facts = [_fact("When", when(e.tick)), _fact("Kind", e.category.value), _fact("Importance", e.importance.name.lower())]
    sections = [{"title": "Who", "items": names.people(e.agents_involved) or [{"text": "nobody in particular"}]}]
    # What it names that can be opened: know-how, governments, laws, faiths
    from world.knowhow import KNOWHOW
    text = f"{e.title} {e.description}"
    about = [link("knowhow", k.name, k.label) for k in KNOWHOW.values() if k.label in text]
    gm = sim.governance_manager
    about += [link("government", g.id, g.name) for g in gm.governments.values() if g.name in text]
    about += [link("law", l.id, l.name) for l in gm.laws.values() if len(l.name) > 6 and l.name in text][:3]
    about += [link("faith", r.id, r.name) for r in sim.religion.religions.values() if r.name in text]
    if about:
        sections.append({"title": "What it's about", "items": [{"text": l["label"], "link": l} for l in about[:8]]})
    # The hour around it, for context
    nearby = [o for o in sim.event_logger.events if o.id != e.id and abs(o.tick - e.tick) <= 6]
    if nearby:
        sections.append({"title": "Around the same time", "items": [
            {"text": o.title, "note": when(o.tick), "link": link("event", o.id, o.title)}
            for o in sorted(nearby, key=lambda o: o.tick)[:12]]})
    icon = "" if not e.title[:1].isalnum() else "📌"     # titles often start with their own emoji
    return {"kind": "event", "id": e.id, "icon": icon, "title": e.title, "subtitle": when(e.tick),
            "summary": e.description, "facts": facts, "sections": sections}


DESCRIBERS = {"agent": agent, "government": government, "law": law, "faith": faith, "knowhow": knowhow,
              "invention": invention, "gathering": gathering, "building": building, "event": event}


def describe(sim, kind: str, item_id: str) -> Optional[Dict]:
    describer = DESCRIBERS.get(kind)
    return describer(sim, item_id) if describer else None


def knowhow_view(sim) -> Dict:
    """Everything people can come to know how to do (world/knowhow.py), in
    tiers by what each builds on: who knows it now, who first worked it out
    and when, what was lost; and how know-how has passed between people
    (GET /knowhow, the Knowledge tab)."""
    from world.knowhow import AGES, KNOWHOW, knows
    ledger = sim.knowhow
    names = _Names(sim)
    alive = [a for a in sim.world.agents if a.alive]
    depth: Dict[str, int] = {}

    def tier(n):
        if n not in depth:
            depth[n] = 0 if not KNOWHOW[n].needs else 1 + max(tier(m) for m in KNOWHOW[n].needs)
        return depth[n]

    lost = {l['knowhow'] for l in ledger.lost}
    nodes = []
    for k in KNOWHOW.values():
        knowers = sum(1 for a in alive if knows(a, k.name)) if ledger.active else len(alive)
        first = ledger.firsts.get(k.name)
        state = "known" if knowers else ("lost" if k.name in lost or first else "not yet")
        nodes.append({"id": k.name, "label": k.label, "tier": tier(k.name), "knowers": knowers, "state": state,
                      "needs": [{"id": n, "label": KNOWHOW[n].label} for n in k.needs], "humans": k.humans,
                      "lets": [u.replace('_', ' ') for u in k.unlocks],
                      "first": None if not first else {"who": first['who'], "id": first['agent_id'],
                                                       "day": first['day'], "how": HOW_WORDS.get(first['how'], first['how'])}})
    recent = []
    for t, what, who, how, teacher in list(getattr(ledger, 'log', []))[-40:][::-1]:
        label = KNOWHOW[what].label if what in KNOWHOW else what
        if how == 'taught' and teacher:
            text, links = f"{names.name(teacher)} taught {names.name(who)} {label}", [names.person(teacher), names.person(who)]
        else:
            text, links = f"{names.name(who)} {HOW_WORDS.get(how, how)}: {label}", [names.person(who)]
        recent.append({"tick": t, "when": when(t), "text": text,
                       "links": [l for l in links if l] + [link("knowhow", what, label)]})
    known_now = {n["id"] for n in nodes if n["state"] == "known"}
    ages = []
    for name, marks, humans in AGES:
        reached = [ledger.firsts[m]['tick'] for m in marks if m in ledger.firsts]
        ages.append({"name": name, "marks": [KNOWHOW[m].label for m in marks], "humans": humans,
                     "now": bool(known_now & set(marks)),
                     "first_day": min(reached) // TICKS_PER_DAY + 1 if reached else None})
    age = next((a for a in reversed(ages) if a["now"]), None)
    # Within reach: not known now, but everything it builds on is
    frontier = [{"id": k.name, "label": k.label, "needs": [KNOWHOW[n].label for n in k.needs],
                 "sparks": [x.replace('_', ' ') for x in k.sparks], "humans": k.humans}
                for k in KNOWHOW.values() if k.name not in known_now and all(n in known_now for n in k.needs)]
    return {"active": ledger.active, "alive": len(alive), "nodes": sorted(nodes, key=lambda n: (n["tier"], n["label"])),
            "counts": dict(ledger.counts), "recent": recent,
            "known": len(known_now), "total": len(nodes),
            "age": age["name"] if age else "Before tools", "ages": ages, "frontier": frontier}
