"""Materials Action Handler - Handles materials science and alloy creation."""

from typing import TYPE_CHECKING
import random
import logging

from engine.action_handlers import (ActionHandler, ActionResult, ActionContext, validate_agent_alive)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)

class MaterialsHandler(ActionHandler):
    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [ActionType.DISCOVER_MATERIAL, ActionType.CREATE_ALLOY, ActionType.REFINE_MATERIAL]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        if not validate_agent_alive(agent)[0]:
            return validate_agent_alive(agent)
        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        materials_science = self.context.get_system('materials_science')
        if not materials_science:
            return ActionResult(success=False, emotional_impact=0.0, message="Materials science system unavailable")
        
        current_tick = self.context.current_tick
        
        if action.action_type == ActionType.DISCOVER_MATERIAL:
            undiscovered = [(mid, mat) for mid, mat in materials_science.materials.items() if not mat.discovered]
            if undiscovered and random.random() < 0.04:
                material_id, material = random.choice(undiscovered)
                materials_science.discover_material(material_id, agent.id, current_tick)
                logger.info(f"🔬 {agent.name} discovered {material.name}!")
                agent.needs.satisfy_need(NeedType.LEARNING, 0.5)
                agent.needs.satisfy_need(NeedType.MASTERY, 0.4)
                emotional_impact = 0.7 if material.unlocks_era else 0.5
                return ActionResult(success=True, emotional_impact=emotional_impact, message=f"Discovered {material.name}!", metadata={'material_id': material_id})
            return ActionResult(success=False, emotional_impact=0.05, message="Material research yielded no discoveries")
        
        elif action.action_type == ActionType.CREATE_ALLOY:
            if agent.inventory.has_item('iron') and agent.inventory.has_item('carbon'):
                steel_alloy = materials_science.alloys.get('steel')
                if steel_alloy and not steel_alloy.discovered:
                    materials_science.create_alloy('steel', agent.id, current_tick)
                    agent.inventory.remove_item('iron', 1)
                    agent.inventory.remove_item('carbon', 1)
                    agent.inventory.add_item('steel', 2)
                    logger.info(f"🔬 {agent.name} created steel!")
                    agent.needs.satisfy_need(NeedType.MASTERY, 0.6)
                    return ActionResult(success=True, emotional_impact=0.8, message="Created steel!", metadata={'alloy': 'steel'})
            
            if agent.inventory.has_item('copper') and agent.inventory.has_item('tin'):
                bronze_alloy = materials_science.alloys.get('bronze')
                if bronze_alloy and not bronze_alloy.discovered:
                    materials_science.create_alloy('bronze', agent.id, current_tick)
                    agent.inventory.remove_item('copper', 3)
                    agent.inventory.remove_item('tin', 1)
                    agent.inventory.add_item('bronze', 4)
                    logger.info(f"🔬 {agent.name} created bronze!")
                    agent.needs.satisfy_need(NeedType.MASTERY, 0.7)
                    return ActionResult(success=True, emotional_impact=0.9, message="Created bronze! Bronze Age begins!", metadata={'alloy': 'bronze'})
            
            return ActionResult(success=False, emotional_impact=-0.1, message="Missing materials for alloy creation")
        
        elif action.action_type == ActionType.REFINE_MATERIAL:
            if agent.inventory.has_item('iron_ore'):
                result = materials_science.process_material('iron', {'iron_ore': agent.inventory.items.get('iron_ore', 0)}, has_heat=True, temperature=1538)
                if result and result.get('success'):
                    agent.inventory.remove_item('iron_ore', 1)
                    agent.inventory.add_item('iron', 1)
                    logger.info(f"🔬 {agent.name} refined iron ore → iron")
                    agent.needs.satisfy_need(NeedType.MASTERY, 0.3)
                    return ActionResult(success=True, emotional_impact=0.4, message="Refined iron ore into iron", metadata={'material': 'iron'})
            elif agent.inventory.has_item('sand'):
                result = materials_science.process_material('glass', {'sand': agent.inventory.items.get('sand', 0)}, has_heat=True, temperature=1400)
                if result and result.get('success'):
                    agent.inventory.remove_item('sand', 1)
                    agent.inventory.add_item('glass', 1)
                    logger.info(f"🔬 {agent.name} made glass")
                    agent.needs.satisfy_need(NeedType.MASTERY, 0.3)
                    return ActionResult(success=True, emotional_impact=0.4, message="Created glass from sand", metadata={'material': 'glass'})
            
            return ActionResult(success=False, emotional_impact=0.0, message="No raw materials to refine")
        
        return ActionResult(success=False, emotional_impact=0.0, message="Unknown materials action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'materials_science']
