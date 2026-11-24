"""
System Coordinator - World Systems Management

This module handles ONLY system-level coordination:
- Natural disaster effects
- Civilization milestones
- Resource sinks (food spoilage, tool decay, etc.)

Extracted from simulation.py to enforce Single Responsibility Principle.
"""

import logging
import random
from typing import TYPE_CHECKING

from agents.agent import Agent
from engine.events import EventCategory, EventImportance
from engine.psychology import NeedType

if TYPE_CHECKING:
    from engine.simulation import SimulationEngine

logger = logging.getLogger(__name__)

# Agents within this distance of a standing building count as sheltered
# (the same radius AgentUpdater._apply_weather_effects uses for weather).
SHELTER_RADIUS = 6.0


class SystemCoordinator:
    """
    Coordinates system-level updates and effects.

    Responsibilities:
    - Apply disaster effects to world
    - Track civilization milestones
    - Apply resource sinks (spoilage, decay)
    """

    def __init__(self, simulation: 'SimulationEngine'):
        """
        Initialize system coordinator.

        Args:
            simulation: Reference to main simulation engine
        """
        self.sim = simulation

    def apply_disaster_to_world(self, disaster):
        """
        Apply disaster effects to buildings and agents in the affected area.

        Args:
            disaster: Disaster object from NaturalDisasterSystem
        """
        from world.disasters import Disaster

        # Get disaster effects
        effects = self.sim.disasters.get_disaster_effects(disaster)
        if not effects:
            return

        casualties = 0
        buildings_destroyed = 0
        buildings_damaged = 0
        agents_injured = 0

        # Apply effects to buildings
        for building in list(self.sim.building_manager.buildings.values()):  # Copy to allow removal
            if self.sim.disasters.is_location_affected(building.location.x, building.location.y, disaster):
                # Destruction check
                if random.random() < effects.building_destroy_chance:
                    # Building is completely destroyed
                    self.sim.building_manager.remove_building(building.id)
                    buildings_destroyed += 1
                    logger.info(f"{effects.emoji} Building {building.building_type.value} destroyed by {disaster.disaster_type.value}!")

                elif random.random() < effects.building_damage_chance:
                    # Building is damaged (reduce health if it exists)
                    if hasattr(building, 'health'):
                        building.health = max(0, building.health - 50)
                        buildings_damaged += 1
                        logger.info(f"{effects.emoji} Building {building.building_type.value} damaged by {disaster.disaster_type.value}!")

        # The buildings agents actually build live in dynamic_building_system; the
        # loop above only covers the legacy manager, so disasters never touched
        # them. Sturdier buildings (durability comes from their materials) are
        # less likely to be destroyed.
        dbs = getattr(self.sim, 'dynamic_building_system', None)
        durability_before = {}  # building id -> durability when the disaster hit
        if dbs is not None:
            for building in list(dbs.buildings.values()):
                if not building.is_complete or building.collapsed:
                    continue
                bx, by = building.location
                if not self.sim.disasters.is_location_affected(bx, by, disaster):
                    continue
                durability = max(0.0, min(1.0, building.durability))
                durability_before[building.id] = durability
                if random.random() < effects.building_destroy_chance * (1.0 - durability):
                    dbs.collapse_building(building.id, f"Destroyed by {disaster.disaster_type.value}")
                    buildings_destroyed += 1
                    self._release_building_purpose(dbs, building)
                    self.sim.event_logger.log_event(
                        EventCategory.ENVIRONMENTAL,
                        EventImportance.MODERATE,
                        f"{effects.emoji} {building.name} destroyed",
                        f"{building.name} collapsed in the {disaster.disaster_type.value}.",
                        self.sim.world.time.current_tick,
                        list(building.builder_ids),
                        {'x': bx, 'y': by}
                    )
                elif random.random() < effects.building_damage_chance:
                    # Same hit as the legacy buildings above: half of full strength
                    building.durability = max(0.0, building.durability - 0.5)
                    building.maintenance_needed = True
                    buildings_damaged += 1

        # Apply effects to agents
        for agent in self.sim.world.agents:
            if not agent.alive:
                continue

            if self.sim.disasters.is_location_affected(agent.location.x, agent.location.y, disaster):
                # Agents at a building that is still standing shelter in it: their
                # risk shrinks with the building's durability when the disaster hit.
                # Before, shelter made no difference, so one catastrophic quake
                # could kill 40% of a town standing next to stone houses.
                death_chance = effects.agent_death_chance
                shelter = dbs.standing_building_near(agent.location.x, agent.location.y, SHELTER_RADIUS) if dbs is not None else None
                if shelter is not None:
                    protection = durability_before.get(shelter.id, max(0.0, min(1.0, shelter.durability)))
                    death_chance *= 1.0 - protection

                # Death check
                if random.random() < death_chance:
                    agent.alive = False
                    agent.death_tick = self.sim.world.time.current_tick
                    agent.death_cause = f"{disaster.disaster_type.value}"
                    casualties += 1  # counted in death_causes by LifecycleManager.handle_deaths

                    logger.info(f"💀 {agent.name} killed by {disaster.disaster_type.value}!")

                    # Log death event
                    self.sim.event_logger.log_event(
                        EventCategory.LIFE,
                        EventImportance.MAJOR,
                        f"💀 {agent.name} killed by {disaster.disaster_type.value}",
                        f"{agent.name} perished in a {disaster.disaster_type.value}",
                        self.sim.world.time.current_tick,
                        [agent.id],
                        {'x': agent.location.x, 'y': agent.location.y}
                    )

                else:
                    # Apply damage
                    if effects.agent_damage > 0:
                        security_need = agent.needs.needs.get(NeedType.SECURITY)
                        if security_need:
                            security_need.level = min(
                                1.0,
                                security_need.level + (effects.agent_damage / 100.0)
                            )
                        agents_injured += 1

        # Destroy resources in the affected area
        if effects.resource_destruction > 0:
            for resource_type in ['food', 'water', 'wood', 'stone']:
                current = self.sim.world.resource_pools.get(resource_type, 0)
                destroyed = current * effects.resource_destruction * 0.1  # Scale down resource destruction
                self.sim.world.resource_pools[resource_type] = max(0, current - destroyed)

        # Update disaster statistics
        disaster.casualties = casualties
        disaster.buildings_destroyed = buildings_destroyed
        disaster.buildings_damaged = buildings_damaged
        disaster.agents_injured = agents_injured

        self.sim.disasters.total_casualties += casualties
        self.sim.disasters.total_buildings_destroyed += buildings_destroyed

        # Log disaster event
        self.sim.event_logger.log_event(
            EventCategory.ENVIRONMENTAL,
            EventImportance.MAJOR if casualties > 0 else EventImportance.MODERATE,
            f"{effects.emoji} {disaster.disaster_type.value.title()} strikes!",
            f"{effects.description} | Casualties: {casualties}, Buildings destroyed: {buildings_destroyed}, Injured: {agents_injured}",
            self.sim.world.time.current_tick,
            [],
            {'x': disaster.location_x, 'y': disaster.location_y}
        )

    def _release_building_purpose(self, dbs, building):
        """Let the builders of a destroyed building build that kind again.

        ConstructionHandler allows one building per purpose per agent
        (agent.built_purposes); without this, an agent whose home was destroyed
        could never rebuild it.
        """
        design = dbs.designs.get(building.design_id)
        if not design or not design.intended_purposes:
            return
        purpose = design.intended_purposes[0]
        for builder_id in building.builder_ids:
            builder = self.sim.get_agent_by_id(builder_id)
            if builder is not None and hasattr(builder, 'built_purposes'):
                builder.built_purposes.discard(purpose)

    def check_civilization_milestones(self, current_tick: int):
        """
        Check and record civilization milestones.

        Tracks:
        - Population milestones (10, 25, 50, 100, etc.)
        - Building milestones (1, 10, 50, 100, etc.)
        - Knowledge milestones (10, 50, 100, etc.)

        Args:
            current_tick: Current simulation tick
        """
        alive_agents = [a for a in self.sim.world.agents if a.alive]
        population = len(alive_agents)
        total_buildings = len(self.sim.dynamic_building_system.buildings)
        total_knowledge = len(self.sim.knowledge_system.knowledge_records)

        # Population milestones
        pop_milestones = [10, 25, 50, 100, 200, 500]
        for milestone in pop_milestones:
            milestone_key = f"pop_{milestone}"
            if population >= milestone and milestone_key not in self.sim.achieved_milestones:
                self.sim.achieved_milestones.add(milestone_key)
                self.sim.milestone_history.append({
                    "type": "population",
                    "milestone": f"{milestone} Synthetics",
                    "tick": current_tick,
                    "day": current_tick // 24,
                    "details": f"Population reached {population} living synthetics"
                })
                print(f"🎉 MILESTONE: Population reached {milestone}!")

        # Building milestones
        building_milestones = [1, 10, 50, 100, 250, 500]
        for milestone in building_milestones:
            milestone_key = f"buildings_{milestone}"
            if total_buildings >= milestone and milestone_key not in self.sim.achieved_milestones:
                self.sim.achieved_milestones.add(milestone_key)
                self.sim.milestone_history.append({
                    "type": "buildings",
                    "milestone": f"{milestone} Buildings",
                    "tick": current_tick,
                    "day": current_tick // 24,
                    "details": f"Civilization has constructed {total_buildings} buildings"
                })
                print(f"🏗️  MILESTONE: {milestone} buildings constructed!")

        # Knowledge milestones
        knowledge_milestones = [10, 50, 100, 250, 500, 1000]
        for milestone in knowledge_milestones:
            milestone_key = f"knowledge_{milestone}"
            if total_knowledge >= milestone and milestone_key not in self.sim.achieved_milestones:
                self.sim.achieved_milestones.add(milestone_key)
                self.sim.milestone_history.append({
                    "type": "knowledge",
                    "milestone": f"{milestone} Knowledge Records",
                    "tick": current_tick,
                    "day": current_tick // 24,
                    "details": f"Civilization has accumulated {total_knowledge} pieces of knowledge"
                })
                print(f"📚 MILESTONE: {milestone} knowledge records created!")

    def apply_resource_sinks(self, agent: Agent):
        """
        Apply resource sinks to prevent economic inflation.

        Based on survival game research:
        - Food spoilage (0.5% per tick)
        - Water evaporation (0.3% per tick)
        - Tool degradation (0.2% chance per tick)
        - Wealth decay (0.1% per tick)
        - Plant fiber decay (0.4% per tick)

        Args:
            agent: Agent to apply resource sinks to
        """
        from economy.materials import get_material

        # 1. FOOD SPOILAGE (0.5% per tick = ~7% per day)
        if 'food' in agent.inventory.items:
            spoilage_rate = 0.005  # 0.5% per tick
            food_qty = agent.inventory.items['food']
            spoiled = int(food_qty * spoilage_rate)
            if spoiled > 0 or random.random() < (food_qty * spoilage_rate - spoiled):
                agent.inventory.remove_item('food', max(1, spoiled))

        # 2. WATER EVAPORATION (0.3% per tick)
        if 'water' in agent.inventory.items:
            evaporation_rate = 0.003
            water_qty = agent.inventory.items['water']
            evaporated = int(water_qty * evaporation_rate)
            if evaporated > 0 or random.random() < (water_qty * evaporation_rate - evaporated):
                agent.inventory.remove_item('water', max(1, evaporated))

        # 3. TOOL DEGRADATION (small chance per tick)
        tools = ['axe', 'pickaxe', 'sword', 'hammer', 'knife']
        for tool in tools:
            if tool in agent.inventory.items:
                # 0.2% chance per tick that tool breaks
                if random.random() < 0.002:
                    agent.inventory.remove_item(tool, 1)
                    # Log tool breaking (minor event, don't spam)
                    if random.random() < 0.1:  # Only log 10% of breaks
                        self.sim.event_logger.log_event(
                            EventCategory.ECONOMIC,
                            EventImportance.MINOR,
                            f"🔨 {agent.name}'s {tool} broke",
                            f"Wear and tear claimed another tool",
                            self.sim.world.time.current_tick,
                            [agent.id]
                        )

        # 4. WEALTH DECAY (0.1% per tick = ~14% per day)
        # Represents storage costs, theft risk, etc.
        if agent.wealth > 0:
            decay_rate = 0.001  # 0.1% per tick
            wealth_lost = agent.wealth * decay_rate
            agent.wealth = max(0, agent.wealth - wealth_lost)

        # 5. PLANT FIBER DEGRADATION (organic material decays)
        if 'plant_fiber' in agent.inventory.items:
            decay_rate = 0.004  # 0.4% per tick
            fiber_qty = agent.inventory.items['plant_fiber']
            decayed = int(fiber_qty * decay_rate)
            if decayed > 0 or random.random() < (fiber_qty * decay_rate - decayed):
                agent.inventory.remove_item('plant_fiber', max(1, decayed))
