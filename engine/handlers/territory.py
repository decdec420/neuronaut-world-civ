"""Territory Action Handler - Handles agent land ownership and territorial actions."""

from typing import TYPE_CHECKING
import logging

from engine.action_handlers import (
    ActionHandler,
    ActionResult,
    ActionContext,
    validate_agent_alive,
)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)


class TerritoryHandler(ActionHandler):
    """Handles territorial actions for agents."""

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [ActionType.CLAIM_TERRITORY, ActionType.PATROL, ActionType.GUARD]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive_valid = validate_agent_alive(agent)
        if not alive_valid[0]:
            return alive_valid

        territory = self.context.get_system('territory')
        if not territory:
            return False, "Territory system unavailable"

        if action.action_type in [ActionType.PATROL, ActionType.GUARD]:
            agent_territories = territory.get_agent_territories(agent.id)
            if not agent_territories:
                return False, "No territory to patrol/guard"

        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from world.territory import TerritoryType

        territory = self.context.get_system('territory')
        if not territory:
            return ActionResult(success=False, emotional_impact=0.0, message="Territory system unavailable")

        current_tick = self.context.current_tick

        if action.action_type == ActionType.CLAIM_TERRITORY:
            existing = territory.get_territory_at_location((agent.location.x, agent.location.y))
            if existing and existing.owner_id == agent.id:
                return ActionResult(success=False, emotional_impact=0.0, message="Already own this territory")
            if existing:
                return ActionResult(success=False, emotional_impact=-0.1, message="Land already claimed by another")

            terr = territory.claim_territory(
                agent.id, agent.name, (agent.location.x, agent.location.y),
                radius=15.0, territory_type=TerritoryType.PERSONAL, current_tick=current_tick
            )

            if terr:
                logger.info(f"🗺️  {agent.name} claimed {terr.name}!")
                agent.needs.satisfy_need(NeedType.SECURITY, 0.3)
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.2)
                return ActionResult(success=True, emotional_impact=0.3, message=f"Claimed {terr.name}", metadata={'territory_id': terr.id})

            return ActionResult(success=False, emotional_impact=0.0, message="Could not claim territory")

        elif action.action_type == ActionType.PATROL:
            agent_territories = territory.get_agent_territories(agent.id)
            terr = agent_territories[0]
            terr.last_patrol = current_tick

            trespassers_found = []
            for trespasser_id in terr.trespassers:
                trespasser = next((a for a in self.context.world.agents if a.id == trespasser_id), None)
                if trespasser and trespasser.alive:
                    dist = ((trespasser.location.x - terr.center[0])**2 + (trespasser.location.y - terr.center[1])**2)**0.5
                    if dist <= terr.radius:
                        trespassers_found.append(trespasser.name)

            if trespassers_found:
                logger.warning(f"⚔️  {agent.name} found trespassers: {', '.join(trespassers_found)}")
                agent.needs.satisfy_need(NeedType.SECURITY, -0.2)
                return ActionResult(success=True, emotional_impact=-0.1, message="Found trespassers", metadata={'trespassers': len(trespassers_found)})
            else:
                agent.needs.satisfy_need(NeedType.SECURITY, 0.1)
                return ActionResult(success=True, emotional_impact=0.1, message="Territory secure")

        elif action.action_type == ActionType.GUARD:
            agent_territories = territory.get_agent_territories(agent.id)
            terr = agent_territories[0]
            territory.add_guard(terr.id, agent.id)
            logger.info(f"🛡️ {agent.name} now guards {terr.name}")
            agent.needs.satisfy_need(NeedType.SECURITY, 0.2)
            agent.needs.satisfy_need(NeedType.MEANING, 0.1)
            return ActionResult(success=True, emotional_impact=0.2, message=f"Guarding {terr.name}", metadata={'territory_id': terr.id})

        return ActionResult(success=False, emotional_impact=0.0, message="Unknown territory action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'territory']
