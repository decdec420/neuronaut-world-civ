"""
Lifecycle Manager - Birth and Death Handler

This module handles ONLY lifecycle events:
- Agent births (reproduction)
- Agent deaths (removal and cleanup)

Extracted from simulation.py to enforce Single Responsibility Principle.
"""

import logging
from typing import Dict, TYPE_CHECKING

from agents.agent import Agent, Position
from engine.events import EventGenerator, EventCategory, EventImportance

if TYPE_CHECKING:
    from engine.simulation import SimulationEngine

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Manages agent lifecycle events: births and deaths.

    Responsibilities:
    - Handle birth of new agents (reproduction)
    - Create child agents with inherited traits
    - Handle agent deaths and cleanup
    - Track births/deaths for statistics
    """

    def __init__(self, simulation: 'SimulationEngine'):
        """
        Initialize lifecycle manager.

        Args:
            simulation: Reference to main simulation engine
        """
        self.sim = simulation

    def handle_birth(
        self,
        parent_a: Agent,
        parent_b: Agent,
        child_data: Dict,
        current_tick: int
    ):
        """
        Handle birth of new child agent.

        Creates the child, adds to world, inherits traits from parents.

        Args:
            parent_a: First parent agent
            parent_b: Second parent agent
            child_data: Dictionary containing child information from life_system
            current_tick: Current simulation tick
        """
        # Create child agent (starts at age 0)
        child = self.sim.create_agent(
            name=None,  # Will get random name
            age=0,  # Newborn!
            is_player=False
        )

        # Place child near parents
        child.location = Position(
            (parent_a.location.x + parent_b.location.x) / 2,
            (parent_a.location.y + parent_b.location.y) / 2
        )

        # Give child inherited wealth
        child.wealth = child_data.get('inherited_wealth', 0.0)

        # Add minimal starting items (babies don't have much!)
        child.inventory.add_item('food', 2)
        child.inventory.add_item('water', 2)

        # Add to world
        self.sim.world.agents.append(child)

        # Create life profile with parents
        personality_dict = {
            'openness': child.personality.openness,
            'conscientiousness': child.personality.conscientiousness,
            'extraversion': child.personality.extraversion,
            'agreeableness': child.personality.agreeableness,
            'neuroticism': child.personality.neuroticism,
        }
        self.sim.life_system.create_life_profile(
            child.id,
            personality_dict,
            parents=child_data.get('parents', []),
            inherited_wealth=child_data.get('inherited_wealth', 0.0)
        )

        # Log birth event!
        title = f"👶 {child.name} is born!"
        desc = f"{parent_a.name} and {parent_b.name} have a child! Welcome to the world, {child.name}. Generation {child_data.get('generation', 2)}."

        self.sim.event_logger.log_event(
            EventCategory.LIFE,
            EventImportance.MAJOR,
            title, desc,
            current_tick,
            [parent_a.id, parent_b.id, child.id]
        )

        print(f"\n👶 BIRTH! {parent_a.name} & {parent_b.name} → {child.name} (Gen {child_data.get('generation', 2)})")

        self.sim.total_agents_created += 1

        # Track birth for population history
        self.sim.births_this_day += 1

    def _widow(self, dead: Agent) -> None:
        """A partnership ends when one partner dies; the other grieves."""
        from engine.psychology import EmotionType
        partner = self.sim._get_agent_by_id(dead.partner_id)
        dead.partner_id = None
        if partner is None or partner.partner_id != dead.id:
            return
        partner.partner_id = None
        profile = self.sim.life_system.life_profiles.get(partner.id)
        if profile is not None:
            profile.spouse = None
        partner.emotions.trigger_emotion(EmotionType.SADNESS, 0.8)
        self.sim.event_logger.log_event(
            EventCategory.LIFE, EventImportance.MODERATE,
            f"{partner.name} lost their partner {dead.name}",
            f"{partner.name} mourns {dead.name}.", self.sim.world.time.current_tick, [partner.id, dead.id])

    def handle_deaths(self):
        """
        Process agent deaths and cleanup.

        - Tracks death causes for statistics
        - Logs death events
        - Generates death stories
        - Checks for achievements
        - Removes dead agents after delay
        """
        current_tick = self.sim.world.time.current_tick

        for agent in self.sim.world.agents[:]:  # Copy list
            if not agent.alive and agent.partner_id:
                self._widow(agent)
            if not agent.alive and agent.ticks_lived > 100:
                # Determine death cause from agent
                death_cause = getattr(agent, 'death_cause', None) or ("old age" if agent.age > 100 else "health")

                # Track death for population history
                self.sim.deaths_this_day += 1
                self.sim.death_causes[death_cause] = self.sim.death_causes.get(death_cause, 0) + 1

                # Log death if not already logged
                title, desc = EventGenerator.agent_died(
                    agent.name,
                    agent.age,
                    death_cause
                )
                self.sim.event_logger.log_event(
                    EventCategory.LIFE,
                    EventImportance.MODERATE,
                    title, desc,
                    current_tick,
                    [agent.id]
                )

                # ===== DEATH STORY - Create LEGENDARY memorial! =====
                current_day = current_tick // 144

                # Build legacy context for story
                legacy_context = {
                    'agent_id': agent.id,
                    'achievement_count': len(self.sim.achievement_tracker.agent_achievements.get(agent.id, []).achievements) if agent.id in self.sim.achievement_tracker.agent_achievements else 0,
                    'children_count': len(agent.children_ids),
                    'grandchildren_count': 0,  # TODO: Calculate
                    'buildings_built': getattr(agent, 'buildings_constructed', 0),
                    'discoveries': 0,  # TODO: Track
                    'wealth': agent.inventory.items.get('wealth', 0),
                    'birth_day': 0,  # TODO: Track
                    'generation': 1  # TODO: Track
                }

                death_story = self.sim.story_generator.generate_death_story(
                    agent.name, agent.age, death_cause, current_day, legacy_context
                )
                self.sim.story_feed.add_story(death_story)
                logger.info(f"💀 STORY: {death_story.title}")

                # ===== ACHIEVEMENTS - Final check =====
                # Update days survived for elder achievements
                if agent.id in self.sim.achievement_tracker.agent_achievements:
                    self.sim.achievement_tracker.update_agent_stat(agent.id, 'days_survived', agent.ticks_lived)
                    final_achievements = self.sim.achievement_tracker.check_agent_achievements(agent.id, current_day)
                    for ach in final_achievements:
                        logger.info(f"🏆 {agent.name} earned posthumous achievement: {ach.name}")

                # Civilization achievement - FIRST DEATH
                from engine.achievements import AchievementType
                first_death_ach = self.sim.achievement_tracker.unlock_civilization_achievement(
                    AchievementType.FIRST_DEATH, current_day
                )
                if first_death_ach:
                    logger.info(f"🎆 CIVILIZATION: {first_death_ach.name}")

                # Remove from world (after delay)
                # In production, would archive agent data
                # For now, keep in list as dead
