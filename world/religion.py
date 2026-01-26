"""
Religion & Spirituality System - Beliefs Shape Civilization

Implements:
- Belief formation (unexplained events create religious explanations)
- Religious leaders and prophets (high charisma agents)
- Multiple religions (polytheism, monotheism, animism, ancestor worship)
- Temples and sacred sites
- Rituals, prayers, and ceremonies
- Religious conflicts and cooperation
- Moral codes and divine laws

Philosophy: Religion emerges from attempts to explain the unexplainable.
Provides meaning, social cohesion, moral frameworks, and cultural identity.
"""

import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum


class ReligionType(Enum):
    """Types of religious beliefs"""
    ANIMISM = "animism"  # Spirits in nature
    POLYTHEISM = "polytheism"  # Multiple gods
    MONOTHEISM = "monotheism"  # One god
    ANCESTOR_WORSHIP = "ancestor_worship"  # Worship of ancestors
    SHAMANISM = "shamanism"  # Spirit communication
    PANTHEISM = "pantheism"  # God is everything


class DeityDomain(Enum):
    """Domains of gods/spirits"""
    SUN = "sun"  # Sun god, light, warmth
    MOON = "moon"  # Moon goddess, night, mystery
    SKY = "sky"  # Sky god, weather, thunder
    EARTH = "earth"  # Earth mother, fertility, harvest
    WAR = "war"  # War god, battle, strength
    WISDOM = "wisdom"  # Knowledge god, learning
    DEATH = "death"  # Death god, underworld
    LOVE = "love"  # Love goddess, beauty, passion
    CRAFTS = "crafts"  # Craftsman god, innovation
    CHAOS = "chaos"  # Trickster god, unpredictability


class RitualType(Enum):
    """Types of religious rituals"""
    PRAYER = "prayer"  # Individual prayer
    SACRIFICE = "sacrifice"  # Offerings to gods
    CEREMONY = "ceremony"  # Group ritual
    PILGRIMAGE = "pilgrimage"  # Journey to sacred site
    MEDITATION = "meditation"  # Spiritual contemplation
    BLESSING = "blessing"  # Divine favor requested
    FUNERAL = "funeral"  # Death rite


@dataclass
class Deity:
    """A god, spirit, or divine being"""
    id: str
    name: str
    domain: DeityDomain

    # Attributes
    power_level: float = 1.0  # 0-1, how powerful
    benevolent: float = 0.5  # 0-1, 0=wrathful, 1=kind

    # Associated with events
    associated_events: List[str] = field(default_factory=list)

    # Worship
    followers: Set[str] = field(default_factory=set)  # Agent IDs
    temples: Set[str] = field(default_factory=set)  # Temple IDs


@dataclass
class Religion:
    """An organized religious belief system"""
    id: str
    name: str
    religion_type: ReligionType

    # Founding
    founder_id: Optional[str] = None
    founder_name: Optional[str] = None
    founded_tick: int = 0

    # Deities
    deities: List[str] = field(default_factory=list)  # Deity IDs

    # Beliefs and tenets
    core_beliefs: List[str] = field(default_factory=list)
    moral_code: List[str] = field(default_factory=list)
    sacred_texts: List[str] = field(default_factory=list)

    # Followers
    followers: Set[str] = field(default_factory=set)  # Agent IDs
    priests: Set[str] = field(default_factory=set)  # Religious leaders

    # Sacred places
    temples: Set[str] = field(default_factory=set)  # Temple IDs
    sacred_sites: List[Tuple[float, float]] = field(default_factory=list)

    # Rituals
    regular_rituals: List[RitualType] = field(default_factory=list)
    holy_days: List[str] = field(default_factory=list)


@dataclass
class Temple:
    """A religious building"""
    id: str
    name: str
    religion_id: str
    location: Tuple[float, float]

    # Construction
    builder_id: str
    built_at: int

    # Properties
    size: int = 1  # 1-5 scale
    sacred_value: float = 1.0  # How holy is it

    # Usage
    worshippers: Set[str] = field(default_factory=set)
    priests: Set[str] = field(default_factory=set)
    last_ritual: int = 0


