"""
Economic Crises System - Booms, Busts, and Bubbles

Implements:
- Inflation and deflation
- Market crashes and panics
- Asset bubbles and speculation
- Bank runs and financial contagion
- Depressions and recessions
- Economic recovery cycles
- Market manipulation

Philosophy: Markets are not always rational.
Greed and fear drive boom-bust cycles.
Crises destroy wealth but create opportunities.
Economic shocks test civilization resilience.
"""

import random
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Deque
from enum import Enum
from datetime import datetime


class CrisisType(Enum):
    """Types of economic crises"""
    INFLATION = "inflation"  # Money losing value
    HYPERINFLATION = "hyperinflation"  # Catastrophic inflation
    DEFLATION = "deflation"  # Falling prices
    BANK_RUN = "bank_run"  # Mass withdrawal from banks
    MARKET_CRASH = "market_crash"  # Asset prices collapse
    DEBT_CRISIS = "debt_crisis"  # Mass loan defaults
    BUBBLE_BURST = "bubble_burst"  # Speculative bubble pops
    DEPRESSION = "depression"  # Severe long-term downturn


class CrisisSeverity(Enum):
    """Severity of economic crisis"""
    MINOR = "minor"  # < 10% impact
    MODERATE = "moderate"  # 10-25% impact
    MAJOR = "major"  # 25-50% impact
    CATASTROPHIC = "catastrophic"  # > 50% impact


class EconomicPhase(Enum):
    """Phase of economic cycle"""
    EXPANSION = "expansion"  # Growth
    PEAK = "peak"  # Top of cycle
    CONTRACTION = "contraction"  # Decline
    TROUGH = "trough"  # Bottom of cycle
    RECOVERY = "recovery"  # Rebuilding


@dataclass
class Crisis:
    """An economic crisis event"""
    id: str
    crisis_type: CrisisType
    severity: CrisisSeverity

    # Cause
    trigger: str  # What caused it
    root_causes: List[str] = field(default_factory=list)

    # Impact
    wealth_destroyed: float = 0.0
    agents_affected: Set[str] = field(default_factory=set)
    banks_failed: int = 0
    businesses_bankrupt: int = 0

    # Timeline
    started_tick: int = 0
    ended_tick: int = 0
    duration_ticks: int = 0
    active: bool = True

    # Recovery
    recovery_started: bool = False
    recovery_progress: float = 0.0  # 0-1


@dataclass
class AssetBubble:
    """A speculative bubble in an asset"""
    id: str
    asset_type: str  # What's being speculated on
    name: str

    # Bubble dynamics
    fair_value: float  # Actual worth
    market_price: float  # Inflated price
    overvaluation: float = 1.0  # How overvalued (2.0 = 200% of fair value)

    # Speculation
    speculators: Set[str] = field(default_factory=set)
    total_invested: float = 0.0

    # Timeline
    formed_tick: int = 0
    peak_tick: int = 0
    burst_tick: int = 0

    # Status
    growing: bool = True
    peaked: bool = False
    burst: bool = False


@dataclass
class SpeculativeInvestment:
    """A speculative investment in a bubble"""
    id: str
    investor_id: str
    bubble_id: str

    # Investment
    amount_invested: float
    purchase_price: float  # Price when bought
    current_value: float  # Current market value

    # Timing
    invested_tick: int
    sold_tick: int = 0

    # Outcome
    realized: bool = False
    profit_loss: float = 0.0


