"""
Social System - Relationships, groups, and social dynamics

Handles:
- Agent relationships (friendship, romance, rivalry)
- Group formation and dynamics
- Social networks
- Cultural emergence
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
from datetime import datetime


class RelationshipType(Enum):
    """Types of relationships"""
    FRIENDSHIP = "friendship"
    ROMANCE = "romance"
    FAMILY = "family"
    RIVALRY = "rivalry"
    BUSINESS = "business"
    MENTOR_APPRENTICE = "mentor_apprentice"


@dataclass
class Relationship:
    """Relationship between two agents"""
    id: str
    agent_a: str  # Agent ID
    agent_b: str  # Agent ID
    relationship_type: RelationshipType
    strength: float = 0.5  # 0-1
    trust: float = 0.5  # 0-1
    history: List[Dict] = field(default_factory=list)
    formed_at: datetime = field(default_factory=datetime.now)

    def update_strength(self, delta: float):
        """Modify relationship strength"""
        self.strength = max(0.0, min(1.0, self.strength + delta))

        # Relationships can end if strength too low
        if self.strength < 0.1:
            return "ended"

        return "active"

    def add_interaction(self, interaction_type: str, outcome: str):
        """Record an interaction"""
        self.history.append({
            'timestamp': datetime.now(),
            'type': interaction_type,
            'outcome': outcome
        })

        # Recent interactions matter more
        if len(self.history) > 50:
            self.history = self.history[-50:]

    def get_relationship_quality(self) -> str:
        """Describe relationship quality"""
        if self.strength > 0.8:
            return "very_strong"
        elif self.strength > 0.6:
            return "strong"
        elif self.strength > 0.4:
            return "moderate"
        elif self.strength > 0.2:
            return "weak"
        else:
            return "very_weak"


class RelationshipManager:
    """Manages all relationships in the world"""

    def __init__(self):
        self.relationships: Dict[str, Relationship] = {}
        # Index for quick lookups
        self.agent_relationships: Dict[str, Set[str]] = {}

    def create_relationship(
        self,
        agent_a_id: str,
        agent_b_id: str,
        relationship_type: RelationshipType,
        initial_strength: float = 0.5
    ) -> Relationship:
        """Create new relationship"""
        # Check if already exists
        existing = self.get_relationship(agent_a_id, agent_b_id)
        if existing:
            return existing

        rel_id = str(uuid.uuid4())
        relationship = Relationship(
            id=rel_id,
            agent_a=agent_a_id,
            agent_b=agent_b_id,
            relationship_type=relationship_type,
            strength=initial_strength
        )

        self.relationships[rel_id] = relationship

        # Update index
        if agent_a_id not in self.agent_relationships:
            self.agent_relationships[agent_a_id] = set()
        if agent_b_id not in self.agent_relationships:
            self.agent_relationships[agent_b_id] = set()

        self.agent_relationships[agent_a_id].add(rel_id)
        self.agent_relationships[agent_b_id].add(rel_id)

        return relationship

    def get_relationship(
        self,
        agent_a_id: str,
        agent_b_id: str
    ) -> Optional[Relationship]:
        """Get relationship between two agents"""
        agent_rels = self.agent_relationships.get(agent_a_id, set())

        for rel_id in agent_rels:
            rel = self.relationships.get(rel_id)
            if rel and (
                (rel.agent_a == agent_a_id and rel.agent_b == agent_b_id) or
                (rel.agent_a == agent_b_id and rel.agent_b == agent_a_id)
            ):
                return rel

        return None

    def get_agent_relationships(
        self,
        agent_id: str,
        relationship_type: Optional[RelationshipType] = None
    ) -> List[Relationship]:
        """Get all relationships for an agent"""
        rel_ids = self.agent_relationships.get(agent_id, set())
        relationships = [self.relationships[rid] for rid in rel_ids
                        if rid in self.relationships]

        if relationship_type:
            relationships = [r for r in relationships
                           if r.relationship_type == relationship_type]

        return relationships

    def update_relationship(
        self,
        agent_a_id: str,
        agent_b_id: str,
        interaction_type: str,
        positive: bool
    ):
        """Update relationship based on interaction"""
        rel = self.get_relationship(agent_a_id, agent_b_id)

        if not rel:
            # Create new relationship based on interaction
            if positive:
                rel_type = RelationshipType.FRIENDSHIP
                initial_strength = 0.3
            else:
                rel_type = RelationshipType.RIVALRY
                initial_strength = 0.2

            rel = self.create_relationship(
                agent_a_id, agent_b_id, rel_type, initial_strength
            )

        # Update strength
        delta = 0.1 if positive else -0.1
        status = rel.update_strength(delta)

        # Record interaction
        outcome = "positive" if positive else "negative"
        rel.add_interaction(interaction_type, outcome)

        # Remove if ended
        if status == "ended":
            self.relationships.pop(rel.id, None)

    def get_social_network(self, agent_id: str, depth: int = 2) -> Set[str]:
        """Get agent's social network (friends of friends)"""
        network = {agent_id}
        current_layer = {agent_id}

        for _ in range(depth):
            next_layer = set()
            for agent in current_layer:
                rels = self.get_agent_relationships(agent)
                for rel in rels:
                    other_id = rel.agent_b if rel.agent_a == agent else rel.agent_a
                    if other_id not in network:
                        next_layer.add(other_id)
                        network.add(other_id)
            current_layer = next_layer

        return network


