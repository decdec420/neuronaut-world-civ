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
        inv = agent.inventory
        if action.action_type == ActionType.CREATE_ALLOY:
            has_carbon = any(inv.has_item(c, 2) for c in ('carbon', 'charcoal', 'coal', 'wood'))
            if not ((inv.has_item('iron') and has_carbon) or (inv.has_item('copper', 3) and inv.has_item('tin'))):
                return False, "Need iron and something to burn (steel), or copper and tin (bronze)"
        if action.action_type == ActionType.REFINE_MATERIAL:
            if not any(inv.has_item(i) for i in ('iron_ore', 'metal_ore', 'sand')):
                return False, "No raw materials to refine"
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
                agent.needs.satisfy_need(NeedType.GROWTH, 0.5)
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.4)
                emotional_impact = 0.7 if material.unlocks_era else 0.5
                return ActionResult(success=True, emotional_impact=emotional_impact, message=f"Discovered {material.name}!", metadata={'material_id': material_id, 'product': material.name})
            return ActionResult(success=False, emotional_impact=0.05, message="Material research yielded no discoveries")
        
        elif action.action_type == ActionType.CREATE_ALLOY:
            # Steel: iron plus carbon, which a furnace gets from burning wood
            # (charcoal). Bronze: copper plus tin. A discovered alloy can be made
            # again by anyone with the ingredients; it used to work only once.
            carbon = next((c for c in ('carbon', 'charcoal', 'coal', 'wood') if agent.inventory.has_item(c, 2)), None)
            recipes = [('steel', {'iron': 1, carbon: 2} if carbon else None, 2, 0.6),
                       ('bronze', {'copper': 3, 'tin': 1}, 4, 0.7)]
            for alloy_name, needs, made, satisfaction in recipes:
                if not needs or not all(agent.inventory.has_item(i, q) for i, q in needs.items()):
                    continue
                alloy = materials_science.alloys.get(alloy_name)
                first = alloy is not None and not alloy.discovered
                if first:
                    materials_science.create_alloy(alloy_name, agent.id, current_tick)
                for item, qty in needs.items():
                    agent.inventory.remove_item(item, qty)
                agent.inventory.add_item(alloy_name, made)
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, satisfaction if first else 0.2)
                return ActionResult(success=True, emotional_impact=0.8 if first else 0.3,
                                    message=f"{'Created' if first else 'Made'} {alloy_name}",
                                    metadata={'alloy': alloy_name, 'product': alloy_name})
            return ActionResult(success=False, emotional_impact=-0.1, message="Missing materials for alloy creation")

        elif action.action_type == ActionType.REFINE_MATERIAL:
            if agent.inventory.has_item('iron_ore'):
                result = materials_science.process_material('iron', {'iron_ore': agent.inventory.items.get('iron_ore', 0)}, has_heat=True, temperature=1538)
                if result and result.get('success'):
                    agent.inventory.remove_item('iron_ore', 1)
                    agent.inventory.add_item('iron', 1)
                    logger.info(f"🔬 {agent.name} refined iron ore → iron")
                    agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
                    return ActionResult(success=True, emotional_impact=0.4, message="Refined iron ore into iron", metadata={'material': 'iron', 'product': 'iron'})
            elif agent.inventory.has_item('metal_ore'):
                # The world's metal ore is copper-bearing
                agent.inventory.remove_item('metal_ore', 1)
                agent.inventory.add_item('copper', 1)
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
                return ActionResult(success=True, emotional_impact=0.4, message="Refined metal ore into copper",
                                    metadata={'material': 'copper', 'product': 'copper'})
            elif agent.inventory.has_item('sand'):
                result = materials_science.process_material('glass', {'sand': agent.inventory.items.get('sand', 0)}, has_heat=True, temperature=1400)
                if result and result.get('success'):
                    agent.inventory.remove_item('sand', 1)
                    agent.inventory.add_item('glass', 1)
                    logger.info(f"🔬 {agent.name} made glass")
                    agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
                    return ActionResult(success=True, emotional_impact=0.4, message="Created glass from sand", metadata={'material': 'glass', 'product': 'glass'})
            
            return ActionResult(success=False, emotional_impact=0.0, message="No raw materials to refine")
        
        return ActionResult(success=False, emotional_impact=0.0, message="Unknown materials action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'materials_science']
