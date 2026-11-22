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
