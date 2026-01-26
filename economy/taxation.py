"""
Taxation & Revenue System - No Taxation Without Representation!

Implements:
- Tax types (income, wealth, sales, property, poll tax)
- Tax collection and enforcement
- Tax resistance and evasion
- Revolutionary movements against unfair taxation
- Public goods funded by taxes
- Representation and consent
- Tax revolts and rebellions

Philosophy: Taxation requires legitimacy.
Taxation without representation breeds revolution.
Excessive taxes destroy wealth creation.
Public goods require collective funding.
"""

import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class TaxType(Enum):
    """Types of taxes"""
    INCOME_TAX = "income_tax"  # Percentage of earnings
    WEALTH_TAX = "wealth_tax"  # Percentage of total wealth
    SALES_TAX = "sales_tax"  # Per transaction
    PROPERTY_TAX = "property_tax"  # On land/buildings owned
    POLL_TAX = "poll_tax"  # Fixed amount per person
    TARIFF = "tariff"  # On imported goods


class TaxBurden(Enum):
    """How heavy the tax burden feels"""
    MINIMAL = "minimal"  # < 5% total
    LIGHT = "light"  # 5-15%
    MODERATE = "moderate"  # 15-30%
    HEAVY = "heavy"  # 30-50%
    OPPRESSIVE = "oppressive"  # > 50%


class ResistanceLevel(Enum):
    """Levels of tax resistance"""
    COMPLIANT = "compliant"  # Pay willingly
    GRUMBLING = "grumbling"  # Pay reluctantly
    EVADING = "evading"  # Try to avoid
    REFUSING = "refusing"  # Actively refuse
    REVOLTING = "revolting"  # Armed resistance


@dataclass
class TaxPolicy:
    """A tax policy"""
    id: str
    tax_type: TaxType
    rate: float  # Tax rate (0.10 = 10%)

    # Who pays
    applies_to: str = "all"  # "all", "wealthy", "poor", "merchants", etc.
    exemptions: Set[str] = field(default_factory=set)  # Agent IDs exempt

    # Collection
    collector_id: Optional[str] = None  # Who collects (ruler/government)
    collection_efficiency: float = 0.8  # % actually collected

    # Legitimacy
    has_representation: bool = False  # Do taxpayers have a say?
    popular_approval: float = 0.5  # 0-1, how much people support it

    # Implementation
    enacted_tick: int = 0
    repealed_tick: int = 0
    active: bool = True


@dataclass
class TaxCollection:
    """A tax collection event"""
    id: str
    policy_id: str
    taxpayer_id: str
    collector_id: str

    # Collection details
    amount_owed: float
    amount_paid: float
    amount_evaded: float = 0.0

    # Enforcement
    enforced: bool = False
    penalty_applied: float = 0.0

    # Timing
    collected_tick: int = 0

    # Resistance
    resisted: bool = False
    violence_used: bool = False


@dataclass
class TaxRevolt:
    """A tax resistance movement or revolt"""
    id: str
    name: str

    # Cause
    triggering_policy_id: str
    grievance: str  # Why they're revolting

    # Participants
    leader_id: str
    participants: Set[str] = field(default_factory=set)

    # Demands
    demands: List[str] = field(default_factory=list)

    # Status
    started_tick: int = 0
    ended_tick: int = 0
    active: bool = True
    succeeded: bool = False

    # Violence
    violent: bool = False
    casualties: int = 0


@dataclass
class PublicGood:
    """Something funded by tax revenue"""
    id: str
    name: str
    description: str

    # Funding
    cost_per_tick: float
    total_funded: float = 0.0

    # Benefits
    beneficiaries: Set[str] = field(default_factory=set)
    benefit_value: float = 0.0  # How much value it provides

    # Status
    funded: bool = True
    created_tick: int = 0


