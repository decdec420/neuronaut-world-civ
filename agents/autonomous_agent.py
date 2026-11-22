"""
Autonomous Agent Extensions - TRUE AUTONOMY through LLM integration

This module extends the base Agent class with:
- LLM-powered decision making (unlimited AI thinking)
- Long-term goal planning
- Persistent memory and learning
- Self-reflection and growth
- Creative problem solving

Agents have COMPLETE FREEDOM to:
- Make any decision they want
- Plan their own life goals
- Learn from experiences
- Develop unique personalities through choices
- Build their own path in life

NO artificial constraints on agent autonomy!
"""

import logging
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class GoalType(Enum):
    """Types of goals agents can pursue"""
    SURVIVAL = "survival"  # Basic needs
    WEALTH = "wealth"  # Become rich
    FAMILY = "family"  # Build family, raise children
    KNOWLEDGE = "knowledge"  # Discover, learn, innovate
    CREATIVITY = "creativity"  # Create art, build beautiful things
    POWER = "power"  # Become leader, gain influence
    SOCIAL = "social"  # Make friends, be popular
    HEDONISM = "hedonism"  # Have fun, enjoy life
    SPIRITUALITY = "spirituality"  # Find meaning, help others
    LEGACY = "legacy"  # Be remembered, make impact


@dataclass
class Goal:
    """A goal an agent is pursuing"""
    goal_type: GoalType
    description: str  # Agent's own words
    priority: float  # 0-1, how important
    progress: float = 0.0  # 0-1, how far along
    created_tick: int = 0
    deadline_tick: Optional[int] = None  # When to achieve by
    subgoals: List[str] = field(default_factory=list)
    achieved: bool = False


@dataclass
class Memory:
    """A memory of an event"""
    id: str
    tick: int
    timestamp: datetime
    event_type: str
    description: str
    emotional_intensity: float  # How strongly remembered (0-1)
    importance: float  # How significant (0-1)
    participants: List[str] = field(default_factory=list)  # Other agents involved
    location: tuple = (0, 0)
    related_goal: Optional[str] = None


