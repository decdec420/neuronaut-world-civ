"""
Strategic Decision-Making System

Agents make long-term plans and strategic decisions:
- Set goals based on their psychology
- Plan multi-step strategies
- Adapt to changing circumstances
- Learn from success/failure
- Form alliances and coalitions

Agents have TRUE autonomy - they decide their own destiny!
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from datetime import datetime, timedelta
import random


class GoalType(Enum):
    """Types of goals agents can pursue"""
    # Survival
    SURVIVE = "survive"
    FIND_SHELTER = "find_shelter"
    SECURE_FOOD = "secure_food"

    # Economic
    GET_RICH = "get_rich"
    BUILD_BUSINESS = "build_business"
    ACCUMULATE_RESOURCES = "accumulate_resources"

    # Social
    MAKE_FRIENDS = "make_friends"
    FIND_LOVE = "find_love"
    BUILD_FAMILY = "build_family"
    GAIN_POPULARITY = "gain_popularity"

    # Power
    BECOME_LEADER = "become_leader"
    DOMINATE_AREA = "dominate_area"
    BUILD_EMPIRE = "build_empire"

    # Knowledge
    MASTER_SKILL = "master_skill"
    DISCOVER_INNOVATION = "discover_innovation"
    BUILD_LIBRARY = "build_library"

    # Creative
    CREATE_ART = "create_art"
    BUILD_MONUMENT = "build_monument"
    LEAVE_LEGACY = "leave_legacy"

    # Conflict
    DEFEAT_RIVAL = "defeat_rival"
    CONQUER_TERRITORY = "conquer_territory"
    REVENGE = "revenge"


@dataclass
class Goal:
    """A goal an agent is pursuing"""
    id: str
    goal_type: GoalType
    description: str
    created_at: datetime = field(default_factory=datetime.now)

    # Progress
    progress: float = 0.0  # 0-1
    completed: bool = False
    completed_at: Optional[datetime] = None

    # Priority (how important)
    priority: float = 0.5  # 0-1

    # Plan (steps to achieve goal)
    planned_actions: List[str] = field(default_factory=list)
    current_step: int = 0

    # Obstacles encountered
    obstacles: List[str] = field(default_factory=list)
    failures: int = 0

    def advance_step(self) -> bool:
        """Move to next step in plan"""
        if self.current_step < len(self.planned_actions) - 1:
            self.current_step += 1
            return True
        return False

    def add_obstacle(self, obstacle: str):
        """Record an obstacle"""
        self.obstacles.append(obstacle)
        self.failures += 1

    def update_progress(self, amount: float):
        """Update progress toward goal"""
        self.progress = min(1.0, self.progress + amount)

        if self.progress >= 1.0:
            self.completed = True
            self.completed_at = datetime.now()


class StrategicPlanner:
    """Creates strategic plans for agents"""

    @staticmethod
    def choose_goal(
        agent: 'Agent',
        world_context: Dict
    ) -> Optional[Goal]:
        """
        Agent chooses a goal based on their psychology and situation

        Agents with different personalities pursue different goals!
        """
        # Analyze agent's psychology
        personality = agent.personality
        needs = agent.needs

        # Score different goal types based on personality + needs
        goal_scores = {}

        # Survival goals (high if needs urgent)
        from engine.psychology import NeedType
        if needs.needs[NeedType.HUNGER].get_urgency() > 0.8:
            goal_scores[GoalType.SECURE_FOOD] = 1.0
        if needs.needs[NeedType.SHELTER].get_urgency() > 0.7:
            goal_scores[GoalType.FIND_SHELTER] = 0.9

        # Economic goals (high conscientiousness + low agreeableness)
        if personality.conscientiousness > 0.6 and agent.wealth < 500:
            goal_scores[GoalType.GET_RICH] = (
                personality.conscientiousness * personality.ambition
            )

        # Social goals (high extraversion + high agreeableness)
        if personality.extraversion > 0.6:
            if needs.needs[NeedType.FRIENDSHIP].get_urgency() > 0.6:
                goal_scores[GoalType.MAKE_FRIENDS] = personality.extraversion

        if personality.sexuality > 0.6:
            if needs.needs[NeedType.ROMANCE].get_urgency() > 0.7:
                goal_scores[GoalType.FIND_LOVE] = personality.sexuality

        # Power goals (high ambition + low agreeableness)
        if personality.ambition > 0.7 and personality.agreeableness < 0.4:
            goal_scores[GoalType.BECOME_LEADER] = (
                personality.ambition * (1.0 - personality.agreeableness)
            )

        # Knowledge goals (high openness + high conscientiousness)
        if personality.openness > 0.7:
            goal_scores[GoalType.DISCOVER_INNOVATION] = (
                personality.openness * personality.creativity
            )

        # Creative goals (high creativity + high openness)
        if personality.creativity > 0.7:
            goal_scores[GoalType.CREATE_ART] = personality.creativity

        # Conflict goals (high aggression + high ambition)
        if personality.aggression > 0.6:
            # Check for rivals
            if world_context.get('has_rivals', False):
                goal_scores[GoalType.DEFEAT_RIVAL] = (
                    personality.aggression * personality.ambition
                )

        # No strong goals? Default to survival/wealth
        if not goal_scores:
            goal_scores[GoalType.ACCUMULATE_RESOURCES] = 0.5

        # Choose highest scoring goal
        best_goal_type = max(goal_scores, key=goal_scores.get)
        score = goal_scores[best_goal_type]

        # Only pursue if score high enough
        if score < 0.4:
            return None

        # Create goal
        import uuid
        goal_id = str(uuid.uuid4())

        goal = Goal(
            id=goal_id,
            goal_type=best_goal_type,
            description=StrategicPlanner._generate_goal_description(
                best_goal_type, agent.name
            ),
            priority=score
        )

        # Generate plan
        goal.planned_actions = StrategicPlanner._generate_plan(
            best_goal_type, agent, world_context
        )

        return goal

    @staticmethod
    def _generate_goal_description(goal_type: GoalType, agent_name: str) -> str:
        """Generate description for goal"""
        descriptions = {
            GoalType.SECURE_FOOD: f"{agent_name} wants to secure a reliable food source",
            GoalType.FIND_SHELTER: f"{agent_name} needs to find or build shelter",
            GoalType.GET_RICH: f"{agent_name} aims to accumulate wealth",
            GoalType.MAKE_FRIENDS: f"{agent_name} wants to build strong friendships",
            GoalType.FIND_LOVE: f"{agent_name} is searching for romance",
            GoalType.BECOME_LEADER: f"{agent_name} aspires to leadership",
            GoalType.DISCOVER_INNOVATION: f"{agent_name} wants to make discoveries",
            GoalType.CREATE_ART: f"{agent_name} wants to create art",
            GoalType.DEFEAT_RIVAL: f"{agent_name} seeks to defeat their rival",
        }

        return descriptions.get(goal_type, f"{agent_name} pursues a goal")

    @staticmethod
    def _generate_plan(
        goal_type: GoalType,
        agent: 'Agent',
        world_context: Dict
    ) -> List[str]:
        """
        Generate a plan (sequence of actions) to achieve goal

        Agent creates their OWN plan based on what they know
        """
        plans = {
            GoalType.SECURE_FOOD: [
                "find_food_source",
                "gather_food",
                "build_farm_if_possible",
                "stockpile_food",
            ],
            GoalType.FIND_SHELTER: [
                "gather_materials",
                "find_good_location",
                "build_shelter",
            ],
            GoalType.GET_RICH: [
                "gather_valuable_resources",
                "learn_trade_skill",
                "establish_trade_relationships",
                "build_business",
            ],
            GoalType.MAKE_FRIENDS: [
                "meet_new_people",
                "socialize_regularly",
                "help_others",
                "build_trust",
            ],
            GoalType.FIND_LOVE: [
                "meet_potential_partners",
                "build_relationship",
                "court_partner",
            ],
            GoalType.BECOME_LEADER: [
                "build_reputation",
                "gain_political_power",
                "form_faction",
                "challenge_leadership",
            ],
            GoalType.DISCOVER_INNOVATION: [
                "study_existing_knowledge",
                "experiment_with_combinations",
                "develop_new_technique",
            ],
            GoalType.CREATE_ART: [
                "learn_art_skill",
                "gather_materials",
                "create_artwork",
                "share_with_others",
            ],
            GoalType.DEFEAT_RIVAL: [
                "build_strength",
                "gather_allies",
                "prepare_for_conflict",
                "confront_rival",
            ],
        }

        return plans.get(goal_type, ["work_toward_goal"])


class StrategyManager:
    """Manages strategic planning for all agents"""

    def __init__(self):
        # Agent goals
        self.agent_goals: Dict[str, List[Goal]] = {}  # agent_id -> goals

        # Completed goals (for history)
        self.completed_goals: Dict[str, List[Goal]] = {}

    def get_agent_goals(self, agent_id: str) -> List[Goal]:
        """Get agent's current goals"""
        return self.agent_goals.get(agent_id, [])

    def add_goal(self, agent_id: str, goal: Goal):
        """Add goal for agent"""
        if agent_id not in self.agent_goals:
            self.agent_goals[agent_id] = []

        self.agent_goals[agent_id].append(goal)

        # Sort by priority
        self.agent_goals[agent_id].sort(key=lambda g: g.priority, reverse=True)

    def complete_goal(self, agent_id: str, goal_id: str):
        """Mark goal as complete"""
        goals = self.agent_goals.get(agent_id, [])

        for goal in goals:
            if goal.id == goal_id:
                goal.completed = True
                goal.completed_at = datetime.now()

                # Move to completed
                if agent_id not in self.completed_goals:
                    self.completed_goals[agent_id] = []
                self.completed_goals[agent_id].append(goal)

                # Remove from active
                goals.remove(goal)
                break

    def abandon_goal(self, agent_id: str, goal_id: str):
        """Agent gives up on goal"""
        goals = self.agent_goals.get(agent_id, [])

        for goal in goals:
            if goal.id == goal_id:
                goals.remove(goal)
                break

    def update_goal_progress(
        self,
        agent_id: str,
        goal_id: str,
        progress: float,
        action_result: Dict
    ):
        """Update progress on a goal"""
        goals = self.agent_goals.get(agent_id, [])

        for goal in goals:
            if goal.id == goal_id:
                # Update progress
                goal.update_progress(progress)

                # Check for obstacles
                if not action_result.get('success', True):
                    goal.add_obstacle(action_result.get('reason', 'unknown'))

                # Advance to next step if current step successful
                if action_result.get('success', False):
                    goal.advance_step()

                # Complete if done
                if goal.completed:
                    self.complete_goal(agent_id, goal_id)

                break

    def get_current_goal(self, agent_id: str) -> Optional[Goal]:
        """Get agent's highest priority goal"""
        goals = self.agent_goals.get(agent_id, [])

        if not goals:
            return None

        return goals[0]  # Already sorted by priority

    def should_pursue_new_goal(
        self,
        agent_id: str,
        agent: 'Agent'
    ) -> bool:
        """Check if agent should pursue a new goal"""
        current_goals = self.get_agent_goals(agent_id)

        # No goals? Definitely need one
        if not current_goals:
            return True

        # Too many goals? Don't add more
        if len(current_goals) >= 3:
            return False

        # Personality affects goal-setting
        # High conscientiousness = more goals
        # High openness = more diverse goals

        goal_chance = (
            agent.personality.conscientiousness * 0.5 +
            agent.personality.openness * 0.3 +
            agent.personality.ambition * 0.2
        )

        return random.random() < goal_chance * 0.1  # 10% base chance per tick

    def evaluate_goal_action(
        self,
        agent: 'Agent',
        goal: Goal
    ) -> Optional[str]:
        """
        Determine what action agent should take to advance their goal

        Returns action type or None
        """
        # Get current step in plan
        if goal.current_step >= len(goal.planned_actions):
            # Plan complete
            return None

        current_action = goal.planned_actions[goal.current_step]

        # Map plan steps to actual action types
        action_mapping = {
            'find_food_source': 'explore',
            'gather_food': 'gather_food',
            'gather_materials': 'gather_materials',
            'build_shelter': 'build',
            'meet_new_people': 'socialize',
            'socialize_regularly': 'socialize',
            'meet_potential_partners': 'seek_romance',
            'build_relationship': 'socialize',
            'study_existing_knowledge': 'learn_skill',
            'experiment_with_combinations': 'craft',
            'build_strength': 'train_combat',
            'gather_allies': 'recruit',
            'learn_trade_skill': 'learn_skill',
            'establish_trade_relationships': 'trade',
        }

        return action_mapping.get(current_action, current_action)

    def get_statistics(self) -> Dict:
        """Get strategy statistics"""
        total_active_goals = sum(len(goals) for goals in self.agent_goals.values())
        total_completed = sum(len(goals) for goals in self.completed_goals.values())

        goal_type_distribution = {}
        for goals in self.agent_goals.values():
            for goal in goals:
                gtype = goal.goal_type.value
                goal_type_distribution[gtype] = goal_type_distribution.get(gtype, 0) + 1

        return {
            'total_active_goals': total_active_goals,
            'total_completed_goals': total_completed,
            'agents_with_goals': len(self.agent_goals),
            'goal_distribution': goal_type_distribution,
        }