@dataclass
class Group:
    """A social group or faction"""
    id: str
    name: str
    leader_id: Optional[str] = None
    members: Set[str] = field(default_factory=set)
    founded_at: datetime = field(default_factory=datetime.now)

    # Group properties
    cohesion: float = 0.5  # How unified the group is
    status: float = 0.5  # Social standing
    wealth: float = 0.0  # Collective resources

    # Culture
    values: Dict[str, float] = field(default_factory=dict)
    traditions: List[str] = field(default_factory=list)

    def add_member(self, agent_id: str):
        """Add member to group"""
        self.members.add(agent_id)

    def remove_member(self, agent_id: str):
        """Remove member from group"""
        self.members.discard(agent_id)

        # If leader leaves, find new leader
        if self.leader_id == agent_id:
            self.leader_id = None
            if self.members:
                # Randomly select new leader (could be based on status)
                import random
                self.leader_id = random.choice(list(self.members))

    def is_member(self, agent_id: str) -> bool:
        """Check if agent is member"""
        return agent_id in self.members

    def update_cohesion(self, delta: float):
        """Update group cohesion"""
        self.cohesion = max(0.0, min(1.0, self.cohesion + delta))

        # Groups can dissolve if cohesion too low
        if self.cohesion < 0.2 and len(self.members) < 3:
            return "dissolved"

        return "active"


class GroupManager:
    """Manages all groups in the world"""

    def __init__(self):
        self.groups: Dict[str, Group] = {}
        # Index: agent -> groups they're in
        self.agent_groups: Dict[str, Set[str]] = {}

    def create_group(
        self,
        name: str,
        founder_id: str
    ) -> Group:
        """Create new group"""
        group_id = str(uuid.uuid4())
        group = Group(
            id=group_id,
            name=name,
            leader_id=founder_id,
            members={founder_id}
        )

        self.groups[group_id] = group

        # Update index
        if founder_id not in self.agent_groups:
            self.agent_groups[founder_id] = set()
        self.agent_groups[founder_id].add(group_id)

        return group

    def add_agent_to_group(self, agent_id: str, group_id: str):
        """Add agent to group"""
        if group_id in self.groups:
            self.groups[group_id].add_member(agent_id)

            if agent_id not in self.agent_groups:
                self.agent_groups[agent_id] = set()
            self.agent_groups[agent_id].add(group_id)

    def remove_agent_from_group(self, agent_id: str, group_id: str):
        """Remove agent from group"""
        if group_id in self.groups:
            self.groups[group_id].remove_member(agent_id)

            if agent_id in self.agent_groups:
                self.agent_groups[agent_id].discard(group_id)

            # Dissolve if no members
            if len(self.groups[group_id].members) == 0:
                self.groups.pop(group_id)

    def get_agent_groups(self, agent_id: str) -> List[Group]:
        """Get all groups agent belongs to"""
        group_ids = self.agent_groups.get(agent_id, set())
        return [self.groups[gid] for gid in group_ids if gid in self.groups]

    def find_groups_near(
        self,
        agent_id: str,
        relationship_manager: RelationshipManager
    ) -> List[Group]:
        """Find groups agent might want to join (based on social network)"""
        # Get agent's friends
        friendships = relationship_manager.get_agent_relationships(
            agent_id,
            RelationshipType.FRIENDSHIP
        )

        potential_groups = set()
        for friendship in friendships:
            friend_id = (friendship.agent_b if friendship.agent_a == agent_id
                        else friendship.agent_a)
            friend_groups = self.get_agent_groups(friend_id)
            potential_groups.update(friend_groups)

        return list(potential_groups)
