"""
What the agents have built together, as one snapshot for the dashboard's
Society tab (GET /society): governments and their laws, faiths, families,
the economy, and inventions. Read-only.
"""

from typing import Dict, List

TICKS_PER_DAY = 144


def society_snapshot(sim) -> Dict:
    by_id = {a.id: a for a in sim.world.agents}
    name = lambda agent_id: by_id[agent_id].name if agent_id in by_id else None  # noqa: E731
    gm = sim.governance_manager

    governments = []
    for gov in gm.governments.values():
        laws = [gm.laws[l] for l in gov.laws if l in gm.laws]
        governments.append({
            "id": gov.id, "name": gov.name, "type": gov.government_type.value, "active": gov.active,
            "leader": name(gov.leader_id), "leader_id": gov.leader_id, "citizens": len(gov.citizens),
            "approval": round(gov.approval_rating, 2),
            "founded_day": gov.founded_tick // TICKS_PER_DAY + 1 if getattr(gov, 'founded_tick', None) is not None else None,
            "laws": [{"id": law.id, "name": law.name, "description": law.description, "active": law.active,
                      "proposed_by": name(law.created_by), "proposed_by_id": law.created_by,
                      "supporters": len(law.supporters),
                      "opposers": len(law.opposers), "broken": law.times_broken} for law in laws],
        })

    religions = [{
        "id": r.id, "name": r.name, "type": r.religion_type.value, "prophet": r.founder_name or name(r.founder_id),
        "prophet_id": r.founder_id, "followers": len(r.followers), "temples": len(r.temples),
        "belief": r.core_beliefs[0] if r.core_beliefs else None,
    } for r in sim.religion.religions.values()]

    economy = sim.economy
    alive = [a for a in sim.world.agents if a.alive]
    richest = sorted(alive, key=lambda a: -a.wealth)[:3]
    banks = getattr(getattr(economy, "banking", None), "banks", {})
    successes = getattr(sim, "action_successes", {})
    economy_view = {
        "money": round(sum(a.wealth for a in alive), 1),
        "trades": successes.get("trade", 0),
        "coins_minted": successes.get("mint_coins", 0),
        "banks": len(banks),
        "richest": [{"id": a.id, "name": a.name, "wealth": round(a.wealth, 1)} for a in richest if a.wealth > 0],
    }

    inventions = [{
        "id": inv.id, "name": inv.name, "type": inv.discovery_type.value, "inventor": name(inv.discoverer_id),
        "inventor_id": inv.discoverer_id, "known_by": len(inv.known_by),
    } for inv in sim.innovation_manager.innovations.values()]

    return {
        "tick": sim.world.time.current_tick,
        "governments": governments,
        "religions": religions,
        "families": family_tree(sim),
        "economy": economy_view,
        "inventions": inventions,
        "village_life": village_life(sim),
    }


def village_life(sim) -> Dict:
    """Gatherings (upcoming and recent), the news most people know, and the
    village's public works."""
    now = sim.world.time.current_tick
    alive = [a.id for a in sim.world.agents if a.alive]
    gatherings, news = sim.gatherings, sim.news

    def when(tick):
        return f"day {tick // 144 + 1}, {tick // 6 % 24:02d}:00"
    upcoming = [{"id": g.id, "host": g.organizer_name, "host_id": g.organizer, "kind": g.kind, "place": g.place,
                 "when": when(g.start),
                 "on": g.is_on(now), "heard": sum(1 for a in alive if g.news_id and news.knows(a, g.news_id)),
                 "here": len(g.attendees)}
                for g in sorted(gatherings.upcoming.values(), key=lambda g: g.start)]
    recent = [{"id": g.id, "host": g.organizer_name, "host_id": g.organizer, "kind": g.kind, "place": g.place,
               "when": when(g.start),
               "heard": g.heard_before_start, "came": len(g.attendees)}
              for g in reversed(gatherings.history[-8:])]
    talked_about = sorted(((news.reach(n.id, alive), n.text) for n in news.items.values()), reverse=True)[:6]
    works = sim.infrastructure
    return {
        "upcoming": upcoming,
        "recent": recent,
        "news": [{"text": text, "reach": round(reach, 2)} for reach, text in talked_about],
        "works": {"road_tiles": len(works.roads), "wells": len(works.wells), "street_lights": len(works.lights),
                  "lit": sum(1 for l in works.lights.values() if l.lit)},
        "conversations": news.conversations,
    }


