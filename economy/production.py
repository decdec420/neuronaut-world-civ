"""
Production Chains and Crafting System

Agents can:
- Craft complex items from simple resources
- Discover new recipes through experimentation
- Specialize in production
- Create supply chains

Production is agent-driven, not pre-scripted!
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime


@dataclass
class Recipe:
    """A recipe for crafting an item"""
    id: str
    name: str
    output_item: str
    output_quantity: int = 1

    # Inputs required
    inputs: Dict[str, int] = field(default_factory=dict)  # item -> quantity

    # Requirements
    required_skill: Optional[str] = None
    min_skill_level: float = 0.0
    required_tool: Optional[str] = None
    required_building: Optional[str] = None

    # Production
    production_time: int = 10  # Ticks
    skill_bonus_multiplier: float = 1.0  # Skilled crafters produce more

    # Discovery
    discovered_by: Optional[str] = None
    discovered_at: Optional[datetime] = None

    # Usage stats
    times_crafted: int = 0
    success_rate: float = 1.0

    def can_craft(self, agent: 'Agent', has_building: bool = False) -> Tuple[bool, str]:
        """Check if agent can craft this"""
        # Check inputs
        for item, qty in self.inputs.items():
            if not agent.inventory.has_item(item, qty):
                return False, f"Need {qty} {item}"

        # Check skill
        if self.required_skill:
            skill_level = agent.skills.get_skill(self.required_skill)
            if skill_level < self.min_skill_level:
                return False, f"Need {self.required_skill} skill {self.min_skill_level}"

        # Check tool
        if self.required_tool:
            if not agent.inventory.has_item(self.required_tool):
                return False, f"Need {self.required_tool}"

        # Check building
        if self.required_building and not has_building:
            return False, f"Need {self.required_building}"

        return True, "Can craft"

    def execute_craft(self, agent: 'Agent') -> Tuple[bool, str]:
        """Execute crafting"""
        can_craft, message = self.can_craft(agent)
        if not can_craft:
            return False, message

        # Remove inputs
        for item, qty in self.inputs.items():
            agent.inventory.remove_item(item, qty)

        # Calculate output (skill bonus)
        output_qty = self.output_quantity

        if self.required_skill:
            skill_level = agent.skills.get_skill(self.required_skill)
            bonus = skill_level * self.skill_bonus_multiplier
            output_qty = int(output_qty * (1.0 + bonus))

        # Add output
        success = agent.inventory.add_item(self.output_item, output_qty)

        if not success:
            # Inventory full, give items back
            for item, qty in self.inputs.items():
                agent.inventory.add_item(item, qty)
            return False, "Inventory full"

        # Stats
        self.times_crafted += 1

        # Learn skill
        if self.required_skill:
            agent.skills.learn_skill(self.required_skill, amount=0.05)

        return True, f"Crafted {output_qty} {self.output_item}"


# BASIC RECIPES (agents can discover more through experimentation)
BASE_RECIPES = {
    "wooden_plank": Recipe(
        id="wooden_plank",
        name="Wooden Plank",
        output_item="wooden_plank",
        output_quantity=4,
        inputs={"wood": 1},
        production_time=5
    ),

    "stone_tool": Recipe(
        id="stone_tool",
        name="Stone Tool",
        output_item="stone_tool",
        output_quantity=1,
        inputs={"stone": 2, "wood": 1},
        required_skill="crafting",
        min_skill_level=0.1,
        production_time=10
    ),

    "rope": Recipe(
        id="rope",
        name="Rope",
        output_item="rope",
        output_quantity=2,
        inputs={"plant_fiber": 3},
        required_skill="weaving",
        min_skill_level=0.1,
        production_time=8
    ),

    "bread": Recipe(
        id="bread",
        name="Bread",
        output_item="bread",
        output_quantity=2,
        inputs={"wheat": 2},
        required_skill="cooking",
        min_skill_level=0.2,
        production_time=15
    ),

    "cooked_meat": Recipe(
        id="cooked_meat",
        name="Cooked Meat",
        output_item="cooked_meat",
        output_quantity=1,
        inputs={"raw_meat": 1, "wood": 1},
        required_skill="cooking",
        min_skill_level=0.1,
        production_time=10
    ),

    "clay_pot": Recipe(
        id="clay_pot",
        name="Clay Pot",
        output_item="clay_pot",
        output_quantity=1,
        inputs={"clay": 3},
        required_skill="pottery",
        min_skill_level=0.3,
        required_building="pottery_shop",
        production_time=20
    ),

    "iron_ingot": Recipe(
        id="iron_ingot",
        name="Iron Ingot",
        output_item="iron_ingot",
        output_quantity=1,
        inputs={"iron_ore": 2, "wood": 1},
        required_skill="metalworking",
        min_skill_level=0.4,
        required_building="smithy",
        production_time=30
    ),

    "iron_sword": Recipe(
        id="iron_sword",
        name="Iron Sword",
        output_item="iron_sword",
        output_quantity=1,
        inputs={"iron_ingot": 3, "wood": 1},
        required_skill="metalworking",
        min_skill_level=0.5,
        required_building="smithy",
        required_tool="hammer",
        production_time=40
    ),

    "leather_armor": Recipe(
        id="leather_armor",
        name="Leather Armor",
        output_item="leather_armor",
        output_quantity=1,
        inputs={"leather": 5, "rope": 2},
        required_skill="leatherworking",
        min_skill_level=0.4,
        production_time=35
    ),
}


class ProductionManager:
    """Manages recipes and crafting"""

    def __init__(self):
        # All known recipes
        self.recipes: Dict[str, Recipe] = BASE_RECIPES.copy()

        # Agent specializations (what they focus on producing)
        self.agent_specializations: Dict[str, Set[str]] = {}  # agent_id -> recipe IDs

        # Production queues (for automated production)
        self.production_queues: Dict[str, List[str]] = {}  # agent_id -> recipe IDs

    def discover_recipe(
        self,
        agent_id: str,
        agent_name: str,
        inputs: Dict[str, int],
        output: str,
        context: Dict
    ) -> Recipe:
        """
        Agent discovers a new recipe through experimentation

        This happens when agents try combining items creatively
        """
        recipe_id = str(uuid.uuid4())

        recipe = Recipe(
            id=recipe_id,
            name=f"{output.replace('_', ' ').title()}",
            output_item=output,
            output_quantity=1,
            inputs=inputs,
            discovered_by=agent_id,
            discovered_at=datetime.now()
        )

        # Determine requirements based on context
        if 'skill_used' in context:
            recipe.required_skill = context['skill_used']
            recipe.min_skill_level = 0.2

        if 'building_used' in context:
            recipe.required_building = context['building_used']

        self.recipes[recipe_id] = recipe

        return recipe

    def craft_item(
        self,
        agent: 'Agent',
        recipe_id: str,
        has_building: bool = False
    ) -> Tuple[bool, str]:
        """Agent crafts an item"""
        if recipe_id not in self.recipes:
            return False, "Unknown recipe"

        recipe = self.recipes[recipe_id]

        return recipe.execute_craft(agent)

    def agent_specializes(self, agent_id: str, recipe_id: str):
        """Agent specializes in producing something"""
        if agent_id not in self.agent_specializations:
            self.agent_specializations[agent_id] = set()

        self.agent_specializations[agent_id].add(recipe_id)

    def get_craftable_recipes(self, agent: 'Agent') -> List[Recipe]:
        """Get recipes agent can craft right now"""
        craftable = []

        for recipe in self.recipes.values():
            can_craft, _ = recipe.can_craft(agent)
            if can_craft:
                craftable.append(recipe)

        return craftable

    def get_learnable_recipes(self, agent: 'Agent') -> List[Recipe]:
        """Get recipes agent could learn (has materials but not skill/tool)"""
        learnable = []

        for recipe in self.recipes.values():
            # Has materials?
            has_materials = all(
                agent.inventory.has_item(item, qty)
                for item, qty in recipe.inputs.items()
            )

            if not has_materials:
                continue

            # Can't craft due to skill/tool?
            can_craft, reason = recipe.can_craft(agent)
            if not can_craft and ('skill' in reason.lower() or 'tool' in reason.lower()):
                learnable.append(recipe)

        return learnable

    def add_to_queue(self, agent_id: str, recipe_id: str):
        """Add recipe to agent's production queue"""
        if agent_id not in self.production_queues:
            self.production_queues[agent_id] = []

        self.production_queues[agent_id].append(recipe_id)

    def process_production_queue(
        self,
        agent: 'Agent',
        has_building: bool = False
    ) -> List[Tuple[bool, str]]:
        """Process agent's production queue"""
        if agent.id not in self.production_queues:
            return []

        queue = self.production_queues[agent.id]
        results = []

        # Process up to 3 items per tick
        for _ in range(min(3, len(queue))):
            if not queue:
                break

            recipe_id = queue.pop(0)
            success, message = self.craft_item(agent, recipe_id, has_building)
            results.append((success, message))

            if not success:
                # Failed, add back to queue
                queue.insert(0, recipe_id)
                break

        return results

    def get_statistics(self) -> Dict:
        """Get production statistics"""
        total_recipes = len(self.recipes)
        discovered_recipes = sum(
            1 for r in self.recipes.values()
            if r.discovered_by is not None
        )

        total_crafted = sum(r.times_crafted for r in self.recipes.values())

        most_popular = sorted(
            self.recipes.values(),
            key=lambda r: r.times_crafted,
            reverse=True
        )[:10]

        return {
            'total_recipes': total_recipes,
            'base_recipes': len(BASE_RECIPES),
            'discovered_recipes': discovered_recipes,
            'total_items_crafted': total_crafted,
            'specialized_agents': len(self.agent_specializations),
            'most_popular_recipes': [
                {
                    'name': r.name,
                    'times_crafted': r.times_crafted,
                    'success_rate': r.success_rate,
                }
                for r in most_popular
            ],
        }
