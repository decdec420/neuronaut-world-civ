"""
Innovation and Discovery System - TRUE Agent Autonomy

Instead of fixed tech trees, agents:
- Discover things through experimentation
- Invent new items based on needs
- Learn from success/failure
- Share knowledge with others
- Create their own "technologies"

Agents decide WHAT to build, WHEN to build it, and HOW based on their psychology and needs.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum


class DiscoveryType(Enum):
    """Types of things agents can discover"""
    ITEM = "item"  # New craftable item
    TECHNIQUE = "technique"  # Better way to do something
    RECIPE = "recipe"  # Combination of items
    METHOD = "method"  # New approach to a task
    CONCEPT = "concept"  # Abstract idea


@dataclass
class Innovation:
    """Something an agent has discovered or invented"""
    id: str
    name: str
    discovery_type: DiscoveryType
    description: str

    # Who discovered it
    discoverer_id: str
    discovered_at: datetime = field(default_factory=datetime.now)

    # What it does
    effect_description: str = ""
    efficiency_bonus: float = 0.0  # 0-1, improves related actions

    # How to use it
    requires_items: List[str] = field(default_factory=list)
    produces_items: List[str] = field(default_factory=list)
    applies_to_actions: List[str] = field(default_factory=list)

    # Knowledge spread
    known_by: Set[str] = field(default_factory=set)  # Agent IDs
    times_used: int = 0
    success_rate: float = 1.0  # How often it works

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'type': self.discovery_type.value,
            'description': self.description,
            'discoverer_id': self.discoverer_id,
            'discovered_at': self.discovered_at.isoformat(),
            'efficiency_bonus': self.efficiency_bonus,
            'known_by_count': len(self.known_by),
            'times_used': self.times_used,
            'success_rate': self.success_rate,
        }


@dataclass
class BuildingConcept:
    """An agent's idea for a building - they INVENT buildings"""
    id: str
    name: str
    creator_id: str
    created_at: datetime = field(default_factory=datetime.now)

    # What the agent thinks they need to build it
    estimated_wood: int = 0
    estimated_stone: int = 0
    estimated_metal: int = 0
    estimated_labor: int = 10

    # What the agent hopes it will do
    intended_purpose: str = "shelter"  # shelter, production, defense, social, etc.

    # Has it been built?
    successfully_built: bool = False
    times_attempted: int = 0
    times_succeeded: int = 0

    # What it actually does (learned through use)
    actual_benefits: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'creator_id': self.creator_id,
            'purpose': self.intended_purpose,
            'materials': {
                'wood': self.estimated_wood,
                'stone': self.estimated_stone,
                'metal': self.estimated_metal,
            },
            'times_built': self.times_succeeded,
            'success_rate': self.times_succeeded / max(1, self.times_attempted),
        }


