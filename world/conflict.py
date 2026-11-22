"""
Autonomous Warfare and Conflict System

Agents decide to engage in conflict based on:
- Personality (aggression, ambition)
- Needs (resources, territory, status)
- Relationships (rivalries, grudges)
- Circumstances (desperation, opportunity)

Conflict types:
- Individual duels
- Gang warfare
- Territorial disputes
- Resource wars
- Ideological conflicts
"""

import uuid
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum


class ConflictType(Enum):
    """Types of conflicts"""
    DUEL = "duel"  # 1v1 combat
    SKIRMISH = "skirmish"  # Small group fight
    BATTLE = "battle"  # Large scale combat
    SIEGE = "siege"  # Attack on fortified position
    RAID = "raid"  # Quick attack for resources
    AMBUSH = "ambush"  # Surprise attack


class ConflictReason(Enum):
    """Why agents fight"""
    RESOURCES = "resources"  #争夺资源
    TERRITORY = "territory"  # Land disputes
    REVENGE = "revenge"  # Payback
    HONOR = "honor"  # Pride/status
    IDEOLOGY = "ideology"  # Different beliefs
    SURVIVAL = "survival"  # Desperate need
    OPPORTUNITY = "opportunity"  # Easy target
    DEFENSE = "defense"  # Protecting something


@dataclass
class CombatStats:
    """Agent's combat capabilities"""
    strength: float = 0.5  # Physical power
    skill: float = 0.0  # Combat skill
    equipment_bonus: float = 0.0  # Weapon/armor bonus
    morale: float = 1.0  # Willingness to fight
    fatigue: float = 0.0  # Tiredness (reduces effectiveness)

    def get_combat_power(self) -> float:
        """Calculate overall combat effectiveness"""
        base = (self.strength + self.skill) / 2
        equipment = 1.0 + self.equipment_bonus
        morale_factor = 0.5 + (self.morale * 0.5)
        fatigue_penalty = 1.0 - (self.fatigue * 0.5)

        return base * equipment * morale_factor * fatigue_penalty


@dataclass
class Weapon:
    """Combat equipment"""
    name: str
    damage: float = 1.0  # Damage multiplier
    skill_requirement: float = 0.0  # Minimum skill to use effectively
    durability: float = 100.0  # Degrades with use

    def get_effective_damage(self, user_skill: float) -> float:
        """Calculate effective damage based on user skill"""
        if user_skill < self.skill_requirement:
            # Penalty for unskilled use
            penalty = (self.skill_requirement - user_skill)
            return self.damage * (1.0 - penalty)
        else:
            # Bonus for skilled use
            bonus = (user_skill - self.skill_requirement) * 0.5
            return self.damage * (1.0 + bonus)


@dataclass
class Armor:
    """Protective equipment"""
    name: str
    defense: float = 0.1  # Damage reduction
    mobility_cost: float = 0.0  # Reduces speed
    durability: float = 100.0


@dataclass
class Conflict:
    """An ongoing conflict"""
    id: str
    conflict_type: ConflictType
    reason: ConflictReason
    started_at: datetime = field(default_factory=datetime.now)

    # Participants
    side_a: Set[str] = field(default_factory=set)  # Agent IDs
    side_b: Set[str] = field(default_factory=set)

    # Leaders (if organized)
    leader_a: Optional[str] = None
    leader_b: Optional[str] = None

    # State
    active: bool = True
    turns_elapsed: int = 0

    # Casualties and outcomes
    casualties_a: Set[str] = field(default_factory=set)
    casualties_b: Set[str] = field(default_factory=set)
    winner: Optional[str] = None  # 'side_a' or 'side_b'
    ended_at: Optional[datetime] = None

    # Stakes (what they're fighting over)
    stakes: Dict = field(default_factory=dict)

    def get_size(self) -> Tuple[int, int]:
        """Get number of combatants on each side"""
        return len(self.side_a - self.casualties_a), len(self.side_b - self.casualties_b)

    def is_over(self) -> bool:
        """Check if conflict is over"""
        if not self.active:
            return True

        # No one left on a side
        size_a, size_b = self.get_size()
        return size_a == 0 or size_b == 0

    def resolve_turn(self) -> Dict:
        """Resolve one turn of combat"""
        results = {
            'casualties': [],
            'damages': {},
            'morale_changes': {},
        }

        self.turns_elapsed += 1

        # Combat resolution happens elsewhere
        return results


