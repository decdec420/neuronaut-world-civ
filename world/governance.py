"""
Governance and Political System - Emergent Leadership

Agents form their own governments based on:
- Natural leaders emerge (high charisma + competence)
- Different government types evolve organically
- Laws created by agents, not pre-scripted
- Power struggles and revolutions

No fixed political system - agents create their own!
"""

from engine.ids import new_uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum


class GovernmentType(Enum):
    """Types of government (emerge organically)"""
    ANARCHY = "anarchy"  # No government
    STRONGMAN = "strongman"  # Single powerful leader
    OLIGARCHY = "oligarchy"  # Rule by few
    DEMOCRACY = "democracy"  # Rule by many
    COUNCIL = "council"  # Elected council
    THEOCRACY = "theocracy"  # Religious rule


@dataclass
class Law:
    """A rule created by agents"""
    id: str
    name: str
    description: str
    created_by: str  # Agent ID
    created_at: datetime = field(default_factory=datetime.now)

    # What the law does
    prohibition: Optional[str] = None  # What's forbidden
    requirement: Optional[str] = None  # What's required
    punishment: str = "social_penalty"  # What happens if broken

    # Support
    supporters: Set[str] = field(default_factory=set)
    opposers: Set[str] = field(default_factory=set)
    active: bool = True

    # Enforcement
    times_enforced: int = 0
    times_broken: int = 0

    def get_support_ratio(self) -> float:
        """Get ratio of support"""
        total = len(self.supporters) + len(self.opposers)
        if total == 0:
            return 0.5
        return len(self.supporters) / total


@dataclass
class Government:
    """A government formed by agents"""
    id: str
    name: str
    government_type: GovernmentType
    founded_at: datetime = field(default_factory=datetime.now)

    # Leadership
    leader_id: Optional[str] = None
    council_ids: Set[str] = field(default_factory=set)

    # Territory
    controlled_territory: Set[Tuple[int, int]] = field(default_factory=set)  # Grid positions
    citizens: Set[str] = field(default_factory=set)  # Agent IDs

    # Laws and policies
    laws: List[str] = field(default_factory=list)  # Law IDs
    treasury: float = 0.0  # Government wealth

    # Legitimacy
    approval_rating: float = 0.5  # 0-1, how much citizens support it
    stability: float = 1.0  # 0-1, risk of collapse

    active: bool = True


@dataclass
class Election:
    """An election for leadership"""
    id: str
    government_id: str
    position: str  # What's being elected
    started_at: datetime = field(default_factory=datetime.now)
    ends_at: datetime = field(default_factory=datetime.now)

    # Candidates
    ends_tick: int = 0  # the sim tick it closes on (ends_at is wall-clock and unused)
    candidates: Dict[str, int] = field(default_factory=dict)  # agent_id -> vote count
    eligible_voters: Set[str] = field(default_factory=set)
    votes_cast: Set[str] = field(default_factory=set)  # Who voted

    complete: bool = False
    winner: Optional[str] = None