class MemorySystem:
    """
    Agent's memory and learning system

    Agents remember:
    - Important life events (births, deaths, discoveries)
    - Successes and failures
    - Relationships and interactions
    - Lessons learned
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.episodic_memory: List[Memory] = []  # Life events
        self.semantic_memory: Dict[str, Any] = {}  # Facts and knowledge
        self.procedural_memory: Dict[str, float] = {}  # Skills learned
        self.emotional_memories: List[Memory] = []  # Strongest emotional moments

    def remember(
        self,
        tick: int,
        event_type: str,
        description: str,
        emotional_intensity: float = 0.5,
        importance: float = 0.5,
        participants: List[str] = None,
        location: tuple = (0, 0)
    ):
        """Store a new memory"""

        memory = Memory(
            id=f"mem_{tick}_{random.randint(1000, 9999)}",
            tick=tick,
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            emotional_intensity=emotional_intensity,
            importance=importance,
            participants=participants or [],
            location=location
        )

        self.episodic_memory.append(memory)

        # Strong emotional memories are specially tracked
        if emotional_intensity > 0.7:
            self.emotional_memories.append(memory)

        # Trim old, unimportant memories
        self._consolidate_memories()

        logger.debug(f"[{self.agent_id}] Remembered: {description}")

    def _consolidate_memories(self):
        """Keep only important/recent memories to manage size"""

        # Keep all memories if we don't have many
        if len(self.episodic_memory) <= 100:
            return

        # Sort by importance and recency
        sorted_memories = sorted(
            self.episodic_memory,
            key=lambda m: m.importance * 0.5 + (m.tick / 10000) * 0.5,
            reverse=True
        )

        # Keep top 100
        self.episodic_memory = sorted_memories[:100]

    def get_recent_memories(self, count: int = 10) -> List[Memory]:
        """Get most recent memories"""
        return sorted(
            self.episodic_memory,
            key=lambda m: m.tick,
            reverse=True
        )[:count]

    def get_memories_about(self, agent_id: str) -> List[Memory]:
        """Get all memories involving another agent"""
        return [m for m in self.episodic_memory if agent_id in m.participants]

    def get_significant_memories(self, min_importance: float = 0.7) -> List[Memory]:
        """Get life-defining moments"""
        return [m for m in self.episodic_memory if m.importance >= min_importance]

    def add_memory(self, memory_obj):
        """
        Compatibility method for original Agent memory system

        Converts old Memory format to autonomous Memory format
        """
        # Extract data from old memory object
        from agents.agent import Memory as OldMemory

        if isinstance(memory_obj, OldMemory):
            # Convert old memory to new format
            self.remember(
                tick=0,  # We don't have tick in old memory
                event_type=memory_obj.event_type,
                description=f"{memory_obj.event_type} - emotional impact: {memory_obj.emotional_impact}",
                emotional_intensity=abs(memory_obj.emotional_impact),
                importance=0.5,  # Default importance
                participants=memory_obj.agents_involved,
                location=(memory_obj.location.x if hasattr(memory_obj.location, 'x') else 0,
                         memory_obj.location.y if hasattr(memory_obj.location, 'y') else 0)
            )
        else:
            # If it's already in new format or unknown, just log it
            logger.warning(f"add_memory called with unexpected type: {type(memory_obj)}")

    def learn_fact(self, key: str, value: Any):
        """Learn a new fact or update knowledge"""
        self.semantic_memory[key] = value

    def improve_skill(self, skill_name: str, amount: float = 0.1):
        """Improve a skill through practice"""
        current = self.procedural_memory.get(skill_name, 0.0)
        self.procedural_memory[skill_name] = min(1.0, current + amount)


class GoalSystem:
    """
    Agent's goal planning and pursuit system

    Agents have FULL AUTONOMY to:
    - Set their own life goals
    - Prioritize what matters to them
    - Change goals based on experiences
    - Pursue multiple goals simultaneously
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.active_goals: List[Goal] = []
        self.completed_goals: List[Goal] = []
        self.abandoned_goals: List[Goal] = []

    def add_goal(
        self,
        goal_type: GoalType,
        description: str,
        priority: float,
        current_tick: int,
        deadline_tick: Optional[int] = None
    ):
        """Agent sets a new goal"""

        goal = Goal(
            goal_type=goal_type,
            description=description,
            priority=priority,
            created_tick=current_tick,
            deadline_tick=deadline_tick
        )

        self.active_goals.append(goal)

        logger.info(f"🎯 [{self.agent_id}] New goal: {description} (priority: {priority:.2f})")

    def get_top_goals(self, count: int = 3) -> List[Goal]:
        """Get highest priority active goals"""
        return sorted(
            self.active_goals,
            key=lambda g: g.priority,
            reverse=True
        )[:count]

    def update_goal_progress(self, goal_description: str, progress_delta: float):
        """Update progress on a goal"""

        for goal in self.active_goals:
            if goal_description.lower() in goal.description.lower():
                goal.progress += progress_delta
                goal.progress = min(1.0, goal.progress)

                if goal.progress >= 1.0:
                    goal.achieved = True
                    self.completed_goals.append(goal)
                    self.active_goals.remove(goal)
                    logger.info(f"🎉 [{self.agent_id}] Goal achieved: {goal.description}")

    def abandon_goal(self, goal_description: str, reason: str = "Changed priorities"):
        """Agent gives up on a goal"""

        for goal in self.active_goals:
            if goal_description.lower() in goal.description.lower():
                self.abandoned_goals.append(goal)
                self.active_goals.remove(goal)
                logger.info(f"❌ [{self.agent_id}] Abandoned goal: {goal.description} ({reason})")

    def has_goal_type(self, goal_type: GoalType) -> bool:
        """Check if agent is pursuing this type of goal"""
        return any(g.goal_type == goal_type for g in self.active_goals)


