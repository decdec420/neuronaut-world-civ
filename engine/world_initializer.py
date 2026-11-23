"""
World Initializer - World and Agent Creation

This module handles ONLY world initialization:
- Creating initial world state
- Creating agents with proper setup
- Setting up starting resources

Extracted from simulation.py to enforce Single Responsibility Principle.
"""

import logging
import random
from typing import Optional, TYPE_CHECKING

from agents.agent import Agent, Gender, Position
from engine.events import EventGenerator, EventCategory, EventImportance

if TYPE_CHECKING:
    from engine.simulation import SimulationEngine

logger = logging.getLogger(__name__)


class WorldInitializer:
    """
    Initializes world and creates agents.

    Responsibilities:
    - Initialize world with starting population
    - Create individual agents
    - Set up starting resources and positions
    """

    def __init__(self, simulation: 'SimulationEngine'):
        """
        Initialize world initializer.

        Args:
            simulation: Reference to main simulation engine
        """
        self.sim = simulation

    def initialize_world(self, num_agents: int = 50):
        """
        Initialize world with starting population.

        Creates initial agents with:
        - Balanced genders (50/50 split)
        - Random ages (18-40)
        - Random starting positions
        - Starting resources (no wealth, basic materials)
        - Life profiles for reproduction

        Args:
            num_agents: Number of starting agents to create
        """
        print(f"Initializing Neuronaut World with {num_agents} agents...")
        Agent.reset_names()  # a new world: every name is free again

        # Create initial agents with balanced genders
        num_male = num_agents // 2
        num_female = num_agents - num_male

        for i in range(num_agents):
            # First half male, second half female
            gender = Gender.MALE if i < num_male else Gender.FEMALE
            agent = self.create_agent(
                name=None,  # Random name
                age=random.randint(18, 40),
                gender=gender
            )
            # Birthdays spread through the year (life/aging.py)
            agent.age_ticks = random.randrange(self.sim.config.ticks_per_life_year)

            # A random starting place on the mainland (never in a lake)
            agent.location = self.sim.world.map.random_mainland_position()

            # Give starting resources
            # NO FREE WEALTH - This is a survival world! Must discover economy from scratch.
            # Agents must earn wealth through: trading, gambling, or discovering coin minting!
            agent.wealth = 0.0
            print(f"🆕 Created {agent.name} with wealth: {agent.wealth} (ZERO WEALTH MODE)")
            agent.inventory.add_item('food', random.randint(3, 8))
            agent.inventory.add_item('water', random.randint(3, 8))

            # Give basic materials for experimentation!
            agent.inventory.add_item('wood', random.randint(5, 15))
            agent.inventory.add_item('stone', random.randint(3, 10))
            agent.inventory.add_item('plant_fiber', random.randint(2, 8))
            # Give some metal ore so they can discover smelting → minting → coin creation!
            agent.inventory.add_item('metal_ore', random.randint(2, 5))

            self.sim.world.agents.append(agent)

            # Create life profile for the agent - enables reproduction!
            personality_dict = {
                'openness': agent.personality.openness,
                'conscientiousness': agent.personality.conscientiousness,
                'extraversion': agent.personality.extraversion,
                'agreeableness': agent.personality.agreeableness,
                'neuroticism': agent.personality.neuroticism,
            }
            self.sim.life_system.create_life_profile(
                agent.id,
                personality_dict,
                parents=None,  # First generation has no parents
                inherited_wealth=0.0
            )

            # Log birth
            title, desc = EventGenerator.agent_born(
                agent.name,
                {'x': agent.location.x, 'y': agent.location.y}
            )
            self.sim.event_logger.log_event(
                EventCategory.LIFE,
                EventImportance.MINOR,
                title, desc,
                0,
                [agent.id],
                {'x': agent.location.x, 'y': agent.location.y}
            )

        print(f"✓ Created {num_agents} agents")
        print(f"✓ World initialized")

        # Rebuild agent cache for O(1) lookups
        self.sim._rebuild_agent_cache()
        print(f"✓ Agent cache built ({self.sim._agent_helper.get_cache_size()} agents indexed)")

        print(f"✓ Neuronaut World is ready!")

    def create_agent(
        self,
        name: Optional[str] = None,
        age: int = 20,
        is_player: bool = False,
        gender: Optional[Gender] = None,
        personality=None
    ) -> Agent:
        """
        Create a new agent with proper setup.

        Sets up:
        - Basic agent properties
        - Value learning system
        - Autonomous AI capabilities (if enabled)
        - Tracking counters

        Args:
            name: Agent name (None for random)
            age: Agent age in years
            is_player: Whether this is a player-controlled agent
            gender: Agent gender (None for random)

        Returns:
            Newly created Agent instance
        """
        agent = Agent(
            name=name,
            age=age,
            is_player=is_player,
            gender=gender,
            personality=personality
        )

        # Initialize value learning system with current market prices
        # Agents start with vague, personality-influenced estimates
        agent.initialize_value_estimates(self.sim.economy.market.item_prices)

        # ===== ADD AUTONOMOUS AI CAPABILITIES =====
        # Dynamically add autonomous methods to agent if LLM is enabled
        if self.sim.config.use_llm_decisions:
            from agents.autonomous_agent import bind_autonomous_methods
            bind_autonomous_methods(agent, llm_brain=self.sim.llm_brain)

            # Track last planning/reflection tick (used in simulation loop)
            agent.last_planning_tick = 0
            agent.last_reflection_tick = 0

        self.sim.total_agents_created += 1
        return agent
