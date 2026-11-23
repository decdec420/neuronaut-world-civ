"""
Main Simulation Engine - The Heart of Neuronaut World

This is the orchestrator that coordinates all systems:
- Runs the main simulation loop
- Updates all agents
- Delegates to specialized managers
- Manages world state
- Coordinates events

REFACTORED: Now a clean orchestrator with single responsibility.
All complex logic extracted to specialized modules.
"""

import collections
import time
import asyncio
import random
import logging
from typing import List, Dict, Optional, Deque
from datetime import datetime
from collections import deque

import sys
import os

logger = logging.getLogger(__name__)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent import Agent, Action, ActionType, Position, Gender
from engine.psychology import NeedType, EmotionType
from engine.events import EventCategory, EventImportance

# REFACTORED MODULES (Phase 5 - Final Extraction)
from engine.system_factory import SystemFactory
from engine.lifecycle_manager import LifecycleManager
from engine.system_coordinator import SystemCoordinator
from engine.statistics_exporter import StatisticsExporter
from engine.world_initializer import WorldInitializer

# REFACTORED MODULES (Phase 2, Phase 3, Phase 4)
from engine.agent_updates.perception_builder import PerceptionBuilder
from engine.agent_updates.agent_updater import AgentUpdater
from engine.agent_updates.action_handlers import ActionHandlers

# ACTION HANDLER SYSTEM
from engine.action_handlers import ActionContext, ActionHandlerRegistry
from engine.handlers import (
    MovementActionHandler,
    SurvivalActionHandler,
    SocialInteractionHandler,
    ResourceGatheringHandler,
    KnowledgeActionHandler,
    AgricultureHandler,
    ConstructionHandler,
    EntertainmentHandler,
    GovernanceHandler,
    CombatActionHandler,
    HealthHandler,
    ReligionHandler,
    TerritoryHandler,
    ChemistryHandler,
    EnergyHandler,
    MaterialsHandler,
    AdvancedEconomyHandler,
    FamilyHandler,
    InfrastructureHandler,
    GatheringHandler,
    ShelterHandler,
)

# UTILITIES
from engine.utils.agent_helpers import AgentCacheHelper


# How much of a resource enters the world when an era makes it available (same
# scale as the other non-renewable pools: sand 1000, clay 1200)
ERA_RESOURCE_AMOUNTS = {'metal_ore': 1000.0, 'iron_ore': 800.0}

# Actions that need a partner agent; filled in automatically when missing.
TARGETED_ACTIONS = {'socialize', 'trade', 'teach', 'heal', 'fight', 'tell_story'}