def family_tree(sim) -> List[Dict]:
    """Families as trees: founders (no parents in the village) who have
    children at the top, each child with its own partner and children."""
    by_id = {a.id: a for a in sim.world.agents}

    def person(agent, depth=0) -> Dict:
        partner = by_id.get(agent.partner_id) if agent.partner_id else None
        node = {"id": agent.id, "name": agent.name, "age": agent.age, "alive": agent.alive, "stage": agent.life_stage,
                "partner": partner.name if partner else None, "partner_id": partner.id if partner else None,
                "children": []}
        if depth < 6:
            node["children"] = [person(by_id[c], depth + 1) for c in agent.children_ids if c in by_id]
        return node

    roots, seen = [], set()
    for agent in sim.world.agents:
        if agent.children_ids and not (agent.mother_id in by_id or agent.father_id in by_id):
            # A couple shares one tree: start from whichever parent comes first
            pair = frozenset([agent.id] + [p for c in agent.children_ids if c in by_id
                                            for p in (by_id[c].mother_id, by_id[c].father_id) if p])
            if pair & seen:
                continue
            seen |= pair
            roots.append(person(agent))
    return roots


def roles_snapshot(sim) -> Dict:
    """Who does what (GET /roles): each living person's job (the work they've
    done most in work hours, agents/daily_life.py), the roles people have now
    (an activity that's 30% of what they do lately, named by them,
    world/roles.py) and the roles they've left behind."""
    from agents.daily_life import JOBS
    from collections import Counter
    roles = sim.role_emergence
    by_id = {a.id: a for a in sim.world.agents}

    def day(tick):
        return tick // TICKS_PER_DAY + 1 if tick is not None else None

    current, former = [], []
    for agent_id in sorted(roles.agent_roles):
        agent = by_id.get(agent_id)
        if agent is None:
            continue
        for r in roles.agent_roles[agent_id]:
            action = r.behavior_pattern.dominant_actions[0] if r.behavior_pattern.dominant_actions else "work"
            row = {"role_id": r.role_id, "name": r.custom_role_name or "unnamed", "agent_id": agent.id,
                   "agent_name": agent.name, "alive": agent.alive, "action": action,
                   "activity": action.replace("_", " "), "share": round(r.behavior_pattern.pattern_strength, 2),
                   "times": r.times_acted_in_role, "since_day": day(getattr(r, "started_tick", None)),
                   "ended_day": day(getattr(r, "ended_tick", None)), "recognized_by": len(r.recognized_by),
                   "previous_names": list(r.previous_names)}
            (current if getattr(r, "active", True) and agent.alive else former).append(row)
    current.sort(key=lambda r: (-r["share"], r["agent_name"]))
    former.sort(key=lambda r: -(r["ended_day"] or 0))

    alive = [a for a in sim.world.agents if a.alive]
    jobs = {}
    no_job = []
    for a in sorted(alive, key=lambda a: a.name):
        work = getattr(a, "work_life", None)
        if work is None or not work.job:
            no_job.append({"id": a.id, "name": a.name, "age": a.age,
                           "shifts": len(work.recent_shifts) if work else 0})
            continue
        shifts = Counter(work.recent_shifts)
        entry = jobs.setdefault(work.job, {"key": work.job, "title": JOBS[work.job].title,
                                           "work": [w.replace("_", " ") for w in JOBS[work.job].actions],
                                           "people": []})
        entry["people"].append({"id": a.id, "name": a.name,
                                "share": round(shifts[work.job] / max(1, sum(shifts.values())), 2)})
    return {
        "jobs": sorted(jobs.values(), key=lambda j: -len(j["people"])),
        "no_job": no_job,
        "current": current,
        "former": former[:60],
        "activities": Counter(r["activity"] for r in current).most_common(),
        "vocabulary": [{"name": n, "uses": c, "coined_by": by_id[roles.role_name_origins[n]].name
                        if roles.role_name_origins.get(n) in by_id else None,
                        "coined_by_id": roles.role_name_origins.get(n)}
                       for n, c in sorted(roles.role_vocabulary.items(), key=lambda kv: -kv[1])[:24]],
        "alive": len(alive),
    }


