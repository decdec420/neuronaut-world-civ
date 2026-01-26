"""
Swarm Intelligence System - Multi-Agent LLM Coordination

This system enables TRUE EMERGENT BEHAVIOR through collective AI coordination.
Agents don't just act independently - they form alliances, share knowledge,
coordinate strategies, and make collective decisions that no single agent could make alone.

Key Features:
- **Social Network Decision-Making**: Agents consider nearby agents' intentions
- **Emergent Consensus**: Collective decision-making without hardcoded rules
- **Knowledge Sharing**: Semantic memory allows agents to learn from each other
- **Dynamic Alliances**: Friendships and rivalries emerge naturally
- **Swarm Coordination**: Groups coordinate complex multi-agent tasks

This is the foundation for true AI autonomy - where civilization emerges
from agent interactions rather than being programmed.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from agents.llm_brain import MultiLLMBrain, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class ConsensusType(Enum):
    """Types of collective decisions"""
    UNANIMOUS = "unanimous"      # All must agree
    MAJORITY = "majority"        # >50% must agree
    QUORUM = "quorum"           # Sufficient participation
    WEIGHTED = "weighted"        # Based on agent status/expertise


@dataclass
class AgentIntention:
    """Represents an agent's current intention/plan"""
    agent_id: str
    action_type: str
    target: Optional[str] = None
    reasoning: str = ""
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'action_type': self.action_type,
            'target': self.target,
            'reasoning': self.reasoning,
            'confidence': self.confidence
        }


