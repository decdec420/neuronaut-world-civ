"""
What the map viewer needs to draw the town (web/town_map.js).

- map_layout(sim): the terrain grid and where the world's resources are. It
  changes rarely, so the viewer fetches it once from GET /map (and again
  when a save is loaded).
- town_snapshot(sim): what changes every tick and isn't elsewhere in the
  snapshot: buildings at their real places (finished, going up or fallen),
  who lives in each and who is home, gatherings, and the weather.

Read-only: nothing here changes the world.
"""

import math
from typing import Dict, List

TERRAIN_CODES = {"plains": "p", "forest": "f", "mountains": "m", "water": "w", "desert": "d"}
HOME_RADIUS = 3.0   # same as life/homes.py: within this, an agent is at home


def map_layout(sim) -> Dict:
    world_map = sim.world.map
    width, height = world_map.width, world_map.height
    rows = []
    resources: Dict[str, List[List[int]]] = {}
    for y in range(height):
        row = []
        for x in range(width):
            tile = world_map.tiles.get((x, y))
            row.append(TERRAIN_CODES.get(tile.terrain.value, "p") if tile else "p")
            if tile is not None:
                for r in tile.resources:
                    resources.setdefault(r.resource_type.value, []).append([x, y])
        rows.append("".join(row))
    return {"width": width, "height": height, "terrain": rows, "resources": resources,
            "codes": {v: k for k, v in TERRAIN_CODES.items()}}


def town_snapshot(sim) -> Dict:
    dbs = sim.dynamic_building_system
    alive = [a for a in sim.world.agents if a.alive]
    residents: Dict[str, List] = {}
    for a in alive:
        home_id = getattr(a, "home_id", None)
        if home_id:
            residents.setdefault(home_id, []).append(a)

    buildings = []
    for b in dbs.buildings.values():
        design = dbs.designs.get(b.design_id)
        living = residents.get(b.id, [])
        bx, by = b.location
        home_now = [a for a in living
                    if math.hypot(a.location.x - bx, a.location.y - by) <= HOME_RADIUS]
        buildings.append({
            "id": b.id,
            "name": b.name,
            "x": bx,
            "y": by,
            "category": design.category if design is not None else "Residential",
            "purposes": list(design.intended_purposes) if design is not None else [],
            "complete": bool(b.is_complete),
            "progress": round(float(b.construction_progress or 0.0), 3),
            "collapsed": bool(b.collapsed),
            "durability": round(float(b.durability), 3),
            "residents": [a.name for a in living],
            "home_now": len(home_now),
        })

    tick = sim.world.time.current_tick
    gatherings = []
    for g in sim.gatherings.upcoming.values():
        gatherings.append({
            "id": g.id, "kind": g.kind, "place": g.place, "host": g.organizer_name,
            "x": g.x, "y": g.y, "start": g.start, "end": g.end,
            "on": g.is_on(tick), "attendees": len(g.attendees),
        })

    weather = getattr(sim, "weather", None)
    return {
        "tick": tick,
        "hour": sim.world.time.hour,
        "minute": (tick % 6) * 10,          # 6 ticks an hour
        "buildings": buildings,
        "gatherings": gatherings,
        "weather": weather.current_weather.value if weather is not None else None,
    }