class GovernanceManager:
    """Manages governments, laws, and politics"""

    def __init__(self):
        self.governments: Dict[str, Government] = {}
        self.laws: Dict[str, Law] = {}
        self.elections: Dict[str, Election] = {}

        # Agent political influence
        self.political_power: Dict[str, float] = {}  # agent_id -> power level

    def agent_forms_government(
        self,
        founder_id: str,
        name: str,
        gov_type: GovernmentType
    ) -> Government:
        """Agent creates a new government"""
        gov_id = str(new_uuid())

        government = Government(
            id=gov_id,
            name=name,
            government_type=gov_type,
            leader_id=founder_id,
            citizens={founder_id}
        )

        self.governments[gov_id] = government

        # Founder gets political power
        self.political_power[founder_id] = self.political_power.get(founder_id, 0.0) + 0.3

        return government

    def agent_joins_government(self, agent_id: str, government_id: str) -> bool:
        """Agent joins a government"""
        if government_id not in self.governments:
            return False

        government = self.governments[government_id]
        government.citizens.add(agent_id)

        return True

    def agent_creates_law(
        self,
        creator_id: str,
        government_id: str,
        name: str,
        description: str,
        prohibition: Optional[str] = None,
        requirement: Optional[str] = None
    ) -> Optional[Law]:
        """Agent proposes a new law"""
        if government_id not in self.governments:
            return None

        government = self.governments[government_id]

        # Check if agent has authority
        if not self._can_make_law(creator_id, government):
            return None

        law_id = str(new_uuid())

        law = Law(
            id=law_id,
            name=name,
            description=description,
            created_by=creator_id,
            prohibition=prohibition,
            requirement=requirement,
            supporters={creator_id}
        )

        self.laws[law_id] = law
        government.laws.append(law_id)

        return law

    def _can_make_law(self, agent_id: str, government: Government) -> bool:
        """Check if agent can create laws"""
        # Leader can always make laws
        if agent_id == government.leader_id:
            return True

        # Council members can
        if agent_id in government.council_ids:
            return True

        # In democracy, anyone with enough support can propose
        if government.government_type == GovernmentType.DEMOCRACY:
            power = self.political_power.get(agent_id, 0.0)
            return power > 0.2

        return False

    def vote_on_law(self, agent_id: str, law_id: str, support: bool):
        """Agent votes on a law"""
        if law_id not in self.laws:
            return

        law = self.laws[law_id]

        if support:
            law.supporters.add(agent_id)
            law.opposers.discard(agent_id)
        else:
            law.opposers.add(agent_id)
            law.supporters.discard(agent_id)

    def hold_election(
        self,
        government_id: str,
        position: str,
        duration_ticks: int = 100,
        current_tick: int = 0
    ) -> Election:
        """Hold an election that closes duration_ticks from now"""
        election_id = str(new_uuid())

        government = self.governments[government_id]

        election = Election(
            id=election_id,
            government_id=government_id,
            position=position,
            ends_tick=current_tick + duration_ticks,
            eligible_voters=government.citizens.copy()
        )

        self.elections[election_id] = election

        return election

    def agent_runs_for_office(self, agent_id: str, election_id: str) -> bool:
        """Agent becomes a candidate"""
        if election_id not in self.elections:
            return False

        election = self.elections[election_id]

        if election.complete:
            return False

        election.candidates[agent_id] = 0

        return True

    def agent_votes(self, voter_id: str, election_id: str, candidate_id: str) -> bool:
        """Agent casts a vote"""
        if election_id not in self.elections:
            return False

        election = self.elections[election_id]

        # Check eligibility
        if voter_id not in election.eligible_voters:
            return False

        # Check already voted
        if voter_id in election.votes_cast:
            return False

        # Check candidate exists
        if candidate_id not in election.candidates:
            return False

        # Cast vote
        election.candidates[candidate_id] += 1
        election.votes_cast.add(voter_id)

        return True

    def finalize_election(self, election_id: str) -> Optional[str]:
        """Count votes and determine winner"""
        if election_id not in self.elections:
            return None

        election = self.elections[election_id]

        if election.complete:
            return election.winner

        # Find winner
        if not election.candidates:
            election.complete = True
            return None

        winner = max(election.candidates, key=election.candidates.get)
        election.winner = winner
        election.complete = True

        # Update government
        government = self.governments[election.government_id]

        if election.position == "leader":
            government.leader_id = winner
        elif election.position == "council":
            government.council_ids.add(winner)

        # Winner gains political power
        self.political_power[winner] = self.political_power.get(winner, 0.0) + 0.5

        return winner

    def revolution(
        self,
        government_id: str,
        revolutionary_leader: str,
        supporters: Set[str]
    ) -> bool:
        """Attempt to overthrow government"""
        if government_id not in self.governments:
            return False

        government = self.governments[government_id]

        # Calculate revolutionary strength
        revolutionary_strength = len(supporters) / max(1, len(government.citizens))

        # Success chance based on:
        # - Number of supporters
        # - Government stability
        # - Leader's political power

        leader_power = self.political_power.get(revolutionary_leader, 0.0)

        success_chance = (
            revolutionary_strength * 0.5 +
            (1.0 - government.stability) * 0.3 +
            leader_power * 0.2
        )

        import random
        if random.random() < success_chance:
            # Revolution succeeds!
            old_leader = government.leader_id
            government.leader_id = revolutionary_leader
            government.stability = 0.3  # Unstable after revolution

            # Purge old leadership
            government.council_ids.clear()

            # Add revolutionaries to council
            government.council_ids.update(list(supporters)[:5])

            return True
        else:
            # Revolution fails
            # Revolutionaries lose political power
            for agent_id in supporters:
                self.political_power[agent_id] = self.political_power.get(agent_id, 0.5) * 0.5

            government.stability = min(1.0, government.stability + 0.1)

            return False

    # A democracy's leader stands for re-election this often (ticks; a day is
    # 144), and the vote stays open this long. These are the institution's own
    # rules: nobody is made to run or to vote.
    ELECTION_EVERY = 432
    ELECTION_OPEN_FOR = 72

    def open_election(self, government_id: str) -> Optional[Election]:
        for election in self.elections.values():
            if election.government_id == government_id and not election.complete:
                return election
        return None

    def update_governments(self, current_tick: int = 0):
        """Update all governments (approval, stability, elections, repeals)"""
        for election_id, election in list(self.elections.items()):
            if not election.complete and current_tick >= election.ends_tick > 0:
                self.finalize_election(election_id)

        for government in self.governments.values():
            if not government.active:
                continue

            # Democracies choose their leader by election
            if (government.government_type == GovernmentType.DEMOCRACY and current_tick > 0
                    and self.open_election(government.id) is None
                    and current_tick - getattr(government, 'last_election_tick', 0) >= self.ELECTION_EVERY):
                self.hold_election(government.id, "leader", self.ELECTION_OPEN_FOR, current_tick)
                government.last_election_tick = current_tick

            # A law most citizens have voted against is repealed
            for law_id in government.laws:
                law = self.laws.get(law_id)
                if (law and law.active and len(law.opposers) > len(law.supporters)
                        and len(law.supporters) + len(law.opposers) >= max(2, len(government.citizens) // 2)):
                    law.active = False
                    self.repealed_tax_policies = getattr(self, 'repealed_tax_policies', [])
                    if getattr(law, 'tax_policy_id', None):
                        self.repealed_tax_policies.append(law.tax_policy_id)

            # Update approval rating based on:
            # - Law support
            # - Economic conditions
            # - Security

            total_support = 0.0
            total_citizens = max(1, len(government.citizens))

            for law_id in government.laws:
                if law_id in self.laws:
                    law = self.laws[law_id]
                    total_support += law.get_support_ratio()

            if government.laws:
                government.approval_rating = total_support / len(government.laws)
            else:
                government.approval_rating = 0.5

            # Stability affected by approval
            if government.approval_rating < 0.3:
                government.stability -= 0.05
            elif government.approval_rating > 0.7:
                government.stability = min(1.0, government.stability + 0.02)

            # Government collapses if stability too low
            if government.stability < 0.1:
                government.active = False
                government.government_type = GovernmentType.ANARCHY

    def laws_binding(self, agent_id: str) -> List[Law]:
        """The laws in force for an agent (those of its government)."""
        government = self.get_agent_government(agent_id)
        if government is None:
            return []
        return [self.laws[l] for l in government.laws if l in self.laws and self.laws[l].active]

    def get_agent_government(self, agent_id: str) -> Optional[Government]:
        """Get government agent belongs to"""
        for government in self.governments.values():
            if agent_id in government.citizens and government.active:
                return government
        return None

    def get_statistics(self) -> Dict:
        """Get governance statistics"""
        total_governments = len(self.governments)
        active_governments = sum(1 for g in self.governments.values() if g.active)

        by_type = {}
        for gov in self.governments.values():
            if gov.active:
                gtype = gov.government_type.value
                by_type[gtype] = by_type.get(gtype, 0) + 1

        total_laws = len(self.laws)
        active_laws = sum(1 for l in self.laws.values() if l.active)

        return {
            'total_governments': total_governments,
            'active_governments': active_governments,
            'by_type': by_type,
            'total_laws': total_laws,
            'active_laws': active_laws,
            'active_elections': len([e for e in self.elections.values() if not e.complete]),
        }
