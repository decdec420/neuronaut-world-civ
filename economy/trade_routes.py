"""
Trade Routes & Long-Distance Commerce System

Implements:
- Trade routes between settlements
- Caravans and merchants
- Supply and demand across regions
- Price arbitrage opportunities
- Trade monopolies and guilds
- Piracy and banditry
- Trade agreements and embargoes
- Merchant networks

Philosophy: Trade creates prosperity through specialization.
Long-distance commerce connects civilizations.
Price differences drive merchant activity.
Control of trade routes means power and wealth.
"""

import random
from engine.ids import new_uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class RouteStatus(Enum):
    """Status of a trade route"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKADED = "blockaded"  # Blocked by war/piracy
    MONOPOLIZED = "monopolized"  # Controlled by one faction


class CaravanStatus(Enum):
    """Status of a caravan"""
    TRAVELING = "traveling"
    TRADING = "trading"
    RESTING = "resting"
    ATTACKED = "attacked"
    ARRIVED = "arrived"


class GoodType(Enum):
    """Types of tradeable goods"""
    # Basic resources
    FOOD = "food"
    WATER = "water"
    WOOD = "wood"
    STONE = "stone"
    METAL = "metal"

    # Manufactured goods
    TOOLS = "tools"
    WEAPONS = "weapons"
    CLOTHING = "clothing"

    # Luxury goods (high profit margins)
    SPICES = "spices"
    SILK = "silk"
    GEMS = "gems"
    GOLD = "gold"
    PERFUME = "perfume"

    # Special goods
    MEDICINE = "medicine"
    BOOKS = "books"
    ART = "art"


@dataclass
class TradeRoute:
    """A established trade route between two points"""
    id: str
    name: str

    # Endpoints
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    distance: float

    # Usage
    established_by: str  # Agent or faction ID
    established_tick: int

    # Traffic
    caravans_using: Set[str] = field(default_factory=set)
    total_volume: float = 0.0  # Total goods traded

    # Economics
    toll: float = 0.0  # Cost to use route
    toll_collector: Optional[str] = None

    # Security
    safety_level: float = 0.8  # 0-1, higher = safer
    bandit_activity: float = 0.1  # 0-1, higher = more bandits
    guards: int = 0

    # Status
    status: RouteStatus = RouteStatus.ACTIVE
    monopoly_holder: Optional[str] = None


@dataclass
class Caravan:
    """A traveling merchant caravan"""
    id: str
    merchant_id: str  # Owner/operator

    # Route
    route_id: str
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    current_position: Tuple[float, float]
    progress: float = 0.0  # 0-1

    # Cargo
    cargo: Dict[str, int] = field(default_factory=dict)  # good -> quantity
    cargo_value: float = 0.0

    # Economics
    expected_profit: float = 0.0
    actual_profit: float = 0.0

    # Security
    guards: int = 0
    armed: bool = False

    # Journey
    departed_tick: int = 0
    arrival_tick: int = 0
    status: CaravanStatus = CaravanStatus.TRAVELING

    # Events
    attacked: bool = False
    goods_lost: float = 0.0


@dataclass
class Market:
    """A regional market"""
    id: str
    name: str
    location: Tuple[float, float]

    # Supply and demand
    supply: Dict[str, int] = field(default_factory=dict)  # good -> quantity available
    demand: Dict[str, int] = field(default_factory=dict)  # good -> quantity wanted

    # Prices (affected by supply/demand)
    prices: Dict[str, float] = field(default_factory=dict)  # good -> price

    # Market activity
    total_trade_volume: float = 0.0
    merchants_present: Set[str] = field(default_factory=set)

    # Modifiers
    prosperity: float = 1.0  # Multiplier for all prices


@dataclass
class MerchantGuild:
    """A merchant organization/monopoly"""
    id: str
    name: str

    # Members
    guildmaster_id: str
    members: Set[str] = field(default_factory=set)

    # Controlled routes
    controlled_routes: Set[str] = field(default_factory=set)
    monopolized_goods: Set[GoodType] = field(default_factory=set)

    # Economics
    guild_treasury: float = 0.0
    membership_fee: float = 10.0

    # Power
    political_influence: float = 0.3  # 0-1

    founded_tick: int = 0


@dataclass
class PirateGang:
    """Bandits/pirates that attack caravans"""
    id: str
    name: str

    # Members
    leader_id: str
    base_location: Tuple[float, float]  # Territory location

    # Members and territory
    members: Set[str] = field(default_factory=set)
    operating_routes: Set[str] = field(default_factory=set)

    # Activity
    total_raids: int = 0
    total_loot: float = 0.0
    success_rate: float = 0.5

    # Status
    active: bool = True
    bounty: float = 0.0  # Reward for capture


class TradeRoutesManager:
    """
    Manages long-distance trade, caravans, and commerce.

    Key mechanics:
    - Price differences between markets create arbitrage opportunities
    - Trade routes become more valuable as they're used
    - Monopolies can form on profitable routes
    - Bandits attack caravans based on cargo value
    - Supply and demand update based on trade flows
    """

    def __init__(self):
        self.trade_routes: Dict[str, TradeRoute] = {}
        self.caravans: Dict[str, Caravan] = {}
        self.markets: Dict[str, Market] = {}
        self.merchant_guilds: Dict[str, MerchantGuild] = {}
        self.pirate_gangs: Dict[str, PirateGang] = {}

        # Statistics
        self.total_routes_established: int = 0
        self.total_caravans_sent: int = 0
        self.total_goods_traded: float = 0.0
        self.total_profit_made: float = 0.0
        self.total_caravans_raided: int = 0

    # ===== TRADE ROUTES =====

    def establish_trade_route(
        self,
        establisher_id: str,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        current_tick: int
    ) -> TradeRoute:
        """Establish a new trade route"""

        route_id = str(new_uuid())

        # Calculate distance
        distance = ((destination[0] - origin[0])**2 + (destination[1] - origin[1])**2)**0.5

        route = TradeRoute(
            id=route_id,
            name=f"Route {len(self.trade_routes) + 1}",
            origin=origin,
            destination=destination,
            distance=distance,
            established_by=establisher_id,
            established_tick=current_tick
        )

        self.trade_routes[route_id] = route
        self.total_routes_established += 1

        return route

    def set_toll(
        self,
        route_id: str,
        toll_amount: float,
        collector_id: str
    ) -> bool:
        """Set a toll on a trade route"""

        if route_id not in self.trade_routes:
            return False

        route = self.trade_routes[route_id]
        route.toll = toll_amount
        route.toll_collector = collector_id

        return True

    def monopolize_route(
        self,
        route_id: str,
        monopoly_holder_id: str
    ) -> bool:
        """Take monopoly control of a route"""

        if route_id not in self.trade_routes:
            return False

        route = self.trade_routes[route_id]
        route.status = RouteStatus.MONOPOLIZED
        route.monopoly_holder = monopoly_holder_id

        return True

    # ===== CARAVANS =====

    def send_caravan(
        self,
        merchant_id: str,
        route_id: str,
        cargo: Dict[str, int],
        cargo_value: float,
        guards: int,
        current_tick: int
    ) -> Optional[Caravan]:
        """Send a merchant caravan"""

        if route_id not in self.trade_routes:
            return None

        route = self.trade_routes[route_id]

        if route.status not in [RouteStatus.ACTIVE, RouteStatus.MONOPOLIZED]:
            return None  # Route unusable

        caravan_id = str(new_uuid())

        # Calculate expected travel time
        travel_time = int(route.distance / 5)  # Assume 5 units per tick

        caravan = Caravan(
            id=caravan_id,
            merchant_id=merchant_id,
            route_id=route_id,
            origin=route.origin,
            destination=route.destination,
            current_position=route.origin,
            cargo=cargo,
            cargo_value=cargo_value,
            guards=guards,
            armed=guards > 0,
            departed_tick=current_tick,
            arrival_tick=current_tick + travel_time
        )

        self.caravans[caravan_id] = caravan
        route.caravans_using.add(caravan_id)

        self.total_caravans_sent += 1

        return caravan

    def update_caravans(self, current_tick: int) -> List[Dict]:
        """Update all traveling caravans"""

        events = []

        for caravan in self.caravans.values():
            if caravan.status != CaravanStatus.TRAVELING:
                continue

            route = self.trade_routes.get(caravan.route_id)
            if not route:
                continue

            # Update progress
            ticks_traveled = current_tick - caravan.departed_tick
            total_journey_time = caravan.arrival_tick - caravan.departed_tick
            caravan.progress = ticks_traveled / max(1, total_journey_time)

            # Update position (linear interpolation)
            caravan.current_position = (
                caravan.origin[0] + (caravan.destination[0] - caravan.origin[0]) * caravan.progress,
                caravan.origin[1] + (caravan.destination[1] - caravan.origin[1]) * caravan.progress
            )

            # Check for arrival
            if current_tick >= caravan.arrival_tick:
                caravan.status = CaravanStatus.ARRIVED
                caravan.progress = 1.0
                caravan.current_position = caravan.destination

                events.append({
                    'type': 'caravan_arrived',
                    'caravan_id': caravan.id,
                    'merchant_id': caravan.merchant_id,
                    'cargo_value': caravan.cargo_value
                })

                # Update route traffic
                route.total_volume += caravan.cargo_value
                route.caravans_using.discard(caravan.id)

            # Check for bandit attacks
            elif random.random() < route.bandit_activity * 0.1:  # Attack chance per tick
                attack_result = self._resolve_bandit_attack(caravan, route)
                if attack_result['attacked']:
                    events.append(attack_result)

        return events

    def _resolve_bandit_attack(
        self,
        caravan: Caravan,
        route: TradeRoute
    ) -> Dict:
        """Resolve a bandit attack on a caravan"""

        # Determine if attack succeeds
        # More guards = lower success chance
        base_success = 0.7
        guard_reduction = caravan.guards * 0.1
        attack_success_chance = max(0.1, base_success - guard_reduction)

        if random.random() < attack_success_chance:
            # Attack succeeds - lose cargo
            loss_percentage = random.uniform(0.3, 0.8)  # Lose 30-80% of cargo
            goods_lost = caravan.cargo_value * loss_percentage

            caravan.attacked = True
            caravan.goods_lost = goods_lost
            caravan.cargo_value -= goods_lost
            caravan.status = CaravanStatus.ATTACKED

            self.total_caravans_raided += 1

            return {
                'type': 'caravan_attacked',
                'caravan_id': caravan.id,
                'merchant_id': caravan.merchant_id,
                'goods_lost': goods_lost,
                'attacked': True,
                'guards_helped': False
            }
        else:
            # Attack failed - guards protected caravan
            return {
                'type': 'attack_repelled',
                'caravan_id': caravan.id,
                'merchant_id': caravan.merchant_id,
                'attacked': False,
                'guards_helped': True
            }

    # ===== MARKETS =====

    def create_market(
        self,
        name: str,
        location: Tuple[float, float]
    ) -> Market:
        """Create a regional market"""

        market_id = str(new_uuid())

        # Initialize with base prices
        base_prices = {
            GoodType.FOOD.value: 1.0,
            GoodType.WATER.value: 0.5,
            GoodType.WOOD.value: 2.0,
            GoodType.STONE.value: 3.0,
            GoodType.METAL.value: 5.0,
            GoodType.SPICES.value: 20.0,
            GoodType.SILK.value: 30.0,
            GoodType.GEMS.value: 50.0
        }

        market = Market(
            id=market_id,
            name=name,
            location=location,
            prices=base_prices
        )

        self.markets[market_id] = market

        return market

    def update_market_prices(self, market_id: str):
        """Update prices based on supply and demand"""

        if market_id not in self.markets:
            return

        market = self.markets[market_id]

        for good, supply in market.supply.items():
            demand = market.demand.get(good, 0)

            if supply == 0 and demand > 0:
                # High demand, no supply = huge price increase
                market.prices[good] = market.prices.get(good, 1.0) * 2.0
            elif supply > 0 and demand == 0:
                # Supply but no demand = price decrease
                market.prices[good] = market.prices.get(good, 1.0) * 0.5
            elif supply > 0 and demand > 0:
                # Adjust based on ratio
                ratio = demand / supply
                if ratio > 1.5:
                    market.prices[good] = market.prices.get(good, 1.0) * 1.2
                elif ratio < 0.5:
                    market.prices[good] = market.prices.get(good, 1.0) * 0.8

    def calculate_arbitrage_opportunity(
        self,
        market_a_id: str,
        market_b_id: str,
        good: str
    ) -> Dict:
        """Calculate profit potential from price arbitrage"""

        market_a = self.markets.get(market_a_id)
        market_b = self.markets.get(market_b_id)

        if not market_a or not market_b:
            return {'profitable': False, 'reason': 'Markets not found'}

        price_a = market_a.prices.get(good, 0)
        price_b = market_b.prices.get(good, 0)

        if price_a == 0 or price_b == 0:
            return {'profitable': False, 'reason': 'Good not traded in one market'}

        # Calculate profit margin
        buy_price = min(price_a, price_b)
        sell_price = max(price_a, price_b)
        profit_margin = (sell_price - buy_price) / buy_price

        # Account for transport costs (simplified)
        distance = ((market_a.location[0] - market_b.location[0])**2 +
                   (market_a.location[1] - market_b.location[1])**2)**0.5
        transport_cost_ratio = distance * 0.01  # 1% per distance unit

        net_profit_margin = profit_margin - transport_cost_ratio

        return {
            'profitable': net_profit_margin > 0,
            'buy_at': market_a_id if price_a < price_b else market_b_id,
            'sell_at': market_b_id if price_a < price_b else market_a_id,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'profit_margin': net_profit_margin,
            'expected_profit_per_unit': buy_price * net_profit_margin
        }

    # ===== MERCHANT GUILDS =====

    def found_merchant_guild(
        self,
        guildmaster_id: str,
        name: str,
        current_tick: int
    ) -> MerchantGuild:
        """Found a merchant guild"""

        guild_id = str(new_uuid())

        guild = MerchantGuild(
            id=guild_id,
            name=name,
            guildmaster_id=guildmaster_id,
            members={guildmaster_id},
            founded_tick=current_tick
        )

        self.merchant_guilds[guild_id] = guild

        return guild

    def join_guild(
        self,
        guild_id: str,
        merchant_id: str,
        membership_fee: float
    ) -> bool:
        """Join a merchant guild"""

        if guild_id not in self.merchant_guilds:
            return False

        guild = self.merchant_guilds[guild_id]
        guild.members.add(merchant_id)
        guild.guild_treasury += membership_fee

        return True

    # ===== PIRACY =====

    def form_pirate_gang(
        self,
        leader_id: str,
        name: str,
        base_location: Tuple[float, float]
    ) -> PirateGang:
        """Form a pirate/bandit gang"""

        gang_id = str(new_uuid())

        gang = PirateGang(
            id=gang_id,
            name=name,
            leader_id=leader_id,
            members={leader_id},
            base_location=base_location
        )

        self.pirate_gangs[gang_id] = gang

        return gang

    # ===== QUERIES =====

    def get_active_routes(self) -> List[TradeRoute]:
        """Get all active trade routes"""
        return [r for r in self.trade_routes.values() if r.status == RouteStatus.ACTIVE]

    def get_traveling_caravans(self) -> List[Caravan]:
        """Get all caravans currently traveling"""
        return [c for c in self.caravans.values() if c.status == CaravanStatus.TRAVELING]

    def get_statistics(self) -> Dict:
        """Get trade statistics"""

        active_routes = len(self.get_active_routes())
        traveling_caravans = len(self.get_traveling_caravans())
        total_trade_volume = sum(r.total_volume for r in self.trade_routes.values())

        return {
            'total_routes': len(self.trade_routes),
            'active_routes': active_routes,
            'total_caravans_sent': self.total_caravans_sent,
            'traveling_caravans': traveling_caravans,
            'total_trade_volume': round(total_trade_volume, 2),
            'total_profit_made': round(self.total_profit_made, 2),
            'caravans_raided': self.total_caravans_raided,
            'raid_rate': round((self.total_caravans_raided / max(1, self.total_caravans_sent)) * 100, 2),
            'markets': len(self.markets),
            'merchant_guilds': len(self.merchant_guilds),
            'pirate_gangs': sum(1 for g in self.pirate_gangs.values() if g.active)
        }