@dataclass
class CollectiveDecision:
    """Result of swarm decision-making"""
    decision: str
    participants: List[str]
    consensus_level: float  # 0.0 to 1.0
    reasoning: str
    dissenting_opinions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class SwarmIntelligence:
    """
    Multi-Agent LLM Coordination System

    This enables agents to:
    1. Share their intentions with nearby agents
    2. Make collective decisions through emergent consensus
    3. Form dynamic alliances based on shared goals
    4. Coordinate complex multi-agent tasks

    Example Emergent Behaviors:
    - Hunters coordinate to surround prey
    - Builders collaborate on large structures
    - Traders form markets and negotiate
    - Warriors form battle formations
    - Scientists collaborate on discoveries
    """

    def __init__(self, llm_brain: MultiLLMBrain, config: Dict[str, Any] = None):
        self.llm_brain = llm_brain
        self.config = config or {}

        # Configuration
        self.max_swarm_size = self.config.get('max_swarm_size', 10)
        self.consensus_threshold = self.config.get('consensus_threshold', 0.6)
        self.coordination_radius = self.config.get('coordination_radius', 5.0)
        self.enable_parallel_llm = self.config.get('enable_parallel_llm', True)

        # Active intentions (agent_id -> AgentIntention)
        self.intentions: Dict[str, AgentIntention] = {}

        # Social network tracking
        self.alliances: Dict[str, List[str]] = {}  # agent_id -> list of ally_ids
        self.rivalries: Dict[str, List[str]] = {}  # agent_id -> list of rival_ids

        # Statistics
        self.total_swarm_decisions = 0
        self.successful_coordinations = 0
        self.emergent_alliances_formed = 0

    # ============================================================================
    # CORE SWARM INTELLIGENCE METHODS
    # ============================================================================

    async def social_network_decision(
        self,
        agent: 'Agent',
        action_type: str,
        nearby_agents: List['Agent'],
        context: Dict[str, Any] = None
    ) -> Tuple[str, str]:
        """
        Make a decision considering nearby agents' intentions and relationships.

        This is where EMERGENT BEHAVIOR happens:
        - Agents see what allies are doing and coordinate
        - Agents compete with rivals for resources
        - Agents learn from successful strategies of others
        - Groups spontaneously form around shared goals

        Args:
            agent: The agent making the decision
            action_type: Type of action being considered
            nearby_agents: Agents within coordination radius
            context: Additional context (resources, threats, etc.)

        Returns:
            Tuple of (decision, reasoning)
        """
        context = context or {}

        # Gather intentions from nearby agents
        nearby_intentions = []
        for nearby in nearby_agents[:self.max_swarm_size]:
            if nearby.agent_id in self.intentions:
                intention = self.intentions[nearby.agent_id]
                nearby_intentions.append(intention)

        # Check relationships
        allies = self.alliances.get(agent.agent_id, [])
        rivals = self.rivalries.get(agent.agent_id, [])

        ally_intentions = [i for i in nearby_intentions if i.agent_id in allies]
        rival_intentions = [i for i in nearby_intentions if i.agent_id in rivals]
        neutral_intentions = [i for i in nearby_intentions if i.agent_id not in allies and i.agent_id not in rivals]

        # Build context for LLM
        prompt = self._build_social_decision_prompt(
            agent=agent,
            action_type=action_type,
            ally_intentions=ally_intentions,
            rival_intentions=rival_intentions,
            neutral_intentions=neutral_intentions,
            context=context
        )

        # Get decision from LLM (considering social context)
        provider = self.llm_brain.get_available_provider(complexity="complex")
        response = self.llm_brain.call_llm(
            provider=provider,
            prompt=prompt,
            temperature=0.8,  # Higher temp for creative coordination
            max_tokens=300
        )

        if response:
            decision, reasoning = self._parse_social_decision(response.text)

            # Update this agent's intention
            self.intentions[agent.agent_id] = AgentIntention(
                agent_id=agent.agent_id,
                action_type=action_type,
                reasoning=reasoning,
                confidence=0.8
            )

            return decision, reasoning

        # Fallback: act independently
        return action_type, "No social coordination available"

    async def emergent_consensus(
        self,
        agents: List['Agent'],
        decision_topic: str,
        options: List[str],
        consensus_type: ConsensusType = ConsensusType.MAJORITY
    ) -> CollectiveDecision:
        """
        Collective decision-making where consensus emerges from agent discussions.

        This enables TRUE SWARM INTELLIGENCE:
        - No hardcoded rules for group decisions
        - Agents debate and persuade each other
        - Different perspectives lead to better decisions
        - Minority opinions are preserved for learning

        Example Use Cases:
        - Should we attack another settlement?
        - Where should we build the next city?
        - Which technology should we research?
        - How should we respond to a threat?

        Args:
            agents: List of agents participating in decision
            decision_topic: What they're deciding about
            options: Possible choices
            consensus_type: How to determine consensus

        Returns:
            CollectiveDecision with the group's choice
        """
        if not agents or not options:
            return CollectiveDecision(
                decision=options[0] if options else "no_action",
                participants=[],
                consensus_level=0.0,
                reasoning="Insufficient participants or options"
            )

        # Limit swarm size for performance
        participating_agents = agents[:self.max_swarm_size]

        # Phase 1: Each agent forms initial opinion (parallel LLM calls)
        if self.enable_parallel_llm:
            initial_opinions = await self._gather_opinions_parallel(
                agents=participating_agents,
                decision_topic=decision_topic,
                options=options
            )
        else:
            initial_opinions = await self._gather_opinions_sequential(
                agents=participating_agents,
                decision_topic=decision_topic,
                options=options
            )

        # Phase 2: Agents debate and influence each other
        final_opinions = await self._debate_phase(
            agents=participating_agents,
            decision_topic=decision_topic,
            initial_opinions=initial_opinions,
            rounds=2  # 2 rounds of debate
        )

        # Phase 3: Calculate consensus
        decision = self._calculate_consensus(
            opinions=final_opinions,
            consensus_type=consensus_type,
            threshold=self.consensus_threshold
        )

        self.total_swarm_decisions += 1

        return decision

    # ============================================================================
    # ALLIANCE & RIVALRY TRACKING
    # ============================================================================

    def update_relationships(
        self,
        agent1_id: str,
        agent2_id: str,
        interaction_type: str,
        success: bool
    ):
        """
        Update alliance/rivalry based on interactions.

        Emergent Relationships Form From:
        - Successful cooperation → Stronger alliance
        - Failed cooperation → Weakened bond
        - Competition for resources → Rivalry
        - Repeated positive interactions → Friendship

        Args:
            agent1_id: First agent
            agent2_id: Second agent
            interaction_type: Type of interaction (cooperate, compete, trade, etc.)
            success: Whether interaction was successful
        """
        # Initialize if needed
        if agent1_id not in self.alliances:
            self.alliances[agent1_id] = []
        if agent1_id not in self.rivalries:
            self.rivalries[agent1_id] = []

        # Positive interactions strengthen alliances
        if interaction_type in ['cooperate', 'trade', 'gift', 'protect'] and success:
            if agent2_id not in self.alliances[agent1_id]:
                self.alliances[agent1_id].append(agent2_id)
                self.emergent_alliances_formed += 1
                logger.info(f"🤝 Alliance formed: {agent1_id} ↔ {agent2_id}")

            # Remove from rivalries if present
            if agent2_id in self.rivalries[agent1_id]:
                self.rivalries[agent1_id].remove(agent2_id)

        # Negative interactions create rivalries
        elif interaction_type in ['attack', 'steal', 'compete'] or not success:
            if agent2_id not in self.rivalries[agent1_id]:
                self.rivalries[agent1_id].append(agent2_id)
                logger.info(f"⚔️ Rivalry formed: {agent1_id} ↔ {agent2_id}")

            # Remove from alliances if present
            if agent2_id in self.alliances[agent1_id]:
                self.alliances[agent1_id].remove(agent2_id)

    def get_agent_allies(self, agent_id: str) -> List[str]:
        """Get list of agent's allies"""
        return self.alliances.get(agent_id, []).copy()

    def get_agent_rivals(self, agent_id: str) -> List[str]:
        """Get list of agent's rivals"""
        return self.rivalries.get(agent_id, []).copy()

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _build_social_decision_prompt(
        self,
        agent: 'Agent',
        action_type: str,
        ally_intentions: List[AgentIntention],
        rival_intentions: List[AgentIntention],
        neutral_intentions: List[AgentIntention],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for social network decision-making"""

        prompt = f"""You are {agent.name}, deciding what to do next.

Your intended action: {action_type}

NEARBY ALLIES ({len(ally_intentions)}):
"""
        for intention in ally_intentions[:3]:  # Top 3 allies
            prompt += f"- {intention.agent_id}: {intention.action_type} ({intention.reasoning})\n"

        if rival_intentions:
            prompt += f"\nNEARBY RIVALS ({len(rival_intentions)}):\n"
            for intention in rival_intentions[:3]:
                prompt += f"- {intention.agent_id}: {intention.action_type} ({intention.reasoning})\n"

        if neutral_intentions:
            prompt += f"\nOTHER AGENTS ({len(neutral_intentions)}):\n"
            for intention in neutral_intentions[:2]:
                prompt += f"- {intention.agent_id}: {intention.action_type}\n"

        prompt += f"""
Your personality: {getattr(agent, 'personality', 'balanced')}
Your needs: hunger={getattr(agent, 'hunger', 50)}, social={getattr(agent, 'social_need', 50)}

Should you:
A) Coordinate with allies (work together on shared goals)
B) Compete with rivals (outperform or counter them)
C) Act independently (pursue your own goal)

