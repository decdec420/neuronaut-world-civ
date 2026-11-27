"""
Life System - Full Autonomous Life Simulation

Agents live complete lives:
- Birth, childhood, adulthood, old age, death
- Romance, marriage, reproduction
- Career goals and life philosophies
- Generational wealth and inheritance
- Population growth from 50 → billions → trillions

NO LIMITS. Agents decide how far civilization goes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum
import random
from engine.ids import new_uuid


class LifeStage(Enum):
    """Stages of life"""
    CHILD = "child"  # 0-13
    ADOLESCENT = "adolescent"  # 14-17
    YOUNG_ADULT = "young_adult"  # 18-30
    ADULT = "adult"  # 31-50
    MIDDLE_AGE = "middle_age"  # 51-65
    ELDER = "elder"  # 66-80
    ANCIENT = "ancient"  # 81+


# The ideal number of children, as U.S. adults answered it in 2023 (Gallup,
# June-July 2023, n=2,028: 0: 2%, 1: 3%, 2: 44%, 3: 29%, 4: 12%, 5: 2%,
# 6 or more: 2%; mean 2.7; the 6% without an answer left out). Each person
# draws their own; nobody is made to have any.
IDEAL_FAMILY_SIZE = ((0, 2), (1, 3), (2, 44), (3, 29), (4, 12), (5, 2), (6, 2))


class LifePhilosophy(Enum):
    """How agent approaches life"""
    WEALTH_BUILDER = "wealth_builder"  # Accumulate resources, build dynasty
    LEGACY_SEEKER = "legacy_seeker"  # Create lasting impact, teach, build monuments
    ADVENTURE_SEEKER = "adventure_seeker"  # Explore, experiment, risk-taking
    STABILITY_SEEKER = "stability_seeker"  # Security, family, predictability
    PLEASURE_SEEKER = "pleasure_seeker"  # Live in moment, parties, experiences
    POWER_SEEKER = "power_seeker"  # Status, influence, leadership
    KNOWLEDGE_SEEKER = "knowledge_seeker"  # Learn everything, discover, research
    COMMUNITY_BUILDER = "community_builder"  # Relationships, helping others


@dataclass
class LifeGoal:
    """A life goal an agent pursues"""
    id: str
    goal_type: str  # "career", "family", "wealth", "legacy", "adventure"
    description: str
    target_value: float  # What they're aiming for
    current_progress: float = 0.0
    priority: float = 0.5  # 0-1, how important
    deadline_age: Optional[int] = None  # Age they want to achieve by

    def is_achieved(self) -> bool:
        return self.current_progress >= self.target_value


@dataclass
class FamilyBond:
    """Relationship between family members"""
    agent_id: str
    relation_type: str  # "parent", "child", "sibling", "spouse", "grandparent", "grandchild"
    bond_strength: float = 0.8  # How close they are
    inheritance_share: float = 0.0  # % of wealth they'll inherit


@dataclass
class LifeProfile:
    """Complete life profile for an agent"""
    agent_id: str

    # Life stage
    life_stage: LifeStage = LifeStage.YOUNG_ADULT
    philosophy: LifePhilosophy = LifePhilosophy.STABILITY_SEEKER

    # Family
    parents: List[str] = field(default_factory=list)  # Parent agent IDs
    children: List[str] = field(default_factory=list)  # Child agent IDs
    spouse: Optional[str] = None
    family_bonds: Dict[str, FamilyBond] = field(default_factory=dict)

    # Life goals
    current_goals: List[LifeGoal] = field(default_factory=list)
    achieved_goals: List[LifeGoal] = field(default_factory=list)

    # Career/legacy
    career_path: Optional[str] = None  # Based on discovered role
    mastered_skills: List[str] = field(default_factory=list)
    legacy_projects: List[str] = field(default_factory=list)  # Buildings, discoveries, teachings

    # Wealth & property
    inherited_wealth: float = 0.0
    self_made_wealth: float = 0.0
    property_ids: List[str] = field(default_factory=list)

    # Life choices
    risk_tolerance: float = 0.5  # 0-1, how much risk they take
    family_priority: float = 0.5  # 0-1, how much they value family
    wealth_priority: float = 0.5  # 0-1, how much they value wealth
    experience_priority: float = 0.5  # 0-1, how much they value experiences

    # Reproductive
    wants_children: bool = True
    ideal_children_count: int = 2
    children_born: int = 0
    fertility: float = 1.0  # Decreases with age

    # Life history
    major_life_events: List[Dict] = field(default_factory=list)
    birth_date: datetime = field(default_factory=datetime.now)
    death_date: Optional[datetime] = None
    cause_of_death: Optional[str] = None


class LifeSystem:
    """
    Manages full life simulation for all agents.

    Handles:
    - Birth and reproduction
    - Life stage transitions
    - Goal setting and pursuit
    - Family dynamics
    - Inheritance
    - Death and legacy

    Scales from 50 agents to billions!
    """

    def __init__(self):
        self.life_profiles: Dict[str, LifeProfile] = {}

        # Population tracking
        self.total_births: int = 0
        self.total_deaths: int = 0
        self.current_population: int = 0

        # Generational tracking
        self.generation_count: int = 1  # Starting generation
        self.family_trees: Dict[str, Set[str]] = {}  # Family lineages

        # Statistics
        self.average_lifespan: float = 0.0
        self.birth_rate: float = 0.0  # Births per tick
        self.death_rate: float = 0.0  # Deaths per tick

    def create_life_profile(
        self,
        agent_id: str,
        agent_personality: Dict,
        parents: Optional[List[str]] = None,
        inherited_wealth: float = 0.0
    ) -> LifeProfile:
        """
        Create life profile for new agent (birth or initial population).

        Philosophy and goals emerge from personality!
        """

        # Determine life philosophy from personality
        philosophy = self._determine_philosophy(agent_personality)

        # Create profile
        profile = LifeProfile(
            agent_id=agent_id,
            philosophy=philosophy,
            parents=parents or [],
            inherited_wealth=inherited_wealth
        )

        # Set priorities based on personality
        profile.risk_tolerance = agent_personality.get('openness', 0.5)
        profile.family_priority = agent_personality.get('agreeableness', 0.5)
        profile.wealth_priority = agent_personality.get('conscientiousness', 0.5)
        profile.experience_priority = agent_personality.get('openness', 0.5)

        # How many children they'd like, as real people answer it (IDEAL_FAMILY_SIZE).
        # It used to be 0-2, 1-3 or 2-4 by life philosophy, and anyone with
        # agreeableness under 0.4 wanted none: a couple stopped at the smaller of
        # two such numbers, about one child, and most villages shrank.
        sizes, weights = zip(*IDEAL_FAMILY_SIZE)
        profile.ideal_children_count = random.choices(sizes, weights=weights)[0]
        profile.wants_children = profile.ideal_children_count > 0

        # Generate initial life goals
        profile.current_goals = self._generate_initial_goals(
            agent_id, philosophy, agent_personality
        )

        self.life_profiles[agent_id] = profile
        self.current_population += 1

        return profile

    def _determine_philosophy(self, personality: Dict) -> LifePhilosophy:
        """Determine life philosophy from personality traits"""

        openness = personality.get('openness', 0.5)
        conscientiousness = personality.get('conscientiousness', 0.5)
        extraversion = personality.get('extraversion', 0.5)
        agreeableness = personality.get('agreeableness', 0.5)

        # High conscientiousness → wealth/stability
        if conscientiousness > 0.7:
            if agreeableness > 0.6:
                return LifePhilosophy.COMMUNITY_BUILDER
            else:
                return LifePhilosophy.WEALTH_BUILDER

        # High openness → adventure/knowledge
        elif openness > 0.7:
            if conscientiousness < 0.4:
                return LifePhilosophy.ADVENTURE_SEEKER
            else:
                return LifePhilosophy.KNOWLEDGE_SEEKER

        # High extraversion → power/pleasure
        elif extraversion > 0.7:
            if conscientiousness < 0.4:
                return LifePhilosophy.PLEASURE_SEEKER
            else:
                return LifePhilosophy.POWER_SEEKER

        # Balanced → legacy or stability
        elif agreeableness > 0.6:
            return LifePhilosophy.LEGACY_SEEKER
        else:
            return LifePhilosophy.STABILITY_SEEKER

    def _generate_initial_goals(
        self,
        agent_id: str,
        philosophy: LifePhilosophy,
        personality: Dict
    ) -> List[LifeGoal]:
        """Generate starting life goals based on philosophy"""

        goals = []

        if philosophy == LifePhilosophy.WEALTH_BUILDER:
            goals.append(LifeGoal(
                id=str(new_uuid()),
                goal_type="wealth",
                description="Accumulate 1000 wealth",
                target_value=1000,
                priority=0.9,
                deadline_age=50
            ))
            goals.append(LifeGoal(
                id=str(new_uuid()),
                goal_type="family",
                description="Raise successful children",
                target_value=2,
                priority=0.7,
                deadline_age=40
            ))

        elif philosophy == LifePhilosophy.ADVENTURE_SEEKER:
            goals.append(LifeGoal(
                id=str(new_uuid()),
                goal_type="adventure",
                description="Make 50 discoveries",
                target_value=50,
                priority=0.9
            ))
            goals.append(LifeGoal(
                id=str(new_uuid()),
                goal_type="experience",
                description="Master experimentation",
                target_value=1.0,
                priority=0.8
            ))

        elif philosophy == LifePhilosophy.LEGACY_SEEKER:
            goals.append(LifeGoal(
                id=str(new_uuid()),
                goal_type="legacy",
                description="Build 10 lasting structures",
                target_value=10,
                priority=0.9,
                deadline_age=60
            ))
            goals.append(LifeGoal(
                id=str(new_uuid()),
                goal_type="legacy",
                description="Teach 100 lessons",
                target_value=100,
                priority=0.8
            ))

        elif philosophy == LifePhilosophy.PLEASURE_SEEKER:
            goals.append(LifeGoal(
                id=str(new_uuid()),
                goal_type="experience",
                description="Live every moment fully",
                target_value=1000,  # Life satisfaction points
                priority=1.0
            ))

        # Add career goal (emerges from discovered role later)
        goals.append(LifeGoal(
            id=str(new_uuid()),
            goal_type="career",
            description="Master my craft",
            target_value=1.0,  # Skill level
            priority=0.6
        ))

        return goals

    def _calculate_fertility(self, age: int) -> float:
        """Calculate fertility based on age (life/family.py)"""
        from life.family import fertility
        return fertility(age)

    def update_life_stage(self, agent_id: str, current_age: int):
        """Update agent's life stage"""
        profile = self.life_profiles.get(agent_id)
        if not profile:
            return

        old_stage = profile.life_stage

        if current_age < 14:
            profile.life_stage = LifeStage.CHILD
        elif current_age < 18:
            profile.life_stage = LifeStage.ADOLESCENT
        elif current_age < 31:
            profile.life_stage = LifeStage.YOUNG_ADULT
        elif current_age < 51:
            profile.life_stage = LifeStage.ADULT
        elif current_age < 66:
            profile.life_stage = LifeStage.MIDDLE_AGE
        elif current_age < 81:
            profile.life_stage = LifeStage.ELDER
        else:
            profile.life_stage = LifeStage.ANCIENT

        # Life stage transition events
        if old_stage != profile.life_stage:
            profile.major_life_events.append({
                'type': 'life_stage_transition',
                'age': current_age,
                'from_stage': old_stage.value,
                'to_stage': profile.life_stage.value,
                'timestamp': datetime.now()
            })

    def process_death(
        self,
        agent_id: str,
        age: int,
        cause: str,
        wealth: float
    ) -> Dict:
        """
        Process agent death and inheritance.

        Returns inheritance distribution.
        """
        profile = self.life_profiles.get(agent_id)
        if not profile:
            return {}

        profile.death_date = datetime.now()
        profile.cause_of_death = cause

        # Calculate inheritance
        inheritance_pool = wealth + profile.self_made_wealth
        inheritance_distribution = {}

        # Distribute to children
        if profile.children:
            per_child = inheritance_pool / len(profile.children)
            for child_id in profile.children:
                inheritance_distribution[child_id] = per_child
        # Otherwise to spouse
        elif profile.spouse:
            inheritance_distribution[profile.spouse] = inheritance_pool

        # Update statistics
        self.total_deaths += 1
        self.current_population -= 1

        # Update average lifespan
        if self.total_deaths > 0:
            self.average_lifespan = (
                (self.average_lifespan * (self.total_deaths - 1) + age) /
                self.total_deaths
            )

        return inheritance_distribution

    def update_goal_progress(
        self,
        agent_id: str,
        goal_type: str,
        progress_delta: float
    ):
        """Update progress on agent's goals"""
        profile = self.life_profiles.get(agent_id)
        if not profile:
            return

        for goal in profile.current_goals:
            if goal.goal_type == goal_type:
                goal.current_progress += progress_delta

                # Check if achieved
                if goal.is_achieved() and goal not in profile.achieved_goals:
                    profile.achieved_goals.append(goal)
                    profile.current_goals.remove(goal)

                    # Record achievement
                    profile.major_life_events.append({
                        'type': 'goal_achieved',
                        'goal': goal.description,
                        'timestamp': datetime.now()
                    })

    def get_statistics(self) -> Dict:
        """Get life system statistics"""

        # Calculate by philosophy
        philosophy_distribution = {}
        for profile in self.life_profiles.values():
            phil = profile.philosophy.value
            philosophy_distribution[phil] = philosophy_distribution.get(phil, 0) + 1

        # Wealth distribution
        wealth_gini = self._calculate_wealth_inequality()

        return {
            'total_population': self.current_population,
            'total_births': self.total_births,
            'total_deaths': self.total_deaths,
            'generation_count': self.generation_count,
            'average_lifespan': self.average_lifespan,
            'birth_rate': self.birth_rate,
            'death_rate': self.death_rate,
            'philosophy_distribution': philosophy_distribution,
            'wealth_inequality': wealth_gini,
            'total_families': len(self.family_trees)
        }

    def _calculate_wealth_inequality(self) -> float:
        """Calculate Gini coefficient for wealth inequality"""
        # Simplified Gini calculation
        wealth_values = [p.self_made_wealth + p.inherited_wealth
                        for p in self.life_profiles.values()]

        if not wealth_values:
            return 0.0

        # Sort wealth
        wealth_values.sort()
        n = len(wealth_values)

        if sum(wealth_values) == 0:
            return 0.0

        # Gini coefficient
        cumsum = 0
        for i, w in enumerate(wealth_values):
            cumsum += (2 * (i + 1) - n - 1) * w

        return cumsum / (n * sum(wealth_values))