# Unimplemented action -> closest implemented action (see execute_action).
UNHANDLED_ACTION_FALLBACKS = {
    # Movement / exploration
    'scout': 'explore', 'map_area': 'explore', 'search': 'explore', 'wander': 'explore',
    'explore_unknown': 'explore', 'chart_map': 'explore', 'survey_land': 'explore',
    'find_resources': 'explore', 'follow': 'move', 'chase': 'move',
    'flee': 'move',
    # Food
    'fish': 'hunt', 'forage': 'gather_food', 'cook': 'eat', 'brew': 'drink',
    'preserve_food': 'gather_food', 'feast': 'eat',
    # Building / crafting
    'build_house': 'build', 'build_workshop': 'build', 'build_market': 'build',
    'build_wall': 'build', 'repair': 'build', 'demolish': 'gather_materials',
    'craft': 'experiment', 'craft_tool': 'experiment', 'craft_weapon': 'experiment',
    'craft_armor': 'experiment', 'craft_clothing': 'experiment',
    'craft_furniture': 'experiment', 'craft_jewelry': 'experiment',
    'smelt': 'smelt_ore', 'weave': 'experiment', 'pottery': 'experiment',
    'synthesize_compound': 'perform_chemistry',
    # Rest
    'sleep': 'rest', 'relax': 'rest', 'meditate': 'pray', 'bathe': 'drink',
    'idle': 'rest', 'wait': 'rest', 'contemplate': 'pray', 'smoke': 'rest',
    # Social
    'communicate': 'socialize', 'converse': 'socialize', 'gossip': 'socialize',
    'joke': 'socialize', 'compliment': 'socialize', 'insult': 'socialize',
    'apologize': 'socialize', 'comfort': 'socialize', 'listen': 'socialize',
    'watch': 'socialize', 'observe': 'explore', 'scheme': 'socialize', 'plan': 'rest',
    # Romance / family
    'flirt': 'seek_romance', 'court': 'seek_romance', 'propose': 'seek_romance',
    'marry': 'seek_romance', 'have_sex': 'seek_romance', 'give_birth': 'rest',
    'parent': 'care_for_child',
    # Economy
    'sell': 'trade', 'buy': 'trade', 'barter': 'trade', 'work': 'gather_materials',
    'employ': 'trade', 'invest': 'trade', 'steal': 'trade', 'beg': 'socialize',
    'counterfeit_coins': 'mint_coins', 'debase_currency': 'mint_coins',
    'open_savings_account': 'open_bank', 'withdraw_savings': 'trade',
    'make_loan_payment': 'trade', 'default_on_loan': 'trade', 'collect_tax': 'govern',
    'pay_tax': 'govern', 'evade_tax': 'join_tax_revolt',
    'start_tax_revolt': 'join_tax_revolt', 'establish_trade_route': 'send_caravan',
    'form_merchant_guild': 'trade', 'attack_caravan': 'fight',
    'invest_in_bubble': 'gamble', 'sell_investment': 'trade', 'speculate': 'gamble',
    # Conflict
    'attack': 'fight', 'defend': 'guard', 'duel': 'fight', 'ambush': 'fight',
    'threaten': 'fight', 'intimidate': 'fight', 'declare_war': 'fight',
    # Culture
    'paint': 'create_art', 'sculpt': 'create_art', 'compose_music': 'create_art',
    'sing': 'play_game', 'dance': 'celebrate', 'perform': 'tell_story',
    'entertain': 'tell_story',
    # Learning
    'learn_skill': 'experiment', 'study': 'write', 'practice': 'experiment',
    'mentor': 'teach', 'apprentice': 'teach', 'research': 'experiment',
    'invent': 'experiment', 'discover': 'experiment',
    # Politics / groups
    'lead': 'govern', 'judge': 'govern', 'negotiate': 'trade', 'form_alliance': 'socialize',
    'make_peace': 'socialize', 'campaign': 'vote', 'join_group': 'socialize',
    'leave_group': 'socialize', 'form_group': 'socialize', 'recruit': 'socialize',
    'exile': 'govern',
    # Religion / health
    'bless': 'perform_ritual', 'curse': 'perform_ritual', 'prophesy': 'worship',
    'convert': 'worship', 'treat': 'heal', 'midwife': 'heal', 'comfort_sick': 'heal',
}


