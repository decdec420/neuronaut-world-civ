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

    def deliver_baby(self, mother: Agent, current_tick: int) -> Agent:
        """A pregnancy comes to term: the one way a child enters the world.

        The child blends both parents' personalities (plus a little variation;
        only the mother's if the father is gone), starts as a baby beside its
        mother, and has family ties to both parents. (There used to be two
        birth paths: an instant one on a successful romance, and one that
        made the baby twice and threw the father's traits away.)
        """
        import random
        from agents.agent import Gender
        from social.relationships import RelationshipType
        father = self.sim._get_agent_by_id(mother.pregnancy_partner_id) if mother.pregnancy_partner_id else None
        personality = mother._create_inherited_personality(father.personality if father else None)
        child = self.sim.create_agent(name=None, age=0, gender=random.choice([Gender.MALE, Gender.FEMALE]),
                                      personality=personality)
        child.location = Position(mother.location.x, mother.location.y)
        child.mother_id = mother.id
        child.father_id = father.id if father else None
        child.generation = 1 + max(getattr(mother, 'generation', 1), getattr(father, 'generation', 1) if father else 0)
        # Born knowing only what comes with being human; it learns from the
        # people around it (world/knowhow.py). In a settlers' world, everything.
        ledger = getattr(self.sim, 'knowhow', None)
        child.knowhow = set() if ledger is not None and ledger.active else None
        child.life_stage = "baby"
        self.sim.world.agents.append(child)

        mother.is_pregnant = False
        mother.pregnancy_partner_id = None
        mother.pregnancy_start_tick = 0
        parents = [p for p in (mother, father) if p is not None]
        rm = self.sim.relationship_manager
        for parent in parents:
            parent.children_ids.append(child.id)
            rel = rm.create_relationship(parent.id, child.id, RelationshipType.FAMILY, 0.8)
            rel.relationship_type = RelationshipType.FAMILY
            profile = self.sim.life_system.life_profiles.get(parent.id)
            if profile is not None:
                profile.children.append(child.id)
                profile.children_born += 1
        self.sim.life_system.create_life_profile(
            child.id,
            {t: getattr(personality, t) for t in ('openness', 'conscientiousness', 'extraversion',
                                                  'agreeableness', 'neuroticism')},
            parents=[p.id for p in parents])

        from life import homes
        mother_home = homes.home_of(self.sim.dynamic_building_system, mother)
        if mother_home is not None:
            homes.move_in(self.sim.dynamic_building_system, child, mother_home, current_tick, "born here",
                          self.sim.life_events)
        self.sim.births_this_day += 1
        self.sim.life_events['born'] += 1
        father_name = father.name if father else "a father who is gone"
        self.sim.event_logger.log_event(
            EventCategory.LIFE, EventImportance.MAJOR, f"👶 {child.name} is born",
            f"{mother.name} and {father_name} have a child, {child.name}.",
            current_tick, [p.id for p in parents] + [child.id])

        current_day = current_tick // 144
        birth_story = self.sim.story_generator.generate_birth_story(
            child.name, mother.name, father_name, current_day,
            {'mother_id': mother.id, 'father_id': child.father_id,
             'population': sum(1 for a in self.sim.world.agents if a.alive), 'generation': child.generation})
        self.sim.story_feed.add_story(birth_story)

        from engine.achievements import AchievementType
        tracker = self.sim.achievement_tracker
        tracker.track_agent(child.id, child.name)
        for parent in parents:
            tracker.track_agent(parent.id, parent.name)
            tracker.update_agent_stat(parent.id, 'children_count', len(parent.children_ids))
            tracker.check_agent_achievements(parent.id, current_day)
        tracker.unlock_civilization_achievement(AchievementType.FIRST_BIRTH, current_day)
        logger.info(f"👶 {mother.name} and {father_name} → {child.name}")
        return child

    def update_aging(self, current_tick: int) -> None:
        """Birthdays, life stages and death of old age (life/aging.py)."""
        import random
        from life import aging
        ticks_per_year = self.sim.config.ticks_per_life_year
        for agent in self.sim.world.agents:
            if not agent.alive:
                continue
            agent.age_ticks += 1
            if agent.age_ticks >= ticks_per_year:
                agent.age_ticks = 0
                agent.age += 1
                self.sim.life_system.update_life_stage(agent.id, agent.age)
                stage = aging.life_stage(agent.age)
                if stage != agent.life_stage:
                    self._stage_changed(agent, stage, current_tick)
            risk = aging.yearly_old_age_risk(agent.age)
            if risk and random.random() < risk / ticks_per_year:
                agent.alive = False
                agent.health = 0.0
                agent.death_cause = "old age"
                agent.death_tick = current_tick

    def _stage_changed(self, agent: Agent, stage: str, current_tick: int) -> None:
        agent.life_stage = stage
        self.sim.life_events[f"became_{stage}"] += 1
        if stage == "adult":
            title, importance = f"🎓 {agent.name} has come of age", EventImportance.MODERATE
        elif stage == "elder":
            title, importance = f"{agent.name} is now an elder", EventImportance.MINOR
        else:
            return
        self.sim.event_logger.log_event(EventCategory.LIFE, importance, title,
                                        f"{agent.name} turned {agent.age}.", current_tick, [agent.id])

    def _widow(self, dead: Agent) -> None:
        """A partnership ends when one partner dies; the other grieves."""
        from engine.psychology import EmotionType
        partner = self.sim._get_agent_by_id(dead.partner_id)
        dead.partner_id = None
        if partner is None or partner.partner_id != dead.id:
            return
        partner.partner_id = None
        # A wish for a child was a wish for one with this partner (reported in
        # review: it could carry over to a new partner who never heard it)
        partner.child_wish_tick = dead.child_wish_tick = None
        profile = self.sim.life_system.life_profiles.get(partner.id)
        if profile is not None:
            profile.spouse = None
        partner.emotions.trigger_emotion(EmotionType.SADNESS, 0.8)
        self.sim.event_logger.log_event(
            EventCategory.LIFE, EventImportance.MODERATE,
            f"{partner.name} lost their partner {dead.name}",
            f"{partner.name} mourns {dead.name}.", self.sim.world.time.current_tick, [partner.id, dead.id])

    def _release_land(self) -> None:
        """The dead stop guarding, and their land is no one's (world/territory.py)."""
        territory = getattr(self.sim, 'territory', None)
        if territory is None:
            return
        alive = {a.id for a in self.sim.world.agents if a.alive}
        for name in territory.forget_the_dead(lambda agent_id: agent_id in alive):
            logger.info("🗺️  %s is no one's now: whoever held it has died", name)

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
            # Each death is counted, logged and mourned once. (This used to
            # re-log every dead agent every tick, and skip anyone who died in
            # their first 100 ticks.)
            if agent.alive or agent.death_recorded:
                continue
            agent.death_recorded = True
            if agent.death_tick is None:
                agent.death_tick = current_tick
            if agent.partner_id:
                self._widow(agent)
            self._release_land()
            death_cause = agent.death_cause or "unknown causes"
            agent.death_cause = death_cause

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
