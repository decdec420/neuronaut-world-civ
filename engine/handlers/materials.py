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
            if self._raw_to_refine(agent, action) is None:
                return False, "No raw materials to refine (glass also needs wood or coal to burn)"
        return True, ""

    # raw material -> (product, what the fire needs). Glass needs a hot fire,
    # so it burns one unit of fuel.
    REFINING = {'iron_ore': ('iron', None), 'metal_ore': ('copper', None), 'sand': ('glass', 'fuel')}
    FUELS = ('coal', 'charcoal', 'wood')
    WORDS = {'iron_ore': ('iron',), 'metal_ore': ('copper', 'metal'), 'sand': ('glass', 'sand')}

    def _fuel(self, agent):
        return next((f for f in self.FUELS if agent.inventory.has_item(f)), None)

    def _raw_to_refine(self, agent, action):
        """What to refine: what the agent asked for (DETAILS: "sand into glass"),
        else the raw material it holds most of. (This used to take iron ore,
        then metal ore, then sand, so glass came only from agents with no ore.)"""
        inv = agent.inventory
        usable = [raw for raw, (_, needs) in self.REFINING.items()
                  if inv.has_item(raw) and (needs != 'fuel' or self._fuel(agent))]
        if not usable:
            return None
        details = str((action.parameters or {}).get('details', '')).lower()
        asked = [raw for raw in usable if any(w in details for w in self.WORDS[raw])]
        if asked:
            return asked[0]
        return max(usable, key=lambda raw: inv.items.get(raw, 0))

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
            raw = self._raw_to_refine(agent, action)
            if raw is None:
                return ActionResult(success=False, emotional_impact=0.0, message="No raw materials to refine")
            product, needs = self.REFINING[raw]
            if product in ('iron', 'glass'):
                melting = 1538 if product == 'iron' else 1400
                result = materials_science.process_material(product, {raw: agent.inventory.items.get(raw, 0)},
                                                            has_heat=True, temperature=melting)
                if not (result and result.get('success')):
                    return ActionResult(success=False, emotional_impact=-0.1,
                                        message=f"Couldn't make {product}: {(result or {}).get('reason', 'unknown')}")
            agent.inventory.remove_item(raw, 1)
            if needs == 'fuel':
                agent.inventory.remove_item(self._fuel(agent), 1)
            agent.inventory.add_item(product, 1)
            agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
            logger.info(f"🔬 {agent.name} refined {raw} into {product}")
            return ActionResult(success=True, emotional_impact=0.4,
                                message=f"Refined {raw.replace('_', ' ')} into {product}",
                                metadata={'material': product, 'product': product})

        return ActionResult(success=False, emotional_impact=0.0, message="Unknown materials action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'materials_science']