class SimulationEngine:
    """
    Main simulation engine - Clean orchestrator pattern.

    This class now focuses ONLY on:
    1. Running the simulation loop
    2. Delegating to specialized managers
    3. Coordinating tick updates
    4. Executing agent actions
    """

    def __init__(self, world_width: int = 100, world_height: int = 100):
        """
        Initialize simulation engine.

        All system creation delegated to SystemFactory.
        All initialization logic delegated to specialized managers.
        """
        # Ids come from the world's dice (engine/ids.py), seeded before any
        # system makes one, so the same seed gives the same world
        from engine import ids
        ids.seed(random.getrandbits(64))

        # ===== SYSTEM INITIALIZATION (Delegated to SystemFactory) =====
        systems = SystemFactory.create_simulation_systems(world_width, world_height)

        # Unpack all systems into self
        self._unpack_systems(systems)

        # ===== SPECIALIZED MANAGERS (Phase 5 Refactoring) =====
        print("  Specialized managers...")
        self.lifecycle_manager = LifecycleManager(self)
        self.system_coordinator = SystemCoordinator(self)
        self.statistics_exporter = StatisticsExporter(self)
        self.world_initializer = WorldInitializer(self)
        print("✅ Lifecycle, system coordination, statistics, and world initialization managers enabled!")

        # ===== ACTION HANDLERS (Phase 4 Refactoring) =====
        # Old action handlers from agent_updates module (kept for compatibility)
        self.action_handlers = ActionHandlers(self)
        # The modular handlers (engine/handlers/*) look this up by the name
        # 'interaction_handler'. Without the alias, gathering, rest, social and
        # trade actions all silently failed and agents starved.
        self.interaction_handler = self.action_handlers

        # Used by the /agents/{id} and /agents/{id}/profile API endpoints
        from agents.profiles import ProfileBuilder
        self.profile_builder = ProfileBuilder(self)
        print("🎯 Action Handlers enabled - Modular interaction handling (Phase 4)!")

        # New action handler system (modular, testable)
        self._action_context = ActionContext(self)
        self._handler_registry = ActionHandlerRegistry()
        self._register_action_handlers()
        print("⚙️  Action Handler System enabled - Modular action execution!")

        # The AI brain's menu comes from the same registry and aliases the
        # engine runs actions with, so the two can't drift apart.
        if self.llm_brain is not None:
            from agents.action_menu import build_menu
            self.llm_brain.set_action_menu(build_menu(self._handler_registry, UNHANDLED_ACTION_FALLBACKS))

        # ===== AGENT UTILITIES =====
        # Agent lookup cache for O(1) performance
        self._agent_helper = AgentCacheHelper()
        print("🚀 Agent lookup cache enabled - O(1) agent queries!")

        # Perception builder for cleaner agent decision-making (Phase 2 refactor)
        self._perception_builder = PerceptionBuilder(self)
        print("👁️  Perception Builder enabled - Modular perception construction!")

        # Agent updater for cleaner agent update loop (Phase 3 refactor)
        self._agent_updater = AgentUpdater(self)
        print("🔄 Agent Updater enabled - Modular agent update loop!")

        # ===== SIMULATION STATE =====
        self.running = False
        self.tick_rate = 1.0  # Seconds per tick
        self.paused = False

        # ===== STATISTICS =====
        self.total_agents_created = 0
        self.total_reactions_performed = 0  # Chemistry reactions

        # Civilization milestone tracking
        self.achieved_milestones = set()
        self.milestone_history: Deque = deque(maxlen=1000)

        # Death wipe tracking
        self.death_wipe_detected = False
        self.last_auto_save_tick = 0
        self.civilization_history_exported = False

        # Population history tracking
        self.population_history: Deque = deque(maxlen=10000)
        self.births_this_day = 0
        self.deaths_this_day = 0
        self.death_causes = {}
        # Partnerships formed, separations, births... (engine/handlers/family.py)
        self.life_events = collections.Counter()
        # Who knows what, and conversations that pass it on (world/news.py)
        from world.news import NewsNetwork
        self.news = NewsNetwork()
        # Gatherings someone announces and others hear about (world/gatherings.py)
        from world.gatherings import Gatherings
        self.gatherings = Gatherings(self)
        # Successful actions by kind, and the village's history (engine/chronicle.py)
        self.action_successes = collections.Counter()
        self.products = collections.Counter()  # things made (glass, steel, coins...), by name
        from engine.chronicle import Chronicle
        self.chronicle = Chronicle()
        self.last_tracked_day = 0
        print("📊 Population tracking enabled - track births/deaths over time!")

        print("\n🎉 SIMULATION ENGINE READY - All systems operational!")

    def _unpack_systems(self, systems: Dict):
        """
        Unpack systems dictionary into self attributes.

        Args:
            systems: Dictionary of initialized systems from SystemFactory
        """
        # Core systems
        self.world = systems['world']
        self.relationship_manager = systems['relationship_manager']
        self.group_manager = systems['group_manager']
        self.economy = systems['economy']
        self.event_logger = systems['event_logger']
        # Everyone involved in an event remembers it (agents/memory_stream.py)
        self.event_logger.listeners.append(self._remember_event)

        # Old systems
        self.building_manager = systems['building_manager']
        self.innovation_manager = systems['innovation_manager']
        self.warfare_manager = systems['warfare_manager']
        self.governance_manager = systems['governance_manager']
        self.production_manager = systems['production_manager']
        self.strategy_manager = systems['strategy_manager']

        # Autonomous systems
        self.experimentation_engine = systems['experimentation_engine']
        self.dynamic_building_system = systems['dynamic_building_system']
        self.knowledge_system = systems['knowledge_system']
        self.consequence_engine = systems['consequence_engine']
        self.role_emergence = systems['role_emergence']
        self.tech_progression = systems['tech_progression']
        self.persistence = systems['persistence']
        self.persistence.simulation = self  # Set reference
        self.purposeful_evaluator = systems['purposeful_evaluator']

        # Progression systems
        self.civilization = systems['civilization']
        self.life_system = systems['life_system']
        self.fun_system = systems['fun_system']

        # Specialized systems
        self.agriculture = systems['agriculture']
        self.health = systems['health']
        self.religion = systems['religion']
        self.territory = systems['territory']
        self.chemistry = systems['chemistry']
        self.energy = systems['energy']
        self.materials_science = systems['materials_science']

        # Story and achievements
        self.story_feed = systems['story_feed']
        self.story_generator = systems['story_generator']
        self.achievement_tracker = systems['achievement_tracker']

        # Meta-progression
        self.meta_progression = systems['meta_progression']

        # Pathfinding
        self.pathfinder = systems['pathfinder']
        # Roads, wells and street lights agents build (world/infrastructure.py);
        # paths prefer road tiles
        from world.infrastructure import Infrastructure
        self.infrastructure = Infrastructure(self.world.map.width, self.world.map.height)
        self.pathfinder.road_tiles = self.infrastructure.roads
        self.pathfinder.set_terrain(self.world.map)  # water is impassable
        self.resource_memory = systems['resource_memory']

        # Weather and disasters
        self.weather = systems['weather']
        self.disasters = systems['disasters']

        # AI systems
        self.config = systems['config']
        self.llm_brain = systems['llm_brain']
        self.swarm_intelligence = systems['swarm_intelligence']

    def _register_action_handlers(self) -> None:
        """
        Register all action handlers with the registry.

        All 17 handlers registered for 100% coverage.
        """
        handlers = [
            # Basic Actions
            MovementActionHandler(self._action_context),
            SurvivalActionHandler(self._action_context),
            SocialInteractionHandler(self._action_context),
            ResourceGatheringHandler(self._action_context),

            # Knowledge & Learning
            KnowledgeActionHandler(self._action_context),

            # Production & Building
            AgricultureHandler(self._action_context),
            ConstructionHandler(self._action_context),

            # Culture & Entertainment
            EntertainmentHandler(self._action_context),

            # Society & Politics
            GovernanceHandler(self._action_context),
            CombatActionHandler(self._action_context),

            # Health & Religion
            HealthHandler(self._action_context),
            ReligionHandler(self._action_context),

            # Territory & Resources
            TerritoryHandler(self._action_context),

            # Advanced Science
            ChemistryHandler(self._action_context),
            EnergyHandler(self._action_context),
            MaterialsHandler(self._action_context),

            # Advanced Economy
            AdvancedEconomyHandler(self._action_context),

            # Romance and family
            FamilyHandler(self._action_context),

            # Public works: roads, wells, street lights
            InfrastructureHandler(self._action_context),

            # Gatherings people are invited to by word of mouth
            GatheringHandler(self._action_context),
            ShelterHandler(self._action_context),
        ]

        self._handler_registry.register_multiple(handlers)

        # Log coverage statistics
        stats = self._handler_registry.get_coverage_stats()
        print(f"   Registered {len(handlers)} action handlers")
        print(f"   Coverage: {stats['covered_count']}/{stats['total_action_types']} action types ({stats['coverage_percentage']:.1f}%)")

        if stats['coverage_percentage'] >= 100:
            print(f"   ✅ 100% ACTION COVERAGE ACHIEVED!")

    def _rebuild_agent_cache(self) -> None:
        """Rebuild the agent lookup cache for O(1) access by ID."""
        self._agent_helper.rebuild_cache(self.world.agents)

    def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """Fast O(1) agent lookup by ID using cache."""
        return self._agent_helper.get_agent_by_id(agent_id, self.world.agents)

    # ===== DELEGATION TO SPECIALIZED MANAGERS =====

    def initialize_world(self, num_agents: int = 50):
        """Initialize world with starting population (delegated)."""
        self.world_initializer.initialize_world(num_agents)

    def create_agent(
        self,
        name: Optional[str] = None,
        age: int = 20,
        is_player: bool = False,
        gender: Optional[Gender] = None,
        personality=None
    ) -> Agent:
        """Create a new agent (delegated)."""
        return self.world_initializer.create_agent(name, age, is_player, gender, personality)

    def get_population_statistics(self) -> Dict:
        """Get population statistics (delegated)."""
        return self.statistics_exporter.get_population_statistics()

    def get_state_snapshot(self) -> Dict:
        """Get complete world state snapshot (delegated)."""
        return self.statistics_exporter.get_state_snapshot()

    # ===== MAIN SIMULATION LOOP =====

    async def run(self):
        """Main simulation loop."""
        self.running = True
        print("🚀 Neuronaut World simulation started!")

        while self.running:
            if not self.paused:
                try:
                    await self.tick()
                except Exception:
                    # Logged with its traceback; the world carries on with the next tick
                    logger.exception("Tick %d failed", self.world.time.current_tick)

            # Sleep until next tick
            await asyncio.sleep(self.tick_rate)

    async def tick(self):
        """
        Single simulation tick.

        Orchestrates all system updates in proper order.
        """
        current_tick = self.world.time.current_tick
        current_season = self.world.time.season

        # Update weather system
        self.weather.update(current_season, current_tick)
        weather_effects = self.weather.get_current_effects()

        # Update disaster system
        alive_count = sum(1 for a in self.world.agents if a.alive)
        self.disasters.update(
            current_tick,
            current_season,
            self.weather.current_weather.value,
            alive_count
        )

        # Apply disaster effects to buildings and agents (DELEGATED)
        for disaster in self.disasters.active_disasters:
            if disaster.tick == current_tick:
                self.system_coordinator.apply_disaster_to_world(disaster)

        # Advance world time (with weather effects affecting resources!)
        self.world.tick(weather_effects=weather_effects)

        # Update all managers
        self.building_manager.update_buildings()
        self.governance_manager.update_governments(current_tick)
        # A repealed tax law ends its tax
        for policy_id in getattr(self.governance_manager, 'repealed_tax_policies', []):
            self.economy.taxation.repeal_tax_policy(policy_id, current_tick)
        self.governance_manager.repealed_tax_policies = []
        # Resources a new era makes available enter the world (AUDIT.md #11:
        # metal and iron ore pools stayed at 0 forever)
        for resource in self.civilization.available_resources:
            if self.world.resource_pools.get(resource, None) == 0.0 and resource not in self.world.unlocked_resources:
                self.world.unlock_resource(resource, ERA_RESOURCE_AMOUNTS.get(resource, 500.0))
                self.world.unlocked_resources.add(resource)

        # Update fun system (celebrations, games, etc.)
        completed_celebrations = self.fun_system.update_celebrations(delta_time=1.0)

        # Update agriculture system (crops, animals, seasons)
        season_changed = self.agriculture.update_season(current_tick)
        if season_changed:
            logger.info(f"🌍 Season changed to {self.agriculture.current_season.value}!")

        self.agriculture.update_crops(current_tick)
        self.agriculture.update_animals(current_tick)

        # Update health system (disease progression and spreading)
        deaths_from_disease = self.health.update_diseases(current_tick, self.world.agents)

        # Handle disease deaths
        for agent_id in deaths_from_disease:
            agent = next((a for a in self.world.agents if a.id == agent_id), None)
            if agent and agent.alive:
                agent.alive = False
                agent.health = 0
                agent.death_cause = "disease"
                logger.warning(f"💀 {agent.name} died from disease!")

                self.event_logger.log_event(
                    EventCategory.DEATH,
                    EventImportance.MAJOR,
                    f"{agent.name} succumbed to disease",
                    f"{agent.name} died from an untreated illness at age {agent.age}.",
                    current_tick,
                    [agent_id]
                )

        # Spread contagious diseases between nearby agents
        self.health.spread_diseases(self.world.agents, current_tick)

        # Update religion system (rituals)
        completed_rituals = self.religion.update_rituals(current_tick)
        self.religion.lapse_inactive_followers(current_tick)

        # Apply spiritual benefits from completed rituals
        for ritual in completed_rituals:
            for participant_id in ritual.participants:
                participant = next((a for a in self.world.agents if a.id == participant_id), None)
                if participant:
                    participant.needs.satisfy_need(NeedType.MEANING, ritual.spiritual_benefit)
                    participant.needs.satisfy_need(NeedType.BELONGING, ritual.social_cohesion)

            logger.info(f"🙏 Religious {ritual.ritual_type.value} completed with {len(ritual.participants)} participants")

        # Apply mood boost to celebration participants
        for celebration in completed_celebrations:
            for participant_id in celebration.participants:
                agent = next((a for a in self.world.agents if a.id == participant_id), None)
                if agent:
                    agent.needs.satisfy_need(NeedType.BELONGING, celebration.mood_boost)
                    agent.needs.satisfy_need(NeedType.MEANING, celebration.mood_boost * 0.5)
                    agent.emotions.trigger_emotion(EmotionType.JOY, celebration.mood_boost)

            self.event_logger.log_event(
                EventCategory.CULTURAL,
                EventImportance.MINOR,
                f"✨ {celebration.celebration_name} concluded",
                f"The celebration attended by {len(celebration.participants)} agents has concluded. Memories were made!",
                current_tick,
                list(celebration.participants)
            )

        # ===== AGENT UPDATE LOOP (Phase 3 Refactor) =====
        # All agent update logic delegated to AgentUpdater
        await self._agent_updater.update_all_agents(current_tick)

        # Update economy
        economic_events = self.economy.tick_update(current_tick, self.world.agents)

        # Check for currency evolution
        currency_message = self.economy.check_currency_evolution(current_tick)
        if currency_message:
            logger.info(currency_message)
            self.event_logger.log_event(
                EventCategory.ECONOMIC,
                EventImportance.MAJOR,
                "Currency Evolution",
                currency_message,
                current_tick,
                []
            )

        # Log major economic events
        if economic_events.get('defaulted_loans'):
            # check_for_defaults returns loan ids (this read attributes off the id
            # string and raised once loans became possible)
            for loan_id in economic_events['defaulted_loans']:
                loan = self.economy.banking.loans[loan_id]
                logger.warning(f"💸 Loan default: {loan.borrower_id} failed to repay {loan.amount_remaining:.0f}")

        if economic_events.get('crisis_events'):
            for crisis in economic_events['crisis_events']:
                logger.warning(f"📉 Economic crisis: {crisis.get('type', 'unknown')}")

        # ROLE EMERGENCE - Let agents discover their specializations!
        if current_tick % 50 == 0:
            self._update_role_emergence(current_tick)

        # Birthdays, life stages, old age; then every new death, once
        self.lifecycle_manager.update_aging(current_tick)
        self.lifecycle_manager.handle_deaths()

        # Street lights burn and light the night (world/infrastructure.py)
        self.infrastructure.update_lights(self.world, current_tick)
        # Gatherings start and end (world/gatherings.py)
        self.gatherings.update(current_tick)

        # Write down any firsts and milestones (engine/chronicle.py)
        self.chronicle.observe(self, current_tick)

        # Check civilization milestones (DELEGATED)
        self.system_coordinator.check_civilization_milestones(current_tick)

        # Update population history (DELEGATED)
        self.statistics_exporter.update_population_history()

        # Auto-save and death wipe detection
        self._handle_autosave_and_extinction(current_tick, alive_count)

    def _update_role_emergence(self, current_tick: int):
        """Handle role emergence detection for agents."""
        for agent in self.world.agents:
            if not agent.alive:
                continue

            patterns = self.role_emergence.detect_behavior_patterns(agent.id)

            for pattern in patterns:
                existing_roles = self.role_emergence.agent_roles.get(agent.id, [])
                pattern_exists = any(
                    r.behavior_pattern.pattern_type == pattern.pattern_type
                    for r in existing_roles
                )

                if not pattern_exists and pattern.pattern_strength > 0.30:
                    agent_role_name = self.role_emergence.generate_agent_role_name(
                        pattern,
                        agent_personality={'openness': agent.personality.openness if hasattr(agent, 'personality') else 0.5},
                        agent_recent_discoveries=None,
                        agent_culture_context=None
                    )

                    role = self.role_emergence.agent_discovers_role(
                        agent.id,
                        agent.name,
                        pattern,
                        agent_generated_name=agent_role_name
                    )

                    if role:
                        title = f"{agent.name} becomes {agent_role_name}!"
                        desc = f"{agent.name} has specialized in {', '.join(pattern.dominant_actions)} and now identifies as a {agent_role_name}."
                        self.event_logger.log_event(
                            EventCategory.CULTURAL,
                            EventImportance.MODERATE,
                            title, desc,
                            current_tick,
                            [agent.id]
                        )

    def _handle_autosave_and_extinction(self, current_tick: int, alive_count: int):
        """Handle auto-save and extinction detection."""
        # Death wipe detection
        if alive_count == 0 and len(self.world.agents) > 0 and not self.death_wipe_detected:
            self.death_wipe_detected = True
            self._log_extinction_event(current_tick)

        # Autosave every AUTOSAVE_EVERY ticks (0 = off): a full save that can
        # be loaded from the dashboard, keeping the newest AUTOSAVE_KEEP. (It
        # used to write a summary that couldn't be loaded.)
        elif alive_count > 0 and self.config.autosave_every > 0 \
                and current_tick - self.last_auto_save_tick >= self.config.autosave_every:
            from engine.save_manager import SaveManager
            self.last_auto_save_tick = current_tick
            try:
                manager = SaveManager(self.config.save_dir)
                manager.auto_save(self.persistence.create_snapshot(), simulation=self,
                                  keep=self.config.autosave_keep)
                logger.info("Autosaved (day %d, %d alive)", self.world.time.day, alive_count)
            except OSError:
                # a full disk or an unwritable folder: say so, and keep running
                logger.exception("Autosave failed")

        # Warn when the population falls below 10, once per new low (this
        # printed on every tick while it stayed low)
        if 0 < alive_count < 10 and not self.death_wipe_detected and \
                alive_count < getattr(self, '_lowest_warned', 10):
            self._lowest_warned = alive_count
            logger.warning("Only %d agents remain: the village is at risk", alive_count)
        elif alive_count >= 10:
            self._lowest_warned = 10

    def _log_extinction_event(self, current_tick: int):
        """Log civilization extinction event."""
        print("\n" + "="*60)
        print("💀 CIVILIZATION EXTINCTION EVENT 💀")
        print("="*60)
        print(f"All {len(self.world.agents)} agents have died!")
        print(f"Civilization lasted {self.world.time.day} days ({current_tick} ticks)")
        print(f"Era: {self.civilization.current_era.value}")
        print(f"Total discoveries: {len(self.experimentation_engine.discoveries)}")
        print(f"Total buildings: {len(self.dynamic_building_system.buildings)}")

        # Export history
        if not self.civilization_history_exported:
            try:
                history_path = self.persistence.export_civilization_history(
                    self,
                    output_file=f"extinction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                print(f"\n📜 Civilization history exported to: {history_path}")
                self.civilization_history_exported = True
            except Exception as e:
                print(f"\n❌ Failed to export history: {e}")

        print("\n" + "="*60)

    async def execute_action(self, agent: Agent, action: Action) -> Dict:
        """
        Execute an agent's action using the modular handler system.

        Args:
            agent: Agent performing the action
            action: Action to execute

        Returns:
            Dictionary with result (success, emotional_impact, message, etc.)
        """
        current_tick = self.world.time.current_tick

        # Get handler from registry
        handler = self._handler_registry.get_handler(action.action_type)
        if not handler:
            # Many ActionTypes have no dedicated handler yet. Route them to the
            # closest implemented action so the agent's choice still does
            # something, instead of silently failing every tick.
            fallback = UNHANDLED_ACTION_FALLBACKS.get(action.action_type.value)
            if fallback:
                action = Action(
                    ActionType(fallback),
                    target_agent=action.target_agent,
                    target_position=action.target_position,
                    parameters=action.parameters,
                    priority=action.priority,
                )
                handler = self._handler_registry.get_handler(action.action_type)
        if not handler:
            logger.error(f"❌ No handler found for action type: {action.action_type}")
            return {
                'success': False,
                'emotional_impact': 0.0,
                'message': f'Action type {action.action_type} not implemented'
            }

        # Babies and children can do only some things (life/family.py)
        from life.family import allowed_at_stage
        if not allowed_at_stage(agent, action.action_type.value):
            return {
                'success': False,
                'emotional_impact': 0.0,
                'message': f"Too young to {action.action_type.value.replace('_', ' ')}"
            }

        # Social actions chosen without a partner: pick the nearest living agent
        if action.target_agent is None and action.action_type.value in TARGETED_ACTIONS:
            others = [a for a in self.world.agents if a.alive and a.id != agent.id]
            if others:
                nearest = min(others, key=lambda o: agent.location.distance_to(o.location))
                action.target_agent = nearest.id

        # Validate action can be performed
        can_execute, reason = handler.validate(agent, action)
        if not can_execute:
            return {
                'success': False,
                'emotional_impact': -0.05,
                'message': reason
            }

        # Execute via handler
        result = handler.execute(agent, action)

        return result.to_dict()

    def ensure_newer_systems(self) -> None:
        """A world saved by an older version lacks systems added since; give it
        fresh ones (as a new world would have) so it can carry on."""
        import collections as _c
        if not hasattr(self, 'products'):
            self.products = _c.Counter()
        if not hasattr(self, 'news'):
            from world.news import NewsNetwork
            self.news = NewsNetwork()
        if not hasattr(self, 'gatherings'):
            from world.gatherings import Gatherings
            self.gatherings = Gatherings(self)
        if not hasattr(self, 'infrastructure'):
            from world.infrastructure import Infrastructure
            self.infrastructure = Infrastructure(self.world.map.width, self.world.map.height)
            self.pathfinder.road_tiles = self.infrastructure.roads
        if not hasattr(self.world.map, 'land_component'):
            self.world.map._label_land()
        if not getattr(self.pathfinder, 'water', None):
            self.pathfinder.set_terrain(self.world.map)

    EVENT_MEMORY_IMPORTANCE = {0: 0.1, 1: 0.3, 2: 0.5, 3: 0.8, 4: 1.0}

    def _remember_event(self, event) -> None:
        importance = self.EVENT_MEMORY_IMPORTANCE.get(event.importance.value, 0.3)
        text = f"{event.title}: {event.description}" if event.description else event.title
        involved = []
        for agent_id in set(event.agents_involved or ()):
            agent = self._get_agent_by_id(agent_id)
            if agent is not None and agent.alive:
                agent.memory_stream.add(event.tick, text, importance)
                involved.append(agent)
        # Something that matters becomes news: those involved know it, and so
        # does anyone near enough to have seen it (world/news.py)
        if event.importance.value >= 2:
            places = [(event.location['x'], event.location['y'])] if event.location and 'x' in event.location \
                else [(a.location.x, a.location.y) for a in involved]
            knowers = {a.id for a in involved}
            for x, y in places:
                knowers.update(self.news.witnesses(self.world.agents, x, y))
            self.news.publish(event.tick, event.title, importance, knowers, about=[a.id for a in involved])

    def _get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        for agent in self.world.agents:
            if agent.id == agent_id:
                return agent
        return None

    def stop(self):
        """Stop simulation."""
        self.running = False
        if getattr(self._agent_updater, 'thinking', None) is not None:
            self._agent_updater.thinking.close()  # don't wait on model calls in flight
        print("Simulation stopped")