class TaxationManager:
    """
    Manages taxation, collection, resistance, and revolts.

    Key mechanics:
    - Taxes require legitimacy (representation) to be accepted
    - Excessive taxation breeds resistance
    - Tax revolts can overthrow governments
    - Public goods justify taxation
    - Evasion is rational when taxes are unfair
    """

    def __init__(self):
        self.tax_policies: Dict[str, TaxPolicy] = {}
        self.collections: Dict[str, TaxCollection] = {}
        self.revolts: Dict[str, TaxRevolt] = {}
        self.public_goods: Dict[str, PublicGood] = {}

        # Resistance tracking
        self.agent_resistance: Dict[str, ResistanceLevel] = {}
        self.tax_burden_by_agent: Dict[str, float] = {}

        # Revenue tracking
        self.total_revenue_collected: float = 0.0
        self.total_revenue_evaded: float = 0.0
        self.total_public_spending: float = 0.0

        # Statistics
        self.total_revolts: int = 0
        self.successful_revolts: int = 0
        self.violent_revolts: int = 0

    # ===== TAX POLICY =====

    def enact_tax_policy(
        self,
        tax_type: TaxType,
        rate: float,
        collector_id: str,
        has_representation: bool,
        current_tick: int,
        applies_to: str = "all"
    ) -> TaxPolicy:
        """Enact a new tax policy"""

        policy_id = str(uuid.uuid4())

        # Calculate initial approval based on representation and rate
        if has_representation:
            # With representation, reasonable taxes are more accepted
            if rate < 0.15:
                approval = 0.7
            elif rate < 0.30:
                approval = 0.5
            else:
                approval = 0.3
        else:
            # Without representation, all taxes are less accepted
            if rate < 0.10:
                approval = 0.4
            elif rate < 0.25:
                approval = 0.2
            else:
                approval = 0.1  # "No taxation without representation!"

        policy = TaxPolicy(
            id=policy_id,
            tax_type=tax_type,
            rate=rate,
            applies_to=applies_to,
            collector_id=collector_id,
            has_representation=has_representation,
            popular_approval=approval,
            enacted_tick=current_tick
        )

        self.tax_policies[policy_id] = policy

        return policy

    def repeal_tax_policy(self, policy_id: str, current_tick: int) -> bool:
        """Repeal a tax policy"""

        if policy_id not in self.tax_policies:
            return False

        policy = self.tax_policies[policy_id]
        policy.active = False
        policy.repealed_tick = current_tick

        return True

    # ===== TAX COLLECTION =====

    def collect_tax(
        self,
        policy_id: str,
        taxpayer_id: str,
        taxpayer_wealth: float,
        taxpayer_income: float,
        current_tick: int
    ) -> Dict:
        """Attempt to collect tax from an agent"""

        if policy_id not in self.tax_policies:
            return {'success': False, 'reason': 'Policy not found'}

        policy = self.tax_policies[policy_id]

        if not policy.active:
            return {'success': False, 'reason': 'Policy not active'}

        # Calculate amount owed
        amount_owed = self._calculate_tax_owed(policy, taxpayer_wealth, taxpayer_income)

        # Check for evasion
        resistance_level = self.get_resistance_level(taxpayer_id, policy)
        evasion_chance = self._get_evasion_chance(resistance_level, policy)

        amount_evaded = 0.0
        if random.random() < evasion_chance:
            # Tax evasion!
            evasion_rate = random.uniform(0.3, 0.9)  # Evade 30-90%
            amount_evaded = amount_owed * evasion_rate
            amount_owed -= amount_evaded
            self.total_revenue_evaded += amount_evaded

        # Determine if tax is resisted
        resisted = resistance_level in [ResistanceLevel.REFUSING, ResistanceLevel.REVOLTING]

        collection_id = str(uuid.uuid4())
        collection = TaxCollection(
            id=collection_id,
            policy_id=policy_id,
            taxpayer_id=taxpayer_id,
            collector_id=policy.collector_id,
            amount_owed=amount_owed,
            amount_paid=amount_owed if not resisted else 0.0,
            amount_evaded=amount_evaded,
            resisted=resisted,
            collected_tick=current_tick
        )

        self.collections[collection_id] = collection

        if not resisted:
            self.total_revenue_collected += amount_owed

            # Update tax burden
            current_burden = self.tax_burden_by_agent.get(taxpayer_id, 0.0)
            self.tax_burden_by_agent[taxpayer_id] = current_burden + amount_owed

            return {
                'success': True,
                'amount_collected': amount_owed,
                'amount_evaded': amount_evaded,
                'resisted': False
            }
        else:
            # Tax resistance!
            return {
                'success': False,
                'amount_collected': 0.0,
                'amount_evaded': amount_evaded,
                'resisted': True,
                'resistance_level': resistance_level.value
            }

    def _calculate_tax_owed(
        self,
        policy: TaxPolicy,
        wealth: float,
        income: float
    ) -> float:
        """Calculate tax amount owed"""

        if policy.tax_type == TaxType.INCOME_TAX:
            return income * policy.rate
        elif policy.tax_type == TaxType.WEALTH_TAX:
            return wealth * policy.rate
        elif policy.tax_type == TaxType.POLL_TAX:
            return policy.rate  # Fixed amount
        elif policy.tax_type == TaxType.PROPERTY_TAX:
            # Simplified: assume wealth represents property value
            return wealth * 0.5 * policy.rate
        else:
            return wealth * policy.rate

    # ===== TAX RESISTANCE =====

    def get_resistance_level(
        self,
        agent_id: str,
        policy: TaxPolicy
    ) -> ResistanceLevel:
        """Determine agent's resistance level to a tax"""

        if agent_id in self.agent_resistance:
            return self.agent_resistance[agent_id]

        # Calculate resistance based on policy characteristics
        resistance_score = 0.0

        # Factor 1: Tax rate
        if policy.rate > 0.50:
            resistance_score += 0.5  # Oppressive
        elif policy.rate > 0.30:
            resistance_score += 0.3  # Heavy
        elif policy.rate > 0.15:
            resistance_score += 0.1  # Moderate

        # Factor 2: Representation
        if not policy.has_representation:
            resistance_score += 0.3  # "No taxation without representation!"

        # Factor 3: Popular approval
        resistance_score += (1.0 - policy.popular_approval) * 0.2

        # Factor 4: Total tax burden
        total_burden = self.tax_burden_by_agent.get(agent_id, 0.0)
        if total_burden > 100:
            resistance_score += 0.2

        # Convert score to resistance level
        if resistance_score < 0.2:
            level = ResistanceLevel.COMPLIANT
        elif resistance_score < 0.4:
            level = ResistanceLevel.GRUMBLING
        elif resistance_score < 0.6:
            level = ResistanceLevel.EVADING
        elif resistance_score < 0.8:
            level = ResistanceLevel.REFUSING
        else:
            level = ResistanceLevel.REVOLTING

        self.agent_resistance[agent_id] = level
        return level

    def _get_evasion_chance(
        self,
        resistance: ResistanceLevel,
        policy: TaxPolicy
    ) -> float:
        """Calculate chance of tax evasion"""

        base_chances = {
            ResistanceLevel.COMPLIANT: 0.05,
            ResistanceLevel.GRUMBLING: 0.15,
            ResistanceLevel.EVADING: 0.40,
            ResistanceLevel.REFUSING: 0.70,
            ResistanceLevel.REVOLTING: 0.90
        }

        chance = base_chances.get(resistance, 0.2)

        # Adjust for collection efficiency
        chance *= (1.0 - policy.collection_efficiency)

        return min(0.95, chance)

    # ===== TAX REVOLTS =====

    def start_tax_revolt(
        self,
        leader_id: str,
        triggering_policy_id: str,
        grievance: str,
        current_tick: int
    ) -> TaxRevolt:
        """Start a tax revolt/rebellion"""

        revolt_id = str(uuid.uuid4())

        policy = self.tax_policies.get(triggering_policy_id)

        # Generate demands
        demands = self._generate_revolt_demands(policy)

        revolt = TaxRevolt(
            id=revolt_id,
            name=f"Tax Revolt of {current_tick}",
            triggering_policy_id=triggering_policy_id,
            grievance=grievance,
            leader_id=leader_id,
            participants={leader_id},
            demands=demands,
            started_tick=current_tick
        )

        self.revolts[revolt_id] = revolt
        self.total_revolts += 1

        return revolt

    def join_revolt(self, revolt_id: str, agent_id: str) -> bool:
        """Agent joins a tax revolt"""

        if revolt_id not in self.revolts:
            return False

        revolt = self.revolts[revolt_id]

        if not revolt.active:
            return False

        revolt.participants.add(agent_id)

        # Escalate to violence if enough participants
        if len(revolt.participants) > 10 and not revolt.violent:
            revolt.violent = True
            self.violent_revolts += 1

        return True

    def resolve_revolt(
        self,
        revolt_id: str,
        demands_met: bool,
        current_tick: int
    ) -> Dict:
        """Resolve a tax revolt"""

        if revolt_id not in self.revolts:
            return {'success': False, 'reason': 'Revolt not found'}

        revolt = self.revolts[revolt_id]
        revolt.active = False
        revolt.ended_tick = current_tick
        revolt.succeeded = demands_met

        if demands_met:
            self.successful_revolts += 1

            # Repeal the triggering policy
            if revolt.triggering_policy_id in self.tax_policies:
                self.repeal_tax_policy(revolt.triggering_policy_id, current_tick)

        return {
            'success': True,
            'revolt_succeeded': demands_met,
            'participants': len(revolt.participants),
            'violent': revolt.violent
        }

    def _generate_revolt_demands(self, policy: Optional[TaxPolicy]) -> List[str]:
        """Generate demands for a revolt"""

        demands = []

        if policy:
            if not policy.has_representation:
                demands.append("Representation in government")

            if policy.rate > 0.30:
                demands.append("Lower tax rates")

            demands.append("Repeal unjust taxes")

        demands.append("Fair taxation")

        return demands

    # ===== PUBLIC GOODS =====

    def create_public_good(
        self,
        name: str,
        description: str,
        cost_per_tick: float,
        benefit_value: float,
        current_tick: int
    ) -> PublicGood:
        """Create a public good funded by taxes"""

        good_id = str(uuid.uuid4())

        good = PublicGood(
            id=good_id,
            name=name,
            description=description,
            cost_per_tick=cost_per_tick,
            benefit_value=benefit_value,
            created_tick=current_tick
        )

        self.public_goods[good_id] = good

        return good

    def fund_public_goods(self, available_revenue: float) -> float:
        """Allocate tax revenue to public goods"""

        total_spent = 0.0

        for good in self.public_goods.values():
            if not good.funded:
                continue

            if available_revenue >= good.cost_per_tick:
                available_revenue -= good.cost_per_tick
                good.total_funded += good.cost_per_tick
                total_spent += good.cost_per_tick
                self.total_public_spending += good.cost_per_tick
            else:
                # Not enough funds
                good.funded = False

        return total_spent

    # ===== QUERIES =====

    def get_active_policies(self) -> List[TaxPolicy]:
        """Get all active tax policies"""
        return [p for p in self.tax_policies.values() if p.active]

    def get_total_tax_rate(self) -> float:
        """Get combined tax rate from all policies"""
        return sum(p.rate for p in self.get_active_policies())

    def calculate_tax_burden(self, agent_wealth: float, agent_income: float) -> Dict:
        """Calculate total tax burden for an agent"""

        total_owed = 0.0

        for policy in self.get_active_policies():
            amount = self._calculate_tax_owed(policy, agent_wealth, agent_income)
            total_owed += amount

        # Classify burden
        burden_ratio = total_owed / max(1.0, agent_wealth + agent_income)

        if burden_ratio < 0.05:
            burden = TaxBurden.MINIMAL
        elif burden_ratio < 0.15:
            burden = TaxBurden.LIGHT
        elif burden_ratio < 0.30:
            burden = TaxBurden.MODERATE
        elif burden_ratio < 0.50:
            burden = TaxBurden.HEAVY
        else:
            burden = TaxBurden.OPPRESSIVE

        return {
            'total_owed': total_owed,
            'burden_ratio': burden_ratio,
            'burden_level': burden.value
        }

    def get_statistics(self) -> Dict:
        """Get taxation statistics"""

        active_policies = self.get_active_policies()
        active_revolts = sum(1 for r in self.revolts.values() if r.active)

        return {
            'active_tax_policies': len(active_policies),
            'total_revenue_collected': round(self.total_revenue_collected, 2),
            'total_revenue_evaded': round(self.total_revenue_evaded, 2),
            'evasion_rate': round((self.total_revenue_evaded / max(1, self.total_revenue_collected + self.total_revenue_evaded)) * 100, 2),
            'total_public_spending': round(self.total_public_spending, 2),
            'public_goods_funded': len(self.public_goods),
            'total_revolts': self.total_revolts,
            'active_revolts': active_revolts,
            'successful_revolts': self.successful_revolts,
            'violent_revolts': self.violent_revolts
        }
