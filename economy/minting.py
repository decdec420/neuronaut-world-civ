"""
Minting & Coinage System - From Ore to Currency

Implements:
- Metal-based coin denominations (gold, silver, copper, bronze)
- Minting workshops and facilities
- Coin purity and debasement
- Counterfeiting mechanics
- Metal value hierarchy
- Coin discovery and adoption
- Currency standardization

Philosophy: Real money emerges from scarce, valuable metals.
The progression from barter → commodity money → metal coins → paper money.
"""

import random
from engine.ids import new_uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class CoinType(Enum):
    """Types of metal coins"""
    COPPER_PENNY = "copper_penny"  # 1 unit
    BRONZE_PENNY = "bronze_penny"  # 1 unit (early alternative)
    SILVER_SHILLING = "silver_shilling"  # 12 units
    GOLD_CROWN = "gold_crown"  # 240 units
    PLATINUM_SOVEREIGN = "platinum_sovereign"  # 2400 units (rare, late game)


class MintQuality(Enum):
    """Quality of minting facility"""
    CRUDE = "crude"  # Hand-hammered, irregular
    BASIC = "basic"  # Simple press
    ADVANCED = "advanced"  # Screw press
    INDUSTRIAL = "industrial"  # Steam-powered
    MODERN = "modern"  # Automated


@dataclass
class CoinDenomination:
    """A standardized coin denomination"""
    id: str
    coin_type: CoinType
    name: str
    metal_type: str  # copper, bronze, silver, gold, platinum

    # Value in base units (copper pennies)
    value_in_pennies: int

    # Metal content
    metal_weight_grams: float  # Weight of actual metal
    metal_cost: float  # How much metal required to mint
    purity: float = 1.0  # 0-1, how pure the metal is

    # Production
    difficulty: float = 0.5  # How hard to mint (0-1)

    # Discovery
    discovered: bool = False
    discoverer_id: Optional[str] = None
    discovered_tick: int = 0

    # Usage stats
    total_minted: int = 0
    in_circulation: int = 0


@dataclass
class Mint:
    """A minting facility that produces coins"""
    id: str
    name: str
    location: Tuple[float, float]

    # Ownership
    owner_id: str
    built_tick: int

    # Quality and capabilities
    quality: MintQuality = MintQuality.CRUDE
    max_output_per_tick: int = 10  # Coins per tick

    # What can be minted here
    can_mint: Set[CoinType] = field(default_factory=set)

    # Security
    security_level: float = 0.5  # 0-1, prevents counterfeiting
    guards: int = 0

    # Metal reserves
    metal_reserves: Dict[str, float] = field(default_factory=dict)

    # Production history
    total_coins_minted: int = 0
    coins_by_type: Dict[str, int] = field(default_factory=dict)

    # Status
    operational: bool = True


@dataclass
class CounterfeitOperation:
    """An illegal counterfeiting operation"""
    id: str
    counterfeiter_id: str
    location: Tuple[float, float]

    # What they're faking
    target_coin: CoinType
    quality: float = 0.3  # 0-1, how good the fakes are

    # Production
    coins_produced: int = 0
    detection_risk: float = 0.5  # Chance of being caught per use

    # Status
    discovered: bool = False
    discovered_tick: int = 0


