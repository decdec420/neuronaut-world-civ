"""
Comprehensive Agent Profile System

Detailed profiles for every agent including:
- Full psychology breakdown
- Complete relationship network
- Life history and achievements
- Skills and specializations
- Possessions and wealth
- Political influence
- Combat record
- Innovations and discoveries
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentProfile:
    """Complete profile for an agent"""

    # BASIC INFO
    agent_id: str
    name: str
    age: int
    gender: str
    is_player: bool

    # VITAL STATS
    health: float
    energy: float
    alive: bool
    ticks_lived: int
    created_at: datetime

    # LOCATION
    location: Dict[str, float]
    current_action: Optional[str]

    # PSYCHOLOGY
    needs: Dict[str, float]  # All needs with urgency
    personality: Dict[str, float]  # All personality traits
    emotions: Dict[str, float]  # Current emotional state
    mood: float  # Overall mood
    stress: float
    life_satisfaction: float

    # SKILLS & EXPERTISE
    skills: Dict[str, float]  # All skills with levels
    top_skills: List[Dict[str, float]]  # Top 5 skills
    specializations: List[str]  # What they focus on

    # ECONOMIC
    wealth: float
    net_worth: float  # Including property
    inventory: Dict[str, int]
    inventory_value: float
    properties_owned: List[Dict]

    # SOCIAL
    status: float  # Social standing
    relationships: List[Dict]  # All relationships with details
    close_friends: List[str]  # Best friends
    romantic_partners: List[str]
    rivals: List[str]
    group_memberships: List[Dict]  # Groups they belong to
    social_network_size: int  # Total connections

    # POLITICAL
    government_affiliation: Optional[Dict]
    political_power: float
    laws_created: int
    votes_cast: int
    is_leader: bool
    is_council_member: bool

    # MILITARY
    combat_stats: Dict[str, float]
    equipment: Dict[str, str]  # Weapons/armor equipped
    battles_fought: int
    battles_won: int
    kills: int
    times_wounded: int

    # ACHIEVEMENTS & HISTORY
    innovations_discovered: List[Dict]
    buildings_built: List[Dict]
    major_accomplishments: List[str]
    life_events: List[Dict]  # Recent significant events

    # PRODUCTION & TRADE
    items_crafted: int
    specialization_recipes: List[str]
    trades_completed: int
    total_trade_volume: float

    # METRICS
    days_survived: int
    happiness_score: float  # 0-100
    success_rating: float  # Overall success metric
    influence_score: float  # How influential they are

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            # Basic
            'id': self.agent_id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'is_player': self.is_player,

            # Vitals
            'health': self.health,
            'energy': self.energy,
            'alive': self.alive,
            'ticks_lived': self.ticks_lived,
            'days_survived': self.days_survived,

            # Location
            'location': self.location,
            'current_action': self.current_action,

            # Psychology
            'psychology': {
                'needs': self.needs,
                'personality': self.personality,
                'emotions': self.emotions,
                'mood': self.mood,
                'stress': self.stress,
                'life_satisfaction': self.life_satisfaction,
            },

            # Skills
            'skills': {
                'all_skills': self.skills,
                'top_skills': self.top_skills,
                'specializations': self.specializations,
            },

            # Economic
            'economics': {
                'wealth': self.wealth,
                'net_worth': self.net_worth,
                'inventory': self.inventory,
                'inventory_value': self.inventory_value,
                'properties': self.properties_owned,
            },

            # Social
            'social': {
                'status': self.status,
                'relationships': self.relationships,
                'close_friends': self.close_friends,
                'romantic_partners': self.romantic_partners,
                'rivals': self.rivals,
                'groups': self.group_memberships,
                'network_size': self.social_network_size,
            },

            # Political
            'political': {
                'government': self.government_affiliation,
                'power': self.political_power,
                'laws_created': self.laws_created,
                'votes_cast': self.votes_cast,
                'is_leader': self.is_leader,
                'is_council_member': self.is_council_member,
            },

            # Military
            'military': {
                'stats': self.combat_stats,
                'equipment': self.equipment,
                'battles_fought': self.battles_fought,
                'battles_won': self.battles_won,
                'kills': self.kills,
                'times_wounded': self.times_wounded,
            },

            # Achievements
            'achievements': {
                'innovations': self.innovations_discovered,
                'buildings': self.buildings_built,
                'accomplishments': self.major_accomplishments,
                'recent_events': self.life_events,
            },

            # Production
            'production': {
                'items_crafted': self.items_crafted,
                'specializations': self.specialization_recipes,
                'trades_completed': self.trades_completed,
                'trade_volume': self.total_trade_volume,
            },

            # Metrics
            'metrics': {
                'happiness': self.happiness_score,
                'success': self.success_rating,
                'influence': self.influence_score,
            }
        }


class ProfileBuilder:
    """Builds comprehensive profiles for agents"""

    def __init__(
        self,
        simulation_engine: 'SimulationEngine'
    ):
        self.simulation = simulation_engine

    def _safe_float(self, value: float, default: float = 0.0) -> float:
        """
        Ensure float value is not NaN or infinity.
        Returns default value if invalid.
        """
        import math
        if value is None or math.isnan(value) or math.isinf(value):
            return default
        return float(value)

    def build_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """Build complete profile for an agent"""
        # Get agent
        agent = self.simulation._get_agent_by_id(agent_id)
        if not agent:
            return None

        # Gather all data
        profile = AgentProfile(
            agent_id=agent.id,
            name=agent.name,
            age=agent.age,
            gender=agent.gender.value,
            is_player=agent.is_player,

            # Vitals
            health=self._safe_float(agent.health, 100.0),
            energy=self._safe_float(agent.energy, 100.0),
            alive=agent.alive,
            ticks_lived=agent.ticks_lived,
            created_at=agent.created_at,
            days_survived=agent.ticks_lived // 144,  # Assuming 144 ticks/day

            # Location
            location={'x': agent.location.x, 'y': agent.location.y},
            current_action=agent.current_action.action_type.value if agent.current_action else None,

            # Psychology
            needs=self._get_needs_data(agent),
            personality=self._get_personality_data(agent),
            emotions=self._get_emotions_data(agent),
            mood=self._safe_float(agent.emotions.mood, 0.0),
            stress=self._safe_float(agent.emotions.stress, 0.2),
            life_satisfaction=self._safe_float(agent.needs.get_overall_satisfaction(), 0.5),

            # Skills
            skills={name: skill.level for name, skill in agent.skills.skills.items()},
            top_skills=[
                {'name': name, 'level': level}
                for name, level in agent.skills.get_top_skills(5)
            ],
            specializations=self._get_specializations(agent),

            # Economic
            wealth=agent.wealth,
            net_worth=self._get_net_worth(agent),
            inventory=dict(agent.inventory.items),
            inventory_value=agent.inventory.get_value(),
            properties_owned=self._get_properties(agent),

            # Social
            status=agent.status,
            relationships=self._get_relationships(agent),
            close_friends=self._get_close_friends(agent),
            romantic_partners=self._get_romantic_partners(agent),
            rivals=self._get_rivals(agent),
            group_memberships=self._get_groups(agent),
            social_network_size=self._get_network_size(agent),

            # Political
            government_affiliation=self._get_government(agent),
            political_power=self._get_political_power(agent),
            laws_created=self._get_laws_created(agent),
            votes_cast=0,  # TODO: Track this
            is_leader=self._is_leader(agent),
            is_council_member=self._is_council_member(agent),

            # Military
            combat_stats=self._get_combat_stats(agent),
            equipment=self._get_equipment(agent),
            battles_fought=self._get_battles_fought(agent),
            battles_won=self._get_battles_won(agent),
            kills=0,  # TODO: Track this
            times_wounded=0,  # TODO: Track this

            # Achievements
            innovations_discovered=self._get_innovations(agent),
            buildings_built=self._get_buildings(agent),
            major_accomplishments=self._get_accomplishments(agent),
            life_events=self._get_recent_events(agent),

            # Production
            items_crafted=0,  # TODO: Track this
            specialization_recipes=self._get_recipe_specializations(agent),
            trades_completed=self._get_trades_completed(agent),
            total_trade_volume=0.0,  # TODO: Track this

            # Metrics
            happiness_score=self._calculate_happiness(agent),
            success_rating=self._calculate_success(agent),
            influence_score=self._calculate_influence(agent),
        )

        return profile

    def _get_needs_data(self, agent) -> Dict[str, float]:
        """
        Get all needs with LEVEL (not urgency) for consistency with World View.

        IMPORTANT: This returns the raw need level (0=satisfied, 1=desperate)
        to match what agent.to_dict() returns, ensuring consistency between
        World View cards and Detail View.
        """
        return {
            need.value: need_obj.level
            for need, need_obj in agent.needs.needs.items()
        }

    def _get_personality_data(self, agent) -> Dict[str, float]:
        """Get all personality traits"""
        return {
            'openness': agent.personality.openness,
            'conscientiousness': agent.personality.conscientiousness,
            'extraversion': agent.personality.extraversion,
            'agreeableness': agent.personality.agreeableness,
            'neuroticism': agent.personality.neuroticism,
            'risk_taking': agent.personality.risk_taking,
            'aggression': agent.personality.aggression,
            'sexuality': agent.personality.sexuality,
            'ambition': agent.personality.ambition,
            'creativity': agent.personality.creativity,
            'empathy': agent.personality.empathy,
            'rationality': agent.personality.rationality,
        }

    def _get_emotions_data(self, agent) -> Dict[str, float]:
        """Get current emotional state"""
        return {
            emotion.value: emotion_obj.intensity
            for emotion, emotion_obj in agent.emotions.emotions.items()
        }

    def _get_specializations(self, agent) -> List[str]:
        """Get what agent specializes in"""
        # Check production manager if available
        specs = []
        # TODO: Get from production manager
        return specs

    def _get_net_worth(self, agent) -> float:
        """Calculate total net worth"""
        return self.simulation.economy.property_manager.get_agent_net_worth(
            agent.id, agent.wealth
        )

    def _get_properties(self, agent) -> List[Dict]:
        """Get owned properties"""
        props = self.simulation.economy.property_manager.get_agent_properties(agent.id)
        return [
            {
                'type': p.property_type,
                'location': p.location,
                'value': p.value,
            }
            for p in props
        ]

    def _get_relationships(self, agent) -> List[Dict]:
        """Get all relationships"""
        rels = self.simulation.relationship_manager.get_agent_relationships(agent.id)
        return [
            {
                'type': r.relationship_type.value,
                'with_id': r.agent_b if r.agent_a == agent.id else r.agent_a,
                'with_name': self._get_agent_name(r.agent_b if r.agent_a == agent.id else r.agent_a),
                'strength': r.strength,
                'trust': r.trust,
            }
            for r in rels
        ]

    def _get_close_friends(self, agent) -> List[str]:
        """Get best friends"""
        from social.relationships import RelationshipType
        friends = self.simulation.relationship_manager.get_agent_relationships(
            agent.id, RelationshipType.FRIENDSHIP
        )
        # Sort by strength
        friends.sort(key=lambda r: r.strength, reverse=True)
        return [
            r.agent_b if r.agent_a == agent.id else r.agent_a
            for r in friends[:5]
            if r.strength > 0.6
        ]

    def _get_romantic_partners(self, agent) -> List[str]:
        """Get romantic partners"""
        from social.relationships import RelationshipType
        romances = self.simulation.relationship_manager.get_agent_relationships(
            agent.id, RelationshipType.ROMANCE
        )
        return [
            r.agent_b if r.agent_a == agent.id else r.agent_a
            for r in romances
            if r.strength > 0.5
        ]

    def _get_rivals(self, agent) -> List[str]:
        """Get rivals"""
        from social.relationships import RelationshipType
        rivalries = self.simulation.relationship_manager.get_agent_relationships(
            agent.id, RelationshipType.RIVALRY
        )
        return [
            r.agent_b if r.agent_a == agent.id else r.agent_a
            for r in rivalries
        ]

    def _get_groups(self, agent) -> List[Dict]:
        """Get group memberships"""
        groups = self.simulation.group_manager.get_agent_groups(agent.id)
        return [
            {
                'id': g.id,
                'name': g.name,
                'is_leader': g.leader_id == agent.id,
                'members_count': len(g.members),
            }
            for g in groups
        ]

    def _get_network_size(self, agent) -> int:
        """Get size of social network"""
        network = self.simulation.relationship_manager.get_social_network(agent.id, depth=2)
        return len(network)

    def _get_government(self, agent) -> Optional[Dict]:
        """Get government affiliation"""
        # TODO: Implement when governance manager is integrated
        return None

    def _get_political_power(self, agent) -> float:
        """Get political influence"""
        # TODO: Get from governance manager
        return 0.0

    def _get_laws_created(self, agent) -> int:
        """Get number of laws created"""
        # TODO: Get from governance manager
        return 0

    def _is_leader(self, agent) -> bool:
        """Check if agent is a leader"""
        # TODO: Check governance manager
        return False

    def _is_council_member(self, agent) -> bool:
        """Check if agent is council member"""
        # TODO: Check governance manager
        return False

    def _get_combat_stats(self, agent) -> Dict[str, float]:
        """Get combat statistics"""
        # TODO: Get from warfare manager
        return {
            'strength': 0.5,
            'skill': agent.skills.get_skill('combat'),
            'morale': 1.0,
        }

    def _get_equipment(self, agent) -> Dict[str, str]:
        """Get equipped items"""
        # TODO: Get from warfare manager
        return {}

    def _get_battles_fought(self, agent) -> int:
        """Get number of battles"""
        # TODO: Track in warfare manager
        return 0

    def _get_battles_won(self, agent) -> int:
        """Get battles won"""
        # TODO: Track in warfare manager
        return 0

    def _get_innovations(self, agent) -> List[Dict]:
        """Get innovations discovered"""
        # TODO: Get from innovation manager
        return []

    def _get_buildings(self, agent) -> List[Dict]:
        """Get buildings built"""
        # TODO: Get from building manager
        return []

    def _get_accomplishments(self, agent) -> List[str]:
        """Get major accomplishments"""
        accomplishments = []

        # High wealth
        if agent.wealth > 1000:
            accomplishments.append("Wealthy Merchant")

        # Many friends
        friends = len(self._get_close_friends(agent))
        if friends > 5:
            accomplishments.append("Popular")

        # High skills
        top_skill = max(agent.skills.skills.values(), key=lambda s: s.level, default=None)
        if top_skill and top_skill.level > 0.8:
            accomplishments.append(f"Master {top_skill.name}")

        return accomplishments

    def _get_recent_events(self, agent) -> List[Dict]:
        """Get recent significant events"""
        events = self.simulation.event_logger.get_events_involving_agent(agent.id, 10)
        return [
            {
                'title': e.title,
                'description': e.description,
                'timestamp': e.timestamp.isoformat(),
                'importance': e.importance.value,
            }
            for e in events
        ]

    def _get_recipe_specializations(self, agent) -> List[str]:
        """Get crafting specializations"""
        # TODO: Get from production manager
        return []

    def _get_trades_completed(self, agent) -> int:
        """Get number of trades"""
        # TODO: Track in economy manager
        return 0

    def _calculate_happiness(self, agent) -> float:
        """Calculate happiness score 0-100"""
        satisfaction = agent.needs.get_overall_satisfaction()
        mood = (agent.emotions.mood + 1.0) / 2.0  # Convert -1..1 to 0..1
        stress_factor = 1.0 - agent.emotions.stress

        happiness = (satisfaction * 0.5 + mood * 0.3 + stress_factor * 0.2) * 100
        return happiness

    def _calculate_success(self, agent) -> float:
        """Calculate overall success rating 0-100"""
        # Economic success
        wealth_score = min(100, agent.wealth / 10)  # Cap at 1000 wealth

        # Social success
        social_score = agent.status * 100

        # Skill mastery
        avg_skill = sum(s.level for s in agent.skills.skills.values()) / max(1, len(agent.skills.skills))
        skill_score = avg_skill * 100

        # Combine
        success = (wealth_score * 0.4 + social_score * 0.3 + skill_score * 0.3)
        return success

    def _calculate_influence(self, agent) -> float:
        """Calculate influence score 0-100"""
        # Social influence (network size + status)
        network_score = min(50, self._get_network_size(agent))
        status_score = agent.status * 50

        influence = network_score + status_score
        return influence

    def _get_agent_name(self, agent_id: str) -> str:
        """Get agent name by ID"""
        agent = self.simulation._get_agent_by_id(agent_id)
        return agent.name if agent else "Unknown"