class InnovationManager:
    """Manages discoveries and agent inventions"""

    def __init__(self):
        # All innovations discovered
        self.innovations: Dict[str, Innovation] = {}

        # Building concepts agents have invented
        self.building_concepts: Dict[str, BuildingConcept] = {}

        # Agent knowledge (what each agent knows)
        self.agent_knowledge: Dict[str, Set[str]] = {}  # agent_id -> set of innovation IDs

        # Experimentation results (agents learn from trying things)
        self.experiment_log: List[Dict] = []

    def agent_discovers(
        self,
        agent_id: str,
        agent_name: str,
        discovery_type: DiscoveryType,
        context: Dict
    ) -> Optional[Innovation]:
        """
        Agent makes a discovery through experimentation

        This happens naturally when agents try things:
        - Combining items
        - Trying new approaches
        - Solving problems creatively
        """
        # Generate innovation based on context
        innovation_id = str(uuid.uuid4())

        # Let the agent NAME their discovery
        name = self._generate_innovation_name(agent_name, discovery_type, context)

        innovation = Innovation(
            id=innovation_id,
            name=name,
            discovery_type=discovery_type,
            description=f"Discovered by {agent_name}",
            discoverer_id=agent_id,
            known_by={agent_id}
        )

        # Determine effects based on what agent was trying to do
        if 'action' in context:
            innovation.applies_to_actions = [context['action']]
            innovation.efficiency_bonus = 0.1  # Small improvement

        if 'items_used' in context:
            innovation.requires_items = context['items_used']

        if 'result' in context:
            innovation.produces_items = [context['result']]

        self.innovations[innovation_id] = innovation

        # Agent learns it
        self.learn_innovation(agent_id, innovation_id)

        return innovation

    def _generate_innovation_name(
        self,
        agent_name: str,
        discovery_type: DiscoveryType,
        context: Dict
    ) -> str:
        """Generate a name for the innovation"""
        prefixes = {
            DiscoveryType.ITEM: ["Tool", "Device", "Creation"],
            DiscoveryType.TECHNIQUE: ["Method", "Way", "Technique"],
            DiscoveryType.RECIPE: ["Recipe", "Formula", "Combination"],
            DiscoveryType.METHOD: ["Approach", "Process", "System"],
            DiscoveryType.CONCEPT: ["Idea", "Concept", "Theory"],
        }

        import random
        prefix = random.choice(prefixes.get(discovery_type, ["Discovery"]))

        # Sometimes name after inventor
        if random.random() < 0.3:
            return f"{agent_name}'s {prefix}"
        else:
            return f"{prefix} {random.randint(1, 999)}"

    def agent_invents_building(
        self,
        agent_id: str,
        agent_name: str,
        purpose: str,
        available_materials: Dict[str, int]
    ) -> BuildingConcept:
        """
        Agent INVENTS a new type of building based on their needs

        They estimate what materials they need and what it should do
        """
        concept_id = str(uuid.uuid4())

        # Agent makes educated guesses about materials needed
        import random

        # More materials = bigger/better building
        wood = min(available_materials.get('wood', 0), random.randint(10, 100))
        stone = min(available_materials.get('stone', 0), random.randint(5, 80))
        metal = min(available_materials.get('metal', 0), random.randint(0, 30))

        # Name it
        purposes = {
            'shelter': ['House', 'Home', 'Dwelling', 'Hut'],
            'production': ['Workshop', 'Factory', 'Mill', 'Shop'],
            'defense': ['Fort', 'Wall', 'Tower', 'Bastion'],
            'social': ['Hall', 'Gathering Place', 'Center', 'Plaza'],
            'storage': ['Warehouse', 'Storage', 'Vault', 'Depot'],
        }

        import random
        base_names = purposes.get(purpose, ['Building'])
        name = f"{random.choice(base_names)} (by {agent_name})"

        concept = BuildingConcept(
            id=concept_id,
            name=name,
            creator_id=agent_id,
            estimated_wood=wood,
            estimated_stone=stone,
            estimated_metal=metal,
            estimated_labor=int((wood + stone + metal) / 5),
            intended_purpose=purpose
        )

        self.building_concepts[concept_id] = concept

        return concept

    def learn_innovation(self, agent_id: str, innovation_id: str):
        """Agent learns about an innovation (from discovery or teaching)"""
        if agent_id not in self.agent_knowledge:
            self.agent_knowledge[agent_id] = set()

        self.agent_knowledge[agent_id].add(innovation_id)

        if innovation_id in self.innovations:
            self.innovations[innovation_id].known_by.add(agent_id)

    def teach_innovation(
        self,
        teacher_id: str,
        student_id: str,
        innovation_id: str
    ) -> bool:
        """One agent teaches another"""
        # Teacher must know it
        if innovation_id not in self.agent_knowledge.get(teacher_id, set()):
            return False

        # Student learns it
        self.learn_innovation(student_id, innovation_id)

        return True

    def agent_knows(self, agent_id: str, innovation_id: str) -> bool:
        """Check if agent knows an innovation"""
        return innovation_id in self.agent_knowledge.get(agent_id, set())

    def get_agent_innovations(self, agent_id: str) -> List[Innovation]:
        """Get all innovations an agent knows"""
        known_ids = self.agent_knowledge.get(agent_id, set())
        return [self.innovations[iid] for iid in known_ids if iid in self.innovations]

    def use_innovation(
        self,
        agent_id: str,
        innovation_id: str,
        success: bool
    ):
        """Track usage of an innovation"""
        if innovation_id not in self.innovations:
            return

        innovation = self.innovations[innovation_id]
        innovation.times_used += 1

        # Update success rate
        if innovation.times_used == 1:
            innovation.success_rate = 1.0 if success else 0.0
        else:
            # Running average
            innovation.success_rate = (
                innovation.success_rate * 0.9 + (1.0 if success else 0.0) * 0.1
            )

        # If innovation keeps failing, reduce its bonuses
        if innovation.success_rate < 0.3:
            innovation.efficiency_bonus *= 0.5

    def record_experiment(
        self,
        agent_id: str,
        action: str,
        items_used: List[str],
        outcome: str,
        success: bool
    ):
        """Record an agent's experiment"""
        self.experiment_log.append({
            'timestamp': datetime.now(),
            'agent_id': agent_id,
            'action': action,
            'items_used': items_used,
            'outcome': outcome,
            'success': success,
        })

        # Keep last 1000 experiments
        if len(self.experiment_log) > 1000:
            self.experiment_log = self.experiment_log[-1000:]

    def get_building_concepts(self, purpose: Optional[str] = None) -> List[BuildingConcept]:
        """Get building concepts, optionally filtered by purpose"""
        concepts = list(self.building_concepts.values())

        if purpose:
            concepts = [c for c in concepts if c.intended_purpose == purpose]

        # Sort by success rate
        concepts.sort(key=lambda c: c.times_succeeded / max(1, c.times_attempted), reverse=True)

        return concepts

    def building_attempt(self, concept_id: str, success: bool):
        """Record a building attempt"""
        if concept_id not in self.building_concepts:
            return

        concept = self.building_concepts[concept_id]
        concept.times_attempted += 1

        if success:
            concept.times_succeeded += 1
            concept.successfully_built = True

    def get_statistics(self) -> Dict:
        """Get innovation statistics"""
        total_innovations = len(self.innovations)
        total_concepts = len(self.building_concepts)

        by_type = {}
        for innovation in self.innovations.values():
            dtype = innovation.discovery_type.value
            by_type[dtype] = by_type.get(dtype, 0) + 1

        # Most widely known innovations
        most_known = sorted(
            self.innovations.values(),
            key=lambda i: len(i.known_by),
            reverse=True
        )[:10]

        return {
            'total_innovations': total_innovations,
            'total_building_concepts': total_concepts,
            'total_experiments': len(self.experiment_log),
            'innovations_by_type': by_type,
            'most_widely_known': [
                {
                    'name': i.name,
                    'known_by': len(i.known_by),
                    'times_used': i.times_used,
                }
                for i in most_known
            ],
        }