class EconomicCrisesManager:
    """
    Manages economic crises, bubbles, and boom-bust cycles.

    Key mechanics:
    - Inflation erodes purchasing power over time
    - Bubbles form when speculation exceeds fundamentals
    - Crashes happen when confidence collapses
    - Crises spread through interconnected systems (contagion)
    - Recovery requires time and policy intervention
    """

    def __init__(self):
        self.active_crises: Dict[str, Crisis] = {}
        self.historical_crises: Deque[Crisis] = deque(maxlen=1000)  # Keep last 1000 crises
        self.asset_bubbles: Dict[str, AssetBubble] = {}
        self.speculative_investments: Dict[str, SpeculativeInvestment] = {}

        # Economic indicators
        self.inflation_rate: float = 0.0  # Annual inflation %
        self.unemployment_rate: float = 0.05  # % without income
        self.economic_phase: EconomicPhase = EconomicPhase.EXPANSION

        # Crisis tracking
        self.total_crises: int = 0
        self.total_wealth_destroyed: float = 0.0
        self.total_bubbles_burst: int = 0

        # Market confidence
        self.market_confidence: float = 0.7  # 0-1, affects investment
        self.panic_level: float = 0.0  # 0-1, drives crises

    # ===== INFLATION & DEFLATION =====

    def update_inflation(
        self,
        money_supply_change: float,
        goods_production_change: float
    ):
        """Update inflation based on monetary and real factors"""

        # Quantity theory: inflation = money growth - production growth
        # Simplified: MV = PQ → ΔP = ΔM - ΔQ

        inflation_pressure = money_supply_change - goods_production_change

        # Add some randomness (supply shocks, etc.)
        shock = random.gauss(0, 0.01)
        inflation_pressure += shock

        # Update inflation rate (smoothed)
        self.inflation_rate = self.inflation_rate * 0.9 + inflation_pressure * 0.1

        # Check for crisis levels
        if self.inflation_rate > 0.50:  # 50%+ inflation
            self._trigger_hyperinflation()
        elif self.inflation_rate > 0.15:  # 15%+ inflation
            self._trigger_inflation_crisis()
        elif self.inflation_rate < -0.10:  # 10%+ deflation
            self._trigger_deflation_crisis()

    def _trigger_inflation_crisis(self):
        """Trigger an inflation crisis"""

        # Check if already have inflation crisis
        for crisis in self.active_crises.values():
            if crisis.crisis_type == CrisisType.INFLATION:
                return  # Already in one

        crisis_id = str(uuid.uuid4())
        crisis = Crisis(
            id=crisis_id,
            crisis_type=CrisisType.INFLATION,
            severity=CrisisSeverity.MODERATE,
            trigger="Excessive money supply growth",
            root_causes=["Money printing", "Currency debasement", "Supply shortages"],
            started_tick=0  # Set by caller
        )

        self.active_crises[crisis_id] = crisis
        self.total_crises += 1

    def _trigger_hyperinflation(self):
        """Trigger catastrophic hyperinflation"""

        crisis_id = str(uuid.uuid4())
        crisis = Crisis(
            id=crisis_id,
            crisis_type=CrisisType.HYPERINFLATION,
            severity=CrisisSeverity.CATASTROPHIC,
            trigger="Loss of currency confidence",
            root_causes=["Excessive money printing", "War finance", "Economic collapse"],
            started_tick=0
        )

        self.active_crises[crisis_id] = crisis
        self.total_crises += 1
        self.market_confidence *= 0.3  # Massive confidence loss

    def _trigger_deflation_crisis(self):
        """Trigger deflation crisis"""

        crisis_id = str(uuid.uuid4())
        crisis = Crisis(
            id=crisis_id,
            crisis_type=CrisisType.DEFLATION,
            severity=CrisisSeverity.MODERATE,
            trigger="Collapsing demand",
            root_causes=["Depression", "Debt deleveraging", "Money hoarding"],
            started_tick=0
        )

        self.active_crises[crisis_id] = crisis
        self.total_crises += 1

    # ===== ASSET BUBBLES =====

    def create_bubble(
        self,
        asset_type: str,
        fair_value: float,
        current_tick: int
    ) -> AssetBubble:
        """Create a new speculative bubble"""

        bubble_id = str(uuid.uuid4())

        bubble = AssetBubble(
            id=bubble_id,
            asset_type=asset_type,
            name=f"{asset_type.title()} Bubble",
            fair_value=fair_value,
            market_price=fair_value,
            overvaluation=1.0,
            formed_tick=current_tick
        )

        self.asset_bubbles[bubble_id] = bubble

        return bubble

    def invest_in_bubble(
        self,
        bubble_id: str,
        investor_id: str,
        amount: float,
        current_tick: int
    ) -> Optional[SpeculativeInvestment]:
        """Agent speculates in a bubble"""

        if bubble_id not in self.asset_bubbles:
            return None

        bubble = self.asset_bubbles[bubble_id]

        if bubble.burst:
            return None  # Can't invest in burst bubble

        investment_id = str(uuid.uuid4())

        investment = SpeculativeInvestment(
            id=investment_id,
            investor_id=investor_id,
            bubble_id=bubble_id,
            amount_invested=amount,
            purchase_price=bubble.market_price,
            current_value=amount,
            invested_tick=current_tick
        )

        self.speculative_investments[investment_id] = investment

        # Add to bubble
        bubble.speculators.add(investor_id)
        bubble.total_invested += amount

        # Speculation increases price!
        price_increase = amount / bubble.fair_value * 0.1
        bubble.market_price *= (1 + price_increase)
        bubble.overvaluation = bubble.market_price / bubble.fair_value

        return investment

    def update_bubbles(self, current_tick: int) -> List[Dict]:
        """Update all bubbles - grow or burst"""

        events = []

        for bubble in self.asset_bubbles.values():
            if bubble.burst:
                continue

            if bubble.growing:
                # Bubble grows with speculation
                growth_rate = len(bubble.speculators) * 0.02  # 2% per speculator
                bubble.market_price *= (1 + growth_rate)
                bubble.overvaluation = bubble.market_price / bubble.fair_value

                # Update investment values
                for investment in self.speculative_investments.values():
                    if investment.bubble_id == bubble.id and not investment.realized:
                        investment.current_value = (
                            investment.amount_invested * (bubble.market_price / investment.purchase_price)
                        )

                # Check if bubble peaks
                if bubble.overvaluation > 5.0:  # 500% overvalued
                    bubble.peaked = True
                    bubble.peak_tick = current_tick

                # Check if bubble bursts
                burst_chance = max(0, (bubble.overvaluation - 2.0) * 0.1)
                if bubble.peaked and random.random() < burst_chance:
                    # BUBBLE BURSTS!
                    result = self._burst_bubble(bubble, current_tick)
                    events.append(result)

        return events

    def _burst_bubble(self, bubble: AssetBubble, current_tick: int) -> Dict:
        """Burst a speculative bubble"""

        bubble.burst = True
        bubble.burst_tick = current_tick
        bubble.growing = False

        # Price crashes to fair value (or below)
        crash_severity = random.uniform(0.7, 1.2)  # Can overcorrect
        bubble.market_price = bubble.fair_value / crash_severity

        # Calculate losses
        total_lost = 0.0
        losers = []

        for investment in self.speculative_investments.values():
            if investment.bubble_id == bubble.id and not investment.realized:
                # Realize the loss
                final_value = investment.amount_invested * (bubble.market_price / investment.purchase_price)
                investment.current_value = final_value
                investment.realized = True
                investment.profit_loss = final_value - investment.amount_invested
                investment.sold_tick = current_tick

                loss = investment.amount_invested - final_value
                total_lost += loss

                losers.append(investment.investor_id)

        # Trigger crisis if big enough
        if total_lost > 1000:
            self._trigger_bubble_burst_crisis(bubble, total_lost)

        self.total_bubbles_burst += 1
        self.total_wealth_destroyed += total_lost

        # Market confidence drops
        confidence_impact = min(0.5, total_lost / 10000)
        self.market_confidence *= (1 - confidence_impact)

        return {
            'type': 'bubble_burst',
            'bubble_id': bubble.id,
            'asset_type': bubble.asset_type,
            'overvaluation_peak': bubble.overvaluation,
            'wealth_destroyed': total_lost,
            'investors_affected': len(losers)
        }

    def _trigger_bubble_burst_crisis(self, bubble: AssetBubble, wealth_lost: float):
        """Trigger crisis from bubble bursting"""

        severity = CrisisSeverity.MINOR
        if wealth_lost > 10000:
            severity = CrisisSeverity.CATASTROPHIC
        elif wealth_lost > 5000:
            severity = CrisisSeverity.MAJOR
        elif wealth_lost > 1000:
            severity = CrisisSeverity.MODERATE

        crisis_id = str(uuid.uuid4())
        crisis = Crisis(
            id=crisis_id,
            crisis_type=CrisisType.BUBBLE_BURST,
            severity=severity,
            trigger=f"{bubble.asset_type} bubble burst",
            root_causes=["Speculation", "Irrational exuberance", "Overvaluation"],
            wealth_destroyed=wealth_lost,
            agents_affected=bubble.speculators.copy(),
            started_tick=bubble.burst_tick
        )

        self.active_crises[crisis_id] = crisis
        self.total_crises += 1

    # ===== MARKET CRASHES =====

    def trigger_market_crash(
        self,
        trigger: str,
        severity: CrisisSeverity,
        current_tick: int
    ) -> Crisis:
        """Trigger a general market crash"""

        crisis_id = str(uuid.uuid4())

        # Calculate impact
        severity_multipliers = {
            CrisisSeverity.MINOR: 0.10,
            CrisisSeverity.MODERATE: 0.25,
            CrisisSeverity.MAJOR: 0.50,
            CrisisSeverity.CATASTROPHIC: 0.75
        }

        wealth_loss_multiplier = severity_multipliers.get(severity, 0.25)

        crisis = Crisis(
            id=crisis_id,
            crisis_type=CrisisType.MARKET_CRASH,
            severity=severity,
            trigger=trigger,
            root_causes=["Market panic", "Loss of confidence", "Systemic risk"],
            started_tick=current_tick
        )

        self.active_crises[crisis_id] = crisis
        self.total_crises += 1

        # Confidence collapse
        self.market_confidence *= (1 - wealth_loss_multiplier)
        self.panic_level = wealth_loss_multiplier

        return crisis

    # ===== BANK RUNS =====

    def trigger_bank_run(
        self,
        triggering_event: str,
        current_tick: int
    ) -> Crisis:
        """Trigger a bank run panic"""

        crisis_id = str(uuid.uuid4())

        crisis = Crisis(
            id=crisis_id,
            crisis_type=CrisisType.BANK_RUN,
            severity=CrisisSeverity.MAJOR,
            trigger=triggering_event,
            root_causes=["Loss of confidence in banks", "Fear of insolvency", "Contagion"],
            started_tick=current_tick
        )

        self.active_crises[crisis_id] = crisis
        self.total_crises += 1
        self.panic_level = 0.8

        return crisis

    # ===== CRISIS MANAGEMENT =====

    def update_crises(self, current_tick: int) -> List[Dict]:
        """Update all active crises"""

        events = []

        for crisis in list(self.active_crises.values()):
            if not crisis.active:
                continue

            crisis.duration_ticks = current_tick - crisis.started_tick

            # Natural recovery over time
            if crisis.duration_ticks > 100:  # After 100 ticks, recovery starts
                if not crisis.recovery_started:
                    crisis.recovery_started = True
                    events.append({
                        'type': 'crisis_recovery_started',
                        'crisis_id': crisis.id,
                        'crisis_type': crisis.crisis_type.value
                    })

                # Recovery progress
                crisis.recovery_progress = min(1.0, (crisis.duration_ticks - 100) / 200)

                # End crisis when fully recovered
                if crisis.recovery_progress >= 1.0:
                    crisis.active = False
                    crisis.ended_tick = current_tick
                    self.historical_crises.append(crisis)
                    del self.active_crises[crisis.id]

                    events.append({
                        'type': 'crisis_ended',
                        'crisis_id': crisis.id,
                        'crisis_type': crisis.crisis_type.value,
                        'duration': crisis.duration_ticks
                    })

                    # Restore confidence gradually
                    self.market_confidence = min(0.9, self.market_confidence * 1.1)
                    self.panic_level *= 0.5

        return events

    def calculate_wealth_impact(
        self,
        agent_wealth: float,
        crisis_exposure: float = 1.0
    ) -> float:
        """Calculate how much wealth is lost due to active crises"""

        total_impact = 0.0

        for crisis in self.active_crises.values():
            severity_impacts = {
                CrisisSeverity.MINOR: 0.05,
                CrisisSeverity.MODERATE: 0.15,
                CrisisSeverity.MAJOR: 0.35,
                CrisisSeverity.CATASTROPHIC: 0.60
            }

            impact_rate = severity_impacts.get(crisis.severity, 0.1)
            wealth_lost = agent_wealth * impact_rate * crisis_exposure

            total_impact += wealth_lost

        return total_impact

    # ===== ECONOMIC CYCLE =====

    def update_economic_phase(self, growth_rate: float):
        """Update current economic phase based on growth"""

        if growth_rate > 0.05:
            if self.economic_phase == EconomicPhase.RECOVERY:
                self.economic_phase = EconomicPhase.EXPANSION
            elif self.economic_phase == EconomicPhase.EXPANSION:
                # Check for overheating
                if self.inflation_rate > 0.10:
                    self.economic_phase = EconomicPhase.PEAK
        elif growth_rate < -0.03:
            if self.economic_phase in [EconomicPhase.PEAK, EconomicPhase.EXPANSION]:
                self.economic_phase = EconomicPhase.CONTRACTION
            elif self.economic_phase == EconomicPhase.CONTRACTION:
                # Deep recession
                self.economic_phase = EconomicPhase.TROUGH
        else:
            # Moderate growth - recovery
            if self.economic_phase == EconomicPhase.TROUGH:
                self.economic_phase = EconomicPhase.RECOVERY

    # ===== QUERIES =====

    def get_active_crises(self) -> List[Crisis]:
        """Get all active crises"""
        return list(self.active_crises.values())

    def is_in_crisis(self) -> bool:
        """Check if economy is in crisis"""
        return len(self.active_crises) > 0 or self.panic_level > 0.5

    def get_statistics(self) -> Dict:
        """Get crisis statistics"""

        active_bubbles = sum(1 for b in self.asset_bubbles.values() if not b.burst)
        growing_bubbles = sum(1 for b in self.asset_bubbles.values() if b.growing)

        return {
            'active_crises': len(self.active_crises),
            'total_historical_crises': len(self.historical_crises),
            'total_wealth_destroyed': round(self.total_wealth_destroyed, 2),
            'inflation_rate': round(self.inflation_rate * 100, 2),
            'market_confidence': round(self.market_confidence * 100, 1),
            'panic_level': round(self.panic_level * 100, 1),
            'economic_phase': self.economic_phase.value,
            'active_bubbles': active_bubbles,
            'growing_bubbles': growing_bubbles,
            'bubbles_burst': self.total_bubbles_burst,
            'in_crisis': self.is_in_crisis()
        }
