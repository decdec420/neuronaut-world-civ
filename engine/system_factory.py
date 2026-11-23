"""
System Factory - System Instantiation and Configuration

This module handles ONLY system creation:
- Instantiate all game systems
- Configure system parameters
- Return initialized system dictionary

Extracted from simulation.py to enforce Single Responsibility Principle.
"""

import logging
from typing import Dict, Any

from world.simulation import World
from world.buildings import BuildingManager
from world.innovations import InnovationManager
from world.conflict import WarfareManager
from world.governance import GovernanceManager
from social.relationships import RelationshipManager, GroupManager
from economy.economic_engine import EconomicEngine
from economy.production import ProductionManager
from engine.events import EventLogger
from agents.strategy import StrategyManager
from agents.profiles import ProfileBuilder

# NEW AUTONOMOUS SYSTEMS
from world.experimentation import ExperimentationEngine
from world.dynamic_buildings import DynamicBuildingSystem
from world.knowledge import KnowledgeSystem
from world.consequences import ConsequenceEngine
from world.roles import RoleEmergence
from world.tech_progression import TechProgressionTracker
from engine.persistence import PersistenceEngine
from agents.purposeful_action import PurposefulActionEvaluator
from world.civilization_progression import CivilizationProgressionEngine

# REFACTORED MODULES
from life.life_system import LifeSystem
from world.fun_system import FunSystem
from engine.storytelling import StoryGenerator, StoryFeed
from engine.achievements import AchievementTracker

# ADDITIONAL SYSTEMS
from world.agriculture import AgricultureManager
from world.health import HealthManager
from world.religion import ReligionManager
from world.territory import TerritoryManager
from world.chemistry import ChemistryEngine
from world.energy import EnergyManager
from world.materials import MaterialsManager
from world.meta_progression import MetaProgressionEngine
from agents.pathfinding import Pathfinder, ResourceMemory
from world.weather import WeatherSystem
from world.disasters import NaturalDisasterSystem

# AI AUTONOMY SYSTEMS
from agents.llm_brain import MultiLLMBrain
from agents.swarm_intelligence import SwarmIntelligence
from config import load_config

logger = logging.getLogger(__name__)


