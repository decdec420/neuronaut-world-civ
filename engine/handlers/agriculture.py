"""
Agriculture Action Handler - Handles agent agricultural actions.

This handler manages all agriculture-related actions including:
- PLANT_CROPS: Planting crops in fields
- TEND_CROPS: Improving crop growth with irrigation and care
- HARVEST: Harvesting mature crops for food
- RAISE_ANIMALS: Domesticating and tending animals

These actions enable agents to develop sustainable food production and
advance from hunter-gatherer to agricultural civilization.
"""

from typing import TYPE_CHECKING
import logging

from engine.action_handlers import (
    ActionHandler,
    ActionResult,
    ActionContext,
    validate_agent_alive,
    validate_agent_energy,
    combine_validations,
)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)


class AgricultureHandler(ActionHandler):
    """
    Handles agricultural actions for agents.

    This handler processes PLANT_CROPS, TEND_CROPS, HARVEST, and RAISE_ANIMALS
    actions by delegating to the agriculture system.

    Action Details:

    PLANT_CROPS:
    - Creates crop field at agent's location
    - Consumes seeds from inventory
    - Defaults to wheat (basic crop)
    - Satisfies achievement need (0.15)
    - Requires seeds in inventory

    TEND_CROPS:
    - Improves crop growth and prevents disease
    - Can add irrigation if agent has wood
    - Satisfies resource need (0.1)
    - Requires agent to have a farm with fields

    HARVEST:
    - Harvests ready crops (up to 3 fields per action)
    - Adds food to inventory
    - Removes harvested fields
    - Satisfies achievement (0.3) and resource (0.2) needs
    - Requires harvestable crops

    RAISE_ANIMALS:
    - Domesticates new animals (chickens, pigs, cows)
    - Collects animal products (eggs, milk, wool)
    - Creates farm if agent doesn't have one
    - Limit of 10 animals per agent
    - Satisfies achievement need (0.2)

    Validation Requirements:
    - Agent must be alive for all actions
    - Agent must have sufficient energy (minimum 10%)
    - PLANT_CROPS: Requires seeds in inventory
    - TEND_CROPS: Requires farm with fields
    - HARVEST: Requires harvestable crops
    - RAISE_ANIMALS: No specific requirements (creates farm if needed)

    Examples:
        >>> handler = AgricultureHandler(context)
        >>> action = Action(ActionType.PLANT_CROPS)
        >>> result = handler.execute(agent, action)
        >>> print(result.success)  # True if crops planted

        >>> action = Action(ActionType.HARVEST)
        >>> result = handler.execute(agent, action)
        >>> print(result.metadata.get('food_gained'))  # Food harvested
    """

    # Minimum energy required for agriculture (as fraction 0-1)
    MIN_ENERGY_FOR_AGRICULTURE = 0.1

    def can_handle(self, action_type: ActionType) -> bool:
        """
        Check if this handler can process the given action type.

        Args:
            action_type: The type of action to check

        Returns:
            True if action_type is any agriculture action, False otherwise
        """
        return action_type in [
            ActionType.PLANT_CROPS,
            ActionType.TEND_CROPS,
            ActionType.HARVEST,
            ActionType.RAISE_ANIMALS
        ]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        """
        Validate if the agent can perform the agricultural action.

        Checks:
        1. Agent is alive (all actions)
        2. Agent has sufficient energy (at least 10%)
        3. PLANT_CROPS: Has seeds in inventory
        4. TEND_CROPS: Has farm with fields
        5. HARVEST: Has harvestable crops

        Args:
            agent: The agent attempting the action
            action: The agricultural action to validate

        Returns:
            Tuple of (can_execute, reason):
            - (True, "") if validation passes
            - (False, reason_string) if validation fails

        Examples:
            >>> can_execute, reason = handler.validate(agent, action)
            >>> if not can_execute:
            ...     print(f"Cannot farm: {reason}")
        """
        # Check if agent is alive
        alive_valid = validate_agent_alive(agent)

        # Check if agent has sufficient energy
        energy_valid = validate_agent_energy(agent, self.MIN_ENERGY_FOR_AGRICULTURE)

        # Combine basic validations
        basic_validation = combine_validations(alive_valid, energy_valid)
        if not basic_validation[0]:
            return basic_validation

        # Action-specific validation
        if action.action_type == ActionType.PLANT_CROPS:
            if not agent.inventory.has_item('seeds'):
                return False, "No seeds to plant"

        elif action.action_type == ActionType.TEND_CROPS:
            agriculture = self.context.get_system('agriculture')
            if not agriculture:
                return False, "Agriculture system not available"

            farm = agriculture.get_agent_farm(agent.id)
            if not farm or len(farm.fields) == 0:
                return False, "No crops to tend"

        elif action.action_type == ActionType.HARVEST:
            agriculture = self.context.get_system('agriculture')
            if not agriculture:
                return False, "Agriculture system not available"

            harvestable = agriculture.get_harvestable_crops(agent.id)
            if not harvestable:
                return False, "No crops ready to harvest"

        # RAISE_ANIMALS has no specific validation requirements
        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        """
        Execute the agricultural action.

        Delegates to the agriculture system for crop and animal management.

        PLANT_CROPS Algorithm:
        1. Choose crop type (default wheat)
        2. Plant crop at agent's location
        3. Consume seeds from inventory
        4. Satisfy achievement need

        TEND_CROPS Algorithm:
        1. Get agent's farm
        2. Add irrigation if has wood
        3. Satisfy resource need

        HARVEST Algorithm:
        1. Get harvestable crops
        2. Harvest up to 3 fields
        3. Add food to inventory
        4. Remove harvested fields
        5. Satisfy achievement and resource needs

        RAISE_ANIMALS Algorithm:
        1. Create farm if needed
        2. Domesticate new animal if under limit (10)
        3. Collect products from existing animals
        4. Satisfy achievement need

        Args:
            agent: The agent performing the action
            action: The agricultural action to execute

        Returns:
            ActionResult with:
            - success: True if action completed successfully
            - emotional_impact: Emotional effect (varies by action)
            - message: Description of what occurred
            - metadata: Action-specific details

        Examples:
            >>> action = Action(ActionType.PLANT_CROPS)
            >>> result = handler.execute(agent, action)
            >>> print(result.message)  # "Planted wheat"
        """
        from world.agriculture import CropType, AnimalType

        agriculture = self.context.get_system('agriculture')
        if not agriculture:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message="Agriculture system not available"
            )

        current_tick = self.context.current_tick

        if action.action_type == ActionType.PLANT_CROPS:
            # Choose crop type (default wheat)
            crop_type = CropType.WHEAT

            # Plant the crop
            field = agriculture.plant_crop(
                agent.id,
                crop_type,
                (agent.location.x, agent.location.y),
                current_tick
            )

            if field:
                # Consume seeds
                if agent.inventory.has_item('seeds'):
                    agent.inventory.remove_item('seeds', 1)

                logger.info(f"🌱 {agent.name} planted {crop_type.value} field")
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.15)

                return ActionResult(
                    success=True,
                    emotional_impact=0.2,
                    message=f'Planted {crop_type.value}',
                    metadata={
                        'action_type': 'plant_crops',
                        'crop_type': crop_type.value,
                        'field_id': field.id if hasattr(field, 'id') else None
                    }
                )
            else:
                return ActionResult(
                    success=False,
                    emotional_impact=0.0,
                    message='Could not plant crop',
                    metadata={'action_type': 'plant_crops'}
                )

        elif action.action_type == ActionType.TEND_CROPS:
            farm = agriculture.get_agent_farm(agent.id)

            if farm and len(farm.fields) > 0:
                # Improve irrigation if possible
                if not farm.has_irrigation and agent.inventory.has_item('wood'):
                    farm.has_irrigation = True
                    agent.inventory.remove_item('wood', 1)
                    logger.info(f"💧 {agent.name} added irrigation to farm!")
                    message = 'Added irrigation to farm'
                    emotional_impact = 0.15
                else:
                    message = 'Tended crops'
                    emotional_impact = 0.1

                agent.needs.satisfy_need(NeedType.RESOURCES, 0.1)

                return ActionResult(
                    success=True,
                    emotional_impact=emotional_impact,
                    message=message,
                    metadata={
                        'action_type': 'tend_crops',
                        'has_irrigation': farm.has_irrigation
                    }
                )
            else:
                return ActionResult(
                    success=False,
                    emotional_impact=0.0,
                    message='No crops to tend',
                    metadata={'action_type': 'tend_crops'}
                )

        elif action.action_type == ActionType.HARVEST:
            harvestable = agriculture.get_harvestable_crops(agent.id)

            if harvestable:
                total_food = 0
                harvested_count = 0

                for field in harvestable[:3]:  # Harvest up to 3 fields
                    food_yield = agriculture.harvest_crop(field.id, agent.id)
                    total_food += food_yield
                    harvested_count += 1

                    # Remove the field after harvest
                    farm = agriculture.get_agent_farm(agent.id)
                    if farm and field.id in farm.fields:
                        farm.fields.remove(field.id)

                # Add food to inventory
                agent.inventory.add_item('food', total_food)

                logger.info(f"🌾 {agent.name} harvested {total_food} food from {harvested_count} fields")
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
                agent.needs.satisfy_need(NeedType.RESOURCES, 0.2)

                return ActionResult(
                    success=True,
                    emotional_impact=0.3,
                    message=f'Harvested {total_food} food from {harvested_count} fields',
                    metadata={
                        'action_type': 'harvest',
                        'food_gained': total_food,
                        'fields_harvested': harvested_count
                    }
                )
            else:
                return ActionResult(
                    success=False,
                    emotional_impact=-0.05,
                    message='No crops ready to harvest',
                    metadata={'action_type': 'harvest'}
                )

        elif action.action_type == ActionType.RAISE_ANIMALS:
            farm = agriculture.get_agent_farm(agent.id)
            if not farm:
                # Create farm first
                farm = agriculture.create_farm(
                    agent.id,
                    agent.name,
                    (agent.location.x, agent.location.y)
                )

            # Check if agent has animals already
            agent_animals = agriculture.get_agent_animals(agent.id)

            if len(agent_animals) < 10:  # Limit to 10 animals
                # Domesticate a new animal
                animal_type = AnimalType.CHICKEN if len(agent_animals) < 3 else AnimalType.PIG

                animal = agriculture.domesticate_animal(agent.id, animal_type, current_tick)

                if animal:
                    logger.info(f"🐓 {agent.name} domesticated a {animal_type.value}!")
                    agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.2)

                    return ActionResult(
                        success=True,
                        emotional_impact=0.25,
                        message=f'Domesticated a {animal_type.value}',
                        metadata={
                            'action_type': 'raise_animals',
                            'animal': animal_type.value
                        }
                    )
            else:
                # Tend to existing animals (collect products)
                products_collected = 0
                for animal in agent_animals:
                    if animal.produces_material and current_tick - animal.last_production >= animal.production_rate:
                        # Collect production (eggs, milk, wool, etc.)
                        agent.inventory.add_item(animal.produces_material, 1)
                        animal.last_production = current_tick
                        products_collected += 1
                        logger.info(f"🥚 {agent.name} collected {animal.produces_material} from {animal.animal_type.value}")

                if products_collected > 0:
                    return ActionResult(
                        success=True,
                        emotional_impact=0.15,
                        message=f'Collected {products_collected} animal products',
                        metadata={
                            'action_type': 'raise_animals',
                            'products_collected': products_collected
                        }
                    )
                else:
                    return ActionResult(
                        success=True,
                        emotional_impact=0.1,
                        message='Tended animals',
                        metadata={'action_type': 'raise_animals'}
                    )

            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message='Animal raising failed',
                metadata={'action_type': 'raise_animals'}
            )

        # Should never reach here
        return ActionResult(
            success=False,
            emotional_impact=0.0,
            message=f"Unknown agriculture action: {action.action_type.value}",
            metadata={'action_type': action.action_type.value}
        )

    def get_required_systems(self) -> list[str]:
        """
        Return list of required system dependencies.

        Agriculture handler requires:
        - world: For basic world access
        - agriculture: For all agricultural operations

        Returns:
            List of required system attribute names
        """
        return ['world', 'agriculture']
