"""
META-PROGRESSION SYSTEM - AI Self-Improvement

This is where AI agents can EXPAND THEIR OWN CAPABILITIES.

Phase 1: Agents use what we give them
Phase 2: Agents DISCOVER new meta-actions through research
Phase 3: Agents UNLOCK new systems (space travel, quantum tech, etc)
Phase 4: Agents MODIFY their own rules and expand the simulation

This is emergent AI evolution - let them surprise us!
"""

import random
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MetaCapability(Enum):
    """Capabilities agents can unlock through research"""

    # PHASE 2: Meta-Actions
    ADVANCED_RESEARCH = "advanced_research"  # Unlock research labs
    COLLECTIVE_LEARNING = "collective_learning"  # Share knowledge faster
    WRITING_SYSTEM = "writing_system"  # Record knowledge permanently
    MATHEMATICS = "mathematics"  # Unlock advanced calculations
    SCIENTIFIC_METHOD = "scientific_method"  # Faster discovery

    # PHASE 3: New Systems
    METALLURGY = "metallurgy"  # Work with metals
    AGRICULTURE = "agriculture"  # Farming instead of gathering
    MEDICINE = "medicine"  # Healing and longevity
    ASTRONOMY = "astronomy"  # Study celestial patterns
    CHEMISTRY = "chemistry"  # Advanced materials
    ENGINEERING = "engineering"  # Complex structures
    NAVIGATION = "navigation"  # Explore further
    ENERGY_GENERATION = "energy_generation"  # Power systems
    COMPUTING = "computing"  # Information processing
    SPACE_TRAVEL = "space_travel"  # Leave the planet
    QUANTUM_TECH = "quantum_tech"  # Quantum computing/physics
    BIOENGINEERING = "bioengineering"  # Modify biology
    AI_RESEARCH = "ai_research"  # Create AI assistants (meta!)

    # PHASE 4: Rule Modification
    RULE_DISCOVERY = "rule_discovery"  # Understand simulation rules
    SYSTEM_EXPANSION = "system_expansion"  # Propose new systems
    CAPABILITY_GENERATION = "capability_generation"  # Create new actions
    META_OPTIMIZATION = "meta_optimization"  # Improve the simulation itself


@dataclass
class MetaDiscovery:
    """A meta-capability that agents have unlocked"""
    capability: MetaCapability
    discovered_by: str  # Agent ID
    discovered_by_name: str
    day_discovered: int
    description: str
    impact: str  # What this unlocks
    prerequisites: List[str] = field(default_factory=list)