# Helper functions for agents to use

def can_agent_experiment(agent_skills: Dict[str, float], action: str) -> bool:
    """
    Check if agent is capable of experimenting with this action

    Agents with higher skills can try more complex experiments
    """
    # Higher creativity and openness = more experimentation
    creativity = agent_skills.get('creativity', 0.5)
    knowledge = agent_skills.get('knowledge', 0.5)

    experiment_threshold = 0.3  # Minimum to try

    return (creativity + knowledge) / 2 > experiment_threshold


def calculate_innovation_chance(
    agent_personality: 'PersonalityProfile',
    agent_skills: Dict[str, float],
    task_difficulty: float
) -> float:
    """
    Calculate chance agent will innovate while doing a task

    High openness + creativity + relevant skills = more innovation
    """
    # Personality factors
    openness = agent_personality.openness
    creativity = agent_personality.creativity
    rationality = agent_personality.rationality

    # Relevant skills
    skill_level = sum(agent_skills.values()) / max(1, len(agent_skills))

    # Innovation chance
    base_chance = (openness + creativity + rationality) / 3
    skill_bonus = skill_level * 0.3
    difficulty_factor = task_difficulty * 0.2  # Harder tasks drive innovation

    innovation_chance = base_chance + skill_bonus + difficulty_factor

    return min(1.0, innovation_chance)
