"""
Natural Disasters System - Dramatic World Events

Catastrophic events that challenge civilizations:
- Earthquakes damage buildings
- Floods destroy resources
- Fires spread and consume
- Tornadoes devastate areas
- Meteors create craters
- Plagues spread disease
- Droughts (integrated with weather)
- Volcanic eruptions

Features:
- Multiple disaster types
- Location-based effects
- Warning systems
- Disaster severity levels
- Building/agent damage
- Resource destruction
- Disaster history tracking
"""

import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


class DisasterType(Enum):
    """Types of natural disasters"""
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    WILDFIRE = "wildfire"
    TORNADO = "tornado"
    METEOR = "meteor"
    PLAGUE = "plague"
    VOLCANO = "volcano"
    LANDSLIDE = "landslide"
    TSUNAMI = "tsunami"


class DisasterSeverity(Enum):
    """Severity levels of disasters"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


@dataclass
class Disaster:
    """A disaster event"""
    disaster_type: DisasterType
    severity: DisasterSeverity
    location_x: float
    location_y: float
    radius: float  # Affected area radius
    tick: int
    casualties: int = 0
    buildings_destroyed: int = 0
    buildings_damaged: int = 0
    agents_injured: int = 0
    resources_lost: Dict[str, float] = None
    warning_given: bool = False

    def __post_init__(self):
        if self.resources_lost is None:
            self.resources_lost = {}


@dataclass
class DisasterEffects:
    """Effects of a disaster on the world"""
    building_damage_chance: float = 0.0  # Chance to damage buildings
    building_destroy_chance: float = 0.0  # Chance to destroy buildings
    agent_damage: float = 0.0  # Direct damage to agents
    agent_death_chance: float = 0.0  # Chance of instant death
    resource_destruction: float = 0.0  # % of resources destroyed
    fire_spread_chance: float = 0.0  # Chance to start fires
    can_warn: bool = False  # Can we warn before it happens?
    warning_time: int = 0  # Ticks of warning
    emoji: str = "⚠️"
    description: str = ""


class NaturalDisasterSystem:
    """Manages natural disasters in the world"""

    # Disaster definitions
    DISASTER_EFFECTS = {
        DisasterType.EARTHQUAKE: {
            DisasterSeverity.MINOR: DisasterEffects(
                building_damage_chance=0.3,
                building_destroy_chance=0.05,
                agent_damage=5.0,
                agent_death_chance=0.01,
                resource_destruction=0.1,
                can_warn=False,
                emoji="🌍",
                description="Minor tremors shake the ground"
            ),
            DisasterSeverity.MODERATE: DisasterEffects(
                building_damage_chance=0.6,
                building_destroy_chance=0.15,
                agent_damage=15.0,
                agent_death_chance=0.05,
                resource_destruction=0.25,
                can_warn=False,
                emoji="🌍",
                description="Earthquake rattles buildings"
            ),
            DisasterSeverity.MAJOR: DisasterEffects(
                building_damage_chance=0.85,
                building_destroy_chance=0.40,
                agent_damage=30.0,
                agent_death_chance=0.15,
                resource_destruction=0.50,
                can_warn=False,
                emoji="🌍💥",
                description="Massive earthquake devastates area"
            ),
            DisasterSeverity.CATASTROPHIC: DisasterEffects(
                building_damage_chance=1.0,
                building_destroy_chance=0.80,
                agent_damage=60.0,
                agent_death_chance=0.40,
                resource_destruction=0.80,
                can_warn=False,
                emoji="🌍💥💥",
                description="Catastrophic earthquake - total destruction"
            ),
        },
        DisasterType.FLOOD: {
            DisasterSeverity.MINOR: DisasterEffects(
                building_damage_chance=0.2,
                building_destroy_chance=0.0,
                agent_damage=5.0,
                resource_destruction=0.3,
                can_warn=True,
                warning_time=20,
                emoji="💧",
                description="Rising water floods low areas"
            ),
            DisasterSeverity.MODERATE: DisasterEffects(
                building_damage_chance=0.5,
                building_destroy_chance=0.1,
                agent_damage=15.0,
                agent_death_chance=0.05,
                resource_destruction=0.6,
                can_warn=True,
                warning_time=15,
                emoji="🌊",
                description="Flood waters sweep through area"
            ),
            DisasterSeverity.MAJOR: DisasterEffects(
                building_damage_chance=0.8,
                building_destroy_chance=0.4,
                agent_damage=30.0,
                agent_death_chance=0.20,
                resource_destruction=0.85,
                can_warn=True,
                warning_time=10,
                emoji="🌊💥",
                description="Massive flooding destroys everything"
            ),
        },
        DisasterType.WILDFIRE: {
            DisasterSeverity.MINOR: DisasterEffects(
                building_damage_chance=0.4,
                building_destroy_chance=0.2,
                agent_damage=10.0,
                agent_death_chance=0.03,
                resource_destruction=0.5,
                fire_spread_chance=0.3,
                can_warn=True,
                warning_time=15,
                emoji="🔥",
                description="Small fire spreading through area"
            ),
            DisasterSeverity.MODERATE: DisasterEffects(
                building_damage_chance=0.7,
                building_destroy_chance=0.5,
                agent_damage=25.0,
                agent_death_chance=0.10,
                resource_destruction=0.75,
                fire_spread_chance=0.6,
                can_warn=True,
                warning_time=10,
                emoji="🔥🔥",
                description="Raging wildfire consumes everything"
            ),
            DisasterSeverity.MAJOR: DisasterEffects(
                building_damage_chance=1.0,
                building_destroy_chance=0.90,
                agent_damage=50.0,
                agent_death_chance=0.30,
                resource_destruction=0.95,
                fire_spread_chance=0.9,
                can_warn=True,
                warning_time=5,
                emoji="🔥🔥🔥",
                description="Inferno engulfs the land"
            ),
        },
        DisasterType.TORNADO: {
            DisasterSeverity.MODERATE: DisasterEffects(
                building_damage_chance=0.9,
                building_destroy_chance=0.6,
                agent_damage=35.0,
                agent_death_chance=0.20,
                resource_destruction=0.7,
                can_warn=True,
                warning_time=5,
                emoji="🌪️",
                description="Tornado tears through settlement"
            ),
            DisasterSeverity.MAJOR: DisasterEffects(
                building_damage_chance=1.0,
                building_destroy_chance=0.95,
                agent_damage=60.0,
                agent_death_chance=0.45,
                resource_destruction=0.90,
                can_warn=True,
                warning_time=3,
                emoji="🌪️💥",
                description="Massive tornado obliterates everything"
            ),
        },
        DisasterType.METEOR: {
            DisasterSeverity.MODERATE: DisasterEffects(
                building_damage_chance=1.0,
                building_destroy_chance=0.8,
                agent_damage=40.0,
                agent_death_chance=0.30,
                resource_destruction=0.9,
                can_warn=False,
                emoji="☄️",
                description="Meteor impact creates crater"
            ),
            DisasterSeverity.CATASTROPHIC: DisasterEffects(
                building_damage_chance=1.0,
                building_destroy_chance=1.0,
                agent_damage=100.0,
                agent_death_chance=0.90,
                resource_destruction=1.0,
                can_warn=False,
                emoji="☄️💥💥",
                description="Extinction-level meteor strike"
            ),
        },
        DisasterType.PLAGUE: {
            DisasterSeverity.MINOR: DisasterEffects(
                agent_damage=10.0,
                agent_death_chance=0.05,
                can_warn=True,
                warning_time=30,
                emoji="🦠",
                description="Disease begins to spread"
            ),
            DisasterSeverity.MODERATE: DisasterEffects(
                agent_damage=25.0,
                agent_death_chance=0.15,
                can_warn=True,
                warning_time=20,
                emoji="🦠☠️",
                description="Plague spreads through population"
            ),
            DisasterSeverity.MAJOR: DisasterEffects(
                agent_damage=50.0,
                agent_death_chance=0.40,
                can_warn=True,
                warning_time=15,
                emoji="🦠☠️☠️",
                description="Deadly plague decimates civilization"
            ),
        },
        DisasterType.VOLCANO: {
            DisasterSeverity.MODERATE: DisasterEffects(
                building_damage_chance=0.7,
                building_destroy_chance=0.4,
                agent_damage=30.0,
                agent_death_chance=0.15,
                resource_destruction=0.6,
                fire_spread_chance=0.5,
                can_warn=True,
                warning_time=25,
                emoji="🌋",
                description="Volcanic eruption spews lava"
            ),
            DisasterSeverity.MAJOR: DisasterEffects(
                building_damage_chance=1.0,
                building_destroy_chance=0.85,
                agent_damage=70.0,
                agent_death_chance=0.50,
                resource_destruction=0.95,
                fire_spread_chance=0.9,
                can_warn=True,
                warning_time=20,
                emoji="🌋💥",
                description="Massive eruption buries the land"
            ),
        },
        DisasterType.LANDSLIDE: {
            DisasterSeverity.MODERATE: DisasterEffects(
                building_damage_chance=0.6,
                building_destroy_chance=0.3,
                agent_damage=20.0,
                agent_death_chance=0.10,
                resource_destruction=0.4,
                can_warn=True,
                warning_time=5,
                emoji="⛰️",
                description="Landslide buries structures"
            ),
        },
        DisasterType.TSUNAMI: {
            DisasterSeverity.MAJOR: DisasterEffects(
                building_damage_chance=1.0,
                building_destroy_chance=0.9,
                agent_damage=60.0,
                agent_death_chance=0.50,
                resource_destruction=0.95,
                can_warn=True,
                warning_time=10,
                emoji="🌊💥💥",
                description="Tsunami wave devastates coast"
            ),
        },
    }

    # Base disaster chances (per 1000 ticks; a day is 144). Together about one
    # disaster every 38 days, more in bad weather, in spring, and with more
    # people. (They used to be rolled as chances per tick, so a disaster came
    # within a few ticks of every cooldown ending: one every 1.4 days whatever
    # the weather, 27 times the rate written here.)
    BASE_DISASTER_CHANCES = {
        DisasterType.EARTHQUAKE: 0.05,
        DisasterType.FLOOD: 0.03,
        DisasterType.WILDFIRE: 0.04,
        DisasterType.TORNADO: 0.02,
        DisasterType.METEOR: 0.001,
        DisasterType.PLAGUE: 0.02,
        DisasterType.VOLCANO: 0.005,
        DisasterType.LANDSLIDE: 0.015,
        DisasterType.TSUNAMI: 0.003,
    }

    ACTIVE_TICKS = 6   # one hour

    def __init__(self, world_width: int = 100, world_height: int = 100):
        self.world_width = world_width
        self.world_height = world_height

        # Disaster tracking
        self.active_disasters: List[Disaster] = []
        self.disaster_history: List[Disaster] = []
        self.pending_warnings: List[Dict] = []  # Disasters with advance warning
        self._last_tick = 0

        # Statistics
        self.total_disasters = 0
        self.disaster_counts = {d: 0 for d in DisasterType}
        self.total_casualties = 0
        self.total_buildings_destroyed = 0

        # Disaster cooldown (prevent disaster spam)
        self.ticks_since_last_disaster = 0
        self.min_disaster_cooldown = 200  # Min ticks between disasters

    def update(self, current_tick: int, season: str, current_weather: str, population: int):
        """
        Update disaster system each tick.
        Check for new disasters and process warnings.
        """
        self.ticks_since_last_disaster += 1
        self._last_tick = current_tick

        # A disaster is "active" (shown, perceived) for ACTIVE_TICKS after it
        # hits; after that it is history. (It used to stay active forever, so
        # anyone inside any past disaster's radius was told to evacuate.)
        self.active_disasters = [d for d in self.active_disasters
                                 if current_tick - d.tick < self.ACTIVE_TICKS]

        # Process pending warnings
        self._process_warnings(current_tick)

        # Check if we should trigger a disaster
        if self.ticks_since_last_disaster >= self.min_disaster_cooldown:
            self._check_for_disaster(current_tick, season, current_weather, population)

    def _check_for_disaster(self, current_tick: int, season: str, weather: str, population: int):
        """Check if a disaster should occur"""
        # Calculate disaster chance modifiers
        weather_modifier = self._get_weather_modifier(weather)
        season_modifier = self._get_season_modifier(season)
        population_modifier = 1.0 + (population / 100.0)  # More people = more risk

        # Roll for each disaster type
        for disaster_type, base_chance in self.BASE_DISASTER_CHANCES.items():
            # Adjust chance based on conditions; this roll is for one tick
            final_chance = base_chance / 1000.0 * weather_modifier * season_modifier * population_modifier

            # Random roll
            if random.random() < final_chance:
                self._trigger_disaster(disaster_type, current_tick)
                break  # Only one disaster at a time

    def _get_weather_modifier(self, weather: str) -> float:
        """Weather affects disaster chances"""
        modifiers = {
            'stormy': 3.0,  # Storms increase flood/tornado risk
            'rainy': 2.0,   # Rain increases flood/landslide risk
            'heat_wave': 4.0,  # Heat increases fire risk
            'drought': 3.0,  # Drought increases fire risk
            'sunny': 1.0,
            'cloudy': 1.0,
            'snowy': 0.5,   # Snow reduces most disasters
            'foggy': 1.0,
        }
        return modifiers.get(weather, 1.0)

    def _get_season_modifier(self, season: str) -> float:
        """Seasons affect disaster chances"""
        modifiers = {
            'spring': 1.5,  # Spring floods
            'summer': 1.3,  # Summer fires
            'autumn': 1.2,  # Autumn storms (the world's name for it; this said 'fall', which never matched)
            'winter': 0.8,  # Winter quieter
        }
        return modifiers.get(season, 1.0)

    def _trigger_disaster(self, disaster_type: DisasterType, current_tick: int, severity: Optional[DisasterSeverity] = None):
        """Trigger a specific disaster"""
        # Determine severity (use provided or roll random)
        if severity is None:
            severity = self._roll_severity()

        # Get disaster effects
        effects_by_severity = self.DISASTER_EFFECTS.get(disaster_type, {})
        if severity not in effects_by_severity:
            # Use most appropriate severity
            severity = list(effects_by_severity.keys())[0]

        effects = effects_by_severity[severity]

        # Random location
        location_x = random.uniform(10, self.world_width - 10)
        location_y = random.uniform(10, self.world_height - 10)

        # Radius based on severity
        radius = {
            DisasterSeverity.MINOR: 15.0,
            DisasterSeverity.MODERATE: 25.0,
            DisasterSeverity.MAJOR: 40.0,
            DisasterSeverity.CATASTROPHIC: 60.0,
        }[severity]

        # Create disaster
        disaster = Disaster(
            disaster_type=disaster_type,
            severity=severity,
            location_x=location_x,
            location_y=location_y,
            radius=radius,
            tick=current_tick
        )

        # Can we warn?
        if effects.can_warn and effects.warning_time > 0:
            # Add to pending warnings
            self.pending_warnings.append({
                'disaster': disaster,
                'warning_tick': current_tick,
                'impact_tick': current_tick + effects.warning_time,
                'effects': effects
            })
            disaster.warning_given = True
            print(f"⚠️  DISASTER WARNING: {effects.description} expected in {effects.warning_time} ticks!")
        else:
            # Immediate disaster
            self.active_disasters.append(disaster)
            self._apply_disaster_effects(disaster, effects)
            print(f"{effects.emoji} DISASTER: {effects.description} at ({location_x:.0f}, {location_y:.0f})!")

        self.ticks_since_last_disaster = 0
        self.total_disasters += 1
        self.disaster_counts[disaster_type] += 1

    def _process_warnings(self, current_tick: int):
        """Process pending disaster warnings"""
        for warning in self.pending_warnings[:]:
            if current_tick >= warning['impact_tick']:
                # Disaster hits now! It happens at this tick: the engine applies
                # disasters whose tick is the current one. (It kept the tick of
                # its warning, so no warned disaster ever did anything: only
                # earthquakes, which come without warning, ever hit.)
                disaster = warning['disaster']
                effects = warning['effects']
                disaster.tick = current_tick

                self.active_disasters.append(disaster)
                self._apply_disaster_effects(disaster, effects)

                print(f"{effects.emoji} DISASTER IMPACT: {effects.description}!")
                self.pending_warnings.remove(warning)

    def _apply_disaster_effects(self, disaster: Disaster, effects: DisasterEffects):
        """Apply disaster effects (called by simulation engine)"""
        # Effects are applied by the simulation engine
        # This just logs and tracks
        self.disaster_history.append(disaster)

        # Keep history manageable
        if len(self.disaster_history) > 50:
            self.disaster_history.pop(0)

    def _roll_severity(self) -> DisasterSeverity:
        """Randomly determine disaster severity"""
        roll = random.random()

        if roll < 0.50:
            return DisasterSeverity.MINOR
        elif roll < 0.80:
            return DisasterSeverity.MODERATE
        elif roll < 0.95:
            return DisasterSeverity.MAJOR
        else:
            return DisasterSeverity.CATASTROPHIC

    def get_disaster_effects(self, disaster: Disaster) -> Optional[DisasterEffects]:
        """Get effects for a disaster"""
        effects_by_severity = self.DISASTER_EFFECTS.get(disaster.disaster_type, {})
        return effects_by_severity.get(disaster.severity)

    def is_location_affected(self, x: float, y: float, disaster: Disaster) -> bool:
        """Check if a location is affected by a disaster"""
        dx = x - disaster.location_x
        dy = y - disaster.location_y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance <= disaster.radius

    def force_disaster(self, disaster_type: DisasterType, severity: DisasterSeverity, current_tick: int):
        """Force a specific disaster (for testing/god mode)"""
        self._trigger_disaster(disaster_type, current_tick, severity)

    def get_statistics(self) -> Dict:
        """Get disaster system statistics"""
        current_disasters = []
        for disaster in self.active_disasters:
            effects = self.get_disaster_effects(disaster)
            current_disasters.append({
                'type': disaster.disaster_type.value,
                'severity': disaster.severity.value,
                'location': {'x': disaster.location_x, 'y': disaster.location_y},
                'radius': disaster.radius,
                'emoji': effects.emoji if effects else '⚠️',
                'description': effects.description if effects else 'Unknown disaster',
                'casualties': disaster.casualties,
                'buildings_destroyed': disaster.buildings_destroyed,
            })

        warnings = []
        for warning in self.pending_warnings:
            disaster = warning['disaster']
            effects = warning['effects']
            warnings.append({
                'type': disaster.disaster_type.value,
                'emoji': effects.emoji,
                'description': effects.description,
                'time_until_impact': warning['impact_tick'] - getattr(self, '_last_tick', warning['warning_tick']),
                'impact_tick': warning['impact_tick'],
                'location': {'x': disaster.location_x, 'y': disaster.location_y},
            })

        return {
            'total_disasters': self.total_disasters,
            'disaster_counts': {d.value: c for d, c in self.disaster_counts.items()},
            'total_casualties': self.total_casualties,
            'total_buildings_destroyed': self.total_buildings_destroyed,
            'active_disasters': current_disasters,
            'pending_warnings': warnings,
            'ticks_since_last': self.ticks_since_last_disaster,
            'recent_history': [
                {
                    'type': d.disaster_type.value,
                    'severity': d.severity.value,
                    'tick': d.tick,
                    'casualties': d.casualties,
                    'buildings_destroyed': d.buildings_destroyed,
                }
                for d in self.disaster_history[-10:]
            ]
        }
