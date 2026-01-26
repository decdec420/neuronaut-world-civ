"""
Personality Evolution System - Agents Develop Through Experience

This system enables TRUE PERSONALITY DEVELOPMENT based on life experiences.
Personalities are no longer static - they evolve dynamically as agents:
- Learn from successes and failures
- Develop specializations through repeated activities
- Form social roles (leader, follower, mentor, rebel)
- Change traits based on major life events

Key Features:
- **Experience-Based Evolution**: Traits shift based on what agents do
- **Role Emergence**: Leaders, specialists, mentors emerge naturally
- **Life Event Impact**: Major moments shape personality permanently
- **Social Influence**: Swarm participation affects social traits
- **Specialist Development**: Hunters, builders, traders develop distinct personalities
- **Realistic Change**: Gradual shifts, not sudden transformations

This creates LIVING CHARACTERS with depth, growth, and authentic development.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from engine.psychology import PersonalityProfile

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Emergent social roles that develop through experience"""
    UNDEFINED = "undefined"  # No clear role yet

    # Leadership roles
    LEADER = "leader"  # High swarm participation, successful coordinations
    FOLLOWER = "follower"  # Participates but doesn't initiate
    REBEL = "rebel"  # Rejects group consensus frequently

    # Specialist roles
    HUNTER = "hunter"  # Frequent hunting actions
    GATHERER = "gatherer"  # Frequent gathering
    BUILDER = "builder"  # Frequent construction
    TRADER = "trader"  # Frequent trading
    WARRIOR = "warrior"  # Frequent combat
    EXPLORER = "explorer"  # Frequent movement to new areas
    HEALER = "healer"  # Frequent care for others
    SCIENTIST = "scientist"  # Frequent research/discovery
    ARTIST = "artist"  # Frequent creative activities

    # Social roles
    MENTOR = "mentor"  # Shares knowledge frequently
    MEDIATOR = "mediator"  # Resolves conflicts
    SOCIALITE = "socialite"  # High social interaction
    HERMIT = "hermit"  # Avoids social interaction


@dataclass
class ExperienceImpact:
    """Record of how an experience impacts personality"""
    experience_type: str  # Action or event type
    trait_changes: Dict[str, float]  # trait_name -> delta
    impact_strength: float = 1.0  # 0-1, how strongly this impacts personality
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PersonalityDevelopment:
    """Track an agent's personality development over time"""
    agent_id: str
    base_personality: PersonalityProfile  # Original personality at birth
    current_personality: PersonalityProfile  # Current evolved personality

    # Experience tracking
    action_counts: Dict[str, int] = field(default_factory=dict)  # action_type -> count
    swarm_participations: int = 0
    successful_coordinations: int = 0
    leadership_initiatives: int = 0

    # Role development
    current_role: AgentRole = AgentRole.UNDEFINED
    role_confidence: float = 0.0  # 0-1, how established this role is

    # Life-changing events
    major_events: List[str] = field(default_factory=list)

    # Personality change history
    trait_history: Dict[str, List[Tuple[int, float]]] = field(default_factory=dict)  # trait -> [(tick, value)]

    # Statistics
    total_experiences: int = 0
    last_evolution_tick: int = 0


