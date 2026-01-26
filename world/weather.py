"""
Weather System - Environmental Dynamics

Dynamic weather that affects the world and agents:
- Rain increases water, helps plants grow
- Drought decreases water, slows regeneration
- Snow slows movement, requires shelter
- Storms dangerous, buildings provide safety
- Heat waves increase thirst
- Fog reduces visibility

Features:
- Seasonal weather patterns
- Weather transitions (can't go sunny → blizzard instantly)
- Weather effects on resources
- Weather effects on agents
- Weather history tracking
"""

import random
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class WeatherType(Enum):
    """Types of weather"""
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORMY = "stormy"
    SNOWY = "snowy"
    BLIZZARD = "blizzard"
    FOGGY = "foggy"
    DROUGHT = "drought"
    HEAT_WAVE = "heat_wave"


@dataclass
class WeatherEffects:
    """Effects of weather on world and agents"""
    # Resource modifiers (multipliers)
    water_regeneration: float = 1.0
    food_regeneration: float = 1.0
    wood_regeneration: float = 1.0

    # Agent effects
    energy_drain: float = 0.0  # Extra energy drain per tick
    movement_speed: float = 1.0  # Movement speed multiplier
    gathering_efficiency: float = 1.0  # Gathering yield multiplier
    shelter_required: bool = False  # Agents seek shelter
    danger_level: float = 0.0  # Damage to exposed agents

    # Visibility
    visibility_range: float = 1.0  # Perception range multiplier

    # Description
    description: str = ""
    emoji: str = "☀️"