Respond with: DECISION: [A/B/C] | REASONING: [brief explanation]"""

        return prompt

    def _parse_social_decision(self, response: str) -> Tuple[str, str]:
        """Parse LLM response for social decision"""
        try:
            if 'DECISION:' in response and 'REASONING:' in response:
                parts = response.split('|')
                decision_part = parts[0].split('DECISION:')[1].strip()
                reasoning_part = parts[1].split('REASONING:')[1].strip() if len(parts) > 1 else ""

                # Map A/B/C to actions
                if 'A' in decision_part.upper():
                    return "coordinate_with_allies", reasoning_part
                elif 'B' in decision_part.upper():
                    return "compete_with_rivals", reasoning_part
                else:
                    return "act_independently", reasoning_part

            return "act_independently", response[:100]
        except Exception as e:
            logger.warning(f"Failed to parse social decision: {e}")
            return "act_independently", ""

    async def _gather_opinions_parallel(
        self,
        agents: List['Agent'],
        decision_topic: str,
        options: List[str]
    ) -> Dict[str, str]:
        """Gather agent opinions in parallel (faster)"""

        async def get_agent_opinion(agent: 'Agent') -> Tuple[str, str]:
            """Get single agent's opinion"""
            prompt = f"""As {agent.name}, choose the best option for: {decision_topic}

Options:
{chr(10).join(f'{i+1}. {opt}' for i, opt in enumerate(options))}

Your personality: {getattr(agent, 'personality', 'balanced')}

Respond with: CHOICE: [option number] | REASON: [why this is best]"""

            provider = self.llm_brain.get_available_provider(complexity="simple")
            response = self.llm_brain.call_llm(
                provider=provider,
                prompt=prompt,
                temperature=0.7,
                max_tokens=150
            )

            if response:
                return agent.agent_id, response.text
            return agent.agent_id, f"CHOICE: 1 | REASON: Default choice"

        # Run all LLM calls in parallel
        tasks = [get_agent_opinion(agent) for agent in agents]
        results = await asyncio.gather(*tasks)

        return dict(results)

    async def _gather_opinions_sequential(
        self,
        agents: List['Agent'],
        decision_topic: str,
        options: List[str]
    ) -> Dict[str, str]:
        """Gather agent opinions one by one (slower but more reliable)"""
        opinions = {}

        for agent in agents:
            prompt = f"""As {agent.name}, choose the best option for: {decision_topic}

Options:
{chr(10).join(f'{i+1}. {opt}' for i, opt in enumerate(options))}

Respond with: CHOICE: [option number] | REASON: [why]"""

            provider = self.llm_brain.get_available_provider(complexity="simple")
            response = self.llm_brain.call_llm(
                provider=provider,
                prompt=prompt,
                temperature=0.7,
                max_tokens=150
            )

            opinions[agent.agent_id] = response.text if response else "CHOICE: 1"

        return opinions

    async def _debate_phase(
        self,
        agents: List['Agent'],
        decision_topic: str,
        initial_opinions: Dict[str, str],
        rounds: int = 2
    ) -> Dict[str, str]:
        """
        Agents debate and potentially change their minds.

        This is where EMERGENT CONSENSUS forms - not from averaging,
        but from agents persuading each other with reasoning.
        """
        current_opinions = initial_opinions.copy()

        for round_num in range(rounds):
            # Each agent sees others' opinions and can reconsider
            for agent in agents:
                # Sample some other opinions to consider
                other_opinions = [
                    f"{aid}: {opinion}"
                    for aid, opinion in current_opinions.items()
                    if aid != agent.agent_id
                ][:5]  # Top 5 others

                if not other_opinions:
                    continue

                prompt = f"""Reconsidering: {decision_topic}

Your initial choice: {current_opinions.get(agent.agent_id, 'CHOICE: 1')}

Other agents' reasoning:
{chr(10).join(other_opinions)}

After hearing others, what's your final choice?
Respond with: CHOICE: [number] | REASON: [brief]"""

                provider = self.llm_brain.get_available_provider(complexity="simple")
                response = self.llm_brain.call_llm(
                    provider=provider,
                    prompt=prompt,
                    temperature=0.6,  # Lower temp = more stable opinions
                    max_tokens=150
                )

                if response:
                    current_opinions[agent.agent_id] = response.text

        return current_opinions

    def _calculate_consensus(
        self,
        opinions: Dict[str, str],
        consensus_type: ConsensusType,
        threshold: float
    ) -> CollectiveDecision:
        """Calculate final consensus from agent opinions"""

        # Parse choices from opinions
        choice_counts = {}
        all_reasoning = []

        for agent_id, opinion in opinions.items():
            try:
                # Extract choice number
                if 'CHOICE:' in opinion:
                    choice_str = opinion.split('CHOICE:')[1].split('|')[0].strip()
                    choice = int(''.join(filter(str.isdigit, choice_str)))
                    choice_counts[choice] = choice_counts.get(choice, 0) + 1

                    # Extract reasoning
                    if 'REASON:' in opinion:
                        reason = opinion.split('REASON:')[1].strip()[:100]
                        all_reasoning.append(f"{agent_id}: {reason}")
            except Exception as e:
                logger.debug(f"Failed to parse opinion from {agent_id}: {e}")

        if not choice_counts:
            return CollectiveDecision(
                decision="option_1",
                participants=list(opinions.keys()),
                consensus_level=0.0,
                reasoning="No valid choices parsed"
            )

        # Find winner based on consensus type
        total_votes = sum(choice_counts.values())
        winner = max(choice_counts.items(), key=lambda x: x[1])
        winner_choice, winner_votes = winner

        consensus_level = winner_votes / total_votes if total_votes > 0 else 0.0

        # Check if meets threshold
        if consensus_level >= threshold:
            self.successful_coordinations += 1

        return CollectiveDecision(
            decision=f"option_{winner_choice}",
            participants=list(opinions.keys()),
            consensus_level=consensus_level,
            reasoning=f"{winner_votes}/{total_votes} agents agree. " + "; ".join(all_reasoning[:3]),
            dissenting_opinions=[
                f"Option {choice}: {count} votes"
                for choice, count in choice_counts.items()
                if choice != winner_choice
            ]
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get swarm intelligence statistics"""
        return {
            'total_swarm_decisions': self.total_swarm_decisions,
            'successful_coordinations': self.successful_coordinations,
            'emergent_alliances': self.emergent_alliances_formed,
            'total_alliances': sum(len(allies) for allies in self.alliances.values()),
            'total_rivalries': sum(len(rivals) for rivals in self.rivalries.values()),
            'active_intentions': len(self.intentions),
        }