class SystemFactory:
    """
    Factory for creating and configuring all simulation systems.

    This class is responsible for instantiating all 30+ game systems
    and returning them in a structured format.
    """

    @staticmethod
    def create_simulation_systems(world_width: int, world_height: int) -> Dict[str, Any]:
        """
        Create and configure all simulation systems.

        This instantiates all managers, engines, and subsystems required
        for the simulation to run.

        Args:
            world_width: Width of the world grid
            world_height: Height of the world grid

        Returns:
            Dictionary containing all initialized systems, organized by category:
            - core: Core simulation systems (world, relationships, economy, events)
            - old_systems: Legacy civilization systems (buildings, innovations, etc.)
            - autonomous: New autonomous systems (experimentation, knowledge, etc.)
            - specialized: Domain-specific systems (agriculture, health, religion, etc.)
            - ai: AI systems (LLM brain, swarm intelligence)
            - config: Configuration object
        """
        print("🏗️  Initializing all simulation systems...")

        systems = {}

        # ===== CORE SYSTEMS =====
        print("  Core systems...")
        systems['world'] = World(world_width, world_height)
        systems['relationship_manager'] = RelationshipManager()
        systems['group_manager'] = GroupManager()
        systems['economy'] = EconomicEngine()
        systems['event_logger'] = EventLogger()

        # ===== OLD SYSTEMS - Full Civilization functionality (kept for compatibility) =====
        print("  Legacy civilization systems...")
        systems['building_manager'] = BuildingManager()
        systems['innovation_manager'] = InnovationManager()
        systems['warfare_manager'] = WarfareManager()
        systems['governance_manager'] = GovernanceManager()
        systems['production_manager'] = ProductionManager()
        systems['strategy_manager'] = StrategyManager()

        # ===== NEW AUTONOMOUS SYSTEMS - TRUE Freedom! =====
        print("  Autonomous systems...")
        systems['experimentation_engine'] = ExperimentationEngine()
        systems['dynamic_building_system'] = DynamicBuildingSystem()
        systems['knowledge_system'] = KnowledgeSystem()
        systems['consequence_engine'] = ConsequenceEngine()
        systems['role_emergence'] = RoleEmergence()
        systems['tech_progression'] = TechProgressionTracker()
        systems['persistence'] = PersistenceEngine(save_directory=str(load_config().save_dir))
        systems['purposeful_evaluator'] = PurposefulActionEvaluator()

        # ===== CIVILIZATION PROGRESSION - Stone Age → Space Age! =====
        print("  Civilization progression...")
        systems['civilization'] = CivilizationProgressionEngine()
        print(f"🏛️  Civilization starting in Stone Age...")
        print(f"   Available resources: {', '.join(systems['civilization'].available_resources)}")
        print(f"   Next milestone: {systems['civilization'].get_next_milestone().name}")

        # ===== LIFE SYSTEM - Birth, romance, reproduction, family dynamics! =====
        print("  Life systems...")
        systems['life_system'] = LifeSystem()
        print("💕 Life System enabled - Agents can reproduce and build families!")

        # ===== FUN SYSTEM - Games, celebrations, art, entertainment! =====
        systems['fun_system'] = FunSystem()
        print("🎉 Fun System enabled - Agents can play games, throw parties, and create art!")

        # ===== SPECIALIZED SYSTEMS =====
        print("  Specialized domain systems...")

        # AGRICULTURE SYSTEM
        systems['agriculture'] = AgricultureManager()
        print("🌾 Agriculture System enabled - Farming revolution begins!")
        print("   Plant crops, tend fields, harvest food")
        print("   Domesticate animals for food and materials")
        print("   Seasonal cycles affect growth")

        # HEALTH & DISEASE SYSTEM
        systems['health'] = HealthManager()
        print("💊 Health & Disease System enabled - Medical challenges!")
        print("   Diseases spread through proximity")
        print("   Discover medicinal treatments")
        print("   Healers specialize in medical knowledge")

        # RELIGION & SPIRITUALITY SYSTEM
        systems['religion'] = ReligionManager()
        print("🙏 Religion & Spirituality System enabled - Faith emerges!")
        print("   Beliefs form from unexplained events")
        print("   Charismatic leaders found religions")
        print("   Temples, rituals, and sacred traditions")

        # TERRITORY & LAND OWNERSHIP SYSTEM
        systems['territory'] = TerritoryManager()
        print("🗺️  Territory & Ownership System enabled - Land disputes!")
        print("   Agents claim and defend territory")
        print("   Borders and trespassing create conflict")
        print("   Resource ownership drives expansion")

        # REAL CHEMISTRY SYSTEM
        systems['chemistry'] = ChemistryEngine()
        print("⚗️  Real Chemistry System enabled - Science begins!")
        print("   Discover elements from the periodic table")
        print("   Perform real chemical reactions (Fe2O3 + 3C → 2Fe + 3CO)")
        print("   Synthesize compounds through experimentation")

        # ENERGY PROGRESSION SYSTEM
        systems['energy'] = EnergyManager()
        print("⚡ Energy Progression System enabled - Power civilization!")
        print("   Progress from wood → coal → oil → electricity → nuclear")
        print("   Build power plants and energy grids")
        print("   Manage fuel consumption and power distribution")

        # ADVANCED MATERIALS SYSTEM
        systems['materials_science'] = MaterialsManager()
        print("🔬 Advanced Materials System enabled - Material ages!")
        print("   Progress from Stone → Bronze → Iron → Steel → Silicon Age")
        print("   Discover alloys, ceramics, polymers, and composites")
        print("   Material properties determine what can be built")

        # ===== STORY ENGINE & ACHIEVEMENTS =====
        print("  Story and achievement systems...")
        systems['story_feed'] = StoryFeed(max_stories=100)
        systems['story_generator'] = StoryGenerator()
        print("📜 Story Engine enabled - Every moment becomes a legend!")

        systems['achievement_tracker'] = AchievementTracker()
        print("🏆 Achievement System enabled - Legends will be made!")

        # ===== META-PROGRESSION SYSTEM - AI Self-Improvement! =====
        systems['meta_progression'] = MetaProgressionEngine()
        print("🧬 META-PROGRESSION enabled - Agents can expand their own capabilities!")
        print("   Phase 1: Using provided actions")
        print("   Phase 2-4: Discovery, system unlocking, and RULE MODIFICATION await...")

        # ===== PATHFINDING & NAVIGATION =====
        systems['pathfinder'] = Pathfinder(world_width, world_height)
        systems['resource_memory'] = ResourceMemory(memory_capacity=30)
        print("🗺️  Pathfinding enabled - Agents navigate intelligently!")
        print("   A* algorithm for optimal routes")
        print("   Resource location memory for efficiency")

        # ===== WEATHER SYSTEM =====
        systems['weather'] = WeatherSystem()
        print("🌦️  Weather System enabled - Dynamic environment!")
        print("   Rain, snow, storms, drought affect gameplay")
        print("   Seasonal weather patterns")
        print("   Weather affects resources and agent survival")

        # ===== NATURAL DISASTERS =====
        systems['disasters'] = NaturalDisasterSystem(world_width, world_height)
        print("⚠️  Natural Disasters enabled - Dramatic challenges!")
        print("   Earthquakes, floods, fires, tornadoes, and more")
        print("   Warning systems for predictable disasters")
        print("   Buildings and agents affected by catastrophes")

        # ===== AI AUTONOMY SYSTEM - FULL AI-POWERED AGENTS! =====
        print("  AI autonomy systems...")
        config = load_config()
        systems['config'] = config

        # Initialize LLM brain (shared across all agents)
        if config.use_llm_decisions:
            systems['llm_brain'] = MultiLLMBrain(api_keys=config.get_api_keys(), config=config)
            print("🧠 AI Autonomy ENABLED - Agents will make AI-powered decisions!")
            keyed = [name for name in ('groq', 'together', 'gemini', 'huggingface') if config.get_api_keys().get(name)]
            print(f"   LLM providers, in order: {', '.join(keyed + [f'Ollama ({config.ollama_model} at {config.ollama_host})'])}")
            print(f"   Long-term planning: Every {config.long_term_planning_interval} ticks")
            print(f"   Self-reflection: Every {config.reflection_interval} ticks")
        else:
            systems['llm_brain'] = None
            print("🤖 AI Autonomy DISABLED - Using rule-based psychology only")
            print("   (Set USE_LLM_DECISIONS=true in .env to enable AI)")

        # Initialize Swarm Intelligence (v2.0 - Multi-Agent Coordination)
        if config.enable_swarm_intelligence and systems['llm_brain']:
            systems['swarm_intelligence'] = SwarmIntelligence(
                llm_brain=systems['llm_brain'],
                config=config.get_swarm_config()
            )
            print("🐝 SWARM INTELLIGENCE ENABLED - Agents will coordinate and form alliances!")
            print(f"   Max Swarm Size: {config.max_swarm_size} agents")
            print(f"   Consensus Threshold: {config.consensus_threshold * 100:.0f}%")
            print(f"   Coordination Radius: {config.coordination_radius} tiles")
            print(f"   Parallel LLM: {'✅' if config.enable_parallel_llm else '❌'}")
        else:
            systems['swarm_intelligence'] = None
            if config.enable_swarm_intelligence and not systems['llm_brain']:
                print("⚠️  Swarm Intelligence requires LLM decisions to be enabled")
            else:
                print("🤖 Swarm Intelligence DISABLED - Agents act independently")

        print("✅ All systems initialized!")
        return systems