class WarfareManager:
    """Manages all conflicts in the world"""

    def __init__(self):
        self.active_conflicts: Dict[str, Conflict] = {}
        self.conflict_history: List[Conflict] = []

        # Agent combat stats
        self.combat_stats: Dict[str, CombatStats] = {}

        # Equipment
        self.weapons: Dict[str, Weapon] = {}
        self.armor: Dict[str, Armor] = {}

        # Agent equipment
        self.agent_weapons: Dict[str, str] = {}  # agent_id -> weapon_id
        self.agent_armor: Dict[str, str] = {}  # agent_id -> armor_id

        # Rivalries and grudges (drive conflicts)
        self.grudges: Dict[Tuple[str, str], float] = {}  # (agent_a, agent_b) -> intensity

    def get_combat_stats(self, agent_id: str) -> CombatStats:
        """Get or create combat stats for agent"""
        if agent_id not in self.combat_stats:
            self.combat_stats[agent_id] = CombatStats()
        return self.combat_stats[agent_id]

    def should_agent_fight(
        self,
        agent_id: str,
        target_id: str,
        agent_personality: 'PersonalityProfile',
        agent_needs: 'NeedState',
        context: Dict
    ) -> Tuple[bool, ConflictReason]:
        """
        Determine if agent wants to initiate conflict

        Agents decide based on:
        - Personality (aggression, courage)
        - Needs (desperation)
        - Opportunity (weak target)
        - Relationship (grudges)
        """
        # Personality factors
        aggression = agent_personality.aggression
        ambition = agent_personality.ambition
        risk_taking = agent_personality.risk_taking
        agreeableness = agent_personality.agreeableness  # Low = more likely to fight

        # Needs (desperate agents more likely to fight)
        from engine.psychology import NeedType
        resource_need = agent_needs.needs[NeedType.RESOURCES].get_urgency()
        security_need = agent_needs.needs[NeedType.SECURITY].get_urgency()

        # Grudge
        grudge_intensity = self.get_grudge(agent_id, target_id)

        # Calculate fight likelihood for different reasons
        reasons_scores = {}

        # Resource conflict (if desperate)
        if resource_need > 0.7:
            reasons_scores[ConflictReason.RESOURCES] = (
                resource_need * aggression * (1.0 - agreeableness)
            )

        # Revenge (if grudge exists)
        if grudge_intensity > 0.5:
            reasons_scores[ConflictReason.REVENGE] = (
                grudge_intensity * aggression * ambition
            )

        # Opportunistic attack
        if context.get('target_is_weak', False):
            reasons_scores[ConflictReason.OPPORTUNITY] = (
                aggression * ambition * risk_taking * 0.5
            )

        # Honor/Status
        status_need = agent_needs.needs.get(NeedType.STATUS, None)
        if status_need and status_need.get_urgency() > 0.6:
            reasons_scores[ConflictReason.HONOR] = (
                status_need.get_urgency() * aggression * ambition
            )

        # Find strongest reason
        if not reasons_scores:
            return False, None

        best_reason = max(reasons_scores, key=reasons_scores.get)
        best_score = reasons_scores[best_reason]

        # Threshold (modified by risk-taking)
        threshold = 0.6 * (1.0 - risk_taking * 0.3)

        should_fight = best_score > threshold

        return should_fight, best_reason if should_fight else None

    def initiate_duel(
        self,
        challenger_id: str,
        target_id: str,
        reason: ConflictReason
    ) -> Conflict:
        """Start a 1v1 duel"""
        conflict_id = str(uuid.uuid4())

        conflict = Conflict(
            id=conflict_id,
            conflict_type=ConflictType.DUEL,
            reason=reason,
            side_a={challenger_id},
            side_b={target_id},
            leader_a=challenger_id,
            leader_b=target_id
        )

        self.active_conflicts[conflict_id] = conflict

        return conflict

    def join_conflict(
        self,
        conflict_id: str,
        agent_id: str,
        side: str  # 'side_a' or 'side_b'
    ) -> bool:
        """Agent joins an ongoing conflict"""
        if conflict_id not in self.active_conflicts:
            return False

        conflict = self.active_conflicts[conflict_id]

        if side == 'side_a':
            conflict.side_a.add(agent_id)
        elif side == 'side_b':
            conflict.side_b.add(agent_id)
        else:
            return False

        # Escalate conflict type based on size
        size_a, size_b = conflict.get_size()
        total = size_a + size_b

        if total > 20:
            conflict.conflict_type = ConflictType.BATTLE
        elif total > 5:
            conflict.conflict_type = ConflictType.SKIRMISH

        return True

    def resolve_combat_turn(
        self,
        conflict_id: str,
        agents: Dict[str, 'Agent']  # All agents involved
    ) -> Dict:
        """
        Resolve one turn of combat

        Agents fight based on their stats, equipment, and tactics
        """
        if conflict_id not in self.active_conflicts:
            return {'error': 'Conflict not found'}

        conflict = self.active_conflicts[conflict_id]

        if not conflict.active or conflict.is_over():
            return {'status': 'conflict_over'}

        results = {
            'damages': {},
            'casualties': [],
            'retreats': [],
            'status': 'ongoing'
        }

        # Get combatants
        combatants_a = [agents[aid] for aid in conflict.side_a
                       if aid in agents and agents[aid].alive and aid not in conflict.casualties_a]
        combatants_b = [agents[aid] for aid in conflict.side_b
                       if aid in agents and agents[aid].alive and aid not in conflict.casualties_b]

        if not combatants_a or not combatants_b:
            # One side eliminated or fled
            self.end_conflict(conflict_id, 'side_a' if combatants_b else 'side_b')
            results['status'] = 'ended'
            return results

        # Pair up fighters (random matching for now)
        random.shuffle(combatants_a)
        random.shuffle(combatants_b)

        max_pairs = min(len(combatants_a), len(combatants_b))

        for i in range(max_pairs):
            attacker = combatants_a[i]
            defender = combatants_b[i]

            # Resolve combat between these two
            combat_result = self._resolve_single_combat(attacker, defender)

            results['damages'][attacker.id] = combat_result['damage_to_attacker']
            results['damages'][defender.id] = combat_result['damage_to_defender']

            # Apply damage
            attacker.health -= combat_result['damage_to_attacker']
            defender.health -= combat_result['damage_to_defender']

            # Check for casualties
            if attacker.health <= 0:
                attacker.alive = False
                attacker.death_cause = "killed in a fight"
                conflict.casualties_a.add(attacker.id)
                results['casualties'].append(attacker.id)

            if defender.health <= 0:
                defender.alive = False
                defender.death_cause = "killed in a fight"
                conflict.casualties_b.add(defender.id)
                results['casualties'].append(defender.id)

        # Check for retreat (low morale)
        self._check_morale_and_retreat(conflict, combatants_a, combatants_b, results)

        # Update conflict state
        conflict.turns_elapsed += 1

        # Check if over
        if conflict.is_over():
            size_a, size_b = conflict.get_size()
            winner = 'side_a' if size_a > size_b else 'side_b'
            self.end_conflict(conflict_id, winner)
            results['status'] = 'ended'
            results['winner'] = winner

        return results

    def _resolve_single_combat(
        self,
        attacker: 'Agent',
        defender: 'Agent'
    ) -> Dict:
        """Resolve combat between two agents"""
        # Get combat stats
        attacker_stats = self.get_combat_stats(attacker.id)
        defender_stats = self.get_combat_stats(defender.id)

        # Calculate combat power
        attacker_power = attacker_stats.get_combat_power()
        defender_power = defender_stats.get_combat_power()

        # Add randomness (fog of war)
        attacker_power *= random.uniform(0.7, 1.3)
        defender_power *= random.uniform(0.7, 1.3)

        # Base damage
        base_damage = 10.0

        # Damage dealt
        damage_to_defender = base_damage * attacker_power
        damage_to_attacker = base_damage * defender_power * 0.5  # Defender hits back

        # Equipment modifies damage
        attacker_weapon = self.agent_weapons.get(attacker.id)
        if attacker_weapon and attacker_weapon in self.weapons:
            weapon = self.weapons[attacker_weapon]
            attacker_skill = attacker.skills.get_skill('combat')
            damage_to_defender *= weapon.get_effective_damage(attacker_skill)

        defender_armor_id = self.agent_armor.get(defender.id)
        if defender_armor_id and defender_armor_id in self.armor:
            armor = self.armor[defender_armor_id]
            damage_to_defender *= (1.0 - armor.defense)

        return {
            'damage_to_attacker': damage_to_attacker,
            'damage_to_defender': damage_to_defender,
        }

    def _check_morale_and_retreat(
        self,
        conflict: Conflict,
        combatants_a: List['Agent'],
        combatants_b: List['Agent'],
        results: Dict
    ):
        """Check if either side retreats due to low morale"""
        # Calculate morale for each side
        casualties_a_count = len(conflict.casualties_a)
        casualties_b_count = len(conflict.casualties_b)

        total_a = len(conflict.side_a)
        total_b = len(conflict.side_b)

        # Casualties reduce morale
        morale_a = 1.0 - (casualties_a_count / max(1, total_a))
        morale_b = 1.0 - (casualties_b_count / max(1, total_b))

        # Retreat threshold (depends on personality)
        retreat_threshold = 0.3

        if morale_a < retreat_threshold:
            # Side A retreats
            for agent in combatants_a:
                if random.random() < 0.7:  # 70% flee
                    results['retreats'].append(agent.id)
                    # Remove from conflict (but not casualty)
                    conflict.side_a.discard(agent.id)

        if morale_b < retreat_threshold:
            # Side B retreats
            for agent in combatants_b:
                if random.random() < 0.7:
                    results['retreats'].append(agent.id)
                    conflict.side_b.discard(agent.id)

    def end_conflict(self, conflict_id: str, winner: str):
        """End a conflict"""
        if conflict_id not in self.active_conflicts:
            return

        conflict = self.active_conflicts[conflict_id]
        conflict.active = False
        conflict.winner = winner
        conflict.ended_at = datetime.now()

        # Move to history
        self.conflict_history.append(conflict)
        del self.active_conflicts[conflict_id]

        # Create grudges from conflict
        self._create_grudges_from_conflict(conflict)

    def _create_grudges_from_conflict(self, conflict: Conflict):
        """Conflicts create lasting grudges"""
        # Losers hold grudges against winners
        winners = conflict.side_a if conflict.winner == 'side_a' else conflict.side_b
        losers = conflict.side_b if conflict.winner == 'side_a' else conflict.side_a

        for loser in losers:
            for winner in winners:
                # Add or increase grudge
                key = (loser, winner)
                current_grudge = self.grudges.get(key, 0.0)
                self.grudges[key] = min(1.0, current_grudge + 0.3)

    def get_grudge(self, agent_a: str, agent_b: str) -> float:
        """Get grudge level between two agents"""
        key = (agent_a, agent_b)
        return self.grudges.get(key, 0.0)

    def set_grudge(self, agent_a: str, agent_b: str, intensity: float):
        """Set grudge level"""
        key = (agent_a, agent_b)
        self.grudges[key] = max(0.0, min(1.0, intensity))

    def get_agent_conflicts(self, agent_id: str) -> List[Conflict]:
        """Get all conflicts involving an agent"""
        conflicts = []

        for conflict in self.active_conflicts.values():
            if agent_id in conflict.side_a or agent_id in conflict.side_b:
                conflicts.append(conflict)

        return conflicts

    def get_statistics(self) -> Dict:
        """Get warfare statistics"""
        total_conflicts = len(self.active_conflicts) + len(self.conflict_history)
        active = len(self.active_conflicts)
        completed = len(self.conflict_history)

        total_casualties = sum(
            len(c.casualties_a) + len(c.casualties_b)
            for c in self.conflict_history
        )

        by_type = {}
        for conflict in list(self.active_conflicts.values()) + self.conflict_history:
            ctype = conflict.conflict_type.value
            by_type[ctype] = by_type.get(ctype, 0) + 1

        return {
            'total_conflicts': total_conflicts,
            'active_conflicts': active,
            'completed_conflicts': completed,
            'total_casualties': total_casualties,
            'by_type': by_type,
            'active_grudges': len(self.grudges),
        }

    def equip_weapon(self, agent_id: str, weapon_id: str):
        """Equip a weapon"""
        self.agent_weapons[agent_id] = weapon_id

    def equip_armor(self, agent_id: str, armor_id: str):
        """Equip armor"""
        self.agent_armor[agent_id] = armor_id

    def create_weapon(self, name: str, damage: float, skill_req: float = 0.0) -> str:
        """Create a new weapon type"""
        weapon_id = str(uuid.uuid4())
        self.weapons[weapon_id] = Weapon(name, damage, skill_req)
        return weapon_id

    def create_armor(self, name: str, defense: float, mobility_cost: float = 0.0) -> str:
        """Create a new armor type"""
        armor_id = str(uuid.uuid4())
        self.armor[armor_id] = Armor(name, defense, mobility_cost)
        return armor_id