def culture_snapshot(sim) -> Dict:
    """What people do for joy (GET /culture): celebrations someone chose to
    throw, with the host and who came; the gatherings people organized and
    went to; art and who made it; games, who played and who won. In sim
    time, with ids so each person opens."""
    fun = sim.fun_system
    by_id = {a.id: a for a in sim.world.agents}

    def person(agent_id):
        a = by_id.get(agent_id)
        return {"id": agent_id, "name": a.name if a else "someone"}

    def when(tick):
        return f"day {tick // TICKS_PER_DAY + 1}, {tick // 6 % 24:02d}:00" if tick is not None else None

    def celebration(c, live):
        return {"id": c.id, "name": c.celebration_name or "A celebration", "kind": c.celebration_type.value,
                "why": c.trigger_event, "host": person(c.organizer_id), "live": live,
                "guests": [person(g) for g in sorted(c.participants) if g != c.organizer_id],
                "when": when(getattr(c, "start_tick", None)),
                "hours_left": round(c.duration_ticks / 6, 1) if live else None}

    celebrations = ([celebration(c, True) for c in fun.active_celebrations.values()]
                    + [celebration(c, False) for c in reversed(fun.celebration_history[-30:])])
    art = sorted(fun.art_pieces.values(), key=lambda a: getattr(a, "tick", None) or -1, reverse=True)
    finest = sorted(fun.art_pieces.values(), key=lambda a: -a.quality)[:6]

    def art_row(a):
        return {"id": a.id, "title": a.title, "kind": a.art_type, "maker": person(a.creator_id),
                "quality": round(a.quality, 2), "when": when(getattr(a, "tick", None))}

    games = [{"kind": g.game_type.value, "players": [person(p) for p in g.players],
              "winner": person(g.winner) if g.winner else None, "when": when(getattr(g, "tick", None))}
             for g in reversed(fun.game_history[-12:])]
    life = village_life(sim)
    return {
        "counts": {"celebrations": fun.total_celebrations, "games": fun.total_games,
                   "art": fun.total_art_created,
                   "gatherings_held": len(sim.gatherings.history),   # the last 50 are kept
                   "live": len(fun.active_celebrations)},
        "celebrations": celebrations,
        "kinds": dict(sorted(fun.traditions.items(), key=lambda kv: -kv[1])),
        "gatherings": {"upcoming": life.get("upcoming", []), "recent": life.get("recent", [])},
        "art": {"latest": [art_row(a) for a in art[:10]], "finest": [art_row(a) for a in finest]},
        "games": games,
    }


def lab_snapshot(sim) -> Dict:
    """What experimenting has come to (GET /lab): what's been made, the
    things worked out most often first (by how many people), who made each
    first and from what; the newest; who experiments most; and what keeps
    failing, by reason and by the combination tried. In sim time, with ids."""
    from collections import Counter
    engine = sim.experimentation_engine
    by_id = {a.id: a for a in sim.world.agents}

    def person(agent_id):
        a = by_id.get(agent_id)
        return {"id": agent_id, "name": a.name if a else "someone"}

    def when(tick):
        return f"day {tick // TICKS_PER_DAY + 1}, {tick // 6 % 24:02d}:00" if tick is not None else None

    def made_from(recipe):
        inputs = (recipe or {}).get("inputs") or {}
        method = str((recipe or {}).get("method") or "").replace("_", " ")
        parts = " + ".join(f"{q} {m.replace('_', ' ')}" for m, q in sorted(inputs.items()))
        return f"{method}: {parts}" if method else parts

    def row(d):
        return {"id": d.id, "name": d.name.replace("_", " "), "by": person(d.discovered_by),
                "when": when(getattr(d, "tick", None)), "from": made_from(d.recipe),
                "known_by": len(d.known_by), "used": d.times_used, "kind": d.category.value,
                "properties": sorted(p.value for p in (d.properties or ()))[:4]}

    found = list(engine.discoveries.values())
    failed = list(engine.failed_experiments)
    # The same thing is often worked out again by someone else (each is its
    # own record, known only to its maker): group them by what was made
    groups = {}
    for d in found:
        groups.setdefault(d.name, []).append(d)

    def made_thing(name, ds):
        first = min(ds, key=lambda d: (getattr(d, "tick", None) is None, getattr(d, "tick", None) or 0))
        makers = {d.discovered_by for d in ds}
        return {**row(first), "times": len(ds), "makers": len(makers)}

    made = Counter(d.discovered_by for d in found)
    missed = Counter(f["agent_id"] for f in failed)
    people = sorted(set(made) | set(missed), key=lambda i: (-(made[i] + missed[i]), i))
    ticked = [d for d in found if getattr(d, "tick", None) is not None]
    newest = sorted(ticked, key=lambda d: d.tick, reverse=True)[:10] if ticked else list(reversed(found[-10:]))
    return {
        "counts": {"tried": len(found) + len(failed), "made": len(found), "failed": len(failed),
                   "people": len(people)},
        "distinct": len(groups),
        "most_made": [made_thing(n, ds) for n, ds in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:20]],
        "newest": [row(d) for d in newest],
        "experimenters": [{**person(i), "made": made[i], "failed": missed[i]} for i in people[:10]],
        "failures_by_reason": Counter(str(f.get("reason")) for f in failed).most_common(8),
        "failing_combinations": Counter(made_from({"inputs": f.get("inputs"), "method": f.get("method")})
                                        for f in failed).most_common(8),
    }