class MintingManager:
    """
    Manages the minting and coinage system.

    Key mechanics:
    - Metal scarcity drives coin value
    - Better mints produce purer coins
    - Counterfeiting creates inflation
    - Debasement (reducing purity) is tempting for rulers
    - Coin discovery progresses: copper → silver → gold
    """

    def __init__(self):
        self.denominations: Dict[str, CoinDenomination] = {}
        self.mints: Dict[str, Mint] = {}
        self.counterfeit_ops: Dict[str, CounterfeitOperation] = {}

        # Discovery tracking
        self.discovered_coins: Set[CoinType] = set()

        # Economic impact
        self.total_coins_in_circulation: int = 0
        self.total_metal_value_minted: float = 0.0
        self.inflation_rate: float = 0.0

        # Statistics
        self.total_mints_built: int = 0
        self.total_counterfeiting_detected: int = 0

        # Initialize coin denominations
        self._init_denominations()

    # ===== DENOMINATION INITIALIZATION =====

    def _init_denominations(self):
        """Initialize all coin denominations"""

        denominations_data = [
            # (coin_type, name, metal, value_pennies, weight_g, metal_cost, difficulty, discovered)
            (CoinType.COPPER_PENNY, "Copper Penny", "copper", 1, 3.5, 3.5, 0.2, True),
            (CoinType.BRONZE_PENNY, "Bronze Penny", "bronze", 1, 3.5, 3.5, 0.3, False),
            (CoinType.SILVER_SHILLING, "Silver Shilling", "silver", 12, 5.6, 5.6, 0.5, False),
            (CoinType.GOLD_CROWN, "Gold Crown", "gold", 240, 7.98, 7.98, 0.7, False),
            (CoinType.PLATINUM_SOVEREIGN, "Platinum Sovereign", "platinum", 2400, 8.0, 8.0, 0.9, False),
        ]

        for coin_type, name, metal, value, weight, cost, diff, discovered in denominations_data:
            denom_id = str(new_uuid())
            denom = CoinDenomination(
                id=denom_id,
                coin_type=coin_type,
                name=name,
                metal_type=metal,
                value_in_pennies=value,
                metal_weight_grams=weight,
                metal_cost=cost,
                difficulty=diff,
                discovered=discovered
            )
            self.denominations[coin_type.value] = denom

            if discovered:
                self.discovered_coins.add(coin_type)

    # ===== MINT CONSTRUCTION =====

    def build_mint(
        self,
        owner_id: str,
        location: Tuple[float, float],
        quality: MintQuality,
        current_tick: int
    ) -> Mint:
        """Build a new minting facility"""

        mint_id = str(new_uuid())

        # Determine capabilities based on quality
        capabilities = self._get_mint_capabilities(quality)

        mint = Mint(
            id=mint_id,
            name=f"{quality.value.title()} Mint",
            location=location,
            owner_id=owner_id,
            built_tick=current_tick,
            quality=quality,
            max_output_per_tick=capabilities['output'],
            can_mint=capabilities['can_mint'],
            security_level=capabilities['security']
        )

        self.mints[mint_id] = mint
        self.total_mints_built += 1

        return mint

    def _get_mint_capabilities(self, quality: MintQuality) -> Dict:
        """Get capabilities for mint quality level"""

        capabilities = {
            MintQuality.CRUDE: {
                'output': 5,
                'can_mint': {CoinType.COPPER_PENNY, CoinType.BRONZE_PENNY},
                'security': 0.3
            },
            MintQuality.BASIC: {
                'output': 20,
                'can_mint': {CoinType.COPPER_PENNY, CoinType.BRONZE_PENNY, CoinType.SILVER_SHILLING},
                'security': 0.5
            },
            MintQuality.ADVANCED: {
                'output': 50,
                'can_mint': {CoinType.COPPER_PENNY, CoinType.BRONZE_PENNY,
                           CoinType.SILVER_SHILLING, CoinType.GOLD_CROWN},
                'security': 0.7
            },
            MintQuality.INDUSTRIAL: {
                'output': 200,
                'can_mint': {CoinType.COPPER_PENNY, CoinType.BRONZE_PENNY,
                           CoinType.SILVER_SHILLING, CoinType.GOLD_CROWN,
                           CoinType.PLATINUM_SOVEREIGN},
                'security': 0.85
            },
            MintQuality.MODERN: {
                'output': 1000,
                'can_mint': set(CoinType),
                'security': 0.95
            }
        }

        return capabilities.get(quality, capabilities[MintQuality.CRUDE])

    # ===== COIN MINTING =====

    def mint_coins(
        self,
        mint_id: str,
        coin_type: CoinType,
        quantity: int,
        metal_available: Dict[str, float]
    ) -> Dict:
        """Mint coins at a facility"""

        if mint_id not in self.mints:
            return {'success': False, 'reason': 'Mint not found'}

        mint = self.mints[mint_id]

        if not mint.operational:
            return {'success': False, 'reason': 'Mint not operational'}

        # Check if coin type can be minted here
        if coin_type not in mint.can_mint:
            return {'success': False, 'reason': f'Cannot mint {coin_type.value} at this quality mint'}

        # Check if coin discovered
        if coin_type not in self.discovered_coins:
            return {'success': False, 'reason': 'Coin type not yet discovered'}

        denomination = self.denominations.get(coin_type.value)
        if not denomination:
            return {'success': False, 'reason': 'Denomination not found'}

        # Check metal availability
        metal_needed = denomination.metal_cost * quantity
        metal_type = denomination.metal_type

        if metal_available.get(metal_type, 0.0) < metal_needed:
            return {
                'success': False,
                'reason': f'Insufficient {metal_type} (need {metal_needed:.1f}g, have {metal_available.get(metal_type, 0):.1f}g)'
            }

        # Check production capacity
        if quantity > mint.max_output_per_tick:
            quantity = mint.max_output_per_tick

        # Mint the coins!
        denomination.total_minted += quantity
        denomination.in_circulation += quantity

        mint.total_coins_minted += quantity
        mint.coins_by_type[coin_type.value] = mint.coins_by_type.get(coin_type.value, 0) + quantity

        self.total_coins_in_circulation += quantity
        self.total_metal_value_minted += metal_needed

        return {
            'success': True,
            'coins_minted': quantity,
            'metal_consumed': metal_needed,
            'coin_value': quantity * denomination.value_in_pennies,
            'coins_produced': {coin_type.value: quantity}
        }

    # ===== COIN DISCOVERY =====

    def discover_coin(
        self,
        coin_type: CoinType,
        discoverer_id: str,
        current_tick: int
    ) -> Optional[CoinDenomination]:
        """Discover a new coin denomination"""

        if coin_type in self.discovered_coins:
            return None  # Already discovered

        denomination = self.denominations.get(coin_type.value)
        if not denomination:
            return None

        # Discovery successful!
        denomination.discovered = True
        denomination.discoverer_id = discoverer_id
        denomination.discovered_tick = current_tick

        self.discovered_coins.add(coin_type)

        return denomination

    # ===== COUNTERFEITING =====

    def start_counterfeiting(
        self,
        counterfeiter_id: str,
        location: Tuple[float, float],
        target_coin: CoinType,
        skill_level: float
    ) -> CounterfeitOperation:
        """Start an illegal counterfeiting operation"""

        op_id = str(new_uuid())

        # Quality based on skill
        quality = min(0.8, skill_level)  # Max 80% quality for fakes

        # Detection risk based on quality
        detection_risk = 1.0 - quality

        operation = CounterfeitOperation(
            id=op_id,
            counterfeiter_id=counterfeiter_id,
            location=location,
            target_coin=target_coin,
            quality=quality,
            detection_risk=detection_risk
        )

        self.counterfeit_ops[op_id] = operation

        return operation

    def produce_counterfeit_coins(
        self,
        operation_id: str,
        quantity: int
    ) -> Dict:
        """Produce counterfeit coins"""

        if operation_id not in self.counterfeit_ops:
            return {'success': False, 'reason': 'Operation not found'}

        operation = self.counterfeit_ops[operation_id]

        if operation.discovered:
            return {'success': False, 'reason': 'Operation has been discovered!'}

        # Produce fakes
        operation.coins_produced += quantity

        # Each fake coin has chance of detection when used
        # This creates inflation without increasing real metal value

        return {
            'success': True,
            'counterfeit_coins': quantity,
            'quality': operation.quality,
            'detection_risk': operation.detection_risk
        }

    def detect_counterfeit(self, operation_id: str, current_tick: int) -> bool:
        """Detect a counterfeiting operation"""

        if operation_id not in self.counterfeit_ops:
            return False

        operation = self.counterfeit_ops[operation_id]
        operation.discovered = True
        operation.discovered_tick = current_tick

        self.total_counterfeiting_detected += 1

        return True

    # ===== DEBASEMENT (Reducing coin purity) =====

    def debase_currency(
        self,
        coin_type: CoinType,
        new_purity: float,
        debaser_id: str
    ) -> Dict:
        """Reduce the purity of coins (inflationary!)"""

        denomination = self.denominations.get(coin_type.value)
        if not denomination:
            return {'success': False, 'reason': 'Coin not found'}

        if new_purity >= denomination.purity:
            return {'success': False, 'reason': 'New purity must be lower'}

        if new_purity < 0.1:
            return {'success': False, 'reason': 'Purity too low (min 10%)'}

        old_purity = denomination.purity
        denomination.purity = new_purity

        # Calculate inflation impact
        purity_loss = old_purity - new_purity
        inflation_impact = purity_loss * 0.5  # Each 10% purity loss = 5% inflation

        self.inflation_rate += inflation_impact

        return {
            'success': True,
            'old_purity': old_purity,
            'new_purity': new_purity,
            'inflation_impact': inflation_impact,
            'message': f'{coin_type.value} debased from {old_purity*100:.0f}% to {new_purity*100:.0f}% purity!'
        }

    # ===== CONVERSION & EXCHANGE =====

    def convert_coins(
        self,
        from_coin: CoinType,
        from_quantity: int,
        to_coin: CoinType
    ) -> Dict:
        """Convert between coin denominations"""

        from_denom = self.denominations.get(from_coin.value)
        to_denom = self.denominations.get(to_coin.value)

        if not from_denom or not to_denom:
            return {'success': False, 'reason': 'Denomination not found'}

        # Calculate value in pennies
        total_value_pennies = from_quantity * from_denom.value_in_pennies

        # Convert to target denomination
        to_quantity = total_value_pennies // to_denom.value_in_pennies
        remainder_pennies = total_value_pennies % to_denom.value_in_pennies

        return {
            'success': True,
            'converted_quantity': to_quantity,
            'remainder_pennies': remainder_pennies,
            'exchange_rate': from_denom.value_in_pennies / to_denom.value_in_pennies
        }

    # ===== QUERIES =====

    def get_coin_value_in_pennies(self, coin_type: CoinType, quantity: int = 1) -> int:
        """Get total value in base pennies"""
        denom = self.denominations.get(coin_type.value)
        if denom:
            return denom.value_in_pennies * quantity
        return 0

    def get_mints_by_owner(self, owner_id: str) -> List[Mint]:
        """Get all mints owned by an agent"""
        return [m for m in self.mints.values() if m.owner_id == owner_id]

    def get_statistics(self) -> Dict:
        """Get minting statistics"""

        total_value_minted = sum(
            d.total_minted * d.value_in_pennies
            for d in self.denominations.values()
        )

        return {
            'total_mints': len(self.mints),
            'operational_mints': sum(1 for m in self.mints.values() if m.operational),
            'total_coins_minted': sum(d.total_minted for d in self.denominations.values()),
            'total_coins_in_circulation': self.total_coins_in_circulation,
            'total_value_pennies': total_value_minted,
            'discovered_coin_types': len(self.discovered_coins),
            'active_counterfeiting': sum(1 for op in self.counterfeit_ops.values() if not op.discovered),
            'detected_counterfeiters': self.total_counterfeiting_detected,
            'inflation_rate': round(self.inflation_rate * 100, 2)
        }
