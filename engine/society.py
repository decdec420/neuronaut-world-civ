"""
What the agents have built together, as one snapshot for the dashboard's
Society tab (GET /society): governments and their laws, faiths, families,
the economy, and inventions. Read-only.
"""

from typing import Dict, List


def society_snapshot(sim) -> Dict:
    by_id = {a.id: a for a in sim.world.agents}
    name = lambda agent_id: by_id[agent_id].name if agent_id in by_id else None  # noqa: E731
    gm = sim.governance_manager

    governments = []
    for gov in gm.governments.values():
        laws = [gm.laws[l] for l in gov.laws if l in gm.laws]
        governments.append({
            "name": gov.name, "type": gov.government_type.value, "active": gov.active,
            "leader": name(gov.leader_id), "citizens": len(gov.citizens),
            "laws": [{"name": law.name, "description": law.description, "active": law.active,
                      "proposed_by": name(law.created_by), "supporters": len(law.supporters),
                      "opposers": len(law.opposers), "broken": law.times_broken} for law in laws],
        })

    religions = [{
        "name": r.name, "type": r.religion_type.value, "prophet": r.founder_name or name(r.founder_id),
        "followers": len(r.followers), "temples": len(r.temples),
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
        "richest": [{"name": a.name, "wealth": round(a.wealth, 1)} for a in richest if a.wealth > 0],
    }

    inventions = [{
        "name": inv.name, "type": inv.discovery_type.value, "inventor": name(inv.discoverer_id),
        "known_by": len(inv.known_by),
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
    upcoming = [{"host": g.organizer_name, "kind": g.kind, "place": g.place, "when": when(g.start),
                 "on": g.is_on(now), "heard": sum(1 for a in alive if g.news_id and news.knows(a, g.news_id)),
                 "here": len(g.attendees)}
                for g in sorted(gatherings.upcoming.values(), key=lambda g: g.start)]
    recent = [{"host": g.organizer_name, "kind": g.kind, "place": g.place, "when": when(g.start),
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
        node = {"name": agent.name, "age": agent.age, "alive": agent.alive, "stage": agent.life_stage,
                "partner": partner.name if partner else None, "children": []}
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
