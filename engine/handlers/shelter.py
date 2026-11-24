"""
hide: take shelter in a standing building (engine/system_coordinator.py).

When a disaster hits, anyone within SHELTER_RADIUS of a standing building is
sheltered by it: their chance of dying shrinks with its durability. Until
now nothing took an agent there on purpose ('hide' fell back to resting
wherever it stood). Now hide walks toward the agent's home if it has one,
else the sturdiest standing building nearby, along real paths (roads help,
water doesn't), and once there it stays put and feels safer.

Whether and when to hide is the agent's choice: warnings of a coming
disaster are in its perception, and the rule-based brain weighs them
(agents/utility_brain.py).
"""

import math
from typing import TYPE_CHECKING, Optional

from engine.action_handlers import ActionHandler, ActionResult, validate_agent_alive
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

SHELTER_SEARCH = 40.0   # how far an agent will look for a building to shelter in


class ShelterHandler(ActionHandler):

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type == ActionType.HIDE

    def get_required_systems(self) -> list[str]:
        return ['world', 'dynamic_building_system', 'pathfinder', 'infrastructure']

    def _shelter_for(self, agent) -> Optional[object]:
        """Its own home if it stands, else the sturdiest standing building
        within SHELTER_SEARCH that it can walk to."""
        from life import homes
        dbs = self.context.get_system('dynamic_building_system')
        home = homes.home_of(dbs, agent)
        if home is not None:
            return home
        pathfinder = self.context.get_system('pathfinder')
        components = getattr(pathfinder, 'land_component', {}) or {}
        mine = components.get((int(agent.location.x), int(agent.location.y)))
        best, best_key = None, None
        for b in sorted(dbs.buildings.values(), key=lambda b: b.id):
            if not b.is_complete or b.collapsed:
                continue
            bx, by = b.location
            dist = math.hypot(agent.location.x - bx, agent.location.y - by)
            if dist > SHELTER_SEARCH:
                continue
            if components and mine is not None and components.get((int(bx), int(by))) not in (mine, None):
                continue   # on land it can't walk to
            key = (-b.durability, dist)
            if best is None or key < best_key:
                best, best_key = b, key
        return best

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive = validate_agent_alive(agent)
        if not alive[0]:
            return alive
        if self._shelter_for(agent) is None:
            return False, "There's no standing building near enough to shelter in"
        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from engine.system_coordinator import SHELTER_RADIUS
        building = self._shelter_for(agent)
        if building is None:
            return ActionResult(success=False, emotional_impact=-0.05,
                                message="There's no standing building near enough to shelter in")
        bx, by = building.location
        distance = math.hypot(agent.location.x - bx, agent.location.y - by)
        if distance > SHELTER_RADIUS - 1:
            works = self.context.get_system('infrastructure')
            moved = works.step_toward(agent, self.context.get_system('pathfinder'), bx, by, self.context.current_tick)
            if not moved:
                return ActionResult(success=False, emotional_impact=-0.05,
                                    message=f"Can't find a way to {building.name}")
            return ActionResult(success=True, emotional_impact=0.0,
                                message=f"Heading for shelter at {building.name}",
                                metadata={'shelter_id': building.id, 'arrived': False})
        agent.needs.satisfy_need(NeedType.SECURITY, 0.3)
        agent.needs.satisfy_need(NeedType.SHELTER, 0.2)
        agent.emotions.stress = max(0.0, agent.emotions.stress - 0.1)
        return ActionResult(success=True, emotional_impact=0.1,
                            message=f"Sheltering in {building.name}",
                            metadata={'shelter_id': building.id, 'arrived': True})