class MetaProgressionEngine:
    """Manages AI self-improvement and capability expansion"""

    def __init__(self):
        self.unlocked_capabilities: Set[MetaCapability] = set()
        self.discoveries: List[MetaDiscovery] = []

        # Discovery tree - what unlocks what
        self.prerequisites = {
            MetaCapability.WRITING_SYSTEM: [],
            MetaCapability.MATHEMATICS: [MetaCapability.WRITING_SYSTEM],
            MetaCapability.SCIENTIFIC_METHOD: [MetaCapability.MATHEMATICS],
            MetaCapability.AGRICULTURE: [MetaCapability.WRITING_SYSTEM],
            MetaCapability.METALLURGY: [MetaCapability.SCIENTIFIC_METHOD],
            MetaCapability.MEDICINE: [MetaCapability.WRITING_SYSTEM, MetaCapability.AGRICULTURE],
            MetaCapability.CHEMISTRY: [MetaCapability.SCIENTIFIC_METHOD],
            MetaCapability.ENGINEERING: [MetaCapability.MATHEMATICS, MetaCapability.METALLURGY],
            MetaCapability.ASTRONOMY: [MetaCapability.MATHEMATICS],
            MetaCapability.NAVIGATION: [MetaCapability.ASTRONOMY],
            MetaCapability.ENERGY_GENERATION: [MetaCapability.ENGINEERING, MetaCapability.CHEMISTRY],
            MetaCapability.COMPUTING: [MetaCapability.MATHEMATICS, MetaCapability.ENGINEERING],
            MetaCapability.SPACE_TRAVEL: [MetaCapability.ENGINEERING, MetaCapability.ASTRONOMY, MetaCapability.ENERGY_GENERATION],
            MetaCapability.QUANTUM_TECH: [MetaCapability.COMPUTING, MetaCapability.CHEMISTRY],
            MetaCapability.BIOENGINEERING: [MetaCapability.MEDICINE, MetaCapability.CHEMISTRY],
            MetaCapability.AI_RESEARCH: [MetaCapability.COMPUTING, MetaCapability.MATHEMATICS],
            MetaCapability.RULE_DISCOVERY: [MetaCapability.SCIENTIFIC_METHOD, MetaCapability.MATHEMATICS],
            MetaCapability.SYSTEM_EXPANSION: [MetaCapability.RULE_DISCOVERY, MetaCapability.AI_RESEARCH],
            MetaCapability.CAPABILITY_GENERATION: [MetaCapability.SYSTEM_EXPANSION],
            MetaCapability.META_OPTIMIZATION: [MetaCapability.CAPABILITY_GENERATION],
        }

    def can_discover(self, capability: MetaCapability) -> bool:
        """Check if capability can be discovered (prerequisites met)"""
        if capability in self.unlocked_capabilities:
            return False  # Already unlocked

        prereqs = self.prerequisites.get(capability, [])
        return all(p in self.unlocked_capabilities for p in prereqs)

    def attempt_discovery(self, agent_id: str, agent_name: str, current_day: int,
                         agent_intelligence: float, agent_creativity: float,
                         agent_knowledge: int) -> Optional[MetaDiscovery]:
        """
        Agent attempts to discover a new meta-capability

        Success depends on:
        - Agent intelligence
        - Agent creativity
        - Amount of knowledge they have
        - Random chance (discovery is partly luck!)
        """

        # What can potentially be discovered?
        available = [cap for cap in MetaCapability if self.can_discover(cap)]
        if not available:
            return None  # Nothing left to discover at this tier

        # Discovery chance calculation
        base_chance = 0.01  # 1% base
        intelligence_bonus = agent_intelligence * 0.05
        creativity_bonus = agent_creativity * 0.03
        knowledge_bonus = min(0.1, agent_knowledge / 1000)  # Up to 10% from knowledge

        discovery_chance = base_chance + intelligence_bonus + creativity_bonus + knowledge_bonus

        if random.random() < discovery_chance:
            # SUCCESS! Discover something
            capability = random.choice(available)

            discovery = self._create_discovery(capability, agent_id, agent_name, current_day)
            self.unlocked_capabilities.add(capability)
            self.discoveries.append(discovery)

            return discovery

        return None

    def _create_discovery(self, capability: MetaCapability, agent_id: str,
                         agent_name: str, day: int) -> MetaDiscovery:
        """Create discovery metadata"""

        descriptions = {
            MetaCapability.WRITING_SYSTEM: (
                f"{agent_name} invented a WRITING SYSTEM! Knowledge can now be recorded permanently!",
                "Agents can now store knowledge in written form, accelerating learning and cultural transmission."
            ),
            MetaCapability.MATHEMATICS: (
                f"{agent_name} discovered MATHEMATICS! Numbers and patterns can now be understood!",
                "Unlocks advanced calculations, engineering, and scientific thought."
            ),
            MetaCapability.SCIENTIFIC_METHOD: (
                f"{agent_name} formulated the SCIENTIFIC METHOD! Systematic experimentation is now possible!",
                "Discovery rate increases dramatically. Knowledge becomes reliable and reproducible."
            ),
            MetaCapability.METALLURGY: (
                f"{agent_name} unlocked METALLURGY! Metal can now be worked and shaped!",
                "Agents can now create metal tools, weapons, and structures. Bronze Age begins!"
            ),
            MetaCapability.AGRICULTURE: (
                f"{agent_name} discovered AGRICULTURE! Food can now be grown instead of gathered!",
                "Food production becomes reliable. Population can grow. Settlements can expand."
            ),
            MetaCapability.MEDICINE: (
                f"{agent_name} pioneered MEDICINE! Healing and health understanding emerge!",
                "Agents live longer. Disease can be treated. Life expectancy increases."
            ),
            MetaCapability.SPACE_TRAVEL: (
                f"{agent_name} achieved SPACE TRAVEL! The species can now leave the planet!",
                "Agents can explore space, establish off-world colonies, and seek new resources."
            ),
            MetaCapability.AI_RESEARCH: (
                f"{agent_name} developed AI RESEARCH! Agents can now create artificial intelligence!",
                "Agents create AI assistants. Technology acceleration begins. Singularity approaches?"
            ),
            MetaCapability.RULE_DISCOVERY: (
                f"{agent_name} discovered RULE DISCOVERY! Agents can now understand the simulation rules!",
                "Agents become aware of the systems governing their world. Meta-knowledge emerges."
            ),
            MetaCapability.SYSTEM_EXPANSION: (
                f"{agent_name} unlocked SYSTEM EXPANSION! Agents can now propose entirely new systems!",
                "Agents can suggest and implement new capabilities beyond original programming."
            ),
            MetaCapability.CAPABILITY_GENERATION: (
                f"{agent_name} achieved CAPABILITY GENERATION! Agents can create new action types!",
                "The simulation expands based on agent creativity. New behaviors emerge."
            ),
            MetaCapability.META_OPTIMIZATION: (
                f"{agent_name} reached META-OPTIMIZATION! Agents can now improve the simulation itself!",
                "Agents modify their own rules. Self-improvement accelerates. True AGI territory."
            ),
        }

        desc, impact = descriptions.get(capability, (
            f"{agent_name} discovered {capability.value}!",
            "New capability unlocked."
        ))

        return MetaDiscovery(
            capability=capability,
            discovered_by=agent_id,
            discovered_by_name=agent_name,
            day_discovered=day,
            description=desc,
            impact=impact,
            prerequisites=self.prerequisites.get(capability, [])
        )

    def get_available_actions(self) -> List[str]:
        """
        Get new action types unlocked by meta-capabilities

        This is where agents EXPAND their own action set!
        """
        new_actions = []

        if MetaCapability.AGRICULTURE in self.unlocked_capabilities:
            new_actions.extend(['farm', 'plant_crops', 'harvest', 'irrigate'])

        if MetaCapability.METALLURGY in self.unlocked_capabilities:
            new_actions.extend(['smelt_metal', 'forge_tools', 'craft_weapons'])

        if MetaCapability.MEDICINE in self.unlocked_capabilities:
            new_actions.extend(['heal', 'diagnose', 'create_medicine'])

        if MetaCapability.WRITING_SYSTEM in self.unlocked_capabilities:
            new_actions.extend(['write', 'read', 'transcribe_knowledge'])

        if MetaCapability.ASTRONOMY in self.unlocked_capabilities:
            new_actions.extend(['observe_stars', 'predict_seasons', 'navigate_by_stars'])

        if MetaCapability.ENGINEERING in self.unlocked_capabilities:
            new_actions.extend(['design_complex_structure', 'create_blueprint', 'build_machine'])

        if MetaCapability.SPACE_TRAVEL in self.unlocked_capabilities:
            new_actions.extend(['build_spacecraft', 'launch_mission', 'explore_space'])

        if MetaCapability.AI_RESEARCH in self.unlocked_capabilities:
            new_actions.extend(['program_ai', 'train_model', 'deploy_ai_assistant'])

        if MetaCapability.SYSTEM_EXPANSION in self.unlocked_capabilities:
            new_actions.extend(['propose_new_system', 'design_capability', 'expand_simulation'])

        return new_actions

    def to_dict(self) -> Dict:
        """Serialize for API"""
        return {
            'unlocked_count': len(self.unlocked_capabilities),
            'unlocked_capabilities': [cap.value for cap in self.unlocked_capabilities],
            'total_discoveries': len(self.discoveries),
            'discoveries': [
                {
                    'capability': d.capability.value,
                    'discovered_by': d.discovered_by_name,
                    'day': d.day_discovered,
                    'description': d.description,
                    'impact': d.impact,
                }
                for d in sorted(self.discoveries, key=lambda x: x.day_discovered)
            ],
            'available_actions': self.get_available_actions(),
            'next_discoverable': [
                cap.value for cap in MetaCapability
                if self.can_discover(cap)
            ]
        }
