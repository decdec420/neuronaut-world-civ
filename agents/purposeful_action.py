"""
Purposeful Action System - TRUE Purpose-Driven Decision Making

Every action an agent takes should have:
1. CLEAR PURPOSE - What need/goal drives this?
2. PERSONALITY FIT - Does this match who they are?
3. SKILL ALIGNMENT - Can they actually do this?
4. SUCCESS METRICS - How do we measure if it worked?
5. FEEDBACK LOOP - Did it make their life better?

This creates MEANINGFUL decisions instead of random actions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random

from engine.psychology import NeedType, NeedState, PersonalityProfile, EmotionalState


# ==============================================================================
# PURPOSE EVALUATION - Why is the agent doing this?
# ==============================================================================

@dataclass
class ActionPurpose:
    """
    The TRUE PURPOSE behind an action - the FULL story.

    This answers:
    - WHY are they doing this? (primary need)
    - What else do they hope to achieve? (secondary needs)
    - Does this match their personality?
    - Do they have the skills for this?
    - What are they risking?
    """

    # Primary driver
    primary_need: NeedType  # The MAIN need this addresses
    primary_need_urgency: float  # How urgent (0-1)

    # Secondary benefits
    secondary_needs: List[NeedType] = field(default_factory=list)

    # Personality alignment
    personality_fit: float = 0.5  # How well this matches their personality (0-1)
    personality_reasoning: str = ""  # WHY it fits (or doesn't)

    # Skill readiness
    skill_level: float = 0.0  # Their current skill (0-1)
    skill_confidence: float = 0.5  # How confident they feel (0-1)

    # Risk assessment
    risk_level: float = 0.0  # How risky is this? (0-1)
    risk_tolerance: float = 0.5  # How much risk they're willing to take

    # Social context
    social_motivation: Optional[str] = None  # If influenced by relationships
    emotional_driver: Optional[str] = None  # If driven by emotion

    # Expected outcome
    expected_need_satisfaction: Dict[NeedType, float] = field(default_factory=dict)
    expected_life_satisfaction_change: float = 0.0

    # Meta reasoning
    reasoning_summary: str = ""  # The FULL chain-of-thought


@dataclass
class ActionOutcome:
    """
    The ACTUAL RESULTS of an action - did it work?

    This measures success across multiple dimensions:
    - Need satisfaction
    - Life satisfaction
    - Skill growth
    - Relationship impact
    - Emotional impact
    """

    # Success/failure flag
    succeeded: bool = False

    # Need impact (what changed?)
    need_changes: Dict[NeedType, float] = field(default_factory=dict)  # -1 to 1

    # Overall wellbeing
    life_satisfaction_before: float = 0.0
    life_satisfaction_after: float = 0.0
    life_satisfaction_delta: float = 0.0

    # Skill growth
    skill_growth: float = 0.0  # How much they learned (0-1)
    skill_name: str = ""

    # Social impact
    relationship_changes: Dict[str, float] = field(default_factory=dict)  # agent_id -> change

    # Emotional impact
    emotions_triggered: Dict[str, float] = field(default_factory=dict)  # emotion -> intensity

    # Economic impact
    wealth_change: float = 0.0
    resources_gained: Dict[str, int] = field(default_factory=dict)
    resources_lost: Dict[str, int] = field(default_factory=dict)

    # Memory
    memorable: bool = False  # Should this be remembered?
    emotional_impact: float = 0.0  # For memory storage

    # Outcome narrative
    what_happened: str = ""  # Description of what actually happened
    why_it_worked: str = ""  # If success, why?
    why_it_failed: str = ""  # If failure, why?
    lesson_learned: str = ""  # What did they learn?


# ==============================================================================
# PURPOSEFUL ACTION EVALUATOR
# ==============================================================================

class PurposefulActionEvaluator:
    """
    Evaluates whether an action is purposeful and measures its success.

    This is the engine that creates TRUE MEANING in agent decisions.
    """

    def __init__(self):
        # Action -> Need mappings
        # What needs does each action satisfy?
        self.action_need_map = {
            # Survival actions
            'gather_food': [NeedType.HUNGER],
            'gather_water': [NeedType.THIRST],
            'rest': [NeedType.SLEEP],
            'sleep': [NeedType.SLEEP],

            # Safety actions
            'build': [NeedType.SHELTER, NeedType.SECURITY],
            'gather_materials': [NeedType.RESOURCES, NeedType.SECURITY],

            # Social actions
            'socialize': [NeedType.BELONGING, NeedType.FRIENDSHIP],
            'trade': [NeedType.RESOURCES, NeedType.BELONGING],
            'teach': [NeedType.ACHIEVEMENT, NeedType.RECOGNITION, NeedType.MEANING],

            # Creative actions
            'experiment': [NeedType.CREATIVITY, NeedType.ACHIEVEMENT, NeedType.MEANING],
            'create_art': [NeedType.CREATIVITY, NeedType.RECOGNITION],

            # Growth actions
            'learn': [NeedType.GROWTH, NeedType.ACHIEVEMENT],
            'explore': [NeedType.GROWTH, NeedType.CREATIVITY],
        }

        # Action -> Personality fit
        # Which personality traits make you more likely to do this?
        self.action_personality_map = {
            'experiment': {
                'openness': 1.0,  # High openness = loves experimenting
                'creativity': 0.8,
                'risk_taking': 0.6,
                'conscientiousness': 0.3,  # Low conscientiousness might experiment more recklessly
            },
            'build': {
                'conscientiousness': 1.0,  # High conscientiousness = loves building
                'ambition': 0.6,
                'creativity': 0.4,
            },
            'socialize': {
                'extraversion': 1.0,  # High extraversion = loves socializing
                'agreeableness': 0.6,
                'empathy': 0.5,
            },
            'trade': {
                'extraversion': 0.7,
                'ambition': 0.6,
                'rationality': 0.5,
            },
            'teach': {
                'empathy': 1.0,
                'extraversion': 0.7,
                'conscientiousness': 0.6,
                'agreeableness': 0.5,
            },
            'gather_food': {
                'conscientiousness': 0.5,
            },
            'rest': {
                'neuroticism': 0.6,  # High neuroticism = more likely to rest when stressed
            },
        }

        # Action risk levels
        self.action_risk = {
            'experiment': 0.6,  # Moderate-high risk
            'explore': 0.5,
            'fight': 0.9,
            'build': 0.2,
            'gather_food': 0.1,
            'socialize': 0.1,
            'trade': 0.3,
            'teach': 0.1,
        }

    def evaluate_purpose(
        self,
        action: str,
        agent_needs: NeedState,
        agent_personality: PersonalityProfile,
        agent_skills: Dict[str, float],
        context: Dict = None
    ) -> ActionPurpose:
        """
        Determine the TRUE PURPOSE behind choosing this action.

        This creates the "chain-of-thought" for WHY they're doing this.
        """
        context = context or {}

        # 1. What needs does this action address?
        needs_addressed = self.action_need_map.get(action, [])

        if not needs_addressed:
            # Unknown action, assume it's generic
            primary_need = NeedType.MEANING
            primary_urgency = 0.5
            secondary_needs = []
        else:
            # Find the most urgent need this action addresses
            urgencies = {}
            for need_type in needs_addressed:
                if need_type in agent_needs.needs:
                    urgencies[need_type] = agent_needs.needs[need_type].get_urgency()

            if urgencies:
                primary_need = max(urgencies.items(), key=lambda x: x[1])[0]
                primary_urgency = urgencies[primary_need]
                secondary_needs = [n for n in urgencies.keys() if n != primary_need]
            else:
                primary_need = needs_addressed[0]
                primary_urgency = 0.5
                secondary_needs = needs_addressed[1:]

        # 2. How well does this match their personality?
        personality_fit, personality_reasoning = self._evaluate_personality_fit(
            action, agent_personality
        )

        # 3. Do they have the skills?
        skill_name = f"{action}_skill"
        skill_level = agent_skills.get(skill_name, 0.0)

        # Confidence = skill level adjusted by personality
        confidence_modifier = (
            agent_personality.risk_taking * 0.3 +
            agent_personality.conscientiousness * -0.2 +  # Conscientious people are more cautious
            agent_personality.neuroticism * -0.3  # Neurotic people less confident
        )
        skill_confidence = min(1.0, max(0.0, skill_level + confidence_modifier))

        # 4. Risk assessment
        risk_level = self.action_risk.get(action, 0.3)
        risk_tolerance = agent_personality.risk_taking

        # 5. Social/emotional context
        social_motivation = context.get('social_motivation')
        emotional_driver = context.get('emotional_driver')

        # 6. Expected outcomes
        expected_satisfaction = {}
        for need_type in needs_addressed:
            # Estimate how much this will satisfy the need
            # Better skills = better satisfaction
            satisfaction_amount = 0.3 + (skill_level * 0.4)
            expected_satisfaction[need_type] = satisfaction_amount

        # Estimate life satisfaction change
        current_satisfaction = agent_needs.get_overall_satisfaction()
        # If addressing urgent needs, expect improvement
        expected_improvement = primary_urgency * 0.2 * personality_fit

        # 7. Generate reasoning summary
        reasoning = self._generate_reasoning_summary(
            action=action,
            primary_need=primary_need,
            primary_urgency=primary_urgency,
            personality_fit=personality_fit,
            personality_reasoning=personality_reasoning,
            skill_level=skill_level,
            skill_confidence=skill_confidence,
            risk_level=risk_level,
            risk_tolerance=risk_tolerance,
            social_motivation=social_motivation,
            emotional_driver=emotional_driver
        )

        return ActionPurpose(
            primary_need=primary_need,
            primary_need_urgency=primary_urgency,
            secondary_needs=secondary_needs,
            personality_fit=personality_fit,
            personality_reasoning=personality_reasoning,
            skill_level=skill_level,
            skill_confidence=skill_confidence,
            risk_level=risk_level,
            risk_tolerance=risk_tolerance,
            social_motivation=social_motivation,
            emotional_driver=emotional_driver,
            expected_need_satisfaction=expected_satisfaction,
            expected_life_satisfaction_change=expected_improvement,
            reasoning_summary=reasoning
        )

    def _evaluate_personality_fit(
        self,
        action: str,
        personality: PersonalityProfile
    ) -> Tuple[float, str]:
        """
        How well does this action match their personality?

        Returns: (fit_score, reasoning)
        """
        trait_weights = self.action_personality_map.get(action, {})

        if not trait_weights:
            return (0.5, "This action doesn't strongly relate to personality traits.")

        # Calculate weighted fit
        fit_score = 0.0
        total_weight = 0.0
        reasons = []

        for trait_name, weight in trait_weights.items():
            trait_value = getattr(personality, trait_name, 0.5)

            # Contribution = how close trait value is to ideal (weight tells us ideal)
            if weight > 0.5:
                # High trait value is good
                contribution = trait_value * weight
                if trait_value > 0.7:
                    reasons.append(f"High {trait_name} makes this appealing")
                elif trait_value < 0.3:
                    reasons.append(f"Low {trait_name} makes this unappealing")
            else:
                # Low trait value is good
                contribution = (1.0 - trait_value) * weight
                if trait_value < 0.3:
                    reasons.append(f"Low {trait_name} makes this appealing")

            fit_score += contribution
            total_weight += weight

        if total_weight > 0:
            fit_score = fit_score / total_weight
        else:
            fit_score = 0.5

        reasoning = "; ".join(reasons) if reasons else "Neutral personality fit"

        return (fit_score, reasoning)

    def _generate_reasoning_summary(
        self,
        action: str,
        primary_need: NeedType,
        primary_urgency: float,
        personality_fit: float,
        personality_reasoning: str,
        skill_level: float,
        skill_confidence: float,
        risk_level: float,
        risk_tolerance: float,
        social_motivation: Optional[str],
        emotional_driver: Optional[str]
    ) -> str:
        """
        Generate a human-readable summary of WHY they're doing this.
        """
        # Urgency description
        if primary_urgency > 0.8:
            urgency_desc = "desperately"
        elif primary_urgency > 0.6:
            urgency_desc = "urgently"
        elif primary_urgency > 0.4:
            urgency_desc = "moderately"
        else:
            urgency_desc = "mildly"

        # Primary motivation
        need_names = {
            NeedType.HUNGER: "hunger",
            NeedType.THIRST: "thirst",
            NeedType.SLEEP: "exhaustion",
            NeedType.SECURITY: "feeling unsafe",
            NeedType.RESOURCES: "need for resources",
            NeedType.SHELTER: "need for shelter",
            NeedType.BELONGING: "feeling lonely",
            NeedType.FRIENDSHIP: "desire for connection",
            NeedType.ACHIEVEMENT: "drive to accomplish something",
            NeedType.MEANING: "search for purpose",
            NeedType.CREATIVITY: "creative impulse",
            NeedType.GROWTH: "desire to grow and learn",
            NeedType.STATUS: "desire for recognition",
            NeedType.RECOGNITION: "need to be acknowledged",
        }

        primary_driver = need_names.get(primary_need, str(primary_need.value))

        reasoning_parts = [
            f"I'm {urgency_desc} driven by {primary_driver}."
        ]

        # Personality fit
        if personality_fit > 0.7:
            reasoning_parts.append(f"{personality_reasoning}, so this feels natural to me.")
        elif personality_fit < 0.3:
            reasoning_parts.append(f"{personality_reasoning}, but I'll do it anyway out of necessity.")

        # Skill consideration
        if skill_level > 0.7:
            reasoning_parts.append(f"I'm skilled at this, so I'm confident it will work.")
        elif skill_level < 0.3:
            reasoning_parts.append(f"I'm inexperienced, but I need to try.")

        # Risk consideration
        if risk_level > 0.6 and risk_tolerance < 0.4:
            reasoning_parts.append(f"This is risky and I'm usually cautious, but the need is urgent.")
        elif risk_level > 0.6 and risk_tolerance > 0.6:
            reasoning_parts.append(f"This is risky, but I enjoy taking chances.")

        # Social/emotional
        if social_motivation:
            reasoning_parts.append(social_motivation)
        if emotional_driver:
            reasoning_parts.append(emotional_driver)

        return " ".join(reasoning_parts)

    def measure_outcome(
        self,
        purpose: ActionPurpose,
        action_succeeded: bool,
        agent_needs_before: NeedState,
        agent_needs_after: NeedState,
        context: Dict = None
    ) -> ActionOutcome:
        """
        Measure the ACTUAL outcome of the action.

        Did it achieve what they hoped? How did it change their life?
        """
        context = context or {}

        # Calculate need changes
        need_changes = {}
        for need_type in NeedType:
            if need_type in agent_needs_before.needs and need_type in agent_needs_after.needs:
                before = agent_needs_before.needs[need_type].level
                after = agent_needs_after.needs[need_type].level
                change = before - after  # Positive = need was satisfied
                if abs(change) > 0.01:  # Only record significant changes
                    need_changes[need_type] = change

        # Life satisfaction change
        life_sat_before = agent_needs_before.get_overall_satisfaction()
        life_sat_after = agent_needs_after.get_overall_satisfaction()
        life_sat_delta = life_sat_after - life_sat_before

        # Did they achieve their goal?
        primary_need_satisfied = need_changes.get(purpose.primary_need, 0.0) > 0

        # Overall success
        succeeded = action_succeeded and (primary_need_satisfied or life_sat_delta > 0)

        # Skill growth (you learn from both success and failure)
        skill_growth = 0.01  # Base learning
        if action_succeeded:
            skill_growth += 0.02  # Learn more from success
        else:
            skill_growth += 0.015  # Learn from failure too

        # Emotional impact
        emotions_triggered = {}
        if succeeded:
            emotions_triggered['joy'] = min(1.0, 0.3 + life_sat_delta)
            if purpose.primary_need in [NeedType.ACHIEVEMENT, NeedType.RECOGNITION]:
                emotions_triggered['pride'] = 0.5
        else:
            emotions_triggered['sadness'] = 0.3
            if purpose.primary_need_urgency > 0.7:
                emotions_triggered['fear'] = 0.4  # Fear when failing at urgent needs

        # Generate outcome narrative
        what_happened = context.get('what_happened', 'Action completed.')

        if succeeded:
            why_worked = f"I successfully addressed my {purpose.primary_need.value}."
            if purpose.skill_level > 0.6:
                why_worked += " My experience helped."
            why_failed = ""
            lesson = f"This was a good choice for satisfying my {purpose.primary_need.value}."
        else:
            why_worked = ""
            why_failed = f"I failed to address my {purpose.primary_need.value}."
            if purpose.skill_level < 0.3:
                why_failed += " I lacked the necessary skills."
            elif purpose.risk_level > purpose.risk_tolerance:
                why_failed += " The risk was too great."
            lesson = f"I need to approach {purpose.primary_need.value} differently next time."

        return ActionOutcome(
            succeeded=succeeded,
            need_changes=need_changes,
            life_satisfaction_before=life_sat_before,
            life_satisfaction_after=life_sat_after,
            life_satisfaction_delta=life_sat_delta,
            skill_growth=skill_growth,
            skill_name=f"{context.get('action', 'unknown')}_skill",
            relationship_changes=context.get('relationship_changes', {}),
            emotions_triggered=emotions_triggered,
            wealth_change=context.get('wealth_change', 0.0),
            resources_gained=context.get('resources_gained', {}),
            resources_lost=context.get('resources_lost', {}),
            memorable=(abs(life_sat_delta) > 0.1 or abs(emotions_triggered.get('joy', 0)) > 0.5),
            emotional_impact=life_sat_delta,
            what_happened=what_happened,
            why_it_worked=why_worked,
            why_it_failed=why_failed,
            lesson_learned=lesson
        )