@dataclass
class Ritual:
    """A religious ritual event"""
    id: str
    ritual_type: RitualType
    religion_id: str

    # Participants
    leader_id: str  # Priest/shaman conducting it
    participants: Set[str] = field(default_factory=set)

    # Event
    location: Tuple[float, float] = (0.0, 0.0)
    started_tick: int = 0
    duration: int = 10  # Ticks
    completed: bool = False

    # Effects
    spiritual_benefit: float = 0.5  # 0-1
    social_cohesion: float = 0.3  # Strengthens community


class ReligionManager:
    """
    Manages religious beliefs, deities, temples, and rituals.

    Key mechanics:
    - Unexplained events trigger belief formation
    - Charismatic agents become religious leaders
    - Religions compete and cooperate
    - Sacred sites and temples provide meaning
    """

    def __init__(self):
        self.religions: Dict[str, Religion] = {}
        self.deities: Dict[str, Deity] = {}
        self.temples: Dict[str, Temple] = {}
        self.active_rituals: Dict[str, Ritual] = {}

        # Event triggers for belief formation
        self.unexplained_events: List[Dict] = []

        # Statistics
        self.total_religions_founded: int = 0
        self.total_temples_built: int = 0
        self.total_rituals_performed: int = 0
        self.total_conversions: int = 0

    # ===== DEITY CREATION =====

    def create_deity(
        self,
        name: str,
        domain: DeityDomain,
        creator_id: str,
        triggering_event: Optional[str] = None
    ) -> Deity:
        """Create a new deity/spirit"""

        deity_id = str(uuid.uuid4())

        # Deity attributes based on domain
        attributes = self._get_deity_attributes(domain)

        deity = Deity(
            id=deity_id,
            name=name,
            domain=domain,
            power_level=attributes['power'],
            benevolent=attributes['benevolence'],
            followers={creator_id}
        )

        if triggering_event:
            deity.associated_events.append(triggering_event)

        self.deities[deity_id] = deity

        return deity

    def _get_deity_attributes(self, domain: DeityDomain) -> Dict:
        """Get default attributes for deity domain"""

        attributes = {
            DeityDomain.SUN: {'power': 1.0, 'benevolence': 0.8},
            DeityDomain.SKY: {'power': 0.9, 'benevolence': 0.5},
            DeityDomain.WAR: {'power': 0.8, 'benevolence': 0.2},
            DeityDomain.EARTH: {'power': 0.9, 'benevolence': 0.9},
            DeityDomain.WISDOM: {'power': 0.7, 'benevolence': 0.8},
            DeityDomain.DEATH: {'power': 0.9, 'benevolence': 0.3},
            DeityDomain.LOVE: {'power': 0.6, 'benevolence': 1.0},
            DeityDomain.CHAOS: {'power': 0.7, 'benevolence': 0.3},
        }

        return attributes.get(domain, {'power': 0.5, 'benevolence': 0.5})

    # ===== RELIGION FOUNDING =====

    def found_religion(
        self,
        founder_id: str,
        founder_name: str,
        religion_type: ReligionType,
        current_tick: int,
        initial_beliefs: Optional[List[str]] = None
    ) -> Religion:
        """Agent founds a new religion"""

        religion_id = str(uuid.uuid4())

        # Generate religion name
        name = self._generate_religion_name(religion_type, founder_name)

        religion = Religion(
            id=religion_id,
            name=name,
            religion_type=religion_type,
            founder_id=founder_id,
            founder_name=founder_name,
            founded_tick=current_tick,
            followers={founder_id},
            priests={founder_id}  # Founder is first priest
        )

        # Set initial beliefs
        if initial_beliefs:
            religion.core_beliefs = initial_beliefs
        else:
            religion.core_beliefs = self._generate_core_beliefs(religion_type)

        # Set regular rituals based on type
        religion.regular_rituals = self._get_default_rituals(religion_type)

        self.religions[religion_id] = religion
        self.total_religions_founded += 1

        return religion

    def _generate_religion_name(self, religion_type: ReligionType, founder_name: str) -> str:
        """Generate name for religion"""

        prefixes = {
            ReligionType.ANIMISM: ["Spirit", "Nature", "Soul"],
            ReligionType.POLYTHEISM: ["Pantheon", "Divine", "Celestial"],
            ReligionType.MONOTHEISM: ["One", "Eternal", "Supreme"],
            ReligionType.ANCESTOR_WORSHIP: ["Elder", "Forefather", "Ancient"],
            ReligionType.SHAMANISM: ["Spirit", "Mystical", "Shaman"],
            ReligionType.PANTHEISM: ["Universal", "All", "Cosmic"]
        }

        suffixes = ["Faith", "Way", "Path", "Order", "Tradition", "Believers"]

        prefix_options = prefixes.get(religion_type, ["Sacred"])
        prefix = random.choice(prefix_options)
        suffix = random.choice(suffixes)

        # Sometimes include founder name
        if random.random() < 0.3:
            return f"{founder_name}'s {prefix} {suffix}"
        else:
            return f"The {prefix} {suffix}"

    def _generate_core_beliefs(self, religion_type: ReligionType) -> List[str]:
        """Generate core beliefs for religion type"""

        beliefs = {
            ReligionType.ANIMISM: [
                "All things have spirits",
                "Respect nature to gain its favor",
                "Spirits can be angered or pleased"
            ],
            ReligionType.POLYTHEISM: [
                "Multiple gods rule different domains",
                "Worship brings divine favor",
                "Gods intervene in mortal affairs"
            ],
            ReligionType.MONOTHEISM: [
                "One supreme deity created all",
                "Faith in the one true god brings salvation",
                "Divine will guides the faithful"
            ],
            ReligionType.ANCESTOR_WORSHIP: [
                "Ancestors watch over the living",
                "Honor the dead to receive blessings",
                "Family lineage is sacred"
            ]
        }

        return beliefs.get(religion_type, ["Faith brings meaning"])

    def _get_default_rituals(self, religion_type: ReligionType) -> List[RitualType]:
        """Get default ritual types for religion"""

        rituals = {
            ReligionType.ANIMISM: [RitualType.PRAYER, RitualType.SACRIFICE, RitualType.MEDITATION],
            ReligionType.POLYTHEISM: [RitualType.CEREMONY, RitualType.SACRIFICE, RitualType.PRAYER],
            ReligionType.MONOTHEISM: [RitualType.PRAYER, RitualType.CEREMONY, RitualType.PILGRIMAGE],
            ReligionType.ANCESTOR_WORSHIP: [RitualType.FUNERAL, RitualType.CEREMONY, RitualType.PRAYER]
        }

        return rituals.get(religion_type, [RitualType.PRAYER])

    # ===== TEMPLES =====

    def build_temple(
        self,
        religion_id: str,
        builder_id: str,
        location: Tuple[float, float],
        current_tick: int,
        size: int = 1
    ) -> Optional[Temple]:
        """Build a temple for a religion"""

        if religion_id not in self.religions:
            return None

        temple_id = str(uuid.uuid4())
        religion = self.religions[religion_id]

        # Generate temple name
        name = f"{religion.name} Temple"

        temple = Temple(
            id=temple_id,
            name=name,
            religion_id=religion_id,
            location=location,
            builder_id=builder_id,
            built_at=current_tick,
            size=size,
            sacred_value=random.uniform(0.7, 1.0),
            priests={builder_id}
        )

        self.temples[temple_id] = temple
        religion.temples.add(temple_id)

        self.total_temples_built += 1

        return temple

    # ===== RITUALS =====

    def start_ritual(
        self,
        ritual_type: RitualType,
        religion_id: str,
        leader_id: str,
        location: Tuple[float, float],
        current_tick: int
    ) -> Ritual:
        """Start a religious ritual"""

        ritual_id = str(uuid.uuid4())

        ritual = Ritual(
            id=ritual_id,
            ritual_type=ritual_type,
            religion_id=religion_id,
            leader_id=leader_id,
            location=location,
            started_tick=current_tick,
            duration=random.randint(5, 20),
            spiritual_benefit=random.uniform(0.3, 0.7),
            social_cohesion=random.uniform(0.2, 0.5)
        )

        self.active_rituals[ritual_id] = ritual

        return ritual

    def update_rituals(self, current_tick: int) -> List[Ritual]:
        """Update active rituals, return completed ones"""

        completed = []

        for ritual_id, ritual in list(self.active_rituals.items()):
            ticks_elapsed = current_tick - ritual.started_tick

            if ticks_elapsed >= ritual.duration:
                ritual.completed = True
                completed.append(ritual)

                self.total_rituals_performed += 1
                del self.active_rituals[ritual_id]

        return completed

    # ===== CONVERSION & MEMBERSHIP =====

    def convert_agent(
        self,
        agent_id: str,
        religion_id: str,
        previous_religion_id: Optional[str] = None
    ) -> bool:
        """Convert agent to a religion"""

        if religion_id not in self.religions:
            return False

        religion = self.religions[religion_id]

        # Remove from previous religion
        if previous_religion_id and previous_religion_id in self.religions:
            prev_religion = self.religions[previous_religion_id]
            prev_religion.followers.discard(agent_id)
            prev_religion.priests.discard(agent_id)

        # Add to new religion
        religion.followers.add(agent_id)

        self.total_conversions += 1

        return True

    def ordain_priest(self, agent_id: str, religion_id: str) -> bool:
        """Make agent a priest of religion"""

        if religion_id not in self.religions:
            return False

        religion = self.religions[religion_id]

        if agent_id in religion.followers:
            religion.priests.add(agent_id)
            return True

        return False

    # ===== EVENT INTERPRETATION =====

    def interpret_event(
        self,
        event_type: str,
        event_description: str,
        witness_id: str
    ) -> Optional[str]:
        """Interpret event through religious lens"""

        # Record unexplained event
        self.unexplained_events.append({
            'type': event_type,
            'description': event_description,
            'witness': witness_id,
            'timestamp': datetime.now()
        })

        # Generate religious interpretation
        interpretations = {
            'lightning': "The sky god shows his wrath",
            'earthquake': "The earth mother is angry",
            'flood': "The water spirits have been disturbed",
            'fire_discovery': "Sacred flame has been revealed",
            'death': "The death god has claimed another soul",
            'birth': "The gods have blessed us with new life",
            'good_harvest': "The earth mother smiles upon us",
            'plague': "The gods punish our transgressions"
        }

        return interpretations.get(event_type, "The gods work in mysterious ways")

    # ===== QUERIES =====

    def get_agent_religion(self, agent_id: str) -> Optional[Religion]:
        """Get religion agent belongs to"""
        for religion in self.religions.values():
            if agent_id in religion.followers:
                return religion
        return None

    def is_priest(self, agent_id: str) -> bool:
        """Check if agent is a priest"""
        for religion in self.religions.values():
            if agent_id in religion.priests:
                return True
        return False

    def get_nearby_temples(
        self,
        location: Tuple[float, float],
        radius: float = 50.0
    ) -> List[Temple]:
        """Get temples within radius of location"""

        nearby = []
        for temple in self.temples.values():
            dist = ((location[0] - temple.location[0])**2 +
                   (location[1] - temple.location[1])**2)**0.5

            if dist < radius:
                nearby.append(temple)

        return nearby

    def get_statistics(self) -> Dict:
        """Get religion system statistics"""

        total_followers = sum(len(r.followers) for r in self.religions.values())
        total_priests = sum(len(r.priests) for r in self.religions.values())

        return {
            'total_religions': len(self.religions),
            'religions_founded': self.total_religions_founded,
            'total_followers': total_followers,
            'total_priests': total_priests,
            'total_temples': len(self.temples),
            'temples_built': self.total_temples_built,
            'active_rituals': len(self.active_rituals),
            'rituals_performed': self.total_rituals_performed,
            'total_conversions': self.total_conversions
        }
