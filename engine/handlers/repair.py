"""
repair: mend a damaged building with wood, stone or clay from the pack.

A disaster takes half a building's condition (engine/system_coordinator.py),
a weak building shelters the people in it less, and the next disaster is
likelier to bring it down. Nothing could mend one: 'repair' fell back to
starting a new building (UNHANDLED_ACTION_FALLBACKS), so every disaster left
homes permanently weaker until they fell.

Now someone who knows how to build shelters can walk to a damaged building
and mend it: their own home first, then one they built, then the nearest
within REPAIR_SEARCH. Each repair uses REPAIR_MATERIALS from the pack and
restores REPAIR_STEP of condition, up to the quality the building was made
with. Whether and when to repair is the agent's choice; this only makes it
possible.
"""

import math
from typing import TYPE_CHECKING, Optional

from engine.action_handlers import ActionHandler, ActionResult, validate_agent_alive
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

REPAIR_BELOW = 0.6        # condition under which a building is worth mending
REPAIR_STEP = 0.15        # condition restored by one repair
REPAIR_MATERIALS = 3      # wood, stone or clay used by one repair
REPAIR_SEARCH = 30.0      # how far an agent will look for a building to mend
MATERIALS = ("wood", "stone", "clay")
REACH = 2.5               # close enough to work on it


def quality(building) -> float:
    """The condition it was made with (older saves didn't keep it: 0.8)."""
    return min(1.0, getattr(building, 'quality', None) or 0.8)


def needs_repair(building) -> bool:
    return (building.is_complete and not building.collapsed
            and building.durability < min(REPAIR_BELOW, quality(building) - 0.05))


class RepairHandler(ActionHandler):

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type == ActionType.REPAIR

    def get_required_systems(self) -> list[str]:
        return ['world', 'dynamic_building_system', 'pathfinder', 'infrastructure']

    def _materials(self, agent) -> int:
        return sum(agent.inventory.items.get(m, 0) for m in MATERIALS)

    def _to_mend(self, agent) -> Optional[object]:
        """Its home if it needs mending, else one it built, else the nearest
        damaged building within REPAIR_SEARCH that it can walk to."""
        from life import homes
        dbs = self.context.get_system('dynamic_building_system')
        home = homes.home_of(dbs, agent)
        if home is not None and needs_repair(home):
            return home
        pathfinder = self.context.get_system('pathfinder')
        components = getattr(pathfinder, 'land_component', {}) or {}
        mine = components.get((int(agent.location.x), int(agent.location.y)))
        best, best_key = None, None
        for b in sorted(dbs.buildings.values(), key=lambda b: b.id):
            if not needs_repair(b):
                continue
            bx, by = b.location
            dist = math.hypot(agent.location.x - bx, agent.location.y - by)
            if dist > REPAIR_SEARCH:
                continue
            if components and mine is not None and components.get((int(bx), int(by))) not in (mine, None):
                continue   # on land it can't walk to
            key = (agent.id not in b.builder_ids, dist)
            if best is None or key < best_key:
                best, best_key = b, key
        return best

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive = validate_agent_alive(agent)
        if not alive[0]:
            return alive
        if self._materials(agent) < REPAIR_MATERIALS:
            return False, f"Needs {REPAIR_MATERIALS} wood, stone or clay to mend anything"
        if self._to_mend(agent) is None:
            return False, "Nothing near needs mending"
        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        building = self._to_mend(agent)
        if building is None:
            return ActionResult(success=False, emotional_impact=0.0, message="Nothing near needs mending")
        if self._materials(agent) < REPAIR_MATERIALS:
            return ActionResult(success=False, emotional_impact=-0.05,
                                message=f"Needs {REPAIR_MATERIALS} wood, stone or clay to mend anything")
        bx, by = building.location
        if math.hypot(agent.location.x - bx, agent.location.y - by) > REACH:
            works = self.context.get_system('infrastructure')
            moved = works.step_toward(agent, self.context.get_system('pathfinder'), bx, by, self.context.current_tick)
            if not moved:
                return ActionResult(success=False, emotional_impact=-0.05,
                                    message=f"Can't find a way to {building.name}")
            return ActionResult(success=True, emotional_impact=0.0,
                                message=f"Heading to mend {building.name}",
                                metadata={'building_id': building.id, 'arrived': False})
        used = {}
        for m in sorted(MATERIALS, key=lambda m: -agent.inventory.items.get(m, 0)):   # the most plentiful first
            while sum(used.values()) < REPAIR_MATERIALS and agent.inventory.items.get(m, 0) > 0:
                agent.inventory.remove_item(m, 1)
                used[m] = used.get(m, 0) + 1
        before = building.durability
        building.durability = min(quality(building), building.durability + REPAIR_STEP)
        building.maintenance_needed = building.durability < 0.5
        building.repairs = getattr(building, 'repairs', 0) + 1
        tick = self.context.current_tick
        building.events.append(f"{agent.name} mended it on day {tick // 144 + 1}, {tick // 6 % 24:02d}:00 "
                               f"({round(before * 100)}% to {round(building.durability * 100)}%)")
        is_home = getattr(agent, 'home_id', None) == building.id
        agent.needs.satisfy_need(NeedType.SHELTER, 0.3 if is_home else 0.1)
        agent.needs.satisfy_need(NeedType.SECURITY, 0.2)
        agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.2)
        return ActionResult(success=True, emotional_impact=0.2,
                            message=f"Mended {building.name} ({round(before * 100)}% to {round(building.durability * 100)}%)",
                            metadata={'building_id': building.id, 'arrived': True, 'used': used,
                                      'condition': round(building.durability, 2)})
