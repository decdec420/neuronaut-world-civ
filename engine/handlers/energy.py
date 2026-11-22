"""Energy Action Handler - Handles power generation and energy discovery."""

from typing import TYPE_CHECKING
import random
import logging

from engine.action_handlers import (ActionHandler, ActionResult, ActionContext, validate_agent_alive)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)

class EnergyHandler(ActionHandler):
    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [ActionType.BUILD_POWER_PLANT, ActionType.DISCOVER_ENERGY, ActionType.OPERATE_POWER_PLANT]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        if not validate_agent_alive(agent)[0]:
            return validate_agent_alive(agent)
        
        if action.action_type == ActionType.BUILD_POWER_PLANT and not agent.inventory.has_item('materials'):
            return False, "Need materials to build"
        
        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from world.energy import PowerPlantType, EnergyType
        
        energy = self.context.get_system('energy')
        if not energy:
            return ActionResult(success=False, emotional_impact=0.0, message="Energy system unavailable")
        
        current_tick = self.context.current_tick
        
        if action.action_type == ActionType.BUILD_POWER_PLANT:
            plant_type = PowerPlantType.FIRE_PIT
            fuel_type = EnergyType.FIRE
            
            if EnergyType.COAL in energy.discovered_energy_types:
                plant_type = PowerPlantType.FURNACE
                fuel_type = EnergyType.COAL
            
            plant = energy.build_power_plant(plant_type, fuel_type, (agent.location.x, agent.location.y), agent.id, agent.id, current_tick)
            
            if plant:
                agent.inventory.remove_item('materials', 5)
                logger.info(f"⚡ {agent.name} built {plant.name}!")
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.5)
                return ActionResult(success=True, emotional_impact=0.6, message=f"Built {plant.name}!", metadata={'plant_id': plant.id})
            return ActionResult(success=False, emotional_impact=-0.1, message="Cannot build power plant")
        
        elif action.action_type == ActionType.DISCOVER_ENERGY:
            undiscovered = [et for et in EnergyType if et not in energy.discovered_energy_types and et not in [EnergyType.MANUAL, EnergyType.FIRE]]
            if undiscovered and random.random() < 0.03:
                energy_type = random.choice(undiscovered)
                source = energy.discover_energy_source(energy_type, agent.id, current_tick)
                if source:
                    logger.info(f"⚡ {agent.name} discovered {source.name}!")
                    agent.needs.satisfy_need(NeedType.GROWTH, 0.5)
                    agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.4)
                    return ActionResult(success=True, emotional_impact=0.7, message=f"Discovered {source.name}!", metadata={'energy_type': energy_type.value})
            return ActionResult(success=False, emotional_impact=0.05, message="Exploration yielded no new energy sources")
        
        elif action.action_type == ActionType.OPERATE_POWER_PLANT:
            plants = energy.get_plants_by_owner(agent.id)
            if not plants:
                return ActionResult(success=False, emotional_impact=0.0, message="No power plants to operate")
            
            plant = plants[0]
            fuel_amount = 0.0
            
            if agent.inventory.has_item('wood'):
                fuel_amount = min(5, agent.inventory.items.get('wood', 0))
                agent.inventory.remove_item('wood', fuel_amount)
            elif agent.inventory.has_item('coal'):
                fuel_amount = min(3, agent.inventory.items.get('coal', 0))
                agent.inventory.remove_item('coal', fuel_amount)
            
            if fuel_amount > 0:
                energy_generated = energy.operate_power_plant(plant.id, fuel_amount)
                logger.info(f"⚡ {agent.name} generated {energy_generated:.1f} kW")
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.2)
                return ActionResult(success=True, emotional_impact=0.3, message=f"Generated {energy_generated:.1f} kW", metadata={'energy': energy_generated})
            return ActionResult(success=False, emotional_impact=-0.1, message="No fuel available")
        
        return ActionResult(success=False, emotional_impact=0.0, message="Unknown energy action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'energy']