class AutonomousAgentMixin:
    """
    Mixin to add autonomous AI capabilities to Agent class

    This gives agents:
    - LLM-powered thinking
    - Long-term planning
    - Memory and learning
    - Full decision autonomy
    """

    def init_autonomous_systems(self, llm_brain=None):
        """Initialize autonomous systems (call in Agent.__init__)"""

        # LLM brain for AI thinking
        self.llm_brain = llm_brain

        # Memory system - KEEP existing SmartMemorySystem from Agent.__init__
        # (Don't replace it with old MemorySystem - SmartMemorySystem is superior)
        # self.memory is already initialized as SmartMemorySystem in Agent.__init__

        # Goal planning
        self.goals = GoalSystem(self.id)

        # Counters for periodic autonomous thinking
        self.ticks_since_planning = 0
        self.ticks_since_reflection = 0

        # Recent memories for LLM context
        self.recent_memories: List[str] = []

    def autonomous_decide(self, perceptions: Dict, current_tick: int, config) -> 'Action':
        """
        Make decision with FULL AUTONOMY

        Process:
        1. Check if critical survival needs (fall back to rule-based)
        2. Periodic long-term planning (set/update goals)
        3. Periodic self-reflection (learn and grow)
        4. Use LLM to make contextual decision based on goals and personality

        Returns: Action to take
        """

        from agents.agent import Action, ActionType
        from engine.psychology import NeedType

        # ===== EMERGENCY SURVIVAL (no AI needed) =====
        # If dying, immediately take survival action
        if self.needs.needs[NeedType.THIRST].level > 0.9 and self.inventory.has_item('water'):
            logger.info(f"🚨 {self.name} EMERGENCY: Drinking water to survive!")
            return Action(ActionType.DRINK)

        if self.needs.needs[NeedType.HUNGER].level > 0.9 and self.inventory.has_item('food'):
            logger.info(f"🚨 {self.name} EMERGENCY: Eating food to survive!")
            return Action(ActionType.EAT)

        if self.health < 20:
            logger.info(f"🚨 {self.name} EMERGENCY: Resting due to critical health!")
            return Action(ActionType.REST)

        # ===== AUTONOMOUS AI THINKING =====

        # Check if LLM is available
        if not self.llm_brain or not config.use_llm_decisions:
            return None  # the agent updater uses the rule-based brain

        # Periodic long-term planning
        self.ticks_since_planning += 1
        if self.ticks_since_planning >= config.long_term_planning_interval:
            self._do_long_term_planning(perceptions, current_tick)
            self.ticks_since_planning = 0

        # Periodic self-reflection
        self.ticks_since_reflection += 1
        if self.ticks_since_reflection >= config.reflection_interval:
            self._do_self_reflection(perceptions, current_tick)
            self.ticks_since_reflection = 0

        # Make AI-powered decision
        return self._llm_decide_action(perceptions)

    def _do_long_term_planning(self, perceptions: Dict, current_tick: int):
        """Agent thinks about long-term goals using AI"""

        logger.info(f"🧠 {self.name} is planning their future...")

        response = self.llm_brain.agent_think(
            agent=self,
            perceptions=perceptions,
            thinking_mode="long_term_planning"
        )

        if response:
            # Parse goals from AI response
            self._parse_and_set_goals(response, current_tick)

            # Remember this planning session
            self.memory.remember(
                tick=current_tick,
                event_type="planning",
                description=f"Planned future goals: {response[:100]}",
                importance=0.6
            )

    def _parse_and_set_goals(self, ai_response: str, current_tick: int):
        """Parse AI response and create goals"""

        # Simple keyword-based goal extraction
        # (You could make this more sophisticated with structured prompts)

        response_lower = ai_response.lower()

        # Map keywords to goal types
        goal_keywords = {
            GoalType.WEALTH: ['wealth', 'rich', 'money', 'trade', 'business'],
            GoalType.FAMILY: ['family', 'children', 'marry', 'romance', 'partner'],
            GoalType.KNOWLEDGE: ['discover', 'learn', 'knowledge', 'research', 'experiment'],
            GoalType.CREATIVITY: ['create', 'art', 'build', 'invent', 'design'],
            GoalType.POWER: ['leader', 'power', 'govern', 'influence', 'control'],
            GoalType.SOCIAL: ['friends', 'social', 'popular', 'community', 'relationships'],
            GoalType.HEDONISM: ['fun', 'enjoy', 'pleasure', 'party', 'celebrate'],
        }

        # Detect goals from response
        for goal_type, keywords in goal_keywords.items():
            if any(keyword in response_lower for keyword in keywords):
                # Check if already pursuing this type of goal
                if not self.goals.has_goal_type(goal_type):
                    # Add new goal
                    priority = self._calculate_goal_priority(goal_type)
                    self.goals.add_goal(
                        goal_type=goal_type,
                        description=f"Pursue {goal_type.value}",
                        priority=priority,
                        current_tick=current_tick
                    )

    def _calculate_goal_priority(self, goal_type: GoalType) -> float:
        """Calculate goal priority based on personality"""

        # Map goal types to personality traits
        priority_map = {
            GoalType.WEALTH: self.personality.ambition * 0.7 + self.personality.conscientiousness * 0.3,
            GoalType.FAMILY: (1.0 - self.personality.ambition) * 0.5 + self.personality.agreeableness * 0.5,
            GoalType.KNOWLEDGE: self.personality.openness * 0.6 + self.personality.creativity * 0.4,
            GoalType.CREATIVITY: self.personality.creativity * 0.8 + self.personality.openness * 0.2,
            GoalType.POWER: self.personality.ambition * 0.8 + self.personality.extraversion * 0.2,
            GoalType.SOCIAL: self.personality.extraversion * 0.7 + self.personality.agreeableness * 0.3,
            GoalType.HEDONISM: self.personality.extraversion * 0.5 + (1.0 - self.personality.conscientiousness) * 0.5,
        }

        return priority_map.get(goal_type, 0.5)

    def _do_self_reflection(self, perceptions: Dict, current_tick: int):
        """Agent reflects on their life using AI"""

        logger.info(f"💭 {self.name} is reflecting on their life...")

        response = self.llm_brain.agent_think(
            agent=self,
            perceptions=perceptions,
            thinking_mode="reflection"
        )

        if response:
            # Store reflection as memory
            self.memory.remember(
                tick=current_tick,
                event_type="reflection",
                description=f"Reflected: {response[:150]}",
                emotional_intensity=0.6,
                importance=0.5
            )

            # Update recent memories for context
            self.recent_memories.append(f"[Self-reflection] {response[:100]}")
            if len(self.recent_memories) > 10:
                self.recent_memories = self.recent_memories[-10:]

    def _llm_decide_action(self, perceptions: Dict) -> Optional['Action']:
        """Ask the AI brain what to do. None means use the rule-based brain this tick."""
        response = self.llm_brain.agent_think(
            agent=self,
            perceptions=perceptions,
            thinking_mode="decide_action"
        )
        if not response:
            return None  # no model reachable
        return self._parse_action_from_llm(response.strip(), perceptions)

    def _parse_action_from_llm(self, llm_response: str, perceptions: Optional[Dict] = None) -> Optional['Action']:
        """Read 'ACTION: <name> / TARGET: <person> / DETAILS / REASON' into an Action.

        Returns None (and counts a parse failure) if the answer doesn't name an
        action on the menu. The old keyword search returned REST for anything it
        couldn't read, and matched words inside other words ("create_art" read
        as eat).
        """
        from agents.agent import Action, ActionType
        from agents.action_menu import parse_decision

        menu = getattr(self.llm_brain, 'action_menu', None) if self.llm_brain else None
        valid = menu.names if menu else {a.value for a in ActionType}
        perceptions = perceptions if perceptions is not None else (getattr(self, 'last_perception', None) or {})
        decision = parse_decision(llm_response, valid, perceptions.get('people_by_name', {}))
        if self.llm_brain is not None and hasattr(self.llm_brain, 'record_parse'):
            self.llm_brain.record_parse(decision is not None, llm_response)
        if decision is None:
            return None

        parameters = {}
        if decision.details:
            parameters['details'] = decision.details
            if decision.action in ('vote', 'campaign'):
                parameters['choice'] = 'no' if decision.details.strip().lower().startswith('no') else 'yes'
        if decision.reason:
            parameters['reason'] = decision.reason
        logger.debug(f"[{self.name}] AI chose {decision.action} ({decision.reason})")
        return Action(ActionType(decision.action), target_agent=decision.target_id, parameters=parameters)

    def _fallback_rule_based_decision(self, perceptions: Dict) -> 'Action':
        """Fallback to original psychology-based decision making"""

        # Use the original Agent.decide() method
        # This method should exist in the Agent class
        return self.decide(perceptions)

    def remember_event(
        self,
        tick: int,
        event_type: str,
        description: str,
        emotional_intensity: float = 0.5,
        importance: float = 0.5,
        participants: List[str] = None
    ):
        """Wrapper to remember an event"""

        self.memory.remember(
            tick=tick,
            event_type=event_type,
            description=description,
            emotional_intensity=emotional_intensity,
            importance=importance,
            participants=participants,
            location=(self.location.x, self.location.y)
        )

        # Add to recent memories for LLM context
        self.recent_memories.append(f"[{event_type}] {description}")
        if len(self.recent_memories) > 15:
            self.recent_memories = self.recent_memories[-15:]