class PersonalityEvolutionSystem:
    """
    Manages dynamic personality evolution for agents

    Personalities evolve based on:
    1. **Actions Taken**: Repeated actions strengthen related traits
    2. **Successes/Failures**: Outcomes affect confidence and risk-taking
    3. **Swarm Participation**: Social coordination affects social traits
    4. **Life Events**: Major moments cause significant shifts
    5. **Memory Recall**: Frequently recalled memories reinforce traits

    Example Evolution Paths:
    - Hunter who succeeds → More confident, less agreeable, higher risk-taking
    - Builder who fails → More cautious, higher conscientiousness
    - Leader of swarms → Higher extraversion, ambition, lower neuroticism
    - Hermit who avoids groups → Lower extraversion, higher independence
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Configuration
        self.evolution_rate = self.config.get('evolution_rate', 0.01)  # How fast traits change
        self.major_event_multiplier = self.config.get('major_event_multiplier', 5.0)
        self.role_threshold = self.config.get('role_threshold', 0.6)  # Confidence needed for role
        self.specialist_action_threshold = self.config.get('specialist_action_threshold', 50)

        # Track all agents
        self.agents: Dict[str, PersonalityDevelopment] = {}

        # Experience impact rules
        self._initialize_impact_rules()

        # Statistics
        self.total_evolutions = 0
        self.roles_emerged = 0

    # ============================================================================
    # CORE EVOLUTION METHODS
    # ============================================================================

    def initialize_agent(self, agent_id: str, base_personality: PersonalityProfile) -> PersonalityDevelopment:
        """Initialize personality tracking for a new agent"""
        import copy

        development = PersonalityDevelopment(
            agent_id=agent_id,
            base_personality=copy.deepcopy(base_personality),
            current_personality=copy.deepcopy(base_personality)
        )

        self.agents[agent_id] = development
        logger.info(f"[{agent_id}] Personality evolution tracking initialized")

        return development

    def record_experience(
        self,
        agent_id: str,
        experience_type: str,
        success: bool = True,
        intensity: float = 1.0,
        tick: int = 0
    ) -> Optional[PersonalityProfile]:
        """
        Record an experience and evolve personality accordingly

        Args:
            agent_id: Agent experiencing this
            experience_type: Type of action/event
            success: Whether it was successful
            intensity: How impactful (0-1)
            tick: Current simulation tick

        Returns:
            Updated personality if changed, None otherwise
        """
        if agent_id not in self.agents:
            logger.warning(f"[{agent_id}] Not initialized for personality evolution")
            return None

        dev = self.agents[agent_id]

        # Track action count
        dev.action_counts[experience_type] = dev.action_counts.get(experience_type, 0) + 1
        dev.total_experiences += 1

        # Get trait changes for this experience
        trait_changes = self._calculate_trait_changes(
            experience_type=experience_type,
            success=success,
            intensity=intensity,
            current_personality=dev.current_personality
        )

        if not trait_changes:
            return None

        # Apply trait changes
        personality_changed = self._apply_trait_changes(
            development=dev,
            trait_changes=trait_changes,
            tick=tick
        )

        # Check for role emergence
        self._update_role(development=dev)

        if personality_changed:
            self.total_evolutions += 1
            dev.last_evolution_tick = tick
            logger.debug(f"[{agent_id}] Personality evolved from {experience_type}")
            return dev.current_personality

        return None

    def record_swarm_participation(
        self,
        agent_id: str,
        was_leader: bool = False,
        consensus_reached: bool = True
    ):
        """Record that agent participated in swarm decision"""
        if agent_id not in self.agents:
            return

        dev = self.agents[agent_id]
        dev.swarm_participations += 1

        if was_leader:
            dev.leadership_initiatives += 1

        if consensus_reached:
            dev.successful_coordinations += 1

        # Swarm participation affects social traits
        if dev.swarm_participations % 10 == 0:  # Every 10 participations
            # Increase extraversion slightly
            dev.current_personality.extraversion = min(
                1.0,
                dev.current_personality.extraversion + 0.02
            )

            # Decrease neuroticism slightly (more confident in groups)
            dev.current_personality.neuroticism = max(
                0.0,
                dev.current_personality.neuroticism - 0.01
            )

            logger.debug(f"[{agent_id}] Social traits evolved from swarm participation")

    def record_major_event(
        self,
        agent_id: str,
        event_description: str,
        trait_impacts: Dict[str, float],
        tick: int = 0
    ):
        """
        Record a major life event that significantly impacts personality

        Examples:
        - First kill in combat
        - Losing a loved one
        - Becoming a parent
        - Major discovery
        - Near-death experience
        """
        if agent_id not in self.agents:
            return

        dev = self.agents[agent_id]
        dev.major_events.append(event_description)

        # Major events have amplified impact
        amplified_changes = {
            trait: delta * self.major_event_multiplier
            for trait, delta in trait_impacts.items()
        }

        self._apply_trait_changes(
            development=dev,
            trait_changes=amplified_changes,
            tick=tick
        )

        logger.info(f"[{agent_id}] Major life event: {event_description}")

    # ============================================================================
    # TRAIT CHANGE CALCULATION
    # ============================================================================

    def _initialize_impact_rules(self):
        """Define how different experiences impact traits"""
        self.impact_rules = {
            # Combat/Hunting
            'hunt': {
                'success': {'risk_taking': 0.01, 'aggression': 0.005, 'confidence': 0.01},
                'failure': {'risk_taking': -0.01, 'neuroticism': 0.01, 'caution': 0.01}
            },
            'attack': {
                'success': {'aggression': 0.02, 'confidence': 0.015, 'empathy': -0.01},
                'failure': {'aggression': -0.005, 'neuroticism': 0.02}
            },

            # Building/Construction
            'build': {
                'success': {'conscientiousness': 0.01, 'creativity': 0.005},
                'failure': {'conscientiousness': 0.015}  # Failure teaches discipline
            },

            # Social
            'socialize': {
                'success': {'extraversion': 0.01, 'agreeableness': 0.005},
                'failure': {'extraversion': -0.005, 'neuroticism': 0.01}
            },
            'trade': {
                'success': {'agreeableness': 0.005, 'rationality': 0.01},
                'failure': {'agreeableness': -0.005}
            },

            # Creative
            'create_art': {
                'success': {'creativity': 0.015, 'openness': 0.01},
                'failure': {'creativity': 0.005}  # Still stimulates creativity
            },

            # Exploration
            'explore': {
                'success': {'openness': 0.01, 'risk_taking': 0.005},
                'failure': {'openness': 0.005, 'risk_taking': -0.01}
            },

            # Learning/Discovery
            'research': {
                'success': {'rationality': 0.01, 'openness': 0.01, 'ambition': 0.005},
                'failure': {'conscientiousness': 0.01}  # Failure teaches thoroughness
            },
        }

    def _calculate_trait_changes(
        self,
        experience_type: str,
        success: bool,
        intensity: float,
        current_personality: PersonalityProfile
    ) -> Dict[str, float]:
        """Calculate how this experience should change traits"""

        # Get base impacts from rules
        if experience_type not in self.impact_rules:
            return {}

        outcome_key = 'success' if success else 'failure'
        base_impacts = self.impact_rules[experience_type].get(outcome_key, {})

        # Scale by intensity and evolution rate
        trait_changes = {}
        for trait, delta in base_impacts.items():
            scaled_delta = delta * intensity * self.evolution_rate

            # Handle special trait names (map to PersonalityProfile attributes)
            actual_trait = self._map_trait_name(trait)
            if actual_trait:
                trait_changes[actual_trait] = scaled_delta

        return trait_changes

    def _map_trait_name(self, trait_name: str) -> Optional[str]:
        """Map logical trait names to PersonalityProfile attributes"""
        mapping = {
            'confidence': 'ambition',  # Confidence increases ambition
            'caution': 'risk_taking',  # Caution is inverse of risk_taking (handle in apply)
        }

        if trait_name in mapping:
            return mapping[trait_name]

        # Check if it's a valid PersonalityProfile attribute
        if hasattr(PersonalityProfile, trait_name):
            return trait_name

        return None

    def _apply_trait_changes(
        self,
        development: PersonalityDevelopment,
        trait_changes: Dict[str, float],
        tick: int
    ) -> bool:
        """Apply calculated trait changes to personality"""
        personality = development.current_personality
        changed = False

        for trait, delta in trait_changes.items():
            if not hasattr(personality, trait):
                continue

            old_value = getattr(personality, trait)
            new_value = max(0.0, min(1.0, old_value + delta))  # Clamp to [0, 1]

            if abs(new_value - old_value) > 0.001:  # Only record significant changes
                setattr(personality, trait, new_value)

                # Record in history
                if trait not in development.trait_history:
                    development.trait_history[trait] = []
                development.trait_history[trait].append((tick, new_value))

                changed = True
                logger.debug(f"[{development.agent_id}] {trait}: {old_value:.3f} → {new_value:.3f}")

        return changed

    # ============================================================================
    # ROLE EMERGENCE
    # ============================================================================

    def _update_role(self, development: PersonalityDevelopment):
        """Determine if agent has developed a clear role"""

        # Check for specialist roles based on action counts
        action_counts = development.action_counts
        total_actions = sum(action_counts.values())

        if total_actions < 20:  # Not enough experience yet
            return

        # Find dominant activity
        if action_counts:
            dominant_action = max(action_counts.items(), key=lambda x: x[1])
            action_type, count = dominant_action

            # If one action is >50% of all actions, they're a specialist
            if count > total_actions * 0.5 and count >= self.specialist_action_threshold:
                new_role = self._determine_specialist_role(action_type)

                if new_role != development.current_role:
                    development.current_role = new_role
                    development.role_confidence = min(1.0, count / (total_actions * 0.75))
                    self.roles_emerged += 1
                    logger.info(f"[{development.agent_id}] Emerged as {new_role.value} (confidence: {development.role_confidence:.2f})")
                    return

        # Check for leadership role
        if development.swarm_participations >= 30:
            leadership_ratio = development.leadership_initiatives / development.swarm_participations

            if leadership_ratio > 0.4:  # Often initiates
                development.current_role = AgentRole.LEADER
                development.role_confidence = min(1.0, leadership_ratio)
                self.roles_emerged += 1
                logger.info(f"[{development.agent_id}] Emerged as LEADER")
                return
            elif leadership_ratio < 0.1:  # Rarely initiates
                development.current_role = AgentRole.FOLLOWER
                development.role_confidence = min(1.0, 1.0 - leadership_ratio)
                return

        # Check for social roles
        social_count = action_counts.get('socialize', 0) + action_counts.get('trade', 0)
        if social_count > total_actions * 0.4 and social_count >= 30:
            development.current_role = AgentRole.SOCIALITE
            development.role_confidence = min(1.0, social_count / total_actions)
            return

    def _determine_specialist_role(self, dominant_action: str) -> AgentRole:
        """Map action type to specialist role"""
        role_mapping = {
            'hunt': AgentRole.HUNTER,
            'gather': AgentRole.GATHERER,
            'gather_food': AgentRole.GATHERER,
            'build': AgentRole.BUILDER,
            'build_shelter': AgentRole.BUILDER,
            'trade': AgentRole.TRADER,
            'attack': AgentRole.WARRIOR,
            'defend': AgentRole.WARRIOR,
            'explore': AgentRole.EXPLORER,
            'move': AgentRole.EXPLORER,
            'heal': AgentRole.HEALER,
            'care': AgentRole.HEALER,
            'research': AgentRole.SCIENTIST,
            'invent': AgentRole.SCIENTIST,
            'create_art': AgentRole.ARTIST,
            'craft': AgentRole.ARTIST,
        }

        return role_mapping.get(dominant_action, AgentRole.UNDEFINED)

    # ============================================================================
    # QUERY & STATISTICS
    # ============================================================================

    def get_personality_changes(self, agent_id: str) -> Dict[str, float]:
        """Get how much each trait has changed from base personality"""
        if agent_id not in self.agents:
            return {}

        dev = self.agents[agent_id]
        base = dev.base_personality
        current = dev.current_personality

        changes = {}
        for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness',
                      'neuroticism', 'risk_taking', 'aggression', 'sexuality', 'ambition',
                      'creativity', 'empathy', 'rationality']:
            base_value = getattr(base, trait)
            current_value = getattr(current, trait)
            changes[trait] = current_value - base_value

        return changes

    def get_agent_development(self, agent_id: str) -> Optional[PersonalityDevelopment]:
        """Get full development record for an agent"""
        return self.agents.get(agent_id)

    def get_role_distribution(self) -> Dict[AgentRole, int]:
        """Get count of agents in each role"""
        distribution = {}
        for dev in self.agents.values():
            role = dev.current_role
            distribution[role] = distribution.get(role, 0) + 1
        return distribution

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        role_dist = self.get_role_distribution()

        return {
            'total_agents': len(self.agents),
            'total_evolutions': self.total_evolutions,
            'roles_emerged': self.roles_emerged,
            'role_distribution': {role.value: count for role, count in role_dist.items()},
            'avg_experiences_per_agent': sum(d.total_experiences for d in self.agents.values()) / len(self.agents) if self.agents else 0,
        }

    def export_agent_story(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Export agent's personality development as a story"""
        if agent_id not in self.agents:
            return None

        dev = self.agents[agent_id]
        changes = self.get_personality_changes(agent_id)

        # Find most changed traits
        significant_changes = {
            trait: delta for trait, delta in changes.items()
            if abs(delta) > 0.1  # Significant change
        }

        return {
            'agent_id': agent_id,
            'base_personality': asdict(dev.base_personality),
            'current_personality': asdict(dev.current_personality),
            'trait_changes': changes,
            'significant_changes': significant_changes,
            'current_role': dev.current_role.value,
            'role_confidence': dev.role_confidence,
            'total_experiences': dev.total_experiences,
            'swarm_participations': dev.swarm_participations,
            'major_events': dev.major_events,
            'dominant_activities': sorted(
                dev.action_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
