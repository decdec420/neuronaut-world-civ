"""
Psychology Engine - Realistic human psychology model for agents

Based on established psychological research:
- Maslow's Hierarchy of Needs
- Big Five Personality Traits
- Emotional psychology
- Decision-making under needs and emotions
"""

import random
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from enum import Enum
import math

logger = logging.getLogger(__name__)


class NeedType(Enum):
    """Types of psychological needs (Maslow + additions)"""
    # Physiological
    HUNGER = "hunger"
    THIRST = "thirst"
    SLEEP = "sleep"
    SEX = "sex"

    # Safety
    SECURITY = "security"
    RESOURCES = "resources"
    SHELTER = "shelter"

    # Social
    BELONGING = "belonging"
    FRIENDSHIP = "friendship"
    ROMANCE = "romance"

    # Esteem
    STATUS = "status"
    ACHIEVEMENT = "achievement"
    RECOGNITION = "recognition"

    # Self-Actualization
    CREATIVITY = "creativity"
    MEANING = "meaning"
    GROWTH = "growth"


class EmotionType(Enum):
    """Basic emotions"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    LOVE = "love"
    LUST = "lust"
    JEALOUSY = "jealousy"
    PRIDE = "pride"
    SHAME = "shame"
    EXCITEMENT = "excitement"


@dataclass
class Need:
    """A single psychological need"""
    need_type: NeedType
    level: float = 0.5  # 0 = fully satisfied, 1 = desperate
    priority: int = 1  # Maslow hierarchy level (1=highest)
    decay_rate: float = 0.01  # How fast it increases per tick

    def update(self, delta_time: float = 1.0):
        """Needs increase over time"""
        self.level = min(1.0, self.level + self.decay_rate * delta_time)

    def satisfy(self, amount: float):
        """Reduce need level"""
        old_level = self.level
        self.level = max(0.0, self.level - amount)
        logger.debug(f"SATISFY: {self.need_type.value} {old_level:.2f} → {self.level:.2f} (reduced by {amount:.2f})")

    def get_urgency(self) -> float:
        """How urgent is this need? (0-1, considers priority)"""
        # Higher priority needs become urgent faster
        urgency = self.level * (2.0 if self.priority == 1 else 1.5 if self.priority == 2 else 1.0)
        return min(1.0, urgency)


@dataclass
class NeedState:
    """Collection of all needs for an agent"""
    needs: Dict[NeedType, Need] = field(default_factory=dict)

    @classmethod
    def create_default(cls) -> 'NeedState':
        """Create with default needs"""
        return cls(needs={
            # Physiological (Priority 1)
            NeedType.HUNGER: Need(NeedType.HUNGER, level=0.3, priority=1, decay_rate=0.02),
            NeedType.THIRST: Need(NeedType.THIRST, level=0.3, priority=1, decay_rate=0.03),
            NeedType.SLEEP: Need(NeedType.SLEEP, level=0.2, priority=1, decay_rate=0.015),
            NeedType.SEX: Need(NeedType.SEX, level=0.4, priority=2, decay_rate=0.005),

            # Safety (Priority 2)
            NeedType.SECURITY: Need(NeedType.SECURITY, level=0.5, priority=2, decay_rate=0.001),
            NeedType.RESOURCES: Need(NeedType.RESOURCES, level=0.6, priority=2, decay_rate=0.005),
            NeedType.SHELTER: Need(NeedType.SHELTER, level=0.4, priority=2, decay_rate=0.002),

            # Social (Priority 3)
            NeedType.BELONGING: Need(NeedType.BELONGING, level=0.5, priority=3, decay_rate=0.01),
            NeedType.FRIENDSHIP: Need(NeedType.FRIENDSHIP, level=0.6, priority=3, decay_rate=0.008),
            NeedType.ROMANCE: Need(NeedType.ROMANCE, level=0.7, priority=3, decay_rate=0.004),

            # Esteem (Priority 4)
            NeedType.STATUS: Need(NeedType.STATUS, level=0.6, priority=4, decay_rate=0.003),
            NeedType.ACHIEVEMENT: Need(NeedType.ACHIEVEMENT, level=0.7, priority=4, decay_rate=0.004),
            NeedType.RECOGNITION: Need(NeedType.RECOGNITION, level=0.6, priority=4, decay_rate=0.003),

            # Self-Actualization (Priority 5)
            NeedType.CREATIVITY: Need(NeedType.CREATIVITY, level=0.8, priority=5, decay_rate=0.002),
            NeedType.MEANING: Need(NeedType.MEANING, level=0.7, priority=5, decay_rate=0.001),
            NeedType.GROWTH: Need(NeedType.GROWTH, level=0.7, priority=5, decay_rate=0.002),
        })

    def update(self, delta_time: float = 1.0):
        """Update all needs"""
        for need in self.needs.values():
            need.update(delta_time)

    def get_most_urgent_need(self) -> Tuple[NeedType, float]:
        """Return the most urgent need and its urgency (breaks ties by priority)"""
        # Sort by urgency first, then by priority (lower number = higher priority)
        most_urgent = max(
            self.needs.items(),
            key=lambda x: (x[1].get_urgency(), -x[1].priority)  # Negative priority to prioritize lower numbers
        )
        return most_urgent[0], most_urgent[1].get_urgency()

    def get_urgent_needs(self, threshold: float = 0.7) -> List[NeedType]:
        """Get all needs above urgency threshold"""
        return [need_type for need_type, need in self.needs.items()
                if need.get_urgency() >= threshold]

    def satisfy_need(self, need_type: NeedType, amount: float):
        """Satisfy a specific need"""
        if need_type in self.needs:
            self.needs[need_type].satisfy(amount)

    def get_overall_satisfaction(self) -> float:
        """Overall life satisfaction (0-1, higher is better)"""
        # Inverse of average need level, weighted by priority
        weighted_needs = []
        weights = []

        for need in self.needs.values():
            weight = 3.0 if need.priority == 1 else 2.0 if need.priority == 2 else 1.0
            weighted_needs.append((1.0 - need.level) * weight)
            weights.append(weight)

        return sum(weighted_needs) / sum(weights) if weights else 0.5


@dataclass
class PersonalityProfile:
    """Big Five + additional personality traits"""
    # Big Five (0-1, 0.5 is average)
    openness: float = 0.5  # Creativity, curiosity, open-mindedness
    conscientiousness: float = 0.5  # Organization, discipline, planning
    extraversion: float = 0.5  # Social, assertive, energetic
    agreeableness: float = 0.5  # Cooperative, empathetic, trusting
    neuroticism: float = 0.5  # Anxiety, emotional instability, stress

    # Additional traits
    risk_taking: float = 0.5  # Willingness to take risks
    aggression: float = 0.3  # Tendency toward conflict
    sexuality: float = 0.5  # Sex drive intensity
    ambition: float = 0.5  # Drive for achievement and status
    creativity: float = 0.5  # Creative thinking and expression
    empathy: float = 0.5  # Understanding others' emotions
    rationality: float = 0.5  # Logic vs emotion in decisions

    @classmethod
    def random(cls) -> 'PersonalityProfile':
        """Generate random personality"""
        return cls(
            openness=random.gauss(0.5, 0.15),
            conscientiousness=random.gauss(0.5, 0.15),
            extraversion=random.gauss(0.5, 0.15),
            agreeableness=random.gauss(0.5, 0.15),
            neuroticism=random.gauss(0.5, 0.15),
            risk_taking=random.gauss(0.5, 0.15),
            aggression=random.gauss(0.3, 0.1),
            sexuality=random.gauss(0.5, 0.15),
            ambition=random.gauss(0.5, 0.15),
            creativity=random.gauss(0.5, 0.15),
            empathy=random.gauss(0.5, 0.15),
            rationality=random.gauss(0.5, 0.15),
        )

    def _clamp(self, value: float) -> float:
        """Clamp value between 0 and 1"""
        return max(0.0, min(1.0, value))

    def __post_init__(self):
        """Ensure all values are in valid range"""
        self.openness = self._clamp(self.openness)
        self.conscientiousness = self._clamp(self.conscientiousness)
        self.extraversion = self._clamp(self.extraversion)
        self.agreeableness = self._clamp(self.agreeableness)
        self.neuroticism = self._clamp(self.neuroticism)
        self.risk_taking = self._clamp(self.risk_taking)
        self.aggression = self._clamp(self.aggression)
        self.sexuality = self._clamp(self.sexuality)
        self.ambition = self._clamp(self.ambition)
        self.creativity = self._clamp(self.creativity)
        self.empathy = self._clamp(self.empathy)
        self.rationality = self._clamp(self.rationality)

    def compatibility_with(self, other: 'PersonalityProfile') -> float:
        """Calculate compatibility with another personality (0-1)"""
        # Similar extraversion helps
        extraversion_match = 1.0 - abs(self.extraversion - other.extraversion)

        # Complementary agreeableness (one should be agreeable)
        agreeableness_factor = max(self.agreeableness, other.agreeableness)

        # Similar openness helps
        openness_match = 1.0 - abs(self.openness - other.openness)

        # Low combined neuroticism is better
        neuroticism_factor = 1.0 - (self.neuroticism + other.neuroticism) / 2

        # Low combined aggression is better
        aggression_factor = 1.0 - (self.aggression + other.aggression) / 2

        # Weighted average
        compatibility = (
            extraversion_match * 0.25 +
            agreeableness_factor * 0.25 +
            openness_match * 0.2 +
            neuroticism_factor * 0.15 +
            aggression_factor * 0.15
        )

        return compatibility


@dataclass
class Emotion:
    """A single emotional state"""
    emotion_type: EmotionType
    intensity: float = 0.0  # 0-1
    decay_rate: float = 0.01  # How fast it fades (reduced from 0.1 - emotions now last 10x longer!)

    def update(self, delta_time: float = 1.0):
        """Emotions decay over time"""
        self.intensity = max(0.0, self.intensity - self.decay_rate * delta_time)

    def intensify(self, amount: float):
        """Increase emotion intensity"""
        self.intensity = min(1.0, self.intensity + amount)


@dataclass
class EmotionalState:
    """Collection of current emotions"""
    emotions: Dict[EmotionType, Emotion] = field(default_factory=dict)

    # Overall mood (-1 to 1, negative to positive)
    mood: float = 0.0

    # Stress level (0-1)
    stress: float = 0.0

    # Arousal level (0-1, general energy/activation)
    arousal: float = 0.5

    @classmethod
    def create_default(cls) -> 'EmotionalState':
        """Create with neutral emotions"""
        return cls(
            emotions={emo_type: Emotion(emo_type, intensity=0.0)
                     for emo_type in EmotionType},
            mood=0.0,
            stress=0.2,
            arousal=0.5
        )

    def update(self, delta_time: float = 1.0):
        """Update emotions (decay over time)"""
        for emotion in self.emotions.values():
            emotion.update(delta_time)

        # Update mood based on current emotions
        self.mood = self._calculate_mood()

        # Stress decays slowly
        self.stress = max(0.0, self.stress - 0.05 * delta_time)

        # Arousal trends toward 0.5
        self.arousal += (0.5 - self.arousal) * 0.1 * delta_time

    def _calculate_mood(self) -> float:
        """Calculate overall mood from emotions"""
        positive = (
            self.emotions[EmotionType.JOY].intensity +
            self.emotions[EmotionType.LOVE].intensity +
            self.emotions[EmotionType.EXCITEMENT].intensity +
            self.emotions[EmotionType.PRIDE].intensity
        )

        negative = (
            self.emotions[EmotionType.SADNESS].intensity +
            self.emotions[EmotionType.ANGER].intensity +
            self.emotions[EmotionType.FEAR].intensity +
            self.emotions[EmotionType.SHAME].intensity +
            self.emotions[EmotionType.JEALOUSY].intensity
        )

        # Range: -1 to 1
        return max(-1.0, min(1.0, (positive - negative) / 2))

    def trigger_emotion(self, emotion_type: EmotionType, intensity: float):
        """Trigger an emotional response"""
        if emotion_type in self.emotions:
            self.emotions[emotion_type].intensify(intensity)

    def get_dominant_emotion(self) -> Tuple[EmotionType, float]:
        """Get strongest current emotion"""
        if not self.emotions:
            return EmotionType.JOY, 0.0

        dominant = max(self.emotions.items(), key=lambda x: x[1].intensity)
        return dominant[0], dominant[1].intensity

    def is_emotionally_stable(self) -> bool:
        """Check if emotions are under control"""
        max_intensity = max(e.intensity for e in self.emotions.values())
        return max_intensity < 0.7 and self.stress < 0.6


class PsychologyEngine:
    """Main psychology engine for decision-making"""

    @staticmethod
    def calculate_action_motivation(
        need_state: NeedState,
        personality: PersonalityProfile,
        emotional_state: EmotionalState,
        action_type: str
    ) -> float:
        """
        Calculate motivation to perform an action based on psychology

        Returns: 0-1, how motivated the agent is to do this action
        """

        # Base motivation from needs
        need_motivation = PsychologyEngine._need_motivation(need_state, action_type)

        # Personality modulation
        personality_factor = PsychologyEngine._personality_factor(personality, action_type)

        # Emotional influence
        emotional_factor = PsychologyEngine._emotional_factor(emotional_state, action_type)

        # Combine factors
        motivation = need_motivation * personality_factor * emotional_factor

        return max(0.0, min(1.0, motivation))

    @staticmethod
    def _need_motivation(need_state: NeedState, action_type: str) -> float:
        """Calculate motivation from needs"""
        # Map actions to needs they satisfy
        action_need_map = {
            # SURVIVAL ACTIONS (critical!)
            'eat': [NeedType.HUNGER],  # FIXED: Added eat action
            'drink': [NeedType.THIRST],  # FIXED: Added drink action
            'gather_food': [NeedType.HUNGER],
            'gather_water': [NeedType.THIRST],
            'rest': [NeedType.SLEEP],
            'hunt': [NeedType.HUNGER],

            # SOCIAL ACTIONS
            'seek_romance': [NeedType.SEX, NeedType.ROMANCE],
            'socialize': [NeedType.BELONGING, NeedType.FRIENDSHIP],

            # PRODUCTIVITY ACTIONS
            'build': [NeedType.SHELTER, NeedType.SECURITY, NeedType.CREATIVITY],
            'gather_materials': [NeedType.RESOURCES],
            'chop_wood': [NeedType.RESOURCES],
            'mine': [NeedType.RESOURCES],
            'trade': [NeedType.RESOURCES],

            # OTHER ACTIONS
            'fight': [NeedType.SECURITY, NeedType.STATUS],
            'create_art': [NeedType.CREATIVITY, NeedType.MEANING],
            'experiment': [NeedType.ACHIEVEMENT, NeedType.CREATIVITY],
            'explore': [NeedType.GROWTH, NeedType.SECURITY],
            'teach': [NeedType.ACHIEVEMENT, NeedType.MEANING],
            'celebrate': [NeedType.BELONGING, NeedType.MEANING],
            'play_game': [NeedType.BELONGING],
        }

        relevant_needs = action_need_map.get(action_type, [])

        if not relevant_needs:
            return 0.5  # Neutral if no specific need

        # Average urgency of relevant needs
        urgencies = [need_state.needs[need].get_urgency()
                    for need in relevant_needs
                    if need in need_state.needs]

        return sum(urgencies) / len(urgencies) if urgencies else 0.5

    @staticmethod
    def _personality_factor(personality: PersonalityProfile, action_type: str) -> float:
        """Calculate personality influence on action"""
        # Map actions to personality traits
        personality_map = {
            # SURVIVAL ACTIONS - Less personality influence (survival is universal)
            'eat': 1.0,  # Everyone needs to eat!
            'drink': 1.0,  # Everyone needs to drink!
            'rest': 1.0,  # Everyone needs sleep!
            'gather_food': personality.conscientiousness,
            'gather_water': personality.conscientiousness,
            'hunt': personality.aggression * personality.risk_taking,

            # SOCIAL ACTIONS
            'seek_romance': personality.sexuality * personality.extraversion,
            'socialize': personality.extraversion,

            # PRODUCTIVITY ACTIONS
            'build': personality.conscientiousness * personality.creativity,
            'gather_materials': personality.conscientiousness,
            'chop_wood': personality.conscientiousness,
            'mine': personality.conscientiousness,
            'trade': personality.openness * (1.0 - personality.neuroticism),

            # OTHER ACTIONS
            'fight': personality.aggression * (1.0 - personality.agreeableness),
            'create_art': personality.creativity * personality.openness,
            'experiment': personality.openness * personality.creativity,
            'explore': personality.openness * personality.risk_taking,
            'teach': personality.empathy * personality.conscientiousness,
            'celebrate': personality.extraversion,
            'play_game': personality.extraversion * (1.0 - personality.neuroticism),
        }

        factor = personality_map.get(action_type, 0.5)

        # Normalize around 1.0 (0.5-1.5 range)
        return 0.5 + factor

    @staticmethod
    def _emotional_factor(emotional_state: EmotionalState, action_type: str) -> float:
        """Calculate emotional influence on action"""
        # Emotions can amplify or suppress actions
        if action_type == 'seek_romance':
            # Boosted by love/lust, suppressed by fear/shame
            boost = (emotional_state.emotions[EmotionType.LOVE].intensity +
                    emotional_state.emotions[EmotionType.LUST].intensity)
            suppress = (emotional_state.emotions[EmotionType.FEAR].intensity +
                       emotional_state.emotions[EmotionType.SHAME].intensity)
            return 0.5 + (boost - suppress) * 0.5

        elif action_type == 'fight':
            # Boosted by anger, suppressed by fear
            boost = emotional_state.emotions[EmotionType.ANGER].intensity
            suppress = emotional_state.emotions[EmotionType.FEAR].intensity
            return 0.5 + (boost - suppress) * 0.5

        elif action_type == 'socialize':
            # Boosted by joy/love, suppressed by sadness/shame
            boost = (emotional_state.emotions[EmotionType.JOY].intensity +
                    emotional_state.emotions[EmotionType.LOVE].intensity)
            suppress = (emotional_state.emotions[EmotionType.SADNESS].intensity +
                       emotional_state.emotions[EmotionType.SHAME].intensity)
            return 0.5 + (boost - suppress) * 0.5

        # High stress reduces motivation for non-urgent actions
        stress_penalty = emotional_state.stress * 0.3

        return max(0.5, 1.0 - stress_penalty)

    @staticmethod
    def relationship_attraction(
        agent_a_personality: PersonalityProfile,
        agent_b_personality: PersonalityProfile,
        agent_a_needs: NeedState,
        agent_b_needs: NeedState
    ) -> Tuple[float, str]:
        """
        Calculate attraction between two agents

        Returns: (attraction_level, relationship_type)
        attraction_level: 0-1
        relationship_type: 'friendship', 'romance', 'rivalry', 'neutral'
        """

        # Base compatibility
        compatibility = agent_a_personality.compatibility_with(agent_b_personality)

        # Sexual attraction (for romance)
        sexual_attraction = (
            agent_a_personality.sexuality *
            agent_b_personality.sexuality *
            agent_a_needs.needs[NeedType.SEX].get_urgency()
        )

        # Social attraction (for friendship)
        social_attraction = (
            agent_a_personality.extraversion *
            agent_a_needs.needs[NeedType.FRIENDSHIP].get_urgency() *
            compatibility
        )

        # Rivalry (competition-based)
        rivalry = (
            agent_a_personality.aggression *
            (1.0 - agent_a_personality.agreeableness) *
            agent_a_personality.ambition
        )

        # Determine relationship type
        if sexual_attraction > 0.6 and compatibility > 0.5:
            return sexual_attraction, 'romance'
        elif social_attraction > 0.5:
            return social_attraction, 'friendship'
        elif rivalry > 0.6 and compatibility < 0.4:
            return rivalry, 'rivalry'
        else:
            return compatibility * 0.5, 'neutral'
