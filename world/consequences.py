"""
Consequence System - Real Stakes, Real Rewards

Actions have REAL consequences:
- Death can be permanent
- Bankruptcy leaves agents homeless
- Building collapses kill occupants
- Explosions destroy workshops
- Failed romance damages reputation
- Bad leadership leads to exile

This creates genuine drama and emergent stories!

Without consequences: Agents try everything carelessly
With consequences: Agents weigh risks, plan carefully, dramatic moments emerge
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
import random
from engine.ids import new_uuid


@dataclass
class Consequence:
    """A consequence of an action"""
    id: str
    caused_by_action: str
    affected_agents: Set[str]
    timestamp: datetime

    # What happened
    consequence_type: str  # death, injury, bankruptcy, reputation_loss, etc.
    severity: float  # 0-1
    description: str

    # Ripple effects
    secondary_consequences: List[str] = field(default_factory=list)
    tick: Optional[int] = None      # sim time (timestamp is wall-clock)


class ConsequenceType:
    """Types of consequences"""
    # Life/Death
    DEATH = "death"
    INJURY = "injury"
    ILLNESS = "illness"

    # Economic
    BANKRUPTCY = "bankruptcy"
    RESOURCE_LOSS = "resource_loss"
    PROPERTY_DESTRUCTION = "property_destruction"

    # Social
    REPUTATION_DAMAGE = "reputation_damage"
    RELATIONSHIP_LOSS = "relationship_loss"
    EXILE = "exile"

    # Structural
    BUILDING_COLLAPSE = "building_collapse"
    EXPLOSION = "explosion"
    FIRE = "fire"

    # Political
    LOSS_OF_POWER = "loss_of_power"
    IMPRISONMENT = "imprisonment"


class ConsequenceEngine:
    """
    Manages consequences of actions.

    Makes risk/reward meaningful!
    """

    def __init__(self):
        self.consequences: Dict[str, Consequence] = {}
        self.death_count: int = 0
        self.bankruptcy_count: int = 0

    def evaluate_action_risk(
        self,
        action_type: str,
        agent_skill: float,
        context: Dict
    ) -> Dict:
        """
        Evaluate the risk of an action.

        Returns potential consequences and probabilities.
        """

        risks = []

        # Experimentation risks
        if action_type == "experiment":
            materials = context.get('materials', [])

            if any("reactive" in m for m in materials):
                risks.append({
                    "type": ConsequenceType.EXPLOSION,
                    "probability": 0.15 - (agent_skill * 0.1),
                    "severity": 0.8
                })

            if any("toxic" in m for m in materials):
                risks.append({
                    "type": ConsequenceType.ILLNESS,
                    "probability": 0.2 - (agent_skill * 0.15),
                    "severity": 0.6
                })

        # Construction risks
        elif action_type == "build":
            materials_count = context.get('materials_count', 0)

            if materials_count > 50:
                # Large construction = collapse risk
                risks.append({
                    "type": ConsequenceType.BUILDING_COLLAPSE,
                    "probability": 0.1 - (agent_skill * 0.08),
                    "severity": 0.9
                })

        # Combat risks
        elif action_type == "fight":
            opponent_strength = context.get('opponent_strength', 0.5)

            risks.append({
                "type": ConsequenceType.INJURY,
                "probability": opponent_strength * 0.6,
                "severity": 0.7
            })

            risks.append({
                "type": ConsequenceType.DEATH,
                "probability": opponent_strength * 0.1,
                "severity": 1.0
            })

        # Economic risks
        elif action_type == "trade":
            trade_value = context.get('value', 0)
            agent_wealth = context.get('wealth', 100)

            if trade_value > agent_wealth * 0.5:
                # Large trade = bankruptcy risk
                risks.append({
                    "type": ConsequenceType.BANKRUPTCY,
                    "probability": 0.15,
                    "severity": 0.8
                })

        return {"risks": risks, "total_risk": sum(r['probability'] * r['severity'] for r in risks)}

    def apply_consequence(
        self,
        consequence_type: str,
        affected_agents: Set[str],
        action: str,
        severity: float,
        context: Dict = None,
        agent_objects: List = None  # NEW: Pass actual agent objects for memory
    ) -> Consequence:
        """
        Apply a consequence to agents.

        NEW: Now connects to agent memory and learning!

        Returns the consequence record.
        """

        context = context or {}

        consequence = Consequence(
            id=str(new_uuid()),
            caused_by_action=action,
            affected_agents=affected_agents,
            timestamp=datetime.now(),
            consequence_type=consequence_type,
            severity=severity,
            description=self._generate_description(consequence_type, affected_agents, action, context),
            tick=context.get('current_tick'),
        )

        # Apply specific effects
        if consequence_type == ConsequenceType.DEATH:
            self.death_count += len(affected_agents)
            # Actual death handled by simulation

        elif consequence_type == ConsequenceType.BANKRUPTCY:
            self.bankruptcy_count += len(affected_agents)
            # Wealth set to 0, lose all property

        elif consequence_type == ConsequenceType.EXPLOSION:
            # Destroys workshop/resources
            consequence.secondary_consequences.append("workshop_destroyed")
            consequence.secondary_consequences.append("materials_lost")

            # Can injure nearby agents
            nearby_count = context.get('nearby_agents', 0)
            if nearby_count > 0:
                consequence.secondary_consequences.append(f"{nearby_count}_agents_injured")

        # ===== NEW: CONNECT TO AGENT MEMORY & LEARNING =====
        if agent_objects:
            current_tick = context.get('current_tick', 0)
            self._teach_agents_from_consequence(
                agent_objects,
                consequence,
                action,
                severity,
                current_tick
            )

        self.consequences[consequence.id] = consequence
        return consequence

    def _generate_description(
        self,
        consequence_type: str,
        agents: Set[str],
        action: str,
        context: Dict
    ) -> str:
        """Generate human-readable description"""

        agent_names = context.get('agent_names', list(agents))
        what = context.get('what')           # e.g. "heating clay and fire"
        who = ', '.join(agent_names[:3])
        if what:
            told = {ConsequenceType.EXPLOSION: f"An explosion while {who} was {what}",
                    "fire": f"A fire broke out while {who} was {what}",
                    ConsequenceType.INJURY: f"{who} was hurt while {what}"}
            if consequence_type in told:
                return told[consequence_type]

        descriptions = {
            ConsequenceType.DEATH: f"{', '.join(agent_names[:3])} died during {action}",
            ConsequenceType.INJURY: f"{', '.join(agent_names[:3])} were injured while {action}",
            ConsequenceType.BANKRUPTCY: f"{', '.join(agent_names[:3])} went bankrupt from {action}",
            ConsequenceType.EXPLOSION: f"Explosion during {action} destroyed everything nearby!",
            ConsequenceType.BUILDING_COLLAPSE: f"Building collapsed during {action}!",
            ConsequenceType.REPUTATION_DAMAGE: f"{', '.join(agent_names[:3])} lost reputation",
            ConsequenceType.EXILE: f"{', '.join(agent_names[:3])} were exiled from the community",
        }

        return descriptions.get(consequence_type, f"Consequence from {action}")

    def get_statistics(self) -> Dict:
        """Get consequence statistics"""

        return {
            "total_consequences": len(self.consequences),
            "deaths": self.death_count,
            "bankruptcies": self.bankruptcy_count,
            "by_type": self._count_by_type(),
            "most_dangerous_action": self._find_most_dangerous_action(),
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count consequences by type"""
        counts = {}
        for c in self.consequences.values():
            counts[c.consequence_type] = counts.get(c.consequence_type, 0) + 1
        return counts

    def _find_most_dangerous_action(self) -> Optional[str]:
        """Find which action causes most consequences"""
        if not self.consequences:
            return None

        action_counts = {}
        for c in self.consequences.values():
            action_counts[c.caused_by_action] = action_counts.get(c.caused_by_action, 0) + 1

        most_dangerous = max(action_counts.items(), key=lambda x: x[1])
        return f"{most_dangerous[0]} ({most_dangerous[1]} consequences)"

    def _teach_agents_from_consequence(
        self,
        agent_objects: List,
        consequence: Consequence,
        action: str,
        severity: float,
        current_tick: int
    ):
        """
        NEW: Teach agents from consequences

        Makes agents:
        1. Remember bad outcomes vividly
        2. Learn to avoid risky actions
        3. Update their risk perception
        4. Share warnings with others
        """

        for agent in agent_objects:
            # Calculate emotional intensity based on severity
            emotional_intensity = min(1.0, severity * 1.2)  # Severe = more memorable
            importance = min(1.0, severity)  # High importance for severe consequences

            # Create vivid memory description
            memory_description = self._create_memorable_description(
                consequence.consequence_type,
                action,
                severity,
                agent.name
            )

            # Store in agent memory (works with both original and autonomous memory)
            if hasattr(agent, 'memory'):
                # Check if autonomous memory (has remember method)
                if hasattr(agent.memory, 'remember'):
                    # Autonomous memory system
                    agent.memory.remember(
                        tick=current_tick,
                        event_type=f"consequence_{consequence.consequence_type}",
                        description=memory_description,
                        emotional_intensity=emotional_intensity,
                        importance=importance,
                        participants=[],
                        location=(agent.location.x if hasattr(agent, 'location') and hasattr(agent.location, 'x') else 0,
                                 agent.location.y if hasattr(agent, 'location') and hasattr(agent.location, 'y') else 0)
                    )

                    # Learn procedural memory: "avoid this action when X"
                    risk_factor = f"risk_{action}"
                    current_risk = agent.memory.procedural_memory.get(risk_factor, 0.5)
                    # Increase perceived risk based on severity
                    agent.memory.procedural_memory[risk_factor] = min(1.0, current_risk + severity * 0.3)

                    # Store semantic knowledge
                    agent.memory.learn_fact(
                        f"{action}_is_dangerous",
                        f"I learned that {action} can lead to {consequence.consequence_type} (severity: {severity:.1f})"
                    )

            # Emotional trauma from severe consequences
            if severity > 0.7 and hasattr(agent, 'emotions'):
                from engine.psychology import EmotionType
                agent.emotions.trigger_emotion(EmotionType.FEAR, severity)
                if consequence.consequence_type in ['death', 'explosion', 'injury']:
                    agent.emotions.trigger_emotion(EmotionType.SADNESS, severity * 0.8)

            # Skill degradation from trauma (makes agent more cautious)
            if severity > 0.6 and hasattr(agent, 'skills'):
                skill_name = f"{action}_skill"
                if hasattr(agent.skills, 'skills') and skill_name in agent.skills.skills:
                    # Trauma makes agent hesitant - reduce skill temporarily
                    current_skill = agent.skills.skills[skill_name].level
                    agent.skills.skills[skill_name].level = max(0.0, current_skill - severity * 0.1)

            # Log the learning
            print(f"💡 {agent.name} learned from {consequence.consequence_type}: "
                  f"Will be more careful with {action} (risk perception: +{severity*30:.0f}%)")

    def _create_memorable_description(
        self,
        consequence_type: str,
        action: str,
        severity: float,
        agent_name: str
    ) -> str:
        """Create vivid, memorable description for agent memory"""

        severity_words = {
            (0.0, 0.3): "minor incident",
            (0.3, 0.6): "serious problem",
            (0.6, 0.8): "terrible disaster",
            (0.8, 1.0): "catastrophic failure"
        }

        severity_label = next(
            (label for (low, high), label in severity_words.items() if low <= severity < high),
            "incident"
        )

        descriptions = {
            "explosion": f"EXPLOSION during {action}! A {severity_label} that I'll never forget. I was lucky to survive.",
            "fire": f"FIRE broke out during {action}. {severity_label.capitalize()} - I barely escaped!",
            "injury": f"I was INJURED badly while {action}. {severity_label.capitalize()} that taught me to be more careful.",
            "building_collapse": f"The building COLLAPSED during {action}! {severity_label.capitalize()} - everything was destroyed.",
            "death": f"Someone DIED during {action}. Absolutely tragic. I must be more careful.",
            "bankruptcy": f"FINANCIAL RUIN from {action}. {severity_label.capitalize()} - I lost everything.",
            "illness": f"I became SICK from {action}. {severity_label.capitalize()} that weakened me severely.",
        }

        return descriptions.get(
            consequence_type,
            f"Bad outcome from {action}: {consequence_type} ({severity_label})"
        )
