"""
Civilization Narrator - AI Tells Its Own Story

This system generates compelling narratives about AI civilization development.
Instead of dry logs, you get EPIC STORIES about what the AI discovers.

Key Features:
- **Era Detection**: Identifies historical periods (Stone Age → Space Age)
- **Civilization Naming**: Names emerge from culture and achievements
- **Event Narration**: Major moments get GPT-4 generated stories
- **Legendary Moments**: Detects and highlights unprecedented discoveries
- **Cultural Identity**: Each civilization develops unique narrative voice
- **Real-Time Feed**: Live story updates as events unfold

This creates LIVING HISTORY - where AI civilizations have their own sagas,
myths, and legends that emerge naturally from their experiences.

Example Output:
    "In the Year of First Fires, the Riverfolk discovered the secret of flame.
     Elder Kara, whose hands had gathered berries for thirty seasons, struck
     flint against stone and birthed light from darkness. The tribe gathered
     in wonder as shadows danced on cave walls for the first time..."
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random

from agents.llm_brain import MultiLLMBrain

logger = logging.getLogger(__name__)


class Era(Enum):
    """Historical eras that emerge from technological/social progress"""
    DAWN = "The Dawn"  # First 100 ticks - survival
    STONE_AGE = "Stone Age"  # Tools, fire, basic shelters
    TRIBAL = "Tribal Era"  # Permanent settlements, social structures
    BRONZE_AGE = "Bronze Age"  # Metalworking, writing
    IRON_AGE = "Iron Age"  # Advanced tools, warfare
    CLASSICAL = "Classical Era"  # Philosophy, arts, governance
    MEDIEVAL = "Medieval Era"  # Feudalism, religion
    RENAISSANCE = "Renaissance"  # Science, exploration, art
    INDUSTRIAL = "Industrial Era"  # Machines, factories
    MODERN = "Modern Era"  # Electronics, global trade
    SPACE_AGE = "Space Age"  # Space exploration, AI


class EventMagnitude(Enum):
    """How significant is this event?"""
    TRIVIAL = "trivial"  # Not worth narrating
    MINOR = "minor"  # Brief mention
    MODERATE = "moderate"  # Short paragraph
    MAJOR = "major"  # Full story
    LEGENDARY = "legendary"  # Epic multi-paragraph saga


@dataclass
class NarrativeEvent:
    """A story-worthy event in civilization history"""
    event_id: str
    tick: int
    era: Era
    magnitude: EventMagnitude
    event_type: str

    # Story elements
    title: str
    description: str  # Raw data
    narrative: Optional[str] = None  # GPT-4 generated story

    # Context
    agents_involved: List[str] = field(default_factory=list)
    location: Tuple[int, int] = (0, 0)
    civilization_name: Optional[str] = None

    # Metadata
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    is_legendary: bool = False


@dataclass
class CivilizationIdentity:
    """Unique identity and culture of a civilization"""
    civilization_id: str

    # Naming
    name: Optional[str] = None  # Generated from culture
    demonym: Optional[str] = None  # "Riverfolk", "Mountain People"

    # Cultural traits
    values: List[str] = field(default_factory=list)  # "honor", "creativity", "strength"
    specialization: Optional[str] = None  # "hunters", "builders", "traders"

    # Achievements
    major_discoveries: List[str] = field(default_factory=list)
    legendary_figures: Dict[str, str] = field(default_factory=dict)  # agent_id -> epithet

    # Narrative voice
    narrative_style: str = "epic"  # "epic", "poetic", "analytical", "mystical"
    founding_myth: Optional[str] = None

    # Statistics
    population: int = 0
    founding_tick: int = 0
    current_era: Era = Era.DAWN


class CivilizationNarrator:
    """
    Generates epic narratives about AI civilization development

    The narrator observes agent actions, detects significant events,
    and uses LLMs to generate compelling stories that capture the
    essence of what the AI civilization is discovering.

    Features:
    - Era progression tracking
    - Civilization naming and identity
    - Event magnitude assessment
    - GPT-4 story generation
    - Legendary moment detection
    - Cultural voice development
    """

    def __init__(
        self,
        llm_brain: MultiLLMBrain,
        config: Dict[str, Any] = None
    ):
        self.llm_brain = llm_brain
        self.config = config or {}

        # Configuration
        self.narration_enabled = self.config.get('narration_enabled', True)
        self.min_magnitude_to_narrate = EventMagnitude[
            self.config.get('min_magnitude', 'MODERATE')
        ]
        self.auto_name_civilizations = self.config.get('auto_name_civilizations', True)

        # Tracking
        self.civilizations: Dict[str, CivilizationIdentity] = {}
        self.events: List[NarrativeEvent] = []
        self.legendary_moments: List[NarrativeEvent] = []

        # Era tracking
        self.era_thresholds = self._initialize_era_thresholds()

        # Statistics
        self.total_events_detected = 0
        self.stories_generated = 0
        self.civilizations_named = 0

    # ============================================================================
    # CIVILIZATION IDENTITY & NAMING
    # ============================================================================

    def register_civilization(
        self,
        civilization_id: str,
        founding_tick: int = 0,
        initial_population: int = 1
    ) -> CivilizationIdentity:
        """Register a new civilization for narrative tracking"""

        identity = CivilizationIdentity(
            civilization_id=civilization_id,
            founding_tick=founding_tick,
            population=initial_population,
            current_era=Era.DAWN
        )

        self.civilizations[civilization_id] = identity

        logger.info(f"📖 Registered civilization: {civilization_id}")

        return identity

    async def generate_civilization_name(
        self,
        civilization_id: str,
        cultural_context: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Generate a unique civilization name based on their culture

        Args:
            civilization_id: Identifier
            cultural_context: Dict with:
                - dominant_terrain: "river", "mountain", "forest"
                - specialization: "hunters", "builders"
                - values: ["honor", "creativity"]
                - achievements: ["discovered fire", "built first shelter"]

        Returns:
            (civilization_name, demonym)
        """

        if civilization_id not in self.civilizations:
            return "The Unnamed", "the people"

        identity = self.civilizations[civilization_id]

        # Build context for naming
        terrain = cultural_context.get('dominant_terrain', 'land')
        specialization = cultural_context.get('specialization', 'survivors')
        values = cultural_context.get('values', [])
        achievements = cultural_context.get('achievements', [])

        prompt = f"""Generate a compelling civilization name and demonym.

Context:
- Environment: {terrain}
- Specialization: {specialization}
- Core Values: {', '.join(values) if values else 'survival'}
- Major Achievements: {', '.join(achievements[:3]) if achievements else 'still emerging'}

Generate:
1. Civilization Name (2-3 words, evocative, unique)
2. Demonym (what to call the people, e.g., "Riverfolk", "Mountain Clans")

Examples:
- The Crimson Spires / the Spire-dwellers
- Riverfolk Confederation / the Riverfolk
- Children of the Storm / the Storm-born

Format: NAME | DEMONYM"""

        try:
            provider = self.llm_brain.get_available_provider(complexity="complex")
            response = self.llm_brain.call_llm(
                provider=provider,
                prompt=prompt,
                temperature=0.9,  # High creativity
                max_tokens=100
            )

            if response and '|' in response.text:
                parts = response.text.split('|')
                name = parts[0].strip()
                demonym = parts[1].strip() if len(parts) > 1 else "the people"

                # Update identity
                identity.name = name
                identity.demonym = demonym

                self.civilizations_named += 1

                logger.info(f"📖 Named civilization: {name} ({demonym})")

                return name, demonym

        except Exception as e:
            logger.error(f"Failed to generate civilization name: {e}")

        # Fallback to procedural naming
        terrain_names = {
            'river': 'Riverfolk',
            'mountain': 'Mountain Clans',
            'forest': 'Forest People',
            'desert': 'Desert Wanderers',
            'plains': 'Plains Riders'
        }

        name = terrain_names.get(terrain, 'The Wanderers')
        identity.name = name
        identity.demonym = name.lower()

        return name, name.lower()

    # ============================================================================
    # ERA DETECTION & PROGRESSION
    # ============================================================================

    def _initialize_era_thresholds(self) -> Dict[Era, Dict[str, Any]]:
        """Define what triggers each era transition"""
        return {
            Era.STONE_AGE: {
                'min_tick': 100,
                'required_tech': ['tools', 'fire'],
                'min_population': 5
            },
            Era.TRIBAL: {
                'min_tick': 500,
                'required_tech': ['shelter', 'tools'],
                'required_structures': 3,
                'min_population': 10
            },
            Era.BRONZE_AGE: {
                'min_tick': 1000,
                'required_tech': ['metalworking', 'writing'],
                'min_population': 25
            },
            Era.IRON_AGE: {
                'min_tick': 2000,
                'required_tech': ['iron', 'advanced_tools'],
                'min_population': 50
            },
            # ... more eras
        }

    def detect_era(
        self,
        civilization_id: str,
        tick: int,
        technologies: List[str],
        population: int,
        structures: int = 0
    ) -> Optional[Era]:
        """
        Detect if civilization has advanced to a new era

        Returns new Era if advanced, None if no change
        """

        if civilization_id not in self.civilizations:
            return None

        identity = self.civilizations[civilization_id]
        current_era = identity.current_era

        # Check each potential next era
        era_order = list(Era)
        current_index = era_order.index(current_era)

        for potential_era in era_order[current_index + 1:]:
            if potential_era not in self.era_thresholds:
                continue

            thresholds = self.era_thresholds[potential_era]

            # Check all requirements
            if tick < thresholds.get('min_tick', 0):
                continue

            required_tech = thresholds.get('required_tech', [])
            if not all(tech in technologies for tech in required_tech):
                continue

            if population < thresholds.get('min_population', 0):
                continue

            if structures < thresholds.get('required_structures', 0):
                continue

            # All requirements met!
            identity.current_era = potential_era
            logger.info(f"🎭 {identity.name or civilization_id} advanced to {potential_era.value}")

            return potential_era

        return None

    # ============================================================================
    # EVENT DETECTION & MAGNITUDE ASSESSMENT
    # ============================================================================

    def assess_event_magnitude(
        self,
        event_type: str,
        agents_involved: int,
        is_first_of_kind: bool,
        impact_scope: str = "individual"  # individual, group, civilization
    ) -> EventMagnitude:
        """
        Determine how significant an event is

        Args:
            event_type: Type of event
            agents_involved: Number of agents
            is_first_of_kind: First time this has happened
            impact_scope: How widely this affects the civilization

        Returns:
            EventMagnitude
        """

        # Base magnitude from event type
        type_magnitudes = {
            # Always legendary
            'first_fire': EventMagnitude.LEGENDARY,
            'first_writing': EventMagnitude.LEGENDARY,
            'first_wheel': EventMagnitude.LEGENDARY,
            'first_metal': EventMagnitude.LEGENDARY,

            # Major events
            'discovery': EventMagnitude.MAJOR,
            'invention': EventMagnitude.MAJOR,
            'first_war': EventMagnitude.MAJOR,
            'civilization_founded': EventMagnitude.MAJOR,

            # Moderate events
            'birth': EventMagnitude.MODERATE,
            'death': EventMagnitude.MODERATE,
            'marriage': EventMagnitude.MODERATE,
            'trade_route': EventMagnitude.MODERATE,

            # Minor events
            'hunt_success': EventMagnitude.MINOR,
            'structure_built': EventMagnitude.MINOR,

            # Trivial
            'gather_food': EventMagnitude.TRIVIAL,
            'move': EventMagnitude.TRIVIAL,
        }

        base_magnitude = type_magnitudes.get(event_type, EventMagnitude.MINOR)

        # Upgrade magnitude based on context
        if is_first_of_kind and base_magnitude.value != 'trivial':
            # First-ever events are more significant
            magnitude_order = list(EventMagnitude)
            current_index = magnitude_order.index(base_magnitude)
            if current_index < len(magnitude_order) - 1:
                base_magnitude = magnitude_order[current_index + 1]

        if impact_scope == 'civilization':
            # Civilization-wide impact is more significant
            magnitude_order = list(EventMagnitude)
            current_index = magnitude_order.index(base_magnitude)
            if current_index < len(magnitude_order) - 1:
                base_magnitude = magnitude_order[current_index + 1]

        if agents_involved >= 10:
            # Mass events are more significant
            magnitude_order = list(EventMagnitude)
            current_index = magnitude_order.index(base_magnitude)
            if current_index < len(magnitude_order) - 1:
                base_magnitude = magnitude_order[current_index + 1]

        return base_magnitude

    # ============================================================================
    # STORY GENERATION
    # ============================================================================

    async def narrate_event(
        self,
        event: NarrativeEvent,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Generate compelling narrative for an event using LLM

        Args:
            event: Event to narrate
            context: Additional context (agent names, location details, etc.)

        Returns:
            Generated narrative text
        """

        if not self.narration_enabled:
            return event.description

        context = context or {}

        # Get civilization identity for narrative voice
        civ_identity = self.civilizations.get(event.civilization_name)
        narrative_style = civ_identity.narrative_style if civ_identity else "epic"
        civ_name = civ_identity.name if civ_identity else "the people"

        # Build prompt based on magnitude
        if event.magnitude == EventMagnitude.LEGENDARY:
            prompt = self._build_legendary_prompt(event, civ_name, context)
            max_tokens = 500
            temperature = 0.85
        elif event.magnitude == EventMagnitude.MAJOR:
            prompt = self._build_major_prompt(event, civ_name, context)
            max_tokens = 300
            temperature = 0.8
        elif event.magnitude == EventMagnitude.MODERATE:
            prompt = self._build_moderate_prompt(event, civ_name, context)
            max_tokens = 150
            temperature = 0.75
        else:
            # Minor events - brief mention
            return f"{event.title}: {event.description}"

        try:
            provider = self.llm_brain.get_available_provider(complexity="complex")
            response = self.llm_brain.call_llm(
                provider=provider,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if response:
                event.narrative = response.text
                self.stories_generated += 1

                logger.info(f"📖 Generated {event.magnitude.value} narrative: {event.title}")

                return response.text

        except Exception as e:
            logger.error(f"Failed to generate narrative: {e}")

        # Fallback to description
        return event.description

    def _build_legendary_prompt(
        self,
        event: NarrativeEvent,
        civilization_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for legendary event narration"""

        agent_names = context.get('agent_names', ['an unknown soul'])
        location_desc = context.get('location', 'in the wilderness')

        return f"""Write an epic, legendary narrative about a momentous discovery.

Civilization: {civilization_name}
Era: {event.era.value}
Event: {event.title}
Context: {event.description}
Key Figures: {', '.join(agent_names[:3])}
Location: {location_desc}

Write in an epic, mythological style. This is a civilization-defining moment that will be remembered for generations. Include:
- Vivid sensory details
- The emotions of those present
- The significance for the civilization
- A sense of wonder and discovery

Write 2-3 paragraphs in past tense, as if this is ancient history being retold."""

    def _build_major_prompt(
        self,
        event: NarrativeEvent,
        civilization_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for major event narration"""

        return f"""Write a compelling narrative about a significant event.

Civilization: {civilization_name}
Event: {event.title}
What happened: {event.description}

Write in a historical chronicle style. This is an important moment worth recording. Include emotional weight and cultural significance.

Write 1-2 paragraphs."""

    def _build_moderate_prompt(
        self,
        event: NarrativeEvent,
        civilization_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for moderate event narration"""

        return f"""Briefly narrate this event for {civilization_name}.

Event: {event.title}
Details: {event.description}

Write 2-3 sentences in a chronicle style."""

    # ============================================================================
    # PUBLIC API
    # ============================================================================

    async def record_event(
        self,
        event_type: str,
        description: str,
        tick: int,
        civilization_id: str,
        agents_involved: List[str] = None,
        location: Tuple[int, int] = (0, 0),
        is_first_of_kind: bool = False,
        impact_scope: str = "individual",
        context: Dict[str, Any] = None
    ) -> Optional[NarrativeEvent]:
        """
        Record and potentially narrate a civilization event

        Returns: NarrativeEvent if significant enough to record, None otherwise
        """

        self.total_events_detected += 1

        # Assess magnitude
        magnitude = self.assess_event_magnitude(
            event_type=event_type,
            agents_involved=len(agents_involved or []),
            is_first_of_kind=is_first_of_kind,
            impact_scope=impact_scope
        )

        # Skip trivial events
        if magnitude == EventMagnitude.TRIVIAL:
            return None

        # Skip if below minimum threshold
        magnitude_order = list(EventMagnitude)
        if magnitude_order.index(magnitude) < magnitude_order.index(self.min_magnitude_to_narrate):
            return None

        # Get civilization info
        civ_identity = self.civilizations.get(civilization_id)
        era = civ_identity.current_era if civ_identity else Era.DAWN
        civ_name = civ_identity.name if civ_identity else civilization_id

        # Create event
        event = NarrativeEvent(
            event_id=f"{civilization_id}_{tick}_{event_type}",
            tick=tick,
            era=era,
            magnitude=magnitude,
            event_type=event_type,
            title=event_type.replace('_', ' ').title(),
            description=description,
            agents_involved=agents_involved or [],
            location=location,
            civilization_name=civ_name,
            is_legendary=(magnitude == EventMagnitude.LEGENDARY)
        )

        # Generate narrative for significant events
        if magnitude.value in ['major', 'legendary']:
            await self.narrate_event(event, context=context or {})

        # Store event
        self.events.append(event)

        if event.is_legendary:
            self.legendary_moments.append(event)

        return event

    def get_recent_stories(self, count: int = 10) -> List[NarrativeEvent]:
        """Get most recent narrated events"""
        return sorted(
            [e for e in self.events if e.narrative],
            key=lambda e: e.tick,
            reverse=True
        )[:count]

    def get_legendary_moments(self) -> List[NarrativeEvent]:
        """Get all legendary moments"""
        return self.legendary_moments

    def get_civilization_chronicle(self, civilization_id: str) -> List[NarrativeEvent]:
        """Get full chronicle for a civilization"""
        return sorted(
            [e for e in self.events if e.civilization_name == civilization_id or
             (civilization_id in self.civilizations and
              e.civilization_name == self.civilizations[civilization_id].name)],
            key=lambda e: e.tick
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get narrator statistics"""
        return {
            'total_events_detected': self.total_events_detected,
            'stories_generated': self.stories_generated,
            'legendary_moments': len(self.legendary_moments),
            'civilizations_tracked': len(self.civilizations),
            'civilizations_named': self.civilizations_named,
            'events_recorded': len(self.events)
        }
