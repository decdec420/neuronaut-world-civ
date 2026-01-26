"""
Health Action Handler - Handles agent medical and health actions.

This handler manages all health-related actions including:
- HEAL: Treating sick agents with medicine
- DIAGNOSE: Diagnosing illnesses
- CURE: Discovering new medicines through experimentation

These actions enable agents to develop medical knowledge and care for each other.
"""

from typing import TYPE_CHECKING
import random
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


class HealthHandler(ActionHandler):
    """Handles medical and health actions for agents."""

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [ActionType.HEAL, ActionType.DIAGNOSE, ActionType.CURE]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive_valid = validate_agent_alive(agent)
        if not alive_valid[0]:
            return alive_valid

        if action.action_type in [ActionType.HEAL, ActionType.DIAGNOSE]:
            if not action.target_agent:
                return False, "No patient specified"
            target = self.context.get_agent_by_id(action.target_agent)
            if not target:
                return False, "Patient not found"

        if action.action_type == ActionType.CURE:
            if not agent.inventory.items:
                return False, "Need ingredients to create medicine"

        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        health = self.context.get_system('health')
        if not health:
            return ActionResult(success=False, emotional_impact=0.0, message="Health system unavailable")

        current_tick = self.context.current_tick

        if action.action_type == ActionType.HEAL:
            target = self.context.get_agent_by_id(action.target_agent)
            if not target:
                return ActionResult(success=False, emotional_impact=0.0, message="Patient not found")

            if not health.is_agent_sick(target.id):
                return ActionResult(success=False, emotional_impact=-0.05, message="Patient is healthy")

            result = health.apply_treatment(target.id, agent.id, medicine_id=None)

            if result['success']:
                logger.info(f"💊 {agent.name} treated {target.name} for {result['disease_type']}")
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.25)
                agent.needs.satisfy_need(NeedType.MEANING, 0.2)
                return ActionResult(
                    success=True,
                    emotional_impact=0.3,
                    message=f"Treated {target.name}",
                    metadata={'effectiveness': result['effectiveness'], 'disease_type': result['disease_type']}
                )
            else:
                return ActionResult(success=False, emotional_impact=-0.1, message=result.get('reason', 'Treatment failed'))

        elif action.action_type == ActionType.DIAGNOSE:
            target = self.context.get_agent_by_id(action.target_agent)
            if not target:
                return ActionResult(success=False, emotional_impact=0.0, message="Patient not found")

            diagnosis = health.diagnose(target.id, agent.id)

            if diagnosis:
                logger.info(f"🩺 {agent.name} diagnosed {target.name}: {diagnosis['disease_type']}")
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.15)
                return ActionResult(
                    success=True,
                    emotional_impact=0.2,
                    message=f"Diagnosed {diagnosis['disease_type']}",
                    metadata={'diagnosis': diagnosis}
                )
            else:
                return ActionResult(success=False, emotional_impact=0.0, message="Patient appears healthy")

        elif action.action_type == ActionType.CURE:
            # Try to create medicine from available materials
            ingredients = {}
            for item_name, quantity in list(agent.inventory.items.items())[:3]:
                if quantity > 0 and item_name not in ['food', 'water']:
                    ingredients[item_name] = 1
                    agent.inventory.remove_item(item_name, 1)

            if ingredients:
                methods = ['grind', 'boil', 'ferment', 'mix', 'brew']
                method = random.choice(methods)

                medicine = health.discover_medicine(
                    agent.id,
                    agent.name,
                    ingredients,
                    method,
                    current_tick
                )

                if medicine:
                    logger.info(f"💊 {agent.name} discovered medicine: {medicine.name}!")
                    agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.4)
                    agent.needs.satisfy_need(NeedType.MEANING, 0.3)
                    agent.inventory.add_item(f"medicine_{medicine.id[:8]}", 1)
                    return ActionResult(
                        success=True,
                        emotional_impact=0.5,
                        message=f"Discovered medicine: {medicine.name}",
                        metadata={'medicine_id': medicine.id, 'name': medicine.name}
                    )

            return ActionResult(success=False, emotional_impact=0.0, message="Medicine creation failed")

        return ActionResult(success=False, emotional_impact=0.0, message="Unknown health action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'health']
