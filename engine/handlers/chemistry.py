"""Chemistry Action Handler - Handles chemical experimentation and discovery."""

from typing import TYPE_CHECKING
import random
import logging

from engine.action_handlers import (ActionHandler, ActionResult, ActionContext, validate_agent_alive)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)

class ChemistryHandler(ActionHandler):
    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [ActionType.PERFORM_CHEMISTRY, ActionType.SMELT_ORE, ActionType.DISCOVER_ELEMENT]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        if not validate_agent_alive(agent)[0]:
            return validate_agent_alive(agent)
        
        if action.action_type == ActionType.PERFORM_CHEMISTRY and not agent.inventory.has_item('wood'):
            return False, "No materials for chemistry"
        if action.action_type == ActionType.SMELT_ORE and not (agent.inventory.has_item('iron_ore') and agent.inventory.has_item('wood')):
            return False, "Need iron ore and wood"
        
        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        chemistry = self.context.get_system('chemistry')
        if not chemistry:
            return ActionResult(success=False, emotional_impact=0.0, message="Chemistry system unavailable")
        
        current_tick = self.context.current_tick
        
        if action.action_type == ActionType.PERFORM_CHEMISTRY:
            result = chemistry.attempt_reaction(reactants={"CH4": 1, "O2": 2}, temperature=600, has_catalyst=False)
            if result.get('success'):
                agent.inventory.remove_item('wood', 1)
                agent.inventory.add_item('ash', 1)
                for product_formula in result.get('products', {}).keys():
                    compound = chemistry.discover_compound(product_formula, agent.id, current_tick)
                    if compound and compound.discoverer_id == agent.id:
                        logger.info(f"⚗️ {agent.name} discovered {compound.name}!")
                agent.needs.satisfy_need(NeedType.LEARNING, 0.3)
                agent.needs.satisfy_need(NeedType.MASTERY, 0.2)
                return ActionResult(success=True, emotional_impact=0.4, message=f"Chemical reaction: {result.get('reaction_type')}")
            return ActionResult(success=False, emotional_impact=-0.1, message=f"Reaction failed: {result.get('reason')}")
        
        elif action.action_type == ActionType.SMELT_ORE:
            result = chemistry.attempt_reaction(reactants={"Fe2O3": 1, "C": 3}, temperature=1200, has_catalyst=False)
            if result.get('success'):
                agent.inventory.remove_item('iron_ore', 1)
                agent.inventory.remove_item('wood', 3)
                agent.inventory.add_item('iron', 2)
                iron_element = chemistry.discover_element('Fe', agent.id, current_tick)
                if iron_element and iron_element.discoverer_id == agent.id:
                    logger.info(f"⚗️ {agent.name} discovered iron!")
                agent.needs.satisfy_need(NeedType.MASTERY, 0.4)
                return ActionResult(success=True, emotional_impact=0.5, message="Successfully smelted iron!")
            return ActionResult(success=False, emotional_impact=-0.2, message=f"Smelting failed: {result.get('reason')}")
        
        elif action.action_type == ActionType.DISCOVER_ELEMENT:
            undiscovered = [e for e in chemistry.elements.values() if not e.discovered]
            if undiscovered and random.random() < 0.05:
                element = random.choice(undiscovered)
                chemistry.discover_element(element.symbol, agent.id, current_tick)
                logger.info(f"⚗️ {agent.name} discovered {element.name}!")
                agent.needs.satisfy_need(NeedType.LEARNING, 0.5)
                agent.needs.satisfy_need(NeedType.MASTERY, 0.4)
                return ActionResult(success=True, emotional_impact=0.6, message=f"Discovered {element.name}!", metadata={'element': element.symbol})
            return ActionResult(success=False, emotional_impact=0.05, message="Experimentation yielded no new elements")
        
        return ActionResult(success=False, emotional_impact=0.0, message="Unknown chemistry action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'chemistry']
