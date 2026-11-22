"""
Statistics Exporter - Data Aggregation and Reporting

This module handles ONLY statistics and state snapshots:
- Population statistics
- State snapshots for frontend
- Population history tracking

Extracted from simulation.py to enforce Single Responsibility Principle.
"""

import logging
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.simulation import SimulationEngine

logger = logging.getLogger(__name__)


class StatisticsExporter:
    """
    Exports statistics and state snapshots.

    Responsibilities:
    - Generate population statistics
    - Create complete state snapshots
    - Track population history
    """

    def __init__(self, simulation: 'SimulationEngine'):
        """
        Initialize statistics exporter.

        Args:
            simulation: Reference to main simulation engine
        """
        self.sim = simulation

    def get_population_statistics(self) -> Dict:
        """
        Get comprehensive population statistics for frontend display.

        Returns:
            Dictionary containing:
            - current_population: Number of alive agents
            - total_agents_created: Total agents ever created
            - total_deaths: Total deaths
            - births_today: Births in current day
            - deaths_today: Deaths in current day
            - age_distribution: Distribution across age groups
            - death_causes: Breakdown of death causes
            - history: Recent population history
        """
        alive_agents = [a for a in self.sim.world.agents if a.alive]
        alive_count = len(alive_agents)

        # Calculate age distribution
        age_groups = {
            '0-20': 0,
            '21-40': 0,
            '41-60': 0,
            '61-80': 0,
            '81-100': 0,
            '100+': 0
        }

        for agent in alive_agents:
            if agent.age <= 20:
                age_groups['0-20'] += 1
            elif agent.age <= 40:
                age_groups['21-40'] += 1
            elif agent.age <= 60:
                age_groups['41-60'] += 1
            elif agent.age <= 80:
                age_groups['61-80'] += 1
            elif agent.age <= 100:
                age_groups['81-100'] += 1
            else:
                age_groups['100+'] += 1

        # Calculate total deaths and causes
        all_death_causes = {}
        for snapshot in self.sim.population_history:
            for cause, count in snapshot.get('death_causes', {}).items():
                all_death_causes[cause] = all_death_causes.get(cause, 0) + count

        return {
            'current_population': alive_count,
            'total_agents_created': self.sim.total_agents_created,
            'total_deaths': self.sim.total_agents_created - alive_count,
            'births_today': self.sim.births_this_day,
            'deaths_today': self.sim.deaths_this_day,
            'age_distribution': age_groups,
            'death_causes': all_death_causes,
            'history': list(self.sim.population_history)[-100:],  # Last 100 days
        }

    def get_state_snapshot(self) -> Dict:
        """
        Get complete world state snapshot.

        Returns comprehensive state of entire simulation including:
        - World state (resources, time, etc.)
        - All agents
        - Economic system (wealth, market, banking, etc.)
        - All game systems (buildings, knowledge, etc.)
        - Events and stories
        - Population statistics
        """
        # Get comprehensive economic stats (includes wealth, market, banking, taxation, trade, crises, etc.)
        economic_stats = self.sim.economy.get_complete_statistics()

        return {
            'world': self.sim.world.get_statistics(),
            'agents': [agent.to_dict() for agent in self.sim.world.agents if agent.alive],
            'infrastructure': self.sim.infrastructure.to_dict(),
            # COMPLETE ECONOMIC SYSTEM - All financial subsystems!
            'economy': economic_stats.get('wealth', {}),  # Backward compatibility
            'market': economic_stats.get('market', {}),  # Backward compatibility
            'economic_system': economic_stats,  # NEW: Complete economic data
            'events': self.sim.event_logger.get_statistics(),
            'recent_events': [e.to_dict() for e in self.sim.event_logger.get_recent_events(20)],
            # OLD SYSTEMS DATA (kept for compatibility)
            'buildings': self.sim.building_manager.get_statistics(),
            'innovations': self.sim.innovation_manager.get_statistics(),
            'warfare': self.sim.warfare_manager.get_statistics(),
            'governance': self.sim.governance_manager.get_statistics(),
            'production': self.sim.production_manager.get_statistics(),
            'strategy': self.sim.strategy_manager.get_statistics(),
            # NEW AUTONOMOUS SYSTEMS
            'experimentation': self.sim.experimentation_engine.get_statistics(),
            'dynamic_buildings': self.sim.dynamic_building_system.get_statistics(),
            'knowledge': self.sim.knowledge_system.get_statistics(),
            'consequences': self.sim.consequence_engine.get_statistics(),
            'roles': self.sim.role_emergence.get_statistics(),
            'tech_progression': self.sim.tech_progression.get_statistics(),
            # CIVILIZATION PROGRESSION - Stone Age → Space Age!
            'civilization': self.sim.civilization.get_stats(),
            # STORY ENGINE & ACHIEVEMENTS - Epic narratives and milestones!
            'stories': self.sim.story_feed.to_dict(),
            'achievements': self.sim.achievement_tracker.to_dict(),
            # META-PROGRESSION - AI Self-Improvement!
            'meta_progression': self.sim.meta_progression.to_dict(),
            # POPULATION TRACKING - Births, deaths, demographics over time!
            'population': self.get_population_statistics(),
        }

    def update_population_history(self):
        """
        Track population changes over time for graphing.

        Records data once per day including:
        - Population count
        - Births and deaths
        - Death causes breakdown

        This data is used for frontend graphs and analytics.
        """
        current_tick = self.sim.world.time.current_tick
        current_day = self.sim.world.time.day

        # Only record once per day (when day changes)
        if current_day > self.sim.last_tracked_day:
            alive_count = sum(1 for a in self.sim.world.agents if a.alive)

            # Record population snapshot for this day
            population_snapshot = {
                'day': current_day,
                'tick': current_tick,
                'alive': alive_count,
                'births': self.sim.births_this_day,
                'deaths': self.sim.deaths_this_day,
                'total_created': self.sim.total_agents_created,
                'death_causes': self.sim.death_causes.copy()
            }

            self.sim.population_history.append(population_snapshot)

            # Log daily summary if there were births/deaths
            if self.sim.births_this_day > 0 or self.sim.deaths_this_day > 0:
                logger.info(
                    f"📊 Day {current_day}: Population={alive_count} "
                    f"(+{self.sim.births_this_day} births, -{self.sim.deaths_this_day} deaths)"
                )

            # Reset daily counters
            self.sim.births_this_day = 0
            self.sim.deaths_this_day = 0
            self.sim.death_causes = {}
            self.sim.last_tracked_day = current_day