class WeatherSystem:
    """Manages dynamic weather in the world"""

    # Weather type definitions with their effects
    WEATHER_EFFECTS = {
        WeatherType.SUNNY: WeatherEffects(
            water_regeneration=0.8,
            food_regeneration=1.2,
            wood_regeneration=1.1,
            energy_drain=0.0,
            movement_speed=1.0,
            gathering_efficiency=1.1,
            description="Clear skies, perfect conditions",
            emoji="☀️"
        ),
        WeatherType.CLOUDY: WeatherEffects(
            water_regeneration=1.0,
            food_regeneration=1.0,
            wood_regeneration=1.0,
            energy_drain=0.0,
            movement_speed=1.0,
            gathering_efficiency=1.0,
            description="Overcast but calm",
            emoji="☁️"
        ),
        WeatherType.RAINY: WeatherEffects(
            water_regeneration=2.5,  # Rain refills water sources!
            food_regeneration=1.5,  # Plants love rain
            wood_regeneration=1.3,
            energy_drain=0.1,
            movement_speed=0.8,
            gathering_efficiency=0.7,  # Harder to gather in rain
            description="Steady rainfall, refilling water sources",
            emoji="🌧️"
        ),
        WeatherType.STORMY: WeatherEffects(
            water_regeneration=3.0,  # Heavy rain
            food_regeneration=0.8,  # Storms damage crops
            wood_regeneration=0.7,
            energy_drain=0.3,
            movement_speed=0.5,
            gathering_efficiency=0.3,
            shelter_required=True,
            danger_level=0.5,  # Lightning, falling trees
            visibility_range=0.6,
            description="Dangerous storms, seek shelter!",
            emoji="⛈️"
        ),
        WeatherType.SNOWY: WeatherEffects(
            water_regeneration=1.5,  # Snow melts to water
            food_regeneration=0.3,  # Plants dormant
            wood_regeneration=0.2,
            energy_drain=0.2,  # Cold drains energy
            movement_speed=0.6,
            gathering_efficiency=0.5,
            shelter_required=True,
            visibility_range=0.7,
            description="Heavy snowfall, cold weather",
            emoji="❄️"
        ),
        WeatherType.BLIZZARD: WeatherEffects(
            water_regeneration=2.0,
            food_regeneration=0.1,
            wood_regeneration=0.1,
            energy_drain=0.5,  # Extreme cold
            movement_speed=0.3,
            gathering_efficiency=0.1,
            shelter_required=True,
            danger_level=1.0,  # Deadly cold
            visibility_range=0.3,
            description="Blizzard conditions, extreme danger!",
            emoji="🌨️"
        ),
        WeatherType.FOGGY: WeatherEffects(
            water_regeneration=1.2,
            food_regeneration=1.0,
            wood_regeneration=1.0,
            energy_drain=0.0,
            movement_speed=0.7,
            gathering_efficiency=0.8,
            visibility_range=0.4,
            description="Dense fog, limited visibility",
            emoji="🌫️"
        ),
        WeatherType.DROUGHT: WeatherEffects(
            water_regeneration=0.1,  # Water sources dry up!
            food_regeneration=0.3,  # Plants wither
            wood_regeneration=0.5,
            energy_drain=0.15,  # Heat exhaustion
            movement_speed=0.9,
            gathering_efficiency=0.6,
            description="Severe drought, water scarce",
            emoji="☀️💀"
        ),
        WeatherType.HEAT_WAVE: WeatherEffects(
            water_regeneration=0.3,
            food_regeneration=0.5,
            wood_regeneration=0.7,
            energy_drain=0.25,
            movement_speed=0.7,
            gathering_efficiency=0.7,
            danger_level=0.3,  # Heat stroke risk
            description="Extreme heat, stay hydrated!",
            emoji="🔥"
        ),
    }

    # Seasonal weather probabilities
    SEASONAL_WEATHER = {
        "spring": {
            WeatherType.SUNNY: 0.35,
            WeatherType.CLOUDY: 0.25,
            WeatherType.RAINY: 0.30,
            WeatherType.STORMY: 0.05,
            WeatherType.FOGGY: 0.05,
        },
        "summer": {
            WeatherType.SUNNY: 0.50,
            WeatherType.CLOUDY: 0.20,
            WeatherType.RAINY: 0.15,
            WeatherType.STORMY: 0.05,
            WeatherType.HEAT_WAVE: 0.07,
            WeatherType.DROUGHT: 0.03,
        },
        "fall": {
            WeatherType.SUNNY: 0.30,
            WeatherType.CLOUDY: 0.30,
            WeatherType.RAINY: 0.25,
            WeatherType.FOGGY: 0.10,
            WeatherType.STORMY: 0.05,
        },
        "winter": {
            WeatherType.CLOUDY: 0.30,
            WeatherType.SNOWY: 0.35,
            WeatherType.BLIZZARD: 0.10,
            WeatherType.SUNNY: 0.20,
            WeatherType.FOGGY: 0.05,
        }
    }

    # Weather transition compatibility (can't go sunny → blizzard instantly)
    WEATHER_TRANSITIONS = {
        WeatherType.SUNNY: [WeatherType.SUNNY, WeatherType.CLOUDY, WeatherType.HEAT_WAVE],
        WeatherType.CLOUDY: [WeatherType.SUNNY, WeatherType.CLOUDY, WeatherType.RAINY, WeatherType.FOGGY],
        WeatherType.RAINY: [WeatherType.CLOUDY, WeatherType.RAINY, WeatherType.STORMY, WeatherType.FOGGY],
        WeatherType.STORMY: [WeatherType.RAINY, WeatherType.STORMY, WeatherType.CLOUDY],
        WeatherType.SNOWY: [WeatherType.CLOUDY, WeatherType.SNOWY, WeatherType.BLIZZARD, WeatherType.FOGGY],
        WeatherType.BLIZZARD: [WeatherType.SNOWY, WeatherType.BLIZZARD, WeatherType.CLOUDY],
        WeatherType.FOGGY: [WeatherType.FOGGY, WeatherType.CLOUDY, WeatherType.RAINY],
        WeatherType.DROUGHT: [WeatherType.DROUGHT, WeatherType.SUNNY, WeatherType.HEAT_WAVE],
        WeatherType.HEAT_WAVE: [WeatherType.HEAT_WAVE, WeatherType.SUNNY, WeatherType.DROUGHT],
    }

    def __init__(self):
        self.current_weather = WeatherType.SUNNY
        self.weather_duration = 0  # Ticks remaining
        self.min_duration = 50  # Min ticks per weather
        self.max_duration = 200  # Max ticks per weather

        # History tracking
        self.weather_history: List[Dict] = []
        self.total_weather_changes = 0

        # Statistics
        self.weather_counts = {w: 0 for w in WeatherType}
        self.weather_counts[WeatherType.SUNNY] = 1

    def update(self, season: str, current_tick: int):
        """
        Update weather system.
        Called each tick to check for weather changes.
        """
        self.weather_duration -= 1

        # Time to change weather?
        if self.weather_duration <= 0:
            self._change_weather(season, current_tick)

    def _change_weather(self, season: str, current_tick: int):
        """Change to new weather based on season and transitions"""
        # Get possible transitions from current weather
        possible_transitions = self.WEATHER_TRANSITIONS.get(
            self.current_weather,
            list(WeatherType)
        )

        # Filter by seasonal probabilities
        seasonal_weather = self.SEASONAL_WEATHER.get(season, {})

        # Build weighted choices
        choices = []
        weights = []

        for weather in possible_transitions:
            if weather in seasonal_weather:
                choices.append(weather)
                weights.append(seasonal_weather[weather])

        # Fallback if no valid transitions
        if not choices:
            choices = list(seasonal_weather.keys())
            weights = list(seasonal_weather.values())

        # Select new weather
        old_weather = self.current_weather
        self.current_weather = random.choices(choices, weights=weights)[0]

        # Set duration
        self.weather_duration = random.randint(self.min_duration, self.max_duration)

        # Track statistics
        self.weather_counts[self.current_weather] += 1
        self.total_weather_changes += 1

        # Record in history
        self.weather_history.append({
            'tick': current_tick,
            'old_weather': old_weather.value,
            'new_weather': self.current_weather.value,
            'duration': self.weather_duration
        })

        # Keep history manageable
        if len(self.weather_history) > 100:
            self.weather_history.pop(0)

        print(f"🌦️  Weather changed: {old_weather.value} → {self.current_weather.value} (duration: {self.weather_duration} ticks)")

    def get_current_effects(self) -> WeatherEffects:
        """Get current weather effects"""
        return self.WEATHER_EFFECTS.get(
            self.current_weather,
            self.WEATHER_EFFECTS[WeatherType.SUNNY]
        )

    def apply_weather_to_agent(self, agent_health: float, agent_energy: float, has_shelter: bool) -> Dict:
        """
        Apply weather effects to an agent.
        Returns damage and energy drain.
        """
        effects = self.get_current_effects()

        damage = 0.0
        energy_drain = effects.energy_drain

        # Shelter protects from dangerous weather
        if effects.shelter_required and not has_shelter:
            damage = effects.danger_level * 0.5  # Damage per tick
            energy_drain *= 2.0  # Extra energy drain when exposed

        return {
            'damage': damage,
            'energy_drain': energy_drain,
            'needs_shelter': effects.shelter_required and not has_shelter
        }

    def get_statistics(self) -> Dict:
        """Get weather system statistics"""
        effects = self.get_current_effects()

        return {
            'current_weather': self.current_weather.value,
            'weather_emoji': effects.emoji,
            'weather_description': effects.description,
            'duration_remaining': self.weather_duration,
            'total_changes': self.total_weather_changes,
            'weather_counts': {w.value: c for w, c in self.weather_counts.items()},
            'recent_history': self.weather_history[-10:],  # Last 10 changes
            'effects': {
                'water_regen': effects.water_regeneration,
                'food_regen': effects.food_regeneration,
                'movement_speed': effects.movement_speed,
                'gathering_efficiency': effects.gathering_efficiency,
                'shelter_required': effects.shelter_required,
                'danger_level': effects.danger_level,
            }
        }

    def force_weather(self, weather_type: WeatherType, duration: int = 100):
        """Force specific weather (for testing/god mode)"""
        old_weather = self.current_weather
        self.current_weather = weather_type
        self.weather_duration = duration
        print(f"⚡ Weather forced: {old_weather.value} → {weather_type.value}")
